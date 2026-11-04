"""Reproduction script for Startup WebSocket connection error & UI behavior.

Captures Chrome DevTools console, WebSocket lifecycle, toast stack, and status badge.
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = ROOT / "evidence" / "launcher"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def main():
    events = {
        "console": [],
        "ws_opened": [],
        "ws_closed": [],
        "ws_frames_sent": [],
        "ws_frames_received": [],
        "ws_errors": [],
        "toasts": [],
        "status_badge": None,
    }

    with sync_playwright() as p:
        # Launch Chromium (DevTools enabled)
        browser = p.chromium.launch(headless=True)
        # Note: Do not grant camera/mic permissions automatically to reproduce user cold start state
        context = browser.new_context()
        page = context.new_page()

        # Capture console
        page.on("console", lambda msg: events["console"].append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }))

        # Capture WebSockets
        def on_websocket(ws):
            events["ws_opened"].append(ws.url)
            ws.on("framesent", lambda frame: events["ws_frames_sent"].append(frame))
            ws.on("framereceived", lambda frame: events["ws_frames_received"].append(frame))
            ws.on("close", lambda: events["ws_closed"].append({"url": ws.url, "time": time.time()}))
            ws.on("socketerror", lambda err: events["ws_errors"].append(str(err)))

        page.on("websocket", on_websocket)

        print("[DEVTOOLS] Navigating to http://localhost:8000 ...")
        page.goto("http://localhost:8000")

        # Wait 8 seconds to capture reconnect cycles and toast stacking
        print("[DEVTOOLS] Monitoring page for 8 seconds to capture toasts and reconnect loop...")
        page.wait_for_timeout(8000)

        # Inspect status badge
        try:
            status_el = page.query_selector("#status")
            events["status_badge"] = status_el.inner_text() if status_el else None
        except Exception as e:
            events["status_badge"] = f"Error: {e}"

        # Inspect toasts
        try:
            toast_els = page.query_selector_all(".toast-banner")
            for t in toast_els:
                events["toasts"].append(t.inner_text().replace("✕", "").strip())
        except Exception as e:
            events["toasts"].append(f"Error: {e}")

        # Capture screenshot
        screenshot_path = EVIDENCE_DIR / "reproduction_ws_error.png"
        page.screenshot(path=str(screenshot_path))
        print(f"[DEVTOOLS] Screenshot captured: {screenshot_path}")

        browser.close()

    log_path = EVIDENCE_DIR / "reproduction_ws_error.log"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== PARLOR WEBSOCKET STARTUP REPRODUCTION AUDIT ===\n")
        f.write(f"Target URL: http://localhost:8000\n")
        f.write(f"Status Badge Text: {events['status_badge']}\n\n")
        f.write(f"--- Toast Stack (Count: {len(events['toasts'])}) ---\n")
        for i, toast in enumerate(events["toasts"], 1):
            f.write(f"  [{i}] {toast}\n")
        f.write(f"\n--- WebSocket Events ---\n")
        f.write(f"  Opened: {events['ws_opened']}\n")
        f.write(f"  Closed: {events['ws_closed']}\n")
        f.write(f"  Errors: {events['ws_errors']}\n")
        f.write(f"  Frames Sent: {len(events['ws_frames_sent'])}\n")
        f.write(f"  Frames Received: {len(events['ws_frames_received'])}\n\n")
        f.write(f"--- Console Logs (Total: {len(events['console'])}) ---\n")
        for entry in events["console"]:
            f.write(f"  [{entry['type'].upper()}] {entry['text']}\n")

    print(f"[DEVTOOLS] Reproduction log saved: {log_path}")
    print(f"Status Badge: {events['status_badge']}")
    print(f"Toasts captured ({len(events['toasts'])}): {events['toasts']}")


if __name__ == "__main__":
    main()

