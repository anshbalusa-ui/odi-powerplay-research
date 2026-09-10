"""Validate extracted powerplay metrics and match-level invariants."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


PERCENTAGE_TOLERANCE = 0.000001


def _integer(row: dict[str, Any], field: str) -> int:
    return int(str(row[field]).strip())


def _number(row: dict[str, Any], field: str) -> float:
    return float(str(row[field]).strip())


def audit_powerplay_rows(
    rows: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return a reproducible summary and row-level metric/invariant issues."""

    materialized = list(rows)
    issues: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def record(row: dict[str, Any], field: str, expected: Any, actual: Any) -> None:
        issues.append(
            {
                "match_id": row.get("match_id"),
                "innings_number": row.get("innings_number"),
                "field": field,
                "expected": expected,
                "actual": actual,
            }
        )

    for row in materialized:
        grouped[str(row["match_id"])].append(row)
        try:
            runs = _integer(row, "pp_runs")
            wickets = _integer(row, "pp_wickets")
            legal_balls = _integer(row, "pp_legal_balls")
            delivery_events = _integer(row, "pp_delivery_events")
            boundary_balls = _integer(row, "pp_boundary_balls")
            dot_balls = _integer(row, "pp_dot_balls")
            balls_per_over = _integer(row, "balls_per_over")
        except (KeyError, TypeError, ValueError) as error:
            record(row, "numeric_fields", "parseable integers", str(error))
            continue

        if runs < 0:
            record(row, "pp_runs", ">= 0", runs)
        if not 0 <= wickets <= 10:
            record(row, "pp_wickets", "0..10", wickets)
        if legal_balls <= 0:
            record(row, "pp_legal_balls", "> 0", legal_balls)
            continue
        if delivery_events < legal_balls:
            record(row, "pp_delivery_events", f">= {legal_balls}", delivery_events)
        if not 0 <= boundary_balls <= legal_balls:
            record(row, "pp_boundary_balls", f"0..{legal_balls}", boundary_balls)
        if not 0 <= dot_balls <= legal_balls:
            record(row, "pp_dot_balls", f"0..{legal_balls}", dot_balls)
        if boundary_balls + dot_balls > legal_balls:
            record(row, "boundary_plus_dot_balls", f"<= {legal_balls}", boundary_balls + dot_balls)
        if runs < 4 * boundary_balls:
            record(row, "pp_runs", f">= {4 * boundary_balls}", runs)

        expected_run_rate = round(runs * balls_per_over / legal_balls, 6)
        expected_boundary_pct = round(100 * boundary_balls / legal_balls, 6)
        expected_dot_pct = round(100 * dot_balls / legal_balls, 6)
        for field, expected in (
            ("pp_run_rate", expected_run_rate),
            ("pp_boundary_pct", expected_boundary_pct),
            ("pp_dot_ball_pct", expected_dot_pct),
        ):
            try:
                actual = _number(row, field)
            except (KeyError, TypeError, ValueError) as error:
                record(row, field, expected, str(error))
                continue
            if abs(actual - expected) > PERCENTAGE_TOLERANCE:
                record(row, field, expected, actual)

        expected_complete = int(legal_balls >= 10 * balls_per_over)
        try:
            actual_complete = _integer(row, "pp_complete")
        except (KeyError, TypeError, ValueError) as error:
            record(row, "pp_complete", expected_complete, str(error))
        else:
            if actual_complete != expected_complete:
                record(row, "pp_complete", expected_complete, actual_complete)

    for match_id, match_rows in grouped.items():
        first = match_rows[0]
        if len(match_rows) != 2:
            record(first, "match_row_count", 2, len(match_rows))
            continue
        innings_numbers = {_integer(row, "innings_number") for row in match_rows}
        if innings_numbers != {1, 2}:
            record(first, "innings_numbers", [1, 2], sorted(innings_numbers))
        outcomes = {_integer(row, "batting_team_won") for row in match_rows}
        if outcomes != {0, 1}:
            record(first, "batting_team_won", [0, 1], sorted(outcomes))

    issue_counts = Counter(str(issue["field"]) for issue in issues)
    summary = {
        "rows_checked": len(materialized),
        "matches_checked": len(grouped),
        "issue_count": len(issues),
        "issues_by_field": dict(sorted(issue_counts.items())),
    }
    return summary, issues
