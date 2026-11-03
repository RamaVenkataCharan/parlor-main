"""Rigorous 30-Turn Voice TTFA Benchmark across 3 conditions in alternating order:
1. Loop OFF (Wellness loop muted)
2. Loop ON Unmitigated (Wellness loop active, concurrency mitigation disabled)
3. Loop ON Mitigated (Wellness loop active, concurrency mitigation enabled)

Total: 30 cycles x 3 conditions = 90 conversational turns.
Reports Mean, p95, and 95% Bootstrap Confidence Intervals.
"""
import asyncio
import base64
import csv
import json
import os
import sys
import time
from pathlib import Path
import numpy as np
import websockets

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = ROOT / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV_30 = EVIDENCE_DIR / "voice_ttfa_30_turns.csv"
OUT_CSV_MASTER = EVIDENCE_DIR / "voice_ttfa.csv"
FIXTURES_DIR = ROOT / "benchmarks" / "fixtures"

AUDIO_FILES = [
    "capital_france.wav",
    "name_intro.wav",
    "describe_scene.wav",
    "name_recall.wav",
    "how_long_quiet.wav",
    "capital_france_noisy.wav",
    "filler_color.wav",
    "filler_pet.wav",
    "long_question.wav",
    "capital_france.wav",
]


def load_wav_b64(filename: str) -> str:
    path = FIXTURES_DIR / filename
    if not path.exists():
        sr = 16000
        t = np.linspace(0, 1.5, int(sr * 1.5), endpoint=False)
        pcm = (0.3 * np.sin(2 * np.pi * 220.0 * t)).astype(np.int16)
        return base64.b64encode(pcm.tobytes()).decode("ascii")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def query_gpu_telemetry() -> dict:
    try:
        import subprocess
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=clocks.gr,clocks.mem,temperature.gpu,power.draw", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2.0
        )
        parts = [p.strip() for p in res.stdout.strip().split(",")]
        return {
            "gpu_clock_graphics_mhz": float(parts[0]),
            "gpu_clock_mem_mhz": float(parts[1]),
            "gpu_temp_c": float(parts[2]),
            "gpu_power_w": float(parts[3])
        }
    except Exception:
        return {"gpu_clock_graphics_mhz": 0.0, "gpu_clock_mem_mhz": 0.0, "gpu_temp_c": 0.0, "gpu_power_w": 0.0}


async def execute_turn(ws, audio_b64: str) -> dict:
    t0 = time.perf_counter()
    await ws.send(json.dumps({"type": "speech", "audio": audio_b64}))

    ttfa = None
    first_chunk_bytes = 0
    transcript = ""
    reply_text = ""

    while True:
        raw = await ws.recv()
        msg = json.loads(raw)
        m_type = msg.get("type")

        if m_type == "audio_chunk" and ttfa is None:
            ttfa = time.perf_counter() - t0
            first_chunk_bytes = len(msg.get("audio", ""))

        elif m_type == "text_delta":
            reply_text += msg.get("text", "")

        elif m_type == "transcript":
            transcript = msg.get("transcription", "")

        elif m_type == "turn_final":
            if ttfa is None:
                ttfa = time.perf_counter() - t0
            if not transcript:
                transcript = msg.get("transcription", "")
            await ws.send(json.dumps({"type": "ready"}))
            break

        elif m_type == "turn_incomplete":
            await ws.send(json.dumps({"type": "flush"}))

    return {
        "ttfa_s": ttfa,
        "first_chunk_bytes": first_chunk_bytes,
        "transcript": transcript,
        "reply_text": reply_text.strip()
    }


def compute_bootstrap_ci(data: list[float], n_bootstrap: int = 10000, ci: float = 0.95) -> tuple[float, float]:
    arr = np.array(data)
    rng = np.random.RandomState(42)
    boot_means = [np.mean(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_bootstrap)]
    lower = float(np.percentile(boot_means, (1.0 - ci) / 2.0 * 100))
    upper = float(np.percentile(boot_means, (1.0 + ci) / 2.0 * 100))
    return lower, upper


async def run_benchmark():
    uri = "ws://127.0.0.1:8000/ws"
    print("=" * 75)
    print(" 30-TURN VOICE TTFA BENCHMARK (ALTERNATING ORDER)")
    print(f" Target Server : {uri}")
    print(f" Total Turns   : 30 cycles x 3 conditions = 90 turns")
    print("=" * 75)

    records = []
    ttfas_off = []
    ttfas_unmitigated = []
    ttfas_mitigated = []

    blank_face = base64.b64encode(np.full((240, 320, 3), 180, dtype=np.uint8).tobytes()).decode("ascii")

    async with websockets.connect(uri) as ws:
        # Warmup turn
        print("[SETUP] Executing warmup turn...")
        warmup_audio = load_wav_b64("name_intro.wav")
        await execute_turn(ws, warmup_audio)
        await asyncio.sleep(1.0)

        turn_counter = 1
        for cycle in range(1, 31):
            fixture = AUDIO_FILES[(cycle - 1) % len(AUDIO_FILES)]
            audio_b64 = load_wav_b64(fixture)
            print(f"\n--- CYCLE [{cycle:02d}/30] Fixture: {fixture} ---")

            # 1. Condition: Loop OFF
            await ws.send(json.dumps({"type": "set_wellness_mute", "muted": True}))
            r_ack = json.loads(await ws.recv())
            gpu_t1 = query_gpu_telemetry()
            res_off = await execute_turn(ws, audio_b64)
            ttfas_off.append(res_off["ttfa_s"])
            records.append({
                "turn_index": turn_counter,
                "cycle": cycle,
                "condition": "LOOP_OFF",
                "audio_fixture": fixture,
                "ttfa_sec": round(res_off["ttfa_s"], 4),
                "first_chunk_bytes": res_off["first_chunk_bytes"],
                "gpu_temp_c": gpu_t1["gpu_temp_c"],
                "gpu_clock_graphics_mhz": gpu_t1["gpu_clock_graphics_mhz"],
                "gpu_clock_mem_mhz": gpu_t1["gpu_clock_mem_mhz"],
                "gpu_power_w": gpu_t1["gpu_power_w"],
                "transcript": (res_off.get("transcript") or "")[:60],
                "reply": (res_off.get("reply_text") or "")[:60]
            })
            print(f"  [Turn {turn_counter:02d}] LOOP_OFF             : {res_off['ttfa_s']:.3f}s (GPU: {gpu_t1['gpu_temp_c']}C, {gpu_t1['gpu_clock_graphics_mhz']}MHz)")
            turn_counter += 1
            await asyncio.sleep(0.4)

            # 2. Condition: Loop ON (Unmitigated)
            await ws.send(json.dumps({"type": "set_wellness_mute", "muted": False}))
            await ws.recv()
            await ws.send(json.dumps({"type": "set_concurrency_mitigation", "enabled": False}))
            await ws.recv()
            # Feed telemetry to trigger background wellness extraction
            await ws.send(json.dumps({
                "type": "wellness_telemetry",
                "image": f"data:image/jpeg;base64,{blank_face}",
                "audio": audio_b64
            }))
            gpu_t2 = query_gpu_telemetry()
            res_unmit = await execute_turn(ws, audio_b64)
            ttfas_unmitigated.append(res_unmit["ttfa_s"])
            records.append({
                "turn_index": turn_counter,
                "cycle": cycle,
                "condition": "LOOP_ON_UNMITIGATED",
                "audio_fixture": fixture,
                "ttfa_sec": round(res_unmit["ttfa_s"], 4),
                "first_chunk_bytes": res_unmit["first_chunk_bytes"],
                "gpu_temp_c": gpu_t2["gpu_temp_c"],
                "gpu_clock_graphics_mhz": gpu_t2["gpu_clock_graphics_mhz"],
                "gpu_clock_mem_mhz": gpu_t2["gpu_clock_mem_mhz"],
                "gpu_power_w": gpu_t2["gpu_power_w"],
                "transcript": (res_unmit.get("transcript") or "")[:60],
                "reply": (res_unmit.get("reply_text") or "")[:60]
            })
            print(f"  [Turn {turn_counter:02d}] LOOP_ON_UNMITIGATED  : {res_unmit['ttfa_s']:.3f}s (GPU: {gpu_t2['gpu_temp_c']}C, {gpu_t2['gpu_clock_graphics_mhz']}MHz)")
            turn_counter += 1
            await asyncio.sleep(0.4)

            # 3. Condition: Loop ON (Mitigated)
            await ws.send(json.dumps({"type": "set_wellness_mute", "muted": False}))
            await ws.recv()
            await ws.send(json.dumps({"type": "set_concurrency_mitigation", "enabled": True}))
            await ws.recv()
            await ws.send(json.dumps({
                "type": "wellness_telemetry",
                "image": f"data:image/jpeg;base64,{blank_face}",
                "audio": audio_b64
            }))
            gpu_t3 = query_gpu_telemetry()
            res_mit = await execute_turn(ws, audio_b64)
            ttfas_mitigated.append(res_mit["ttfa_s"])
            records.append({
                "turn_index": turn_counter,
                "cycle": cycle,
                "condition": "LOOP_ON_MITIGATED",
                "audio_fixture": fixture,
                "ttfa_sec": round(res_mit["ttfa_s"], 4),
                "first_chunk_bytes": res_mit["first_chunk_bytes"],
                "gpu_temp_c": gpu_t3["gpu_temp_c"],
                "gpu_clock_graphics_mhz": gpu_t3["gpu_clock_graphics_mhz"],
                "gpu_clock_mem_mhz": gpu_t3["gpu_clock_mem_mhz"],
                "gpu_power_w": gpu_t3["gpu_power_w"],
                "transcript": (res_mit.get("transcript") or "")[:60],
                "reply": (res_mit.get("reply_text") or "")[:60]
            })
            print(f"  [Turn {turn_counter:02d}] LOOP_ON_MITIGATED    : {res_mit['ttfa_s']:.3f}s (GPU: {gpu_t3['gpu_temp_c']}C, {gpu_t3['gpu_clock_graphics_mhz']}MHz)")
            turn_counter += 1
            await asyncio.sleep(0.4)

    # Save CSVs
    fieldnames = [
        "turn_index", "cycle", "condition", "audio_fixture", "ttfa_sec", "first_chunk_bytes",
        "gpu_temp_c", "gpu_clock_graphics_mhz", "gpu_clock_mem_mhz", "gpu_power_w",
        "transcript", "reply"
    ]
    for out_p in [OUT_CSV_30, OUT_CSV_MASTER]:
        with open(out_p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(records)

    # Statistical computation
    def print_stats(name, data):
        m = np.mean(data)
        p50 = np.median(data)
        p95 = np.percentile(data, 95)
        mx = np.max(data)
        std = np.std(data, ddof=1)
        ci_low, ci_high = compute_bootstrap_ci(data)
        margin = (ci_high - ci_low) / 2.0
        print(f"\n{name} (N={len(data)}):")
        print(f"  Mean       : {m:.3f} s (formatted: {m:.2f}s)")
        print(f"  p50        : {p50:.3f} s (formatted: {p50:.2f}s)")
        print(f"  p95        : {p95:.3f} s (formatted: {p95:.2f}s)")
        print(f"  Max        : {mx:.3f} s (formatted: {mx:.2f}s)")
        print(f"  Std Dev    : {std:.3f} s")
        print(f"  95% CI     : [{ci_low:.3f}s, {ci_high:.3f}s] (margin +/- {margin:.3f}s)")
        return {
            "mean": round(m, 3), "p50": round(p50, 3), "p95": round(p95, 3),
            "max": round(mx, 3), "std": round(std, 3),
            "ci_95": [round(ci_low, 3), round(ci_high, 3)], "margin": round(margin, 3)
        }

    print("\n" + "=" * 75)
    print(" EMPIRICAL 30-TURN VOICE TTFA SUMMARY")
    print("=" * 75)
    stats_off = print_stats("1. Wellness Loop OFF", ttfas_off)
    stats_unmit = print_stats("2. Wellness Loop ON (Unmitigated)", ttfas_unmitigated)
    stats_mit = print_stats("3. Wellness Loop ON (Mitigated)", ttfas_mitigated)

    delta_unmit = stats_unmit["mean"] - stats_off["mean"]
    delta_mit = stats_mit["mean"] - stats_off["mean"]
    mit_improvement = stats_unmit["mean"] - stats_mit["mean"]

    print("\n--- CONCURRENCY OVERHEAD ANALYSIS ---")
    print(f"  Unmitigated Overhead Delta  : +{delta_unmit:.3f} s")
    print(f"  Mitigated Overhead Delta    : +{delta_mit:.3f} s")
    print(f"  Latency Savings via Deferral: -{mit_improvement:.3f} s (reclaimed conversational responsiveness)")
    print(f"  Saved Evidence: {OUT_CSV_30} and {OUT_CSV_MASTER}")
    print("=" * 75)

    summary_json = {
        "timestamp": time.time(),
        "n_turns_per_condition": 30,
        "total_turns": 90,
        "ordering": "alternating_round_robin",
        "loop_off": stats_off,
        "loop_on_unmitigated": stats_unmit,
        "loop_on_mitigated": stats_mit,
        "delta_unmitigated_s": round(delta_unmit, 3),
        "delta_mitigated_s": round(delta_mit, 3),
        "mitigation_savings_s": round(mit_improvement, 3)
    }
    (EVIDENCE_DIR / "voice_ttfa_summary.json").write_text(json.dumps(summary_json, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(run_benchmark())

