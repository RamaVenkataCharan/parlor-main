"""Unit tests for Multimodal Feature Fusion Engine."""

import pytest
from parlor.fusion import FeatureFusionEngine, EXPLAINABLE_SYSTEM_PROMPT


def test_fusion_engine_empty_state():
    engine = FeatureFusionEngine()
    agg = engine.aggregate_features()
    assert agg["face_detected"] is False
    assert agg["speech_detected"] is False
    assert agg["au04_brow_furrow"] == 0.0
    assert agg["f0_delta_hz"] == 0.0
    
    prompt = engine.format_prompt(agg)
    assert "[MULTIMODAL AFFECTIVE FEATURE VECTOR" in prompt
    assert "NOT DETECTED" in prompt


def test_fusion_engine_with_sample_history():
    engine = FeatureFusionEngine(window_size=3, f0_baseline_hz=145.0)
    
    facial = {
        "face_detected": True,
        "confidence": 0.95,
        "au04_brow_furrow": 0.80,
        "au07_lid_tightener": 0.60,
        "au15_lip_depressor": 0.30,
        "au20_lip_stretcher": 0.50,
        "ear": 0.22,
        "head_pitch": -4.0,
        "head_yaw": 2.0,
        "head_roll": 0.0
    }
    
    vocal = {
        "speech_detected": True,
        "rms_energy": 0.05,
        "f0_mean_hz": 185.0,
        "f0_std_hz": 30.0,
        "jitter_local_pct": 3.2,
        "shimmer_local_pct": 4.1,
        "pause_ratio": 0.15,
        "vocal_tension_index": 0.65
    }
    
    engine.add_frame(facial, vocal)
    agg = engine.aggregate_features()
    
    assert agg["face_detected"] is True
    assert agg["speech_detected"] is True
    assert agg["au04_brow_furrow"] == 0.80
    assert agg["f0_delta_hz"] == 40.0  # 185.0 - 145.0
    
    prompt = engine.format_prompt(agg)
    assert "AU04 Brow Furrow (Eyebrow Tension): 0.8" in prompt
    assert "Pitch Mean (F0): 185.0 Hz" in prompt
