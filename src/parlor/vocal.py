"""Vocal Biomarker Extraction Pipeline.

Extracts real-time acoustic biomarkers (Pitch F0, Pitch Variance F0_SD, Jitter,
Shimmer, Speech Rate / Pause Ratio, and Vocal Tension Index) from 16kHz audio streams.
Uses numpy & scipy signal processing for lightweight execution on both Laptop and Pi hardware.
Includes robust handling for silent frames, brief speech chunks, and background noise.
"""

import time
from typing import Dict, Any, Union
import numpy as np

try:
    from scipy.signal import find_peaks
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class VocalExtractor:
    """Extracts acoustic biomarkers from 16kHz PCM audio buffers."""

    def __init__(self, sample_rate: int = 16000, min_window_sec: float = 1.0):
        self.sample_rate = sample_rate
        self.min_samples = int(sample_rate * min_window_sec)
        self.scipy_available = SCIPY_AVAILABLE

    def extract(self, pcm_data: Union[np.ndarray, bytes, list]) -> Dict[str, Any]:
        """Extract vocal biomarkers from 16kHz audio PCM data.
        
        Returns:
            Dict containing:
                - speech_detected: bool
                - rms_energy: float (0.0 to 1.0)
                - f0_mean_hz: float (Fundamental frequency, typically 80-350 Hz)
                - f0_std_hz: float (Pitch variance, indicator of micro-tremors)
                - jitter_local: float (Percentage cycle-to-cycle period variation)
                - shimmer_local: float (Percentage cycle-to-cycle amplitude variation)
                - pause_ratio: float (0.0 to 1.0, ratio of silence in window)
                - vocal_tension_index: float (High-frequency energy ratio >1kHz)
                - latency_ms: float
        """
        t0 = time.time()
        fallback_res = {
            "speech_detected": False,
            "rms_energy": 0.0,
            "f0_mean_hz": 0.0,
            "f0_std_hz": 0.0,
            "jitter_local": 0.0,
            "shimmer_local": 0.0,
            "pause_ratio": 1.0,
            "vocal_tension_index": 0.0,
            "latency_ms": 0.0
        }

        # Convert input to float32 numpy array normalized to [-1.0, 1.0]
        if isinstance(pcm_data, bytes):
            audio = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0
        elif isinstance(pcm_data, list):
            audio = np.array(pcm_data, dtype=np.float32)
        elif isinstance(pcm_data, np.ndarray):
            if pcm_data.dtype == np.int16:
                audio = pcm_data.astype(np.float32) / 32768.0
            else:
                audio = pcm_data.astype(np.float32)
        else:
            fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
            return fallback_res

        if len(audio) < self.min_samples:
            fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
            return fallback_res

        # RMS Energy check
        rms = float(np.sqrt(np.mean(audio ** 2)))
        fallback_res["rms_energy"] = round(rms, 4)

        if rms < 0.005:  # Silence threshold
            fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
            return fallback_res

        try:
            # 1. Framing: 25ms frame, 10ms hop
            frame_len = int(self.sample_rate * 0.025)
            hop_len = int(self.sample_rate * 0.010)
            n_frames = (len(audio) - frame_len) // hop_len + 1

            if n_frames < 5:
                fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
                return fallback_res

            f0_list = []
            frame_amplitudes = []
            voiced_frames = 0

            # Pitch bounds for human voice: 75 Hz to 400 Hz
            min_lag = int(self.sample_rate / 400)
            max_lag = int(self.sample_rate / 75)

            for i in range(n_frames):
                start = i * hop_len
                frame = audio[start:start + frame_len]
                frame_rms = np.sqrt(np.mean(frame ** 2))

                if frame_rms < 0.008:
                    continue  # Unvoiced / silence frame

                # Autocorrelation for F0 pitch estimation
                autocorr = np.correlate(frame, frame, mode='full')
                autocorr = autocorr[len(frame)-1:]
                
                if len(autocorr) > max_lag:
                    search_corr = autocorr[min_lag:max_lag]
                    peak_idx = np.argmax(search_corr) + min_lag
                    peak_val = autocorr[peak_idx]

                    # Voiced decision threshold
                    if autocorr[0] > 1e-5 and (peak_val / autocorr[0]) > 0.35:
                        f0 = self.sample_rate / peak_idx
                        f0_list.append(f0)
                        frame_amplitudes.append(np.max(np.abs(frame)))
                        voiced_frames += 1

            pause_ratio = float(1.0 - (voiced_frames / max(n_frames, 1)))

            if not f0_list or voiced_frames < 3:
                fallback_res["pause_ratio"] = round(pause_ratio, 4)
                fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
                return fallback_res

            f0_arr = np.array(f0_list)
            f0_mean = float(np.mean(f0_arr))
            f0_std = float(np.std(f0_arr))

            # 2. Local Jitter (|T_i - T_{i+1}| / T_avg)
            periods = 1.0 / f0_arr
            if len(periods) > 1:
                period_diffs = np.abs(np.diff(periods))
                jitter_local = float((np.mean(period_diffs) / np.mean(periods)) * 100.0)
            else:
                jitter_local = 0.0

            # 3. Local Shimmer (|A_i - A_{i+1}| / A_avg)
            amp_arr = np.array(frame_amplitudes)
            if len(amp_arr) > 1:
                amp_diffs = np.abs(np.diff(amp_arr))
                shimmer_local = float((np.mean(amp_diffs) / max(np.mean(amp_arr), 1e-5)) * 100.0)
            else:
                shimmer_local = 0.0

            # 4. Vocal Tension Index: High frequency energy (>1kHz) / Total Energy
            fft_mag = np.abs(np.fft.rfft(audio))
            freqs = np.fft.rfftfreq(len(audio), 1.0 / self.sample_rate)
            hf_mask = freqs >= 1000.0
            total_energy = np.sum(fft_mag ** 2)
            hf_energy = np.sum(fft_mag[hf_mask] ** 2)
            vocal_tension = float(hf_energy / max(total_energy, 1e-5))

            latency = round((time.time() - t0) * 1000, 2)
            return {
                "speech_detected": True,
                "rms_energy": round(rms, 4),
                "f0_mean_hz": round(f0_mean, 2),
                "f0_std_hz": round(f0_std, 2),
                "jitter_local": round(jitter_local, 4),
                "shimmer_local": round(shimmer_local, 4),
                "pause_ratio": round(pause_ratio, 4),
                "vocal_tension_index": round(vocal_tension, 4),
                "latency_ms": latency
            }
        except Exception as e:
            print(f"[VOCAL EXTRACTION ERROR] {e}")
            fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
            return fallback_res
