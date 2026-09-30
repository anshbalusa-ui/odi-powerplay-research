#!/usr/bin/env python3
"""Audit completed SSAC27 tradeoff outputs without opening locked match data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.modeling import predict_model  # noqa: E402
from odi_powerplay.tradeoff import (  # noqa: E402
    _context_row,
    _fit_primary_model,
    assert_unlocked_rows,
)

EXPECTED_MODELS = {
    "additive_benchmark",
    "four_term_interaction",
    "six_term_primary",
    "strength_prior20_sensitivity",
    "boundary_dot_sensitivity",
    "restricted_cubic_spline_sensitivity",
    "random_forest_challenger",
    "xgboost_challenger",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/processed/model_team_innings.csv")
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "artifacts/ssac27_tradeoff")
    parser.add_argument("--raw-manifest", type=Path,
                        default=ROOT / "data/raw/cricsheet/unlocked_20260929/source_manifest.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = json.loads((args.artifact_dir / "analysis_manifest.json").read_text(encoding="utf-8"))
    cells = json.loads((args.artifact_dir / "context_exchange_rates.json").read_text(encoding="utf-8"))
    rows = read_rows(args.input)
    assert_unlocked_rows(rows)

    by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_match[row["match_id"]].append(row)
    pair_issues = []
    for match_id, pair in by_match.items():
        if len(pair) != 2:
            pair_issues.append((match_id, "row_count"))
            continue
        if len({row["split"] for row in pair}) != 1:
            pair_issues.append((match_id, "split"))
        if sorted(int(row["batting_team_won"]) for row in pair) != [0, 1]:
            pair_issues.append((match_id, "outcome"))
        if sorted(int(row["batting_first"]) for row in pair) != [0, 1]:
            pair_issues.append((match_id, "batting_first"))
        if {pair[0]["batting_team"], pair[0]["opponent"]} != {
            pair[1]["batting_team"], pair[1]["opponent"]
        } or pair[0]["batting_team"] == pair[0]["opponent"]:
            pair_issues.append((match_id, "teams"))

    pairing_rows = json.loads(
        (args.artifact_dir / "validation_pairings.json").read_text(encoding="utf-8")
    )
    pairing_issues = [
        pair["match_id"] for pair in pairing_rows
        if len(pair["innings"]) != 2
        or sorted(innings["label"] for innings in pair["innings"]) != [0, 1]
        or any(innings["match_id"] != pair["match_id"] for innings in pair["innings"])
        or any(not 0 <= innings["probability"] <= 1 for innings in pair["innings"])
    ]
    if len({pair["match_id"] for pair in pairing_rows}) != len(pairing_rows):
        pairing_issues.append("duplicate_validation_match")
    validation_ids = {row["match_id"] for row in rows if row["split"] == "validation"}
    if {pair["match_id"] for pair in pairing_rows} != validation_ids:
        pairing_issues.append("validation_membership_mismatch")
    primary = [cell for cell in cells if cell["contrast"] == "primary_1_to_2"]
    finite_primary = [cell for cell in primary if cell["defined"]]
    spec, model, _ = _fit_primary_model(rows)
    reference = manifest["reference_contexts"]
    residuals = []
    for cell in finite_primary:
        common = {
            "innings": cell["innings"],
            "elo": cell["elo_difference"],
            "venue_runs": cell["venue_prior_pp_runs_mean"],
        }
        before = _context_row(reference, runs=cell["run_reference"], wickets=1, **common)
        after = _context_row(
            reference,
            runs=cell["run_reference"] + cell["runs_per_wicket"],
            wickets=2,
            **common,
        )
        probabilities = predict_model(spec, model, [before, after])
        residuals.append(abs(probabilities[1] - probabilities[0]))
    preprocessing = model.named_steps["preprocessing"]
    numeric = preprocessing.named_transformers_["numeric"]
    categorical = preprocessing.named_transformers_["categorical"]
    classifier = model.named_steps["classifier"]
    names = [str(name) for name in preprocessing.get_feature_names_out()]
    coefficients = classifier.coef_[0].tolist()
    if len(names) != len(coefficients):
        raise ValueError("fitted coefficient and encoded feature counts differ")
    model_parameters = {
        "source_sha256": manifest["source_sha256"],
        "development_matches": manifest["development_matches"],
        "development_rows": manifest["development_rows"],
        "estimator": manifest["model"]["estimator"],
        "numeric_features": list(spec.numeric_features),
        "categorical_features": list(spec.categorical_features),
        "interaction_terms": manifest["model"]["interactions"],
        "interaction_decisions": manifest["interaction_decisions"],
        "numeric_imputer_statistics": numeric.named_steps["imputer"].statistics_.tolist(),
        "numeric_missing_indicator_input_indices": (
            numeric.named_steps["imputer"].indicator_.features_.tolist()
        ),
        "numeric_scaler_mean": numeric.named_steps["scaler"].mean_.tolist(),
        "numeric_scaler_scale": numeric.named_steps["scaler"].scale_.tolist(),
        "categorical_imputer_statistics": categorical.named_steps["imputer"].statistics_.tolist(),
        "categorical_encoder_categories": [
            [str(category) for category in categories]
            for categories in categorical.named_steps["encoder"].categories_
        ],
        "encoded_feature_names": names,
        "coefficients": coefficients,
        "intercept": float(classifier.intercept_[0]),
    }
    parameters_path = args.artifact_dir / "primary_model_parameters.json"
    parameters_path.write_text(
        json.dumps(model_parameters, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    artifact_paths = (
        "context_exchange_rates.json",
        "probability_contrasts.csv",
        "validation_pairings.json",
        "primary_exchange_rates.png",
    )
    artifact_checks = {
        name: {
            "sha256": sha256(args.artifact_dir / name),
            "manifest_sha256": manifest["artifact_sha256"].get(name),
        }
        for name in artifact_paths
    }
    validation = manifest["validation"]
    validation_models = sorted(validation)
    validation_bootstrap_ok = all(
        report.get("status") == "fit"
        and report["validation_bootstrap"]["requested"] == 2000
        and report["validation_bootstrap"]["valid"] == 2000
        and report["validation_bootstrap"]["failed"] == 0
        for report in validation.values()
    )
    raw_manifest = json.loads(args.raw_manifest.read_text(encoding="utf-8"))
    archive_matches = (
        sha256(Path(raw_manifest["source_archive"])) == raw_manifest["archive_sha256"]
    )
    registry_matches = (
        sha256(ROOT / "data/manual/match_start_times_template.csv")
        == raw_manifest["registry_sha256"]
    )
    qa = {
        "analysis_manifest_source_sha256_matches_input": (
            manifest["source_sha256"] == sha256(args.input)
        ),
        "input_rows": len(rows),
        "development_matches": len({row["match_id"] for row in rows if row["split"] == "development"}),
        "validation_matches": len({row["match_id"] for row in rows if row["split"] == "validation"}),
        "locked_rows_read": manifest["locked_rows_read"],
        "validation_pairings_count": len(pairing_rows),
        "validation_pairing_issues": pairing_issues,
        "locked_source_manifest_scored": raw_manifest["locked_test_scored"],
        "pair_issue_count": len(pair_issues),
        "pair_issue_examples": pair_issues[:10],
        "primary_context_cell_count": len(primary),
        "primary_finite_root_count": len(finite_primary),
        "primary_finite_root_max_probability_residual": max(residuals, default=None),
        "primary_model_parameters_sha256": sha256(parameters_path),
        "primary_root_bootstrap_valid_counts": [
            (cell.get("bootstrap_ci") or {}).get("runs_per_wicket", {}).get("valid_replicates")
            for cell in finite_primary
        ],
        "development_bootstrap": {
            key: manifest["development_refit_bootstrap"][key]
            for key in ("requested", "valid", "failed", "seed")
        },
        "validation_models": validation_models,
        "validation_models_expected": sorted(EXPECTED_MODELS),
        "validation_bootstrap_all_2000_valid": validation_bootstrap_ok,
        "sensitivity_statuses": {
            name: report.get("status") for name, report in validation.items()
        },
        "artifact_checks": artifact_checks,
        "raw_manifest": {
            "archive_sha256": raw_manifest["archive_sha256"],
            "archive_sha256_verified": archive_matches,
            "registry_sha256_verified": registry_matches,
            "unlocked_mapping_sha256": raw_manifest["unlocked_mapping_sha256"],
            "json_file_count": raw_manifest["json_file_count"],
            "locked_registry_match_count_metadata_only": raw_manifest[
                "locked_registry_match_count_metadata_only"
            ],
        },
        "pass": (
            manifest["source_sha256"] == sha256(args.input)
            and len(rows) == manifest["input_rows"] == 1884
            and len(by_match) == 942
            and len({row["match_id"] for row in rows if row["split"] == "development"}) == manifest["development_matches"] == 871
            and len({row["match_id"] for row in rows if row["split"] == "validation"}) == manifest["validation_matches"] == 71
            and raw_manifest["json_file_count"] == 942
            and archive_matches
            and registry_matches
            and manifest["locked_rows_read"] == 0
            and raw_manifest["locked_test_scored"] is False
            and len(pair_issues) == 0
            and len(pairing_rows) == 71
            and not pairing_issues
            and len(primary) == 18
            and bool(finite_primary)
            and max(residuals, default=1.0) < 1e-4
            and manifest["development_refit_bootstrap"]["requested"] == 1000
            and manifest["development_refit_bootstrap"]["valid"] == 1000
            and manifest["development_refit_bootstrap"]["failed"] == 0
            and validation_models == sorted(EXPECTED_MODELS)
            and validation_bootstrap_ok
            and all(check["sha256"] == check["manifest_sha256"]
                    for check in artifact_checks.values())
        ),
    }
    output = args.output or args.artifact_dir / "statistical_qa.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(qa, indent=2, sort_keys=True))
    if not qa["pass"]:
        raise SystemExit("SSAC27 tradeoff statistical QA failed")


if __name__ == "__main__":
    main()
