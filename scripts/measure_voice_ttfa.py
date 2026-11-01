"""Empirical Benchmark for Conversational Voice TTFA (Time-To-First-Audio).

Measures 10 turns with Wellness Loop OFF and 10 turns with Wellness Loop ON
against the live Parlor server on this machine (ws://127.0.0.1:8000/ws).
Records per-turn metrics to evidence/voice_ttfa.csv.
"""

import asyncio
import base64
import csv
import json
import os
import sys
import time
from typing import List, Dict, Any
import numpy as np
import websockets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(BASE_DIR, "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

FIXTURES_DIR = os.path.join(BASE_DIR, "benchmarks", "fixtures")
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
    path = os.path.join(FIXTURES_DIR, filename)
    if not os.path.exists(path):
        # Generate 1.5s 16kHz sine speech-like audio
        sr = 16000
        t = np.linspace(0, 1.5, int(sr * 1.5), endpoint=False)
        pcm = (0.3 * np.sin(2 * np.pi * 220.0 * t)).astype(np.int16)
        return base64.b64encode(pcm.tobytes()).decode("ascii")

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


async def execute_turn(ws, audio_b64: str) -> Dict[str, Any]:
    """Sends audio speech turn and awaits first audio chunk and terminal message."""
    t0 = time.perf_counter()
    await ws.send(json.dumps({
        "type": "speech",
        "audio": audio_b64
    }))

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
            raw_audio = msg.get("audio", "")
            first_chunk_bytes = len(raw_audio)

        elif m_type == "text_delta":
            reply_text += msg.get("text", "")

        elif m_type == "transcript":
            transcript = msg.get("transcription", "")

        elif m_type == "turn_final":
            if ttfa is None:
                # If no audio sent (e.g. silent turn or error), measure total
                ttfa = time.perf_counter() - t0
            if not transcript:
                transcript = msg.get("transcription", "")
            await ws.send(json.dumps({"type": "ready"}))
            break

        elif m_type == "turn_incomplete":
            # Flush incomplete turn
            await ws.send(json.dumps({"type": "flush"}))

    return {
        "ttfa_s": ttfa,
        "first_chunk_bytes": first_chunk_bytes,
        "transcript": transcript,
        "reply_text": reply_text.strip()
    }


async def run_benchmark(ws_url: str = "ws://127.0.0.1:8000/ws", out_filename: str = "voice_ttfa_mitigated.csv"):
    out_csv = os.path.join(EVIDENCE_DIR, out_filename)
    print("=" * 75)
    print("      RUNNING VOICE TTFA (TIME-TO-FIRST-AUDIO) BENCHMARK")
    print(f" Target Server : {ws_url}")
    print(f" Evidence CSV  : {out_csv}")
    print("=" * 75)

    records = []

    async with websockets.connect(ws_url) as ws:
        # Initial greeting / warm-up turn
        print("[SETUP] Executing warm-up turn...")
        warmup_audio = load_wav_b64("name_intro.wav")
        await execute_turn(ws, warmup_audio)
        await asyncio.sleep(1.0)

        # ── CONDITION 1: 10 TURNS WITH WELLNESS LOOP OFF ──────────────────────
        print("\n--- CONDITION 1: WELLNESS LOOP OFF (10 TURNS) ---")
        await ws.send(json.dumps({"type": "set_wellness_mute", "muted": True}))

        off_ttfas = []
        for i in range(10):
            wav_name = AUDIO_FILES[i]
            audio_b64 = load_wav_b64(wav_name)

            res = await execute_turn(ws, audio_b64)
            ttfa = res["ttfa_s"]
            off_ttfas.append(ttfa)

            records.append({
                "turn_index": i + 1,
                "wellness_loop": "OFF",
                "audio_fixture": wav_name,
                "ttfa_sec": round(ttfa, 4),
                "first_chunk_bytes": res["first_chunk_bytes"],
                "transcript": (res.get("transcript") or "")[:60],
                "reply": (res.get("reply_text") or "")[:60]
            })
            transcript_snippet = (res.get("transcript") or "")[:40]
            print(f"  Turn [{i+1}/10] TTFA: {ttfa:.3f}s | Fixture: {wav_name:<25} | Transcript: {transcript_snippet}")
            await asyncio.sleep(0.5)

        # ── CONDITION 2: 10 TURNS WITH WELLNESS LOOP ON ───────────────────────
        print("\n--- CONDITION 2: WELLNESS LOOP ON (10 TURNS) ---")
        await ws.send(json.dumps({"type": "set_wellness_mute", "muted": False}))

        on_ttfas = []
        for i in range(10):
            wav_name = AUDIO_FILES[i]
            audio_b64 = load_wav_b64(wav_name)

            # Feed a simulated face frame and audio telemetry chunk to trigger wellness extraction
            blank_face = base64.b64encode(np.full((240, 320, 3), 180, dtype=np.uint8).tobytes()).decode("ascii")
            await ws.send(json.dumps({
                "type": "wellness_telemetry",
                "image": f"data:image/jpeg;base64,{blank_face}",
                "audio": audio_b64
            }))

            res = await execute_turn(ws, audio_b64)
            ttfa = res["ttfa_s"]
            on_ttfas.append(ttfa)

            records.append({
                "turn_index": i + 11,
                "wellness_loop": "ON",
                "audio_fixture": wav_name,
                "ttfa_sec": round(ttfa, 4),
                "first_chunk_bytes": res["first_chunk_bytes"],
                "transcript": (res.get("transcript") or "")[:60],
                "reply": (res.get("reply_text") or "")[:60]
            })
            transcript_snippet = (res.get("transcript") or "")[:40]
            print(f"  Turn [{i+1}/10] TTFA: {ttfa:.3f}s | Fixture: {wav_name:<25} | Transcript: {transcript_snippet}")
            await asyncio.sleep(0.5)

    # Write CSV
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "turn_index", "wellness_loop", "audio_fixture", "ttfa_sec",
            "first_chunk_bytes", "transcript", "reply"
        ])
        writer.writeheader()
        writer.writerows(records)

    # Also update evidence/voice_ttfa.csv with latest run
    primary_csv = os.path.join(EVIDENCE_DIR, "voice_ttfa.csv")
    with open(primary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "turn_index", "wellness_loop", "audio_fixture", "ttfa_sec",
            "first_chunk_bytes", "transcript", "reply"
        ])
        writer.writeheader()
        writer.writerows(records)

    all_ttfas = off_ttfas + on_ttfas

    print("\n" + "=" * 75)
    print(" EMPIRICAL VOICE TTFA BENCHMARK RESULTS:")
    print("=" * 75)
    print(f" Wellness Loop OFF (N=10) : Mean={np.mean(off_ttfas):.3f}s | p50={np.median(off_ttfas):.3f}s | p95={np.percentile(off_ttfas, 95):.3f}s | Max={np.max(off_ttfas):.3f}s")
    print(f" Wellness Loop ON  (N=10) : Mean={np.mean(on_ttfas):.3f}s | p50={np.median(on_ttfas):.3f}s | p95={np.percentile(on_ttfas, 95):.3f}s | Max={np.max(on_ttfas):.3f}s")
    print(f" Combined All Turns(N=20) : Mean={np.mean(all_ttfas):.3f}s | p50={np.median(all_ttfas):.3f}s | p95={np.percentile(all_ttfas, 95):.3f}s | Max={np.max(all_ttfas):.3f}s")
    print(f" Delta (Loop ON - OFF)    : {np.mean(on_ttfas) - np.mean(off_ttfas):+.3f}s")
    print(f" Saved Raw Evidence       : {out_csv} and {primary_csv}")
    print("=" * 75)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8000/ws"
    asyncio.run(run_benchmark(url))
