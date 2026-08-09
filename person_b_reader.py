"""
Person B — Phase 4: Feature reader helper.
Reads the shared JSON feature vector written by Person A's pipeline,
handling file locks, partial writes, and checking for staleness.
"""

import json
import os
import time

SHARED_FILE_PATH = "shared_state/latest_features.json"
MAX_RETRIES = 3
RETRY_DELAY = 0.05
STALE_THRESHOLD_SECONDS = 15.0


def read_latest_features():
    """Reads and parses the latest feature JSON file.
    Returns:
        tuple: (vector_dict, is_stale, error_string)
    """
    if not os.path.exists(SHARED_FILE_PATH):
        return None, False, "file_not_found"

    vector = None
    for attempt in range(MAX_RETRIES):
        try:
            with open(SHARED_FILE_PATH, "r", encoding="utf-8") as f:
                vector = json.load(f)
            break
        except (json.JSONDecodeError, PermissionError, FileNotFoundError):
            # File might be in the middle of being written to, retry after delay
            time.sleep(RETRY_DELAY)

    if vector is None:
        return None, False, "invalid_json_after_retries"

    # Normalize flat schemas to nested structure
    if "audio" not in vector and "voice_detected" in vector:
        vector = {
            "timestamp": vector.get("timestamp", os.path.getmtime(SHARED_FILE_PATH)),
            "face": {
                "face_detected": vector.get("face_detected", False),
                "au04_brow_furrow": vector.get("au04_brow_furrow", 0.0),
                "au07_lid_tightener": vector.get("au07_lid_tightener", 0.0),
                "au15_lip_depressor": vector.get("au15_lip_depressor", 0.0),
                "au20_lip_stretcher": vector.get("au20_lip_stretcher", 0.0),
                "ear": vector.get("ear", 0.3)
            },
            "audio": {
                "voice_detected": vector.get("voice_detected", False),
                "pitch_delta": vector.get("pitch_delta", 0.0),
                "pitch_variance": vector.get("pitch_variance", 0.0),
                "jitter": vector.get("jitter", 0.0),
                "shimmer": vector.get("shimmer", 0.0),
                "pause_ratio": vector.get("pause_ratio", 0.0),
                "vocal_tension": vector.get("vocal_tension", 0.0)
            }
        }

    # Evaluate staleness based on timestamp vs current system time
    is_stale = False
    ts = vector.get("timestamp")
    if ts:
        age = time.time() - ts
        if age > STALE_THRESHOLD_SECONDS:
            is_stale = True
    else:
        # Default missing/absent timestamp to stale
        is_stale = True

    return vector, is_stale, None
