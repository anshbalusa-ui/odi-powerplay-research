#!/usr/bin/env python3
"""Audit every powerplay metric and match invariant in a derived dataset."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.quality import audit_powerplay_rows  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/powerplay_metric_audit.json",
    )
    parser.add_argument(
        "--issues-output",
        type=Path,
        default=ROOT / "artifacts/tables/powerplay_metric_issues.csv",
    )
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    summary, issues = audit_powerplay_rows(rows)

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if issues:
        args.issues_output.parent.mkdir(parents=True, exist_ok=True)
        with args.issues_output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(issues[0]))
            writer.writeheader()
            writer.writerows(issues)
    elif args.issues_output.exists():
        args.issues_output.unlink()

    print(json.dumps(summary, indent=2, sort_keys=True))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
