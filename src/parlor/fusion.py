"""Multimodal Feature Fusion Engine for Explainable SLM Stress Reasoning.

Fuses facial micro-expression features (from facial.py) and vocal acoustic biomarkers
(from vocal.py) over a rolling window buffer into a structured, interpretable Markdown prompt.
Generates structured system prompts demanding explainable reasoning, primary biomarker citation,
and confidence/ambiguity evaluations.
"""

from collections import deque
from typing import Dict, Any, List, Optional
import numpy as np


EXPLAINABLE_SYSTEM_PROMPT = (
    "You are an expert Affective Neuroscience & Stress Monitoring AI. "
    "Analyze the provided multimodal feature vector (vocal acoustic biomarkers and facial Action Units). "
    "Your evaluation must be structured, grounded strictly in the numerical signals provided, and fully explainable.\n\n"
    "Respond using the following JSON schema:\n"
    "{\n"
    '  "stress_level": "Low (Tier 0)" | "Moderate (Tier 1)" | "High (Tier 2)",\n'
    '  "primary_drivers": ["biomarker 1 (e.g. AU04 Brow Furrow=0.78)", "biomarker 2 (e.g. Pitch F0 Delta=+39Hz)"],\n'
    '  "explainable_reasoning": "Clear 2-3 sentence clinical explanation linking observed signals to physiological tension.",\n'
    '  "confidence_score": 0.0 to 1.0,\n'
    '  "ambiguity_note": "Note any conflicting signals or missing face/audio data, else None"\n'
    "}"
)


class FeatureFusionEngine:
    """Aggregates rolling windows of facial & vocal feature dicts and formats them into SLM prompts."""

    def __init__(self, window_size: int = 5, f0_baseline_hz: float = 145.0):
        self.window_size = window_size
        self.f0_baseline_hz = f0_baseline_hz
        self.facial_history = deque(maxlen=window_size)
        self.vocal_history = deque(maxlen=window_size)

    def add_frame(self, facial_features: Dict[str, Any], vocal_features: Dict[str, Any]) -> None:
        """Push new facial and vocal feature dicts into the rolling buffer."""
        if facial_features:
            self.facial_history.append(facial_features)
        if vocal_features:
            self.vocal_history.append(vocal_features)

    def clear(self) -> None:
        """Clear rolling buffer history."""
        self.facial_history.clear()
        self.vocal_history.clear()

    def aggregate_features(self) -> Dict[str, Any]:
        """Aggregate history buffer into mean/max normalized metrics."""
        # 1. Aggregate Facial Features
        valid_faces = [f for f in self.facial_history if f.get("face_detected", False)]
        if valid_faces:
            face_detected = True
            face_conf = float(np.mean([f.get("confidence", 0.95) for f in valid_faces]))
            au04 = float(np.max([f.get("au04_brow_furrow", 0.0) for f in valid_faces]))
            au07 = float(np.mean([f.get("au07_lid_tightener", 0.0) for f in valid_faces]))
            au15 = float(np.mean([f.get("au15_lip_depressor", 0.0) for f in valid_faces]))
            au20 = float(np.mean([f.get("au20_lip_stretcher", 0.0) for f in valid_faces]))
            ear = float(np.mean([f.get("ear", 0.30) for f in valid_faces]))
            pitch = float(np.mean([f.get("head_pitch", 0.0) for f in valid_faces]))
            yaw = float(np.mean([f.get("head_yaw", 0.0) for f in valid_faces]))
            roll = float(np.mean([f.get("head_roll", 0.0) for f in valid_faces]))
        else:
            face_detected = False
            face_conf = 0.0
            au04, au07, au15, au20 = 0.0, 0.0, 0.0, 0.0
            ear = 0.30
            pitch, yaw, roll = 0.0, 0.0, 0.0

        # 2. Aggregate Vocal Features
        valid_voices = [v for v in self.vocal_history if v.get("speech_detected", False)]
        if valid_voices:
            speech_detected = True
            rms = float(np.mean([v.get("rms_energy", 0.0) for v in valid_voices]))
            f0_mean = float(np.mean([v.get("f0_mean_hz", 0.0) for v in valid_voices]))
            f0_std = float(np.mean([v.get("f0_std_hz", 0.0) for v in valid_voices]))
            jitter = float(np.max([v.get("jitter_local", 0.0) for v in valid_voices]))
            shimmer = float(np.max([v.get("shimmer_local", 0.0) for v in valid_voices]))
            pause_ratio = float(np.mean([v.get("pause_ratio", 1.0) for v in valid_voices]))
            tension = float(np.mean([v.get("vocal_tension_index", 0.0) for v in valid_voices]))
        else:
            speech_detected = False
            rms = 0.0
            f0_mean = 0.0
            f0_std = 0.0
            jitter = 0.0
            shimmer = 0.0
            pause_ratio = 1.0
            tension = 0.0

        f0_delta = round(f0_mean - self.f0_baseline_hz, 1) if speech_detected else 0.0

        return {
            "window_samples": max(len(self.facial_history), len(self.vocal_history)),
            "face_detected": face_detected,
            "face_confidence": round(face_conf, 2),
            "au04_brow_furrow": round(au04, 3),
            "au07_lid_tightener": round(au07, 3),
            "au15_lip_depressor": round(au15, 3),
            "au20_lip_stretcher": round(au20, 3),
            "ear": round(ear, 3),
            "head_pitch": round(pitch, 1),
            "head_yaw": round(yaw, 1),
            "head_roll": round(roll, 1),
            "speech_detected": speech_detected,
            "rms_energy": round(rms, 4),
            "f0_mean_hz": round(f0_mean, 1),
            "f0_baseline_hz": self.f0_baseline_hz,
            "f0_delta_hz": f0_delta,
            "f0_std_hz": round(f0_std, 1),
            "jitter_local_pct": round(jitter, 2),
            "shimmer_local_pct": round(shimmer, 2),
            "pause_ratio": round(pause_ratio, 2),
            "vocal_tension_index": round(tension, 3)
        }

    def format_prompt(self, agg: Optional[Dict[str, Any]] = None) -> str:
        """Format aggregated feature vector into a structured Markdown prompt for the SLM."""
        if agg is None:
            agg = self.aggregate_features()

        face_status = "DETECTED" if agg["face_detected"] else "NOT DETECTED / POOR LIGHTING"
        speech_status = "DETECTED" if agg["speech_detected"] else "SILENCE / NO SPEECH"

        prompt = f"""[MULTIMODAL AFFECTIVE FEATURE VECTOR - ROLLING WINDOW ({agg['window_samples']} SAMPLES)]

--- FACIAL MICRO-EXPRESSIONS (MediaPipe FaceMesh) ---
- Status: {face_status} (Confidence: {agg['face_confidence']})
- AU04 Brow Furrow (Eyebrow Tension): {agg['au04_brow_furrow']} (0.0=Relaxed, >0.5=Elevated Furrow)
- AU07 Lid Tightener (Eye Squint/Strain): {agg['au07_lid_tightener']} (0.0=Relaxed, >0.5=Squinting)
- AU15 Lip Depressor (Mouth Corner Drop): {agg['au15_lip_depressor']} (0.0=Neutral, >0.4=Depressed)
- AU20 Lip Stretcher (Jaw Tension): {agg['au20_lip_stretcher']} (0.0=Neutral, >0.5=Stretched)
- Eye Aspect Ratio (EAR): {agg['ear']} (Normal: 0.28-0.35, <0.20=Eye Closure/Blink)
- Head Pose: Pitch={agg['head_pitch']}°, Yaw={agg['head_yaw']}°, Roll={agg['head_roll']}°

--- VOCAL ACOUSTIC BIOMARKERS (16kHz Audio) ---
- Status: {speech_status} (RMS Energy: {agg['rms_energy']})
- Pitch Mean (F0): {agg['f0_mean_hz']} Hz (Baseline: {agg['f0_baseline_hz']} Hz, Delta: {agg['f0_delta_hz']:+} Hz)
- Pitch Variance (F0 SD): {agg['f0_std_hz']} Hz (Micro-tremor indicator)
- Local Jitter (Period Perturbation): {agg['jitter_local_pct']}% (Normal <1.5%, High >3.0%)
- Local Shimmer (Amplitude Perturbation): {agg['shimmer_local_pct']}% (Normal <2.0%, High >3.5%)
- Pause Ratio: {agg['pause_ratio']} (0.0=Constant Speech, 1.0=Full Silence)
- Vocal Tension Index (HF Energy >1kHz Ratio): {agg['vocal_tension_index']} (Normal <0.40, High >0.65)

TASK: Evaluate the physiological and behavioral stress state based strictly on the biomarkers above. Output the JSON schema with stress level, primary drivers, explainable reasoning, confidence score, and ambiguity notes.
"""
        return prompt
