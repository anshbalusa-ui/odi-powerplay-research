"""Leakage-safe, date-batched historical venue-condition features."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable


VENUE_CONDITION_FIELDS = (
    "venue_history_available",
    "venue_prior_matches",
    "venue_prior_innings",
    "venue_prior_pp_runs_mean",
    "venue_prior_pp_wickets_mean",
    "venue_prior_boundary_pct",
    "venue_prior_dot_ball_pct",
)


def _venue_key(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def venue_match_rows_from_innings(
    rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collapse clean team-innings pairs to match-level venue scoring summaries."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["match_id"])].append(row)

    matches: list[dict[str, Any]] = []
    for match_id in sorted(grouped):
        match_rows = sorted(grouped[match_id], key=lambda row: int(row["innings_number"]))
        if len(match_rows) != 2 or {int(row["innings_number"]) for row in match_rows} != {1, 2}:
            raise ValueError(f"Match {match_id} must contain exactly innings 1 and 2")
        first, second = match_rows
        match_date = str(first["match_date"])
        venue = str(first.get("venue", "")).strip()
        if str(second["match_date"]) != match_date:
            raise ValueError(f"Match {match_id} has inconsistent dates")
        if str(second.get("venue", "")).strip() != venue:
            raise ValueError(f"Match {match_id} has inconsistent venues")

        legal_balls = sum(int(row["pp_legal_balls"]) for row in match_rows)
        boundary_balls = sum(int(row["pp_boundary_balls"]) for row in match_rows)
        dot_balls = sum(int(row["pp_dot_balls"]) for row in match_rows)
        if legal_balls <= 0 or boundary_balls > legal_balls or dot_balls > legal_balls:
            raise ValueError(f"Match {match_id} has invalid powerplay ball counts")
        matches.append(
            {
                "match_id": match_id,
                "match_date": match_date,
                "venue": venue,
                "venue_key": _venue_key(venue),
                "innings_count": 2,
                "pp_runs_total": sum(int(row["pp_runs"]) for row in match_rows),
                "pp_wickets_total": sum(int(row["pp_wickets"]) for row in match_rows),
                "pp_legal_balls_total": legal_balls,
                "pp_boundary_balls_total": boundary_balls,
                "pp_dot_balls_total": dot_balls,
            }
        )
    return sorted(matches, key=lambda row: (str(row["match_date"]), str(row["match_id"])))


def calculate_prematch_venue_conditions(
    matches: Iterable[dict[str, Any]],
    *,
    rolling_window: int = 20,
) -> list[dict[str, Any]]:
    """Calculate venue scoring history using only matches on earlier dates."""

    if rolling_window < 1:
        raise ValueError("rolling_window must be positive")

    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    for match in matches:
        match_id = str(match["match_id"])
        if match_id in seen_ids:
            raise ValueError(f"Duplicate match ID: {match_id}")
        seen_ids.add(match_id)
        by_date[str(match["match_date"])].append(dict(match))

    histories: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=rolling_window))
    output: list[dict[str, Any]] = []
    for match_date in sorted(by_date):
        date_matches = sorted(by_date[match_date], key=lambda row: str(row["match_id"]))
        for match in date_matches:
            venue_key = _venue_key(match.get("venue_key") or match.get("venue"))
            history = list(histories[venue_key]) if venue_key else []
            innings = sum(int(row["innings_count"]) for row in history)
            legal_balls = sum(int(row["pp_legal_balls_total"]) for row in history)
            output.append(
                {
                    "match_id": str(match["match_id"]),
                    "match_date": match_date,
                    "venue": str(match.get("venue", "")).strip(),
                    "venue_history_available": int(bool(history)),
                    "venue_prior_matches": len(history),
                    "venue_prior_innings": innings,
                    "venue_prior_pp_runs_mean": (
                        round(
                            sum(int(row["pp_runs_total"]) for row in history) / innings,
                            6,
                        )
                        if innings
                        else None
                    ),
                    "venue_prior_pp_wickets_mean": (
                        round(
                            sum(int(row["pp_wickets_total"]) for row in history) / innings,
                            6,
                        )
                        if innings
                        else None
                    ),
                    "venue_prior_boundary_pct": (
                        round(
                            100
                            * sum(int(row["pp_boundary_balls_total"]) for row in history)
                            / legal_balls,
                            6,
                        )
                        if legal_balls
                        else None
                    ),
                    "venue_prior_dot_ball_pct": (
                        round(
                            100
                            * sum(int(row["pp_dot_balls_total"]) for row in history)
                            / legal_balls,
                            6,
                        )
                        if legal_balls
                        else None
                    ),
                }
            )

        for match in date_matches:
            venue_key = _venue_key(match.get("venue_key") or match.get("venue"))
            if venue_key:
                histories[venue_key].append(match)

    return output
