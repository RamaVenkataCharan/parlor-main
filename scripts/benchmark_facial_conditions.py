import cv2
import time
import numpy as np
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from parlor.facial import FacialExtractor

extractor = FacialExtractor()

# Try reading from real webcam
webcam_frame = None
try:
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            webcam_frame = cv2.resize(frame, (640, 480))
        cap.release()
except Exception as e:
    print(f"Webcam capture notice: {e}")

# Load Grace Hopper real face fixture
img_path = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages", "matplotlib", "mpl-data", "sample_data", "grace_hopper.jpg")
if not os.path.exists(img_path):
    # Try alternate location
    img_path = r"C:\Users\ramav\Documents\PROJECTS\parlor\parlor-main-main\.venv\Lib\site-packages\matplotlib\mpl-data\sample_data\grace_hopper.jpg"

face_img = cv2.imread(img_path)
face_img = cv2.resize(face_img, (640, 480))
blank_img = np.full((480, 640, 3), 200, dtype=np.uint8)

# Dim lighting (scale intensity down to 15%)
dim_img = (face_img.astype(np.float32) * 0.15).astype(np.uint8)

# Head turned ~30 deg
h, w = face_img.shape[:2]
M = cv2.getRotationMatrix2D((w / 2, h / 2), 30, 1.0)
turned_img = cv2.warpAffine(face_img, M, (w, h))

def benchmark_cond(name, img, n=100):
    for _ in range(5):
        extractor.extract(img)
    times = []
    results = []
    for _ in range(n):
        t0 = time.perf_counter()
        r = extractor.extract(img)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
        results.append(r)
    last = results[-1]
    mean_lat = np.mean(times)
    p50_lat = np.median(times)
    p95_lat = np.percentile(times, 95)
    max_lat = np.max(times)
    print(f"Condition: {name}")
    print(f"  Face Detected : {last['face_detected']}")
    print(f"  AU04 Brow     : {last['au04_brow_furrow']}")
    print(f"  AU07 Lid      : {last['au07_lid_tightener']}")
    print(f"  AU15 Lip Depr : {last['au15_lip_depressor']}")
    print(f"  AU20 Lip Str  : {last['au20_lip_stretcher']}")
    print(f"  EAR Ratio     : {last['ear']}")
    print(f"  Head Pose     : Pitch={last['head_pitch']} deg, Yaw={last['head_yaw']} deg, Roll={last['head_roll']} deg")
    print(f"  Latency (N={n}): Mean={mean_lat:.2f} ms | p50={p50_lat:.2f} ms | p95={p95_lat:.2f} ms | Max={max_lat:.2f} ms\n")
    return {
        "name": name,
        "face_detected": last['face_detected'],
        "au04": last['au04_brow_furrow'],
        "au07": last['au07_lid_tightener'],
        "au15": last['au15_lip_depressor'],
        "au20": last['au20_lip_stretcher'],
        "ear": last['ear'],
        "pitch": last['head_pitch'],
        "yaw": last['head_yaw'],
        "roll": last['head_roll'],
        "mean_ms": mean_lat,
        "p50_ms": p50_lat,
        "p95_ms": p95_lat,
        "max_ms": max_lat,
        "samples": times,
        "results": results
    }

print("===========================================================================")
print("      FACIAL EXTRACTION TIMING & ROBUSTNESS BENCHMARK")
print("===========================================================================")
r_blank = benchmark_cond("1. Blank / Empty Frame (No Face)", blank_img, 100)
r_face = benchmark_cond("2. Real Face - Normal Lighting (640x480)", face_img, 100)
r_dim = benchmark_cond("3. Real Face - Dim Lighting (15% Lux)", dim_img, 100)
r_turned = benchmark_cond("4. Real Face - Head Turned ~30 deg", turned_img, 100)

if webcam_frame is not None:
    r_cam = benchmark_cond("5. Live Webcam Real Frame (CAP_DSHOW)", webcam_frame, 100)
else:
    print("Live webcam frame was not captured.")
