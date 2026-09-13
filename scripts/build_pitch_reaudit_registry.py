#!/usr/bin/env python3
"""Initialize a reproducible strict-codebook review registry."""

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
    PITCH_REAUDIT_FIELDS,
    build_pitch_reaudit_registry,
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
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/manual/pitch_code_reaudit.csv",
    )
    parser.add_argument("--legacy-count", type=int, default=228)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing manual registry. Omit during normal use.",
    )
    args = parser.parse_args()

    if args.output.exists() and not args.force:
        raise FileExistsError(
            f"Refusing to overwrite manual review state: {args.output}. Use --force only to reset."
        )

    registry = build_pitch_reaudit_registry(
        read_csv(args.input),
        legacy_count=args.legacy_count,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PITCH_REAUDIT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(registry)

    summary = {
        "rows": len(registry),
        "legacy_count": args.legacy_count,
        "coding_standards": dict(
            sorted(Counter(row["coding_standard"] for row in registry).items())
        ),
        "reaudit_statuses": dict(
            sorted(Counter(row["reaudit_status"] for row in registry).items())
        ),
        "output": str(args.output),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
