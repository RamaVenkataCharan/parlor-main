"""Local SQLite Persistence Store for Affective Stress Assessments.

Maintains longitudinal wellness history in a local, on-device SQLite database
(shared_state/wellness_history.db) without any external dependencies or network calls.
"""

import json
import os
import sqlite3
import time
from typing import Dict, Any, List, Optional

DEFAULT_DB_PATH = os.path.join("shared_state", "wellness_history.db")


def get_db_path(custom_path: Optional[str] = None) -> str:
    path = custom_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize SQLite database table for stress assessments."""
    path = get_db_path(db_path)
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stress_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    stress_level TEXT NOT NULL,
                    numeric_score REAL NOT NULL,
                    primary_drivers TEXT,
                    reasoning TEXT,
                    confidence REAL,
                    intervention_fired INTEGER DEFAULT 0,
                    intervention_type TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"[WELLNESS DB] Initialization error: {e}")


def log_assessment(
    slm_output: Dict[str, Any],
    intervention_fired: bool = False,
    intervention_pkg: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """Logs a single stress assessment cycle to local SQLite store."""
    path = get_db_path(db_path)
    now = time.time()

    stress_level = slm_output.get("stress_level", "Low (Tier 0)")
    if "tier 2" in stress_level.lower() or "high" in stress_level.lower():
        numeric_score = 2.0
    elif "tier 1" in stress_level.lower() or "moderate" in stress_level.lower():
        numeric_score = 1.0
    else:
        numeric_score = 0.0

    drivers = slm_output.get("primary_drivers", [])
    drivers_str = json.dumps(drivers) if isinstance(drivers, (list, dict)) else str(drivers)
    reasoning = slm_output.get("explainable_reasoning", "")
    confidence = float(slm_output.get("confidence_score", 0.90))

    intervention_type = ""
    if intervention_fired and intervention_pkg:
        intervention_type = intervention_pkg.get("category", "") or intervention_pkg.get("title", "")

    meta_str = json.dumps(meta or {})

    try:
        with sqlite3.connect(path, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO stress_assessments (
                    timestamp, stress_level, numeric_score, primary_drivers,
                    reasoning, confidence, intervention_fired, intervention_type, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now, stress_level, numeric_score, drivers_str,
                reasoning, confidence, 1 if intervention_fired else 0,
                intervention_type, meta_str
            ))
            conn.commit()
    except Exception as e:
        print(f"[WELLNESS DB] Failed to log assessment: {e}")


def get_recent_history(limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves recent assessment records from local SQLite store."""
    path = get_db_path(db_path)
    if not os.path.exists(path):
        return []

    try:
        with sqlite3.connect(path, timeout=5.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, stress_level, numeric_score, primary_drivers,
                       reasoning, confidence, intervention_fired, intervention_type, metadata
                FROM stress_assessments
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["primary_drivers"] = json.loads(item["primary_drivers"])
                except Exception:
                    pass
                try:
                    item["metadata"] = json.loads(item["metadata"])
                except Exception:
                    pass
                results.append(item)
            return results
    except Exception as e:
        print(f"[WELLNESS DB] Failed to read history: {e}")
        return []
