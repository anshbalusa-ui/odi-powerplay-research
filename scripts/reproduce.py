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
            [sys.executable, "scripts/build_model_table.py"],
            [sys.executable, "scripts/audit_powerplay_metrics.py"],
            [sys.executable, "scripts/build_hand_audit_sample.py"],
            [sys.executable, "scripts/build_pitch_collection_queue.py"],
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            [sys.executable, "scripts/train_models.py", "--fit-without-locked-test"],
            [sys.executable, "scripts/evaluate_models.py"],
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
        ROOT / "data/processed/model_table_manifest.json",
        ROOT / "artifacts/tables/powerplay_metric_audit.json",
        ROOT / "artifacts/models/validation_frozen/manifest.json",
        ROOT / "artifacts/tables/rolling_origin_metrics.json",
        ROOT / "artifacts/tables/validation_metrics.json",
        ROOT / "artifacts/figures/validation_figure_manifest.json",
    ]
    missing = [str(path.relative_to(ROOT)) for path in expected if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Expected artifacts missing: {', '.join(missing)}")

    manifest = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "locked_test_scored": False,
        "pitch_models_run": False,
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
