"""Behavioral tests for the separate pre-match expectation measurement."""

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from odi_powerplay.pitch_expectation import (  # noqa: E402
    assessment_input,
    consensus,
    eligible_sources,
    validate_assessment,
)


class PitchExpectationTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "cricsheet_match_id": "123",
            "match_date": "2023-05-01",
            "event_name": "Series",
            "competition_type": "bilateral_series",
            "venue": "Oval",
            "city": "Town",
            "team_1": "Alpha",
            "team_2": "Beta",
            "source_url": "https://example.org/preview",
            "source_title": "Pre-match preview",
            "published_at_utc": "2023-04-30T20:00:00Z",
            "accessed_at_utc": "2026-09-27T10:00:00Z",
            "pre_match_verified": "1",
        }
        self.start = {"cricsheet_match_id": "123", "start_time_status": "verified",
                      "scheduled_start_utc": "2023-05-01T09:00:00Z"}
        self.answer = {
            "batting_expectation": "favorable", "pace_seam_expectation": "neutral",
            "spin_expectation": "low", "slow_two_paced_expectation": "unlikely",
            "overall_expected_environment": "batting_favorable", "confidence": 72,
            "evidence": "Preview anticipates high scoring on a true surface.",
            "reasoning_basis": ["explicit_playing_effect_statement"],
            "rationale": "The pre-match source forecasts good scoring.",
        }

    def test_forbidden_raw_report_fields_fail_closed(self):
        report = {**self.report, "batting_team_won": "1", "pp_runs": "42",
                  "pp_wickets": "2", "boundary_pct": "0.3", "dot_pct": "0.4",
                  "pitch_primary_category": "spin", "original_spin_support": "2",
                  "reaudited_spin_support": "1", "coder_confidence": "high",
                  "effect_evidence_note": "legacy", "short_paraphrased_note": "prior coder"}
        text = "Published preview expects runs"
        digest = hashlib.sha256(text.encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "forbidden"):
            assessment_input(report, self.start, text, digest)
        with self.assertRaises(ValueError):
            assessment_input(self.report, self.start, text, "sha256:wrong")

    def test_rejects_contaminated_or_unavailable_source_text(self):
        with self.assertRaises(ValueError):
            assessment_input(self.report, self.start, "Final score 300/4", "sha256:abc")
        with self.assertRaises(ValueError):
            assessment_input(self.report, self.start, "", "sha256:abc")
        with self.assertRaises(ValueError):
            assessment_input(self.report, self.start, "Preview", "")

    def test_eligible_source_does_not_include_unavailable_or_late_records(self):
        sources = eligible_sources([self.report], [self.start],
                                   [{"cricsheet_match_id": "123", "reaudit_status": "passed_revised"}])
        self.assertEqual(len(sources), 1)
        self.assertNotIn("reaudit_status", sources[0])
        excluded = eligible_sources([self.report], [self.start],
                                    [{"cricsheet_match_id": "123", "reaudit_status": "source_unavailable"}])
        self.assertEqual(excluded, [])
        with self.assertRaises(ValueError):
            eligible_sources([{**self.report, "published_at_utc": "2023-05-02T09:00:00Z"}],
                             [self.start], [{"cricsheet_match_id": "123", "reaudit_status": "passed_revised"}])

    def test_date_only_publication_must_be_pre_match_even_at_end_of_utc_day(self):
        date_only = {**self.report, "published_at_utc": "2023-04-30"}
        approved = [{"cricsheet_match_id": "123", "reaudit_status": "passed_revised"}]
        self.assertEqual(len(eligible_sources([date_only], [self.start], approved)), 1)
        ambiguous = {**date_only, "published_at_utc": "2023-05-01"}
        exclusions = []
        self.assertEqual(eligible_sources([ambiguous], [self.start], approved, exclusions), [])
        self.assertEqual(exclusions, ["123"])
        with self.assertRaises(ValueError):
            eligible_sources([ambiguous], [self.start], approved)
        fractional_start = {**self.start, "scheduled_start_utc": "2023-04-30T23:59:59.500000Z"}
        fractional_exclusions = []
        self.assertEqual(
            eligible_sources([date_only], [fractional_start], approved, fractional_exclusions), []
        )
        self.assertEqual(fractional_exclusions, ["123"])

    def test_structured_schema_rejects_unsupported_and_noninteger_confidence(self):
        validate_assessment(self.answer)
        for invalid in ({**self.answer, "confidence": True},
                        {**self.answer, "confidence": 101},
                        {**self.answer, "confidence": 63.5},
                        {**self.answer, "spin_expectation": "guaranteed"},
                        {**self.answer, "reasoning_basis": []},
                        {**self.answer, "batting_team_won": 1}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_assessment(invalid)

    def test_majority_disagreement_and_confidence_gates(self):
        a = dict(self.answer)
        b = {**self.answer, "confidence": 60, "spin_expectation": "high"}
        c = {**self.answer, "confidence": 10, "spin_expectation": "neutral",
             "overall_expected_environment": "uncertain"}
        result = consensus([a, b, c])
        self.assertEqual(result["spin_expectation"], "uncertain")
        self.assertEqual(result["overall_expected_environment"], "batting_favorable")
        self.assertEqual(result["confidence"], 60)
        self.assertTrue(result["primary_eligible"])
        self.assertTrue(result["broad_eligible"])
        self.assertFalse(result["high_confidence_eligible"])
        self.assertFalse(result["unanimous_eligible"])
        self.assertFalse(consensus([a, {**b, "confidence": 59}, c])["primary_eligible"])


if __name__ == "__main__":
    unittest.main()
