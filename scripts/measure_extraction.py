"""Empirical Benchmark for Facial and Vocal Feature Extraction Pipelines.

Measures 100 iterations of Facial Action Unit extraction (MediaPipe Face Mesh)
and 100 iterations of Vocal Acoustic DSP extraction (Librosa/SciPy) on this hardware.
Outputs per-run CSVs to evidence/facial_extraction.csv and evidence/vocal_extraction.csv.
"""

import csv
import os
import sys
import time
import cv2
import numpy as np

# Ensure src is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from parlor.facial import FacialExtractor
from parlor.vocal import VocalExtractor

EVIDENCE_DIR = os.path.join(BASE_DIR, "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)


def benchmark_facial(iterations: int = 100) -> str:
    extractor = FacialExtractor()
    out_csv = os.path.join(EVIDENCE_DIR, "facial_extraction.csv")

    # Load real face fixture (Grace Hopper portrait)
    img_path = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages", "matplotlib", "mpl-data", "sample_data", "grace_hopper.jpg")
    if not os.path.exists(img_path):
        img_path = r"C:\Users\ramav\Documents\PROJECTS\parlor\parlor-main-main\.venv\Lib\site-packages\matplotlib\mpl-data\sample_data\grace_hopper.jpg"

    face_frame = cv2.imread(img_path)
    if face_frame is not None:
        face_frame = cv2.resize(face_frame, (640, 480))
    else:
        # Fallback to webcam
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        ret, face_frame = cap.read()
        cap.release()
        if face_frame is not None:
            face_frame = cv2.resize(face_frame, (640, 480))

    blank_frame = np.full((480, 640, 3), 200, dtype=np.uint8)
    dim_frame = (face_frame.astype(np.float32) * 0.15).astype(np.uint8) if face_frame is not None else blank_frame

    # Head turned ~30 deg
    if face_frame is not None:
        h, w = face_frame.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), 30, 1.0)
        turned_frame = cv2.warpAffine(face_frame, M, (w, h))
    else:
        turned_frame = blank_frame

    def run_sub_benchmark(frame, csv_name, label):
        csv_path = os.path.join(EVIDENCE_DIR, csv_name)
        for _ in range(5):
            extractor.extract(frame)
        lats = []
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["run_index", "timestamp_iso", "duration_ms", "face_detected",
                             "au04", "au07", "au15", "au20", "ear", "head_pitch", "head_yaw", "head_roll"])
            for i in range(1, iterations + 1):
                t0 = time.perf_counter()
                res = extractor.extract(frame)
                t1 = time.perf_counter()
                dur = (t1 - t0) * 1000.0
                lats.append(dur)
                now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
                writer.writerow([
                    i,
                    now_iso,
                    f"{dur:.3f}",
                    res.get("face_detected", False),
                    f"{res.get('au04_brow_furrow', 0.0):.4f}",
                    f"{res.get('au07_lid_tightener', 0.0):.4f}",
                    f"{res.get('au15_lip_depressor', 0.0):.4f}",
                    f"{res.get('au20_lip_stretcher', 0.0):.4f}",
                    f"{res.get('ear', 0.0):.4f}",
                    f"{res.get('head_pitch', 0.0):.2f}",
                    f"{res.get('head_yaw', 0.0):.2f}",
                    f"{res.get('head_roll', 0.0):.2f}"
                ])
        mean_ms = np.mean(lats)
        p50_ms = np.median(lats)
        p95_ms = np.percentile(lats, 95)
        max_ms = np.max(lats)
        print(f"[{label}] {iterations} runs:")
        print(f"  Mean: {mean_ms:.2f} ms | p50: {p50_ms:.2f} ms | p95: {p95_ms:.2f} ms | Max: {max_ms:.2f} ms -> {csv_name}")
        return mean_ms, p95_ms

    # Benchmark all 4 conditions
    mean_real, p95_real = run_sub_benchmark(face_frame, "facial_extraction_real.csv", "FACIAL - REAL FACE (NORMAL LIGHT)")
    run_sub_benchmark(blank_frame, "facial_extraction_blank.csv", "FACIAL - BLANK FRAME (NO FACE)")
    run_sub_benchmark(dim_frame, "facial_extraction_dim.csv", "FACIAL - DIM LIGHT (15% LUX)")
    run_sub_benchmark(turned_frame, "facial_extraction_turned.csv", "FACIAL - HEAD TURNED 30 DEG")

    # Primary facial_extraction.csv records the real face benchmark
    import shutil
    shutil.copyfile(os.path.join(EVIDENCE_DIR, "facial_extraction_real.csv"), out_csv)
    print(f"  Saved primary real-face evidence: {out_csv}")
    return out_csv


def benchmark_vocal(iterations: int = 100) -> str:
    extractor = VocalExtractor()
    out_csv = os.path.join(EVIDENCE_DIR, "vocal_extraction.csv")

    # Load real audio if available, else synthetic speech-like signal
    wav_path = os.path.join(BASE_DIR, "benchmarks", "fixtures", "capital_france.wav")
    sr = 16000
    if os.path.exists(wav_path):
        import soundfile as sf
        audio_data, file_sr = sf.read(wav_path, dtype="float32")
        if file_sr != sr:
            audio_data = audio_data[:sr]  # 1 sec slice
        else:
            audio_data = audio_data[:sr]
    else:
        # 1-second synthetic complex harmonic wave
        t = np.linspace(0, 1.0, sr, endpoint=False)
        audio_data = (
            0.4 * np.sin(2 * np.pi * 180.0 * t) +
            0.2 * np.sin(2 * np.pi * 360.0 * t) +
            0.1 * np.random.normal(0, 0.05, sr)
        ).astype(np.float32)

    # Warm-up run
    for _ in range(5):
        extractor.extract(audio_data)

    latencies = []
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["run_index", "timestamp_iso", "duration_ms", "speech_detected", "f0_mean_hz", "jitter_local", "shimmer_local"])

        for i in range(1, iterations + 1):
            t0 = time.perf_counter()
            res = extractor.extract(audio_data)
            t1 = time.perf_counter()

            duration_ms = (t1 - t0) * 1000.0
            latencies.append(duration_ms)
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

            writer.writerow([
                i,
                now_iso,
                f"{duration_ms:.3f}",
                res.get("speech_detected", False),
                f"{res.get('f0_mean_hz', 0.0):.2f}",
                f"{res.get('jitter_local', 0.0):.4f}",
                f"{res.get('shimmer_local', 0.0):.4f}"
            ])

    mean_ms = np.mean(latencies)
    p50_ms = np.median(latencies)
    p95_ms = np.percentile(latencies, 95)
    max_ms = np.max(latencies)

    print(f"[VOCAL BENCHMARK] {iterations} runs completed:")
    print(f"  Mean: {mean_ms:.2f} ms | p50: {p50_ms:.2f} ms | p95: {p95_ms:.2f} ms | Max: {max_ms:.2f} ms")
    print(f"  Saved raw evidence: {out_csv}")
    return out_csv


def benchmark_db(iterations: int = 100) -> str:
    from parlor.db import log_assessment, init_db
    test_db = os.path.join(EVIDENCE_DIR, "benchmark_wellness.db")
    import gc
    gc.collect()
    try:
        if os.path.exists(test_db):
            os.remove(test_db)
    except Exception:
        pass
    init_db(test_db)

    out_csv = os.path.join(EVIDENCE_DIR, "db_write_latency.csv")
    dummy_slm = {
        "stress_level": "Moderate (Tier 1)",
        "confidence_score": 0.88,
        "primary_drivers": ["Pitch F0 Delta=+45Hz", "AU04 Brow Furrow=0.62"],
        "explainable_reasoning": "Elevated cognitive strain observed across visual and acoustic biomarkers."
    }

    latencies = []
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["run_index", "timestamp_iso", "duration_ms", "status"])

        for i in range(1, iterations + 1):
            t0 = time.perf_counter()
            log_assessment(dummy_slm, db_path=test_db)
            t1 = time.perf_counter()

            duration_ms = (t1 - t0) * 1000.0
            latencies.append(duration_ms)
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

            writer.writerow([i, now_iso, f"{duration_ms:.3f}", "SUCCESS"])

    import gc
    gc.collect()
    try:
        if os.path.exists(test_db):
            os.remove(test_db)
    except Exception:
        pass

    mean_ms = np.mean(latencies)
    p50_ms = np.median(latencies)
    p95_ms = np.percentile(latencies, 95)
    max_ms = np.max(latencies)

    print(f"[DB WRITE BENCHMARK] {iterations} runs completed:")
    print(f"  Mean: {mean_ms:.2f} ms | p50: {p50_ms:.2f} ms | p95: {p95_ms:.2f} ms | Max: {max_ms:.2f} ms")
    print(f"  Saved raw evidence: {out_csv}")
    return out_csv


if __name__ == "__main__":
    benchmark_facial(100)
    benchmark_vocal(100)
    benchmark_db(100)
