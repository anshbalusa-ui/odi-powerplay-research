#!/usr/bin/env python3
"""Build canonical, machine-readable SSAC full-cohort result tables."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.evaluation import compute_metrics  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_unlocked_model_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        positions = {field: index for index, field in enumerate(header)}
        required = {"match_id", "split", "pp_runs", "pp_wickets", "pp_boundary_pct", "pp_dot_ball_pct"}
        missing = sorted(required - positions.keys())
        if missing:
            raise ValueError(f"Model table is missing required fields: {', '.join(missing)}")
        rows: list[dict[str, str]] = []
        for values in reader:
            if values[positions["split"]] == "locked_test":
                continue
            rows.append(dict(zip(header, values, strict=True)))
    return rows


def read_validation_predictions(path: Path) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("split") != "validation":
                raise ValueError("Canonical SSAC predictions must contain validation rows only")
            grouped[str(row["model"])].append(row)
    if not grouped:
        raise ValueError("Canonical SSAC predictions are empty")
    return dict(sorted(grouped.items()))


def descriptive_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_split: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_split[row["split"]].append(row)

    def summarize(values: list[float]) -> dict[str, float]:
        return {
            "mean": round(statistics.fmean(values), 6),
            "median": round(statistics.median(values), 6),
            "minimum": round(min(values), 6),
            "maximum": round(max(values), 6),
        }

    summaries: dict[str, Any] = {}
    for split, split_rows in sorted(by_split.items()):
        summaries[split] = {
            "matches": len({row["match_id"] for row in split_rows}),
            "rows": len(split_rows),
            "powerplay_runs": summarize([float(row["pp_runs"]) for row in split_rows]),
            "powerplay_wickets": summarize([float(row["pp_wickets"]) for row in split_rows]),
            "boundary_pct": summarize([float(row["pp_boundary_pct"]) for row in split_rows]),
            "dot_ball_pct": summarize([float(row["pp_dot_ball_pct"]) for row in split_rows]),
        }
    all_rows = [row for split_rows in by_split.values() for row in split_rows]
    summaries["unlocked_primary_total"] = {
        "matches": len({row["match_id"] for row in all_rows}),
        "rows": len(all_rows),
        "powerplay_runs": summarize([float(row["pp_runs"]) for row in all_rows]),
        "powerplay_wickets": summarize([float(row["pp_wickets"]) for row in all_rows]),
        "boundary_pct": summarize([float(row["pp_boundary_pct"]) for row in all_rows]),
        "dot_ball_pct": summarize([float(row["pp_dot_ball_pct"]) for row in all_rows]),
    }
    return summaries


def build_model_rows(
    predictions: dict[str, list[dict[str, str]]],
    saved_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    saved_models = saved_metrics.get("models", {})
    for model_name, rows in predictions.items():
        if model_name not in saved_models:
            raise ValueError(f"Prediction model is missing from saved metrics: {model_name}")
        labels = [int(row["label"]) for row in rows]
        probabilities = [float(row["probability"]) for row in rows]
        direct = compute_metrics(labels, probabilities)
        saved = saved_models[model_name]
        saved_metric_values = saved["metrics"]
        for metric in ("roc_auc", "log_loss", "brier_score"):
            estimate = float(saved_metric_values[metric]["estimate"])
            if abs(direct[metric] - estimate) > 1e-12:
                raise ValueError(
                    f"Saved validation metric mismatch for {model_name}/{metric}: "
                    f"{direct[metric]} != {estimate}"
                )
        output.append(
            {
                "model": model_name,
                "validation_matches": len({row["match_id"] for row in rows}),
                "validation_rows": len(rows),
                "roc_auc": direct["roc_auc"],
                "roc_auc_lower_95": saved_metric_values["roc_auc"]["lower_95"],
                "roc_auc_upper_95": saved_metric_values["roc_auc"]["upper_95"],
                "log_loss": direct["log_loss"],
                "log_loss_lower_95": saved_metric_values["log_loss"]["lower_95"],
                "log_loss_upper_95": saved_metric_values["log_loss"]["upper_95"],
                "brier_score": direct["brier_score"],
                "brier_score_lower_95": saved_metric_values["brier_score"]["lower_95"],
                "brier_score_upper_95": saved_metric_values["brier_score"]["upper_95"],
                "accuracy_at_0_5": direct["accuracy_at_0_5"],
            }
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-table",
        type=Path,
        default=ROOT / "data/processed/model_team_innings.csv",
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=ROOT / "artifacts/tables/validation_predictions.csv",
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=ROOT / "artifacts/tables/validation_metrics.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/tables/ssac_full_cohort_results.json",
    )
    parser.add_argument(
        "--model-summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/ssac_full_cohort_model_summary.csv",
    )
    args = parser.parse_args()

    unlocked_rows = read_unlocked_model_rows(args.model_table)
    predictions = read_validation_predictions(args.predictions)
    saved_metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    if saved_metrics.get("locked_test_scored") is not False:
        raise ValueError("Saved validation metrics do not prove locked-test scoring is disabled")
    model_rows = build_model_rows(predictions, saved_metrics)
    summary = {
        "analysis_scope": "primary_mens_odi_2015_through_2024_unlocked",
        "locked_test_scored": False,
        "locked_test_outcomes_loaded": False,
        "cohort_descriptives": descriptive_summary(unlocked_rows),
        "validation_models": model_rows,
        "checks": {
            "prediction_metrics_match_saved": True,
            "validation_split_only": True,
            "unlocked_model_rows": len(unlocked_rows),
            "unlocked_model_matches": len({row["match_id"] for row in unlocked_rows}),
        },
        "source_artifacts": {
            "model_table": str(args.model_table),
            "model_table_sha256": sha256(args.model_table),
            "validation_predictions": str(args.predictions),
            "validation_predictions_sha256": sha256(args.predictions),
            "validation_metrics": str(args.metrics),
            "validation_metrics_sha256": sha256(args.metrics),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.model_summary_output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(model_rows[0]) if model_rows else ["model"]
    with args.model_summary_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(model_rows)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
