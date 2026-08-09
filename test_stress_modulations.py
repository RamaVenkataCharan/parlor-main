"""
test_stress_modulations.py — Verifies that the SLM responds dynamically to low vs high stress biomarker inputs.
"""

import json
import time
from person_b_slm_reasoning import call_slm


def run_test():
    # 1. Calm/Neutral features
    calm_vector = {
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
            "voice_detected": True,
            "pitch_delta": 0.0,
            "pitch_variance": 0.5,
            "jitter": 0.015,
            "shimmer": 0.0,
            "pause_ratio": 5.3,
            "vocal_tension": 0.0
        }
    }

    print("--- 1. CALLING SLM WITH CALM FEATURES ---")
    calm_res = call_slm(calm_vector)
    print(f"Stress Level: {calm_res['stress_level']}")
    print(f"Reasoning: {calm_res['reasoning']}")
    print(f"Intervention: {calm_res['intervention']}")

    # 2. Agitated/Stressed features
    agitated_vector = {
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
            "voice_detected": True,
            "pitch_delta": 0.0,
            "pitch_variance": 95.8,
            "jitter": 0.85,
            "shimmer": 0.0,
            "pause_ratio": 14.5,
            "vocal_tension": 0.0
        }
    }

    print("\n--- 2. CALLING SLM WITH AGITATED FEATURES ---")
    agitated_res = call_slm(agitated_vector, history=[calm_res])
    print(f"Stress Level: {agitated_res['stress_level']}")
    print(f"Reasoning: {agitated_res['reasoning']}")
    print(f"Intervention: {agitated_res['intervention']}")

    # 3. Moderate features
    moderate_vector = {
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
            "voice_detected": True,
            "pitch_delta": 0.0,
            "pitch_variance": 10.0,
            "jitter": 0.12,
            "shimmer": 0.0,
            "pause_ratio": 8.5,
            "vocal_tension": 0.0
        }
    }

    print("\n--- 3. CALLING SLM WITH MODERATE FEATURES ---")
    moderate_res = call_slm(moderate_vector, history=[calm_res])
    print(f"Stress Level: {moderate_res['stress_level']}")
    print(f"Reasoning: {moderate_res['reasoning']}")
    print(f"Intervention: {moderate_res['intervention']}")


if __name__ == "__main__":
    run_test()
