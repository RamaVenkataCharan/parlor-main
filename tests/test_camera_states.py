"""Playwright integration tests for camera state machine, placeholder visibility, stale data clearing, and mode chip."""

import http.server
import threading
from pathlib import Path
import pytest
from playwright.sync_api import Browser, Page, expect

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "src" / "parlor" / "web"
EVIDENCE_DIR = ROOT / "evidence" / "ui"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


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


def test_camera_state_placeholder_hidden_when_live(browser: Browser, web_server: str):
    """SIMULATED: Verify that when camera stream is live, #cameraPlaceholder is completely hidden,
    video is visible, and the status chip reads 'CAMERA ON'."""
    context = browser.new_context(
        permissions=["camera", "microphone"],
        viewport={"width": 1440, "height": 900}
    )
    page = context.new_page()

    # Provide a mock live video stream with advancing frames
    page.add_init_script("""
        window.navigator.mediaDevices.getUserMedia = async (constraints) => {
            const canvas = document.createElement('canvas');
            canvas.width = 640;
            canvas.height = 480;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#2DD4BF';
            ctx.fillRect(0, 0, 640, 480);
            const stream = canvas.captureStream(30);
            // Add fake audio track if requested
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const dest = audioCtx.createMediaStreamDestination();
            const combined = new MediaStream([
                ...stream.getVideoTracks(),
                ...dest.stream.getAudioTracks()
            ]);
            return combined;
        };
    """)

    page.goto(f"{web_server}/index.html", wait_until="networkidle")
    page.wait_for_timeout(800)

    # Force verification
    page.evaluate("() => { if (typeof verifyCameraLiveState === 'function') verifyCameraLiveState(); }")
    page.wait_for_timeout(300)

    ph = page.locator("#cameraPlaceholder")
    video = page.locator("#video")
    live_text = page.locator("#videoLiveText")

    # Placeholder must be hidden
    expect(ph).to_have_attribute("hidden", "")
    ph_display = page.evaluate("() => window.getComputedStyle(document.getElementById('cameraPlaceholder')).display")
    assert ph_display == "none", f"Expected placeholder display none, got {ph_display}"

    # Video must be fully visible
    expect(video).to_be_visible()
    expect(live_text).to_have_text("CAMERA ON")

    page.screenshot(path=str(EVIDENCE_DIR / "camera_state_live_simulated.png"))
    context.close()


def test_camera_state_denied_shows_actionable_placeholder(browser: Browser, web_server: str):
    """SIMULATED: Verify that when camera permission is denied, placeholder shows actionable guidance
    and chip displays 'ACCESS DENIED'."""
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page.add_init_script("""
        window.navigator.mediaDevices.getUserMedia = async () => {
            const err = new Error('Permission denied');
            err.name = 'NotAllowedError';
            throw err;
        };
    """)

    page.goto(f"{web_server}/index.html", wait_until="networkidle")
    page.wait_for_timeout(500)

    ph = page.locator("#cameraPlaceholder")
    ph_title = page.locator("#placeholderTitle")
    live_text = page.locator("#videoLiveText")

    expect(ph).not_to_have_attribute("hidden", "")
    expect(ph_title).to_contain_text("Permission Denied")
    expect(live_text).to_have_text("ACCESS DENIED")

    page.screenshot(path=str(EVIDENCE_DIR / "camera_state_denied_simulated.png"))
    context.close()


def test_camera_state_busy_shows_actionable_placeholder(browser: Browser, web_server: str):
    """SIMULATED: Verify that when camera device is busy, placeholder shows actionable guidance."""
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page.add_init_script("""
        window.navigator.mediaDevices.getUserMedia = async () => {
            const err = new Error('Camera is already in use');
            err.name = 'NotReadableError';
            throw err;
        };
    """)

    page.goto(f"{web_server}/index.html", wait_until="networkidle")
    page.wait_for_timeout(500)

    ph = page.locator("#cameraPlaceholder")
    ph_title = page.locator("#placeholderTitle")
    live_text = page.locator("#videoLiveText")

    expect(ph).not_to_have_attribute("hidden", "")
    expect(ph_title).to_contain_text("Device In Use")
    expect(live_text).to_have_text("CAMERA BUSY")

    page.screenshot(path=str(EVIDENCE_DIR / "camera_state_busy_simulated.png"))
    context.close()


def test_camera_state_paused_and_resume(browser: Browser, web_server: str):
    """Verify that toggling camera off pauses the stream, shows 'Camera Paused', and updates chip."""
    context = browser.new_context(
        permissions=["camera", "microphone"],
        viewport={"width": 1440, "height": 900}
    )
    page = context.new_page()

    page.add_init_script("""
        window.navigator.mediaDevices.getUserMedia = async (constraints) => {
            const canvas = document.createElement('canvas');
            canvas.width = 640;
            canvas.height = 480;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#2DD4BF';
            ctx.fillRect(0, 0, 640, 480);
            const stream = canvas.captureStream(30);
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const dest = audioCtx.createMediaStreamDestination();
            return new MediaStream([
                ...stream.getVideoTracks(),
                ...dest.stream.getAudioTracks()
            ]);
        };
    """)

    page.goto(f"{web_server}/index.html", wait_until="networkidle")
    page.wait_for_timeout(800)

    # Force verification of live state first
    page.evaluate("() => { if (typeof verifyCameraLiveState === 'function') verifyCameraLiveState(); }")
    page.wait_for_timeout(200)

    live_text = page.locator("#videoLiveText")
    expect(live_text).to_have_text("CAMERA ON")

    # Click Camera Toggle to turn off
    page.locator("#cameraToggle").click()
    page.wait_for_timeout(300)

    ph = page.locator("#cameraPlaceholder")
    ph_title = page.locator("#placeholderTitle")

    expect(ph).not_to_have_attribute("hidden", "")
    expect(ph_title).to_have_text("Camera Paused")
    expect(live_text).to_have_text("CAMERA OFF")

    page.screenshot(path=str(EVIDENCE_DIR / "camera_state_paused.png"))
    context.close()


def test_stale_face_data_clears_after_1500ms(browser: Browser, web_server: str):
    """Verify that if face data is older than 1.5s, AU values reset to '—', bars to 0%, and status to 'Idle' or 'Camera paused'."""
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page.goto(f"{web_server}/index.html", wait_until="networkidle")
    page.wait_for_timeout(400)

    # Inject simulated face data
    page.evaluate("""() => {
        updateFaceMetrics({
            face_detected: true,
            au04_brow_furrow: 0.65,
            au07_lid_tightener: 0.45,
            au15_lip_depressor: 0.20,
            au20_lip_stretcher: 0.35,
            head_yaw: 2.5,
            head_pitch: -1.0,
            head_roll: 0.5,
            mesh_points: [[0.5, 0.5]]
        }, true);
    }""")

    # Verify initial injected values
    au04_val = page.locator("#faceAU04Value")
    au04_bar = page.locator("#faceAU04Bar")
    expect(au04_val).to_have_text("0.65")
    expect(au04_bar).to_have_attribute("style", "width: 65%;")

    # Now make snapshot stale by 2000ms
    page.evaluate("() => { lastFaceSnapshotAt = Date.now() - 2000; }")
    page.wait_for_timeout(400)

    # Values must have been cleared to '—' and 0%
    expect(au04_val).to_have_text("—")
    expect(au04_bar).to_have_attribute("style", "width: 0%;")

    status = page.locator("#faceRailStatus")
    status_text = status.inner_text().strip()
    assert any(s in status_text for s in ("Idle", "Camera paused", "No face")), f"Unexpected status: {status_text}"

    page.screenshot(path=str(EVIDENCE_DIR / "face_stale_cleared.png"))
    context.close()


def test_mode_chip_display_and_switch_back(browser: Browser, web_server: str):
    """Verify that mode chip displays across modes and stop button switches back to Conversation."""
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page.goto(f"{web_server}/index.html", wait_until="networkidle")
    page.wait_for_timeout(400)

    mode_chip = page.locator("#modeChip")
    mode_label = page.locator("#modeLabel")
    mode_stop = page.locator("#modeStop")

    # Initially in conversation mode: chip visible, label Conversation, stop button hidden
    expect(mode_chip).to_be_visible()
    expect(mode_label).to_have_text("Conversation")
    expect(mode_stop).to_be_hidden()

    # Switch to translate mode
    page.evaluate("() => setSessionMode('translate')")
    expect(mode_label).to_have_text("Translating → English")
    expect(mode_stop).to_be_visible()

    # Switch to listen mode
    page.evaluate("() => setSessionMode('listen')")
    expect(mode_label).to_have_text("Just listening")
    expect(mode_stop).to_be_visible()

    # Click stop button to switch back to conversation mode
    mode_stop.click()
    page.wait_for_timeout(200)

    expect(mode_label).to_have_text("Conversation")
    expect(mode_stop).to_be_hidden()

    page.screenshot(path=str(EVIDENCE_DIR / "mode_chip_verified.png"))
    context.close()

