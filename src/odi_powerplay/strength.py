"""Leakage-safe pre-match team-strength features."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def _expected_score(rating: float, opponent_rating: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((opponent_rating - rating) / 400.0))


def add_pre_match_elo(
    rows: Iterable[dict[str, Any]],
    *,
    initial_rating: float = 1500.0,
    k_factor: float = 20.0,
) -> list[dict[str, Any]]:
    """Add pre-match Elo features while batching all updates on the same date.

    The input may contain two team-innings rows per match. Ratings are attached
    from the perspective of each row's batting team. Each match updates ratings
    exactly once, and no result from a date can affect another match on that
    same date.
    """

    materialized = [dict(row) for row in rows]
    indexed = list(enumerate(materialized))
    matches: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, row in indexed:
        matches[str(row["match_id"])].append((index, row))

    matches_by_date: dict[str, list[tuple[str, list[tuple[int, dict[str, Any]]]]]] = defaultdict(list)
    for match_id, match_rows in matches.items():
        dates = {str(row["match_date"]) for _, row in match_rows}
        if len(dates) != 1:
            raise ValueError(f"Match {match_id} has inconsistent dates: {sorted(dates)}")
        matches_by_date[next(iter(dates))].append((match_id, match_rows))

    ratings: dict[str, float] = defaultdict(lambda: float(initial_rating))

    for match_date in sorted(matches_by_date):
        dated_matches = sorted(matches_by_date[match_date], key=lambda item: item[0])
        date_start_ratings = dict(ratings)
        deltas: dict[str, float] = defaultdict(float)

        def pre_rating(team: str) -> float:
            return float(date_start_ratings.get(team, initial_rating))

        for match_id, match_rows in dated_matches:
            first_row = sorted(match_rows, key=lambda item: int(item[1]["innings_number"]))[0][1]
            team_a = str(first_row["batting_team"])
            team_b = str(first_row["opponent"])
            winner = str(first_row.get("winner") or "")
            if winner not in {team_a, team_b}:
                raise ValueError(f"Match {match_id} does not have a decided two-team winner")

            rating_a = pre_rating(team_a)
            rating_b = pre_rating(team_b)

            for _, row in match_rows:
                team = str(row["batting_team"])
                opponent = str(row["opponent"])
                row["team_elo_pre"] = round(pre_rating(team), 6)
                row["opponent_elo_pre"] = round(pre_rating(opponent), 6)
                row["elo_difference"] = round(pre_rating(team) - pre_rating(opponent), 6)

            score_a = 1.0 if winner == team_a else 0.0
            expected_a = _expected_score(rating_a, rating_b)
            delta_a = k_factor * (score_a - expected_a)
            deltas[team_a] += delta_a
            deltas[team_b] -= delta_a

        for team, delta in deltas.items():
            ratings[team] = pre_rating(team) + delta

    return materialized
