"""Create, validate, and merge source-audited pre-match pitch conditions."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Iterable
from urllib.parse import urlparse


PITCH_FIELDS = (
    "pitch_primary_category",
    "batting_ease",
    "pace_seam_support",
    "spin_support",
    "bounce_profile",
    "two_paced_expected",
    "dew_expected",
)
ALLOWED_VALUES = {
    "pitch_primary_category": {
        "batting_friendly",
        "balanced",
        "pace_seam",
        "spin",
        "slow_two_paced",
        "unknown",
    },
    "batting_ease": {"", "0", "1", "2"},
    "pace_seam_support": {"", "0", "1", "2"},
    "spin_support": {"", "0", "1", "2"},
    "bounce_profile": {"", "low", "standard", "steep", "variable"},
    "two_paced_expected": {"", "0", "1"},
    "dew_expected": {"", "0", "1"},
    "coder_confidence": {"high", "medium", "low"},
}


def build_pitch_collection_queue(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one outcome-blind source-collection row per eligible match."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["match_id"])].append(row)

    queue: list[dict[str, Any]] = []
    for match_id in sorted(grouped, key=lambda value: (grouped[value][0]["match_date"], value)):
        match_rows = sorted(grouped[match_id], key=lambda row: int(row["innings_number"]))
        if len(match_rows) != 2:
            raise ValueError(f"Match {match_id} does not have exactly two innings rows")
        first = match_rows[0]
        team_1 = str(first["batting_team"])
        team_2 = str(first["opponent"])
        search_query = (
            f'site:espncricinfo.com "{team_1}" "{team_2}" '
            f'"{first["match_date"]}" preview pitch conditions'
        )
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
                "source_search_query": search_query,
                "source_url": "",
                "source_title": "",
                "published_at_utc": "",
                "accessed_at_utc": "",
                "pre_match_verified": "",
                "coder_id": "",
                "coder_confidence": "",
                "pitch_primary_category": "",
                "batting_ease": "",
                "pace_seam_support": "",
                "spin_support": "",
                "bounce_profile": "",
                "two_paced_expected": "",
                "dew_expected": "",
                "short_paraphrased_note": "",
                "exclusion_reason": "",
            }
        )
    return queue


def _parse_timestamp(value: Any) -> datetime | None:
    normalized = str(value or "").strip().replace("Z", "+00:00")
    if not normalized:
        return None
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def validate_pitch_rows(
    rows: Iterable[dict[str, Any]],
    *,
    eligible_match_ids: set[str] | None = None,
    match_start_by_id: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    """Return validation issues; only verified pre-match rows may enter a model table."""

    issues: list[dict[str, str]] = []
    seen: set[str] = set()

    def issue(match_id: str, field: str, message: str) -> None:
        issues.append({"cricsheet_match_id": match_id, "field": field, "message": message})

    for row in rows:
        match_id = str(row.get("cricsheet_match_id", "")).strip()
        if not match_id:
            issue("", "cricsheet_match_id", "missing match ID")
            continue
        if match_id in seen:
            issue(match_id, "cricsheet_match_id", "duplicate match ID")
        seen.add(match_id)
        if eligible_match_ids is not None and match_id not in eligible_match_ids:
            issue(match_id, "cricsheet_match_id", "match is outside the eligible primary cohort")

        verified = str(row.get("pre_match_verified", "")).strip()
        if verified not in {"0", "1"}:
            issue(match_id, "pre_match_verified", "must be 0 or 1")
            continue
        if verified == "0":
            if not str(row.get("exclusion_reason", "")).strip():
                issue(match_id, "exclusion_reason", "required when source is not verified")
            continue

        source_url = str(row.get("source_url", "")).strip()
        parsed_url = urlparse(source_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            issue(match_id, "source_url", "verified rows require an HTTP(S) source URL")
        for field in ("source_title", "coder_id", "coder_confidence", "pitch_primary_category"):
            if not str(row.get(field, "")).strip():
                issue(match_id, field, "required for verified rows")

        published_at = _parse_timestamp(row.get("published_at_utc"))
        accessed_at = _parse_timestamp(row.get("accessed_at_utc"))
        if published_at is None:
            issue(match_id, "published_at_utc", "must be an ISO-8601 timestamp")
        if accessed_at is None:
            issue(match_id, "accessed_at_utc", "must be an ISO-8601 timestamp")
        if published_at and accessed_at and published_at > accessed_at:
            issue(match_id, "published_at_utc", "cannot be after access time")

        if match_start_by_id is not None:
            match_start = _parse_timestamp(match_start_by_id.get(match_id))
            if match_start is None:
                issue(match_id, "match_start_utc", "verified timing requires a match start timestamp")
            elif published_at and published_at >= match_start:
                issue(match_id, "published_at_utc", "source was not published before match start")

        for field, allowed in ALLOWED_VALUES.items():
            value = str(row.get(field, "")).strip()
            if field in {"coder_confidence", "pitch_primary_category"} and not value:
                continue
            if value not in allowed:
                issue(match_id, field, f"unsupported value: {value}")

        note = str(row.get("short_paraphrased_note", "")).strip()
        if not note:
            issue(match_id, "short_paraphrased_note", "verified rows require a short paraphrase")
        elif len(note) > 300:
            issue(match_id, "short_paraphrased_note", "must not exceed 300 characters")

    return issues


def pitch_coverage_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Summarize verified coverage without using match outcomes."""

    materialized = list(rows)
    verified = [row for row in materialized if str(row.get("pre_match_verified", "")) == "1"]
    by_year = Counter(str(row.get("match_date", ""))[:4] for row in verified)
    by_category = Counter(str(row.get("pitch_primary_category", "")) for row in verified)
    return {
        "queued_matches": len(materialized),
        "verified_pitch_matches": len(verified),
        "coverage_pct": round(100 * len(verified) / len(materialized), 6) if materialized else 0.0,
        "verified_by_year": dict(sorted(by_year.items())),
        "verified_by_primary_category": dict(sorted(by_category.items())),
    }


def merge_pitch_conditions(
    innings_rows: Iterable[dict[str, Any]],
    pitch_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Left-join verified pitch codes to innings without source prose or outcomes."""

    pitch_by_match = {
        str(row["cricsheet_match_id"]): row
        for row in pitch_rows
        if str(row.get("pre_match_verified", "")) == "1"
    }
    merged: list[dict[str, Any]] = []
    for innings in innings_rows:
        output = dict(innings)
        pitch = pitch_by_match.get(str(innings["match_id"]))
        output["pitch_available"] = int(pitch is not None)
        for field in PITCH_FIELDS:
            output[field] = pitch.get(field, "") if pitch else ""
        merged.append(output)
    return merged
