#!/usr/bin/env python3
"""Capture high-resolution screenshots of all UI dialog and active states for evidence."""

import http.server
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


def capture_all():
    server = http.server.HTTPServer(("127.0.0.1", 0), _WebHandler)
    port = server.server_port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base_url = f"http://127.0.0.1:{port}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.goto(f"{base_url}/index.html", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # 1. Settings / Diagnostics Modal
        print("Capturing Settings & Pipeline modal...")
        page.evaluate("() => document.getElementById('diagBtn').click()")
        page.wait_for_timeout(400)
        page.screenshot(path=str(EVIDENCE_DIR / "parlor_settings_modal.png"))
        page.evaluate("() => document.getElementById('diagClose').click()")
        page.wait_for_timeout(300)

        # 2. Intervention Card
        print("Capturing Intervention Card...")
        page.evaluate("""() => {
            if (typeof showInterventionCard === 'function') {
                showInterventionCard({
                    category: 'Guided Breathing',
                    title: 'Guided 4-7-8 Breathing Reset',
                    guidance: 'Observed elevated physiological tension across consecutive cycles.',
                    steps: [
                        'Exhale completely through your mouth.',
                        'Close your mouth and inhale quietly through your nose to a mental count of 4.',
                        'Hold your breath for a count of 7.',
                        'Exhale completely through your mouth to a count of 8.'
                    ],
                    reasoning: 'AU04 brow furrow exceeded baseline (+0.54) with elevated pitch variability for 3 consecutive observation windows.'
                });
            }
        }""")
        page.wait_for_timeout(500)
        page.screenshot(path=str(EVIDENCE_DIR / "parlor_intervention_card.png"))

        # 3. Interactive Breathing Exercise
        print("Capturing 2-Minute Breathing Exercise...")
        page.evaluate("() => { if (typeof startBreathingExercise === 'function') startBreathingExercise(120); }")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "parlor_breathing_exercise.png"))
        page.evaluate("() => { if (typeof stopBreathingExercise === 'function') stopBreathingExercise(); }")

        browser.close()

    server.shutdown()
    print("All additional UI states captured successfully in evidence/ui/!")


if __name__ == "__main__":
    capture_all()

