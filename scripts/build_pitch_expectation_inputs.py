#!/usr/bin/env python3
"""Materialize strictly allowlisted assessor inputs from reviewed pre-match captures.

Capture JSON files are locally retained, ignored and rights-sensitive. Missing captures
remain pending; they are never silently replaced by old coder paraphrases or labels.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import (  # noqa: E402
    META_FIELDS, assessment_input, canonical_json, eligible_sources,
    rubric_hash, rubric_version, source_disposition, source_snapshot,
    validate_screened_capture,
)


def selected_csv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    """Discard excluded CSV columns at the intake boundary."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        offsets = [header.index(field) for field in fields]
        return [dict(zip(fields, (row[index] for index in offsets), strict=True)) for row in reader]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _split_for_date(match_date: str) -> str:
    if match_date <= "2023-12-31":
        return "development"
    if match_date <= "2024-12-31":
        return "validation"
    return "locked"


def _source_coverage(statuses: list[dict]) -> dict:
    """Outcome-blind included/excluded counts for each provenance stratum."""
    dimensions = {
        "by_route": "source_access_route",
        "by_year": "year",
        "by_provider": "provider",
        "by_split": "split",
    }
    counts = {}
    for name, field in dimensions.items():
        groups = {}
        for row in statuses:
            group = row[field]
            if group not in groups:
                groups[group] = {"included": 0, "excluded": 0}
            bucket = "included" if row["source_status"] == "assessable" else "excluded"
            groups[group][bucket] += 1
        counts[name] = dict(sorted(groups.items()))
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, default=ROOT / "data/manual/pitch_reports_verified.csv")
    parser.add_argument("--starts", type=Path, default=ROOT / "data/manual/match_start_times_verified.csv")
    parser.add_argument("--registry", type=Path, default=ROOT / "data/manual/pitch_code_reaudit.csv")
    parser.add_argument("--captures", type=Path, default=ROOT / "data/interim/pitch_expectation_captures")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/pitch_expectations/inputs.jsonl")
    parser.add_argument("--manifest", type=Path, default=ROOT / "artifacts/pitch_expectations/input_manifest.json")
    parser.add_argument("--screened-candidates", type=Path, required=True,
                        help="Frozen article screen bound to this source-review release")
    args = parser.parse_args()
    reports = selected_csv(args.reports, tuple(field for field in META_FIELDS
                                               if field != "scheduled_start_utc") + ("pre_match_verified",))
    starts = selected_csv(args.starts, ("cricsheet_match_id", "start_time_status",
                                        "scheduled_start_utc"))
    registry = selected_csv(args.registry, ("cricsheet_match_id", "reaudit_status"))
    timing_exclusions: list[str] = []
    candidates = eligible_sources(reports, starts, registry, timing_exclusions)
    screens = [json.loads(line) for line in
               args.screened_candidates.read_text(encoding="utf-8").splitlines()]
    screened = {row["cricsheet_match_id"]: row for row in screens}
    if (len(screened) != len(screens)
            or set(screened) != {row["cricsheet_match_id"] for row in candidates}):
        raise ValueError("article screen must cover each timing-eligible source exactly once")
    payloads = []
    by_report_id = {row["cricsheet_match_id"]: row for row in reports}
    statuses = [{
        "cricsheet_match_id": key, "source_status": "timing_ambiguous",
        "source_access_route": "no_eligible_source",
        "year": by_report_id[key]["match_date"][:4],
        "provider": urlparse(by_report_id[key]["source_url"]).hostname or "",
        "split": _split_for_date(by_report_id[key]["match_date"]),
    } for key in timing_exclusions]
    for report in candidates:
        key = report["cricsheet_match_id"]
        screened_candidate = screened[key]
        route = screened_candidate.get("source_access_route", "live_original")
        if route not in {"live_original", "archived_original"}:
            raise ValueError(f"{key}: screened source has an unsupported access route")
        status_base = {
            "cricsheet_match_id": key, "source_access_route": route,
            "year": report["match_date"][:4],
            "provider": urlparse(report["source_url"]).hostname or "",
            "split": _split_for_date(report["match_date"]),
        }
        capture_path = args.captures / f"{key}.json"
        if not capture_path.is_file():
            statuses.append({**status_base, "source_status": "not_retrieved"})
            continue
        capture = json.loads(capture_path.read_text(encoding="utf-8"))
        validate_screened_capture(report, screened_candidate, capture)
        status = capture.get("review_status", "needs_review")
        if status in {"unavailable", "contaminated_or_ambiguous", "needs_review"}:
            statuses.append({**status_base, **source_disposition(report, capture)})
            continue
        validated = source_snapshot(report, capture)
        source_hash = validated["source_hash"]
        payloads.append(assessment_input(report, report, validated["source_text"], source_hash))
        statuses.append({**status_base, "source_status": "assessable",
                         "source_hash": source_hash, "retrieved_at_utc": validated["retrieved_at_utc"],
                         "reviewer_id": validated["reviewer_id"]})
    coverage = _source_coverage(statuses)
    route_counts = Counter(row["source_access_route"] for row in statuses)
    year_counts = Counter(row["year"] for row in statuses)
    provider_counts = Counter(row["provider"] for row in statuses)
    split_counts = Counter(row["split"] for row in statuses)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(canonical_json(row) + "\n" for row in payloads), encoding="utf-8")
    summary = {
        "construct": "pre_match_expected_playing_environment_v1",
        "source_protocol_version": "PE-006-v1",
        "registry_candidate_count": len(candidates) + len(timing_exclusions),
        "eligible_source_count": len(candidates),
        "source_statuses": dict(sorted(Counter(row["source_status"] for row in statuses).items())),
        "sources": statuses,
        "assessable_count": len(payloads),
        "source_access_route_counts": dict(sorted(route_counts.items())),
        "year_counts": dict(sorted(year_counts.items())),
        "provider_counts": dict(sorted(provider_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "source_coverage_counts": coverage,
        "input_sha256": sha256(args.output),
        "rubric_sha256": rubric_hash(),
        "rubric_version": rubric_version(),
        "source_screen_sha256": sha256(args.screened_candidates),
        "source_registry_sha256": {label: sha256(path) for label, path in
                                   (("reports", args.reports), ("starts", args.starts),
                                    ("registry", args.registry))},
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "locked_test_scored": False,
    }
    args.manifest.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in
                      ("eligible_source_count", "assessable_count", "source_statuses",
                       "rubric_sha256", "locked_test_scored")}, indent=2))


if __name__ == "__main__":
    main()
