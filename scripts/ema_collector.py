"""EMA Collector: Interactive Ecological Momentary Assessment tool for human participants.

This tool administers the 3-item EMA questionnaire at the end of each observation window,
captures participant ratings, reads the nearest wellness assessment from SQLite
(shared_state/wellness_history.db), and saves paired Ground-Truth vs System records.

Protocol Items (1-5 Likert Scale):
Q1: "How tense, anxious, or stressed did you feel during the last capture window?" (1: Calm -> 5: Extremely Tense)
Q2: "How overwhelmed did you feel by your current activity?" (1: In Control -> 5: Overwhelmed)
Q3: "Did you notice any physical tension (brow furrowing, jaw clenching, rapid breathing)?" (1: None -> 5: Severe)

Composite Score (3-15):
- 3 - 5: Tier 0 (Low Stress / Baseline)
- 6 - 10: Tier 1 (Moderate Stress / Elevated Tension)
- 11 - 15: Tier 2 (High Stress / Burnout Risk)
"""

import argparse
import datetime
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "shared_state" / "wellness_history.db"
EMA_DATA_PATH = ROOT / "shared_state" / "ema_records.json"


def ema_composite_to_tier(score: int) -> int:
    if score <= 5:
        return 0
    elif score <= 10:
        return 1
    else:
        return 2


def get_nearest_system_assessment(target_timestamp: float) -> dict | None:
    if not DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, tier, confidence, trigger_fired, trigger_type, user_state
            FROM assessments
            ORDER BY ABS(timestamp - ?) ASC
            LIMIT 1
        """, (target_timestamp,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0],
            "timestamp": row[1],
            "time_diff_s": round(abs(row[1] - target_timestamp), 2),
            "tier": row[2],
            "confidence": row[3],
            "trigger_fired": bool(row[4]),
            "trigger_type": row[5],
            "user_state": row[6],
        }
    except Exception as e:
        print(f"Error querying database: {e}")
        return None


def run_interactive_collector():
    print("=" * 60)
    print("PARLOR EMA (Ecological Momentary Assessment) Collector")
    print("=" * 60)
    print("NOTE: This tool collects ground-truth data from HUMAN participants.")
    print("Ensure Parlor (python -m parlor.server) is running and the participant")
    print("is sitting in front of the webcam/mic.")
    print("-" * 60)

    # Consent validation
    consent_input = input("Has the participant signed informed consent for research data collection? [y/N]: ").strip().lower()
    if consent_input not in ("y", "yes"):
        print("[ABORTED] Informed consent is required. Cannot record data without participant consent.")
        return

    participant_id = input("Enter Participant ID (e.g. P01, P02): ").strip()
    if not participant_id:
        print("[ABORTED] Participant ID is mandatory for audit trail.")
        return

    is_dev_input = input("Is the participant a project developer / team member? [y/N]: ").strip().lower()
    is_developer = is_dev_input in ("y", "yes")

    print("\nSelect Experimental Condition:")
    print("1) Quiet Focused Work (Baseline)")
    print("2) Active Speaking / Conversation")
    print("3) Acute Timed Stressor (Speed arithmetic / Stroop task)")
    print("4) Single-Modality / Low Light Fallback")
    cond_choice = input("Choice [1-4]: ").strip()
    cond_map = {
        "1": "Quiet Focused Work",
        "2": "Active Speaking / Conversation",
        "3": "Acute Timed Stressor",
        "4": "Single-Modality Fallback"
    }
    condition = cond_map.get(cond_choice, "Custom Condition")

    input(f"\nCondition set to: '{condition}'. Press [Enter] when capture window completes...")
    prompt_time = time.time()

    def get_score(prompt: str) -> int:
        while True:
            val = input(prompt + " [1-5]: ").strip()
            if val.isdigit() and 1 <= int(val) <= 5:
                return int(val)
            print("Please enter an integer between 1 and 5.")

    print("\n--- 3-Item EMA Survey ---")
    q1 = get_score("1. How tense, anxious, or stressed did you feel? (1: Calm -> 5: Extremely Tense)")
    q2 = get_score("2. How overwhelmed did you feel by your activity? (1: In Control -> 5: Overwhelmed)")
    q3 = get_score("3. Did you notice physical tension (brow furrowing, jaw clenching)? (1: None -> 5: Severe)")

    composite = q1 + q2 + q3
    ground_truth_tier = ema_composite_to_tier(composite)
    print(f"\nComposite EMA Score: {composite}/15 -> Ground Truth: Tier {ground_truth_tier}")

    system_match = get_nearest_system_assessment(prompt_time)
    if system_match:
        sys_tier = system_match["tier"]
        time_diff = system_match["time_diff_s"]
        match_exact = (sys_tier == ground_truth_tier)
        match_tol = (abs(sys_tier - ground_truth_tier) <= 1)
        print(f"Paired with nearest system cycle ({time_diff}s apart): System Tier {sys_tier}")
        print(f"Exact Agreement: {match_exact} | 1-Tier Tolerance: {match_tol}")
    else:
        print("No recent system assessment found in DB. Recording EMA rating without paired cycle.")
        sys_tier = None
        match_exact = None
        match_tol = None

    record = {
        "record_id": f"EMA_{int(prompt_time)}",
        "timestamp": prompt_time,
        "datetime": datetime.datetime.now().isoformat(),
        "participant_id": participant_id,
        "consent_given": True,
        "is_developer": is_developer,
        "condition": condition,
        "responses": {"q1": q1, "q2": q2, "q3": q3},
        "composite_score": composite,
        "ground_truth_tier": ground_truth_tier,
        "system_window_id": system_match["id"] if system_match else None,
        "system_assessment": system_match,
        "exact_agreement": match_exact,
        "one_tier_tolerance": match_tol
    }

    # Save to JSON
    EMA_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = []
    if EMA_DATA_PATH.exists():
        try:
            with open(EMA_DATA_PATH, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []
    records.append(record)
    with open(EMA_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"\nSaved record to {EMA_DATA_PATH}. Total records: {len(records)}.")


if __name__ == "__main__":
    run_interactive_collector()

