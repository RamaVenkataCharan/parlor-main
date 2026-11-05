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


def test_no_media_written_to_disk(tmp_path):
    """Verify that feature extraction, full wellness cycles, and DB persistence never write raw media to disk."""
    import os
    import asyncio
    from unittest.mock import patch
    from parlor import db
    from parlor.wellness import WellnessService

    # 1. Capture list of media files in workspace before processing
    extensions = {".png", ".jpg", ".jpeg", ".bmp", ".wav", ".pcm", ".y4m", ".mp4", ".raw"}
    media_before = {
        os.path.join(root, f)
        for root, _, files in os.walk(".")
        for f in files
        if os.path.splitext(f)[1].lower() in extensions
    }

    # 2. Execute facial and vocal extraction with active non-zero data
    facial = FacialExtractor()
    vocal = VocalExtractor()
    test_img = np.ones((480, 640, 3), dtype=np.uint8) * 128
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    test_audio = (0.3 * np.sin(2 * np.pi * 220.0 * t)).astype(np.float32)

    f_res = facial.extract(test_img)
    v_res = vocal.extract(test_audio)

    # 3. Execute a full end-to-end WellnessService cycle with active camera frame and audio buffer
    test_db = str(tmp_path / "test_wellness.db")
    db.init_db(test_db)
    service = WellnessService(cycle_interval_sec=1.0)
    service.concurrency_mitigation_enabled = False
    service.feed_frame(test_img)
    service.feed_audio(test_audio)

    mock_slm_output = {
        "stress_level": "Low (Tier 0)",
        "primary_drivers": ["Normal brow=0.1", "Stable voice pitch"],
        "explainable_reasoning": "Baseline calm affective state",
        "confidence_score": 0.95,
        "ambiguity_note": None
    }

    async def _run_wellness_cycle():
        with patch("parlor.db.DEFAULT_DB_PATH", test_db), \
             patch.object(service, "_call_slm_reasoning", return_value=mock_slm_output):
            await service.step_cycle()

    asyncio.run(_run_wellness_cycle())

    # 4. Check for any newly created media files across the entire workspace
    media_after = {
        os.path.join(root, f)
        for root, _, files in os.walk(".")
        for f in files
        if os.path.splitext(f)[1].lower() in extensions
    }

    new_media = media_after - media_before
    assert len(new_media) == 0, f"Raw media files were unexpectedly written to disk: {new_media}"
