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
from collect_pitch_expectation_candidates import acquire  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
