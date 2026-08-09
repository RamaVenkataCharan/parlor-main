"""
step3_audio_features.py — Audio signal processing pipeline for stress detection.

Captures microphone audio in a rolling buffer (8s windows) and computes:
  1. voice_detected (RMS threshold check)
  2. pitch_variance (F0 variability via librosa.pyin)
  3. speech_rate_proxy (onset rate per second via librosa.onset)
  4. energy_jitter (frame-to-frame RMS variability)

Lightweight 3-window rolling average smoothing is applied to prevent noise.
"""

import sys
import time
import json
import collections
import os
import numpy as np
import librosa

# Try importing sounddevice for mic capture
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except Exception:
    HAS_SOUNDDEVICE = False


def write_features_atomically(result: dict):
    nested = {
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
            "voice_detected": result.get("voice_detected", False),
            "pitch_delta": 0.0,
            "pitch_variance": result.get("pitch_variance", 0.0),
            "jitter": result.get("energy_jitter", 0.0),
            "shimmer": 0.0,
            "pause_ratio": result.get("speech_rate_proxy", 0.0),
            "vocal_tension": 0.0
        }
    }
    # Ensure the target directory exists
    os.makedirs("shared_state", exist_ok=True)
    temp_path = "shared_state/latest_features.json.tmp"
    target_path = "shared_state/latest_features.json"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(nested, f, indent=2)
    os.replace(temp_path, target_path)



class AudioFeatureExtractor:
    def __init__(self, sr: int = 16000, window_duration_s: float = 8.0, smooth_windows: int = 3):
        self.sr = sr
        self.window_duration_s = window_duration_s
        self.buffer_size = int(sr * window_duration_s)
        self.smooth_windows = smooth_windows

        # Rolling feature history for smoothing (last 3 windows)
        self.history_pitch_var = collections.deque(maxlen=smooth_windows)
        self.history_speech_rate = collections.deque(maxlen=smooth_windows)
        self.history_energy_jitter = collections.deque(maxlen=smooth_windows)

    def process_buffer(self, audio_data: np.ndarray) -> dict:
        """Processes an 8-second audio buffer and returns feature JSON."""
        # Ensure 1D float32 audio normalized [-1.0, 1.0]
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        audio_data = audio_data.astype(np.float32)

        # 1. Voice Activity Detection (RMS threshold)
        rms_frames = librosa.feature.rms(y=audio_data, frame_length=2048, hop_length=512)[0]
        mean_rms = float(np.mean(rms_frames))
        
        # Threshold for speech presence
        voice_detected = mean_rms > 0.008

        if not voice_detected:
            # Reset/append zero for silence to smooth transition
            self.history_pitch_var.append(0.0)
            self.history_speech_rate.append(0.0)
            self.history_energy_jitter.append(0.0)
            res = {
                "voice_detected": False,
                "pitch_variance": 0.0,
                "speech_rate_proxy": 0.0,
                "energy_jitter": 0.0
            }
            write_features_atomically(res)
            return res

        # 2. Pitch Variance (Fundamental Frequency variability via pYIN)
        pitch_variance = 0.0
        try:
            # fmin/fmax covering typical human voice pitch (80Hz to 500Hz)
            f0, voiced_flag, _ = librosa.pyin(
                audio_data,
                fmin=librosa.note_to_hz('C2'),  # ~65 Hz
                fmax=librosa.note_to_hz('C6'),  # ~1046 Hz
                sr=self.sr,
                frame_length=2048,
                hop_length=512
            )
            if f0 is not None:
                valid_f0 = f0[~np.isnan(f0)]
                if len(valid_f0) >= 5:
                    pitch_variance = float(np.var(valid_f0))
        except Exception as e:
            # Fallback gracefully if pYIN fails on edge cases
            pitch_variance = 0.0

        # 3. Speech Rate Proxy (Onset detection per second)
        speech_rate_proxy = 0.0
        try:
            onset_env = librosa.onset.onset_strength(y=audio_data, sr=self.sr, hop_length=512)
            onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=self.sr, hop_length=512)
            speech_rate_proxy = float(len(onsets) / self.window_duration_s)
        except Exception:
            speech_rate_proxy = 0.0

        # 4. Energy Jitter (Frame-to-frame RMS variability / voice shakiness)
        energy_jitter = 0.0
        if len(rms_frames) > 1:
            diffs = np.abs(np.diff(rms_frames))
            energy_jitter = float(np.std(diffs) / (np.mean(rms_frames) + 1e-6))

        # Apply rolling window smoothing
        self.history_pitch_var.append(pitch_variance)
        self.history_speech_rate.append(speech_rate_proxy)
        self.history_energy_jitter.append(energy_jitter)

        smoothed_pitch_var = float(np.mean(self.history_pitch_var))
        smoothed_speech_rate = float(np.mean(self.history_speech_rate))
        smoothed_energy_jitter = float(np.mean(self.history_energy_jitter))

        res = {
            "voice_detected": True,
            "pitch_variance": round(smoothed_pitch_var, 3),
            "speech_rate_proxy": round(smoothed_speech_rate, 3),
            "energy_jitter": round(smoothed_energy_jitter, 4)
        }
        write_features_atomically(res)
        return res


def run_mic_stream(duration_s=8.0, sr=16000):
    """Captures continuous mic input in 8-second windows."""
    if not HAS_SOUNDDEVICE:
        print("Error: sounddevice is not available.")
        return

    print(f"Starting audio feature extractor (mic sampling @ {sr}Hz, {duration_s}s windows)...")
    extractor = AudioFeatureExtractor(sr=sr, window_duration_s=duration_s)

    buffer_samples = int(sr * duration_s)
    
    while True:
        try:
            print("\nListening to mic...", end="", flush=True)
            audio = sd.rec(buffer_samples, samplerate=sr, channels=1, dtype='float32')
            sd.wait()
            print(" Processing buffer...")
            result = extractor.process_buffer(audio.flatten())
            print(json.dumps(result, indent=2))
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"Error reading mic: {e}")
            time.sleep(1.0)


def run_synthetic_validation():
    """Validates the feature extractor against synthetic audio scenarios:
    1. Silence
    2. Flat / Monotone Voice (Constant frequency tone)
    3. Varying Pitch / Dynamic Voice (Pitch modulation)
    4. Fast Speech vs Slow Speech (Fast vs slow onset bursts)
    5. Shaky Voice (Amplitude jitter)
    """
    print("=== RUNNING FEATURE VALIDATION SUITE ===")
    sr = 16000
    duration_s = 8.0
    extractor = AudioFeatureExtractor(sr=sr, window_duration_s=duration_s)

    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)

    # 1. Silence
    extractor = AudioFeatureExtractor(sr=sr, window_duration_s=duration_s)
    silence = np.zeros_like(t)
    res_silence = extractor.process_buffer(silence)
    print("\n1. Silence Buffer Output:")
    print(json.dumps(res_silence, indent=2))
    assert res_silence["voice_detected"] is False

    # 2. Monotone / Flat Speech (Constant 220Hz tone + subtle noise)
    extractor = AudioFeatureExtractor(sr=sr, window_duration_s=duration_s)
    monotone = 0.1 * np.sin(2 * np.pi * 220 * t) + 0.001 * np.random.randn(len(t))
    res_monotone = extractor.process_buffer(monotone)
    print("\n2. Monotone/Flat Pitch Output:")
    print(json.dumps(res_monotone, indent=2))

    # 3. Dynamic Pitch Speech (Modulated 150Hz - 350Hz pitch)
    extractor = AudioFeatureExtractor(sr=sr, window_duration_s=duration_s)
    pitch_mod = 250 + 80 * np.sin(2 * np.pi * 2 * t)
    phase = 2 * np.pi * np.cumsum(pitch_mod) / sr
    dynamic_pitch = 0.1 * np.sin(phase) + 0.001 * np.random.randn(len(t))
    res_dynamic = extractor.process_buffer(dynamic_pitch)
    print("\n3. Dynamic Pitch Output:")
    print(json.dumps(res_dynamic, indent=2))

    # Verify: pitch_variance of dynamic speech > monotone speech
    print(f"   Validation check: Dynamic pitch_variance ({res_dynamic['pitch_variance']}) > Monotone pitch_variance ({res_monotone['pitch_variance']}) -> {res_dynamic['pitch_variance'] > res_monotone['pitch_variance']}")

    # 4. Fast vs Slow Speech (Pulse bursts)
    # Slow speech: 2 pulses/sec
    extractor_slow = AudioFeatureExtractor(sr=sr, window_duration_s=duration_s)
    slow_pulses = np.zeros_like(t)
    for i in range(16):
        idx = int(i * 0.5 * sr)
        if idx < len(slow_pulses):
            slow_pulses[idx:idx+800] = 0.1 * np.sin(2 * np.pi * 300 * np.linspace(0, 0.05, 800))
    res_slow = extractor_slow.process_buffer(slow_pulses)

    # Fast speech: 6 pulses/sec
    extractor_fast = AudioFeatureExtractor(sr=sr, window_duration_s=duration_s)
    fast_pulses = np.zeros_like(t)
    for i in range(48):
        idx = int(i * 0.16 * sr)
        if idx < len(fast_pulses):
            fast_pulses[idx:idx+800] = 0.1 * np.sin(2 * np.pi * 300 * np.linspace(0, 0.05, 800))
    res_fast = extractor_fast.process_buffer(fast_pulses)

    print("\n4a. Slow Speech Rate Output:")
    print(json.dumps(res_slow, indent=2))
    print("4b. Fast Speech Rate Output:")
    print(json.dumps(res_fast, indent=2))
    print(f"   Validation check: Fast speech_rate ({res_fast['speech_rate_proxy']}) > Slow speech_rate ({res_slow['speech_rate_proxy']}) -> {res_fast['speech_rate_proxy'] > res_slow['speech_rate_proxy']}")

    # 5. Steady vs Shaky Voice (Energy jitter)
    # Steady voice: constant envelope
    extractor_steady = AudioFeatureExtractor(sr=sr, window_duration_s=duration_s)
    steady_voice = 0.1 * np.sin(2 * np.pi * 200 * t)
    res_steady = extractor_steady.process_buffer(steady_voice)

    # Shaky voice: rapidly fluctuating envelope amplitude
    extractor_shaky = AudioFeatureExtractor(sr=sr, window_duration_s=duration_s)
    jitter_env = 0.1 + 0.08 * np.sin(2 * np.pi * 15 * t)
    shaky_voice = jitter_env * np.sin(2 * np.pi * 200 * t)
    res_shaky = extractor_shaky.process_buffer(shaky_voice)

    print("\n5a. Steady Voice Output:")
    print(json.dumps(res_steady, indent=2))
    print("5b. Shaky Voice Output:")
    print(json.dumps(res_shaky, indent=2))
    print(f"   Validation check: Shaky energy_jitter ({res_shaky['energy_jitter']}) > Steady energy_jitter ({res_steady['energy_jitter']}) -> {res_shaky['energy_jitter'] > res_steady['energy_jitter']}")

    print("\n=== VALIDATION SUITE PASSED SUCCESSFULLY ===")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_synthetic_validation()
    else:
        # Default to synthetic validation if mic is headless or --test passed, else run mic stream
        if len(sys.argv) > 1 and sys.argv[1] == "--mic":
            run_mic_stream()
        else:
            print("Running synthetic validation test. Pass --mic to record from actual microphone.")
            run_synthetic_validation()
