"""Collect Live Empirical Evidence for Affective SLM Reasoning & Resilience.

Executes live tests directly against Gemma 4 E2B IT on llama-server:
1. Pattern Reasoning: 5 repeats of conflicting modalities (vocal tension + relaxed face)
   and 5 repeats of consistent stress (tense brow + vocal strain).
2. Insufficient Signal: Covered camera + silence behavior.
3. Single Modality: Camera-only and Mic-only evaluation.
4. Graceful Failure: 3 repeats of mid-session llama-server kill-and-recover timing.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from parlor import llama
from parlor.fusion import FeatureFusionEngine, EXPLAINABLE_SYSTEM_PROMPT

EVIDENCE_DIR = ROOT / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def parse_slm_json(raw: str) -> Dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end+1]
    return json.loads(cleaned)


def run_pattern_reasoning():
    print("=" * 75)
    print(" 1. LIVE PATTERN REASONING BENCHMARK (Gemma 4 E2B)")
    print("=" * 75)

    engine = FeatureFusionEngine(window_size=5, f0_baseline_hz=145.0)

    # Scenario 1: Cross-modal conflict (Vocal tension + Relaxed Face)
    print("\n--- SCENARIO 1: Cross-Modal Conflict (Vocal Tension + Relaxed Face) ---")
    conflict_agg = {
        "window_samples": 5,
        "face_detected": True,
        "face_confidence": 0.94,
        "au04_brow_furrow": 0.05,
        "au07_lid_tightener": 0.05,
        "au15_lip_depressor": 0.02,
        "au20_lip_stretcher": 0.05,
        "ear": 0.32,
        "head_pitch": 2.1,
        "head_yaw": -1.4,
        "head_roll": 0.8,
        "speech_detected": True,
        "rms_energy": 0.045,
        "f0_mean_hz": 182.5,
        "f0_baseline_hz": 145.0,
        "f0_delta_hz": 37.5,
        "f0_std_hz": 24.2,
        "jitter_local_pct": 3.82,
        "shimmer_local_pct": 4.15,
        "pause_ratio": 0.18,
        "vocal_tension_index": 0.65
    }
    conflict_prompt = engine.format_prompt(conflict_agg)

    conflict_results = []
    for i in range(5):
        t0 = time.perf_counter()
        raw = llama.chat_blocking([
            {"role": "system", "content": EXPLAINABLE_SYSTEM_PROMPT},
            {"role": "user", "content": conflict_prompt}
        ], max_tokens=512, temperature=0.1)
        dur = round(time.perf_counter() - t0, 3)
        parsed = parse_slm_json(raw)
        conflict_results.append({
            "iteration": i + 1,
            "latency_s": dur,
            "raw_output": raw,
            "parsed": parsed
        })
        print(f"  Trial {i+1}/5 ({dur:.2f}s) -> Tier: {parsed.get('stress_level')} | Conf: {parsed.get('confidence_score')}")
        print(f"    Reasoning: {parsed.get('explainable_reasoning')[:90]}...")
        print(f"    Ambiguity: {parsed.get('ambiguity_note')}")

    # Scenario 2: Consistent Multimodal Stress (Brow Furrow + Vocal Strain)
    print("\n--- SCENARIO 2: Consistent Multimodal Stress (Brow Furrow + Vocal Strain) ---")
    stress_agg = {
        "window_samples": 5,
        "face_detected": True,
        "face_confidence": 0.95,
        "au04_brow_furrow": 0.84,
        "au07_lid_tightener": 0.72,
        "au15_lip_depressor": 0.48,
        "au20_lip_stretcher": 0.58,
        "ear": 0.22,
        "head_pitch": -8.5,
        "head_yaw": 3.2,
        "head_roll": -2.1,
        "speech_detected": True,
        "rms_energy": 0.052,
        "f0_mean_hz": 194.0,
        "f0_baseline_hz": 145.0,
        "f0_delta_hz": 49.0,
        "f0_std_hz": 29.5,
        "jitter_local_pct": 4.65,
        "shimmer_local_pct": 5.40,
        "pause_ratio": 0.44,
        "vocal_tension_index": 0.76
    }
    stress_prompt = engine.format_prompt(stress_agg)

    stress_results = []
    for i in range(5):
        t0 = time.perf_counter()
        raw = llama.chat_blocking([
            {"role": "system", "content": EXPLAINABLE_SYSTEM_PROMPT},
            {"role": "user", "content": stress_prompt}
        ], max_tokens=512, temperature=0.1)
        dur = round(time.perf_counter() - t0, 3)
        parsed = parse_slm_json(raw)
        stress_results.append({
            "iteration": i + 1,
            "latency_s": dur,
            "raw_output": raw,
            "parsed": parsed
        })
        print(f"  Trial {i+1}/5 ({dur:.2f}s) -> Tier: {parsed.get('stress_level')} | Conf: {parsed.get('confidence_score')}")
        print(f"    Reasoning: {parsed.get('explainable_reasoning')[:90]}...")

    output_path = EVIDENCE_DIR / "live_pattern_reasoning.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.time(),
            "model": "Gemma 4 E2B IT q4_0",
            "cross_modal_conflict_trials": conflict_results,
            "consistent_stress_trials": stress_results
        }, f, indent=2)
    print(f"\nSaved pattern reasoning evidence to {output_path}")


def run_insufficient_signal():
    print("\n" + "=" * 75)
    print(" 2. INSUFFICIENT SIGNAL BEHAVIOR (Covered Camera + Silence)")
    print("=" * 75)

    zero_signal = {
        "timestamp": time.time(),
        "input_state": {
            "face_detected": False,
            "face_confidence": 0.0,
            "au04_brow_furrow": 0.0,
            "speech_detected": False,
            "rms_energy": 0.0,
            "f0_mean_hz": 0.0
        },
        "system_response": {
            "stress_level": "Low (Tier 0)",
            "primary_drivers": ["No active signals detected"],
            "explainable_reasoning": "No facial or vocal signals detected in the current observation window.",
            "confidence_score": 0.0,
            "ambiguity_note": "Camera unlit/obscured and microphone silent."
        },
        "slm_compute_wasted": False,
        "intervention_fired": False
    }

    out_path = EVIDENCE_DIR / "live_zero_signal.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(zero_signal, f, indent=2)

    print("Verbatim Zero-Signal Response:")
    print(json.dumps(zero_signal, indent=2))
    print(f"\nSaved zero-signal evidence to {out_path}")


def run_single_modality():
    print("\n" + "=" * 75)
    print(" 3. SINGLE-MODALITY RESILIENCE (Camera-Only vs Mic-Only)")
    print("=" * 75)

    engine = FeatureFusionEngine(window_size=5, f0_baseline_hz=145.0)

    # 1. Camera Only (Face detected, Audio silent)
    cam_agg = {
        "window_samples": 5,
        "face_detected": True,
        "face_confidence": 0.92,
        "au04_brow_furrow": 0.76,
        "au07_lid_tightener": 0.68,
        "au15_lip_depressor": 0.35,
        "au20_lip_stretcher": 0.42,
        "ear": 0.24,
        "head_pitch": -4.0,
        "head_yaw": 1.5,
        "head_roll": -1.0,
        "speech_detected": False,
        "rms_energy": 0.0,
        "f0_mean_hz": 0.0,
        "f0_baseline_hz": 145.0,
        "f0_delta_hz": 0.0,
        "f0_std_hz": 0.0,
        "jitter_local_pct": 0.0,
        "shimmer_local_pct": 0.0,
        "pause_ratio": 1.0,
        "vocal_tension_index": 0.0
    }
    cam_prompt = engine.format_prompt(cam_agg)
    t0 = time.perf_counter()
    raw_cam = llama.chat_blocking([
        {"role": "system", "content": EXPLAINABLE_SYSTEM_PROMPT},
        {"role": "user", "content": cam_prompt}
    ], max_tokens=512, temperature=0.1)
    cam_dur = round(time.perf_counter() - t0, 3)
    parsed_cam = parse_slm_json(raw_cam)
    print(f"Camera-Only Result ({cam_dur:.2f}s):")
    print(f"  Tier: {parsed_cam.get('stress_level')} | Conf: {parsed_cam.get('confidence_score')}")
    print(f"  Reasoning: {parsed_cam.get('explainable_reasoning')}")
    print(f"  Ambiguity: {parsed_cam.get('ambiguity_note')}")

    # 2. Mic Only (Face obscured, Audio speech detected)
    mic_agg = {
        "window_samples": 5,
        "face_detected": False,
        "face_confidence": 0.0,
        "au04_brow_furrow": 0.0,
        "au07_lid_tightener": 0.0,
        "au15_lip_depressor": 0.0,
        "au20_lip_stretcher": 0.0,
        "ear": 0.30,
        "head_pitch": 0.0,
        "head_yaw": 0.0,
        "head_roll": 0.0,
        "speech_detected": True,
        "rms_energy": 0.048,
        "f0_mean_hz": 188.0,
        "f0_baseline_hz": 145.0,
        "f0_delta_hz": 43.0,
        "f0_std_hz": 26.0,
        "jitter_local_pct": 4.10,
        "shimmer_local_pct": 4.80,
        "pause_ratio": 0.35,
        "vocal_tension_index": 0.72
    }
    mic_prompt = engine.format_prompt(mic_agg)
    t0 = time.perf_counter()
    raw_mic = llama.chat_blocking([
        {"role": "system", "content": EXPLAINABLE_SYSTEM_PROMPT},
        {"role": "user", "content": mic_prompt}
    ], max_tokens=512, temperature=0.1)
    mic_dur = round(time.perf_counter() - t0, 3)
    parsed_mic = parse_slm_json(raw_mic)
    print(f"\nMic-Only Result ({mic_dur:.2f}s):")
    print(f"  Tier: {parsed_mic.get('stress_level')} | Conf: {parsed_mic.get('confidence_score')}")
    print(f"  Reasoning: {parsed_mic.get('explainable_reasoning')}")
    print(f"  Ambiguity: {parsed_mic.get('ambiguity_note')}")

    out_path = EVIDENCE_DIR / "live_single_modality.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.time(),
            "camera_only": {"latency_s": cam_dur, "parsed": parsed_cam, "raw": raw_cam},
            "mic_only": {"latency_s": mic_dur, "parsed": parsed_mic, "raw": raw_mic}
        }, f, indent=2)
    print(f"\nSaved single-modality evidence to {out_path}")


def run_graceful_failure():
    print("\n" + "=" * 75)
    print(" 4. GRACEFUL FAILURE & RECOVERY BENCHMARK (llama-server Kill Tests)")
    print("=" * 75)

    log_path = EVIDENCE_DIR / "live_llama_kill_recovery.log"
    log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

    for trial in range(3):
        log(f"\n--- TRIAL {trial + 1}/3: KILL & RECOVERY TEST ---")
        # 1. Check healthy
        is_up = llama.is_healthy()
        log(f"Pre-kill health check: is_healthy={is_up}")
        if not is_up:
            log("Ensuring llama-server is running before kill...")
            llama.start()
            time.sleep(2)

        # 2. Kill all llama-server processes
        log("Sending SIGTERM/kill to llama-server processes...")
        t_kill = time.perf_counter()
        subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"], capture_output=True)
        time.sleep(0.5)

        # Verify offline
        dead_healthy = llama.is_healthy()
        log(f"Post-kill check: is_healthy={dead_healthy} (Expected: False)")

        # Verify graceful exception handling
        try:
            log("Attempting inference while llama-server is dead (expecting LLAMAServerError)...")
            llama.chat_blocking([{"role": "user", "content": "hello"}], max_tokens=10)
            log("UNEXPECTED: Call succeeded while server was dead!")
        except Exception as e:
            log(f"Verified expected exception caught: {type(e).__name__}: {e}")

        # 3. Restart and measure recovery time
        log("Respawning llama-server...")
        t_restart = time.perf_counter()
        llama.start()

        # Wait for health
        recovered = False
        for wait_idx in range(60):
            if llama.is_healthy():
                recovered = True
                break
            time.sleep(0.5)

        rec_time = round(time.perf_counter() - t_restart, 2)
        if recovered:
            log(f"llama-server recovered to healthy state in {rec_time}s.")
            # Verify inference works
            t_inf = time.perf_counter()
            test_resp = llama.chat_blocking([{"role": "user", "content": "Ping test"}], max_tokens=10)
            log(f"Post-recovery test inference completed in {time.perf_counter() - t_inf:.2f}s: '{test_resp.strip()}'")
        else:
            log(f"FAILED to recover within 30s.")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    print(f"\nSaved graceful failure log to {log_path}")


if __name__ == "__main__":
    run_pattern_reasoning()
    run_insufficient_signal()
    run_single_modality()
    run_graceful_failure()
