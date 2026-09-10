#!/usr/bin/env python3
"""Create an outcome-blind pre-match pitch-source collection queue."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.pitch_queue import build_pitch_queue  # noqa: E402


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise SystemExit("Pitch queue is empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data/processed/pitch_collection_queue.csv",
    )
    args = parser.parse_args()

    queue = build_pitch_queue(read_rows(args.input))
    write_rows(args.output, queue)
    print(f"Wrote {len(queue)} outcome-blind match rows to {args.output}")


if __name__ == "__main__":
    main()
