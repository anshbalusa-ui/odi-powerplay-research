#!/usr/bin/env python3
"""Build a compact local research release without redistributing match-level data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_write(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-dir", type=Path, default=ROOT / "artifacts/ssac27_tradeoff"
    )
    args = parser.parse_args()
    directory = args.artifact_dir
    analysis = json.loads((directory / "analysis_manifest.json").read_text(encoding="utf-8"))
    qa = json.loads((directory / "statistical_qa.json").read_text(encoding="utf-8"))
    parameters = json.loads(
        (directory / "primary_model_parameters.json").read_text(encoding="utf-8")
    )
    cells = json.loads(
        (directory / "context_exchange_rates.json").read_text(encoding="utf-8")
    )
    paired = json.loads(
        (directory / "paired_context_differences.json").read_text(encoding="utf-8")
    )
    if not qa["pass"]:
        raise ValueError("Refusing release with failed independent statistical QA")
    if file_sha256(directory / "primary_model_parameters.json") != qa[
        "primary_model_parameters_sha256"
    ]:
        raise ValueError("Primary fit differs from independent QA")
    if any(
        file_sha256(directory / name) != expected
        for name, expected in analysis["artifact_sha256"].items()
    ):
        raise ValueError("Analysis artifact has changed since the model run")

    roots = [cell for cell in cells if cell["contrast"] == "primary_1_to_2"]
    json_write(directory / "primary_model_metrics.json", {
        "amended_source_only": True,
        "input_table_sha256": analysis["source_sha256"],
        "development_matches": analysis["development_matches"],
        "development_rows": analysis["development_rows"],
        "validation_matches": analysis["validation_matches"],
        "validation_rows": analysis["validation_rows"],
        "locked_rows_read": analysis["locked_rows_read"],
        "primary_model": analysis["model"],
        "primary_root_contexts": len(roots),
        "primary_defined_roots": [
            {key: cell[key] for key in (
                "innings", "elo_state", "venue_state", "elo_difference",
                "venue_prior_pp_runs_mean", "run_reference", "runs_per_wicket",
                "bootstrap_ci",
            )}
            for cell in roots if cell["defined"]
        ],
        "development_refit_bootstrap": {
            key: analysis["development_refit_bootstrap"][key]
            for key in ("requested", "valid", "failed", "seed")
        },
        "paired_context_comparisons": len(paired),
    })

    names = parameters["encoded_feature_names"]
    coefficients = parameters["coefficients"]
    if len(names) != len(coefficients) or len(set(names)) != len(names):
        raise ValueError("Malformed fitted design coefficient names")
    with (directory / "primary_coefficients.csv").open(
        "w", newline="", encoding="utf-8"
    ) as destination:
        writer = csv.writer(destination)
        writer.writerow(("encoded_feature", "penalized_coefficient"))
        writer.writerow(("(intercept)", parameters["intercept"]))
        writer.writerows(zip(names, coefficients))

    validation = analysis["validation"]
    json_write(directory / "validation_metrics.json", {
        name: {
            key: report[key] for key in (
                "status", "n_rows", "n_matches", "development_rows",
                "development_matches", "class_balance", "missing_history_rows",
                "metrics", "calibration", "validation_bootstrap", "reliability_bins",
            ) if key in report
        }
        for name, report in validation.items()
    })
    json_write(directory / "sensitivity_summary.json", {
        "models": {
            name: {
                key: report[key] for key in (
                    "status", "n_rows", "n_matches", "metrics", "calibration",
                    "validation_bootstrap", "reason",
                ) if key in report
            }
            for name, report in validation.items()
            if name != "six_term_primary"
        },
        "complete_case": analysis["complete_case_sensitivity"],
        "spline": analysis["spline_sensitivity"],
    })

    release_files = (
        "analysis_manifest.json", "primary_model_parameters.json", "statistical_qa.json",
        "context_exchange_rates.json", "paired_context_differences.json",
        "bootstrap_context_values.json", "probability_contrasts.csv",
        "validation_pairings.json",
        "primary_model_metrics.json", "primary_coefficients.csv", "validation_metrics.json",
        "sensitivity_summary.json", "primary_exchange_rates.png", "data_audit.json",
    )
    for name in release_files:
        if not (directory / name).is_file():
            raise ValueError(f"Missing final release artifact: {name}")
    release_manifest = {
        "status": "amended_source_unlocked_2015_2024_only",
        "original_fixed_september_10_archive_reproduced": False,
        "archive_sha256": qa["raw_manifest"]["archive_sha256"],
        "input_table_sha256": analysis["source_sha256"],
        "protocol_sha256": file_sha256(ROOT / "docs/ssac27_powerplay_tradeoff_protocol.md"),
        "statistical_spec_sha256": file_sha256(ROOT / "docs/ssac27_tradeoff_statistical_spec.md"),
        "release_files_sha256": {
            name: file_sha256(directory / name) for name in release_files
        },
        "raw_source_bytes_in_release": False,
        "publication_note": "Local ignored files; review third-party rights before redistribution.",
    }
    json_write(directory / "release_manifest.json", release_manifest)
    print(json.dumps({
        "release_dir": str(directory), "files_hashed": len(release_files),
        "defined_primary_roots": sum(cell["defined"] for cell in roots),
        "release_manifest_sha256": file_sha256(directory / "release_manifest.json"),
    }, indent=2))


if __name__ == "__main__":
    main()
