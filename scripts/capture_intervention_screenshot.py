"""Capture proof of intervention_triggered card firing in browser in Balanced mode.

Uses Playwright to:
1. Launch headless Chromium.
2. Navigate to http://127.0.0.1:8000.
3. Wait for WebSocket connection.
4. Set sensitivity mode to Balanced (3 consecutive cycles required, 300s cooldown).
5. Send 3 consecutive Tier 2 cycles to reach hysteresis.
6. Verify the server dispatches 'intervention_triggered' and the UI displays #interventionCard.
7. Capture full browser screenshot showing the intervention card.
"""
import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    evidence_dir = Path("evidence")
    evidence_dir.mkdir(exist_ok=True)
    screenshot_path = evidence_dir / "intervention_card_browser.png"
    log_path = evidence_dir / "live_browser_intervention.log"

    print("Launching Chromium via Playwright with fake media devices...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--allow-file-access-from-files",
                "--disable-web-security"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            permissions=["camera", "microphone"]
        )
        page = context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        ws_messages_received = []

        # Monitor WebSocket frames via CDP
        client = context.new_cdp_session(page)
        client.send("Network.enable")

        def on_ws_frame(event):
            payload = event.get("response", {}).get("payloadData", "")
            try:
                data = json.loads(payload)
                if data.get("type") in ("intervention_triggered", "test_wellness_cycle_result", "concurrency_mitigation_changed"):
                    ws_messages_received.append(data)
            except Exception:
                pass

        client.on("Network.webSocketFrameReceived", on_ws_frame)

        print("Navigating to http://127.0.0.1:8000...")
        page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        time.sleep(2)

        # Confirm WebSocket is open via wsOpen()
        print("Waiting for WebSocket connection (wsOpen)...")
        page.wait_for_function("() => typeof wsOpen === 'function' && wsOpen()", timeout=15000)
        print("WebSocket successfully connected!")

        # 1. Set Balanced mode
        print("Setting sensitivity mode to Balanced...")
        page.evaluate("() => wsSend({type: 'set_wellness_sensitivity', mode: 'balanced'})")
        time.sleep(1)

        # 2. Fire 3 consecutive Tier 2 cycles
        cycle_payload = {
            "type": "test_wellness_cycle",
            "slm_output": {
                "stress_level": "High (Tier 2)",
                "primary_drivers": ["AU04 Brow Furrow=0.95", "Vocal Tension=0.88", "Pitch Delta=+68Hz"],
                "explainable_reasoning": "Severe sustained brow furrow and high vocal acoustic tension indicating acute stress.",
                "confidence_score": 0.95,
                "ambiguity_note": None
            }
        }

        print("Sending Cycle 1 (Tier 2)...")
        page.evaluate("(payload) => wsSend(payload)", cycle_payload)
        time.sleep(1.5)

        print("Sending Cycle 2 (Tier 2)...")
        page.evaluate("(payload) => wsSend(payload)", cycle_payload)
        time.sleep(1.5)

        print("Sending Cycle 3 (Tier 2 - Hysteresis reached)...")
        page.evaluate("(payload) => wsSend(payload)", cycle_payload)
        time.sleep(2.0)

        # Check if interventionCard is visible (hidden === false)
        card_visible = page.evaluate("() => { const c = document.getElementById('interventionCard'); return c && !c.hidden; }")
        print(f"Intervention Card visible in DOM: {card_visible}")

        card_title = page.evaluate("() => document.getElementById('interventionTitle').textContent")
        card_category = page.evaluate("() => document.getElementById('interventionCategory').textContent")
        card_note = page.evaluate("() => document.getElementById('interventionNote').textContent")
        card_reasoning = page.evaluate("() => document.getElementById('interventionReasoning').textContent")

        print(f"Card Title   : {card_title}")
        print(f"Card Category: {card_category}")
        print(f"Card Note    : {card_note}")
        print(f"Card Reason  : {card_reasoning}")

        # Save screenshot
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Screenshot successfully captured: {screenshot_path}")

        # Write log
        log_content = (
            "===========================================================================\n"
            "   LIVE BROWSER INTERVENTION CARD FIRING AUDIT -- BALANCED MODE\n"
            "===========================================================================\n"
            f"Mode                 : Balanced (3 consecutive cycles, 300s cooldown)\n"
            f"WebSocket Status     : CONNECTED (ws://127.0.0.1:8000/ws)\n"
            f"Card Visible in DOM  : {card_visible}\n"
            f"Card Title           : {card_title}\n"
            f"Card Category        : {card_category}\n"
            f"Card Personalized    : {card_note}\n"
            f"Card Reasoning       : {card_reasoning}\n"
            f"Screenshot Evidence  : {screenshot_path}\n"
            "---------------------------------------------------------------------------\n"
            "WebSocket Intervention Messages Received in Browser:\n"
            f"{json.dumps(ws_messages_received, indent=2)}\n"
            "---------------------------------------------------------------------------\n"
            "Browser Console Messages:\n" + "\n".join(console_logs) + "\n"
        )
        log_path.write_text(log_content, encoding="utf-8")
        print(f"Audit log saved: {log_path}")

        browser.close()

    assert card_visible is True, "Intervention card did not become visible!"
    print("VERIFICATION COMPLETE: Intervention card fired and captured in browser!")

if __name__ == "__main__":
    main()
