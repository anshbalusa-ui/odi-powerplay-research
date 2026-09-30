"""A transient fetch may be retried without replacing its original snapshot."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from collect_pitch_expectation_candidates import acquire  # noqa: E402
from audit_pitch_expectations import main as audit_inputs  # noqa: E402
from build_pitch_expectation_inputs import _source_coverage  # noqa: E402
from odi_powerplay.pitch_expectation import assessment_input, rubric_hash, rubric_version  # noqa: E402


class SourceRetryTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "cricsheet_match_id": "123",
            "source_url": "https://example.org/preview",
            "source_title": "Match preview",
            "published_at_utc": "2023-04-29T12:00:00Z",
            "scheduled_start_utc": "2023-04-30T09:00:00Z",
        }
        self.html = b'''<html><head>
        <meta property="article:published_time" content="2023-04-29T12:00:00Z">
        <meta property="article:modified_time" content="2023-04-29T13:00:00Z">
        </head><article><p>The pitch has a little grass and could offer seam movement early.</p>
        </article></html>'''

    def snapshot(self, root, code="000", exit_status=28):
        (root / "123.20260101T000000000000Z.html").write_bytes(b"")
        original = {
            "cricsheet_match_id": "123", "source_url": self.report["source_url"],
            "snapshot_filename": "123.20260101T000000000000Z.html",
            "raw_sha256": hashlib.sha256(b"").hexdigest(),
            "retrieved_at_utc": "2026-01-01T00:00:00+00:00",
            "http_status": code, "curl_exit_status": exit_status,
        }
        (root / "123.20260101T000000000000Z.json").write_text(json.dumps(original))
        return original

    def test_retry_preserves_old_failure_and_reuses_new_verified_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = self.snapshot(root)
            with patch("collect_pitch_expectation_candidates.subprocess.run", return_value=SimpleNamespace(
                returncode=0, stdout=self.html + b"200",
            )) as request:
                updated = acquire(self.report, root, retry_transient=True)
                self.assertEqual(updated["status"], "pre_match_candidate")
                self.assertEqual(acquire(self.report, root), updated)
                request.assert_called_once()
            self.assertEqual(json.loads((root / "123.20260101T000000000000Z.json").read_text()), old)
            self.assertEqual((root / "123.20260101T000000000000Z.html").read_bytes(), b"")
            self.assertEqual(len(list(root.glob("123.*.json"))), 2)
            self.assertEqual(len(list(root.glob("123.*.html"))), 2)

    def test_nontransient_failure_is_not_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.snapshot(root, "403", 56)
            with patch("collect_pitch_expectation_candidates.subprocess.run") as request:
                result = acquire(self.report, root, retry_transient=True)
                self.assertEqual(result["status"], "needs_review")
                request.assert_not_called()


    def test_assessor_projection_excludes_route_and_outcome_metadata(self):
        report = {
            "cricsheet_match_id": "m1", "match_date": "2023-01-01",
            "event_name": "event", "competition_type": "league", "venue": "ground",
            "city": "city", "team_1": "one", "team_2": "two",
            "source_url": "https://example.org/p", "source_title": "Preview",
            "published_at_utc": "2022-12-31T00:00:00+00:00",
            "accessed_at_utc": "2023-01-01T00:00:00+00:00",
            "source_access_route": "archived_original",
        }
        start = {"scheduled_start_utc": "2023-01-02T00:00:00+00:00"}
        text = "Grass and seam movement."
        payload = assessment_input(report, start, text, hashlib.sha256(text.encode()).hexdigest())
        self.assertNotIn("source_access_route", payload)
        self.assertFalse({"winner", "result", "score"} & set(payload))
        with self.assertRaises(ValueError):
            assessment_input({**report, "winner": "one"}, start, text,
                            hashlib.sha256(text.encode()).hexdigest())

    def test_timing_ambiguous_route_cannot_masquerade_as_an_original(self):
        text = "The pitch could offer seam movement early."
        report = {
            "cricsheet_match_id": "123", "match_date": "2024-03-01",
            "event_name": "Tour", "competition_type": "bilateral_series",
            "venue": "Ground", "city": "Town", "team_1": "A", "team_2": "B",
            "source_url": "https://example.org/preview", "source_title": "Preview",
            "published_at_utc": "2024-02-29T09:00:00Z",
            "accessed_at_utc": "2026-09-28T09:00:00Z",
            "scheduled_start_utc": "2024-03-01T09:00:00Z",
        }
        payload = assessment_input(report, report, text, hashlib.sha256(text.encode()).hexdigest())
        statuses = [
            {"cricsheet_match_id": "123", "source_status": "assessable",
             "source_access_route": "live_original", "year": "2024",
             "provider": "example.org", "split": "validation"},
            {"cricsheet_match_id": "124", "source_status": "timing_ambiguous",
             "source_access_route": "no_eligible_source", "year": "2025",
             "provider": "example.org", "split": "locked"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs, manifest, output = (root / name for name in
                                        ("inputs.jsonl", "manifest.json", "audit.json"))
            inputs.write_text(json.dumps(payload) + "\n")
            release = {
                "locked_test_scored": False, "rubric_sha256": rubric_hash(),
                "rubric_version": rubric_version(), "source_protocol_version": "PE-006-v1",
                "input_sha256": hashlib.sha256(inputs.read_bytes()).hexdigest(),
                "assessable_count": 1, "sources": statuses,
                "source_access_route_counts": {"live_original": 1, "no_eligible_source": 1},
                "source_coverage_counts": _source_coverage(statuses),
            }
            manifest.write_text(json.dumps(release))
            with patch.object(sys, "argv", ["audit", "--inputs", str(inputs),
                                            "--manifest", str(manifest),
                                            "--output", str(output)]):
                audit_inputs()
            self.assertTrue(json.loads(output.read_text())["passed_structural_blinding_audit"])
            statuses[1]["source_access_route"] = "archived_original"
            release["source_access_route_counts"] = {
                "live_original": 1, "archived_original": 1,
            }
            release["source_coverage_counts"] = _source_coverage(statuses)
            manifest.write_text(json.dumps(release))
            with patch.object(sys, "argv", ["audit", "--inputs", str(inputs),
                                            "--manifest", str(manifest),
                                            "--output", str(output)]):
                with self.assertRaises(SystemExit):
                    audit_inputs()
            self.assertFalse(json.loads(output.read_text())["passed_structural_blinding_audit"])

if __name__ == "__main__":
    unittest.main()
