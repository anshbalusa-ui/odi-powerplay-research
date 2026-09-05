"""Create auditable clean cohorts from extracted team-innings rows."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


ESSENTIAL_MATCH_FIELDS = (
    "match_date",
    "venue",
    "batting_team",
    "opponent",
    "toss_winner",
    "toss_decision",
)


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def exclusion_reasons(rows: list[dict[str, Any]]) -> list[str]:
    """Return prespecified match-level exclusion codes for extracted rows."""

    reasons: list[str] = []
    first = rows[0] if rows else {}

    if len(rows) != 2:
        reasons.append("NOT_TWO_REGULATION_INNINGS")

    status = str(first.get("match_status", "unknown"))
    if status == "tie":
        reasons.append("TIE")
    elif status == "no_result":
        reasons.append("NO_RESULT")
    elif status != "decided":
        reasons.append("UNKNOWN_RESULT")

    if _present(first.get("result_method")):
        reasons.append("DLS_OR_REVISED_TARGET")

    if any(int(row.get("pp_complete", 0) or 0) != 1 for row in rows):
        reasons.append("INCOMPLETE_POWERPLAY")

    if any(not _present(row.get(field)) for row in rows for field in ESSENTIAL_MATCH_FIELDS):
        reasons.append("MISSING_MATCH_METADATA")

    outcomes = {row.get("batting_team_won") for row in rows}
    if status == "decided" and (len(rows) == 2 and outcomes != {0, 1}):
        reasons.append("INCONSISTENT_OUTCOME_LABELS")

    return reasons


def _normalize_kept_row(row: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(row)
    cleaned["city_missing"] = int(not _present(cleaned.get("city")))
    if cleaned["city_missing"]:
        cleaned["city"] = "Unknown"
    if not _present(cleaned.get("event_name")):
        cleaned["event_name"] = "Unknown"
    if not _present(cleaned.get("result_method")):
        cleaned["result_method"] = "none"
    cleaned["analysis_eligible_core"] = 1
    cleaned["exclusion_reasons"] = "none"
    return cleaned


def clean_rows(
    rows: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return clean innings rows, match audit rows, and excluded match rows."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["match_id"])].append(row)

    cleaned: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for match_id in sorted(grouped):
        match_rows = sorted(grouped[match_id], key=lambda row: int(row["innings_number"]))
        reasons = exclusion_reasons(match_rows)
        first = match_rows[0]
        audit_row = {
            "match_id": match_id,
            "match_date": first.get("match_date"),
            "year": first.get("year"),
            "event_name": first.get("event_name") or "Unknown",
            "gender": first.get("gender"),
            "venue": first.get("venue"),
            "team_1": first.get("batting_team"),
            "team_2": first.get("opponent"),
            "regulation_innings_count": len(match_rows),
            "match_status": first.get("match_status"),
            "result_method": first.get("result_method") or "none",
            "both_powerplays_complete": int(
                len(match_rows) == 2
                and all(int(row.get("pp_complete", 0) or 0) == 1 for row in match_rows)
            ),
            "city_missing": int(not _present(first.get("city"))),
            "analysis_eligible_core": int(not reasons),
            "exclusion_reasons": ";".join(reasons),
        }
        audit.append(audit_row)
        if reasons:
            excluded.append(audit_row)
        else:
            cleaned.extend(_normalize_kept_row(row) for row in match_rows)

    return cleaned, audit, excluded


def select_pilot(
    rows: Iterable[dict[str, Any]],
    *,
    years: set[int] | None = None,
    gender: str = "male",
    event_names: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Select the prespecified World Cup pilot from already-clean rows."""

    selected_years = years or {2015, 2019, 2023}
    selected_events = event_names or {"ICC Cricket World Cup", "World Cup"}
    return [
        dict(row)
        for row in rows
        if int(row["year"]) in selected_years
        and str(row["gender"]) == gender
        and str(row["event_name"]) in selected_events
    ]
