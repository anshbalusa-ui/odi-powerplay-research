#!/usr/bin/env python3
"""Build the hashed team-innings model table with optional verified pitch data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.model_table import build_model_table, validate_feature_allowlist  # noqa: E402
from odi_powerplay.pitch import validate_pitch_rows  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--innings-input",
        type=Path,
        default=ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--strength-input",
        type=Path,
        default=ROOT / "data/processed/team_strength_pre_match.csv",
    )
    parser.add_argument(
        "--venue-input",
        type=Path,
        default=ROOT / "data/processed/venue_conditions_pre_match.csv",
    )
    parser.add_argument("--pitch-input", type=Path)
    parser.add_argument("--match-start-input", type=Path)
    parser.add_argument(
        "--feature-config",
        type=Path,
        default=ROOT / "config/feature_allowlist.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/processed/model_team_innings.csv",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=ROOT / "data/processed/model_table_manifest.json",
    )
    args = parser.parse_args()

    innings_rows = read_csv(args.innings_input)
    strength_rows = read_csv(args.strength_input)
    venue_rows = read_csv(args.venue_input)
    pitch_rows: list[dict[str, str]] = []
    if args.pitch_input:
        if not args.match_start_input:
            raise ValueError("--match-start-input is required with --pitch-input")
        pitch_rows = read_csv(args.pitch_input)
        match_starts = {
            row["cricsheet_match_id"]: row.get("scheduled_start_utc", "")
            for row in read_csv(args.match_start_input)
        }
        issues = validate_pitch_rows(
            pitch_rows,
            eligible_match_ids={row["match_id"] for row in innings_rows},
            match_start_by_id=match_starts,
        )
        if issues:
            fields = sorted({issue["field"] for issue in issues})
            raise ValueError(
                f"Pitch data has {len(issues)} validation issues in fields: {', '.join(fields)}"
            )

    model_rows = build_model_table(
        innings_rows,
        strength_rows,
        venue_rows,
        pitch_rows=pitch_rows,
    )
    feature_config = json.loads(args.feature_config.read_text(encoding="utf-8"))
    feature_sets = feature_config["feature_sets"]
    base_features = [
        *feature_sets["pre_match_context"],
        *feature_sets["powerplay_primary"],
        *feature_sets["powerplay_intensity_sensitivity"],
    ]
    validate_feature_allowlist(model_rows, base_features)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(model_rows[0]))
        writer.writeheader()
        writer.writerows(model_rows)

    match_ids_by_split: dict[str, set[str]] = defaultdict(set)
    for row in model_rows:
        match_ids_by_split[str(row["split"])].add(str(row["match_id"]))
    split_rows = Counter(str(row["split"]) for row in model_rows)
    manifest = {
        "rows": len(model_rows),
        "matches": len({str(row["match_id"]) for row in model_rows}),
        "pitch_matches": sum(int(row["pitch_available"]) for row in model_rows) // 2,
        "venue_history_matches": sum(int(row["venue_history_available"]) for row in model_rows)
        // 2,
        "row_counts_by_split": dict(sorted(split_rows.items())),
        "match_counts_by_split": {
            split: len(match_ids) for split, match_ids in sorted(match_ids_by_split.items())
        },
        "match_ids_by_split": {
            split: sorted(match_ids) for split, match_ids in sorted(match_ids_by_split.items())
        },
        "model_table_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "feature_config_sha256": hashlib.sha256(args.feature_config.read_bytes()).hexdigest(),
        "strength_table_sha256": hashlib.sha256(args.strength_input.read_bytes()).hexdigest(),
        "venue_table_sha256": hashlib.sha256(args.venue_input.read_bytes()).hexdigest(),
    }
    args.manifest_output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: value for key, value in manifest.items() if key != "match_ids_by_split"},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
