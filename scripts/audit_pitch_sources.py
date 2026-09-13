#!/usr/bin/env python3
"""Audit the provider mix of verified pre-match pitch sources."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import pitch_source_provider_summary  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/manual/pitch_reports_verified.csv",
    )
    parser.add_argument(
        "--table-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_source_providers.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_source_provider_audit.json",
    )
    args = parser.parse_args()

    summary = pitch_source_provider_summary(read_csv(args.input))
    providers = summary.pop("providers")

    args.table_output.parent.mkdir(parents=True, exist_ok=True)
    with args.table_output.open("w", encoding="utf-8", newline="") as handle:
        if providers:
            writer = csv.DictWriter(handle, fieldnames=list(providers[0]))
            writer.writeheader()
            writer.writerows(providers)

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
