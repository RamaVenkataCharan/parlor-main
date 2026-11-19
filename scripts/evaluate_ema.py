"""Evaluate EMA: Evaluates Ground-Truth vs System Tier accuracy from human session data.

Reads `shared_state/ema_records.json` (or a specified path) and computes:
- Strict Refusal Check (missing participant ID, timestamp, or consent flag)
- EMA Tier Class Distribution
- Majority-Class Baseline Agreement
- Exact-Tier Agreement Rate (%) with 95% Bootstrap CI
- One-Tier-Tolerance Agreement Rate (%) with 95% Bootstrap CI
- Quadratic-Weighted Cohen's Kappa (kappa_w)
- Full 3x3 Confusion Matrix (System vs EMA Ground Truth)
- Per-Participant Agreement Breakdown
- Clinical Safety Rates (Tier 2 FPR and FNR) with and without developer participants
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EMA_DATA_PATH = ROOT / "shared_state" / "ema_records.json"
DEFAULT_STUDY_DIR = ROOT / "study_data"


def load_dataset(target_path: Path) -> Tuple[List[Dict[str, Any]], str]:
    """Loads records from either study_data JSONL files or legacy JSON file."""
    # 1. If pointing to a study_data dir or jsonl file
    if target_path.is_dir() or target_path.suffix == ".jsonl" or (not target_path.exists() and DEFAULT_STUDY_DIR.exists()):
        study_dir = target_path if target_path.is_dir() else (target_path.parent if target_path.suffix == ".jsonl" else DEFAULT_STUDY_DIR)
        ema_file = study_dir / "ema_responses.jsonl"
        win_file = study_dir / "observation_windows.jsonl"
        registry_file = study_dir / "participants_registry.json"

        if not ema_file.exists():
            return [], f"No study EMA responses found at {ema_file}"

        # Load registry for roles and consent if present
        registry: Dict[str, Dict[str, Any]] = {}
        if registry_file.exists():
            try:
                with open(registry_file, "r", encoding="utf-8") as rf:
                    registry = json.load(rf)
            except Exception:
                pass

        # Load windows indexed by (participant_code, step)
        windows_by_pair: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        if win_file.exists():
            with open(win_file, "r", encoding="utf-8") as wf:
                for line in wf:
                    if line.strip():
                        try:
                            w = json.loads(line)
                            p = str(w.get("participant_code", "")).upper()
                            s = str(w.get("step", "")).lower()
                            windows_by_pair.setdefault((p, s), []).append(w)
                        except Exception:
                            pass

        # Load EMA records
        paired_records: List[Dict[str, Any]] = []
        with open(ema_file, "r", encoding="utf-8") as ef:
            for idx, line in enumerate(ef):
                if not line.strip():
                    continue
                try:
                    ema = json.loads(line)
                    p_code = str(ema.get("participant_code", "")).upper()
                    st = str(ema.get("step", "")).lower()
                    reg = registry.get(p_code, {})

                    # Determine group & role
                    grp = str(ema.get("group", reg.get("group", "validation"))).lower()
                    role = str(ema.get("role", reg.get("role", "external"))).lower()
                    consent = bool(ema.get("consent_given", reg.get("consent_given", True)))
                    is_adult = bool(ema.get("is_adult", reg.get("is_adult", True)))

                    # EXCLUDE CALIBRATION COHORT: calibration participants are excluded from validation
                    if grp == "calibration":
                        continue

                    # Ground truth tier
                    gt_tier = ema.get("mapped_tier")
                    if gt_tier is None:
                        comp = int(ema.get("q1_emotional_tension", 1)) + int(ema.get("q2_perceived_demand", 1)) + int(ema.get("q3_somatic_symptoms", 1))
                        gt_tier = 0 if comp <= 5 else (1 if comp <= 10 else 2)

                    # Match with system tier from observation windows
                    pair_wins = windows_by_pair.get((p_code, st), [])
                    pred_tier = 0
                    if pair_wins:
                        tiers = [int(w.get("model_tier", 0)) for w in pair_wins if w.get("model_tier") is not None]
                        pred_tier = int(np.round(np.mean(tiers))) if tiers else 0

                    paired_records.append({
                        "record_id": ema.get("response_id", f"ema_{idx}"),
                        "participant_id": p_code,
                        "timestamp": ema.get("timestamp", 0),
                        "consent_given": consent,
                        "is_adult": is_adult,
                        "ground_truth_tier": gt_tier,
                        "group": grp,
                        "is_developer": (role == "team"),
                        "system_assessment": {
                            "tier": pred_tier,
                            "stress_level": f"Tier {pred_tier}"
                        }
                    })
                except Exception:
                    continue

        return paired_records, f"Loaded {len(paired_records)} validation records from {study_dir}"

    # 2. Legacy JSON file
    if target_path.exists():
        with open(target_path, "r", encoding="utf-8") as f:
            try:
                raw_records = json.load(f)
                filtered = [r for r in raw_records if str(r.get("group", "validation")).lower() != "calibration"]
                return filtered, f"Loaded {len(filtered)} records from {target_path}"
            except Exception as e:
                return [], f"Failed reading JSON from {target_path}: {e}"

    return [], f"File not found: {target_path}"


def compute_quadratic_weighted_kappa(y_true: List[int], y_pred: List[int], num_classes: int = 3) -> float:
    """Computes quadratic-weighted Cohen's kappa."""
    n = len(y_true)
    if n == 0:
        return 0.0

    # Build observed confusion matrix O
    O = np.zeros((num_classes, num_classes), dtype=float)
    for t, p in zip(y_true, y_pred):
        if 0 <= t < num_classes and 0 <= p < num_classes:
            O[t, p] += 1.0

    # Marginals
    row_sums = O.sum(axis=1)
    col_sums = O.sum(axis=0)

    # Expected matrix E under independence
    E = np.outer(row_sums, col_sums) / n

    # Quadratic weight matrix W: penalty = (i - j)^2 / (k - 1)^2
    W = np.zeros((num_classes, num_classes), dtype=float)
    max_dist_sq = float((num_classes - 1) ** 2)
    for i in range(num_classes):
        for j in range(num_classes):
            W[i, j] = ((i - j) ** 2) / max_dist_sq

    # Weighted observed and expected disagreements
    num = np.sum(W * O)
    den = np.sum(W * E)

    if den == 0.0:
        return 1.0 if num == 0.0 else 0.0

    return float(1.0 - (num / den))


def bootstrap_ci(y_true: List[int], y_pred: List[int], metric_fn, n_bootstraps: int = 1000, ci: float = 0.95) -> Tuple[float, float]:
    """Computes two-sided bootstrap confidence interval."""
    rng = np.random.RandomState(42)
    n = len(y_true)
    if n < 2:
        val = metric_fn(y_true, y_pred)
        return (val, val)

    scores = []
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    for _ in range(n_bootstraps):
        idxs = rng.choice(n, size=n, replace=True)
        scores.append(metric_fn(y_true_arr[idxs], y_pred_arr[idxs]))

    alpha = (1.0 - ci) / 2.0
    lower = float(np.percentile(scores, alpha * 100))
    upper = float(np.percentile(scores, (1.0 - alpha) * 100))
    return (lower, upper)


def evaluate(file_path: Path):
    print("=" * 75)
    print(" PARLOR EMA GROUND-TRUTH ACCURACY EVALUATION")
    print(f" Target Path: {file_path}")
    print("=" * 75)

    records, msg = load_dataset(file_path)
    print(f"[LOADER] {msg}")

    if not records:
        print("\n[STATUS] REQUIRES HUMAN — PROTOCOL AND COLLECTION HARNESS READY")
        print("No human EMA records collected yet. Run Study Mode sessions (Settings -> Study Mode) or 'python scripts/ema_collector.py'.")
        return

    # 1. STRICT INTEGRITY & CONSENT REFUSAL CHECK
    print(f"\n[AUDIT] Validating {len(records)} records for participant ID, timestamp, and consent...")
    invalid_records = []
    for idx, r in enumerate(records):
        rec_id = r.get("record_id", f"index_{idx}")
        p_id = r.get("participant_id")
        ts = r.get("timestamp")
        consent = r.get("consent_given")

        reasons = []
        if not p_id or str(p_id).strip() == "" or p_id == "P_Anon":
            reasons.append("Missing/invalid participant_id")
        if not ts or not isinstance(ts, (int, float)):
            reasons.append("Missing/invalid timestamp")
        if consent is not True:
            reasons.append("Missing confirmed informed consent flag")

        if reasons:
            invalid_records.append((rec_id, reasons))

    if invalid_records:
        print(f"\n[REFUSAL] Integrity check failed on {len(invalid_records)} record(s):")
        for rec_id, reasons in invalid_records[:5]:
            print(f"  - Record {rec_id}: {', '.join(reasons)}")
        if len(invalid_records) > 5:
            print(f"  ... and {len(invalid_records) - 5} more.")
        print("\n[ABORTED] Evaluation refused due to unverified consent or missing identification metadata.")
        return

    # Filter to paired records (explicitly excluding zero-signal / 'insufficient signal' windows)
    excluded_insufficient = 0
    paired = []
    for r in records:
        sys_ass = r.get("system_assessment")
        if not sys_ass or sys_ass.get("tier") is None:
            continue
        stress_lvl = str(sys_ass.get("stress_level", "")).lower()
        tier_val = sys_ass.get("tier")
        if "insufficient" in stress_lvl or str(tier_val) in ["-1", "None", "insufficient signal"]:
            excluded_insufficient += 1
            continue
        paired.append(r)

    if excluded_insufficient > 0:
        print(f"[FILTER] Excluded {excluded_insufficient} zero-signal / 'insufficient signal' window(s) from EMA accuracy calculation.")
    if not paired:
        print("\n[STATUS] REQUIRES HUMAN — NO PAIRED SYSTEM ASSESSMENTS FOUND")
        print(f"Found {len(records)} valid EMA submissions, but none have paired system assessments.")
        return

    n_total = len(paired)
    y_true = [int(r["ground_truth_tier"]) for r in paired]
    y_pred = [int(r["system_assessment"]["tier"]) for r in paired]

    # 2. CLASS DISTRIBUTION & MAJORITY BASELINE
    counts = {0: y_true.count(0), 1: y_true.count(1), 2: y_true.count(2)}
    maj_class = max(counts, key=counts.get)
    maj_count = counts[maj_class]
    maj_pct = (maj_count / n_total) * 100.0

    print(f"\n--- 1. DATASET CHARACTERISTICS (N = {n_total}) ---")
    print(f"  Ground Truth Distribution : Tier 0={counts[0]} ({counts[0]/n_total*100:.1f}%), "
          f"Tier 1={counts[1]} ({counts[1]/n_total*100:.1f}%), Tier 2={counts[2]} ({counts[2]/n_total*100:.1f}%)")
    print(f"  Majority Class Baseline   : {maj_pct:.1f}% (Always predicting Tier {maj_class})")

    # 3. AGREEMENT METRICS & BOOTSTRAP CIS
    exact_fn = lambda yt, yp: float(np.mean(np.array(yt) == np.array(yp)) * 100.0)
    tol_fn = lambda yt, yp: float(np.mean(np.abs(np.array(yt) - np.array(yp)) <= 1) * 100.0)

    exact_acc = exact_fn(y_true, y_pred)
    exact_ci = bootstrap_ci(y_true, y_pred, exact_fn)

    tol_acc = tol_fn(y_true, y_pred)
    tol_ci = bootstrap_ci(y_true, y_pred, tol_fn)

    qw_kappa = compute_quadratic_weighted_kappa(y_true, y_pred, num_classes=3)

    print(f"\n--- 2. AGREEMENT METRICS ---")
    print(f"  Exact Tier Agreement      : {exact_acc:.1f}% (95% CI: [{exact_ci[0]:.1f}%, {exact_ci[1]:.1f}%])")
    print(f"  One-Tier Tolerance Agree  : {tol_acc:.1f}% (95% CI: [{tol_ci[0]:.1f}%, {tol_ci[1]:.1f}%])")
    print(f"  Quadratic-Weighted Kappa  : {qw_kappa:.3f}")

    # 4. 3x3 CONFUSION MATRIX
    # Fixed-width ASCII confusion matrix terminal output
    matrix = np.zeros((3, 3), dtype=int)
    for gt, pred in zip(y_true, y_pred):
        if 0 <= gt < 3 and 0 <= pred < 3:
            matrix[gt, pred] += 1

    print(f"\n--- 3. 3x3 CONFUSION MATRIX ---")
    print("                           System Prediction")
    print("Ground Truth (EMA)      Tier 0    Tier 1    Tier 2     Total")
    for row_idx, label in enumerate(["Tier 0 (Low)", "Tier 1 (Moderate)", "Tier 2 (High)"]):
        row = matrix[row_idx]
        print(f"  {label:<18}   {row[0]:>6}    {row[1]:>6}    {row[2]:>6}     {sum(row):>5}")
    col_totals = matrix.sum(axis=0)
    print(f"  {'Total Pred':<18}   {col_totals[0]:>6}    {col_totals[1]:>6}    {col_totals[2]:>6}     {n_total:>5}")

    # 5. PER-PARTICIPANT BREAKDOWN
    participants = sorted(list(set(r["participant_id"] for r in paired)))
    print(f"\n--- 4. PER-PARTICIPANT BREAKDOWN ({len(participants)} Participants) ---")
    print(f"  {'Participant':<15} {'Role':<12} {'Windows':<10} {'Exact Agree':<15} {'1-Tier Agree':<15}")
    for p in participants:
        p_recs = [r for r in paired if r["participant_id"] == p]
        p_yt = [int(r["ground_truth_tier"]) for r in p_recs]
        p_yp = [int(r["system_assessment"]["tier"]) for r in p_recs]
        p_role = "Developer" if p_recs[0].get("is_developer", False) else "External"
        p_exact = np.mean(np.array(p_yt) == np.array(p_yp)) * 100.0
        p_tol = np.mean(np.abs(np.array(p_yt) - np.array(p_yp)) <= 1) * 100.0
        print(f"  {p:<15} {p_role:<12} {len(p_recs):<10} {p_exact:>5.1f}%          {p_tol:>5.1f}%")

    # 6. COHORT SAFETY RATES (WITH AND WITHOUT DEVELOPERS)
    # Separate developer from external cohort to audit confirmation bias
    def calc_safety_rates(records_subset: List[Dict[str, Any]]) -> Tuple[float, float, int, int]:
        sub_yt = [int(r["ground_truth_tier"]) for r in records_subset]
        sub_yp = [int(r["system_assessment"]["tier"]) for r in records_subset]
        negs = sum(1 for gt in sub_yt if gt in (0, 1))
        fps = sum(1 for gt, pr in zip(sub_yt, sub_yp) if gt in (0, 1) and pr == 2)
        pos = sum(1 for gt in sub_yt if gt == 2)
        fns = sum(1 for gt, pr in zip(sub_yt, sub_yp) if gt == 2 and pr in (0, 1))
        fpr = (fps / negs * 100.0) if negs > 0 else 0.0
        fnr = (fns / pos * 100.0) if pos > 0 else 0.0
        return fpr, fnr, negs, pos

    fpr_all, fnr_all, neg_all, pos_all = calc_safety_rates(paired)
    non_dev_recs = [r for r in paired if not r.get("is_developer", False)]
    fpr_ext, fnr_ext, neg_ext, pos_ext = calc_safety_rates(non_dev_recs) if non_dev_recs else (0.0, 0.0, 0, 0)
    dev_recs = [r for r in paired if r.get("is_developer", False)]
    fpr_dev, fnr_dev, neg_dev, pos_dev = calc_safety_rates(dev_recs) if dev_recs else (0.0, 0.0, 0, 0)

    print(f"\n--- 5. TIER 2 SAFETY ANALYSIS (With & Without Developers) ---")
    print(f"  Overall Cohort (N={n_total}):")
    print(f"    - False Positive Rate (FPR): {fpr_all:.1f}% ({neg_all} non-Tier 2 trials)")
    print(f"    - False Negative Rate (FNR): {fnr_all:.1f}% ({pos_all} Tier 2 trials)")
    if non_dev_recs:
        print(f"  External / Non-Developer Cohort (N={len(non_dev_recs)}):")
        print(f"    - False Positive Rate (FPR): {fpr_ext:.1f}% ({neg_ext} non-Tier 2 trials)")
        print(f"    - False Negative Rate (FNR): {fnr_ext:.1f}% ({pos_ext} Tier 2 trials)")
    else:
        print("  External Cohort: No non-developer records present.")
    if dev_recs:
        print(f"  Developer Cohort (N={len(dev_recs)}):")
        print(f"    - False Positive Rate (FPR): {fpr_dev:.1f}% ({neg_dev} non-Tier 2 trials)")
        print(f"    - False Negative Rate (FNR): {fnr_dev:.1f}% ({pos_dev} Tier 2 trials)")

    print("\n" + "=" * 75)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate EMA Accuracy")
    parser.add_argument("file", nargs="?", default=str(DEFAULT_EMA_DATA_PATH), help="Path to EMA records JSON file")
    args = parser.parse_args()
    evaluate(Path(args.file))
