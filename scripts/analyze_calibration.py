"""Analyze Calibration: Evaluates feature distributions, rest vs stressor effect sizes,
feature separation, and trigger rule simulations from calibration study sessions.

Mandates:
- Reads `study_data/observation_windows.jsonl` (or custom path).
- Filters for `group == "calibration"`.
- Refuses to run on <3 participants with clear warning unless `--allow-small-n` is set.
- Computes feature distributions per step (median, IQR, 5th, 95th percentiles).
- Computes bootstrap effect sizes (Rest vs Stressor) with 95% CI.
- Simulates candidate trigger rules (Tier >= 1, Tier 2, baseline z-scores, persistence).
- Writes `docs/CALIBRATION_REPORT.md` and saves face-free scalar plots to `evidence/calibration_plots/`.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WINDOWS_PATH = ROOT / "study_data" / "observation_windows.jsonl"
DEFAULT_REPORT_PATH = ROOT / "docs" / "CALIBRATION_REPORT.md"
DEFAULT_PLOTS_DIR = ROOT / "evidence" / "calibration_plots"

TARGET_FEATURES = [
    ("au04", "AU04 Brow Furrow"),
    ("au07", "AU07 Eyelid Tighten"),
    ("au15", "AU15 Lip Depressor"),
    ("au20", "AU20 Lip Stretch"),
    ("pose_pitch", "Head Pitch (deg)"),
    ("pitch_delta_hz", "Pitch Delta (Hz)"),
    ("jitter_pct", "Voice Jitter (%)"),
    ("shimmer_pct", "Voice Shimmer (%)"),
    ("steadiness", "Voice Steadiness (0-1)"),
    ("speech_pace", "Speech Pace Proxy"),
]

STEPS = ["rest", "speech", "stressor", "recovery"]


def compute_distribution(vals: List[float]) -> Dict[str, float]:
    """Computes sample size, median, interquartile range (IQR), 5th and 95th percentiles."""
    if not vals:
        return {"n": 0, "median": 0.0, "iqr": 0.0, "p05": 0.0, "p95": 0.0}
    arr = np.array(vals, dtype=float)
    p25 = float(np.percentile(arr, 25))
    p75 = float(np.percentile(arr, 75))
    return {
        "n": len(arr),
        "median": float(np.median(arr)),
        "iqr": float(p75 - p25),
        "p05": float(np.percentile(arr, 5)),
        "p95": float(np.percentile(arr, 95)),
    }


def compute_cohens_d(x1: np.ndarray, x2: np.ndarray) -> float:
    """Computes Cohen's d effect size between two groups."""
    n1, n2 = len(x1), len(x2)
    if n1 < 2 or n2 < 2:
        return 0.0
    # Compute unbiased sample variances and pooled standard deviation
    s1_sq = float(np.var(x1, ddof=1))
    s2_sq = float(np.var(x2, ddof=1))
    pooled_s = math.sqrt(((n1 - 1) * s1_sq + (n2 - 1) * s2_sq) / (n1 + n2 - 2))
    if pooled_s <= 1e-8:
        return 0.0
    return float((np.mean(x2) - np.mean(x1)) / pooled_s)


def bootstrap_effect_size_ci(
    x_rest: List[float], x_stress: List[float], n_bootstraps: int = 1000, ci: float = 0.95
) -> Tuple[float, float, float]:
    """Computes Cohen's d with two-sided bootstrap confidence interval."""
    if len(x_rest) < 2 or len(x_stress) < 2:
        return (0.0, 0.0, 0.0)
    arr_rest = np.array(x_rest, dtype=float)
    arr_stress = np.array(x_stress, dtype=float)

    point_d = compute_cohens_d(arr_rest, arr_stress)
    # Resample with replacement to compute empirical bootstrap distribution
    rng = np.random.RandomState(42)
    boot_ds = []

    for _ in range(n_bootstraps):
        b_rest = rng.choice(arr_rest, size=len(arr_rest), replace=True)
        b_stress = rng.choice(arr_stress, size=len(arr_stress), replace=True)
        boot_ds.append(compute_cohens_d(b_rest, b_stress))

    alpha = (1.0 - ci) / 2.0
    lower = float(np.percentile(boot_ds, alpha * 100))
    upper = float(np.percentile(boot_ds, (1.0 - alpha) * 100))
    return (point_d, lower, upper)


def run_analysis(
    windows_path: Path,
    report_path: Path,
    plots_dir: Path,
    allow_small_n: bool = False,
) -> bool:
    print("=" * 75)
    print(" PARLOR CALIBRATION COHORT FEATURE ANALYSIS")
    print(f" Target Windows: {windows_path}")
    print("=" * 75)

    if not windows_path.exists():
        print("\n[STATUS] REQUIRES HUMAN — CALIBRATION PROTOCOL AND ANALYSIS HARNESS READY")
        print(f"File not found: {windows_path}")
        print("Run calibration sessions via Study Mode in the Parlor UI (Settings -> Study Mode).")
        return False

    records: List[Dict[str, Any]] = []
    with open(windows_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass

    if not records:
        print("\n[STATUS] REQUIRES HUMAN — DATASET IS EMPTY")
        return False

    # Filter to calibration cohort
    calib_records = [
        r for r in records if str(r.get("group", "")).strip().lower() == "calibration"
    ]
    if not calib_records:
        print("\n[STATUS] REQUIRES HUMAN — NO CALIBRATION RECORDS FOUND")
        print(f"Found {len(records)} total observation windows, but none belong to 'calibration' group.")
        return False

    participants = sorted(list(set(str(r.get("participant_code", "")).upper() for r in calib_records)))
    print(f"\n[COHORT] Found {len(calib_records)} calibration observation windows across {len(participants)} participant(s): {', '.join(participants)}")

    # Check N >= 3 requirement
    if len(participants) < 3 and not allow_small_n:
        print("\n" + "!" * 75)
        print(f"[REFUSAL] Insufficient calibration cohort size (N = {len(participants)} < 3).")
        print("Protocol mandates at least 3 distinct human participants to compute population baselines.")
        print("Use '--allow-small-n' only for automated unit testing or developer simulation.")
        print("!" * 75)
        return False

    # Extract features per step
    step_data: Dict[str, Dict[str, List[float]]] = {s: {feat[0]: [] for feat in TARGET_FEATURES} for s in STEPS}
    step_records: Dict[str, List[Dict[str, Any]]] = {s: [] for s in STEPS}

    for r in calib_records:
        st = str(r.get("step", "")).strip().lower()
        if st in step_data:
            step_records[st].append(r)
            for f_key, _ in TARGET_FEATURES:
                v = r.get(f_key)
                if v is None and "face" in r and isinstance(r["face"], dict):
                    v = r["face"].get(f_key)
                if v is None and "vocal" in r and isinstance(r["vocal"], dict):
                    v = r["vocal"].get(f_key)
                if v is not None and isinstance(v, (int, float)) and not math.isnan(float(v)):
                    step_data[st][f_key].append(float(v))

    print("\n--- 1. FEATURE DISTRIBUTIONS PER PROTOCOL STEP ---")
    dist_table: Dict[str, Dict[str, Dict[str, float]]] = {}
    for st in STEPS:
        print(f"\nStep: {st.upper()} (N = {len(step_records[st])} windows)")
        dist_table[st] = {}
        for f_key, f_label in TARGET_FEATURES:
            d = compute_distribution(step_data[st][f_key])
            dist_table[st][f_key] = d
            print(f"  {f_label:<25} : Median={d['median']:>6.3f}, IQR={d['iqr']:>6.3f}, P05={d['p05']:>6.3f}, P95={d['p95']:>6.3f}")

    print("\n--- 2. REST VS STRESSOR EFFECT SIZES (Cohen's d + 95% Bootstrap CI) ---")
    effects_table: Dict[str, Tuple[float, float, float]] = {}
    for f_key, f_label in TARGET_FEATURES:
        r_vals = step_data["rest"][f_key]
        s_vals = step_data["stressor"][f_key]
        d_val, ci_lo, ci_hi = bootstrap_effect_size_ci(r_vals, s_vals)
        effects_table[f_key] = (d_val, ci_lo, ci_hi)
        sig = " (Moderate/Large)" if abs(d_val) >= 0.5 else " (Small/Negligible)"
        print(f"  {f_label:<25} : d = {d_val:>+6.3f} [95% CI: {ci_lo:>+6.3f}, {ci_hi:>+6.3f}]{sig}")

    print("\n--- 3. CANDIDATE TRIGGER RULE SIMULATION ---")
    # Simulate trigger rules across rest vs stressor windows
    rest_wins = step_records["rest"]
    stress_wins = step_records["stressor"]

    # Candidate Rule 1: Model Tier >= 1
    def rule_tier1(win: dict) -> bool:
        t = win.get("model_tier", 0)
        return int(t) >= 1 if isinstance(t, (int, float)) else False

    # Candidate Rule 2: Model Tier == 2
    def rule_tier2(win: dict) -> bool:
        t = win.get("model_tier", 0)
        return int(t) == 2 if isinstance(t, (int, float)) else False

    # Candidate Rule 3: AU04 Elevated (> Median_Rest + 1.5 * IQR_Rest)
    au04_thresh = dist_table["rest"]["au04"]["median"] + 1.5 * dist_table["rest"]["au04"]["iqr"]
    def rule_au04_z(win: dict) -> bool:
        return float(win.get("au04", 0.0)) > au04_thresh

    rules = [
        ("Tier >= 1 (Sensitive)", rule_tier1),
        ("Tier == 2 (Conservative/High Stress)", rule_tier2),
        (f"AU04 > Baseline + 1.5 IQR (> {au04_thresh:.2f})", rule_au04_z),
    ]

    print(f"  {'Rule Name':<40} {'Rest FPR (%)':<16} {'Stressor TPR (%)':<18} {'Separation':<12}")
    sim_results = []
    for r_name, r_fn in rules:
        r_fpr = (sum(1 for w in rest_wins if r_fn(w)) / len(rest_wins) * 100.0) if rest_wins else 0.0
        s_tpr = (sum(1 for w in stress_wins if r_fn(w)) / len(stress_wins) * 100.0) if stress_wins else 0.0
        sep = s_tpr - r_fpr
        sim_results.append((r_name, r_fpr, s_tpr, sep))
        print(f"  {r_name:<40} {r_fpr:>10.1f}%       {s_tpr:>10.1f}%         {sep:>+8.1f}%")

    # Generate Plots
    plots_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Plot 1: Rest vs Stressor Boxplots for key biomarkers
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        plot_keys = [("au04", "AU04 Brow Furrow"), ("pitch_delta_hz", "Pitch Delta (Hz)"), ("steadiness", "Voice Steadiness")]
        for ax, (k, lbl) in zip(axes, plot_keys):
            data_to_plot = [step_data[s][k] for s in STEPS if step_data[s][k]]
            labels_to_plot = [s.capitalize() for s in STEPS if step_data[s][k]]
            if data_to_plot:
                ax.boxplot(data_to_plot, labels=labels_to_plot, patch_artist=True)
            ax.set_title(lbl, fontsize=12, fontweight="bold")
            ax.grid(True, linestyle="--", alpha=0.5)

        plt.tight_layout()
        plot1_path = plots_dir / "calibration_feature_distributions.png"
        fig.savefig(plot1_path, dpi=150)
        plt.close(fig)
        print(f"\n[PLOTS] Generated face-free scalar distribution chart: {plot1_path}")
    except Exception as e:
        print(f"\n[PLOTS NOTE] Could not render matplotlib plot ({e}). Proceeding with text report.")

    # Write CALIBRATION_REPORT.md
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Parlor Human Calibration Analysis Report\n\n")
        f.write(f"**Cohort Size:** N = {len(participants)} Participants ({', '.join(participants)})\n")
        f.write(f"**Total Calibration Windows:** {len(calib_records)}\n")
        f.write(f"**Data Source:** `{windows_path.name}` (Strict numeric features only; zero raw media)\n\n")
        f.write("---\n\n")

        f.write("## 1. Feature Distributions Across Protocol Steps\n\n")
        f.write("| Feature | Step | N | Median | IQR | 5th % | 95th % |\n")
        f.write("|:---|:---|:---:|:---:|:---:|:---:|:---:|\n")
        for st in STEPS:
            for f_key, f_label in TARGET_FEATURES:
                d = dist_table[st][f_key]
                f.write(f"| {f_label} | {st.capitalize()} | {d['n']} | {d['median']:.3f} | {d['iqr']:.3f} | {d['p05']:.3f} | {d['p95']:.3f} |\n")

        f.write("\n---\n\n")
        f.write("## 2. Rest vs Stressor Effect Sizes (Cohen's d)\n\n")
        f.write("| Biomarker | Cohen's d | 95% Bootstrap CI | Interpretation |\n")
        f.write("|:---|:---:|:---:|:---|\n")
        for f_key, f_label in TARGET_FEATURES:
            d_val, ci_lo, ci_hi = effects_table[f_key]
            interp = "Moderate/Large Effect" if abs(d_val) >= 0.5 else "Small Effect"
            f.write(f"| {f_label} | {d_val:+.3f} | [{ci_lo:+.3f}, {ci_hi:+.3f}] | {interp} |\n")

        f.write("\n---\n\n")
        f.write("## 3. Trigger Policy Simulation & Separation\n\n")
        f.write("| Trigger Candidate Rule | Rest False Positive Rate (%) | Stressor True Positive Rate (%) | Net Separation (%) |\n")
        f.write("|:---|:---:|:---:|:---:|\n")
        for r_name, r_fpr, s_tpr, sep in sim_results:
            f.write(f"| {r_name} | {r_fpr:.1f}% | {s_tpr:.1f}% | {sep:+.1f}% |\n")

        f.write("\n---\n\n")
        f.write("## 4. Methodological Transparency & Limitations\n\n")
        f.write("- **Zero Media Leak:** All distributions and plots are strictly numeric scalars; no webcam frames, landmark coordinate meshes, or audio files are ever stored.\n")
        f.write(f"- **Sample Size:** Current analysis reflects N = {len(participants)}. Full clinical validation requires larger heterogeneous cohorts.\n")

    print(f"\n[REPORT] Calibration report successfully written to: {report_path}")
    print("=" * 75)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze Parlor Calibration Cohort Data", epilog="Example: python scripts/analyze_calibration.py --allow-small-n")
    parser.add_argument("--windows", default=str(DEFAULT_WINDOWS_PATH), help="Path to observation_windows.jsonl")
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH), help="Path to write CALIBRATION_REPORT.md")
    parser.add_argument("--plots-dir", default=str(DEFAULT_PLOTS_DIR), help="Directory to save face-free plots")
    parser.add_argument("--allow-small-n", action="store_true", help="Allow running on N < 3 participants for testing")
    args = parser.parse_args()

    run_analysis(
        windows_path=Path(args.windows),
        report_path=Path(args.report),
        plots_dir=Path(args.plots_dir),
        allow_small_n=args.allow_small_n,
    )
