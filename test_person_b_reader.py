"""
test_person_b_reader.py — Test script to execute person_b_reader.py alone.
"""

import json
from person_b_reader import read_latest_features


def main():
    vector, is_stale, error = read_latest_features()
    print("--- Reader Results ---")
    print(f"Vector (formatted): {json.dumps(vector, indent=2)}")
    print(f"is_stale: {is_stale}")
    print(f"error: {error}")


if __name__ == "__main__":
    main()
