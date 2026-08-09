"""
step3_audio_features_mock.py — Mock continuous features pipeline for headless testing.
Writes synthetic/simulated stress features to stress_features.json every 8 seconds.
"""

import json
import os
import random
import time

SHARED_FILE_PATH = "shared_state/latest_features.json"
TEMP_FILE_PATH = "shared_state/latest_features.json.tmp"


def write_features_atomically(result: dict):
    os.makedirs("shared_state", exist_ok=True)
    nested = {
        "timestamp": time.time(),
        "face": {
            "face_detected": False,
            "au04_brow_furrow": 0.0,
            "au07_lid_tightener": 0.0,
            "au15_lip_depressor": 0.0,
            "au20_lip_stretcher": 0.0,
            "ear": 0.3
        },
        "audio": {
            "voice_detected": result.get("voice_detected", True),
            "pitch_delta": 0.0,
            "pitch_variance": result.get("pitch_variance", 0.0),
            "jitter": result.get("energy_jitter", 0.0),
            "shimmer": 0.0,
            "pause_ratio": result.get("speech_rate_proxy", 0.0),
            "vocal_tension": 0.0
        }
    }
    with open(TEMP_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(nested, f, indent=2)
    os.replace(TEMP_FILE_PATH, SHARED_FILE_PATH)


def main():
    print("Starting continuous mock features writer (updates every 8s)...")
    cycle = 1
    try:
        while True:
            # Vary values slightly to simulate dynamic voice stress
            pitch_var = round(random.uniform(10.0, 50.0) if cycle % 2 == 0 else random.uniform(0.0, 2.0), 3)
            speech_rate = round(random.uniform(3.0, 8.0), 3)
            jitter = round(random.uniform(0.1, 0.8) if cycle % 2 == 0 else random.uniform(0.01, 0.05), 4)

            res = {
                "voice_detected": True,
                "pitch_variance": pitch_var,
                "speech_rate_proxy": speech_rate,
                "energy_jitter": jitter
            }
            write_features_atomically(res)
            print(f"Cycle {cycle}: Wrote features (pitch_var={pitch_var}, speech_rate={speech_rate}, jitter={jitter})")
            cycle += 1
            time.sleep(8)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
