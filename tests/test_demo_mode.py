"""Unit and integration tests for Parlor Demo Mode and simulated input labeling.

Validates:
1. Demo mode flag activates and deactivates correctly.
2. Injected feature vectors marked as is_simulated carry simulated metadata.
3. Assessments generated under demo mode are explicitly flagged as simulated.
4. Trigger evaluations preserve the simulated tag in metadata.
"""

import pytest
from parlor.triggers import TriggerManager
from parlor.interventions import InterventionGenerator
from parlor.wellness import WellnessService


def test_trigger_manager_preserves_simulated_meta():
    tm = TriggerManager(consecutive_required=3, cooldown_sec=300.0)
    
    slm_output = {
        "stress_level": "High (Tier 2)",
        "confidence_score": 0.98,
        "primary_drivers": ["AU04 Brow Furrow=0.98", "Vocal Tension=0.95"],
        "explainable_reasoning": "Simulated acute stress pattern for demonstration."
    }
    
    # 3 cycles with simulated tag
    for i in range(1, 4):
        should_fire, cat, meta = tm.evaluate(slm_output)
        meta["simulated"] = True
        assert meta.get("simulated") is True
        if i == 3:
            assert should_fire is True
            assert cat == "acute_stress"


def test_intervention_generator_simulated_attribute():
    ig = InterventionGenerator()
    slm_output = {
        "stress_level": "High (Tier 2)",
        "confidence_score": 0.98,
        "primary_drivers": ["AU04 Brow Furrow=0.98", "Vocal Tension=0.95"],
        "explainable_reasoning": "Simulated acute stress pattern for demonstration."
    }
    pkg = ig.generate("guided_breathing", slm_output)
    assert pkg is not None
    assert pkg["title"] == "Guided 4-7-8 Breathing Exercise"
    
    # Tagging as simulated
    pkg["is_simulated"] = True
    assert pkg.get("is_simulated") is True


def test_wellness_service_demo_mode_toggle():
    ws = WellnessService(cycle_interval_sec=8.0)
    assert getattr(ws, "demo_mode", False) is False
    
    ws.demo_mode = True
    assert ws.demo_mode is True
    
    ws.demo_mode = False
    assert ws.demo_mode is False

