"""Leakage-safe pre-match Elo and rolling-win-rate features."""

from __future__ import annotations

import csv
from collections import defaultdict, deque
from itertools import groupby
from pathlib import Path
from typing import Any, Iterable


def innings_rows_to_matches(rows: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Collapse two primary-cohort innings rows into one chronological match row."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["match_id"])].append(dict(row))

    matches: list[dict[str, str]] = []
    for match_id, match_rows in grouped.items():
        ordered = sorted(match_rows, key=lambda row: int(row["innings_number"]))
        if len(ordered) != 2 or [int(row["innings_number"]) for row in ordered] != [1, 2]:
            raise ValueError(f"Match {match_id} does not contain exactly innings 1 and 2")
        first, second = ordered
        if str(first["batting_team"]) != str(second["opponent"]) or str(
            first["opponent"]
        ) != str(second["batting_team"]):
            raise ValueError(f"Match {match_id} has inconsistent team identities")
        if str(first["winner"]) != str(second["winner"]):
            raise ValueError(f"Match {match_id} has inconsistent winner values")
        matches.append(
            {
                "match_id": match_id,
                "match_date": str(first["match_date"]),
                "team_1": str(first["batting_team"]),
                "team_2": str(first["opponent"]),
                "winner": str(first["winner"]),
            }
        )

    return sorted(matches, key=lambda row: (row["match_date"], row["match_id"]))


def _expected_score(rating: float, opponent_rating: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((opponent_rating - rating) / 400.0))


def _rolling_summary(history: deque[int]) -> tuple[int, float | None]:
    count = len(history)
    return count, (sum(history) / count if count else None)


def calculate_prematch_strength(
    matches: Iterable[dict[str, Any]],
    *,
    initial_rating: float = 1500.0,
    k_factor: float = 20.0,
    rolling_window: int = 20,
) -> list[dict[str, Any]]:
    """Return one pre-match strength row per match without same-day leakage."""

    if rolling_window < 1:
        raise ValueError("rolling_window must be at least 1")

    materialized = [dict(row) for row in matches]
    match_ids = [str(row["match_id"]) for row in materialized]
    if len(match_ids) != len(set(match_ids)):
        raise ValueError("Duplicate match_id values are not allowed")

    ordered = sorted(materialized, key=lambda row: (str(row["match_date"]), str(row["match_id"])))
    ratings: dict[str, float] = defaultdict(lambda: float(initial_rating))
    histories: dict[str, deque[int]] = defaultdict(lambda: deque(maxlen=rolling_window))
    output: list[dict[str, Any]] = []

    for match_date, same_day_iter in groupby(ordered, key=lambda row: str(row["match_date"])):
        same_day = list(same_day_iter)
        rating_deltas: dict[str, float] = defaultdict(float)
        results_to_append: list[tuple[str, int, str]] = []

        for match_row in same_day:
            team_1 = str(match_row["team_1"])
            team_2 = str(match_row["team_2"])
            winner = str(match_row["winner"])
            if team_1 == team_2:
                raise ValueError(f"Match {match_row['match_id']} has the same team twice")
            if winner not in {team_1, team_2}:
                raise ValueError(f"Match {match_row['match_id']} has an invalid winner")

            team_1_rating = ratings[team_1]
            team_2_rating = ratings[team_2]
            team_1_count, team_1_win_rate = _rolling_summary(histories[team_1])
            team_2_count, team_2_win_rate = _rolling_summary(histories[team_2])
            score_1 = float(winner == team_1)
            score_2 = 1.0 - score_1
            expected_1 = _expected_score(team_1_rating, team_2_rating)
            expected_2 = 1.0 - expected_1

            output.append(
                {
                    "match_id": str(match_row["match_id"]),
                    "match_date": match_date,
                    "team_1": team_1,
                    "team_2": team_2,
                    "team_1_elo_pre": round(team_1_rating, 6),
                    "team_2_elo_pre": round(team_2_rating, 6),
                    "elo_difference_team_1": round(team_1_rating - team_2_rating, 6),
                    "team_1_prior_matches": team_1_count,
                    "team_2_prior_matches": team_2_count,
                    "team_1_rolling_win_rate": (
                        round(team_1_win_rate, 6) if team_1_win_rate is not None else None
                    ),
                    "team_2_rolling_win_rate": (
                        round(team_2_win_rate, 6) if team_2_win_rate is not None else None
                    ),
                }
            )

            rating_deltas[team_1] += k_factor * (score_1 - expected_1)
            rating_deltas[team_2] += k_factor * (score_2 - expected_2)
            results_to_append.append((team_1, int(score_1), str(match_row["match_id"])))
            results_to_append.append((team_2, int(score_2), str(match_row["match_id"])))

        for team, delta in rating_deltas.items():
            ratings[team] += delta
        for team, result, _match_id in sorted(results_to_append, key=lambda item: (item[2], item[0])):
            histories[team].append(result)

    return output


def write_strength_csv(rows: Iterable[dict[str, Any]], output_path: str | Path) -> None:
    """Write pre-match strength rows using their stable key order."""

    materialized = list(rows)
    if not materialized:
        raise ValueError("No strength rows to write")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(materialized[0]))
        writer.writeheader()
        writer.writerows(materialized)
