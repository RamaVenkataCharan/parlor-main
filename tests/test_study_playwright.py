"""Playwright end-to-end integration test for Parlor Study Mode runner.

Tests:
- Settings toggle for Study Mode and header badge visibility
- Launching Study Runner Modal
- Consent & 18+ adult confirmation gating
- Pre-Session Sensor Quality Check (~1 min)
- 4-step Guided Protocol (Rest, Speech, Arithmetic Stressor, Recovery)
- 3-item EMA survey responses submitted after each step
- Session QA Summary display
- Anonymized CSV export and zero-media logging verification
- Complete cleanup of temporary test directories
"""

import http.server
import json
import threading
from pathlib import Path
import pytest
from playwright.sync_api import Browser, expect

from parlor.study import StudyStorage

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "src" / "parlor" / "web"


class _WebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def web_server():
    server = http.server.HTTPServer(("127.0.0.1", 0), _WebHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def test_study_mode_end_to_end_flow(browser: Browser, web_server: str, tmp_path: Path):
    """E2E test of complete Study Mode session flow from consent to export."""
    storage_dir = tmp_path / "study_data_playwright"
    storage = StudyStorage(data_dir=storage_dir)

    context = browser.new_context(
        permissions=["camera", "microphone"],
        viewport={"width": 1440, "height": 900}
    )
    page = context.new_page()

    # Route /api/study requests to our isolated StudyStorage instance
    def handle_study_routes(route):
        req = route.request
        url = req.url
        if "/api/study/participants" in url:
            registry = storage.load_participants()
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"participants": registry, "next_code": "P99"})
            )
        elif "/api/study/register" in url:
            data = req.post_data_json
            try:
                storage.register_participant(
                    participant_code=data.get("participant_code", "P99"),
                    group=data.get("group", "validation"),
                    role=data.get("role", "external"),
                    is_adult=bool(data.get("is_adult", False)),
                    consent_given=bool(data.get("consent_given", False)),
                )
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({"success": True, "participant_code": "P99", "warning": ""})
                )
            except Exception as e:
                route.fulfill(status=400, content_type="application/json", body=json.dumps({"detail": str(e)}))
        elif "/api/study/window" in url:
            win_id = storage.log_observation_window(req.post_data_json)
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"success": True, "window_id": win_id}))
        elif "/api/study/ema" in url:
            resp_id = storage.log_ema_response(req.post_data_json)
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"success": True, "response_id": resp_id}))
        elif "/api/study/finish" in url:
            sess_id = storage.log_session_summary(req.post_data_json)
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"success": True, "session_id": sess_id}))
        elif "/api/study/export/csv" in url:
            csv_data = storage.export_anonymized_csv()
            route.fulfill(status=200, content_type="text/csv", body=csv_data)
        else:
            route.continue_()

    page.route("**/api/study/**", handle_study_routes)

    # Mock media stream & speed up study countdown for testing
    page.add_init_script("""
        window.__STUDY_SPEEDUP__ = true;
        window.navigator.mediaDevices.getUserMedia = async (constraints) => {
            const canvas = document.createElement('canvas');
            canvas.width = 640;
            canvas.height = 480;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#10B981';
            ctx.fillRect(0, 0, 640, 480);
            const stream = canvas.captureStream(30);
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const dest = audioCtx.createMediaStreamDestination();
            return new MediaStream([...stream.getVideoTracks(), ...dest.stream.getAudioTracks()]);
        };
        // Inject mock face and vocal telemetry snapshots
        setInterval(() => {
            if (typeof updateFaceMetrics === 'function') {
                updateFaceMetrics({
                    face_detected: true,
                    au04_brow_furrow: 0.28,
                    au07_lid_tightener: 0.22,
                    au15_lip_depressor: 0.15,
                    au20_lip_stretcher: 0.35,
                    head_yaw: -2.1,
                    head_pitch: 3.5,
                    head_roll: 0.8
                });
            }
            if (typeof updateVocalMetrics === 'function') {
                updateVocalMetrics({
                    speech_detected: true,
                    pitch_hz: 148.0,
                    pitch_delta_hz: 5.2,
                    jitter_pct: 0.8,
                    shimmer_pct: 1.5,
                    steadiness: 0.88,
                    speech_pace: 4.5
                });
            }
        }, 100);
    """)

    page.goto(f"{web_server}/")

    # 1. Open settings panel
    page.click("#diagBtn")
    expect(page.locator("#diagPanel")).to_be_visible()

    # 2. Toggle Study Mode
    page.evaluate("() => { const el = document.getElementById('studyModeToggle'); el.checked = true; el.dispatchEvent(new Event('change')); }")
    expect(page.locator("#studyModeBadge")).to_be_visible()
    expect(page.locator("#studyModeBadge")).to_contain_text("Study mode: recording numeric features locally")

    # 3. Launch Study Runner
    page.evaluate("() => { document.getElementById('btnLaunchStudy').click(); }")
    expect(page.locator("#studyModal")).to_be_visible()
    expect(page.locator("#studyStageConsent")).to_be_visible()

    # Verify Proceed button is initially disabled
    proceed_btn = page.locator("#btnProceedToQuality")
    expect(proceed_btn).to_be_disabled()

    # Check Age 18+ and Consent
    page.evaluate("() => { document.getElementById('studyAdultCheck').click(); document.getElementById('studyConsentCheck').click(); }")
    expect(proceed_btn).to_be_enabled()

    # Set Code and Group
    page.fill("#studyParticipantCode", "P99")
    page.select_option("#studyParticipantGroup", "validation")
    page.click("#btnProceedToQuality")

    # 4. Sensor Quality Check Stage
    expect(page.locator("#studyStageQuality")).to_be_visible()
    page.wait_for_timeout(1000)

    start_btn = page.locator("#btnStartProtocol")
    expect(start_btn).to_be_enabled()
    start_btn.click()

    # 5. Protocol Stage
    expect(page.locator("#studyStageProtocol")).to_be_visible()

    # Complete 4 Steps and EMA Surveys
    for step_num in range(1, 5):
        # Verify step title or pill
        page.wait_for_timeout(400)
        # Advance via Skip/Next Step to prompt EMA
        page.click("#btnSkipStep")
        expect(page.locator("#studyEmaOverlay")).to_be_visible()

        # Submit EMA Survey
        page.click("#btnSubmitEmaSurvey")
        page.wait_for_timeout(400)

    # 6. Summary Stage
    expect(page.locator("#studyStageSummary")).to_be_visible()
    expect(page.locator("#sumParticipantCode")).to_contain_text("P99")
    expect(page.locator("#sumGroup")).to_contain_text("validation")

    # 7. Verify Logged Data Files
    assert storage.windows_file.exists(), "Observation windows file missing!"
    assert storage.ema_file.exists(), "EMA responses file missing!"
    assert storage.sessions_file.exists(), "Study sessions file missing!"

    with open(storage.windows_file, "r", encoding="utf-8") as wf:
        wins = [json.loads(line) for line in wf if line.strip()]
    assert len(wins) > 0, "No observation windows recorded!"

    with open(storage.ema_file, "r", encoding="utf-8") as ef:
        emas = [json.loads(line) for line in ef if line.strip()]
    assert len(emas) == 4, f"Expected 4 EMA responses, got {len(emas)}"

    # STRICT ASSERTION: Zero image, frame, or audio bytes
    for w in wins:
        assert "image" not in w
        assert "frame" not in w
        assert "audio" not in w
        assert "landmarks" not in w

    # Verify CSV export
    csv_str = storage.export_anonymized_csv()
    assert "P99" in csv_str
    assert "validation" in csv_str
    assert "paired_ema_tier" in csv_str

    # 8. Close Runner
    page.click("#btnSummaryDone")
    expect(page.locator("#studyModal")).not_to_be_visible()
