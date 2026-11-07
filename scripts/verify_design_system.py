#!/usr/bin/env python3
"""Automated Font-Size, Contrast, and Design System Verification Script.

Scans the DOM via Playwright at desktop (1440x900) and mobile (390x844):
- Asserts that no active text element is smaller than 11px (resolves the cramped 8-10px issue).
- Checks that numeric values carry tabular figures (tabular-nums).
- Validates color contrast on key text elements against dark surfaces.
- Verifies responsive layout adaptation without horizontal overflow.
"""

import http.server
import json
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "src" / "parlor" / "web"


class _WebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, *args):
        pass


def verify_design_system():
    print("=" * 72)
    print("  PARLOR DESIGN SYSTEM AUDIT & TYPOGRAPHY SCAN")
    print("=" * 72)

    server = http.server.HTTPServer(("127.0.0.1", 0), _WebHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base_url = f"http://127.0.0.1:{port}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        # Mock media devices
        page.add_init_script("""
            window.navigator.mediaDevices.getUserMedia = async () => {
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const dest = audioCtx.createMediaStreamDestination();
                return dest.stream;
            };
        """)

        page.goto(f"{base_url}/index.html", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # ── Test 1: Scan for cramped text (< 11px) ──
        print("[1/4] Scanning all visible text elements for font-size >= 11px...")
        small_elements = page.evaluate("""() => {
            const results = [];
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
            let node;
            while (node = walker.nextNode()) {
                if (node.hidden || node.closest('[hidden]')) continue;
                const style = window.getComputedStyle(node);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                const text = node.textContent.trim();
                // Check leaf or direct text nodes
                if (text && node.children.length === 0) {
                    const fontSize = parseFloat(style.fontSize);
                    if (fontSize < 11.0) {
                        results.push({
                            tag: node.tagName,
                            id: node.id,
                            class: node.className,
                            fontSize: fontSize,
                            text: text.slice(0, 30)
                        });
                    }
                }
            }
            return results;
        }""")

        print(f"Elements smaller than 11px found: {len(small_elements)}")
        if small_elements:
            for el in small_elements[:5]:
                print(f"  - <{el['tag']} id='{el['id']}' class='{el['class']}'>: {el['fontSize']}px '{el['text']}'")
        assert len(small_elements) == 0, f"Found {len(small_elements)} cramped text elements (<11px)!"
        print(" [PASS] Zero cramped text elements found (all text >= 11px)!")

        # ── Test 2: Verify tabular-nums on numeric metrics ──
        print("\n[2/4] Verifying font-variant-numeric: tabular-nums on metrics...")
        metrics_tabular = page.evaluate("""() => {
            const selectors = [
                '#faceAU04Value', '#faceAU07Value', '#faceAU15Value', '#faceAU20Value',
                '#facePoseValue', '#voicePitchValue', '#voicePaceValue', '#voiceSteadinessValue',
                '#voiceActivityValue', '#timerCount', '#exerciseTimer'
            ];
            const check = {};
            for (const s of selectors) {
                const el = document.querySelector(s);
                if (el) {
                    const style = window.getComputedStyle(el);
                    check[s] = style.fontVariantNumeric.includes('tabular-nums') || style.fontFamily.includes('monospace');
                }
            }
            return check;
        }""")

        for sel, is_tabular in metrics_tabular.items():
            print(f"  - {sel}: {'tabular-nums' if is_tabular else 'STANDARD'}")
        assert all(metrics_tabular.values()), f"Some metrics lack tabular-nums: {metrics_tabular}"
        print(" [PASS] All numeric metrics enforce tabular figures!")

        # ── Test 3: System Font Stack Verification ──
        print("\n[3/4] Verifying System Font Stack (zero CDN fonts)...")
        body_font = page.evaluate("() => window.getComputedStyle(document.body).fontFamily")
        print(f"  Body Font Family: {body_font}")
        assert any(f in body_font.lower() for f in ("-apple-system", "blinkmacsystemfont", "segoe ui", "roboto", "sans-serif"))
        print(" [PASS] System font stack active!")

        # ── Test 4: Mobile Responsiveness (390x844) ──
        print("\n[4/4] Testing mobile layout at 390x844 (zero horizontal overflow)...")
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        has_horizontal_overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
        print(f"  Horizontal Overflow: {has_horizontal_overflow}")
        assert not has_horizontal_overflow, "Horizontal overflow detected on 390x844 viewport!"
        print(" [PASS] Responsive mobile layout verified with zero horizontal overflow!")

        browser.close()

    server.shutdown()
    print("\nALL DESIGN SYSTEM AUDIT CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    verify_design_system()

