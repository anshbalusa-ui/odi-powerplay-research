"""Build deterministic hand audits and compare processed rows with raw JSON."""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .extract_cricsheet import extract_match


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

AUDIT_FIELDS = (
    "match_date",
    "year",
    "event_name",
    "venue",
    "city",
    "batting_team",
    "opponent",
    "innings_number",
    "batting_first",
    "chasing",
    "toss_winner",
    "toss_decision",
    "batting_team_won_toss",
    "match_status",
    "result_method",
    "winner",
    "batting_team_won",
    "pp_runs",
    "pp_wickets",
    "pp_legal_balls",
    "pp_delivery_events",
    "pp_run_rate",
    "pp_boundary_balls",
    "pp_boundary_pct",
    "pp_dot_balls",
    "pp_dot_ball_pct",
    "pp_complete",
    "balls_per_over",
)

NUMERIC_AUDIT_FIELDS = {
    "year",
    "innings_number",
    "batting_first",
    "chasing",
    "batting_team_won_toss",
    "batting_team_won",
    "pp_runs",
    "pp_wickets",
    "pp_legal_balls",
    "pp_delivery_events",
    "pp_run_rate",
    "pp_boundary_balls",
    "pp_boundary_pct",
    "pp_dot_balls",
    "pp_dot_ball_pct",
    "pp_complete",
    "balls_per_over",
}


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
        if len(match_rows) == 2 and {int(row["innings_number"]) for row in match_rows} == {1, 2}
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


def _stable_year_rank(seed: int, year: int, match_id: str) -> str:
    value = f"{seed}:{year}:{match_id}".encode()
    return hashlib.sha256(value).hexdigest()


def select_audit_match_ids(
    rows: Iterable[dict[str, Any]],
    *,
    n: int,
    seed: int,
) -> list[str]:
    """Select unique matches in deterministic round-robin order across years."""

    if n < 1:
        raise ValueError("n must be at least 1")

    by_year: dict[int, set[str]] = defaultdict(set)
    for row in rows:
        by_year[int(row["year"])].add(str(row["match_id"]))

    available = sum(len(match_ids) for match_ids in by_year.values())
    if n > available:
        raise ValueError(f"Requested {n} matches but only {available} are available")

    ranked = {
        year: sorted(
            match_ids,
            key=lambda match_id: _stable_year_rank(seed, year, match_id),
        )
        for year, match_ids in by_year.items()
    }
    selected: list[str] = []
    offset = 0
    years = sorted(ranked)
    while len(selected) < n:
        for year in years:
            if offset < len(ranked[year]):
                selected.append(ranked[year][offset])
                if len(selected) == n:
                    break
        offset += 1
    return selected


def _normalized_audit_value(value: Any, field: str) -> Any:
    if value is None or str(value).strip() == "":
        return None
    if field in NUMERIC_AUDIT_FIELDS:
        return float(value)
    return str(value).strip()


def _audit_values_match(processed: Any, reextracted: Any, field: str) -> bool:
    left = _normalized_audit_value(processed, field)
    right = _normalized_audit_value(reextracted, field)
    if field in NUMERIC_AUDIT_FIELDS and left is not None and right is not None:
        return abs(left - right) <= 1e-6
    return left == right


def audit_raw_against_processed(
    raw_dir: str | Path,
    processed_rows: Iterable[dict[str, Any]],
    match_ids: Iterable[str],
) -> list[dict[str, Any]]:
    """Re-extract selected matches and compare every declared field by innings."""

    raw_root = Path(raw_dir)
    processed_index = {
        (str(row["match_id"]), int(row["innings_number"])): row for row in processed_rows
    }
    audit_rows: list[dict[str, Any]] = []

    for match_id in match_ids:
        path = raw_root / f"{match_id}.json"
        if not path.exists():
            candidates = list(raw_root.rglob(f"{match_id}.json"))
            if len(candidates) != 1:
                raise FileNotFoundError(
                    f"Expected one raw JSON file for match {match_id}; " f"found {len(candidates)}"
                )
            path = candidates[0]

        reextracted_rows = extract_match(path)
        reextracted_index = {
            (str(row["match_id"]), int(row["innings_number"])): row for row in reextracted_rows
        }
        innings_numbers = sorted(
            {
                innings_number
                for indexed_match_id, innings_number in (
                    set(processed_index) | set(reextracted_index)
                )
                if indexed_match_id == str(match_id)
            }
        )
        for innings_number in innings_numbers:
            key = (str(match_id), innings_number)
            processed = processed_index.get(key, {})
            reextracted = reextracted_index.get(key, {})
            for field in AUDIT_FIELDS:
                processed_value = processed.get(field)
                reextracted_value = reextracted.get(field)
                audit_rows.append(
                    {
                        "match_id": str(match_id),
                        "innings_number": innings_number,
                        "field": field,
                        "processed_value": processed_value,
                        "reextracted_value": reextracted_value,
                        "matches": int(
                            _audit_values_match(
                                processed_value,
                                reextracted_value,
                                field,
                            )
                        ),
                    }
                )

    return audit_rows


def write_audit_csv(rows: Iterable[dict[str, Any]], output_path: str | Path) -> None:
    """Write a stable field-level extraction audit CSV."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    materialized = list(rows)
    fieldnames = (
        "match_id",
        "innings_number",
        "field",
        "processed_value",
        "reextracted_value",
        "matches",
    )
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(materialized)
