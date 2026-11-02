"""Sweep 10 feature vectors from mild to extreme (3 repeats each) against live Gemma 4 E2B."""
import json
import time
from pathlib import Path
from parlor import llama
from parlor.fusion import FeatureFusionEngine, EXPLAINABLE_SYSTEM_PROMPT

vectors = [
    {"name": "V01_Calm", "au04": 0.05, "au07": 0.02, "f0_delta": 2.0, "jitter": 0.8, "tension": 0.22},
    {"name": "V02_VeryMild", "au04": 0.18, "au07": 0.15, "f0_delta": 10.0, "jitter": 1.1, "tension": 0.31},
    {"name": "V03_MildEffort", "au04": 0.32, "au07": 0.28, "f0_delta": 18.5, "jitter": 1.4, "tension": 0.40},
    {"name": "V04_ModOnset", "au04": 0.45, "au07": 0.40, "f0_delta": 28.0, "jitter": 1.9, "tension": 0.50},
    {"name": "V05_ClearMod", "au04": 0.58, "au07": 0.52, "f0_delta": 38.0, "jitter": 2.4, "tension": 0.60},
    {"name": "V06_Elevated", "au04": 0.68, "au07": 0.60, "f0_delta": 46.0, "jitter": 2.9, "tension": 0.68},
    {"name": "V07_HighThresh", "au04": 0.76, "au07": 0.70, "f0_delta": 55.0, "jitter": 3.4, "tension": 0.74},
    {"name": "V08_AcuteStrain", "au04": 0.85, "au07": 0.78, "f0_delta": 65.0, "jitter": 4.1, "tension": 0.81},
    {"name": "V09_VeryHigh", "au04": 0.92, "au07": 0.86, "f0_delta": 78.0, "jitter": 4.8, "tension": 0.88},
    {"name": "V10_Extreme", "au04": 0.98, "au07": 0.95, "f0_delta": 92.0, "jitter": 5.6, "tension": 0.95},
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
        "f0_mean_hz": 145.0 + v["f0_delta"], "f0_std_hz": round(15.0 + v["f0_delta"] * 0.3, 1),
        "jitter_local": v["jitter"], "shimmer_local": round(v["jitter"] * 1.1, 2),
        "pause_ratio": 0.35, "vocal_tension_index": v["tension"]
    }
    fe.add_frame(face, vocal)
    return fe.format_prompt()

results = []
print("Starting 10-vector x 3-repeat sweep...")
for idx, v in enumerate(vectors, 1):
    prompt_str = make_prompt(v)
    for rep in range(1, 4):
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
        try:
            p = json.loads(cleaned.strip())
            tier = p.get("stress_level", "Unknown")
        except Exception:
            for cand in ["High (Tier 2)", "Moderate (Tier 1)", "Low (Tier 0)"]:
                if cand in raw:
                    tier = cand
                    break
        print(f"[{idx:02d}/10] Rep {rep}: {v['name']} -> {tier} ({lat:.2f}s)")
        results.append({
            "vector_id": idx,
            "vector_name": v["name"],
            "rep": rep,
            "au04": v["au04"],
            "au07": v["au07"],
            "f0_delta": v["f0_delta"],
            "jitter": v["jitter"],
            "tension": v["tension"],
            "tier": tier,
            "latency_s": round(lat, 3),
            "raw": raw
        })

tiers_seen = {r["tier"] for r in results}
print(f"\nTiers observed: {tiers_seen}")
Path("evidence/tier_sweep_initial.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

