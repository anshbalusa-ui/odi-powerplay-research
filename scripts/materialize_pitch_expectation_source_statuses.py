#!/usr/bin/env python3
"""Write auditable non-assessed dispositions; never promote candidates to verified."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def screened_disposition(candidate: dict) -> dict:
    status = candidate["status"]
    if status not in {"unavailable", "needs_review", "contaminated_or_ambiguous"}:
        raise ValueError("only separately reviewed excerpts can become assessable")
    return {
        "source_url": candidate["source_url"],
        "retrieved_at_utc": candidate["retrieved_at_utc"],
        "review_status": status,
        "reviewer_id": "automated_article_condition_screen_v1",
        "status_note": candidate["reason"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path,
                        default=ROOT / "artifacts/pitch_expectations/source_candidates.jsonl")
    parser.add_argument("--captures", type=Path,
                        default=ROOT / "data/interim/pitch_expectation_captures")
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.candidates.read_text(encoding="utf-8").splitlines()]
    if len({row["cricsheet_match_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate screened source IDs")
    args.captures.mkdir(parents=True, exist_ok=True)
    written = 0
    reviewed = 0
    for candidate in rows:
        key = candidate["cricsheet_match_id"]
        path = args.captures / f"{key}.json"
        if candidate["status"] == "pre_match_candidate":
            if path.exists():
                reviewed += 1
            continue
        disposition = screened_disposition(candidate)
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing["review_status"] != disposition["review_status"] or existing["source_url"] != disposition["source_url"]:
                raise ValueError(f"{key}: stale verified capture conflicts with source screen")
            continue
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(disposition, indent=2, sort_keys=True) + "\n")
        written += 1
    print(json.dumps({"screened_source_count": len(rows), "dispositions_created": written,
                      "pre_match_candidates_reviewed": reviewed,
                      "pre_match_candidates_pending": sum(row["status"] == "pre_match_candidate" for row in rows) - reviewed,
                      "locked_test_scored": False}, sort_keys=True))


if __name__ == "__main__":
    main()
