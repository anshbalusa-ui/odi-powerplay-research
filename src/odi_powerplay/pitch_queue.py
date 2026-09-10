"""Build outcome-blind queues for pre-match pitch-source collection."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def _search_query(team_1: str, team_2: str, match_date: str, venue: str) -> str:
    return (
        f'ESPNcricinfo {team_1} vs {team_2} {match_date} ODI preview '
        f'pitch conditions {venue}'
    )


def build_pitch_queue(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one outcome-blind pitch-collection row per match.

    Results and powerplay values are intentionally omitted so source discovery
    and coding can be completed without seeing the eventual match outcome.
    """

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["match_id"])].append(dict(row))

    queue: list[dict[str, Any]] = []
    for match_id, match_rows in grouped.items():
        ordered = sorted(match_rows, key=lambda item: int(item.get("innings_number", 99)))
        first = ordered[0]
        team_1 = str(first.get("batting_team") or "")
        team_2 = str(first.get("opponent") or "")
        match_date = str(first.get("match_date") or "")
        venue = str(first.get("venue") or "")
        queue.append(
            {
                "cricsheet_match_id": match_id,
                "match_date": match_date,
                "year": first.get("year"),
                "venue": venue,
                "city": first.get("city"),
                "team_1": team_1,
                "team_2": team_2,
                "event_name": first.get("event_name"),
                "competition_type": first.get("competition_type"),
                "search_query": _search_query(team_1, team_2, match_date, venue),
                "collection_status": "unsearched",
            }
        )

    return sorted(queue, key=lambda item: (str(item["match_date"]), str(item["cricsheet_match_id"])))
