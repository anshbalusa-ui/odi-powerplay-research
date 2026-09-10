"""Leakage-safe pre-match team-strength features."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def _expected_score(rating: float, opponent_rating: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((opponent_rating - rating) / 400.0))


def add_pre_match_elo(
    rows: Iterable[dict[str, Any]],
    *,
    history_rows: Iterable[dict[str, Any]] | None = None,
    initial_rating: float = 1500.0,
    k_factor: float = 20.0,
) -> list[dict[str, Any]]:
    """Add leakage-safe pre-match Elo ratings to target team-innings rows.

    ``history_rows`` may contain additional decided ODIs that are not eligible
    for the powerplay analysis (for example a DLS match). Those matches can
    update team strength without being returned as analysis rows. If omitted,
    the target rows themselves are used as the rating history.

    All matches sharing a calendar date are rated from the same start-of-day
    snapshot, so an unknown within-day match ordering cannot leak one result
    into another.
    """

    targets = [dict(row) for row in rows]
    history = [dict(row) for row in (history_rows if history_rows is not None else targets)]

    matches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in history:
        matches[str(row["match_id"])].append(row)

    matches_by_date: dict[str, list[tuple[str, list[dict[str, Any]]]]] = defaultdict(list)
    for match_id, match_rows in matches.items():
        dates = {str(row["match_date"]) for row in match_rows}
        if len(dates) != 1:
            raise ValueError(f"Match {match_id} has inconsistent dates: {sorted(dates)}")
        matches_by_date[next(iter(dates))].append((match_id, match_rows))

    ratings: dict[str, float] = defaultdict(lambda: float(initial_rating))
    pre_match: dict[tuple[str, str], tuple[float, float]] = {}

    for match_date in sorted(matches_by_date):
        dated_matches = sorted(matches_by_date[match_date], key=lambda item: item[0])
        date_start_ratings = dict(ratings)
        deltas: dict[str, float] = defaultdict(float)

        def pre_rating(team: str) -> float:
            return float(date_start_ratings.get(team, initial_rating))

        for match_id, match_rows in dated_matches:
            first_row = sorted(match_rows, key=lambda item: int(item["innings_number"]))[0]
            team_a = str(first_row["batting_team"])
            team_b = str(first_row["opponent"])
            winner = str(first_row.get("winner") or "")
            if winner not in {team_a, team_b}:
                continue

            rating_a = pre_rating(team_a)
            rating_b = pre_rating(team_b)
            pre_match[(match_id, team_a)] = (rating_a, rating_b)
            pre_match[(match_id, team_b)] = (rating_b, rating_a)

            score_a = 1.0 if winner == team_a else 0.0
            expected_a = _expected_score(rating_a, rating_b)
            delta_a = k_factor * (score_a - expected_a)
            deltas[team_a] += delta_a
            deltas[team_b] -= delta_a

        for team, delta in deltas.items():
            ratings[team] = pre_rating(team) + delta

    for row in targets:
        key = (str(row["match_id"]), str(row["batting_team"]))
        ratings_for_row = pre_match.get(key)
        if ratings_for_row is None:
            raise ValueError(f"No decided Elo-history match found for target row {key}")
        team_rating, opponent_rating = ratings_for_row
        row["team_elo_pre"] = round(team_rating, 6)
        row["opponent_elo_pre"] = round(opponent_rating, 6)
        row["elo_difference"] = round(team_rating - opponent_rating, 6)

    return targets
