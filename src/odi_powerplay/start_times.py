"""Outcome-blind collection and validation of scheduled match start times."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

START_TIME_STATUSES = {"pending", "verified", "unavailable", "rejected"}
START_TIME_FIELDS = (
    "cricsheet_match_id",
    "match_date",
    "event_name",
    "competition_type",
    "venue",
    "city",
    "team_1",
    "team_2",
    "source_search_query",
    "source_url",
    "source_title",
    "accessed_at_utc",
    "scheduled_start_local",
    "timezone_name",
    "scheduled_start_utc",
    "start_time_status",
    "verifier_id",
    "verification_note",
    "exclusion_reason",
)


def _parse_datetime(value: Any) -> datetime | None:
    normalized = str(value or "").strip().replace("Z", "+00:00")
    if not normalized:
        return None
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def build_match_start_queue(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one outcome-blind start-time verification row per match."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["match_id"])].append(row)

    queue: list[dict[str, Any]] = []
    for match_id in sorted(
        grouped,
        key=lambda value: (str(grouped[value][0]["match_date"]), value),
    ):
        match_rows = sorted(grouped[match_id], key=lambda row: int(row["innings_number"]))
        if len(match_rows) != 2 or {int(row["innings_number"]) for row in match_rows} != {1, 2}:
            raise ValueError(f"Match {match_id} must contain exactly innings 1 and 2")
        first, second = match_rows
        team_1 = str(first["batting_team"])
        team_2 = str(first["opponent"])
        if str(second["batting_team"]) != team_2 or str(second["opponent"]) != team_1:
            raise ValueError(f"Match {match_id} has inconsistent team identifiers")
        for field in ("match_date", "event_name", "competition_type", "venue", "city"):
            if str(first.get(field, "")) != str(second.get(field, "")):
                raise ValueError(f"Match {match_id} has inconsistent {field}")
        queue.append(
            {
                "cricsheet_match_id": match_id,
                "match_date": first["match_date"],
                "event_name": first["event_name"],
                "competition_type": first["competition_type"],
                "venue": first["venue"],
                "city": first["city"],
                "team_1": team_1,
                "team_2": team_2,
                "source_search_query": (
                    f'"{team_1}" "{team_2}" "{first["match_date"]}" ' "scheduled start time"
                ),
                "source_url": "",
                "source_title": "",
                "accessed_at_utc": "",
                "scheduled_start_local": "",
                "timezone_name": "",
                "scheduled_start_utc": "",
                "start_time_status": "pending",
                "verifier_id": "",
                "verification_note": "",
                "exclusion_reason": "",
            }
        )
    return queue


def _reference_by_match(
    rows: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    reference: dict[str, dict[str, Any]] = {}
    for row in rows:
        match_id = str(row.get("cricsheet_match_id", row.get("match_id", ""))).strip()
        if not match_id:
            raise ValueError("Eligible start-time reference contains a missing match ID")
        if match_id in reference:
            raise ValueError(f"Duplicate eligible start-time reference ID: {match_id}")
        reference[match_id] = row
    return reference


def _valid_local_utc_pair(
    local_start: datetime,
    zone: ZoneInfo,
    utc_start: datetime,
) -> bool:
    candidates: set[datetime] = set()
    for fold in (0, 1):
        zoned = local_start.replace(tzinfo=zone, fold=fold)
        candidate = zoned.astimezone(timezone.utc)
        round_trip = candidate.astimezone(zone).replace(tzinfo=None)
        if round_trip == local_start:
            candidates.add(candidate)
    return utc_start.astimezone(timezone.utc) in candidates


def validate_match_start_rows(
    rows: Iterable[dict[str, Any]],
    *,
    eligible_rows: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Return structural, cohort-identity, and timezone validation issues."""

    materialized = list(rows)
    reference = _reference_by_match(eligible_rows or []) if eligible_rows is not None else None
    issues: list[dict[str, str]] = []
    seen: set[str] = set()

    def issue(match_id: str, field: str, message: str) -> None:
        issues.append({"cricsheet_match_id": match_id, "field": field, "message": message})

    for row in materialized:
        match_id = str(row.get("cricsheet_match_id", "")).strip()
        if not match_id:
            issue("", "cricsheet_match_id", "missing match ID")
            continue
        if match_id in seen:
            issue(match_id, "cricsheet_match_id", "duplicate match ID")
        seen.add(match_id)

        expected = reference.get(match_id) if reference is not None else None
        if reference is not None and expected is None:
            issue(match_id, "cricsheet_match_id", "match is outside the eligible cohort")
        elif expected is not None:
            for field in (
                "match_date",
                "event_name",
                "competition_type",
                "venue",
                "city",
                "team_1",
                "team_2",
            ):
                if str(row.get(field, "")).strip() != str(expected.get(field, "")).strip():
                    issue(match_id, field, "does not match the outcome-blind cohort reference")

        status = str(row.get("start_time_status", "")).strip()
        if status not in START_TIME_STATUSES:
            issue(match_id, "start_time_status", f"unsupported value: {status}")
            continue
        if status in {"unavailable", "rejected"}:
            if not str(row.get("exclusion_reason", "")).strip():
                issue(match_id, "exclusion_reason", f"required when status is {status}")
            continue
        if status == "pending":
            continue

        source_url = str(row.get("source_url", "")).strip()
        parsed_url = urlparse(source_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            issue(match_id, "source_url", "verified start time requires an HTTP(S) source")
        for field in ("source_title", "timezone_name", "verifier_id"):
            if not str(row.get(field, "")).strip():
                issue(match_id, field, "required for a verified start time")

        accessed_at = _parse_datetime(row.get("accessed_at_utc"))
        if accessed_at is None or accessed_at.tzinfo is None:
            issue(match_id, "accessed_at_utc", "must be an offset-aware ISO-8601 timestamp")
        elif accessed_at.utcoffset() != timezone.utc.utcoffset(accessed_at):
            issue(match_id, "accessed_at_utc", "must use UTC offset +00:00 or Z")

        local_start = _parse_datetime(row.get("scheduled_start_local"))
        if local_start is None or local_start.tzinfo is not None:
            issue(
                match_id,
                "scheduled_start_local",
                "must be an offset-naive ISO-8601 local datetime",
            )
            local_start = None
        elif local_start.date().isoformat() != str(row.get("match_date", "")).strip():
            issue(match_id, "scheduled_start_local", "local date must equal match_date")

        utc_start = _parse_datetime(row.get("scheduled_start_utc"))
        if utc_start is None or utc_start.tzinfo is None:
            issue(
                match_id,
                "scheduled_start_utc",
                "must be an offset-aware ISO-8601 timestamp",
            )
            utc_start = None
        elif utc_start.utcoffset() != timezone.utc.utcoffset(utc_start):
            issue(match_id, "scheduled_start_utc", "must use UTC offset +00:00 or Z")

        timezone_name = str(row.get("timezone_name", "")).strip()
        zone = None
        if timezone_name:
            try:
                zone = ZoneInfo(timezone_name)
            except ZoneInfoNotFoundError:
                issue(match_id, "timezone_name", "unknown IANA timezone")
        if local_start is not None and utc_start is not None and zone is not None:
            if not _valid_local_utc_pair(local_start, zone, utc_start):
                issue(
                    match_id,
                    "scheduled_start_utc",
                    "does not equal the local start converted with timezone_name",
                )

    if reference is not None:
        for missing_id in sorted(reference.keys() - seen):
            issue(
                missing_id, "cricsheet_match_id", "eligible match is missing from start-time file"
            )
    return issues


def verified_match_start_map(rows: Iterable[dict[str, Any]]) -> dict[str, str]:
    """Return only explicitly verified start timestamps keyed by Cricsheet match ID."""

    verified: dict[str, str] = {}
    for row in rows:
        if str(row.get("start_time_status", "")).strip() != "verified":
            continue
        match_id = str(row.get("cricsheet_match_id", "")).strip()
        if not match_id:
            raise ValueError("Verified start-time row is missing cricsheet_match_id")
        if match_id in verified:
            raise ValueError(f"Duplicate verified match start: {match_id}")
        verified[match_id] = str(row.get("scheduled_start_utc", "")).strip()
    return verified


def match_start_coverage_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Summarize verification status without outcomes or pitch-report content."""

    materialized = list(rows)
    statuses = Counter(str(row.get("start_time_status", "")).strip() for row in materialized)
    verified = statuses["verified"]
    return {
        "rows": len(materialized),
        "verified_start_times": verified,
        "coverage_pct": round(100 * verified / len(materialized), 6) if materialized else 0.0,
        "status_counts": dict(sorted(statuses.items())),
    }
