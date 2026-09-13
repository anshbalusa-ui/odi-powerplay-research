"""Assemble leakage-safe team-innings model tables and chronological splits."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .pitch import merge_pitch_conditions
from .venue import VENUE_CONDITION_FIELDS


FORBIDDEN_PREDICTORS = {
    "batting_team_won",
    "winner",
    "match_status",
    "result_method",
    "exclusion_reasons",
    "source_search_query",
    "source_url",
    "source_title",
    "published_at_utc",
    "accessed_at_utc",
    "scheduled_start_local",
    "timezone_name",
    "scheduled_start_utc",
    "match_start_utc",
    "start_time_status",
    "verifier_id",
    "verification_note",
    "short_paraphrased_note",
}


def merge_strength_into_innings(
    innings_rows: Iterable[dict[str, Any]],
    strength_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Map match-level strength to each batting team's perspective."""

    strength_by_match: dict[str, dict[str, Any]] = {}
    for strength in strength_rows:
        match_id = str(strength["match_id"])
        if match_id in strength_by_match:
            raise ValueError(f"Duplicate strength row for match {match_id}")
        strength_by_match[match_id] = strength

    merged: list[dict[str, Any]] = []
    seen_match_ids: set[str] = set()
    for innings in innings_rows:
        match_id = str(innings["match_id"])
        strength = strength_by_match.get(match_id)
        if strength is None:
            raise ValueError(f"Missing strength row for match {match_id}")
        if str(innings["match_date"]) != str(strength["match_date"]):
            raise ValueError(f"Strength date mismatch for match {match_id}")

        batting_team = str(innings["batting_team"])
        opponent = str(innings["opponent"])
        team_1 = str(strength["team_1"])
        team_2 = str(strength["team_2"])
        if {batting_team, opponent} != {team_1, team_2}:
            raise ValueError(f"Strength team mismatch for match {match_id}")

        is_team_1 = batting_team == team_1
        team_prefix = "team_1" if is_team_1 else "team_2"
        opponent_prefix = "team_2" if is_team_1 else "team_1"
        output = dict(innings)
        output.update(
            {
                "team_elo_pre": strength[f"{team_prefix}_elo_pre"],
                "opponent_elo_pre": strength[f"{opponent_prefix}_elo_pre"],
                "elo_difference": (
                    float(strength["elo_difference_team_1"])
                    if is_team_1
                    else -float(strength["elo_difference_team_1"])
                ),
                "team_prior_matches": strength[f"{team_prefix}_prior_matches"],
                "opponent_prior_matches": strength[f"{opponent_prefix}_prior_matches"],
                "team_prior20_win_rate": strength[f"{team_prefix}_prior20_win_rate"],
                "opponent_prior20_win_rate": strength[f"{opponent_prefix}_prior20_win_rate"],
            }
        )
        merged.append(output)
        seen_match_ids.add(match_id)

    unused = set(strength_by_match) - seen_match_ids
    if unused:
        raise ValueError(f"Strength table has {len(unused)} rows outside the innings cohort")
    return merged


def merge_venue_conditions_into_innings(
    innings_rows: Iterable[dict[str, Any]],
    venue_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Join pre-match venue history while copying only its predictor allowlist."""

    venue_by_match: dict[str, dict[str, Any]] = {}
    for venue_row in venue_rows:
        match_id = str(venue_row["match_id"])
        if match_id in venue_by_match:
            raise ValueError(f"Duplicate venue-condition row for match {match_id}")
        venue_by_match[match_id] = venue_row

    merged: list[dict[str, Any]] = []
    seen_match_ids: set[str] = set()
    for innings in innings_rows:
        match_id = str(innings["match_id"])
        venue_row = venue_by_match.get(match_id)
        if venue_row is None:
            raise ValueError(f"Missing venue-condition row for match {match_id}")
        if str(innings["match_date"]) != str(venue_row["match_date"]):
            raise ValueError(f"Venue-condition date mismatch for match {match_id}")
        if str(innings.get("venue", "")).strip() != str(venue_row.get("venue", "")).strip():
            raise ValueError(f"Venue-condition venue mismatch for match {match_id}")

        output = dict(innings)
        output.update({field: venue_row[field] for field in VENUE_CONDITION_FIELDS})
        merged.append(output)
        seen_match_ids.add(match_id)

    unused = set(venue_by_match) - seen_match_ids
    if unused:
        raise ValueError(f"Venue-condition table has {len(unused)} rows outside the innings cohort")
    return merged


def assign_split(match_date: Any) -> str:
    """Assign the prespecified development, validation, or locked-test period."""

    date = str(match_date)
    if date <= "2023-12-31":
        return "development"
    if date <= "2024-12-31":
        return "validation"
    return "locked_test"


def add_chronological_splits(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach split labels and reject any match spanning multiple periods."""

    output: list[dict[str, Any]] = []
    splits_by_match: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        split = assign_split(row["match_date"])
        enriched = {**row, "split": split}
        output.append(enriched)
        splits_by_match[str(row["match_id"])].add(split)

    crossed = [match_id for match_id, splits in splits_by_match.items() if len(splits) != 1]
    if crossed:
        raise ValueError(f"{len(crossed)} matches cross chronological splits")
    return output


def validate_feature_allowlist(
    rows: Iterable[dict[str, Any]],
    feature_names: Iterable[str],
) -> None:
    """Reject forbidden or unavailable predictor names before modeling."""

    features = list(feature_names)
    forbidden = sorted(set(features) & FORBIDDEN_PREDICTORS)
    if forbidden:
        raise ValueError(f"Forbidden predictors: {', '.join(forbidden)}")
    materialized = list(rows)
    if not materialized:
        raise ValueError("Cannot validate predictors against an empty model table")
    missing = sorted(set(features) - set(materialized[0]))
    if missing:
        raise ValueError(f"Predictors missing from model table: {', '.join(missing)}")


def build_model_table(
    innings_rows: Iterable[dict[str, Any]],
    strength_rows: Iterable[dict[str, Any]],
    venue_rows: Iterable[dict[str, Any]],
    *,
    pitch_rows: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build the full team-innings table; verified pitch codes remain optional."""

    with_strength = merge_strength_into_innings(innings_rows, strength_rows)
    with_venue = merge_venue_conditions_into_innings(with_strength, venue_rows)
    with_pitch = merge_pitch_conditions(with_venue, pitch_rows or [])
    return add_chronological_splits(with_pitch)
