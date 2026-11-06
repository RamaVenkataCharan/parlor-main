#!/usr/bin/env python3
"""Interactive Verification Script: Live Webcam Facial Signal & Action Unit Validation.

REQUIRES HUMAN: An operator must sit in front of the webcam and perform 4 facial expressions:
1. Neutral Expression (calm, resting face, looking straight at camera)
2. Brow Furrow (contract corrugator supercilii — pull inner brows together and down)
3. Eye Squint (tighten eyelids — contract orbicularis oculi)
4. Lip Stretch (stretch mouth horizontally wide — contract risorius)

Expected validation criteria:
- Neutral head pose: Pitch, Yaw, Roll within +/- 15 degrees.
- Prompts produce distinct, elevated Action Unit signals relative to baseline:
  * Brow Furrow -> AU04 significantly elevated (> 0.35)
  * Eye Squint  -> AU07 significantly elevated (> 0.35)
  * Lip Stretch -> AU20 significantly elevated (> 0.35)
"""

import sys
import time
import numpy as np

try:
    import cv2
except ImportError:
    print("Error: OpenCV (cv2) is required. Run 'uv pip install opencv-python'.")
    sys.exit(1)

from parlor.facial import FacialExtractor


PROMPTS = [
    {
        "id": "neutral",
        "title": "1. NEUTRAL EXPRESSION",
        "instruction": "Look directly at the camera with a relaxed, resting face for 5 seconds.",
        "target_au": None,
    },
    {
        "id": "brow_furrow",
        "title": "2. BROW FURROW",
        "instruction": "Frown and pull your inner eyebrows tightly together and down for 5 seconds.",
        "target_au": "AU04",
    },
    {
        "id": "eye_squint",
        "title": "3. EYE SQUINT",
        "instruction": "Narrow and squint your eyes tightly (lid tightening) for 5 seconds.",
        "target_au": "AU07",
    },
    {
        "id": "lip_stretch",
        "title": "4. LIP STRETCH",
        "instruction": "Stretch your lips horizontally wide as in a tight grimace for 5 seconds.",
        "target_au": "AU20",
    },
]


def run_check():
    print("=" * 72)
    print("  PARLOR LIVE FACIAL SIGNAL & ACTION UNIT CHECK")
    print("  Status: REQUIRES HUMAN operator to perform facial prompts")
    print("=" * 72)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("\n[ERROR] Could not open webcam device index 0.")
        print("REQUIRES HUMAN: Ensure a USB webcam or integrated camera is connected and permitted.")
        return

    extractor = FacialExtractor()
    if not extractor.mp_available:
        print("\n[ERROR] MediaPipe FaceMesh is not available in current environment.")
        cap.release()
        return

    results_table = []

    try:
        for p in PROMPTS:
            print("\n" + "-" * 72)
            print(f"PROMPT: {p['title']}")
            print(f"Instruction: {p['instruction']}")
            print("Get ready! Starting in 3 seconds...")
            for countdown in range(3, 0, -1):
                print(f"  {countdown}...")
                time.sleep(1.0)

            print("  --> RECORDING 5 SECONDS (Hold expression)...")
            samples = []
            t_start = time.time()
            while time.time() - t_start < 5.0:
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.05)
                    continue

                res = extractor.extract(frame)
                if res.get("face_detected"):
                    samples.append(res)
                time.sleep(0.08)  # ~12 FPS sampling

            if not samples:
                print("  [WARNING] No face detected during observation period!")
                results_table.append({
                    "prompt": p["title"],
                    "samples": 0,
                    "pitch": "—",
                    "yaw": "—",
                    "roll": "—",
                    "au04": "—",
                    "au07": "—",
                    "au15": "—",
                    "au20": "—",
                })
                continue

            mean_pitch = float(np.mean([s["head_pitch"] for s in samples]))
            mean_yaw = float(np.mean([s["head_yaw"] for s in samples]))
            mean_roll = float(np.mean([s["head_roll"] for s in samples]))
            max_au04 = float(np.percentile([s["au04_brow_furrow"] for s in samples], 80))
            max_au07 = float(np.percentile([s["au07_lid_tightener"] for s in samples], 80))
            max_au15 = float(np.percentile([s["au15_lip_depressor"] for s in samples], 80))
            max_au20 = float(np.percentile([s["au20_lip_stretcher"] for s in samples], 80))

            results_table.append({
                "prompt": p["title"],
                "samples": len(samples),
                "pitch": f"{mean_pitch:+.1f}°",
                "yaw": f"{mean_yaw:+.1f}°",
                "roll": f"{mean_roll:+.1f}°",
                "au04": f"{max_au04:.2f}",
                "au07": f"{max_au07:.2f}",
                "au15": f"{max_au15:.2f}",
                "au20": f"{max_au20:.2f}",
            })
            print(f"  Completed: collected {len(samples)} valid frames.")

    finally:
        cap.release()

    # Print Summary Markdown Table
    print("\n" + "=" * 72)
    print("  MEASURED FACIAL SIGNAL TABLE")
    print("=" * 72)
    header = f"| {'Prompt':<24} | {'Pose (P / Y / R)':<18} | {'AU04':<6} | {'AU07':<6} | {'AU15':<6} | {'AU20':<6} |"
    divider = f"|{'-'*26}|{'-'*20}|{'-'*8}|{'-'*8}|{'-'*8}|{'-'*8}|"
    print(header)
    print(divider)
    for r in results_table:
        pose_str = f"{r['pitch']} / {r['yaw']} / {r['roll']}"
        print(f"| {r['prompt']:<24} | {pose_str:<18} | {r['au04']:<6} | {r['au07']:<6} | {r['au15']:<6} | {r['au20']:<6} |")
    print(divider)
    print("\nVerification Criteria Check:")
    if results_table:
        neu = results_table[0]
        print(f"- Neutral Head Pose: {neu['pitch']} / {neu['yaw']} / {neu['roll']}")
    print("=" * 72)


if __name__ == "__main__":
    run_check()

