#!/usr/bin/env python3
"""Reproduce every currently unblocked full-cohort artifact in dependency order."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Reuse the existing checksummed raw Cricsheet snapshot.",
    )
    args = parser.parse_args()

    commands: list[list[str]] = []
    if not args.skip_download:
        commands.append(
            [
                sys.executable,
                "scripts/download_cricsheet.py",
                "--output-dir",
                "data/raw/cricsheet",
            ]
        )
    commands.extend(
        [
            [
                sys.executable,
                "scripts/extract_cricsheet.py",
                "--input-dir",
                "data/raw/cricsheet",
                "--output",
                "data/interim/powerplay_innings.csv",
            ],
            [sys.executable, "scripts/build_clean_dataset.py"],
            [sys.executable, "scripts/build_team_strength.py"],
            [sys.executable, "scripts/build_venue_conditions.py"],
            [
                sys.executable,
                "scripts/build_model_table.py",
                "--pitch-input",
                "data/manual/pitch_reports_verified.csv",
                "--match-start-input",
                "data/manual/match_start_times_verified.csv",
            ],
            [sys.executable, "scripts/audit_powerplay_metrics.py"],
            [sys.executable, "scripts/audit_extraction.py"],
            [sys.executable, "scripts/build_hand_audit_sample.py"],
            [sys.executable, "scripts/build_pitch_collection_queue.py"],
            [sys.executable, "scripts/build_match_start_queue.py"],
            [
                sys.executable,
                "scripts/audit_match_start_times.py",
                "--require-full-cohort",
            ],
            [
                sys.executable,
                "scripts/audit_match_start_times.py",
                "--input",
                "data/manual/match_start_times_verified.csv",
            ],
            [
                sys.executable,
                "scripts/audit_pitch_collection.py",
                "--pitch-input",
                "data/manual/pitch_reports_verified.csv",
                "--match-start-input",
                "data/manual/match_start_times_verified.csv",
            ],
            [sys.executable, "scripts/audit_pitch_sources.py"],
            [sys.executable, "scripts/build_pitch_reliability_sample.py"],
            [sys.executable, "scripts/audit_espn_linkage.py"],
            [
                sys.executable,
                "scripts/select_pitch_batch.py",
                "--n",
                "25",
                "--seed",
                "20250905",
                "--ignore-completed",
            ],
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            [sys.executable, "scripts/train_models.py", "--fit-without-locked-test"],
            [sys.executable, "scripts/evaluate_models.py"],
            [
                sys.executable,
                "scripts/train_models.py",
                "--fit-without-locked-test",
                "--input",
                "data/processed/model_team_innings_pitch.csv",
                "--model-dir",
                "artifacts/models/pitch_validation_frozen",
                "--predictions-output",
                "artifacts/tables/pitch_validation_predictions.csv",
                "--manifest-output",
                "artifacts/models/pitch_validation_frozen/manifest.json",
                "--rolling-origin-output",
                "artifacts/tables/pitch_rolling_origin_metrics.json",
                "--rolling-validation-years",
                "2022",
                "2023",
            ],
            [
                sys.executable,
                "scripts/evaluate_models.py",
                "--input",
                "artifacts/tables/pitch_validation_predictions.csv",
                "--metrics-output",
                "artifacts/tables/pitch_validation_metrics.json",
                "--calibration-output",
                "artifacts/tables/pitch_validation_calibration.csv",
            ],
            [sys.executable, "scripts/make_figures.py"],
        ]
    )

    completed: list[list[str]] = []
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)
        completed.append(command)

    expected = [
        ROOT / "data/raw/cricsheet/source_manifest.json",
        ROOT / "data/processed/dataset_summary.json",
        ROOT / "artifacts/tables/team_strength_audit.json",
        ROOT / "artifacts/tables/venue_conditions_audit.json",
        ROOT / "data/processed/model_table_manifest.json",
        ROOT / "artifacts/tables/powerplay_metric_audit.json",
        ROOT / "artifacts/tables/extraction_audit.csv",
        ROOT / "artifacts/tables/espn_linkage_audit.json",
        ROOT / "data/manual/match_start_times_template.csv",
        ROOT / "artifacts/tables/match_start_time_audit.json",
        ROOT / "data/manual/pitch_batch_001_template.csv",
        ROOT / "artifacts/tables/pitch_coverage_audit.json",
        ROOT / "artifacts/tables/pitch_collection_status.csv",
        ROOT / "artifacts/tables/pitch_source_provider_audit.json",
        ROOT / "artifacts/tables/pitch_source_providers.csv",
        ROOT / "data/manual/pitch_reliability_sample_template.csv",
        ROOT / "artifacts/models/validation_frozen/manifest.json",
        ROOT / "artifacts/tables/rolling_origin_metrics.json",
        ROOT / "artifacts/tables/validation_metrics.json",
        ROOT / "artifacts/models/pitch_validation_frozen/manifest.json",
        ROOT / "artifacts/tables/pitch_rolling_origin_metrics.json",
        ROOT / "artifacts/tables/pitch_validation_metrics.json",
        ROOT / "artifacts/figures/validation_figure_manifest.json",
    ]
    missing = [str(path.relative_to(ROOT)) for path in expected if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Expected artifacts missing: {', '.join(missing)}")

    manifest = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "locked_test_scored": False,
        "pitch_models_run": True,
        "espn_linkage_network_requests_performed": False,
        "match_start_time_network_requests_performed": False,
        "venue_history_model_run": True,
        "commands": [command[1:] for command in completed],
        "artifacts": {str(path.relative_to(ROOT)): sha256(path) for path in expected},
    }
    output = ROOT / "artifacts/run_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
