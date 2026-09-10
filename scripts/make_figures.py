#!/usr/bin/env python3
"""Render validation-only calibration and model-comparison figures."""

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
    "m2_prespecified_interactions": "M2 interactions",
    "scoring_process_sensitivity": "Scoring process",
    "random_forest_challenger": "Random forest",
    "xgboost_challenger": "XGBoost",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metrics-input",
        type=Path,
        default=ROOT / "artifacts/tables/validation_metrics.json",
    )
    parser.add_argument(
        "--calibration-input",
        type=Path,
        default=ROOT / "artifacts/tables/validation_calibration.csv",
    )
    parser.add_argument(
        "--dataset-summary",
        type=Path,
        default=ROOT / "data/processed/dataset_summary.json",
    )
    parser.add_argument(
        "--model-table",
        type=Path,
        default=ROOT / "data/processed/model_team_innings.csv",
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

    dataset_summary = json.loads(args.dataset_summary.read_text(encoding="utf-8"))
    with args.model_table.open(encoding="utf-8", newline="") as handle:
        model_rows = [row for row in csv.DictReader(handle) if row["split"] != "locked_test"]
    metrics = json.loads(args.metrics_input.read_text(encoding="utf-8"))
    if metrics.get("locked_test_scored") is not False or metrics.get("split") != "validation":
        raise ValueError("Figures require validation-only metrics")
    with args.calibration_input.open(encoding="utf-8", newline="") as handle:
        calibration = list(csv.DictReader(handle))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = args.output_dir / "validation_model_comparison.png"
    calibration_path = args.output_dir / "validation_calibration.png"

    cohort_path = args.output_dir / "cohort_flow.png"
    trends_path = args.output_dir / "powerplay_trends_by_year.png"
    ordered_models = list(metrics["models"])
    estimates = [
        metrics["models"][name]["metrics"]["roc_auc"]["estimate"] for name in ordered_models
    ]
    lower = [metrics["models"][name]["metrics"]["roc_auc"]["lower_95"] for name in ordered_models]
    upper = [metrics["models"][name]["metrics"]["roc_auc"]["upper_95"] for name in ordered_models]
    positions = list(range(len(ordered_models)))

    figure, axis = plt.subplots(figsize=(9, 5.5))
    axis.errorbar(
        estimates,
        positions,
        xerr=[
            [estimate - bound for estimate, bound in zip(estimates, lower)],
            [bound - estimate for estimate, bound in zip(estimates, upper)],
        ],
        fmt="o",
        capsize=4,
        color="#174a7e",
    )
    axis.axvline(0.5, color="#777777", linestyle="--", linewidth=1)
    axis.set_yticks(positions, [DISPLAY_NAMES.get(name, name) for name in ordered_models])
    axis.set_xlabel("2024 validation ROC-AUC (95% match-clustered CI)")
    axis.set_title("ODI win-probability model comparison")
    axis.set_xlim(0.35, 0.9)
    axis.grid(axis="x", alpha=0.25)
    figure.tight_layout()
    figure.savefig(comparison_path, dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(2, 4, figsize=(12, 7), sharex=True, sharey=True)
    for axis, model_name in zip(axes.flat, ordered_models):
        rows = [row for row in calibration if row["model"] == model_name]
        if not rows:
            raise ValueError(f"Missing calibration rows for {model_name}")
        predicted = [float(row["mean_probability"]) for row in rows]
        observed = [float(row["observed_rate"]) for row in rows]
        observed_lower = [float(row["observed_rate_lower_95"]) for row in rows]
        observed_upper = [float(row["observed_rate_upper_95"]) for row in rows]
        axis.plot([0, 1], [0, 1], color="#777777", linestyle="--", linewidth=1)
        axis.errorbar(
            predicted,
            observed,
            yerr=[
                [value - bound for value, bound in zip(observed, observed_lower)],
                [bound - value for value, bound in zip(observed, observed_upper)],
            ],
            marker="o",
            linewidth=1.2,
            capsize=2,
            color="#174a7e",
        )
        axis.set_title(DISPLAY_NAMES.get(model_name, model_name), fontsize=10)
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1)
        axis.grid(alpha=0.2)
    figure.supxlabel("Mean predicted win probability")
    figure.supylabel("Observed win rate")
    figure.suptitle("2024 temporal-validation calibration", fontsize=15)
    figure.tight_layout()
    figure.savefig(calibration_path, dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8, 4.5))
    cohort_labels = ["Extracted", "Core clean", "Primary 2015+"]
    cohort_counts = [
        int(dataset_summary["extracted_matches"]),
        int(dataset_summary["core_clean_matches"]),
        int(dataset_summary["primary_matches"]),
    ]
    bars = axis.barh(cohort_labels, cohort_counts, color=["#9ecae1", "#4292c6", "#08519c"])
    axis.bar_label(bars, padding=4, fmt="{:,.0f}")
    axis.invert_yaxis()
    axis.set_xlabel("Matches")
    axis.set_title("ODI cohort construction")
    axis.set_xlim(0, max(cohort_counts) * 1.15)
    axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()
    figure.savefig(cohort_path, dpi=180)
    plt.close(figure)

    trends: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    for row in model_rows:
        trends[(int(row["year"]), int(row["batting_first"]))].append(
            (float(row["pp_runs"]), float(row["pp_wickets"]))
        )
    years = sorted({year for year, _ in trends})
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True)
    for batting_first, label, color in (
        (1, "Batting first", "#174a7e"),
        (0, "Chasing", "#c44e52"),
    ):
        run_means = [
            sum(value[0] for value in trends[(year, batting_first)])
            / len(trends[(year, batting_first)])
            for year in years
        ]
        wicket_means = [
            sum(value[1] for value in trends[(year, batting_first)])
            / len(trends[(year, batting_first)])
            for year in years
        ]
        axes[0].plot(years, run_means, marker="o", label=label, color=color)
        axes[1].plot(years, wicket_means, marker="o", label=label, color=color)
    axes[0].set_ylabel("Mean powerplay runs")
    axes[1].set_ylabel("Mean powerplay wickets")
    for axis in axes:
        axis.set_xlabel("Year")
        axis.grid(alpha=0.2)
        axis.legend(fontsize=8)
    figure.suptitle("First-10-over performance in development and validation data")
    figure.tight_layout()
    figure.savefig(trends_path, dpi=180)
    plt.close(figure)
    manifest = {
        "split": "validation",
        "locked_test_scored": False,
        "figures": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (comparison_path, calibration_path, cohort_path, trends_path)
        },
    }
    manifest_path = args.output_dir / "validation_figure_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
