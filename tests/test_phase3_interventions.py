"""Unit tests for Phase 3 Intervention Trigger Manager and Micro-Intervention Generator."""

import time
import pytest
from parlor.triggers import TriggerManager
from parlor.interventions import InterventionGenerator


def test_trigger_manager_consecutive_cycle_requirement():
    mgr = TriggerManager(consecutive_required=3, cooldown_sec=300.0)

    low_slm = {"stress_level": "Low (Tier 0)"}
    high_slm = {"stress_level": "High (Tier 2)", "explainable_reasoning": "High brow tension and pitch elevation."}

    # Single high stress cycle -> Should NOT fire
    fire, cat, meta = mgr.evaluate(high_slm)
    assert fire is False
    assert meta["consecutive_count"] == 1

    # Single low stress cycle -> Resets consecutive counter
    fire, cat, meta = mgr.evaluate(low_slm)
    assert fire is False
    assert meta["consecutive_count"] == 0

    # 2 consecutive high stress cycles -> Should NOT fire yet
    mgr.evaluate(high_slm)
    fire, cat, meta = mgr.evaluate(high_slm)
    assert fire is False
    assert meta["consecutive_count"] == 2

    # 3rd consecutive high stress cycle -> SHOULD FIRE
    fire, cat, meta = mgr.evaluate(high_slm)
    assert fire is True
    assert cat == "acute_stress"

    # Immediately subsequent cycle -> Blocked by 300s cooldown
    fire, cat, meta = mgr.evaluate(high_slm)
    assert fire is False
    assert "cooldown_active" in meta["reason"]


def test_trigger_manager_sensitivity_modes():
    mgr = TriggerManager()
    
    mgr.set_sensitivity("conservative")
    assert mgr.consecutive_required == 4
    assert mgr.cooldown_sec == 450.0

    mgr.set_sensitivity("sensitive")
    assert mgr.consecutive_required == 2
    assert mgr.cooldown_sec == 180.0


def test_intervention_generator_personalized_output():
    gen = InterventionGenerator()
    slm_data = {
        "stress_level": "High (Tier 2)",
        "primary_drivers": ["AU04 Brow Furrow=0.84", "Pitch Delta=+43.4Hz"],
        "explainable_reasoning": "Severe facial and vocal tension detected across observation windows."
    }

    pkg = gen.generate("guided_breathing", slm_data)
    assert pkg["title"] == "Guided 4-7-8 Breathing Exercise"
    assert "AU04 Brow Furrow=0.84" in pkg["personalized_note"]
    assert "Severe facial and vocal tension" in pkg["slm_reasoning"]
    assert len(pkg["steps"]) == 4


def test_trigger_manager_insufficient_signal_hold_policy():
    mgr = TriggerManager(consecutive_required=3, cooldown_sec=300.0)

    high_slm = {"stress_level": "High (Tier 2)", "explainable_reasoning": "Elevated AU04 and pitch."}
    insufficient_slm = {"stress_level": "Insufficient Signal", "explainable_reasoning": "No face detected in video stream."}
    low_slm = {"stress_level": "Low (Tier 0)", "explainable_reasoning": "Relaxed facial baseline."}

    # Cycle 1: High stress -> consecutive count becomes 1
    fire, cat, meta = mgr.evaluate(high_slm)
    assert fire is False
    assert meta["consecutive_count"] == 1

    # Cycle 2: Insufficient signal (-1.0) -> HOLD: count stays 1, must NOT fire
    fire, cat, meta = mgr.evaluate(insufficient_slm)
    assert fire is False
    assert meta["consecutive_count"] == 1
    assert meta["reason"] == "insufficient_signal_held"

    # Cycle 3: High stress -> consecutive count becomes 2
    fire, cat, meta = mgr.evaluate(high_slm)
    assert fire is False
    assert meta["consecutive_count"] == 2

    # Cycle 4: Insufficient signal (-1.0) -> HOLD: count stays 2, must NOT fire
    fire, cat, meta = mgr.evaluate(insufficient_slm)
    assert fire is False
    assert meta["consecutive_count"] == 2
    assert meta["reason"] == "insufficient_signal_held"

    # Cycle 5: High stress -> consecutive count becomes 3 -> SHOULD FIRE
    fire, cat, meta = mgr.evaluate(high_slm)
    assert fire is True
    assert cat == "acute_stress"

    # Cycle 6: Reset on genuine Tier 0
    mgr.last_intervention_time = 0.0  # clear cooldown for test
    mgr.consecutive_high_stress_count = 2
    fire, cat, meta = mgr.evaluate(low_slm)
    assert fire is False
    assert meta["consecutive_count"] == 0

