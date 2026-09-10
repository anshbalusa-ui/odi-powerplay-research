#!/usr/bin/env python3
"""Extract all ODI innings and create auditable clean cohorts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.clean import (  # noqa: E402
    clean_rows,
    select_primary_cohort,
    select_world_cup_subgroup,
)
from odi_powerplay.extract_cricsheet import extract_directory, write_csv  # noqa: E402


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=PROJECT_ROOT / "data/raw/cricsheet")
    parser.add_argument("--interim-dir", type=Path, default=PROJECT_ROOT / "data/interim")
    parser.add_argument("--processed-dir", type=Path, default=PROJECT_ROOT / "data/processed")
    args = parser.parse_args()

    manifest_path = args.input_dir / "source_manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Missing raw-source manifest: {manifest_path}")

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = extract_directory(args.input_dir)
    cleaned, audit, excluded = clean_rows(rows)
    primary = select_primary_cohort(cleaned)
    world_cup_subgroup = select_world_cup_subgroup(primary)

    args.interim_dir.mkdir(parents=True, exist_ok=True)
    args.processed_dir.mkdir(parents=True, exist_ok=True)

    all_path = args.interim_dir / "powerplay_innings_all.csv"
    clean_path = args.processed_dir / "powerplay_innings_clean.csv"
    primary_path = args.processed_dir / "powerplay_innings_primary.csv"
    world_cup_path = args.processed_dir / "powerplay_innings_world_cup_subgroup.csv"
    audit_path = args.processed_dir / "match_cohort_audit.csv"
    excluded_path = args.processed_dir / "match_exclusions.csv"

    write_csv(rows, all_path)
    write_csv(cleaned, clean_path)
    write_csv(primary, primary_path)
    write_csv(world_cup_subgroup, world_cup_path)
    write_csv(audit, audit_path)
    write_csv(excluded, excluded_path)

    exclusion_counts = Counter()
    for match in excluded:
        exclusion_counts.update(filter(None, str(match["exclusion_reasons"]).split(";")))

    competition_counts = Counter()
    counted_match_ids: set[str] = set()
    for row in primary:
        match_id = str(row["match_id"])
        if match_id not in counted_match_ids:
            competition_counts[str(row["competition_type"])] += 1
            counted_match_ids.add(match_id)

    primary_years = [int(row["year"]) for row in primary]
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_archive_sha256": raw_manifest["archive_sha256"],
        "raw_match_files": raw_manifest["json_file_count"],
        "extracted_team_innings_rows": len(rows),
        "extracted_matches": len(audit),
        "core_clean_team_innings_rows": len(cleaned),
        "core_clean_matches": len(cleaned) // 2,
        "excluded_matches": len(excluded),
        "exclusion_counts_nonexclusive": dict(sorted(exclusion_counts.items())),
        "primary_team_innings_rows": len(primary),
        "primary_matches": len(primary) // 2,
        "primary_matches_by_competition_type": dict(sorted(competition_counts.items())),
        "primary_definition": {
            "gender": "male",
            "start_year": min(primary_years),
            "end_year": max(primary_years),
            "competition_scope": "all available clean Cricsheet men's ODI competition types",
        },
        "world_cup_subgroup_team_innings_rows": len(world_cup_subgroup),
        "world_cup_subgroup_matches": len(world_cup_subgroup) // 2,
        "outputs": {
            str(path.relative_to(PROJECT_ROOT)): file_sha256(path)
            for path in (
                all_path,
                clean_path,
                primary_path,
                world_cup_path,
                audit_path,
                excluded_path,
            )
        },
    }
    summary_path = args.processed_dir / "dataset_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
