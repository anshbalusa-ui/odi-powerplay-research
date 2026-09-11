#!/usr/bin/env python3
"""Export outcome-blind follow-up rows for matches without eligible pitch analysis."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import PITCH_SET_ASIDE_FIELDS, build_pitch_set_aside  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pitch-input", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/manual/pitch_set_aside.csv",
    )
    args = parser.parse_args()

    rows = build_pitch_set_aside(read_csv(args.pitch_input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PITCH_SET_ASIDE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(
        json.dumps(
            {
                "pitch_input": str(args.pitch_input),
                "output": str(args.output),
                "set_aside_matches": len(rows),
                "network_requests_performed": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
