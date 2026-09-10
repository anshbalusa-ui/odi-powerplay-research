#!/usr/bin/env python3
"""Fit fixed chronological models without scoring the locked test."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.evaluation import compute_metrics  # noqa: E402
from odi_powerplay.model_table import FORBIDDEN_PREDICTORS  # noqa: E402
from odi_powerplay.modeling import (  # noqa: E402
    fit_model,
    make_model_specs,
    partition_chronological_rows,
    predict_model,
    rolling_origin_splits,
    validate_model_specs,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fit-without-locked-test", action="store_true")
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/processed/model_team_innings.csv",
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=ROOT / "artifacts/models/validation_frozen",
    )
    parser.add_argument(
        "--predictions-output",
        type=Path,
        default=ROOT / "artifacts/tables/validation_predictions.csv",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=ROOT / "artifacts/models/validation_frozen/manifest.json",
    )
    parser.add_argument(
        "--rolling-origin-output",
        type=Path,
        default=ROOT / "artifacts/tables/rolling_origin_metrics.json",
    )
    args = parser.parse_args()
    if not args.fit_without_locked_test:
        raise ValueError(
            "Pass --fit-without-locked-test; locked-test scoring is intentionally disabled"
        )

    try:
        import joblib
        import sklearn
        import xgboost
    except ImportError as error:
        raise RuntimeError("Install the pinned project dependencies before training") from error

    rows = read_csv(args.input)
    development, validation, locked_test_ids = partition_chronological_rows(rows)
    if not development or not validation or not locked_test_ids:
        raise ValueError("Development, validation, and locked-test periods must all be present")

    include_pitch = all(
        str(row.get("pitch_available", "0")) == "1" for row in development + validation
    )
    specs = make_model_specs(include_pitch=include_pitch)
    validate_model_specs(specs, forbidden=FORBIDDEN_PREDICTORS)
    args.model_dir.mkdir(parents=True, exist_ok=True)
    args.predictions_output.parent.mkdir(parents=True, exist_ok=True)
    rolling_results: dict[str, list[dict[str, object]]] = {}
    folds = rolling_origin_splits(development)
    for spec in specs:
        rolling_results[spec.name] = []
        for fold_training, fold_validation in folds:
            fold_model = fit_model(spec, fold_training)
            fold_probabilities = predict_model(spec, fold_model, fold_validation)
            fold_labels = [int(row["batting_team_won"]) for row in fold_validation]
            rolling_results[spec.name].append(
                {
                    "training_end_year": max(
                        int(str(row["match_date"])[:4]) for row in fold_training
                    ),
                    "validation_year": int(str(fold_validation[0]["match_date"])[:4]),
                    "training_matches": len({row["match_id"] for row in fold_training}),
                    "validation_matches": len({row["match_id"] for row in fold_validation}),
                    "metrics": compute_metrics(fold_labels, fold_probabilities),
                }
            )
    args.rolling_origin_output.parent.mkdir(parents=True, exist_ok=True)
    args.rolling_origin_output.write_text(
        json.dumps(
            {
                "locked_test_scored": False,
                "validation_years": [2021, 2022, 2023],
                "models": rolling_results,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    predictions: list[dict[str, object]] = []
    model_records: list[dict[str, object]] = []
    for spec in specs:
        model = fit_model(spec, development)
        probabilities = predict_model(spec, model, validation)
        model_path = args.model_dir / f"{spec.name}.joblib"
        joblib.dump(model, model_path)
        model_records.append(
            {
                "name": spec.name,
                "estimator": spec.estimator,
                "numeric_features": list(spec.numeric_features),
                "categorical_features": list(spec.categorical_features),
                "interaction_features": [list(pair) for pair in spec.interaction_features],
                "artifact": str(model_path.relative_to(ROOT)),
                "artifact_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
            }
        )
        predictions.extend(
            {
                "model": spec.name,
                "match_id": row["match_id"],
                "innings_number": row["innings_number"],
                "split": "validation",
                "label": int(row["batting_team_won"]),
                "probability": probability,
            }
            for row, probability in zip(validation, probabilities)
        )

    with args.predictions_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(predictions[0]))
        writer.writeheader()
        writer.writerows(predictions)

    manifest = {
        "fit_mode": "development_only_validate_2024",
        "locked_test_scored": False,
        "development_rows": len(development),
        "validation_rows": len(validation),
        "locked_test_match_count": len(locked_test_ids),
        "model_table_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "modeling_config_sha256": hashlib.sha256(
            (ROOT / "config/modeling.json").read_bytes()
        ).hexdigest(),
        "package_versions": {
            "scikit_learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
        },
        "models": model_records,
        "validation_predictions_sha256": hashlib.sha256(
            args.predictions_output.read_bytes()
        ).hexdigest(),
        "rolling_origin_metrics_sha256": hashlib.sha256(
            args.rolling_origin_output.read_bytes()
        ).hexdigest(),
    }
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in manifest.items() if key != "models"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
