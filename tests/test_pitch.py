from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import (
    build_pitch_collection_queue,
    espn_link_candidate,
    espn_linkage_summary,
    merge_pitch_conditions,
    pitch_intercoder_reliability,
    pitch_coverage_summary,
    select_next_pitch_batch,
    validate_espn_linkage_rows,
    validate_pitch_rows,
)


class PitchPipelineTests(unittest.TestCase):
    def innings_rows(self) -> list[dict[str, object]]:
        shared = {
            "match_id": "match-1",
            "match_date": "2026-01-02",
            "year": 2026,
            "event_name": "Fixture ODI Series",
            "competition_type": "bilateral_series",
            "venue": "Fixture Ground",
            "city": "Fixture City",
            "pp_runs": 50,
            "winner": "Team A",
        }
        return [
            {
                **shared,
                "innings_number": 1,
                "batting_team": "Team A",
                "opponent": "Team B",
            },
            {
                **shared,
                "innings_number": 2,
                "batting_team": "Team B",
                "opponent": "Team A",
            },
        ]

    def verified_pitch_row(self) -> dict[str, str]:
        return {
            "cricsheet_match_id": "match-1",
            "match_date": "2026-01-02",
            "source_url": "https://example.com/pre-match-report",
            "source_title": "Pre-match conditions",
            "published_at_utc": "2026-01-01T10:00:00+00:00",
            "accessed_at_utc": "2026-01-01T12:00:00+00:00",
            "pre_match_verified": "1",
            "coder_id": "coder-1",
            "coder_confidence": "high",
            "pitch_primary_category": "pace_seam",
            "batting_ease": "1",
            "pace_seam_support": "2",
            "spin_support": "0",
            "bounce_profile": "steep",
            "two_paced_expected": "0",
            "dew_expected": "",
            "short_paraphrased_note": "Expected grass, carry, and early seam movement.",
            "exclusion_reason": "",
        }

    def test_collection_queue_excludes_outcomes_and_powerplay_metrics(self) -> None:
        queue = build_pitch_collection_queue(self.innings_rows())
        self.assertEqual(len(queue), 1)
        self.assertNotIn("pp_runs", queue[0])
        self.assertNotIn("winner", queue[0])
        self.assertIn("preview pitch conditions", queue[0]["source_search_query"])

    def test_espn_link_candidates_are_unfetched_and_explicitly_unverified(self) -> None:
        candidate = espn_link_candidate("1000887")
        self.assertEqual(candidate["espn_match_id_candidate"], "1000887")
        self.assertEqual(candidate["espn_linkage_status"], "unverified_candidate")
        self.assertEqual(
            candidate["espn_legacy_match_url_candidate"],
            "https://www.espncricinfo.com/ci/engine/match/1000887.html",
        )
        unavailable = espn_link_candidate("local/match")
        self.assertEqual(unavailable["espn_linkage_status"], "not_available")
        self.assertEqual(unavailable["espn_legacy_match_url_candidate"], "")

    def test_espn_linkage_manifest_validates_candidates_without_network(self) -> None:
        row = {
            "cricsheet_match_id": "1000887",
            **espn_link_candidate("1000887"),
        }
        self.assertEqual(validate_espn_linkage_rows([row]), [])
        summary = espn_linkage_summary([row])
        self.assertEqual(summary["candidate_rows"], 1)
        self.assertEqual(summary["human_verified_rows"], 0)
        self.assertEqual(summary["network_requests_performed"], 0)

        tampered = {
            **row,
            "espn_legacy_match_url_candidate": "https://example.com/wrong",
        }
        self.assertEqual(
            {issue["field"] for issue in validate_espn_linkage_rows([tampered])},
            {"espn_legacy_match_url_candidate"},
        )

    def test_batch_selection_is_balanced_deterministic_and_outcome_blind(self) -> None:
        class GuardedRow(dict):
            def get(self, key, default=None):
                if key in {"winner", "pp_runs", "batting_team_won"}:
                    raise AssertionError(f"Outcome-bearing field was read: {key}")
                return super().get(key, default)

        queue = [
            GuardedRow(
                cricsheet_match_id=f"match-{year}-{competition}-{index}",
                match_date=f"{year}-01-01",
                competition_type=competition,
                winner="must-not-be-read",
                pp_runs=99,
            )
            for year, competition in (
                (2020, "bilateral_series"),
                (2020, "world_cup"),
                (2021, "bilateral_series"),
                (2021, "world_cup"),
            )
            for index in range(2)
        ]
        first = select_next_pitch_batch(
            queue,
            completed_match_ids={"match-2020-world_cup-0"},
            n=5,
            seed=7,
        )
        second = select_next_pitch_batch(
            queue,
            completed_match_ids={"match-2020-world_cup-0"},
            n=5,
            seed=7,
        )
        self.assertEqual(first, second)
        self.assertNotIn("match-2020-world_cup-0", {row["cricsheet_match_id"] for row in first})
        self.assertEqual({row["match_date"][:4] for row in first}, {"2020", "2021"})
        self.assertEqual(
            {row["competition_type"] for row in first},
            {"bilateral_series", "world_cup"},
        )
        self.assertEqual([row["batch_sequence"] for row in first], [1, 2, 3, 4, 5])
        self.assertTrue(
            all(
                forbidden not in row
                for row in first
                for forbidden in ("winner", "pp_runs", "batting_team_won")
            )
        )

    def test_verified_source_must_precede_match_start(self) -> None:
        row = self.verified_pitch_row()
        valid = validate_pitch_rows(
            [row],
            eligible_match_ids={"match-1"},
            match_start_by_id={"match-1": "2026-01-02T10:00:00+00:00"},
        )
        self.assertEqual(valid, [])

        row["published_at_utc"] = "2026-01-02T11:00:00+00:00"
        issues = validate_pitch_rows(
            [row],
            eligible_match_ids={"match-1"},
            match_start_by_id={"match-1": "2026-01-02T10:00:00+00:00"},
        )
        self.assertIn(
            "source was not published before match start", {issue["message"] for issue in issues}
        )

    def test_espn_sources_require_human_verified_match_linkage(self) -> None:
        row = self.verified_pitch_row()
        row["source_url"] = "https://www.espncricinfo.com/example-match-preview"

        unverified = validate_pitch_rows(
            [row],
            eligible_match_ids={"match-1"},
            match_start_by_id={"match-1": "2026-01-02T10:00:00+00:00"},
        )
        self.assertIn(
            "espn_linkage_status",
            {issue["field"] for issue in unverified},
        )

        row.update(
            {
                "espn_linkage_status": "verified_match",
                "espn_match_id_verified": "1234567",
                "espn_match_url_verified": (
                    "https://www.espncricinfo.com/series/example-1/"
                    "team-a-vs-team-b-1234567/full-scorecard"
                ),
            }
        )
        self.assertEqual(
            validate_pitch_rows(
                [row],
                eligible_match_ids={"match-1"},
                match_start_by_id={"match-1": "2026-01-02T10:00:00+00:00"},
            ),
            [],
        )

    def test_only_verified_pitch_codes_enter_the_model_table(self) -> None:
        verified = self.verified_pitch_row()
        merged = merge_pitch_conditions(self.innings_rows(), [verified])
        self.assertEqual({row["pitch_available"] for row in merged}, {1})
        self.assertEqual({row["pitch_primary_category"] for row in merged}, {"pace_seam"})
        self.assertNotIn("short_paraphrased_note", merged[0])

        verified["pre_match_verified"] = "0"
        missing = merge_pitch_conditions(self.innings_rows(), [verified])
        self.assertEqual({row["pitch_available"] for row in missing}, {0})

    def test_coverage_summary_uses_only_verified_rows(self) -> None:
        verified = self.verified_pitch_row()
        excluded = {**verified, "cricsheet_match_id": "match-2", "pre_match_verified": "0"}
        summary = pitch_coverage_summary([verified, excluded])
        self.assertEqual(summary["verified_pitch_matches"], 1)
        self.assertEqual(summary["coverage_pct"], 50.0)

    def test_intercoder_reliability_reports_agreement_kappa_and_sample_target(
        self,
    ) -> None:
        def coding_set(
            coder_id: str,
            categories: list[str],
            batting_ease: list[str],
        ) -> list[dict[str, str]]:
            rows: list[dict[str, str]] = []
            for index, (category, ease) in enumerate(
                zip(categories, batting_ease, strict=True),
                start=1,
            ):
                row = self.verified_pitch_row()
                row.update(
                    {
                        "cricsheet_match_id": f"match-{index}",
                        "coder_id": coder_id,
                        "pitch_primary_category": category,
                        "batting_ease": ease,
                        "pace_seam_support": "",
                        "spin_support": "",
                        "bounce_profile": "",
                        "two_paced_expected": "",
                        "dew_expected": "",
                    }
                )
                rows.append(row)
            return rows

        reference = coding_set(
            "coder-a",
            ["batting_friendly", "batting_friendly", "spin", "spin"],
            ["2", "2", "1", "1"],
        )
        recoded = coding_set(
            "coder-b",
            ["batting_friendly", "spin", "spin", "spin"],
            ["2", "1", "1", "1"],
        )

        summary = pitch_intercoder_reliability(reference, recoded)

        self.assertEqual(summary["paired_verified_matches"], 4)
        self.assertEqual(summary["double_coded_pct"], 100.0)
        self.assertTrue(summary["meets_minimum_double_coding_target"])
        self.assertEqual(summary["overall_comparable_items"], 8)
        self.assertEqual(summary["overall_agreement_pct"], 75.0)
        primary = summary["fields"]["pitch_primary_category"]
        self.assertEqual(primary["agreement_pct"], 75.0)
        self.assertEqual(primary["cohen_kappa"], 0.5)
        self.assertEqual(summary["fields"]["dew_expected"]["comparable_pairs"], 0)
        self.assertIsNone(summary["fields"]["dew_expected"]["cohen_kappa"])

    def test_intercoder_reliability_requires_independent_coders(self) -> None:
        reference = self.verified_pitch_row()
        recoded = dict(reference)

        with self.assertRaisesRegex(ValueError, "not independently coded"):
            pitch_intercoder_reliability([reference], [recoded])


if __name__ == "__main__":
    unittest.main()
