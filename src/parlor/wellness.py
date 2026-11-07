"""Affective Stress & Wellness Monitoring Controller.

Unifies real-time facial micro-expression extraction, vocal acoustic biomarker extraction,
multimodal feature fusion, explainable SLM reasoning, anti-false-positive trigger policies,
local SQLite persistence, and WebSocket intervention dispatch into a single event loop.
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, Optional, Callable, List

import numpy as np

from parlor import db, llama
from parlor.facial import FacialExtractor
from parlor.fusion import FeatureFusionEngine, EXPLAINABLE_SYSTEM_PROMPT
from parlor.interventions import InterventionGenerator
from parlor.triggers import TriggerManager
from parlor.vocal import VocalExtractor

SHARED_FILE_PATH = os.path.join("shared_state", "latest_features.json")
TEMP_FILE_PATH = os.path.join("shared_state", "latest_features.json.tmp")


def write_features_atomically(vector: dict) -> None:
    """Atomically writes feature vector to shared_state/latest_features.json for dev/file inspection."""
    try:
        os.makedirs("shared_state", exist_ok=True)
        with open(TEMP_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(vector, f, indent=2)
        os.replace(TEMP_FILE_PATH, SHARED_FILE_PATH)
    except Exception as e:
        print(f"[WELLNESS] Failed to write shared features file: {e}")


class BaselineCalibrator:
    """In-memory personal baseline calibrator.
    
    Accumulates natural resting vocal pitch (F0) and facial baseline features
    over the first 60 seconds of active user interaction.
    """

    def __init__(self, target_duration_sec: float = 60.0, default_f0: float = 145.0):
        self.target_duration_sec = target_duration_sec
        self.default_f0 = default_f0
        self.calibrated = False
        self.accumulated_active_sec = 0.0
        self._last_sample_time: Optional[float] = None
        
        self.f0_samples: List[float] = []
        self.au04_samples: List[float] = []
        self.au07_samples: List[float] = []
        self.au15_samples: List[float] = []
        self.au20_samples: List[float] = []

    def update_vocal(self, vocal_res: Dict[str, Any]) -> None:
        if self.calibrated or not vocal_res.get("speech_detected"):
            return
        now = time.time()
        if self._last_sample_time is not None:
            delta = min(now - self._last_sample_time, 2.0)
            self.accumulated_active_sec += delta
        self._last_sample_time = now
        f0 = vocal_res.get("f0_mean_hz")
        if f0 and f0 > 50.0:
            self.f0_samples.append(float(f0))
        self._check_completion()

    def update_face(self, face_res: Dict[str, Any]) -> None:
        if self.calibrated or not face_res.get("face_detected"):
            return
        now = time.time()
        if self._last_sample_time is not None:
            delta = min(now - self._last_sample_time, 2.0)
            self.accumulated_active_sec += delta
        self._last_sample_time = now
        for au, arr in [
            ("au04_brow_furrow", self.au04_samples),
            ("au07_lid_tightener", self.au07_samples),
            ("au15_lip_depressor", self.au15_samples),
            ("au20_lip_stretcher", self.au20_samples),
        ]:
            val = face_res.get(au)
            if val is not None:
                arr.append(float(val))
        self._check_completion()

    def _check_completion(self) -> None:
        if self.accumulated_active_sec >= self.target_duration_sec:
            self.calibrated = True

    def get_baseline_f0(self) -> float:
        if self.f0_samples:
            return float(np.median(self.f0_samples))
        return self.default_f0

    def get_status(self) -> Dict[str, Any]:
        elapsed = min(self.target_duration_sec, self.accumulated_active_sec)
        if self.calibrated or elapsed >= self.target_duration_sec:
            return {
                "status": "active (calibrated)",
                "calibrated": True,
                "elapsed_sec": int(self.target_duration_sec),
                "target_sec": int(self.target_duration_sec),
                "f0_baseline_hz": round(self.get_baseline_f0(), 1),
            }
        return {
            "status": f"calibrating ({int(elapsed)}/{int(self.target_duration_sec)} s)",
            "calibrated": False,
            "elapsed_sec": int(elapsed),
            "target_sec": int(self.target_duration_sec),
            "f0_baseline_hz": round(self.get_baseline_f0(), 1),
        }


class WellnessService:
    """Orchestrates real-time wellness monitoring on the server asyncio loop."""

    def __init__(
        self,
        cycle_interval_sec: float = 8.0,
        on_intervention: Optional[Callable[[Dict[str, Any]], Any]] = None
    ):
        self.cycle_interval_sec = cycle_interval_sec
        self.on_intervention = on_intervention

        # Core Engines
        self.facial_extractor = FacialExtractor()
        self.vocal_extractor = VocalExtractor()
        self.fusion_engine = FeatureFusionEngine(window_size=5)
        self.baseline_calibrator = BaselineCalibrator(target_duration_sec=60.0)
        self.trigger_manager = TriggerManager(consecutive_required=3, cooldown_sec=300.0)
        self.intervention_generator = InterventionGenerator()

        # Signal Buffers for Live Stream
        self._latest_face_res: Optional[Dict[str, Any]] = None
        self._latest_vocal_res: Optional[Dict[str, Any]] = None
        self._audio_chunks_buffer: List[np.ndarray] = []

        # State & Resilience
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._consecutive_slm_errors = 0
        self._history: List[Dict[str, Any]] = []
        self._voice_active: bool = False
        self._last_voice_turn_time: float = 0.0
        self.concurrency_mitigation_enabled: bool = True

        # Initialize SQLite DB
        db.init_db()

    def set_sensitivity(self, mode: str) -> None:
        """Update sensitivity mode: conservative, balanced, sensitive."""
        self.trigger_manager.set_sensitivity(mode)
        print(f"[WELLNESS] Sensitivity updated to '{self.trigger_manager.sensitivity_mode}' "
              f"(N={self.trigger_manager.consecutive_required}, cooldown={self.trigger_manager.cooldown_sec}s)")

    def set_muted(self, muted: bool) -> None:
        """Enable or mute wellness interventions."""
        self.trigger_manager.enabled = not muted
        print(f"[WELLNESS] Wellness alerts {'MUTED' if muted else 'ACTIVE'}")

    def set_voice_active(self, active: bool) -> None:
        """Mark whether a conversational voice turn or user speech is in progress.
        
        When active, background wellness SLM reasoning calls are deferred to prevent
        GPU contention and avoid evicting the conversational prompt KV cache.
        """
        self._voice_active = active
        if active:
            self._last_voice_turn_time = time.time()

    def snooze(self, minutes: float = 10.0) -> None:
        """Snooze interventions for a given number of minutes."""
        now = time.time()
        self.trigger_manager.last_intervention_time = now + (minutes * 60.0 - self.trigger_manager.cooldown_sec)
        print(f"[WELLNESS] Interventions snoozed for {minutes} minutes")

    def get_baseline_status(self) -> Dict[str, Any]:
        """Return the current personal baseline calibration status."""
        return self.baseline_calibrator.get_status()

    def feed_frame(self, image_data: Any) -> None:
        """Ingest live image frame (Base64 JPEG string or numpy array) from WebSocket."""
        try:
            res = self.facial_extractor.extract(image_data)
            self._latest_face_res = res
            self.baseline_calibrator.update_face(res)
            # Push into fusion engine if vocal result exists
            self.fusion_engine.facial_history.append(res)
        except Exception as e:
            print(f"[WELLNESS] Error extracting facial features: {e}")

    def get_face_snapshot(self) -> Dict[str, Any]:
        """Return only the latest compact face-feature vector for the local UI."""
        fields = (
            "face_detected", "confidence", "au04_brow_furrow",
            "au07_lid_tightener", "au15_lip_depressor",
            "au20_lip_stretcher", "ear", "head_pitch", "head_yaw",
            "head_roll", "mesh_points", "latency_ms",
        )
        latest = self._latest_face_res or {}
        res = {key: latest.get(key) for key in fields}
        res["baseline"] = self.get_baseline_status()
        return res

    def get_vocal_snapshot(self) -> Dict[str, Any]:
        """Return only the latest compact vocal-feature vector for the local UI."""
        fields = (
            "speech_detected", "rms_energy", "f0_mean_hz",
            "f0_std_hz", "jitter_local", "shimmer_local",
            "pause_ratio", "speech_pace_relative", "vocal_tension_index", "latency_ms",
        )
        latest = self._latest_vocal_res or {}
        res = {key: latest.get(key) for key in fields}
        res["baseline"] = self.get_baseline_status()
        return res

    def feed_audio(self, audio_data: Any) -> None:
        """Ingest live audio PCM chunk from WebSocket."""
        try:
            res = self.vocal_extractor.extract(audio_data)
            self._latest_vocal_res = res
            self.baseline_calibrator.update_vocal(res)
            if self.baseline_calibrator.calibrated:
                self.fusion_engine.f0_baseline_hz = self.baseline_calibrator.get_baseline_f0()
            self.fusion_engine.vocal_history.append(res)
        except Exception as e:
            print(f"[WELLNESS] Error extracting vocal features: {e}")

    async def _call_slm_reasoning(self, prompt: str) -> Dict[str, Any]:
        """Calls local llama-server via non-blocking executor with schema enforcement."""
        loop = asyncio.get_running_loop()

        messages = [
            {"role": "system", "content": EXPLAINABLE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        def _blocking_call():
            # Check llama-server health first
            if not llama.is_healthy(timeout=1.0):
                raise RuntimeError("llama-server is currently unreachable or offline")

            raw = llama.chat_blocking(
                messages=messages,
                max_tokens=512,
                temperature=0.1
            )
            return raw

        raw_response = await loop.run_in_executor(None, _blocking_call)

        # Parse JSON response
        cleaned = raw_response.strip()
        if "{" in cleaned and "}" in cleaned:
            cleaned = cleaned[cleaned.find("{"):cleaned.rfind("}") + 1]
        elif cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        try:
            parsed = json.loads(cleaned.strip())
            return parsed
        except Exception as e:
            print(f"[WELLNESS] SLM response JSON decode error: {e}. Raw: {raw_response[:100]}")
            # Honest fallback structure
            return {
                "stress_level": "Low (Tier 0)",
                "primary_drivers": ["Unstructured response parsed as baseline"],
                "explainable_reasoning": "Could not parse structured SLM reasoning; defaulted safely to baseline.",
                "confidence_score": 0.50,
                "ambiguity_note": "JSON parsing fallback"
            }

    async def step_cycle(self) -> Optional[Dict[str, Any]]:
        """Executes a single observation & reasoning cycle."""
        # Aggregate features from rolling window
        agg = self.fusion_engine.aggregate_features()

        # Update fallback shared_state/latest_features.json for file inspection/dev tools
        combined_export = {
            "timestamp": time.time(),
            "face": {
                "face_detected": agg["face_detected"],
                "au04_brow_furrow": agg["au04_brow_furrow"],
                "au07_lid_tightener": agg["au07_lid_tightener"],
                "au15_lip_depressor": agg["au15_lip_depressor"],
                "au20_lip_stretcher": agg["au20_lip_stretcher"],
                "ear": agg["ear"],
                "confidence": agg["face_confidence"]
            },
            "audio": {
                "voice_detected": agg["speech_detected"],
                "pitch_delta": agg["f0_delta_hz"],
                "pitch_variance": agg["f0_std_hz"],
                "jitter": agg["jitter_local_pct"],
                "shimmer": agg["shimmer_local_pct"],
                "pause_ratio": agg["pause_ratio"],
                "vocal_tension": agg["vocal_tension_index"]
            }
        }
        write_features_atomically(combined_export)

        # Insufficient Signal Check: If neither face nor audio is detected, stay honest
        if not agg["face_detected"] and not agg["speech_detected"]:
            # Do not waste compute or hallucinate stress when no user signals exist
            honest_slm = {
                "stress_level": "insufficient signal",
                "primary_drivers": ["No active signals detected"],
                "explainable_reasoning": "No facial or vocal signals detected in the current observation window.",
                "confidence_score": 0.0,
                "ambiguity_note": "Camera unlit/obscured and microphone silent."
            }
            self.trigger_manager.evaluate(honest_slm)
            db.log_assessment(honest_slm, intervention_fired=False, meta={"reason": "no_signals"})
            return None

        # Voice Turn Deferral: If conversational voice turn is active or recently active (< 5s),
        # defer SLM reasoning to prevent GPU contention and avoid evicting conversational prompt KV cache.
        if self.concurrency_mitigation_enabled and (self._voice_active or (time.time() - self._last_voice_turn_time < 5.0)):
            return None

        # Format prompt
        prompt = self.fusion_engine.format_prompt(agg)

        # Reason via local SLM with backoff resilience
        try:
            slm_output = await self._call_slm_reasoning(prompt)
            self._consecutive_slm_errors = 0
        except Exception as e:
            self._consecutive_slm_errors += 1
            backoff_msg = f"backing off (consecutive failures: {self._consecutive_slm_errors})"
            print(f"[WELLNESS] Local SLM reasoning unavailable ({e}) — {backoff_msg}")
            return None

        # Evaluate against TriggerManager
        should_fire, category, meta = self.trigger_manager.evaluate(slm_output)

        intervention_pkg = None
        if should_fire:
            intervention_pkg = self.intervention_generator.generate(category, slm_output)
            print(f"[WELLNESS] *** INTERVENTION TRIGGERED *** Category: {category}, Title: {intervention_pkg['title']}")
            if self.on_intervention:
                try:
                    res = self.on_intervention(intervention_pkg)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    print(f"[WELLNESS] Error dispatching intervention: {e}")

        # Record to local SQLite store
        db.log_assessment(
            slm_output=slm_output,
            intervention_fired=should_fire,
            intervention_pkg=intervention_pkg,
            meta=meta
        )

        return intervention_pkg

    async def run_loop(self) -> None:
        """Main background loop polling observation windows."""
        print(f"[WELLNESS] Starting background monitoring loop (cycle={self.cycle_interval_sec}s)...")
        self._running = True
        try:
            while self._running:
                await asyncio.sleep(self.cycle_interval_sec)
                # Apply exponential backoff if SLM is persistently unreachable
                if self._consecutive_slm_errors >= 3:
                    await asyncio.sleep(20.0)

                await self.step_cycle()
        except asyncio.CancelledError:
            print("[WELLNESS] Background monitoring loop cancelled cleanly.")
        except Exception as e:
            print(f"[WELLNESS] Unexpected loop exception: {e}")

    def start(self) -> asyncio.Task:
        """Start the wellness monitoring background loop on the active event loop."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run_loop())
        return self._task

    def stop(self) -> None:
        """Stop the background loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
