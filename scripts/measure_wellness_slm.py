"""Empirical Benchmark for Small Language Model (SLM) Affective Wellness Reasoning.

Sends 30 distinct, realistic multimodal feature vectors to the local Gemma 4 E2B Q4_0
inference engine running under llama-server on this machine.
Measures latency per call with high precision (time.perf_counter()), parses structured
JSON responses, and outputs raw records to evidence/wellness_slm_latency.csv.
"""

import csv
import json
import os
import sys
import time
from typing import List, Dict, Any
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from parlor import llama
from parlor.fusion import FeatureFusionEngine, EXPLAINABLE_SYSTEM_PROMPT

EVIDENCE_DIR = os.path.join(BASE_DIR, "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)


def generate_30_test_vectors() -> List[Dict[str, Any]]:
    """Generates 30 realistic, deterministic feature vectors across 3 stress states."""
    vectors = []

    # 1. 10 Calm Baseline Vectors
    for i in range(10):
        vectors.append({
            "window_samples": 5,
            "condition": "Calm Baseline",
            "face_detected": True,
            "face_confidence": round(0.92 + 0.05 * (i % 3) / 2.0, 2),
            "au04_brow_furrow": round(0.05 + 0.04 * (i % 4) / 3.0, 3),
            "au07_lid_tightener": round(0.08 + 0.03 * (i % 3) / 2.0, 3),
            "au15_lip_depressor": round(0.04 + 0.02 * (i % 3) / 2.0, 3),
            "au20_lip_stretcher": round(0.06 + 0.03 * (i % 4) / 3.0, 3),
            "ear": round(0.31 + 0.02 * (i % 3) / 2.0, 3),
            "head_pitch": 0.0,
            "head_yaw": 0.0,
            "head_roll": 0.0,
            "speech_detected": True,
            "rms_energy": 0.045,
            "f0_mean_hz": round(146.0 + (i % 5) * 1.5, 1),
            "f0_baseline_hz": 145.0,
            "f0_delta_hz": round(1.0 + (i % 5) * 1.5, 1),
            "f0_std_hz": round(8.5 + (i % 4) * 0.8, 1),
            "jitter_local_pct": round(0.72 + (i % 5) * 0.08, 2),
            "shimmer_local_pct": round(1.35 + (i % 4) * 0.12, 2),
            "pause_ratio": 0.42,
            "vocal_tension_index": 0.28
        })

    # 2. 10 Moderate / Elevated Engagement Vectors
    for i in range(10):
        vectors.append({
            "window_samples": 5,
            "condition": "Moderate Engagement",
            "face_detected": True,
            "face_confidence": round(0.94 + 0.04 * (i % 2), 2),
            "au04_brow_furrow": round(0.28 + 0.08 * (i % 4) / 3.0, 3),
            "au07_lid_tightener": round(0.32 + 0.06 * (i % 3) / 2.0, 3),
            "au15_lip_depressor": round(0.12 + 0.04 * (i % 3) / 2.0, 3),
            "au20_lip_stretcher": round(0.22 + 0.05 * (i % 4) / 3.0, 3),
            "ear": 0.29,
            "head_pitch": 0.0,
            "head_yaw": 0.0,
            "head_roll": 0.0,
            "speech_detected": True,
            "rms_energy": 0.082,
            "f0_mean_hz": round(175.0 + (i % 6) * 3.5, 1),
            "f0_baseline_hz": 145.0,
            "f0_delta_hz": round(30.0 + (i % 6) * 3.5, 1),
            "f0_std_hz": round(18.2 + (i % 4) * 1.5, 1),
            "jitter_local_pct": round(2.15 + (i % 5) * 0.22, 2),
            "shimmer_local_pct": round(3.85 + (i % 4) * 0.35, 2),
            "pause_ratio": 0.22,
            "vocal_tension_index": 0.48
        })

    # 3. 10 Acute Cognitive Stress Vectors
    for i in range(10):
        vectors.append({
            "window_samples": 5,
            "condition": "Acute Stress",
            "face_detected": True,
            "face_confidence": 0.96,
            "au04_brow_furrow": round(0.68 + 0.18 * (i % 4) / 3.0, 3),
            "au07_lid_tightener": round(0.55 + 0.12 * (i % 3) / 2.0, 3),
            "au15_lip_depressor": round(0.38 + 0.08 * (i % 3) / 2.0, 3),
            "au20_lip_stretcher": round(0.45 + 0.10 * (i % 4) / 3.0, 3),
            "ear": 0.22,
            "head_pitch": 0.0,
            "head_yaw": 0.0,
            "head_roll": 0.0,
            "speech_detected": True,
            "rms_energy": 0.095,
            "f0_mean_hz": round(212.0 + (i % 5) * 6.0, 1),
            "f0_baseline_hz": 145.0,
            "f0_delta_hz": round(67.0 + (i % 5) * 6.0, 1),
            "f0_std_hz": round(34.5 + (i % 4) * 3.2, 1),
            "jitter_local_pct": round(5.80 + (i % 5) * 0.55, 2),
            "shimmer_local_pct": round(12.40 + (i % 4) * 1.10, 2),
            "pause_ratio": 0.12,
            "vocal_tension_index": 0.82
        })

    return vectors


def run_benchmark(port: int = 8081) -> str:
    fusion = FeatureFusionEngine()
    vectors = generate_30_test_vectors()
    out_csv = os.path.join(EVIDENCE_DIR, "wellness_slm_latency.csv")

    print("=" * 75)
    print("      RUNNING 30-CYCLE SLM WELLNESS REASONING BENCHMARK")
    print(f" Target Model : Gemma 4 E2B Q4_0 (llama-server on port {port})")
    print(f" Evidence CSV : {out_csv}")
    print("=" * 75)

    # Warm-up call
    warmup_prompt = fusion.format_prompt(vectors[0])
    try:
        llama.chat_blocking(
            messages=[
                {"role": "system", "content": EXPLAINABLE_SYSTEM_PROMPT},
                {"role": "user", "content": warmup_prompt}
            ],
            max_tokens=220,
            temperature=0.1
        )
    except Exception as e:
        print(f"[WARMUP ERROR] Could not contact llama-server: {e}", file=sys.stderr)

    latencies = []
    records = []

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "call_index", "timestamp_iso", "condition", "duration_sec", "au04",
            "f0_delta_hz", "jitter_pct", "shimmer_pct", "stress_level",
            "confidence_score", "reasoning_snippet"
        ])

        for idx, vec in enumerate(vectors, 1):
            prompt = fusion.format_prompt(vec)
            messages = [
                {"role": "system", "content": EXPLAINABLE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]

            t0 = time.perf_counter()
            raw_response = llama.chat_blocking(
                messages=messages,
                max_tokens=220,
                temperature=0.1
            )
            t1 = time.perf_counter()

            duration_s = t1 - t0
            latencies.append(duration_s)
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

            # Parse JSON response
            cleaned = raw_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            stress_level = "Unknown"
            confidence = 0.0
            reasoning = ""
            try:
                parsed = json.loads(cleaned.strip())
                stress_level = parsed.get("stress_level", "Unknown")
                confidence = float(parsed.get("confidence_score", 0.0))
                reasoning = parsed.get("explainable_reasoning", "").replace("\n", " ")[:100]
            except Exception:
                reasoning = raw_response.replace("\n", " ")[:100]

            writer.writerow([
                idx,
                now_iso,
                vec["condition"],
                f"{duration_s:.4f}",
                vec["au04_brow_furrow"],
                vec["f0_delta_hz"],
                vec["jitter_local_pct"],
                vec["shimmer_local_pct"],
                stress_level,
                f"{confidence:.2f}",
                f'"{reasoning}"'
            ])
            print(f"[{idx}/30] Latency: {duration_s:.3f}s | Condition: {vec['condition']:<20} | Inferred: {stress_level}")

    mean_s = np.mean(latencies)
    p50_s = np.median(latencies)
    p95_s = np.percentile(latencies, 95)
    max_s = np.max(latencies)

    print("=" * 75)
    print(" SLM WELLNESS REASONING LATENCY RESULTS (30 CALLS):")
    print(f"  Mean Latency : {mean_s:.3f} s")
    print(f"  p50 (Median) : {p50_s:.3f} s")
    print(f"  p95          : {p95_s:.3f} s")
    print(f"  Max Latency  : {max_s:.3f} s")
    print(f"  5.0s Budget  : {'MET (+{:.3f}s margin)'.format(5.0 - p95_s) if p95_s <= 5.0 else 'EXCEEDED'}")
    print("=" * 75)
    return out_csv


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    run_benchmark(port)
