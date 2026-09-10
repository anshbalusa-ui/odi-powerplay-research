from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.venue import (
    calculate_prematch_venue_conditions,
    venue_match_rows_from_innings,
)


class VenueConditionTests(unittest.TestCase):
    def match(
        self,
        match_id: str,
        match_date: str,
        *,
        runs: int,
        wickets: int,
        boundaries: int,
        dots: int,
    ) -> dict[str, object]:
        return {
            "match_id": match_id,
            "match_date": match_date,
            "venue": "Fixture Ground",
            "venue_key": "fixture ground",
            "innings_count": 2,
            "pp_runs_total": runs,
            "pp_wickets_total": wickets,
            "pp_legal_balls_total": 120,
            "pp_boundary_balls_total": boundaries,
            "pp_dot_balls_total": dots,
        }

    def test_collapses_innings_to_validated_venue_totals(self) -> None:
        shared = {
            "match_id": "m1",
            "match_date": "2020-01-01",
            "venue": "Fixture Ground",
            "pp_legal_balls": "60",
        }
        rows = [
            {
                **shared,
                "innings_number": "1",
                "pp_runs": "48",
                "pp_wickets": "2",
                "pp_boundary_balls": "5",
                "pp_dot_balls": "39",
            },
            {
                **shared,
                "innings_number": "2",
                "pp_runs": "52",
                "pp_wickets": "1",
                "pp_boundary_balls": "7",
                "pp_dot_balls": "35",
            },
        ]

        matches = venue_match_rows_from_innings(rows)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["pp_runs_total"], 100)
        self.assertEqual(matches[0]["pp_wickets_total"], 3)
        self.assertEqual(matches[0]["pp_boundary_balls_total"], 12)
        self.assertEqual(matches[0]["pp_dot_balls_total"], 74)

    def test_same_date_matches_share_only_prior_date_history(self) -> None:
        matches = [
            self.match("a", "2020-01-01", runs=100, wickets=2, boundaries=10, dots=60),
            self.match("b", "2020-01-01", runs=200, wickets=4, boundaries=20, dots=100),
            self.match("c", "2020-01-02", runs=120, wickets=3, boundaries=12, dots=70),
        ]

        output = calculate_prematch_venue_conditions(matches)
        by_id = {row["match_id"]: row for row in output}

        self.assertEqual(by_id["a"]["venue_prior_matches"], 0)
        self.assertEqual(by_id["b"]["venue_prior_matches"], 0)
        self.assertEqual(by_id["c"]["venue_prior_matches"], 2)
        self.assertEqual(by_id["c"]["venue_prior_pp_runs_mean"], 75.0)
        self.assertEqual(by_id["c"]["venue_prior_pp_wickets_mean"], 1.5)
        self.assertEqual(by_id["c"]["venue_prior_boundary_pct"], 12.5)
        self.assertEqual(by_id["c"]["venue_prior_dot_ball_pct"], 66.666667)

    def test_venue_history_is_input_order_and_future_independent(self) -> None:
        earlier = [
            self.match("a", "2020-01-01", runs=100, wickets=2, boundaries=10, dots=60),
            self.match("b", "2020-01-02", runs=120, wickets=3, boundaries=12, dots=70),
        ]
        with_future = [
            *earlier,
            self.match("future", "2021-01-01", runs=240, wickets=8, boundaries=30, dots=40),
        ]

        expected = calculate_prematch_venue_conditions(earlier)
        reversed_with_future = calculate_prematch_venue_conditions(reversed(with_future))

        actual = [row for row in reversed_with_future if row["match_id"] != "future"]
        self.assertEqual(actual, expected)

    def test_rolling_window_and_exact_venue_are_respected(self) -> None:
        first = self.match("a", "2020-01-01", runs=100, wickets=2, boundaries=10, dots=60)
        second = self.match("b", "2020-01-02", runs=120, wickets=3, boundaries=12, dots=70)
        target = self.match("c", "2020-01-03", runs=140, wickets=4, boundaries=14, dots=80)
        other_venue = self.match("d", "2020-01-03", runs=90, wickets=1, boundaries=8, dots=75)
        other_venue.update({"venue": "Other Ground", "venue_key": "other ground"})

        output = calculate_prematch_venue_conditions(
            [first, second, target, other_venue],
            rolling_window=1,
        )
        by_id = {row["match_id"]: row for row in output}

        self.assertEqual(by_id["c"]["venue_prior_matches"], 1)
        self.assertEqual(by_id["c"]["venue_prior_pp_runs_mean"], 60.0)
        self.assertEqual(by_id["d"]["venue_prior_matches"], 0)


if __name__ == "__main__":
    unittest.main()
