#!/usr/bin/env python3
"""Build an outcome-blind queue for manual match-start verification."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.start_times import START_TIME_FIELDS, build_match_start_queue  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/manual/match_start_times_template.csv",
    )
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    queue = build_match_start_queue(rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=START_TIME_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(queue)

    print(f"Wrote {len(queue)} outcome-blind match-start rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
