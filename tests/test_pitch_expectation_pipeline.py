"""Assessment provenance and source eligibility cannot silently degrade."""

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from odi_powerplay.pitch_expectation import (  # noqa: E402
    assessment_input, validate_passes, source_snapshot, source_disposition, rubric_hash,
)


class AssessmentPipelineTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(cricsheet_match_id="123", match_date="2024-03-01", event_name="Tour",
                        competition_type="bilateral_series", venue="Ground", city="City",
                        team_1="A", team_2="B", source_url="https://example.org/pre-match",
                        source_title="Pre-match pitch preview", published_at_utc="2024-02-29T09:00:00Z",
                        accessed_at_utc="2026-09-27T09:00:00Z", scheduled_start_utc="2024-03-01T08:00:00Z")
        self.answer = dict(batting_expectation="uncertain", pace_seam_expectation="uncertain",
                           spin_expectation="uncertain", slow_two_paced_expectation="uncertain",
                           overall_expected_environment="uncertain", confidence=44,
                           evidence="The report describes only a fresh surface.",
                           reasoning_basis=["physical_surface_description"],
                           rationale="The description does not establish a clear favorite.")
        self.text = "The preview describes a fresh surface."
        self.capture = {"source_url": self.row["source_url"], "source_text": self.text,
                        "retrieved_at_utc": "2026-09-27T09:00:00Z", "review_status": "pre_match_content_verified",
                        "reviewer_id": "independent_review_01", "published_at_utc": self.row["published_at_utc"]}

    def test_snapshot_needs_verified_original_content_not_old_paraphrase(self):
        capture = source_snapshot(self.row, self.capture)
        self.assertEqual(capture["source_hash"], hashlib.sha256(self.text.encode()).hexdigest())
        self.assertNotIn("reviewer_id", assessment_input(self.row, self.row, self.text, capture["source_hash"]))
        with self.assertRaises(ValueError):
            source_snapshot(self.row, {**self.capture, "review_status": "needs_review"})
        with self.assertRaises(ValueError):
            source_snapshot(self.row, {**self.capture, "source_text": "Final score 300/4"})
        with self.assertRaises(ValueError):
            source_snapshot(self.row, {**self.capture, "published_at_utc": "2024-03-02T09:00:00Z"})

    def test_unavailable_and_contaminated_require_provenance_not_guesses(self):
        disposition = {
            "source_url": self.row["source_url"],
            "review_status": "unavailable",
            "retrieved_at_utc": "2026-09-27T09:00:00Z",
            "reviewer_id": "reviewer",
            "status_note": "HTTP 404 when opening verified URL",
        }
        self.assertEqual(source_disposition(self.row, disposition)["source_status"], "unavailable")
        for bad in ({**disposition, "status_note": ""},
                    {**disposition, "source_url": "https://example.org/other"},
                    {**disposition, "reviewer_id": ""},
                    {**disposition, "review_status": "assessable"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                source_disposition(self.row, bad)

    def test_no_partial_or_mismatched_passes_can_reach_consensus(self):
        payload = assessment_input(self.row, self.row, self.text,
                                   hashlib.sha256(self.text.encode()).hexdigest())
        record = dict(cricsheet_match_id="123", model_name="test-model", model_version="test-model-001",
                      reasoning_effort="high", prompt_hash=rubric_hash(),
                      source_hash=payload["source_hash"], run_id="run-1",
                      assessed_at_utc="2026-09-27T12:00:00Z", assessment=self.answer)
        passes = {key: [{**record, "assessor_id": key}] for key in "ABC"}
        validate_passes([payload], passes)
        for bad in ({"A": passes["A"], "B": passes["B"]},
                    {**passes, "C": []},
                    {**passes, "B": [{**record, "assessor_id": "A"}]},
                    {**passes, "C": [{**record, "assessor_id": "C", "prompt_hash": "stale"}]},
                    {**passes, "A": [{**record, "assessor_id": "A", "source_hash": "other"}]}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_passes([payload], bad)


if __name__ == "__main__":
    unittest.main()
