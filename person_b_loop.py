"""
Person B — Phase 4 (8-12h): Full loop combining feature reading + SLM reasoning.

Polls Person A's shared JSON every ~8s, only calls the SLM when data is
new, handles missing/no-signal cases gracefully, keeps a short rolling
history, and prints live output for development.
"""

import time
from collections import deque

from person_b_reader import read_latest_features
from person_b_slm_reasoning import call_slm

POLL_INTERVAL_SECONDS = 8
HISTORY_MAXLEN = 5


def run_loop():
    history = deque(maxlen=HISTORY_MAXLEN)
    consecutive_failures = 0
    last_processed_timestamp = None

    print("Starting stress-reasoning loop. Ctrl+C to stop.\n")

    try:
        while True:
            vector, is_stale, error = read_latest_features()

            if error == "file_not_found":
                print("[waiting] No feature file yet from Person A's pipeline.")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            if error == "invalid_json_after_retries":
                print("[warn] Bad JSON read — skipping this cycle.")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            if vector is None:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            ts = vector.get("timestamp")
            if ts == last_processed_timestamp:
                # no new data since last cycle, skip SLM call to save compute
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            face = vector.get("face", {})
            audio = vector.get("audio", {})
            face_ok = face.get("face_detected", False)
            audio_ok = audio.get("voice_detected", False)

            if not face_ok and not audio_ok:
                print(f"[{ts}] No signal detected (no face, no voice) — skipping reasoning.")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            if is_stale:
                print(f"[{ts}] Data looks stale — Person A's pipeline may have stalled.")

            confidence_note = ""
            if face_ok and not audio_ok:
                confidence_note = " (reduced confidence: no audio signal)"
            elif audio_ok and not face_ok:
                confidence_note = " (reduced confidence: no face signal)"

            try:
                result = call_slm(vector, history=list(history))
                consecutive_failures = 0
                last_processed_timestamp = ts
            except Exception as e:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    sleep_time = 30
                    print(f"[{ts}] SLM unreachable, backing off (consecutive failures: {consecutive_failures}, error: {e})")
                else:
                    sleep_time = POLL_INTERVAL_SECONDS
                    print(f"[{ts}] SLM call failed unexpectedly: {e} — continuing loop.")
                time.sleep(sleep_time)
                continue

            history.append(result)

            print(f"\n[{ts}] Stress: {result['stress_level'].upper()}{confidence_note}")
            print(f"  Reasoning: {result['reasoning']}")
            print(f"  Suggested: {result['intervention']}")

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    run_loop()
