"""Leakage-safe, date-batched pre-match team-strength features."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable


def match_rows_from_innings(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse clean team-innings pairs to one validated row per match."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["match_id"])].append(row)

    matches: list[dict[str, Any]] = []
    for match_id in sorted(grouped):
        match_rows = sorted(grouped[match_id], key=lambda row: int(row["innings_number"]))
        if len(match_rows) != 2 or {int(row["innings_number"]) for row in match_rows} != {1, 2}:
            raise ValueError(f"Match {match_id} must contain exactly innings 1 and 2")
        first, second = match_rows
        team_1 = str(first["batting_team"])
        team_2 = str(second["batting_team"])
        winner = str(first["winner"])
        if {team_1, team_2} != {str(first["batting_team"]), str(first["opponent"])}:
            raise ValueError(f"Match {match_id} has inconsistent team identifiers")
        if winner not in {team_1, team_2}:
            raise ValueError(f"Match {match_id} has an invalid winner")
        matches.append(
            {
                "match_id": match_id,
                "match_date": first["match_date"],
                "team_1": team_1,
                "team_2": team_2,
                "winner": winner,
            }
        )
    return sorted(matches, key=lambda row: (str(row["match_date"]), str(row["match_id"])))


def calculate_prematch_strength(
    matches: Iterable[dict[str, Any]],
    *,
    initial_rating: float = 1500.0,
    k_factor: float = 20.0,
    rolling_window: int = 20,
) -> list[dict[str, Any]]:
    """Calculate Elo and rolling win rates without same-date or future leakage."""

    if rolling_window < 1:
        raise ValueError("rolling_window must be positive")
    if k_factor <= 0:
        raise ValueError("k_factor must be positive")

    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    for match in matches:
        match_id = str(match["match_id"])
        if match_id in seen_ids:
            raise ValueError(f"Duplicate match ID: {match_id}")
        seen_ids.add(match_id)
        by_date[str(match["match_date"])].append(dict(match))

    ratings: dict[str, float] = defaultdict(lambda: initial_rating)
    histories: dict[str, deque[int]] = defaultdict(lambda: deque(maxlen=rolling_window))
    match_counts: dict[str, int] = defaultdict(int)
    output: list[dict[str, Any]] = []

    for match_date in sorted(by_date):
        date_matches = sorted(by_date[match_date], key=lambda row: str(row["match_id"]))
        rating_deltas: dict[str, float] = defaultdict(float)
        history_updates: dict[str, list[int]] = defaultdict(list)

        for match in date_matches:
            team_1 = str(match["team_1"])
            team_2 = str(match["team_2"])
            winner = str(match["winner"])
            if team_1 == team_2 or winner not in {team_1, team_2}:
                raise ValueError(f"Invalid teams or winner for match {match['match_id']}")

            team_1_rating = ratings[team_1]
            team_2_rating = ratings[team_2]
            team_1_history = histories[team_1]
            team_2_history = histories[team_2]
            team_1_score = float(winner == team_1)
            team_2_score = 1.0 - team_1_score
            expected_team_1 = 1.0 / (1.0 + 10 ** ((team_2_rating - team_1_rating) / 400.0))
            expected_team_2 = 1.0 - expected_team_1

            output.append(
                {
                    "match_id": str(match["match_id"]),
                    "match_date": match_date,
                    "team_1": team_1,
                    "team_2": team_2,
                    "team_1_elo_pre": round(team_1_rating, 6),
                    "team_2_elo_pre": round(team_2_rating, 6),
                    "elo_difference_team_1": round(team_1_rating - team_2_rating, 6),
                    "team_1_prior_matches": match_counts[team_1],
                    "team_2_prior_matches": match_counts[team_2],
                    "team_1_prior20_win_rate": (
                        round(sum(team_1_history) / len(team_1_history), 6)
                        if team_1_history
                        else None
                    ),
                    "team_2_prior20_win_rate": (
                        round(sum(team_2_history) / len(team_2_history), 6)
                        if team_2_history
                        else None
                    ),
                }
            )
            rating_deltas[team_1] += k_factor * (team_1_score - expected_team_1)
            rating_deltas[team_2] += k_factor * (team_2_score - expected_team_2)
            history_updates[team_1].append(int(team_1_score))
            history_updates[team_2].append(int(team_2_score))

        for team, delta in rating_deltas.items():
            ratings[team] += delta
        for team, results in history_updates.items():
            histories[team].extend(results)
            match_counts[team] += len(results)

    return output
