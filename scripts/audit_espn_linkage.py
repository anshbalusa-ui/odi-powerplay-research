#!/usr/bin/env python3
"""Audit outcome-blind ESPN match-link candidates without network requests."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import (  # noqa: E402
    espn_linkage_summary,
    validate_espn_linkage_rows,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/manual/pitch_collection_queue_template.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/espn_linkage_audit.json",
    )
    parser.add_argument(
        "--issues-output",
        type=Path,
        default=ROOT / "artifacts/tables/espn_linkage_issues.csv",
    )
    args = parser.parse_args()

    rows = read_csv(args.input)
    issues = validate_espn_linkage_rows(rows)
    summary = espn_linkage_summary(rows)
    summary["validation_issue_count"] = len(issues)
    summary["validation_issues_by_field"] = dict(
        sorted(Counter(issue["field"] for issue in issues).items())
    )
    summary["input"] = str(args.input)

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
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
