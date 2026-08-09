"""
test_person_b_reasoning.py — Test script to execute person_b_slm_reasoning.py alone.
"""

from person_b_reader import read_latest_features
from person_b_slm_reasoning import call_slm


def main():
    vector, is_stale, error = read_latest_features()
    if not vector:
        print(f"Error: Could not read latest features. Result: {error}")
        return

    print("Running call_slm() directly against the real vector...")
    result = call_slm(vector)
    print("--- SLM Call Results ---")
    print(f"stress_level: {result.get('stress_level')}")
    print(f"reasoning: {result.get('reasoning')}")
    print(f"intervention: {result.get('intervention')}")


if __name__ == "__main__":
    main()
