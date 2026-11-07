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

    # 1. Capture list of media files in workspace and temp dir before processing
    import tempfile
    extensions = {".png", ".jpg", ".jpeg", ".bmp", ".wav", ".pcm", ".y4m", ".mp4", ".raw", ".webm", ".bin", ".tmp"}
    scan_dirs = [".", tempfile.gettempdir()]
    media_before = {
        os.path.join(root, f)
        for d in scan_dirs
        for root, _, files in os.walk(d)
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

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(asyncio.run, _run_wellness_cycle()).result()
    else:
        asyncio.run(_run_wellness_cycle())

    # 4. Check for any newly created media files across the workspace and temp dir
    media_after = {
        os.path.join(root, f)
        for d in scan_dirs
        for root, _, files in os.walk(d)
        for f in files
        if os.path.splitext(f)[1].lower() in extensions
    }

    new_media = media_after - media_before
    assert len(new_media) == 0, f"Raw media files were unexpectedly written to disk: {new_media}"


def test_facial_head_pose_known_rotations():
    """Verify that solvePnP head pose estimation correctly recovers known Euler angles without flipping."""
    import cv2
    extractor = FacialExtractor()
    model = extractor.model_points_3d
    w, h = 640, 480
    focal = w
    cam = np.array([[focal, 0, w / 2], [0, focal, h / 2], [0, 0, 1]], dtype=np.float64)
    dist = np.zeros((4, 1))

    test_angles = [
        (0.0, 0.0, 0.0),       # Neutral / facing camera
        (15.0, 0.0, 0.0),      # Pitch down 15 deg
        (-15.0, 0.0, 0.0),     # Pitch up 15 deg
        (0.0, 20.0, 0.0),      # Yaw right 20 deg
        (0.0, -20.0, 0.0),     # Yaw left 20 deg
        (0.0, 0.0, 10.0),      # Roll 10 deg
    ]

    for pitch_exp, yaw_exp, roll_exp in test_angles:
        rx = np.radians(pitch_exp)
        ry = np.radians(yaw_exp)
        rz = np.radians(roll_exp)
        Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
        Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
        Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
        R = Rx @ Ry @ Rz
        rvec, _ = cv2.Rodrigues(R)
        tvec = np.array([[0.0], [0.0], [1000.0]])

        proj, _ = cv2.projectPoints(model, rvec, tvec, cam, dist)
        pts_2d = proj.reshape(-1, 2)

        success, rvec_est, _ = cv2.solvePnP(model, pts_2d, cam, dist, flags=cv2.SOLVEPNP_ITERATIVE)
        assert success is True
        rmat_est, _ = cv2.Rodrigues(rvec_est)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat_est)
        p_est = (angles[0] + 180.0) % 360.0 - 180.0
        y_est = (angles[1] + 180.0) % 360.0 - 180.0
        r_est = (angles[2] + 180.0) % 360.0 - 180.0

        assert abs(p_est - pitch_exp) < 1.5, f"Pitch mismatch: expected {pitch_exp}, got {p_est}"
        assert abs(y_est - yaw_exp) < 1.5, f"Yaw mismatch: expected {yaw_exp}, got {y_est}"
        assert abs(r_est - roll_exp) < 1.5, f"Roll mismatch: expected {roll_exp}, got {r_est}"


def test_vocal_extractor_speech_pace_relative():
    """Verify that VocalExtractor correctly extracts relative speech pace from syllable energy bursts."""
    extractor = VocalExtractor()
    sr = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 6 syllable bursts spaced every 0.3s (3.0 syllables/sec)
    envelope = np.zeros_like(t)
    for i in range(6):
        center = 0.2 + i * 0.3
        envelope += np.exp(-((t - center) ** 2) / (2 * (0.05 ** 2)))
    carrier = np.sin(2 * np.pi * 180.0 * t)
    audio = (carrier * envelope).astype(np.float32)

    res = extractor.extract(audio)
    assert res["speech_detected"] is True
    assert "speech_pace_relative" in res
    assert 2.5 <= res["speech_pace_relative"] <= 3.5, f"Expected pace around 3.0, got {res['speech_pace_relative']}"


def test_frontal_face_pose_within_bounds():
    """Verify that a real frontal face fixture reads yaw/pitch/roll within +/- 15 degrees."""
    import cv2
    import os
    img_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        ".venv", "Lib", "site-packages", "matplotlib", "mpl-data", "sample_data", "grace_hopper.jpg"
    )
    if not os.path.exists(img_path):
        import pytest
        pytest.skip("grace_hopper.jpg fixture not found")
    img = cv2.imread(img_path)
    extractor = FacialExtractor()
    res = extractor.extract(img)
    assert res["face_detected"] is True
    assert abs(res["head_pitch"]) <= 15.0, f"Frontal pitch exceeded 15 deg: {res['head_pitch']}"
    assert abs(res["head_yaw"]) <= 15.0, f"Frontal yaw exceeded 15 deg: {res['head_yaw']}"
    assert abs(res["head_roll"]) <= 15.0, f"Frontal roll exceeded 15 deg: {res['head_roll']}"

