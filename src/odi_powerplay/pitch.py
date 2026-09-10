"""Validation and outcome-blind selection for pre-match pitch reports."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from typing import Any, Iterable


PITCH_CATEGORIES = {
    "batting_friendly",
    "balanced",
    "pace_seam",
    "spin",
    "slow_two_paced",
    "unknown",
}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
BOUNCE_PROFILES = {"low", "standard", "steep", "variable"}
ORDINAL_FIELDS = ("batting_ease", "pace_seam_support", "spin_support")
BINARY_FIELDS = ("two_paced_expected", "dew_expected")


def _issue(
    match_id: str,
    issue_code: str,
    detail: str,
    *,
    severity: str = "error",
) -> dict[str, str]:
    return {
        "cricsheet_match_id": match_id,
        "severity": severity,
        "issue_code": issue_code,
        "detail": detail,
    }


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_nullable_integer(
    row: dict[str, Any],
    field: str,
    allowed: set[int],
    issues: list[dict[str, str]],
    match_id: str,
) -> int | None:
    raw = row.get(field)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        value = int(str(raw))
    except ValueError:
        value = -999
    if value not in allowed:
        issues.append(
            _issue(match_id, f"INVALID_{field.upper()}", f"{field}={raw!r}")
        )
        return None
    return value


def validate_pitch_rows(
    rows: Iterable[dict[str, Any]],
    match_index: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Return normalized usable pitch rows and field-level validation issues."""

    materialized = [dict(row) for row in rows]
    duplicate_ids = {
        match_id
        for match_id, count in Counter(
            str(row.get("cricsheet_match_id", "")).strip() for row in materialized
        ).items()
        if match_id and count > 1
    }
    usable: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []

    for row in materialized:
        match_id = str(row.get("cricsheet_match_id", "")).strip()
        row_issues: list[dict[str, str]] = []
        if not match_id:
            issues.append(_issue("", "MISSING_MATCH_ID", "cricsheet_match_id is blank"))
            continue
        if match_id in duplicate_ids:
            issues.append(_issue(match_id, "DUPLICATE_MATCH_ID", "pitch match ID is repeated"))
            continue

        match = match_index.get(match_id)
        if match is None:
            issues.append(_issue(match_id, "UNMATCHED_MATCH_ID", "ID is absent from cohort"))
            continue
        if str(row.get("match_date", "")) != str(match.get("match_date", "")):
            row_issues.append(
                _issue(match_id, "MATCH_DATE_MISMATCH", "pitch and cohort dates differ")
            )
        if str(row.get("venue", "")).strip() != str(match.get("venue", "")).strip():
            row_issues.append(
                _issue(match_id, "VENUE_MISMATCH", "pitch and cohort venues differ")
            )

        pre_match_verified = _parse_nullable_integer(
            row,
            "pre_match_verified",
            {0, 1},
            row_issues,
            match_id,
        )
        normalized = dict(row)
        normalized["pre_match_verified"] = pre_match_verified
        for field in ORDINAL_FIELDS:
            normalized[field] = _parse_nullable_integer(
                row, field, {0, 1, 2}, row_issues, match_id
            )
        for field in BINARY_FIELDS:
            normalized[field] = _parse_nullable_integer(
                row, field, {0, 1}, row_issues, match_id
            )

        category = str(row.get("pitch_primary_category", "")).strip()
        confidence = str(row.get("coder_confidence", "")).strip()
        bounce = str(row.get("bounce_profile", "")).strip()
        exclusion_reason = str(row.get("exclusion_reason", "")).strip()
        if category and category not in PITCH_CATEGORIES:
            row_issues.append(
                _issue(match_id, "INVALID_PITCH_PRIMARY_CATEGORY", f"category={category!r}")
            )
        if confidence and confidence not in CONFIDENCE_LEVELS:
            row_issues.append(
                _issue(match_id, "INVALID_CODER_CONFIDENCE", f"confidence={confidence!r}")
            )
        if bounce and bounce not in BOUNCE_PROFILES:
            row_issues.append(
                _issue(match_id, "INVALID_BOUNCE_PROFILE", f"bounce_profile={bounce!r}")
            )

        is_usable_candidate = (
            pre_match_verified == 1 and not exclusion_reason and category != "unknown"
        )
        if pre_match_verified == 0 and not exclusion_reason:
            row_issues.append(
                _issue(match_id, "UNVERIFIED_WITHOUT_EXCLUSION", "exclusion_reason is blank")
            )
        if pre_match_verified == 1 and not exclusion_reason and category == "unknown":
            row_issues.append(
                _issue(match_id, "UNKNOWN_WITHOUT_EXCLUSION", "usable row needs a pitch category")
            )

        if is_usable_candidate:
            required_fields = (
                "source_url",
                "source_title",
                "published_at_utc",
                "accessed_at_utc",
                "coder_id",
                "coder_confidence",
                "short_paraphrased_note",
            )
            for field in required_fields:
                if not str(row.get(field, "")).strip():
                    row_issues.append(
                        _issue(match_id, f"MISSING_{field.upper()}", f"{field} is required")
                    )

        published_text = str(row.get("published_at_utc", "")).strip()
        if published_text:
            try:
                published_date = date.fromisoformat(published_text[:10])
                match_date = date.fromisoformat(str(match["match_date"])[:10])
                if published_date > match_date:
                    row_issues.append(
                        _issue(match_id, "SOURCE_NOT_PRE_MATCH", "publication date follows match date")
                    )
                match_start_text = str(match.get("match_start_utc", "")).strip()
                if "T" in published_text and match_start_text:
                    if _parse_datetime(published_text) >= _parse_datetime(match_start_text):
                        row_issues.append(
                            _issue(
                                match_id,
                                "SOURCE_NOT_PRE_MATCH",
                                "publication timestamp is at or after match start",
                            )
                        )
                elif published_date == match_date:
                    row_issues.append(
                        _issue(
                            match_id,
                            "SOURCE_TIME_UNRESOLVED",
                            "same-date source lacks an independently comparable timestamp",
                            severity="warning",
                        )
                    )
            except ValueError:
                row_issues.append(
                    _issue(match_id, "INVALID_PUBLISHED_AT", f"published_at_utc={published_text!r}")
                )

        issues.extend(row_issues)
        if is_usable_candidate and not any(
            issue["severity"] == "error" for issue in row_issues
        ):
            usable.append(normalized)

    return usable, issues


def _selection_rank(seed: int, row: dict[str, Any]) -> tuple[str, str]:
    match_id = str(row["match_id"])
    digest = hashlib.sha256(f"{seed}:{match_id}".encode("utf-8")).hexdigest()
    return str(row["match_date"]), digest


def select_next_pitch_batch(
    matches: Iterable[dict[str, Any]],
    *,
    audited_ids: set[str],
    quotas: dict[str, int],
    seed: int,
) -> list[dict[str, str]]:
    """Select evenly spaced unaudited matches using pre-outcome metadata only."""

    allowed_output_fields = (
        "match_id",
        "match_date",
        "venue",
        "competition_type",
        "event_name",
        "team_1",
        "team_2",
    )
    unique_matches: dict[str, dict[str, str]] = {}
    for raw in matches:
        match_id = str(raw["match_id"])
        if match_id in audited_ids or match_id in unique_matches:
            continue
        projected = {
            "match_id": match_id,
            "match_date": str(raw["match_date"]),
            "venue": str(raw.get("venue", "")),
            "competition_type": str(raw["competition_type"]),
            "event_name": str(raw.get("event_name", "")),
            "team_1": str(raw.get("team_1", raw.get("batting_team", ""))),
            "team_2": str(raw.get("team_2", raw.get("opponent", ""))),
        }
        unique_matches[match_id] = projected

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in unique_matches.values():
        grouped[row["competition_type"]].append(row)

    selected: list[dict[str, str]] = []
    for competition_type, quota in quotas.items():
        if quota < 0:
            raise ValueError("Pitch batch quotas cannot be negative")
        candidates = sorted(grouped.get(competition_type, []), key=lambda row: _selection_rank(seed, row))
        take = min(quota, len(candidates))
        if take == 0:
            continue
        positions = [min(len(candidates) - 1, int((index + 0.5) * len(candidates) / take)) for index in range(take)]
        selected.extend(candidates[position] for position in positions)

    return [{field: row[field] for field in allowed_output_fields} for row in selected]
