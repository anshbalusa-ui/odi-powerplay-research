"""Assessment provenance and source eligibility cannot silently degrade."""

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_pitch_expectation_inputs import _source_coverage  # noqa: E402
from odi_powerplay.pitch_expectation import (  # noqa: E402
    assessment_input, validate_passes, source_snapshot, source_disposition, rubric_hash,
    validate_screened_capture, audit_sample,
)
class AssessmentPipelineTests(unittest.TestCase):
    def test_source_coverage_separates_archived_and_live_inclusion(self):
        sources = [
            {"source_access_route": "archived_original", "year": "2024",
             "provider": "a.example", "split": "validation", "source_status": "assessable"},
            {"source_access_route": "archived_original", "year": "2024",
             "provider": "a.example", "split": "validation", "source_status": "needs_review"},
            {"source_access_route": "live_original", "year": "2023",
             "provider": "b.example", "split": "development", "source_status": "assessable"},
            {"source_access_route": "no_eligible_source", "year": "2025",
             "provider": "c.example", "split": "locked", "source_status": "timing_ambiguous"},
        ]
        counts = _source_coverage(sources)
        self.assertEqual(counts["by_route"]["archived_original"],
                         {"included": 1, "excluded": 1})
        self.assertEqual(counts["by_route"]["live_original"],
                         {"included": 1, "excluded": 0})
        self.assertEqual(counts["by_year"]["2024"], {"included": 1, "excluded": 1})
        self.assertEqual(counts["by_provider"]["c.example"],
                         {"included": 0, "excluded": 1})
        self.assertEqual(counts["by_split"]["locked"], {"included": 0, "excluded": 1})

    def test_audit_sample_covers_available_routes_disagreements_uncertain_and_providers(self):
        rows = []
        for index in range(18):
            rows.append({
                "cricsheet_match_id": f"{index:03}",
                "source_access_route": "archived_original" if index < 9 else "live_original",
                "source_url": f"https://{'a' if index % 2 == 0 else 'b'}.example.org/story",
                "match_date": f"{2018 + index % 7}-03-01",
                "overall_expected_environment": "uncertain" if index == 16 else "balanced",
                "confidence": 90 if index == 17 else 50,
                "broad_eligible": index != 15,
            })
        selected = audit_sample(rows)
        self.assertEqual(len(selected), 15)
        self.assertGreaterEqual(sum(r["source_access_route"] == "archived_original"
                                    for r in selected), 3)
        self.assertGreaterEqual(sum(r["source_access_route"] == "live_original"
                                    for r in selected), 3)
        self.assertTrue(any(not r["broad_eligible"] for r in selected))
        self.assertTrue(any(r["overall_expected_environment"] == "uncertain"
                            for r in selected))
        self.assertTrue(any(r["confidence"] >= 75 for r in selected))
        self.assertGreaterEqual(len({r["source_url"].split("/")[2] for r in selected}), 2)



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
            source_snapshot(self.row, {**self.capture, "source_text": "Two defeats on a flat pitch."})
        with self.assertRaises(ValueError):
            source_snapshot(self.row, {**self.capture, "published_at_utc": "2024-03-02T09:00:00Z"})

    def test_prior_series_result_in_title_cannot_enter_model_payload(self):
        report = {**self.row, "source_title": "Series conceded, team seeks revival"}
        with self.assertRaises(ValueError):
            assessment_input(report, report, self.text, hashlib.sha256(self.text.encode()).hexdigest())
    def test_forbidden_registry_fields_are_rejected_before_positive_projection(self):
        payload_hash = hashlib.sha256(self.text.encode()).hexdigest()
        for key in (
            "winner", "batting_team_won", "result", "score", "final_score",
            "innings_total", "pp_delivery_events", "pp_run_rate", "pp_boundary_pct",
            "pp_dot_ball_pct", "powerplay_runs", "powerplay_wickets", "chase",
            "old_pitch_code", "pitch_effect", "coder_id", "confidence",
            "effect_evidence_note", "reconciliation", "peer_assessment",
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                assessment_input(
                    {**self.row, key: "forbidden"}, self.row, self.text, payload_hash
                )

    def test_assessor_payload_must_have_exact_positive_allowlist(self):
        payload_hash = hashlib.sha256(self.text.encode()).hexdigest()
        payload = assessment_input(self.row, self.row, self.text, payload_hash)
        self.assertEqual(set(payload), {
            "cricsheet_match_id", "match_date", "event_name", "competition_type",
            "venue", "city", "team_1", "team_2", "source_url", "source_title",
            "published_at_utc", "accessed_at_utc", "scheduled_start_utc",
            "source_text", "source_hash",
        })

    def test_passes_bind_source_release_hash_and_share_unique_run_ids(self):
        payload = assessment_input(
            self.row, self.row, self.text, hashlib.sha256(self.text.encode()).hexdigest()
        )
        release_hash = "d" * 64
        record = dict(cricsheet_match_id="123", model_name="test-model",
                      model_version="test-model-001", reasoning_effort="high",
                      prompt_hash=rubric_hash(), source_hash=payload["source_hash"],
                      source_release_sha256=release_hash, run_id="run-1",
                      assessed_at_utc="2026-09-27T12:00:00Z", assessment=self.answer)
        passes = {
            key: [{**record, "assessor_id": key, "run_id": f"run-{key}"}]
            for key in "ABC"
        }
        validate_passes([payload], passes, release_hash)
        with self.assertRaises(ValueError):
            validate_passes([payload], {
                **passes, "C": [{**passes["C"][0], "source_release_sha256": "e" * 64}]
            }, release_hash)
        with self.assertRaises(ValueError):
            validate_passes([payload], {
                **passes, "B": [{**passes["B"][0], "run_id": passes["A"][0]["run_id"]}]
            }, release_hash)
        with self.assertRaises(ValueError):
            validate_passes([{**payload, "peer_output": "x"}], passes, release_hash)


    def test_revised_source_screen_revokes_a_stale_verified_capture(self):
        screened = {
            "cricsheet_match_id": "123", "source_url": self.row["source_url"],
            "published_at_utc": self.row["published_at_utc"],
            "scheduled_start_utc": self.row["scheduled_start_utc"],
            "retrieved_at_utc": self.capture["retrieved_at_utc"],
            "raw_sha256": "a" * 64,
            "status": "contaminated_or_ambiguous",
        }
        with self.assertRaises(ValueError):
            validate_screened_capture(self.row, screened, self.capture)
        approved = {**screened, "status": "pre_match_candidate", "source_text": self.text}
        validate_screened_capture(self.row, approved, self.capture)
        with self.assertRaises(ValueError):
            validate_screened_capture(self.row, {**approved, "source_text": "other article"}, self.capture)
        with self.assertRaises(ValueError):
            validate_screened_capture(self.row, {**approved, "raw_sha256": ""}, self.capture)

    def test_archived_source_provenance_must_bound_reviewed_bytes(self):
        stamp = "20240229120000"
        candidate = {
            "cricsheet_match_id": "123", "source_url": self.row["source_url"],
            "published_at_utc": self.row["published_at_utc"],
            "scheduled_start_utc": self.row["scheduled_start_utc"],
            "retrieved_at_utc": self.capture["retrieved_at_utc"],
            "raw_sha256": "a" * 64, "status": "pre_match_candidate",
            "source_text": self.text, "http_status": "403",
            "source_access_route": "archived_original",
            "archive_timestamp": stamp, "archive_http_status": 200,
            "archive_raw_sha256": "a" * 64,
            "archive_retrieved_at_utc": self.capture["retrieved_at_utc"],
            "archive_url": f"http://web.archive.org/web/{stamp}/{self.row['source_url']}",
            "archive_effective_url": (
                f"https://web.archive.org/web/{stamp}id_/{self.row['source_url']}"
            ),
        }
        validate_screened_capture(self.row, candidate, self.capture)
        invalid = [
            {"archive_timestamp": "20240301100000"},
            {"archive_timestamp": "20240229080000"},
            {"archive_effective_url": "https://web.archive.org/web/20240301100000id_/"
                                      + self.row["source_url"]},
            {"archive_raw_sha256": "b" * 64},
            {"archive_http_status": 403},
            {"archive_retrieved_at_utc": "2026-09-28T00:00:00Z"},
        ]
        for changed in invalid:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                validate_screened_capture(self.row, {**candidate, **changed}, self.capture)


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
        release_hash = "d" * 64
        record = dict(cricsheet_match_id="123", model_name="test-model", model_version="test-model-001",
                      reasoning_effort="high", prompt_hash=rubric_hash(),
                      source_hash=payload["source_hash"], source_release_sha256=release_hash,
                      run_id="run-1", assessed_at_utc="2026-09-27T12:00:00Z",
                      assessment=self.answer)
        passes = {
            key: [{**record, "assessor_id": key, "run_id": f"run-{key}"}]
            for key in "ABC"
        }
        validate_passes([payload], passes, release_hash)
        for bad in ({"A": passes["A"], "B": passes["B"]},
                    {**passes, "C": []},
                    {**passes, "B": [{**record, "assessor_id": "A"}]},
                    {**passes, "C": [{**passes["C"][0], "prompt_hash": "stale"}]},
                    {**passes, "A": [{**passes["A"][0], "source_hash": "other"}]},
                    {**passes, "A": [{**passes["A"][0], "source_release_sha256": "e" * 64}]}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_passes([payload], bad, release_hash)


if __name__ == "__main__":
    unittest.main()
