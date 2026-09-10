#!/usr/bin/env python3
"""Geocode unique ODI venue/city pairs with an auditable free API workflow."""

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

from odi_powerplay.geocode import (  # noqa: E402
    build_geocoding_url,
    choose_candidate,
    geocode_query,
)


def read_unique_venues(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for row in rows:
        key = (str(row.get("venue") or "").strip(), str(row.get("city") or "").strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append({"venue": key[0], "city": key[1]})
    return sorted(unique, key=lambda item: (item["venue"], item["city"]))


def fetch_json(url: str, *, attempts: int = 3, timeout: int = 30) -> dict:
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
    raise RuntimeError(f"Geocoding request failed after {attempts} attempts: {url}") from last_error


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
        default=PROJECT_ROOT / "data/processed/venue_geocodes.csv",
    )
    parser.add_argument(
        "--raw-log",
        type=Path,
        default=PROJECT_ROOT / "data/raw/weather/geocoding_responses.jsonl",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=float, default=0.1)
    args = parser.parse_args()

    venues = read_unique_venues(args.input)
    if args.limit is not None:
        venues = venues[: args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.raw_log.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []

    with args.raw_log.open("w", encoding="utf-8") as raw_handle:
        for index, venue_row in enumerate(venues, start=1):
            query = geocode_query(venue_row["venue"], venue_row["city"])
            url = build_geocoding_url(query)
            try:
                payload = fetch_json(url)
                selected = choose_candidate(payload, query)
                raw_handle.write(
                    json.dumps(
                        {
                            "venue": venue_row["venue"],
                            "city": venue_row["city"],
                            "query": query,
                            "request_url": url,
                            "payload": payload,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
            except RuntimeError as exc:
                selected = {
                    "geocode_status": "request_error",
                    "geocode_auto_match": 0,
                    "geocode_id": None,
                    "geocode_name": None,
                    "geocode_admin1": None,
                    "geocode_country": None,
                    "geocode_country_code": None,
                    "latitude": None,
                    "longitude": None,
                    "timezone": None,
                }
                raw_handle.write(
                    json.dumps(
                        {
                            "venue": venue_row["venue"],
                            "city": venue_row["city"],
                            "query": query,
                            "request_url": url,
                            "error": str(exc),
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )

            results.append(
                {
                    "venue": venue_row["venue"],
                    "city": venue_row["city"],
                    "geocode_query": query,
                    "geocode_request_url": url,
                    **selected,
                }
            )
            if index < len(venues) and args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)

    if not results:
        raise SystemExit("No venue rows were available for geocoding")
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    auto = sum(int(row["geocode_auto_match"]) for row in results)
    review = len(results) - auto
    print(f"Geocoded {len(results)} venue/city pairs: {auto} auto-accepted, {review} need review")
    print(f"Output: {args.output}")
    print(f"Raw response log: {args.raw_log}")


if __name__ == "__main__":
    main()
