"""
step4_5_combined_pipeline.py — Real-Time Multimodal (Webcam + Mic) Combined Feature Extraction Pipeline.

Captures camera frames via OpenCV/MediaPipe (src/parlor/facial.py) and audio via sounddevice/librosa (step3_audio_features.py)
concurrently over rolling 8-second observation windows, writing combined vectors atomically to shared_state/latest_features.json.
"""

import json
import os
import sys
import time
import numpy as np

# Import Person A's existing facial feature extractor
try:
    from parlor.facial import FacialExtractor
except ImportError:
    # If running from root without package installation
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
    from parlor.facial import FacialExtractor

# Import Person A's existing audio feature extractor
from step3_audio_features import AudioFeatureExtractor, HAS_SOUNDDEVICE

# Try importing cv2 for webcam
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


SHARED_FILE_PATH = "shared_state/latest_features.json"
TEMP_FILE_PATH = "shared_state/latest_features.json.tmp"


def write_features_atomically(combined_vector: dict):
    """Writes combined feature vector to shared_state/latest_features.json atomically using temp file rename."""
    os.makedirs("shared_state", exist_ok=True)
    with open(TEMP_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(combined_vector, f, indent=2)
    os.replace(TEMP_FILE_PATH, SHARED_FILE_PATH)


def run_combined_pipeline(duration_s=8.0, sr=16000):
    print(f"=== STARTING COMBINED MULTIMODAL PIPELINE ===")
    print(f"Webcam (OpenCV/MediaPipe FaceMesh): {'AVAILABLE' if HAS_CV2 else 'NOT AVAILABLE (Fallback)'}")
    print(f"Microphone (sounddevice @ {sr}Hz): {'AVAILABLE' if HAS_SOUNDDEVICE else 'NOT AVAILABLE (Fallback)'}")

    facial_extractor = FacialExtractor()
    audio_extractor = AudioFeatureExtractor(sr=sr, window_duration_s=duration_s)

    # Initialize webcam capture if available
    cap = None
    if HAS_CV2:
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("[WARNING] Could not open camera device 0. Falling back to camera placeholders.")
                cap = None
        except Exception as e:
            print(f"[WARNING] Camera initialization error: {e}")
            cap = None

    buffer_samples = int(sr * duration_s)
    cycle = 1

    try:
        while True:
            t_start = time.time()
            print(f"\n[Cycle {cycle}] Sampling multimodal window ({duration_s}s)...", end="", flush=True)

            face_frames_res = []

            # Capture webcam frame samples during the window
            if cap is not None:
                # Sample 5 frames spaced across the window
                for _ in range(5):
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        res = facial_extractor.extract(frame)
                        face_frames_res.append(res)
                    time.sleep(0.1)

            # Capture mic audio buffer if sounddevice is available
            audio_data = None
            if HAS_SOUNDDEVICE:
                try:
                    import sounddevice as sd
                    audio_data = sd.rec(buffer_samples, samplerate=sr, channels=1, dtype='float32')
                    sd.wait()
                    audio_data = audio_data.flatten()
                except Exception as e:
                    print(f" [Mic error: {e}]", end="")
                    audio_data = None

            # Process audio features
            if audio_data is not None:
                audio_res = audio_extractor.process_buffer(audio_data)
            else:
                # Fallback to zero buffer if no mic available
                audio_res = audio_extractor.process_buffer(np.zeros(buffer_samples, dtype=np.float32))

            # Process facial features
            valid_faces = [f for f in face_frames_res if f.get("face_detected", False)]
            if valid_faces:
                face_detected = True
                au04_brow = round(float(np.mean([f["au04_brow_furrow"] for f in valid_faces])), 4)
                au07_lid = round(float(np.mean([f["au07_lid_tightener"] for f in valid_faces])), 4)
                au15_lip = round(float(np.mean([f["au15_lip_depressor"] for f in valid_faces])), 4)
                au20_lip = round(float(np.mean([f["au20_lip_stretcher"] for f in valid_faces])), 4)
                ear = round(float(np.mean([f["ear"] for f in valid_faces])), 4)
                
                # Derive secondary metrics
                blinks = sum(1 for f in valid_faces if f.get("ear", 0.3) < 0.20)
                blink_rate_per_min = round(blinks * (60.0 / duration_s), 1)
                brow_tension = au04_brow
                jaw_tension_var = round(float(np.var([f["au20_lip_stretcher"] for f in valid_faces])), 4)
            else:
                face_detected = False
                au04_brow = 0.0
                au07_lid = 0.0
                au15_lip = 0.0
                au20_lip = 0.0
                ear = 0.30
                blink_rate_per_min = 0.0
                brow_tension = 0.0
                jaw_tension_var = 0.0

            # Construct unified schema
            combined_vector = {
                "timestamp": time.time(),
                "face": {
                    "face_detected": face_detected,
                    "au04_brow_furrow": au04_brow,
                    "au07_lid_tightener": au07_lid,
                    "au15_lip_depressor": au15_lip,
                    "au20_lip_stretcher": au20_lip,
                    "ear": ear,
                    "blink_rate_per_min": blink_rate_per_min,
                    "brow_tension": brow_tension,
                    "jaw_tension_variance": jaw_tension_var
                },
                "audio": {
                    "voice_detected": audio_res.get("voice_detected", False),
                    "pitch_variance": audio_res.get("pitch_variance", 0.0),
                    "speech_rate_proxy": audio_res.get("speech_rate_proxy", 0.0),
                    "energy_jitter": audio_res.get("energy_jitter", 0.0)
                }
            }

            # Write combined vector atomically to disk
            write_features_atomically(combined_vector)
            print(" Done!")
            print(json.dumps(combined_vector, indent=2))
            cycle += 1

            # Ensure 8s loop pace
            elapsed = time.time() - t_start
            if elapsed < duration_s:
                time.sleep(duration_s - elapsed)

    except KeyboardInterrupt:
        print("\nStopping combined pipeline.")
    finally:
        if cap is not None:
            cap.release()


if __name__ == "__main__":
    run_combined_pipeline()
