#!/usr/bin/env python3
"""Build the leakage-safe team-innings analysis table from generated context files."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.context import merge_context  # noqa: E402
from odi_powerplay.strength import add_pre_match_elo  # noqa: E402


def read_csv(path: Path, *, optional: bool = False) -> list[dict[str, str]]:
    if optional and not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise SystemExit("Analysis table is empty")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--primary",
        type=Path,
        default=PROJECT_ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=PROJECT_ROOT / "data/interim/powerplay_innings_all.csv",
    )
    parser.add_argument(
        "--pitch",
        type=Path,
        default=PROJECT_ROOT / "data/manual/pitch_reports.csv",
    )
    parser.add_argument(
        "--weather",
        type=Path,
        default=PROJECT_ROOT / "data/processed/match_weather.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data/processed/analysis_innings.csv",
    )
    args = parser.parse_args()

    primary = read_csv(args.primary)
    history = [
        row
        for row in read_csv(args.history)
        if str(row.get("gender")) == "male" and str(row.get("match_status")) == "decided"
    ]
    with_elo = add_pre_match_elo(primary, history_rows=history)
    pitch = read_csv(args.pitch, optional=True)
    weather = read_csv(args.weather, optional=True)
    analysis = merge_context(with_elo, pitch_rows=pitch, weather_rows=weather)
    write_csv(args.output, analysis)

    summary = {
        "team_innings_rows": len(analysis),
        "matches": len({row["match_id"] for row in analysis}),
        "pitch_available_rows": sum(int(row["pitch_available"]) for row in analysis),
        "weather_available_rows": sum(int(row["weather_available"]) for row in analysis),
        "elo_rows": sum("team_elo_pre" in row for row in analysis),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
