"""Trigger Threshold and Cooldown Management Engine.

Prevents false positives by enforcing consecutive pattern requirements (N=3 cycles),
exponential moving average (EMA) stress tracking, mandatory cooldown periods (300s),
and distinct escalation tiers for Acute Stress vs Long-Term Burnout Risk.
"""

import time
from typing import Dict, Any, Tuple, Optional


class TriggerManager:
    """Evaluates SLM stress outputs and manages intervention trigger policies."""

    def __init__(self,
                 consecutive_required: int = 3,
                 cooldown_sec: float = 300.0,
                 burnout_cycles_threshold: int = 15,
                 ema_alpha: float = 0.3):
        self.consecutive_required = consecutive_required
        self.cooldown_sec = cooldown_sec
        self.burnout_cycles_threshold = burnout_cycles_threshold
        self.ema_alpha = ema_alpha

        # State Tracking
        self.consecutive_high_stress_count = 0
        self.total_high_stress_cycles = 0
        self.ema_stress_score = 0.0
        self.last_intervention_time = 0.0
        self.enabled = True
        self.sensitivity_mode = "balanced"  # conservative, balanced, sensitive

    def set_sensitivity(self, mode: str) -> None:
        """Adjust trigger sensitivity mode."""
        mode = mode.lower()
        if mode == "conservative":
            self.consecutive_required = 4
            self.cooldown_sec = 450.0
        elif mode == "sensitive":
            self.consecutive_required = 2
            self.cooldown_sec = 180.0
        else:  # balanced
            self.consecutive_required = 3
            self.cooldown_sec = 300.0
        self.sensitivity_mode = mode

    def evaluate(self, slm_output: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Evaluate SLM reasoning output and determine whether to fire an intervention.
        
        Returns:
            Tuple[should_fire: bool, intervention_category: str, metadata: dict]
            Categories: "none", "acute_stress", "burnout_warning"
        """
        now = time.time()
        meta = {
            "consecutive_count": self.consecutive_high_stress_count,
            "ema_score": round(self.ema_stress_score, 2),
            "cooldown_remaining_sec": max(0.0, round(self.cooldown_sec - (now - self.last_intervention_time), 1)),
            "reason": "normal_operation"
        }

        if not self.enabled:
            meta["reason"] = "system_muted"
            return False, "none", meta

        # Map stress tier to numeric score (0=Low, 1=Moderate, 2=High)
        stress_level_str = slm_output.get("stress_level", "Low (Tier 0)").lower()
        if "tier 2" in stress_level_str or "high" in stress_level_str:
            numeric_score = 2.0
        elif "tier 1" in stress_level_str or "moderate" in stress_level_str:
            numeric_score = 1.0
        else:
            numeric_score = 0.0

        # Update Exponential Moving Average (EMA)
        self.ema_stress_score = (self.ema_alpha * numeric_score) + ((1.0 - self.ema_alpha) * self.ema_stress_score)

        # Pattern Tracking: Increment if Tier 1 or Tier 2
        if numeric_score >= 1.0:
            self.consecutive_high_stress_count += 1
            if numeric_score >= 2.0:
                self.total_high_stress_cycles += 1
        else:
            # Reset consecutive count on low stress / baseline cycle
            self.consecutive_high_stress_count = 0

        meta["consecutive_count"] = self.consecutive_high_stress_count
        meta["ema_score"] = round(self.ema_stress_score, 2)

        # Check Cooldown Period
        time_since_last = now - self.last_intervention_time
        if self.last_intervention_time > 0 and time_since_last < self.cooldown_sec:
            meta["reason"] = f"cooldown_active ({int(self.cooldown_sec - time_since_last)}s left)"
            return False, "none", meta

        # Check Burnout Threshold (Long-term sustained stress)
        if self.total_high_stress_cycles >= self.burnout_cycles_threshold:
            self.last_intervention_time = now
            self.consecutive_high_stress_count = 0
            self.total_high_stress_cycles = 0  # Reset counter after firing
            meta["reason"] = "sustained_burnout_pattern_detected"
            return True, "burnout_warning", meta

        # Check Acute Stress Threshold (Consecutive N cycles or EMA >= 1.4)
        if self.consecutive_high_stress_count >= self.consecutive_required or self.ema_stress_score >= 1.4:
            self.last_intervention_time = now
            self.consecutive_high_stress_count = 0  # Reset consecutive count after firing
            meta["reason"] = f"pattern_matched ({self.consecutive_required}_consecutive_cycles)"
            return True, "acute_stress", meta

        meta["reason"] = "below_threshold"
        return False, "none", meta
