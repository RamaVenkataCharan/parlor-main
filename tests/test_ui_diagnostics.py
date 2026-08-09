"""Playwright UI regression test for Diagnostics button (app.js / index.html):
Verifies that the click handler for #diagBtn is bound on DOMContentLoaded so clicking
the button toggles #diagPanel reliably regardless of camera/mic initialization timing.
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


def test_diagnostics_button_clicks_reliably_during_camera_init(page: Page, web_server: str):
    """Verify that clicking #diagBtn toggles #diagPanel even when startCamera() / getUserMedia
    is still pending or stalled.
    """
    # Mock getUserMedia to hang indefinitely
    page.add_init_script("""
        window.navigator.mediaDevices.getUserMedia = () => new Promise(() => {});
    """)
    page.goto(f"{web_server}/index.html", wait_until="domcontentloaded")

    diag_btn = page.locator("#diagBtn")
    diag_panel = page.locator("#diagPanel")

    # Panel should initially be hidden
    expect(diag_panel).to_have_attribute("hidden", "")

    # Click diagnostics button immediately during camera init
    diag_btn.click()

    # Panel must now be visible (hidden attribute removed)
    expect(diag_panel).not_to_have_attribute("hidden", "")
    expect(diag_btn).to_have_attribute("aria-expanded", "true")
