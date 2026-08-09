"""Unit & Integration Tests for Facial and Vocal Feature Extraction Pipelines."""

import numpy as np
import pytest
from parlor.facial import FacialExtractor
from parlor.vocal import VocalExtractor


def test_facial_extractor_fallback_on_empty_image():
    extractor = FacialExtractor()
    res = extractor.extract(None)
    assert res["face_detected"] is False
    assert res["confidence"] == 0.0
    assert "au04_brow_furrow" in res
    assert "latency_ms" in res
    assert res["latency_ms"] >= 0.0


def test_facial_extractor_with_blank_canvas():
    extractor = FacialExtractor()
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    res = extractor.extract(blank)
    assert res["face_detected"] is False
    assert res["au04_brow_furrow"] == 0.0


def test_vocal_extractor_fallback_on_silence():
    extractor = VocalExtractor()
    silence = np.zeros(16000, dtype=np.float32)
    res = extractor.extract(silence)
    assert res["speech_detected"] is False
    assert res["rms_energy"] == 0.0
    assert res["pause_ratio"] == 1.0


def test_vocal_extractor_with_sine_wave():
    extractor = VocalExtractor()
    sr = 16000
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    # Pure 200 Hz tone
    tone = (0.5 * np.sin(2 * np.pi * 200.0 * t)).astype(np.float32)
    res = extractor.extract(tone)
    assert res["speech_detected"] is True
    assert res["rms_energy"] > 0.1
    # Pitch should be close to 200 Hz
    assert 180.0 <= res["f0_mean_hz"] <= 220.0
    assert res["latency_ms"] < 100.0  # Fast execution < 100ms
