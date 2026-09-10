#!/usr/bin/env python3
"""Collect free historical match-day weather for geocoded ODI venues."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.weather import build_archive_url, summarize_hourly_weather  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fetch_json(url: str, *, attempts: int = 3, timeout: int = 60) -> dict:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "odi-powerplay-research/0.1"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"Weather request failed after {attempts} attempts: {url}") from last_error


def unique_matches(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    matches: list[dict[str, str]] = []
    for row in sorted(rows, key=lambda item: (item["match_date"], item["match_id"])):
        match_id = row["match_id"]
        if match_id in seen:
            continue
        seen.add(match_id)
        matches.append(row)
    return matches


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--matches",
        type=Path,
        default=PROJECT_ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--geocodes",
        type=Path,
        default=PROJECT_ROOT / "data/processed/venue_geocodes.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data/processed/match_weather.csv",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=PROJECT_ROOT / "data/raw/weather/matches",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=float, default=0.1)
    args = parser.parse_args()

    match_rows = unique_matches(read_csv(args.matches))
    if args.limit is not None:
        match_rows = match_rows[: args.limit]
    geocode_rows = read_csv(args.geocodes)
    geocodes = {(row["venue"], row["city"]): row for row in geocode_rows}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    output: list[dict[str, object]] = []

    for index, match in enumerate(match_rows, start=1):
        match_id = match["match_id"]
        base: dict[str, object] = {
            "match_id": match_id,
            "match_date": match["match_date"],
            "venue": match["venue"],
            "city": match["city"],
            "weather_window": "full_local_calendar_day",
            "weather_model": "era5",
        }
        geocode = geocodes.get((match["venue"], match["city"]))
        if not geocode or str(geocode.get("geocode_auto_match")) != "1":
            output.append({**base, "weather_status": "missing_verified_geocode"})
            continue

        try:
            latitude = float(geocode["latitude"])
            longitude = float(geocode["longitude"])
        except (TypeError, ValueError, KeyError):
            output.append({**base, "weather_status": "invalid_geocode"})
            continue

        url = build_archive_url(latitude, longitude, match["match_date"])
        try:
            payload = fetch_json(url)
            raw_path = args.raw_dir / f"{match_id}.json"
            raw_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
            output.append(
                {
                    **base,
                    "weather_status": "ok",
                    "weather_source_url": url,
                    "geocode_name": geocode.get("geocode_name"),
                    "geocode_country": geocode.get("geocode_country"),
                    **summarize_hourly_weather(payload),
                }
            )
        except RuntimeError as exc:
            output.append(
                {
                    **base,
                    "weather_status": "request_error",
                    "weather_source_url": url,
                    "weather_error": str(exc),
                }
            )

        if index < len(match_rows) and args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    if not output:
        raise SystemExit("No match rows were available for weather collection")
    fieldnames: list[str] = []
    for row in output:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output)

    status_counts: dict[str, int] = {}
    for row in output:
        status = str(row["weather_status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    print(json.dumps({"matches": len(output), "status_counts": status_counts}, indent=2, sort_keys=True))
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
