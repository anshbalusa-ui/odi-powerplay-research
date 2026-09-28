"""Automated source screens cannot silently become verified assessor inputs."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from materialize_pitch_expectation_source_statuses import screened_disposition  # noqa: E402


class MaterializedSourceStatusesTests(unittest.TestCase):
    def test_unreviewed_candidates_are_never_automatically_promoted(self):
        candidate = {"status": "pre_match_candidate", "source_url": "https://example.org/a",
                     "retrieved_at_utc": "2026-09-28T07:00:00+00:00"}
        with self.assertRaises(ValueError):
            screened_disposition(candidate)

    def test_late_amended_source_stays_excluded_with_reason(self):
        candidate = {"status": "contaminated_or_ambiguous", "source_url": "https://example.org/a",
                     "retrieved_at_utc": "2026-09-28T07:00:00+00:00",
                     "reason": "article could contain later edits"}
        disposition = screened_disposition(candidate)
        self.assertEqual(disposition["review_status"], "contaminated_or_ambiguous")
        self.assertIn("later edits", disposition["status_note"])
        self.assertNotIn("source_text", disposition)


if __name__ == "__main__":
    unittest.main()
