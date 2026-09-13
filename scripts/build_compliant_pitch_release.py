#!/usr/bin/env python3
"""Materialize the strict source-stated pitch release after legacy re-audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import (  # noqa: E402
    build_compliant_pitch_release,
    validate_pitch_reaudit_registry,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(rows: list[dict[str, Any]], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pitch-input",
        type=Path,
        default=ROOT / "data/manual/pitch_reports_verified.csv",
    )
    parser.add_argument(
        "--registry-input",
        type=Path,
        default=ROOT / "data/manual/pitch_code_reaudit.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/processed/pitch_reports_compliant.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_compliant_release.json",
    )
    parser.add_argument("--legacy-count", type=int, default=228)
    args = parser.parse_args()

    source_rows = read_csv(args.pitch_input)
    registry_rows = read_csv(args.registry_input)
    registry_issues = validate_pitch_reaudit_registry(
        registry_rows,
        source_rows,
        legacy_count=args.legacy_count,
    )
    if registry_issues:
        fields = sorted({issue["field"] for issue in registry_issues})
        raise ValueError(
            f"Pitch re-audit registry has {len(registry_issues)} validation issues: "
            + ", ".join(fields)
        )

    compliant_rows = build_compliant_pitch_release(
        source_rows,
        registry_rows,
        legacy_count=args.legacy_count,
    )
    fieldnames = list(source_rows[0]) if source_rows else []
    write_csv(compliant_rows, args.output, fieldnames)

    statuses = Counter(str(row.get("reaudit_status", "")).strip() for row in registry_rows)
    omitted_ids = sorted(
        str(row["cricsheet_match_id"]).strip()
        for row in registry_rows
        if str(row.get("reaudit_status", "")).strip() == "source_unavailable"
    )
    summary = {
        "release_standard": "explicit_source_only_v1",
        "legacy_count": args.legacy_count,
        "source_rows": len(source_rows),
        "compliant_rows": len(compliant_rows),
        "omitted_source_unavailable_rows": len(omitted_ids),
        "omitted_source_unavailable_match_ids": omitted_ids,
        "reaudit_statuses": dict(sorted(statuses.items())),
        "pitch_input_sha256": sha256(args.pitch_input),
        "registry_input_sha256": sha256(args.registry_input),
        "release_sha256": sha256(args.output),
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
