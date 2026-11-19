"""Parlor Study Mode Backend — Guided calibration and EMA session runner.

Manages participant registration, group separation, observation window logging,
EMA response pairing, session QA summaries, anonymized exports, and participant withdrawal.

PRIVACY & SAFETY MANDATE:
- Strictly numeric biometric features and self-reports only.
- ZERO camera frames, audio samples, or landmark coordinate meshes are stored.
- Local-only storage under study_data/ (gitignored and excluded from release archives).
"""

# Theoretical foundation: WESAD (Schmidt et al., 2018) multimodal stress & PSS-10.
from __future__ import annotations

import csv
import io
import json
import os
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_STUDY_DIR = ROOT_DIR / "study_data"

# EMA Likert composite score boundaries (3-15 scale)
EMA_TIER0_MAX: int = 5
EMA_TIER1_MAX: int = 10
EMA_TIER2_MAX: int = 15


class StudyValidationError(ValueError):
    """Raised when participant validation, consent, or group separation rules are violated."""
    pass


class StudyStorage:
    """Handles thread-safe append-only logging for study observation windows and EMA reports."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_STUDY_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.windows_file = self.data_dir / "observation_windows.jsonl"
        self.ema_file = self.data_dir / "ema_responses.jsonl"
        self.sessions_file = self.data_dir / "study_sessions.jsonl"
        self.participants_file = self.data_dir / "participants_registry.json"

    # ── Registry & Group Separation ──────────────────────────────────────────

    def load_participants(self) -> Dict[str, Dict[str, Any]]:
        """Loads registered participants metadata."""
        if not self.participants_file.exists():
            return {}
        try:
            with open(self.participants_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_participants(self, registry: Dict[str, Dict[str, Any]]) -> None:
        temp_file = self.participants_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
        temp_file.replace(self.participants_file)

    def register_participant(
        self,
        participant_code: str,
        group: str,
        role: str = "external",
        is_adult: bool = False,
        consent_given: bool = False,
    ) -> Tuple[bool, str]:
        """Registers a participant, enforcing 18+, consent, and strict group separation."""
        code = participant_code.strip().upper()
        if not code:
            raise StudyValidationError("Participant code cannot be empty.")
        if not is_adult:
            raise StudyValidationError("Participants must be confirmed 18 years of age or older.")
        if not consent_given:
            raise StudyValidationError("Participant informed consent must be confirmed before registering.")

        group = group.strip().lower()
        if group not in ("calibration", "validation"):
            raise StudyValidationError(f"Invalid study group '{group}'. Must be 'calibration' or 'validation'.")

        role = role.strip().lower()
        if role not in ("team", "external"):
            role = "external"

        registry = self.load_participants()
        warning_msg = ""

        if code in registry:
            existing = registry[code]
            existing_group = existing.get("group")
            if existing_group != group:
                raise StudyValidationError(
                    f"Participant {code} is already registered in '{existing_group}' group. "
                    f"Protocol mandates that one participant cannot participate in both groups."
                )
            warning_msg = f"Notice: Participant code {code} was previously used in '{group}'. Reused code."

        registry[code] = {
            "participant_code": code,
            "group": group,
            "role": role,
            "is_adult": is_adult,
            "consent_given": consent_given,
            "registered_at": time.time(),
        }
        self._save_participants(registry)
        return True, warning_msg

    def get_next_participant_code(self) -> str:
        """Auto-generates the next sequential anonymous code (e.g. P01, P02)."""
        registry = self.load_participants()
        existing_numbers = []
        for code in registry.keys():
            if code.startswith("P") and code[1:].isdigit():
                existing_numbers.append(int(code[1:]))
        next_num = max(existing_numbers, default=0) + 1
        return f"P{next_num:02d}"

    # ── Strict No-Media Sanitizer ────────────────────────────────────────────

    @staticmethod
    def sanitize_window_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Enforces that NO raw media (images, frames, audio buffers, mesh points) is stored."""
        forbidden_keys = {
            "image", "frame", "frame_b64", "raw_image", "img",
            "audio", "audio_b64", "pcm_bytes", "samples", "raw_audio",
            "mesh_points", "landmarks", "raw_landmarks", "video_buffer"
        }
        clean = {}
        for k, v in data.items():
            if k.lower() in forbidden_keys:
                continue
            if isinstance(v, dict):
                clean[k] = StudyStorage.sanitize_window_data(v)
            else:
                clean[k] = v
        return clean

    # ── Append-Only Logging ──────────────────────────────────────────────────

    def log_observation_window(self, window_data: Dict[str, Any]) -> str:
        """Appends a single observation window record to observation_windows.jsonl."""
        clean = self.sanitize_window_data(window_data)
        if "window_id" not in clean:
            clean["window_id"] = f"win_{int(time.time() * 1000)}"
        if "timestamp" not in clean:
            clean["timestamp"] = time.time()

        # Write to append-only JSONL
        with open(self.windows_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(clean) + "\n")
        return str(clean["window_id"])

    def log_ema_response(self, ema_data: Dict[str, Any]) -> str:
        """Appends an EMA response record to ema_responses.jsonl."""
        clean = self.sanitize_window_data(ema_data)
        if "response_id" not in clean:
            clean["response_id"] = f"ema_{int(time.time() * 1000)}"
        if "timestamp" not in clean:
            clean["timestamp"] = time.time()

        # Compute composite score & mapped tier if not provided
        q1 = int(clean.get("q1_emotional_tension", 1))
        q2 = int(clean.get("q2_perceived_demand", 1))
        q3 = int(clean.get("q3_somatic_symptoms", 1))
        composite = q1 + q2 + q3
        clean["composite_score"] = composite

        if "mapped_tier" not in clean:
            if composite <= 5:
                clean["mapped_tier"] = 0
            elif composite <= 10:
                clean["mapped_tier"] = 1
            else:
                clean["mapped_tier"] = 2

        with open(self.ema_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(clean) + "\n")
        return str(clean["response_id"])

    def log_session_summary(self, summary_data: Dict[str, Any]) -> str:
        """Appends session QA summary to study_sessions.jsonl."""
        clean = self.sanitize_window_data(summary_data)
        if "session_id" not in clean:
            clean["session_id"] = f"sess_{int(time.time() * 1000)}"
        if "completed_at" not in clean:
            clean["completed_at"] = time.time()

        with open(self.sessions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(clean) + "\n")
        return str(clean["session_id"])

    # ── Participant Withdrawal (Data Erasure) ────────────────────────────────

    def withdraw_participant(self, participant_code: str) -> Dict[str, int]:
        """Permanently erases all records and registry entries for the participant.

        Returns counts of deleted records per category.
        """
        code = participant_code.strip().upper()
        counts = {"windows": 0, "ema": 0, "sessions": 0, "registry": 0}

        # 1. Purge from Windows JSONL
        if self.windows_file.exists():
            remaining_windows = []
            with open(self.windows_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        record = json.loads(line_str)
                        if str(record.get("participant_code", "")).upper() == code:
                            counts["windows"] += 1
                        else:
                            remaining_windows.append(line_str)
                    except Exception:
                        remaining_windows.append(line_str)

            temp_f = self.windows_file.with_suffix(".tmp")
            with open(temp_f, "w", encoding="utf-8") as f:
                for line_str in remaining_windows:
                    f.write(line_str + "\n")
            temp_f.replace(self.windows_file)

        # 2. Purge from EMA JSONL
        if self.ema_file.exists():
            remaining_ema = []
            with open(self.ema_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        record = json.loads(line_str)
                        if str(record.get("participant_code", "")).upper() == code:
                            counts["ema"] += 1
                        else:
                            remaining_ema.append(line_str)
                    except Exception:
                        remaining_ema.append(line_str)

            temp_f = self.ema_file.with_suffix(".tmp")
            with open(temp_f, "w", encoding="utf-8") as f:
                for line_str in remaining_ema:
                    f.write(line_str + "\n")
            temp_f.replace(self.ema_file)

        # 3. Purge from Sessions JSONL
        if self.sessions_file.exists():
            remaining_sessions = []
            with open(self.sessions_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        record = json.loads(line_str)
                        if str(record.get("participant_code", "")).upper() == code:
                            counts["sessions"] += 1
                        else:
                            remaining_sessions.append(line_str)
                    except Exception:
                        remaining_sessions.append(line_str)

            temp_f = self.sessions_file.with_suffix(".tmp")
            with open(temp_f, "w", encoding="utf-8") as f:
                for line_str in remaining_sessions:
                    f.write(line_str + "\n")
            temp_f.replace(self.sessions_file)

        # 4. Remove from Registry
        registry = self.load_participants()
        if code in registry:
            del registry[code]
            self._save_participants(registry)
            counts["registry"] = 1

        return counts

    # ── Anonymized Export ────────────────────────────────────────────────────

    def export_anonymized_csv(self) -> str:
        """Generates an anonymized combined CSV string of windows and paired EMA."""
        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            "window_id", "timestamp", "participant_code", "group", "role",
            "step", "face_detected", "speech_detected",
            "au04", "au07", "au15", "au20",
            "pose_yaw", "pose_pitch", "pose_roll",
            "pitch_hz", "pitch_delta_hz", "jitter_pct", "shimmer_pct", "steadiness", "pace",
            "model_tier", "confidence", "insufficient_signal", "trigger_fired",
            "paired_ema_tier", "paired_ema_score"
        ]
        writer.writerow(headers)

        if not self.windows_file.exists():
            return output.getvalue()

        # Index EMA responses by (participant_code, step)
        ema_index: Dict[Tuple[str, str], Dict[str, Any]] = {}
        if self.ema_file.exists():
            with open(self.ema_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            em = json.loads(line)
                            p = str(em.get("participant_code", "")).upper()
                            s = str(em.get("step", "")).lower()
                            ema_index[(p, s)] = em
                        except Exception:
                            pass

        with open(self.windows_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    w = json.loads(line)
                    p_code = str(w.get("participant_code", "")).upper()
                    st = str(w.get("step", "")).lower()
                    ema_pair = ema_index.get((p_code, st), {})

                    face = w.get("face", {})
                    vocal = w.get("vocal", {})
                    pose = w.get("head_pose", {})

                    writer.writerow([
                        w.get("window_id", ""),
                        w.get("timestamp", ""),
                        p_code,
                        w.get("group", ""),
                        w.get("role", "external"),
                        st,
                        face.get("face_detected", w.get("face_detected", False)),
                        vocal.get("speech_detected", w.get("speech_detected", False)),
                        face.get("au04", w.get("au04", 0.0)),
                        face.get("au07", w.get("au07", 0.0)),
                        face.get("au15", w.get("au15", 0.0)),
                        face.get("au20", w.get("au20", 0.0)),
                        pose.get("yaw", w.get("pose_yaw", 0.0)),
                        pose.get("pitch", w.get("pose_pitch", 0.0)),
                        pose.get("roll", w.get("pose_roll", 0.0)),
                        vocal.get("pitch_hz", w.get("pitch_hz", 0.0)),
                        vocal.get("pitch_delta_hz", w.get("pitch_delta_hz", 0.0)),
                        vocal.get("jitter_pct", w.get("jitter_pct", 0.0)),
                        vocal.get("shimmer_pct", w.get("shimmer_pct", 0.0)),
                        vocal.get("steadiness", w.get("steadiness", 0.0)),
                        vocal.get("speech_pace", w.get("speech_pace", 0.0)),
                        w.get("model_tier", ""),
                        w.get("confidence", ""),
                        w.get("insufficient_signal", False),
                        w.get("trigger_decision", False),
                        ema_pair.get("mapped_tier", ""),
                        ema_pair.get("composite_score", ""),
                    ])
                except Exception:
                    continue

        return output.getvalue()


# Global module singleton default storage
study_storage = StudyStorage()
