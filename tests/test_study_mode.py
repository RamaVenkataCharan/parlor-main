"""Unit tests for Parlor Study Mode & Human Calibration/EMA Protocol Runner.

Validates:
- 18+ adult confirmation gating
- Explicit informed consent gating
- Participant registration and auto-generated anonymous codes
- Strict group separation (participant cannot participate in both calibration and validation)
- Reused code warnings
- Strict zero-media sanitizer (strips image, frame, pcm_bytes, landmarks)
- Append-only window and EMA logging with composite scoring (3-5: T0, 6-10: T1, 11-15: T2)
- Participant withdrawal data erasure
- Anonymized CSV export
- REST API endpoints in server.py
"""

import json
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from parlor.study import StudyStorage, StudyValidationError
from parlor.server import app


@pytest.fixture
def temp_storage(tmp_path: Path):
    """Fixture providing an isolated StudyStorage instance backed by tmp_path."""
    return StudyStorage(data_dir=tmp_path / "study_data")


def test_consent_and_adult_gating(temp_storage: StudyStorage):
    """Protocol mandates 18+ age verification and informed consent."""
    # Underage participant rejected
    with pytest.raises(StudyValidationError, match="18 years of age or older"):
        temp_storage.register_participant(
            participant_code="P01",
            group="calibration",
            is_adult=False,
            consent_given=True,
        )

    # Missing consent rejected
    with pytest.raises(StudyValidationError, match="informed consent"):
        temp_storage.register_participant(
            participant_code="P01",
            group="calibration",
            is_adult=True,
            consent_given=False,
        )

    # Empty code rejected
    with pytest.raises(StudyValidationError, match="cannot be empty"):
        temp_storage.register_participant(
            participant_code="   ",
            group="calibration",
            is_adult=True,
            consent_given=True,
        )

    # Invalid group rejected
    with pytest.raises(StudyValidationError, match="Invalid study group"):
        temp_storage.register_participant(
            participant_code="P01",
            group="invalid_group",
            is_adult=True,
            consent_given=True,
        )


def test_group_separation_and_code_reuse(temp_storage: StudyStorage):
    """One participant cannot participate in both calibration and validation groups."""
    # Register in calibration
    success, warn = temp_storage.register_participant(
        participant_code="P01",
        group="calibration",
        role="external",
        is_adult=True,
        consent_given=True,
    )
    assert success is True
    assert warn == ""

    # Attempting to register same code in validation MUST fail
    with pytest.raises(StudyValidationError, match="already registered in 'calibration' group"):
        temp_storage.register_participant(
            participant_code="P01",
            group="validation",
            role="external",
            is_adult=True,
            consent_given=True,
        )

    # Registering same code in same group returns reuse notice
    success2, warn2 = temp_storage.register_participant(
        participant_code="P01",
        group="calibration",
        role="external",
        is_adult=True,
        consent_given=True,
    )
    assert success2 is True
    assert "Reused code" in warn2


def test_auto_generated_participant_codes(temp_storage: StudyStorage):
    """Auto-generates sequential anonymous codes (P01, P02, etc.)."""
    assert temp_storage.get_next_participant_code() == "P01"

    temp_storage.register_participant(
        participant_code="P01", group="calibration", is_adult=True, consent_given=True
    )
    assert temp_storage.get_next_participant_code() == "P02"

    temp_storage.register_participant(
        participant_code="P02", group="validation", is_adult=True, consent_given=True
    )
    assert temp_storage.get_next_participant_code() == "P03"


def test_strict_zero_media_sanitizer():
    """Guarantees that no raw video frames, audio samples, or landmark meshes are stored."""
    dirty_payload = {
        "participant_code": "P01",
        "image": "data:image/jpeg;base64,xxxxxx",
        "frame": b"\xff\xd8\xff...",
        "frame_b64": "base64bytes...",
        "audio": "base64audio...",
        "pcm_bytes": [0.1, 0.2, 0.3],
        "landmarks": [[0.5, 0.5, 0.0], [0.6, 0.6, 0.1]],
        "mesh_points": [[10, 20], [30, 40]],
        "au04": 0.42,
        "pose_pitch": -4.2,
        "nested": {
            "raw_image": "image_data",
            "shimmer_pct": 1.25,
            "raw_landmarks": [1, 2, 3],
        },
    }

    clean = StudyStorage.sanitize_window_data(dirty_payload)

    # Forbidden media keys must be stripped
    forbidden = ["image", "frame", "frame_b64", "audio", "pcm_bytes", "landmarks", "mesh_points"]
    for k in forbidden:
        assert k not in clean, f"Key '{k}' was not stripped!"

    assert "raw_image" not in clean["nested"]
    assert "raw_landmarks" not in clean["nested"]

    # Scalar numeric metrics must be preserved
    assert clean["au04"] == 0.42
    assert clean["pose_pitch"] == -4.2
    assert clean["nested"]["shimmer_pct"] == 1.25


def test_window_and_ema_logging_with_tier_mapping(temp_storage: StudyStorage):
    """Tests append-only logging, composite score calculation, and 3-tier mapping."""
    # 1. Log observation window
    win_id = temp_storage.log_observation_window({
        "participant_code": "P01",
        "group": "validation",
        "role": "external",
        "step": "rest",
        "au04": 0.15,
        "pitch_delta_hz": 2.5,
        "model_tier": 0,
    })
    assert win_id.startswith("win_")
    assert temp_storage.windows_file.exists()

    # 2. Log EMA Tier 0 (composite 3-5)
    r1_id = temp_storage.log_ema_response({
        "participant_code": "P01",
        "step": "rest",
        "q1_emotional_tension": 1,
        "q2_perceived_demand": 1,
        "q3_somatic_symptoms": 1,
    })
    assert r1_id.startswith("ema_")

    # 3. Log EMA Tier 1 (composite 6-10)
    r2_id = temp_storage.log_ema_response({
        "participant_code": "P01",
        "step": "speech",
        "q1_emotional_tension": 3,
        "q2_perceived_demand": 3,
        "q3_somatic_symptoms": 2,
    })

    # 4. Log EMA Tier 2 (composite 11-15)
    r3_id = temp_storage.log_ema_response({
        "participant_code": "P01",
        "step": "stressor",
        "q1_emotional_tension": 4,
        "q2_perceived_demand": 5,
        "q3_somatic_symptoms": 4,
    })

    # Read records from file
    with open(temp_storage.ema_file, "r", encoding="utf-8") as f:
        ema_records = [json.loads(line) for line in f if line.strip()]

    assert len(ema_records) == 3
    assert ema_records[0]["composite_score"] == 3
    assert ema_records[0]["mapped_tier"] == 0

    assert ema_records[1]["composite_score"] == 8
    assert ema_records[1]["mapped_tier"] == 1

    assert ema_records[2]["composite_score"] == 13
    assert ema_records[2]["mapped_tier"] == 2


def test_participant_withdrawal_erasure(temp_storage: StudyStorage):
    """Withdrawing a participant permanently purges all windows, EMA ratings, and registry."""
    temp_storage.register_participant("P01", "calibration", is_adult=True, consent_given=True)
    temp_storage.register_participant("P02", "validation", is_adult=True, consent_given=True)

    temp_storage.log_observation_window({"participant_code": "P01", "step": "rest", "au04": 0.1})
    temp_storage.log_observation_window({"participant_code": "P01", "step": "speech", "au04": 0.2})
    temp_storage.log_observation_window({"participant_code": "P02", "step": "rest", "au04": 0.1})

    temp_storage.log_ema_response({"participant_code": "P01", "step": "rest", "q1_emotional_tension": 1})
    temp_storage.log_ema_response({"participant_code": "P02", "step": "rest", "q1_emotional_tension": 1})

    temp_storage.log_session_summary({"participant_code": "P01", "duration_sec": 720})

    # Execute withdrawal
    counts = temp_storage.withdraw_participant("P01")
    assert counts["windows"] == 2
    assert counts["ema"] == 1
    assert counts["sessions"] == 1
    assert counts["registry"] == 1

    # Verify P01 is gone from registry
    reg = temp_storage.load_participants()
    assert "P01" not in reg
    assert "P02" in reg

    # Verify windows only contain P02
    with open(temp_storage.windows_file, "r", encoding="utf-8") as f:
        remaining_wins = [json.loads(line) for line in f if line.strip()]
    assert len(remaining_wins) == 1
    assert remaining_wins[0]["participant_code"] == "P02"


def test_anonymized_csv_export(temp_storage: StudyStorage):
    """Anonymized CSV exports paired windows and EMA ratings without raw media."""
    temp_storage.log_observation_window({
        "window_id": "win_101",
        "timestamp": 1700000000.0,
        "participant_code": "P01",
        "group": "validation",
        "role": "external",
        "step": "rest",
        "au04": 0.12,
        "model_tier": 0,
    })
    temp_storage.log_ema_response({
        "participant_code": "P01",
        "step": "rest",
        "q1_emotional_tension": 2,
        "q2_perceived_demand": 1,
        "q3_somatic_symptoms": 1,
    })

    csv_out = temp_storage.export_anonymized_csv()
    lines = csv_out.strip().splitlines()
    assert len(lines) == 2  # header + 1 record
    header = lines[0]
    assert "window_id" in header
    assert "participant_code" in header
    assert "au04" in header
    assert "paired_ema_tier" in header
    assert "image" not in header
    assert "audio" not in header

    row = lines[1]
    assert "win_101" in row
    assert "P01" in row
    assert "validation" in row


def test_server_rest_api(monkeypatch, tmp_path: Path):
    """Tests the FastAPI endpoints in server.py."""
    isolated_storage = StudyStorage(data_dir=tmp_path / "study_api_test")
    monkeypatch.setattr("parlor.server.study_storage", isolated_storage)

    client = TestClient(app)

    # 1. GET /api/study/participants
    r = client.get("/api/study/participants")
    assert r.status_code == 200
    data = r.json()
    assert data["next_code"] == "P01"
    assert data["participants"] == {}

    # 2. POST /api/study/register validation failure
    r_fail = client.post("/api/study/register", json={
        "participant_code": "P01",
        "group": "calibration",
        "is_adult": False,
        "consent_given": True,
    })
    assert r_fail.status_code == 400
    assert "18 years" in r_fail.json()["detail"]

    # 3. POST /api/study/register success
    r_reg = client.post("/api/study/register", json={
        "participant_code": "P01",
        "group": "calibration",
        "role": "external",
        "is_adult": True,
        "consent_given": True,
    })
    assert r_reg.status_code == 200
    assert r_reg.json()["participant_code"] == "P01"

    # 4. POST /api/study/window
    r_win = client.post("/api/study/window", json={
        "participant_code": "P01",
        "group": "calibration",
        "step": "rest",
        "au04": 0.22,
    })
    assert r_win.status_code == 200
    assert "window_id" in r_win.json()

    # 5. POST /api/study/ema
    r_ema = client.post("/api/study/ema", json={
        "participant_code": "P01",
        "group": "calibration",
        "step": "rest",
        "q1_emotional_tension": 1,
        "q2_perceived_demand": 2,
        "q3_somatic_symptoms": 1,
    })
    assert r_ema.status_code == 200
    assert "response_id" in r_ema.json()

    # 6. GET /api/study/export/csv
    r_csv = client.get("/api/study/export/csv")
    assert r_csv.status_code == 200
    assert "window_id" in r_csv.text

    # 7. POST /api/study/withdraw
    r_with = client.post("/api/study/withdraw", json={"participant_code": "P01"})
    assert r_with.status_code == 200
    assert r_with.json()["deleted_counts"]["windows"] == 1

def test_participant_code_whitespace_trimming(temp_storage: StudyStorage):
    """Participant codes with surrounding whitespace are trimmed and capitalized."""
    success, _ = temp_storage.register_participant("  p88  ", "calibration", is_adult=True, consent_given=True)
    assert success is True
    reg = temp_storage.load_participants()
    assert "P88" in reg
