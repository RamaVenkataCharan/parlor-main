"""Fine-grained Tier 2 Reachability Sweep against live Gemma 4 E2B IT q4_0.

Tests intermediate vectors between V09 and V10, varying:
1. Both modalities (co-occurring facial + vocal strain)
2. Facial AU only (extreme facial strain with calm voice)
3. Vocal only (extreme vocal strain with calm face)

Each vector is evaluated with 3 repeats against the live llama-server.
Outputs:
- evidence/tier2_reachability_sweep.csv
- evidence/tier2_reachability_sweep.json
"""

import csv
import json
import time
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from parlor import llama
from parlor.fusion import FeatureFusionEngine, EXPLAINABLE_SYSTEM_PROMPT

vectors = [
    # --- Both modalities varied (interpolation between V09 and V10) ---
    {"group": "both", "id": "B01_V09", "au04": 0.92, "au07": 0.86, "f0_delta": 78.0, "jitter": 4.8, "tension": 0.88},
    {"group": "both", "id": "B02_Mid1", "au04": 0.93, "au07": 0.88, "f0_delta": 81.0, "jitter": 5.0, "tension": 0.89},
    {"group": "both", "id": "B03_Mid2", "au04": 0.94, "au07": 0.90, "f0_delta": 84.0, "jitter": 5.2, "tension": 0.91},
    {"group": "both", "id": "B04_Mid3", "au04": 0.95, "au07": 0.91, "f0_delta": 86.0, "jitter": 5.3, "tension": 0.92},
    {"group": "both", "id": "B05_Mid4", "au04": 0.96, "au07": 0.92, "f0_delta": 88.0, "jitter": 5.4, "tension": 0.93},
    {"group": "both", "id": "B06_Mid5", "au04": 0.97, "au07": 0.94, "f0_delta": 90.0, "jitter": 5.5, "tension": 0.94},
    {"group": "both", "id": "B07_V10", "au04": 0.98, "au07": 0.95, "f0_delta": 92.0, "jitter": 5.6, "tension": 0.95},

    # --- AU Only varied (Voice held at calm baseline) ---
    {"group": "au_only", "id": "AU_01", "au04": 0.92, "au07": 0.86, "f0_delta": 5.0, "jitter": 0.9, "tension": 0.25},
    {"group": "au_only", "id": "AU_02", "au04": 0.95, "au07": 0.91, "f0_delta": 5.0, "jitter": 0.9, "tension": 0.25},
    {"group": "au_only", "id": "AU_03", "au04": 0.98, "au07": 0.95, "f0_delta": 5.0, "jitter": 0.9, "tension": 0.25},

    # --- Voice Only varied (AU held at calm baseline) ---
    {"group": "voice_only", "id": "VO_01", "au04": 0.08, "au07": 0.05, "f0_delta": 78.0, "jitter": 4.8, "tension": 0.88},
    {"group": "voice_only", "id": "VO_02", "au04": 0.08, "au07": 0.05, "f0_delta": 86.0, "jitter": 5.3, "tension": 0.92},
    {"group": "voice_only", "id": "VO_03", "au04": 0.08, "au07": 0.05, "f0_delta": 92.0, "jitter": 5.6, "tension": 0.95},
]

def make_prompt(v):
    fe = FeatureFusionEngine()
    face = {
        "face_detected": True, "confidence": 0.95,
        "au04_brow_furrow": v["au04"], "au07_lid_tightener": v["au07"],
        "au15_lip_depressor": round(v["au04"] * 0.5, 2),
        "au20_lip_stretcher": round(v["au04"] * 0.6, 2),
        "ear": 0.30, "head_pitch": 0.0, "head_yaw": 0.0, "head_roll": 0.0
    }
    vocal = {
        "speech_detected": True, "rms_energy": 0.08,
        "f0_mean_hz": round(145.0 + v["f0_delta"], 1),
        "f0_std_hz": round(15.0 + v["f0_delta"] * 0.3, 1),
        "jitter_local": v["jitter"], "shimmer_local": round(v["jitter"] * 1.1, 2),
        "pause_ratio": 0.35, "vocal_tension_index": v["tension"]
    }
    fe.add_frame(face, vocal)
    return fe.format_prompt()

def main():
    print(f"=== Starting Tier 2 Reachability Sweep ({len(vectors)} vectors x 3 repeats = {len(vectors)*3} evaluations) ===")
    results = []
    
    csv_rows = []
    total_calls = len(vectors) * 3
    call_idx = 0

    for v in vectors:
        prompt_str = make_prompt(v)
        for rep in range(1, 4):
            call_idx += 1
            t0 = time.perf_counter()
            raw = llama.chat_blocking(
                messages=[
                    {"role": "system", "content": EXPLAINABLE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_str}
                ],
                max_tokens=512,
                temperature=0.1
            )
            lat = time.perf_counter() - t0
            
            # Parse JSON
            cleaned = raw.strip()
            if "```json" in cleaned:
                cleaned = cleaned[cleaned.find("```json") + 7:]
            if "```" in cleaned:
                cleaned = cleaned[:cleaned.rfind("```")]
                
            tier = "Unknown"
            conf = 0.0
            drivers = []
            reasoning = ""
            try:
                p = json.loads(cleaned.strip())
                tier = p.get("stress_level", "Unknown")
                conf = float(p.get("confidence_score", 0.0))
                drivers = p.get("primary_drivers", [])
                reasoning = p.get("explainable_reasoning", "")
            except Exception:
                for cand in ["High (Tier 2)", "Moderate (Tier 1)", "Low (Tier 0)", "Insufficient Signal"]:
                    if cand in raw:
                        tier = cand
                        break

            print(f"[{call_idx:02d}/{total_calls}] {v['group']:<10} {v['id']} Rep {rep}: {tier} (conf={conf:.2f}, lat={lat:.2f}s)")
            
            res_item = {
                "call_idx": call_idx,
                "group": v["group"],
                "vector_id": v["id"],
                "rep": rep,
                "au04": v["au04"],
                "au07": v["au07"],
                "f0_delta": v["f0_delta"],
                "jitter": v["jitter"],
                "tension": v["tension"],
                "tier": tier,
                "confidence": conf,
                "latency_s": round(lat, 3),
                "primary_drivers": drivers,
                "reasoning": reasoning,
                "raw_response": raw
            }
            results.append(res_item)
            
            csv_rows.append({
                "call_idx": call_idx,
                "group": v["group"],
                "vector_id": v["id"],
                "rep": rep,
                "au04": v["au04"],
                "au07": v["au07"],
                "f0_delta": v["f0_delta"],
                "jitter": v["jitter"],
                "tension": v["tension"],
                "tier": tier,
                "confidence": conf,
                "latency_s": round(lat, 3)
            })

    # Save to evidence
    json_path = REPO_ROOT / "evidence" / "tier2_reachability_sweep.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    
    csv_path = REPO_ROOT / "evidence" / "tier2_reachability_sweep.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "call_idx", "group", "vector_id", "rep", "au04", "au07", "f0_delta",
            "jitter", "tension", "tier", "confidence", "latency_s"
        ])
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\n[DONE] Saved JSON to {json_path}")
    print(f"[DONE] Saved CSV to {csv_path}")

    # Summary analysis
    print("\n=== SWEEP SUMMARY BY VECTOR ===")
    from collections import Counter
    for v in vectors:
        vid = v["id"]
        v_results = [r["tier"] for r in results if r["vector_id"] == vid]
        counts = dict(Counter(v_results))
        print(f"{v['group']:<11} {vid:<8} (AU04={v['au04']}, +{v['f0_delta']}Hz, ten={v['tension']}): {counts}")

if __name__ == "__main__":
    main()

