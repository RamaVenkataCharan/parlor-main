"""Phase 5 Automated Tests: Live Affective Wellness Integration.

Covers:
1. Live cycle producing an intervention over WebSocket with schema verification.
2. Graceful degradation when llama-server is unreachable / offline.
3. Insufficient signal honesty (obscured camera / silent mic produces no false positives).
4. Interactive sensitivity mode switching (Conservative, Balanced, Sensitive) and mute toggling.
5. Local SQLite persistence logging of assessments and triggered interventions.
"""

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock

from parlor.wellness import WellnessService
from parlor import db, triggers, interventions


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def test_insufficient_signal_honesty(tmp_path):
    """Verify system remains silent and honest when neither face nor audio is detected."""
    async def _test():
        test_db = str(tmp_path / "test_wellness.db")
        db.init_db(test_db)

        service = WellnessService(cycle_interval_sec=1.0)
        service.fusion_engine.clear()

        # Step cycle with empty buffers
        with patch("parlor.db.DEFAULT_DB_PATH", test_db):
            res = await service.step_cycle()
            assert res is None  # No intervention fired

            records = db.get_recent_history(limit=5, db_path=test_db)
            assert len(records) >= 1
            latest = records[0]
            assert latest["stress_level"] == "insufficient signal"
            assert latest["numeric_score"] == -1.0
            assert latest["confidence"] == 0.0
            assert "no_signals" in str(latest["metadata"])

    _run_async(_test())


def test_graceful_degradation_when_slm_offline(tmp_path):
    """Verify that if local llama-server is offline, the wellness loop recovers gracefully without crashing."""
    async def _test():
        test_db = str(tmp_path / "test_wellness.db")
        service = WellnessService(cycle_interval_sec=1.0)

        # Feed a face and voice frame
        service.fusion_engine.facial_history.append({"face_detected": True, "confidence": 0.95, "au04_brow_furrow": 0.85})
        service.fusion_engine.vocal_history.append({"speech_detected": True, "rms_energy": 0.08, "f0_mean_hz": 185.0})

        # Simulate llama-server crash / unreachability
        with patch("parlor.llama.is_healthy", return_value=False):
            res = await service.step_cycle()
            assert res is None
            assert service._consecutive_slm_errors == 1  # Incremented error count

            # Cycle again
            res2 = await service.step_cycle()
            assert res2 is None
            assert service._consecutive_slm_errors == 2  # Still alive, did not crash

    _run_async(_test())


def test_consecutive_stress_triggers_intervention(tmp_path):
    """Verify 3 consecutive high-stress cycles trigger an intervention matching app.js schema."""
    async def _test():
        test_db = str(tmp_path / "test_wellness.db")
        db.init_db(test_db)
        dispatched = []

        async def mock_dispatch(pkg):
            dispatched.append(pkg)

        service = WellnessService(cycle_interval_sec=1.0, on_intervention=mock_dispatch)
        service.trigger_manager.set_sensitivity("balanced")  # N=3 required

        # High stress SLM output
        mock_slm_output = {
            "stress_level": "High (Tier 2)",
            "primary_drivers": ["AU04 Brow Furrow=0.88", "Pitch Delta=+45Hz", "Jitter=4.2%"],
            "explainable_reasoning": "Sustained high facial strain and severe acoustic frequency perturbation.",
            "confidence_score": 0.95,
            "ambiguity_note": None
        }

        with patch.object(service, "_call_slm_reasoning", return_value=mock_slm_output), \
             patch("parlor.db.DEFAULT_DB_PATH", test_db):

            # Cycle 1: Feed data
            service.fusion_engine.facial_history.append({"face_detected": True, "au04_brow_furrow": 0.88})
            service.fusion_engine.vocal_history.append({"speech_detected": True, "rms_energy": 0.08})
            res1 = await service.step_cycle()
            assert res1 is None
            assert len(dispatched) == 0

            # Cycle 2: Feed data
            service.fusion_engine.facial_history.append({"face_detected": True, "au04_brow_furrow": 0.88})
            service.fusion_engine.vocal_history.append({"speech_detected": True, "rms_energy": 0.08})
            res2 = await service.step_cycle()
            assert res2 is None
            assert len(dispatched) == 0

            # Cycle 3: 3rd consecutive high stress -> MUST FIRE
            service.fusion_engine.facial_history.append({"face_detected": True, "au04_brow_furrow": 0.88})
            service.fusion_engine.vocal_history.append({"speech_detected": True, "rms_energy": 0.08})
            res3 = await service.step_cycle()

            assert res3 is not None
            assert len(dispatched) == 1
            pkg = dispatched[0]

            # Verify exact schema expected by app.js showInterventionCard
            assert "icon" in pkg
            assert "title" in pkg
            assert "category" in pkg
            assert "personalized_note" in pkg
            assert "steps" in pkg and isinstance(pkg["steps"], list) and len(pkg["steps"]) > 0
            assert "slm_reasoning" in pkg
            assert "stress_level" in pkg
            assert "action_label" in pkg
            assert "AU04 Brow Furrow=0.88" in pkg["personalized_note"]

            # Verify local SQLite logging
            records = db.get_recent_history(limit=5, db_path=test_db)
            assert len(records) >= 3
            latest_record = records[0]
            assert latest_record["intervention_fired"] == 1
            assert latest_record["numeric_score"] == 2.0

    _run_async(_test())


def test_sensitivity_modes_and_mute():
    """Verify live sensitivity adjustments and alert muting."""
    service = WellnessService()

    # Default balanced
    assert service.trigger_manager.consecutive_required == 3
    assert service.trigger_manager.cooldown_sec == 300.0

    # Switch to conservative
    service.set_sensitivity("conservative")
    assert service.trigger_manager.consecutive_required == 4
    assert service.trigger_manager.cooldown_sec == 450.0

    # Switch to sensitive
    service.set_sensitivity("sensitive")
    assert service.trigger_manager.consecutive_required == 2
    assert service.trigger_manager.cooldown_sec == 180.0

    # Mute
    assert service.trigger_manager.enabled is True
    service.set_muted(True)
    assert service.trigger_manager.enabled is False

    # When muted, high stress evaluates to should_fire=False
    high_slm = {"stress_level": "High (Tier 2)"}
    fire, cat, meta = service.trigger_manager.evaluate(high_slm)
    assert fire is False
    assert meta["reason"] == "system_muted"

    # Unmute
    service.set_muted(False)
    assert service.trigger_manager.enabled is True


def test_snooze_functionality():
    """Verify snooze moves the cooldown window into the future."""
    service = WellnessService()
    service.set_sensitivity("balanced")  # 300s cooldown
    service.snooze(10.0)  # 10 minutes snooze

    high_slm = {"stress_level": "High (Tier 2)"}
    fire, cat, meta = service.trigger_manager.evaluate(high_slm)
    assert fire is False
    assert "cooldown_active" in meta["reason"]
    assert meta["cooldown_remaining_sec"] > 500.0


def test_server_websocket_wellness_controls():
    """Verify live WebSocket messages for sensitivity, mute, and snooze are handled cleanly."""
    from starlette.testclient import TestClient
    from parlor.server import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        # 1. Send set_wellness_sensitivity
        ws.send_json({"type": "set_wellness_sensitivity", "sensitivity": "sensitive"})
        resp = ws.receive_json()
        assert resp["type"] == "wellness_sensitivity_changed"
        assert resp["sensitivity"] == "sensitive"

        # 2. Send set_wellness_mute
        ws.send_json({"type": "set_wellness_mute", "muted": True})
        resp2 = ws.receive_json()
        assert resp2["type"] == "wellness_mute_changed"
        assert resp2["muted"] is True

        # 3. Send snooze_wellness
        ws.send_json({"type": "snooze_wellness", "minutes": 15})
        resp3 = ws.receive_json()
        assert resp3["type"] == "wellness_snoozed"
        assert resp3["minutes"] == 15.0

        # 4. Send wellness_telemetry
        ws.send_json({"type": "wellness_telemetry", "image": None, "audio": None})

