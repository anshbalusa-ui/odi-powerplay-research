#!/usr/bin/env python3
"""Audit completed SSAC27 tradeoff outputs without opening locked match data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.evaluation import calibration_coefficients, compute_metrics  # noqa: E402
from odi_powerplay.modeling import predict_model  # noqa: E402
from odi_powerplay.tradeoff import (  # noqa: E402
    PRIMARY_INTERACTIONS,
    _context_row,
    _fit_primary_model,
    _prepare_rows,
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

def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    at = (len(ordered) - 1) * probability
    lower, upper = math.floor(at), math.ceil(at)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (at - lower)



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
        if len({row["match_date"] for row in pair}) != 1:
            pair_issues.append((match_id, "match_date"))
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
    paired = json.loads(
        (args.artifact_dir / "paired_context_differences.json").read_text(encoding="utf-8")
    )
    ledger = json.loads(
        (args.artifact_dir / "bootstrap_context_values.json").read_text(encoding="utf-8")
    )
    primary = [cell for cell in cells if cell["contrast"] == "primary_1_to_2"]
    finite_primary = [cell for cell in primary if cell["defined"]]
    spec, model, _ = _fit_primary_model(rows)
    development = [row for row in rows if row["split"] == "development"]
    validation_rows = [row for row in rows if row["split"] == "validation"]
    prepared, _, _ = _prepare_rows(
        [*development, *validation_rows],
        dev=development,
        interactions=PRIMARY_INTERACTIONS,
    )
    independently_predicted = {
        (row["match_id"], int(row["batting_team_won"])): probability
        for row, probability in zip(
            validation_rows, predict_model(spec, model, prepared[len(development):])
        )
    }
    validation_predictions_reproduced = all(
        abs(innings["probability"] - independently_predicted[
            (pair["match_id"], innings["label"])
        ]) < 1e-10
        for pair in pairing_rows for innings in pair["innings"]
    )
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
    root_support_issues = []
    for cell in finite_primary:
        start = cell["run_reference"]
        target = cell["support_target"]
        if not (
            cell["support_start"]["run_min"] <= start <= cell["support_start"]["run_max"]
            and target["run_min"] <= start <= target["run_max"]
            and 0 <= cell["runs_per_wicket"] <= target["run_max"] - start
            and abs(cell["root_upper_delta"] - (target["run_max"] - start)) < 1e-9
        ):
            root_support_issues.append((cell["innings"], cell["elo_state"], cell["venue_state"]))
    preprocessing = model.named_steps["preprocessing"]
    numeric = preprocessing.named_transformers_["numeric"]
    categorical = preprocessing.named_transformers_["categorical"]
    classifier = model.named_steps["classifier"]
    names = [str(name) for name in preprocessing.get_feature_names_out()]
    coefficients = classifier.coef_[0].tolist()
    if len(names) != len(coefficients):
        raise ValueError("fitted coefficient and encoded feature counts differ")
    encoder = categorical.named_steps["encoder"]
    dropped_categories = [
        str(levels[index]) for levels, index in zip(encoder.categories_, encoder.drop_idx_)
    ]
    categorical_reference_ok = (
        spec.categorical_reference
        and all(index == 0 for index in encoder.drop_idx_)
        and len(spec.categorical_features) == len(dropped_categories)
        and all(
            dropped == min(
                str(row[field]) for row in development if row.get(field) not in (None, "")
            )
            for field, dropped in zip(spec.categorical_features, dropped_categories)
        )
        and all(
            f"categorical__{field}_{reference}" not in names
            for field, reference in zip(spec.categorical_features, dropped_categories)
        )
        and sum(len(levels) - 1 for levels in encoder.categories_)
        == sum(name.startswith("categorical__") for name in names)
    )
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
        "categorical_reference_levels": dict(zip(spec.categorical_features, dropped_categories)),
        "categorical_drop_indices": encoder.drop_idx_.tolist(),
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
        "paired_context_differences.json",
        "bootstrap_context_values.json",
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
        and report["validation_bootstrap"]["valid"] > 0
        and report["validation_bootstrap"]["valid"]
            + report["validation_bootstrap"]["failed"] == 2000
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
    data_audit = json.loads(
        (args.artifact_dir / "data_audit.json").read_text(encoding="utf-8")
    )
    validation_predictions = [
        innings for pair in pairing_rows for innings in pair["innings"]
    ]
    labels = [row["label"] for row in validation_predictions]
    probabilities = [row["probability"] for row in validation_predictions]
    observed_metrics = compute_metrics(labels, probabilities)
    observed_calibration = calibration_coefficients(labels, probabilities)
    primary_validation = validation["six_term_primary"]
    validation_reproduced = (
        all(abs(observed_metrics[name] - value) <= 1e-10
            for name, value in primary_validation["metrics"].items())
        and all(
            observed_calibration[name] is not None
            and abs(observed_calibration[name] - value) <= 1e-10
            for name, value in primary_validation["calibration"].items()
        )
    )
    validation_rng = random.Random(manifest["seed"])
    validation_by_match = {
        pair["match_id"]: pair["innings"] for pair in pairing_rows
    }
    validation_sample_ids = sorted(validation_by_match)
    bootstrap_metrics = defaultdict(list)
    validation_failed = 0
    for _ in range(2000):
        sampled = [
            inning
            for match_id in (
                validation_rng.choice(validation_sample_ids)
                for _ in validation_sample_ids
            )
            for inning in validation_by_match[match_id]
        ]
        try:
            sampled_labels = [inning["label"] for inning in sampled]
            sampled_probabilities = [inning["probability"] for inning in sampled]
            statistics = {
                **compute_metrics(sampled_labels, sampled_probabilities),
                **calibration_coefficients(sampled_labels, sampled_probabilities),
            }
        except ValueError:
            validation_failed += 1
            continue
        for name, value in statistics.items():
            if value is not None:
                bootstrap_metrics[name].append(value)
    target_bootstrap = primary_validation["validation_bootstrap"]
    validation_intervals_reproduced = (
        target_bootstrap["requested"] == 2000
        and target_bootstrap["failed"] == validation_failed
        and target_bootstrap["valid"] == 2000 - validation_failed
        and set(target_bootstrap["metrics"]) == set(bootstrap_metrics)
        and all(
            target_bootstrap["metrics"][name]["valid_replicates"] == len(values)
            and abs(target_bootstrap["metrics"][name]["lower_95"]
                    - percentile(values, .025)) < 1e-10
            and abs(target_bootstrap["metrics"][name]["upper_95"]
                    - percentile(values, .975)) < 1e-10
            for name, values in bootstrap_metrics.items()
        )
    )
    ledger_issues = []
    if len(ledger) != 1000:
        ledger_issues.append("replicate_count")
    expected_contexts = {
        (cell["innings"], cell["elo_state"], cell["venue_state"]) for cell in primary
    }
    ledger_maps = []
    for index, replicate in enumerate(ledger):
        if replicate["replicate"] != index or replicate["status"] not in {"fit", "failed"}:
            ledger_issues.append(("replicate_index_or_status", index))
        contexts = {
            (cell["innings"], cell["elo_state"], cell["venue_state"]): cell
            for cell in replicate["contexts"]
        }
        if (len(contexts) != len(replicate["contexts"])
                or set(contexts) != expected_contexts):
            ledger_issues.append(("duplicate_or_missing_context", index))
        ledger_maps.append(contexts)
    if (
        sum(rep["status"] == "fit" for rep in ledger)
        != manifest["development_refit_bootstrap"]["valid"]
        or sum(rep["status"] == "failed" for rep in ledger)
        != manifest["development_refit_bootstrap"]["failed"]
    ):
        ledger_issues.append("global_fit_failure_count")
    paired_issues = []
    valid_axes = {"innings": 9, "strength": 18, "venue": 18}
    pair_counts = defaultdict(int)
    by_context = {
        (cell["innings"], cell["elo_state"], cell["venue_state"]): cell
        for cell in primary
    }
    for record in paired:
        pair_counts[(record["axis"], record["quantity"])] += 1
        a, b = record["context_a"], record["context_b"]
        ca = by_context[(a["innings"], a["elo_state"], a["venue_state"])]
        cb = by_context[(b["innings"], b["elo_state"], b["venue_state"])]
        quantity = record["quantity"]
        if (
            record["requested_replicates"] != 1000
            or record["valid_paired_replicates"]
            + record["failed_fit_replicates"]
            + record["undefined_replicates"] != 1000
            or record["valid_paired_replicates"] < 0
            or record["failed_fit_replicates"] < 0
            or record["undefined_replicates"] < 0
        ):
            paired_issues.append((record["axis"], a, b, "replicate_counts"))
        if quantity == "runs_per_wicket":
            point_ok = ca["defined"] and cb["defined"]
            expected = ca["runs_per_wicket"] - cb["runs_per_wicket"] if point_ok else None
        else:
            point_ok = (ca["probability_difference_fixed_run"] is not None
                        and cb["probability_difference_fixed_run"] is not None)
            expected = (
                ca["probability_difference_fixed_run"]
                - cb["probability_difference_fixed_run"] if point_ok else None
            )
        if (
            (not point_ok and record["estimate"] is not None)
            or (point_ok and (
                record["estimate"] is None or abs(record["estimate"] - expected) > 1e-10
            ))
        ):
            paired_issues.append((record["axis"], a, b, "point_estimate"))
        if record["lower_95"] is not None and (
            record["upper_95"] is None or record["lower_95"] > record["upper_95"]
        ):
            paired_issues.append((record["axis"], a, b, "confidence_interval"))
        if record["axis"] == "innings":
            orientation_ok = (
                a["innings"] == 1 and b["innings"] == 0
                and a["elo_state"] == b["elo_state"]
                and a["venue_state"] == b["venue_state"]
            )
        elif record["axis"] == "strength":
            orientation_ok = (
                a["innings"] == b["innings"]
                and a["venue_state"] == b["venue_state"]
                and (a["elo_state"], b["elo_state"]) in ((1, 2), (1, 3), (2, 3))
            )
        else:
            orientation_ok = (
                a["innings"] == b["innings"]
                and a["elo_state"] == b["elo_state"]
                and (a["venue_state"], b["venue_state"]) in ((1, 2), (1, 3), (2, 3))
            )
        if not orientation_ok:
            paired_issues.append((record["axis"], a, b, "orientation"))
        aligned_values = []
        failed = 0
        a_key = (a["innings"], a["elo_state"], a["venue_state"])
        b_key = (b["innings"], b["elo_state"], b["venue_state"])
        for replicate, contexts in zip(ledger, ledger_maps):
            if replicate["status"] != "fit":
                failed += 1
                continue
            if not point_ok:
                continue
            va, vb = contexts.get(a_key, {}), contexts.get(b_key, {})
            if va.get(quantity) is not None and vb.get(quantity) is not None:
                aligned_values.append(va[quantity] - vb[quantity])
        valid = len(aligned_values)
        undefined = len(ledger) - failed - valid
        if (
            record["valid_paired_replicates"] != valid
            or record["undefined_replicates"] != undefined
            or record["failed_fit_replicates"] != failed
        ):
            paired_issues.append((record["axis"], a, b, "unaligned_paired_counts"))
        interval_allowed = point_ok and valid and (
            quantity != "runs_per_wicket" or valid >= .8 * len(ledger)
        )
        if interval_allowed:
            lower = percentile(aligned_values, .025)
            upper = percentile(aligned_values, .975)
            if (
                record["lower_95"] is None or record["upper_95"] is None
                or abs(record["lower_95"] - lower) > 1e-10
                or abs(record["upper_95"] - upper) > 1e-10
            ):
                paired_issues.append((record["axis"], a, b, "unaligned_paired_ci"))
        elif record["lower_95"] is not None or record["upper_95"] is not None:
            paired_issues.append((record["axis"], a, b, "unsupported_paired_ci"))
    paired_count_ok = len(paired) == 90 and all(
        pair_counts[(axis, quantity)] == count
        for axis, count in valid_axes.items()
        for quantity in ("fixed_run_probability_difference", "runs_per_wicket")
    )
    finite_root_intervals_ok = all(
        (cell.get("bootstrap_ci") or {}).get("runs_per_wicket", {})
        .get("valid_replicates", 0) > 0
        for cell in finite_primary
    )
    fixed_run_intervals_ok = all(
        (cell.get("bootstrap_ci") or {}).get("fixed_run_probability_difference", {})
        .get("valid_replicates", 0) > 0
        for cell in primary if cell.get("probability_difference_fixed_run") is not None
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
        "locked_data_audit_outcomes_loaded": data_audit["locked_test_outcomes_loaded"],
        "locked_data_audit_scored": data_audit["locked_test_scored"],
        "validation_primary_metrics_reproduced_from_pairings": validation_reproduced,
        "validation_primary_predictions_reproduced_from_development_fit": (
            validation_predictions_reproduced
        ),
        "validation_primary_bootstrap_intervals_reproduced": (
            validation_intervals_reproduced
        ),
        "pair_issue_count": len(pair_issues),
        "pair_issue_examples": pair_issues[:10],
        "primary_context_cell_count": len(primary),
        "primary_finite_root_count": len(finite_primary),
        "primary_root_support_issues": root_support_issues,
        "finite_primary_root_intervals_available": finite_root_intervals_ok,
        "supported_primary_fixed_run_intervals_available": fixed_run_intervals_ok,
        "categorical_reference_encoding_verified": categorical_reference_ok,
        "primary_categorical_references": dict(zip(spec.categorical_features, dropped_categories)),
        "paired_context_rows": len(paired),
        "paired_context_count_ok": paired_count_ok,
        "paired_context_issues": paired_issues[:10],
        "bootstrap_replicate_ledger_issues": ledger_issues[:10],
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
        "validation_bootstrap_counts_reconcile": validation_bootstrap_ok,
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
            and data_audit["locked_test_outcomes_loaded"] is False
            and data_audit["locked_test_scored"] is False
            and data_audit["issue_count"] == 0
            and validation_predictions_reproduced
            and validation_reproduced
            and validation_intervals_reproduced
            and len(pair_issues) == 0
            and len(pairing_rows) == 71
            and not pairing_issues
            and len(primary) == 18
            and len(cells) == 54
            and not root_support_issues
            and finite_root_intervals_ok
            and fixed_run_intervals_ok
            and categorical_reference_ok
            and paired_count_ok
            and not paired_issues
            and not ledger_issues
            and max(residuals, default=0.0) < 1e-4
            and manifest["development_refit_bootstrap"]["requested"] == 1000
            and manifest["development_refit_bootstrap"]["valid"]
                + manifest["development_refit_bootstrap"]["failed"] == 1000
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
