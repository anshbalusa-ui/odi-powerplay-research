#!/usr/bin/env python3
"""Render publication-ready SSAC figures and an outcome-free pitch template."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DISPLAY_NAMES = {
    "intercept_only": "Intercept only",
    "m0_pre_match": "M0 pre-match",
    "powerplay_benchmark": "Runs + wickets",
    "m1_context_powerplay": "M1 context + PP",
    "venue_history_powerplay_sensitivity": "Venue history + PP",
    "m2_prespecified_interactions": "M2 interactions",
    "scoring_process_sensitivity": "Scoring process",
    "random_forest_challenger": "Random forest",
    "xgboost_challenger": "XGBoost",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def save_figure(figure: object, output_dir: Path, stem: str) -> list[Path]:
    paths = [output_dir / f"{stem}.png", output_dir / f"{stem}.pdf"]
    for path in paths:
        figure.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results-input",
        type=Path,
        default=ROOT / "artifacts/tables/ssac_full_cohort_results.json",
    )
    parser.add_argument(
        "--marginal-input",
        type=Path,
        default=ROOT / "artifacts/tables/powerplay_marginal_results.csv",
    )
    parser.add_argument(
        "--sparsity-input",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_sparsity_cells.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts/figures",
    )
    args = parser.parse_args()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    results = json.loads(args.results_input.read_text(encoding="utf-8"))
    if results.get("locked_test_scored") is not False:
        raise ValueError("SSAC figures require locked-test scoring to remain disabled")
    marginal_rows = read_csv(args.marginal_input)
    sparsity_rows = read_csv(args.sparsity_input)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "figure.dpi": 150,
            "savefig.dpi": 300,
        }
    )
    navy = "#17365D"
    orange = "#D55E00"
    blue = "#0072B2"
    gray = "#5B6770"

    model_rows = results["validation_models"]
    labels = [DISPLAY_NAMES.get(row["model"], row["model"]) for row in model_rows]
    estimates = np.array([float(row["roc_auc"]) for row in model_rows])
    lowers = np.array([float(row["roc_auc_lower_95"]) for row in model_rows])
    uppers = np.array([float(row["roc_auc_upper_95"]) for row in model_rows])
    positions = np.arange(len(labels))
    figure, axis = plt.subplots(figsize=(7.2, 4.8))
    axis.errorbar(
        estimates,
        positions,
        xerr=[estimates - lowers, uppers - estimates],
        fmt="o",
        color=navy,
        ecolor=navy,
        capsize=3,
        markersize=4,
        linewidth=1.1,
    )
    axis.axvline(0.5, color=gray, linestyle=(0, (3, 2)), linewidth=0.9)
    axis.set_yticks(positions, labels)
    axis.invert_yaxis()
    axis.set_xlim(0.35, 0.9)
    axis.set_xlabel("Validation ROC-AUC (2024; 95% match-clustered interval)")
    axis.set_title("Pre-specified ODI win-probability models")
    axis.grid(axis="x", color="#D9DDE2", linewidth=0.7)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.text(
        0.99,
        -0.13,
        "Associational prediction; locked 2025+ outcomes withheld",
        transform=axis.transAxes,
        ha="right",
        va="top",
        fontsize=7.5,
        color=gray,
    )
    figure.tight_layout()
    comparison_paths = save_figure(figure, args.output_dir, "ssac_validation_model_comparison")
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(7.4, 3.5), sharey=True)
    run_rows = [row for row in marginal_rows if row["scenario"] == "runs_marginal"]
    wicket_rows = [row for row in marginal_rows if row["scenario"] == "wickets_marginal"]
    axes[0].plot(
        [int(row["pp_runs"]) for row in run_rows],
        [float(row["standardized_predicted_win_probability"]) for row in run_rows],
        marker="o",
        color=blue,
        linewidth=1.7,
    )
    axes[0].set_xlabel("Powerplay runs (empirical quantiles)")
    axes[0].set_ylabel("Standardized predicted win probability")
    axes[0].set_title("Runs; wickets observed")
    axes[1].plot(
        [int(row["pp_wickets"]) for row in wicket_rows],
        [float(row["standardized_predicted_win_probability"]) for row in wicket_rows],
        marker="o",
        color=orange,
        linewidth=1.7,
    )
    axes[1].set_xlabel("Powerplay wickets (empirical quantiles)")
    axes[1].set_title("Wickets; runs observed")
    for axis in axes:
        axis.set_ylim(0.25, 0.72)
        axis.grid(color="#D9DDE2", linewidth=0.7)
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Model-standardized powerplay associations, unlocked cohort", fontsize=12)
    figure.text(
        0.99,
        0.005,
        "Not causal; values standardize the fixed runs+wickets model over 2015–2024 innings",
        ha="right",
        va="bottom",
        fontsize=7.5,
        color=gray,
    )
    figure.tight_layout(rect=(0, 0.04, 1, 0.94))
    marginal_paths = save_figure(figure, args.output_dir, "ssac_powerplay_marginal")
    plt.close(figure)

    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in sparsity_rows:
        if row["split"] in {"development", "validation"}:
            counts[(row["dimension"], row["split"])] += int(row["sparse"])
    dimensions = sorted({dimension for dimension, _ in counts})
    x = np.arange(len(dimensions))
    width = 0.38
    figure, axis = plt.subplots(figsize=(8.2, 3.8))
    axis.bar(
        x - width / 2,
        [counts[(dimension, "development")] for dimension in dimensions],
        width,
        label="Development",
        color=navy,
    )
    axis.bar(
        x + width / 2,
        [counts[(dimension, "validation")] for dimension in dimensions],
        width,
        label="Validation",
        color=orange,
    )
    labels = [dimension.replace("primary_by_", "").replace("_", " ") for dimension in dimensions]
    axis.set_xticks(x, labels, rotation=28, ha="right")
    axis.set_ylabel("Cells below 10 matches")
    axis.set_title("Pitch interaction coverage template — no outcome estimates")
    axis.legend(frameon=False, ncols=2, loc="upper left")
    axis.grid(axis="y", color="#D9DDE2", linewidth=0.7)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout(rect=(0, 0.14, 1, 1))
    pitch_paths = save_figure(figure, args.output_dir, "pitch_interaction_template")
    plt.close(figure)

    paths = comparison_paths + marginal_paths + pitch_paths
    manifest = {
        "analysis_scope": results["analysis_scope"],
        "locked_test_scored": False,
        "pitch_result_status": "template_only_pending_reliability_reconciliation",
        "figures": {path.name: digest(path) for path in paths},
        "inputs": {
            "results": digest(args.results_input),
            "marginal": digest(args.marginal_input),
            "sparsity": digest(args.sparsity_input),
        },
    }
    manifest_path = args.output_dir / "ssac_figure_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
