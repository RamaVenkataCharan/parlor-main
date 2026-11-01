"""Evaluate EMA: Evaluates Ground-Truth vs System Tier accuracy from human session data.

Reads `shared_state/ema_records.json` and computes:
- Exact-Tier Agreement Rate (%)
- One-Tier-Tolerance Agreement Rate (%)
- 3x3 Confusion Matrix (System vs EMA Ground Truth)
- False Positive Rate (FPR) for Tier 2 (System called Tier 2 when Ground Truth was Tier 0/1)
- False Negative Rate (FNR) for Tier 2 (Ground Truth was Tier 2 but System called Tier 0/1)
"""

import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
EMA_DATA_PATH = ROOT / "shared_state" / "ema_records.json"


def evaluate():
    print("=" * 60)
    print("PARLOR EMA GROUND-TRUTH ACCURACY EVALUATION")
    print("=" * 60)

    if not EMA_DATA_PATH.exists():
        print(f"File not found: {EMA_DATA_PATH}")
        print("Status: REQUIRES HUMAN — PROTOCOL AND COLLECTION HARNESS READY")
        print("No human EMA records collected yet. Run 'python scripts/ema_collector.py' with human participants.")
        return

    with open(EMA_DATA_PATH, "r", encoding="utf-8") as f:
        try:
            records = json.load(f)
        except Exception as e:
            print(f"Error reading {EMA_DATA_PATH}: {e}")
            return

    paired_records = [r for r in records if r.get("system_assessment") is not None and r["system_assessment"].get("tier") is not None]

    if not paired_records:
        print("Status: REQUIRES HUMAN — PROTOCOL AND COLLECTION HARNESS READY")
        print(f"Found {len(records)} EMA records, but none are paired with a system assessment.")
        return

    total = len(paired_records)
    print(f"Loaded {total} paired human observation windows.\n")

    y_true = [r["ground_truth_tier"] for r in paired_records]
    y_pred = [r["system_assessment"]["tier"] for r in paired_records]

    # Confusion Matrix (3x3)
    # Rows: Ground Truth (0, 1, 2)
    # Cols: System Prediction (0, 1, 2)
    matrix = np.zeros((3, 3), dtype=int)
    for gt, pred in zip(y_true, y_pred):
        matrix[gt, pred] += 1

    exact_matches = sum(1 for gt, pred in zip(y_true, y_pred) if gt == pred)
    one_tier_matches = sum(1 for gt, pred in zip(y_true, y_pred) if abs(gt - pred) <= 1)

    exact_acc = (exact_matches / total) * 100.0
    tol_acc = (one_tier_matches / total) * 100.0

    print("--- ACCURACY METRICS ---")
    print(f"Total Paired Windows:          {total}")
    print(f"Exact Tier Agreement:          {exact_matches}/{total} ({exact_acc:.1f}%)")
    print(f"One-Tier Tolerance Agreement:  {one_tier_matches}/{total} ({tol_acc:.1f}%)\n")

    print("--- 3x3 CONFUSION MATRIX ---")
    print("                        System Prediction")
    print("Ground Truth       Tier 0    Tier 1    Tier 2    Total")
    for row_idx, label in enumerate(["Tier 0 (Low)", "Tier 1 (Moderate)", "Tier 2 (High)"]):
        row = matrix[row_idx]
        print(f"{label:<18} {row[0]:>6}    {row[1]:>6}    {row[2]:>6}    {sum(row):>5}")
    print()

    # False Positive Rate (FPR) for Tier 2:
    # Ground truth is NOT Tier 2 (Tier 0 or 1), but System called Tier 2
    negatives = sum(1 for gt in y_true if gt in (0, 1))
    fp_tier2 = sum(1 for gt, pred in zip(y_true, y_pred) if gt in (0, 1) and pred == 2)
    fpr = (fp_tier2 / negatives * 100.0) if negatives > 0 else 0.0

    # False Negative Rate (FNR) for Tier 2:
    # Ground truth IS Tier 2, but System failed to call Tier 2 (called 0 or 1)
    positives = sum(1 for gt in y_true if gt == 2)
    fn_tier2 = sum(1 for gt, pred in zip(y_true, y_pred) if gt == 2 and pred in (0, 1))
    fnr = (fn_tier2 / positives * 100.0) if positives > 0 else 0.0

    print("--- CLINICAL SAFETY RATES (Tier 2 High-Stress Detection) ---")
    print(f"False Positive Rate (FPR):     {fp_tier2}/{negatives} ({fpr:.1f}%)")
    print(f"False Negative Rate (FNR):     {fn_tier2}/{positives} ({fnr:.1f}%)")


if __name__ == "__main__":
    evaluate()

