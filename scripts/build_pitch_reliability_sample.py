#!/usr/bin/env python3
"""Build a deterministic second-coder template without first-coder judgments."""

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
    PITCH_QUEUE_FIELDS,
    build_blinded_pitch_reliability_sample,
)


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
    parser.add_argument("--sample-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=20250905)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/manual/pitch_reliability_sample_template.csv",
    )
    args = parser.parse_args()

    reference_rows = read_csv(args.input)
    sample = build_blinded_pitch_reliability_sample(
        reference_rows,
        sample_fraction=args.sample_fraction,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [*PITCH_QUEUE_FIELDS, "sample_sequence"]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sample)

    summary = {
        "reference_matches": sum(
            str(row.get("pre_match_verified", "")).strip() == "1" for row in reference_rows
        ),
        "selected_matches": len(sample),
        "sample_fraction": args.sample_fraction,
        "seed": args.seed,
        "years": dict(sorted(Counter(str(row["match_date"])[:4] for row in sample).items())),
        "competition_types": dict(
            sorted(Counter(str(row["competition_type"]) for row in sample).items())
        ),
        "output": str(args.output),
        "first_coder_fields_exposed": False,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
