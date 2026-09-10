"""Build a deterministic, year-stratified hand-audit sample."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Iterable


EXTRACTED_AUDIT_FIELDS = (
    "pp_runs",
    "pp_wickets",
    "pp_legal_balls",
    "pp_boundary_balls",
    "pp_boundary_pct",
    "pp_dot_balls",
    "pp_dot_ball_pct",
    "toss_winner",
    "toss_decision",
    "batting_team_won",
)


def _stable_rank(seed: str, match_id: str) -> str:
    return hashlib.sha256(f"{seed}|{match_id}".encode()).hexdigest()


def select_hand_audit_rows(
    rows: Iterable[dict[str, Any]],
    *,
    minimum_innings: int = 20,
    seed: str = "odi-powerplay-gate-2-v1",
) -> list[dict[str, Any]]:
    """Select full match pairs across years without inspecting outcomes or metrics."""

    if minimum_innings < 2:
        raise ValueError("minimum_innings must be at least 2")

    matches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        matches[str(row["match_id"])].append(row)

    eligible = {
        match_id: sorted(match_rows, key=lambda row: int(row["innings_number"]))
        for match_id, match_rows in matches.items()
        if len(match_rows) == 2
        and {int(row["innings_number"]) for row in match_rows} == {1, 2}
    }
    by_year: dict[int, list[str]] = defaultdict(list)
    for match_id, match_rows in eligible.items():
        by_year[int(match_rows[0]["year"])].append(match_id)

    selected: list[str] = []
    for year in sorted(by_year):
        selected.append(min(by_year[year], key=lambda match_id: _stable_rank(seed, match_id)))

    remaining = sorted(
        (match_id for match_id in eligible if match_id not in selected),
        key=lambda match_id: _stable_rank(seed, match_id),
    )
    while len(selected) * 2 < minimum_innings and remaining:
        selected.append(remaining.pop(0))

    if len(selected) * 2 < minimum_innings:
        raise ValueError("Not enough complete matches to build the requested audit sample")

    sampled = [row for match_id in selected for row in eligible[match_id]]
    return sorted(
        sampled,
        key=lambda row: (int(row["year"]), str(row["match_id"]), int(row["innings_number"])),
    )


def build_hand_audit_template(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return auditable rows with extracted values and blank independent checks."""

    output: list[dict[str, Any]] = []
    for row in rows:
        audit_row: dict[str, Any] = {
            "match_id": row["match_id"],
            "source_json": f"data/raw/cricsheet/{row['match_id']}.json",
            "match_date": row["match_date"],
            "year": row["year"],
            "event_name": row["event_name"],
            "venue": row["venue"],
            "batting_team": row["batting_team"],
            "opponent": row["opponent"],
            "innings_number": row["innings_number"],
        }
        for field in EXTRACTED_AUDIT_FIELDS:
            audit_row[f"extracted_{field}"] = row[field]
            audit_row[f"audited_{field}"] = ""
        audit_row.update(
            {
                "scorecard_url": "",
                "auditor_id": "",
                "audit_date": "",
                "discrepancy_found": "",
                "discrepancy_note": "",
            }
        )
        output.append(audit_row)
    return output
