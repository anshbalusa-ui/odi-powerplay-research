"""Extract leakage-safe first-10-over features from Cricsheet JSON.

The output unit is a team innings. Outcome labels are retained for supervised
learning, but no match information produced after the first ten overs is used as
a predictor here.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


NOT_A_TEAM_WICKET = {"retired hurt"}


def _is_legal_delivery(delivery: dict[str, Any]) -> bool:
    extras = delivery.get("extras", {})
    return "wides" not in extras and "noballs" not in extras


def _is_boundary(delivery: dict[str, Any]) -> bool:
    runs = delivery.get("runs", {})
    return runs.get("batter") in {4, 6} and not bool(runs.get("non_boundary", False))


def _wickets_lost(delivery: dict[str, Any]) -> int:
    return sum(
        1
        for wicket in delivery.get("wickets", [])
        if str(wicket.get("kind", "")).strip().lower() not in NOT_A_TEAM_WICKET
    )


def _winner(info: dict[str, Any]) -> str | None:
    return info.get("outcome", {}).get("winner")


def _method(info: dict[str, Any]) -> str | None:
    method = info.get("outcome", {}).get("method")
    return str(method) if method is not None else None


def _status(info: dict[str, Any]) -> str:
    outcome = info.get("outcome", {})
    if outcome.get("winner"):
        return "decided"
    result = str(outcome.get("result", "unknown")).strip().lower()
    if result in {"tie", "no result"}:
        return result.replace(" ", "_")
    return "unknown"


def _opponent(teams: list[str], batting_team: str) -> str | None:
    return next((team for team in teams if team != batting_team), None)


def _match_date(info: dict[str, Any]) -> str | None:
    dates = info.get("dates", [])
    return str(dates[0]) if dates else None


def _event_name(info: dict[str, Any]) -> str | None:
    event = info.get("event") or {}
    return event.get("name")


def _row_for_innings(
    *,
    match_id: str,
    info: dict[str, Any],
    innings: dict[str, Any],
    innings_number: int,
) -> dict[str, Any]:
    batting_team = str(innings["team"])
    teams = [str(team) for team in info.get("teams", [])]
    balls_per_over = int(info.get("balls_per_over", 6))

    runs = 0
    legal_balls = 0
    delivery_events = 0
    boundary_balls = 0
    dot_balls = 0
    wickets = 0

    for over in innings.get("overs", []):
        over_index = int(over["over"])
        if over_index < 0 or over_index > 9:
            continue
        for delivery in over.get("deliveries", []):
            delivery_events += 1
            runs += int(delivery.get("runs", {}).get("total", 0))
            wickets += _wickets_lost(delivery)
            legal = _is_legal_delivery(delivery)
            if legal:
                legal_balls += 1
                if int(delivery.get("runs", {}).get("total", 0)) == 0:
                    dot_balls += 1
                if _is_boundary(delivery):
                    boundary_balls += 1

    scheduled_balls = 10 * balls_per_over
    winner = _winner(info)
    toss = info.get("toss", {})
    match_status = _status(info)
    batting_team_won = None if match_status != "decided" else int(winner == batting_team)

    return {
        "match_id": match_id,
        "match_date": _match_date(info),
        "year": int(_match_date(info)[:4]) if _match_date(info) else None,
        "event_name": _event_name(info),
        "gender": info.get("gender"),
        "match_type": info.get("match_type"),
        "venue": info.get("venue"),
        "city": info.get("city"),
        "batting_team": batting_team,
        "opponent": _opponent(teams, batting_team),
        "innings_number": innings_number,
        "batting_first": int(innings_number == 1),
        "chasing": int(innings_number == 2),
        "toss_winner": toss.get("winner"),
        "toss_decision": toss.get("decision"),
        "batting_team_won_toss": int(toss.get("winner") == batting_team),
        "match_status": match_status,
        "result_method": _method(info),
        "winner": winner,
        "batting_team_won": batting_team_won,
        "pp_runs": runs,
        "pp_wickets": wickets,
        "pp_legal_balls": legal_balls,
        "pp_delivery_events": delivery_events,
        "pp_run_rate": round(runs * balls_per_over / legal_balls, 6) if legal_balls else None,
        "pp_boundary_balls": boundary_balls,
        "pp_boundary_pct": round(100 * boundary_balls / legal_balls, 6)
        if legal_balls
        else None,
        "pp_dot_balls": dot_balls,
        "pp_dot_ball_pct": round(100 * dot_balls / legal_balls, 6) if legal_balls else None,
        "pp_complete": int(legal_balls >= scheduled_balls),
        "balls_per_over": balls_per_over,
        "is_super_over": int(bool(innings.get("super_over", False))),
    }


def extract_match(path: str | Path) -> list[dict[str, Any]]:
    """Return one record for each regulation innings in one Cricsheet JSON file."""

    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        match = json.load(handle)

    info = match.get("info", {})
    if info.get("match_type") != "ODI":
        return []

    rows: list[dict[str, Any]] = []
    regulation_number = 0
    for innings in match.get("innings", []):
        if innings.get("super_over", False):
            continue
        regulation_number += 1
        rows.append(
            _row_for_innings(
                match_id=source.stem,
                info=info,
                innings=innings,
                innings_number=regulation_number,
            )
        )
    return rows


def extract_directory(input_dir: str | Path) -> list[dict[str, Any]]:
    """Extract every JSON file below *input_dir* in stable path order."""

    root = Path(input_dir)
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        rows.extend(extract_match(path))
    return rows


def write_csv(rows: Iterable[dict[str, Any]], output_path: str | Path) -> None:
    """Write extracted rows using a stable column order."""

    materialized = list(rows)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not materialized:
        raise ValueError("No ODI innings were extracted; output was not written")
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(materialized[0]))
        writer.writeheader()
        writer.writerows(materialized)

