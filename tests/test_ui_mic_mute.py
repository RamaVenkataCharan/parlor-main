"""Playwright UI regression test for mic mute detection (app.js):
Verifies that when MediaStreamTrack has track.muted === true or !track.enabled,
app.js displays an amber UI warning ('Mic Muted', dot class 'muted') and updates
the diagnostics panel to '🔴 Muted', rather than silently hanging in 'listening' state.
"""

import http.server
import threading
from pathlib import Path
import pytest
from playwright.sync_api import Page, expect

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


def test_mic_mute_detection_shows_amber_warning(page: Page, web_server: str):
    """Verify that when MediaStreamTrack has muted === true, app.js sets state to 'muted'
    and displays amber UI warning instead of silently hanging in 'listening' state.
    """
    page.add_init_script("""
        window.navigator.mediaDevices.getUserMedia = async (constraints) => {
            const track = {
                kind: 'audio',
                enabled: true,
                muted: true,
                readyState: 'live',
                label: 'Mock Microphone',
                getSettings: () => ({ deviceId: 'mock-mic-1' }),
                addEventListener: () => {},
                removeEventListener: () => {},
                onmute: null,
                onunmute: null,
                onended: null,
            };
            return {
                getAudioTracks: () => [track],
                getVideoTracks: () => [],
                getTracks: () => [track],
            };
        };
    """)
    page.goto(f"{web_server}/index.html")
    page.wait_for_selector("#status")

    # Assert amber UI warning state
    status_el = page.locator("#status")
    expect(status_el).to_have_text("Mic Muted")
    expect(status_el).to_have_class("status-pill muted")

    state_dot = page.locator("#stateDot")
    expect(state_dot).to_have_class("dot muted")

    # Diagnostics mic status
    diag_mic = page.locator("#diagMic")
    expect(diag_mic).to_contain_text("🔴 Muted")
