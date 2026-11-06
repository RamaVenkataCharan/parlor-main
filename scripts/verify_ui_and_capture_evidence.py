"""Playwright script to verify UI behavior, assert zero outer scrollbar at 1440x900,
verify zero external network requests, zero console errors, and capture evidence screenshots.
"""

import http.server
import json
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "src" / "parlor" / "web"
EVIDENCE_DIR = ROOT / "evidence" / "ui"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


class _WebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, *args):
        pass


def run_verification():
    # 1. Start static server
    server = http.server.HTTPServer(("127.0.0.1", 0), _WebHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base_url = f"http://127.0.0.1:{port}"

    console_errors = []
    network_requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.0
        )
        page = context.new_page()

        # Listen for console and network
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("request", lambda req: network_requests.append(req.url))

        # Mock media devices using real AudioContext MediaStream to satisfy browser native track types
        page.add_init_script("""
            window.navigator.mediaDevices.getUserMedia = async (constraints) => {
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const dest = audioCtx.createMediaStreamDestination();
                const canvas = document.createElement('canvas');
                canvas.width = 1280;
                canvas.height = 720;
                const videoStream = canvas.captureStream ? canvas.captureStream(30) : null;
                const tracks = [...dest.stream.getAudioTracks()];
                if (videoStream) {
                    tracks.push(...videoStream.getVideoTracks());
                }
                return new MediaStream(tracks);
            };
        """)

        print(f"Loading {base_url}/index.html at 1440x900...")
        page.goto(f"{base_url}/index.html", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # ── Test A: Outer Scrollbar Check at 1440x900 ──
        body_scroll_height = page.evaluate("() => document.body.scrollHeight")
        window_height = page.evaluate("() => window.innerHeight")
        portal_scroll_height = page.evaluate("() => document.querySelector('.portal-stack').scrollHeight")
        portal_client_height = page.evaluate("() => document.querySelector('.portal-stack').clientHeight")

        print(f"Viewport Height: {window_height}px, Body ScrollHeight: {body_scroll_height}px")
        print(f"Portal ClientHeight: {portal_client_height}px, Portal ScrollHeight: {portal_scroll_height}px")

        # Zero outer scrollbar: body.scrollHeight should be <= window.innerHeight
        assert body_scroll_height <= window_height + 2, (
            f"Outer scrollbar detected! body.scrollHeight ({body_scroll_height}) > window.innerHeight ({window_height})"
        )
        print(" [PASS] Zero outer scrollbar verified at 1440x900!")

        # Capture Default Diagnostics State
        default_shot = EVIDENCE_DIR / "parlor_1440x900_default.png"
        page.screenshot(path=str(default_shot))
        print(f" Captured: {default_shot}")

        # ── Test B: Demo Mode Verification ──
        print("Toggling Demo Mode...")
        page.evaluate("() => document.getElementById('demoModeToggle').click()")
        page.wait_for_timeout(600)

        sim_badge = page.locator("#simulatedInputBadge")
        assert sim_badge.is_visible(), "SIMULATED INPUT badge should be visible in Demo Mode"

        demo_tags = page.locator(".demo-tag")
        for i in range(demo_tags.count()):
            assert demo_tags.nth(i).is_visible(), f"Demo tag #{i} should be visible in Demo Mode"

        # Check that demo face wireframe is rendered
        face_mini = page.locator("#faceMiniCanvas")
        assert face_mini.is_visible(), "Mini face canvas should be visible when demo face is active"

        demo_shot = EVIDENCE_DIR / "parlor_1440x900_demo_mode.png"
        page.screenshot(path=str(demo_shot))
        print(f" Captured: {demo_shot}")

        # ── Test C: Wellness Overview View Tab ──
        print("Switching to Wellness Tab...")
        wellness_btn = page.locator("#viewWellnessBtn")
        wellness_btn.click()
        page.wait_for_timeout(500)

        wellness_rail = page.locator("#wellnessRail")
        assert wellness_rail.is_visible(), "Wellness rail should be visible"
        diag_rail = page.locator("#diagnosticsRail")
        assert not diag_rail.is_visible(), "Diagnostics rail should be hidden"

        wellness_shot = EVIDENCE_DIR / "parlor_1440x900_wellness_view.png"
        page.screenshot(path=str(wellness_shot))
        print(f" Captured: {wellness_shot}")

        # Switch back to Diagnostics
        diag_btn = page.locator("#viewDiagnosticsBtn")
        diag_btn.click()
        page.wait_for_timeout(500)
        assert diag_rail.is_visible(), "Diagnostics rail should be visible"

        # ── Test D: Mobile Viewport ──
        print("Testing mobile viewport (375x812)...")
        mobile_page = context.new_page()
        mobile_page.set_viewport_size({"width": 375, "height": 812})
        mobile_page.goto(f"{base_url}/index.html", wait_until="networkidle")
        mobile_page.wait_for_timeout(500)

        mobile_shot = EVIDENCE_DIR / "parlor_mobile_375x812.png"
        mobile_page.screenshot(path=str(mobile_shot))
        print(f" Captured: {mobile_shot}")
        mobile_page.close()

        # ── Test E: Zero External Network Requests Audit ──
        print("Auditing network requests for zero external leaks...")
        external_requests = []
        for url in network_requests:
            if url.startswith("data:"):
                continue
            if not (url.startswith(f"http://127.0.0.1:{port}") or url.startswith("ws://127.0.0.1") or url.startswith("ws://localhost")):
                external_requests.append(url)

        print(f"Total network requests observed: {len(network_requests)}")
        print(f"External requests: {len(external_requests)}")
        assert len(external_requests) == 0, f"Privacy violation: observed external requests: {external_requests}"
        print(" [PASS] Zero external requests verified (100% on-device private)!")

        # ── Test F: Zero Console Errors ──
        print("Auditing console errors...")
        # Ignore expected ws connection failure if live server isn't running on port 8000
        filtered_errors = [e for e in console_errors if "WebSocket" not in e and "connect" not in e]
        print(f"Console errors: {len(filtered_errors)}")
        if filtered_errors:
            print("Filtered errors found:", filtered_errors)
        assert len(filtered_errors) == 0, f"Uncaught console errors detected: {filtered_errors}"
        print(" [PASS] Zero console errors verified!")

        browser.close()

    server.shutdown()
    print("\nALL UI VERIFICATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_verification()

