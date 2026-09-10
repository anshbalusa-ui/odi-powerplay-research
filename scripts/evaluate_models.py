#!/usr/bin/env python3
"""Evaluate validation predictions with match-clustered uncertainty."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.evaluation import (  # noqa: E402
    cluster_bootstrap_calibration,
    cluster_bootstrap_metrics,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "artifacts/tables/validation_predictions.csv",
    )
    parser.add_argument(
        "--metrics-output",
        type=Path,
        default=ROOT / "artifacts/tables/validation_metrics.json",
    )
    parser.add_argument(
        "--calibration-output",
        type=Path,
        default=ROOT / "artifacts/tables/validation_calibration.csv",
    )
    parser.add_argument("--bootstrap-repetitions", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20250905)
    parser.add_argument("--calibration-bins", type=int, default=10)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["split"] != "validation":
            raise ValueError("Prediction file contains a non-validation row")
        grouped[row["model"]].append(row)
    if not grouped:
        raise ValueError("No predictions found")

    results: dict[str, object] = {
        "split": "validation",
        "locked_test_scored": False,
        "bootstrap_cluster": "match_id",
        "models": {},
    }
    calibration_rows: list[dict[str, object]] = []
    for model_name, model_rows in sorted(grouped.items()):
        model_result = cluster_bootstrap_metrics(
            model_rows,
            repetitions=args.bootstrap_repetitions,
            seed=args.seed,
        )
        model_result["row_count"] = len(model_rows)
        model_result["match_count"] = len({row["match_id"] for row in model_rows})
        results["models"][model_name] = model_result
        calibration_rows.extend(
            {"model": model_name, **row}
            for row in cluster_bootstrap_calibration(
                model_rows,
                bins=args.calibration_bins,
                repetitions=args.bootstrap_repetitions,
                seed=args.seed,
            )
        )

    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.calibration_output.parent.mkdir(parents=True, exist_ok=True)
    with args.calibration_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(calibration_rows[0]))
        writer.writeheader()
        writer.writerows(calibration_rows)

    compact = {
        model: {
            metric: round(values["estimate"], 4) if values["estimate"] is not None else None
            for metric, values in result["metrics"].items()
        }
        for model, result in results["models"].items()
    }
    print(json.dumps(compact, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
