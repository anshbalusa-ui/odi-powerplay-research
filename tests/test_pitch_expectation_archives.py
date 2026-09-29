"""Only independently timestamped, pre-start archive captures can replace 403s."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from collect_pitch_expectation_archives import (  # noqa: E402
    FetchResult,
    collect_one,
    merge_candidates,
    raw_replay_url,
)
from odi_powerplay.pitch_expectation import validate_screened_capture, source_snapshot


class ArchiveCollectorTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "cricsheet_match_id": "123",
            "source_url": "https://example.org/preview",
            "source_title": "Match preview",
            "published_at_utc": "2023-04-29T12:00:00Z",
            "scheduled_start_utc": "2023-04-30T09:00:00Z",
            "status": "needs_review",
            "http_status": "403",
            "retrieved_at_utc": "2026-09-27T09:00:00Z",
            "raw_sha256": hashlib.sha256(b"").hexdigest(),
            "source_text": "old result-adjacent text must not be reused",
        }
        self.timestamp = "20230429130000"
        self.archive = {
            "match_id": "123",
            "source_url": self.report["source_url"],
            "status": "prestart_hit",
            "archive_status": "200",
            "archive_timestamp": self.timestamp,
            "archive_url": (
                f"http://web.archive.org/web/{self.timestamp}/{self.report['source_url']}"
            ),
        }
        self.html = """<html><head>
        <meta property="article:published_time" content="2023-04-29T12:00:00Z">
        </head><body><article>
        <p>The pitch has a little grass and could offer seam movement early.</p>
        </article></body></html>"""
        self.retrieved = "2026-09-28T12:00:00.123456Z"

    def fake_fetch(self, body=None, final_url=None, status=200):
        replay = raw_replay_url(self.archive["archive_url"], self.report["source_url"])
        return Mock(return_value=FetchResult(
            body=(self.html if body is None else body).encode("utf-8"),
            final_url=replay if final_url is None else final_url,
            http_status=status,
            retrieved_at_utc=self.retrieved,
        ))

    def test_valid_raw_replay_becomes_a_candidate_with_archive_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            fetch = self.fake_fetch()
            result = collect_one(self.report, self.archive, Path(directory), fetcher=fetch)
            self.assertEqual(result["status"], "pre_match_candidate")
            self.assertIn("little grass", result["source_text"])
            self.assertEqual(result["archive_timestamp"], self.timestamp)
            self.assertEqual(result["archive_retrieved_at_utc"], self.retrieved)
            self.assertEqual(result["archive_raw_sha256"], hashlib.sha256(
                self.html.encode("utf-8")).hexdigest())
            self.assertEqual(result["retrieved_at_utc"], self.retrieved)
            self.assertEqual(result["raw_sha256"], result["archive_raw_sha256"])
            self.assertEqual(result["source_access_route"], "archived_original")
            capture = {
                "source_url": self.report["source_url"],
                "published_at_utc": self.report["published_at_utc"],
                "retrieved_at_utc": result["retrieved_at_utc"],
                "review_status": "pre_match_content_verified",
                "reviewer_id": "independent_excerpt_review",
                "source_text": result["source_text"],
            }
            validate_screened_capture(self.report, result, capture)
            self.assertEqual(source_snapshot(self.report, capture)["source_text"],
                             result["source_text"])
            self.assertIn("/web/20230429130000id_/https://example.org/preview",
                          fetch.call_args.args[0])
            self.assertNotIn("<article>", json.dumps(result))
            metadata_files = list(Path(directory).glob("*.json"))
            snapshots = list(Path(directory).glob("*.html"))
            self.assertEqual(len(metadata_files), 1)
            self.assertEqual(len(snapshots), 1)
            metadata = json.loads(metadata_files[0].read_text(encoding="utf-8"))
            self.assertEqual(metadata["archive_url"], self.archive["archive_url"])
            self.assertEqual(metadata["archive_timestamp"], self.timestamp)
            self.assertEqual(metadata["retrieved_at_utc"], self.retrieved)
            self.assertEqual(hashlib.sha256(snapshots[0].read_bytes()).hexdigest(),
                             metadata["raw_sha256"])

    def test_later_timestamp_redirect_is_rejected_without_releasing_text(self):
        later = "https://web.archive.org/web/20230430100000id_/https://example.org/preview"
        with tempfile.TemporaryDirectory() as directory:
            result = collect_one(self.report, self.archive, Path(directory),
                                 fetcher=self.fake_fetch(final_url=later))
            self.assertEqual(result["status"], "needs_review")
            self.assertNotIn("source_text", result)
            self.assertEqual(list(Path(directory).iterdir()), [])
            self.assertEqual(result["retrieved_at_utc"], self.report["retrieved_at_utc"])
            self.assertEqual(result["raw_sha256"], self.report["raw_sha256"])

    def test_redirect_to_different_original_is_rejected(self):
        changed = "https://web.archive.org/web/20230429130000id_/https://example.org/other"
        with tempfile.TemporaryDirectory() as directory:
            result = collect_one(self.report, self.archive, Path(directory),
                                 fetcher=self.fake_fetch(final_url=changed))
            self.assertEqual(result["status"], "needs_review")
            self.assertNotIn("source_text", result)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_replay_redirect_to_nonraw_variant_is_rejected(self):
        rewritten = (
            f"https://web.archive.org/web/{self.timestamp}/{self.report['source_url']}"
        )
        with tempfile.TemporaryDirectory() as directory:
            result = collect_one(self.report, self.archive, Path(directory),
                                 fetcher=self.fake_fetch(final_url=rewritten))
            self.assertEqual(result["status"], "needs_review")
            self.assertNotIn("source_text", result)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_non_prestart_or_missing_archive_record_never_supplies_candidate(self):
        row = dict(self.report)
        row.pop("source_text")
        missing = {"match_id": "123", "source_url": self.report["source_url"],
                   "status": "none_or_late"}
        fetch = self.fake_fetch()
        merged = merge_candidates([row], [missing], Path(tempfile.gettempdir()), fetcher=fetch)
        self.assertEqual(merged[0]["status"], "needs_review")
        self.assertNotIn("source_text", merged[0])
        fetch.assert_not_called()

    def test_archive_index_cannot_replace_an_existing_live_candidate(self):
        live = {**self.report, "status": "pre_match_candidate",
                "source_text": "The pitch is expected to turn."}
        with self.assertRaisesRegex(ValueError, "failed live retrieval"):
            merge_candidates([live], [self.archive], Path(tempfile.gettempdir()),
                             fetcher=self.fake_fetch())

    def test_invalid_archive_original_identity_is_rejected_before_fetch(self):
        wrong = {**self.archive, "archive_url": self.archive["archive_url"] + "/other"}
        fetch = self.fake_fetch()
        with tempfile.TemporaryDirectory() as directory:
            result = collect_one(self.report, wrong, Path(directory), fetcher=fetch)
            self.assertEqual(result["status"], "needs_review")
            self.assertNotIn("source_text", result)
            fetch.assert_not_called()

    def test_archive_capture_must_follow_full_publication_and_precede_start(self):
        same_day = {**self.archive, "archive_timestamp": "20230429115959"}
        same_day["archive_url"] = (
            f"https://web.archive.org/web/{same_day['archive_timestamp']}/"
            f"{self.report['source_url']}"
        )
        fetch = self.fake_fetch()
        with tempfile.TemporaryDirectory() as directory:
            result = collect_one(self.report, same_day, Path(directory), fetcher=fetch)
            self.assertEqual(result["status"], "needs_review")
            self.assertNotIn("source_text", result)
            fetch.assert_not_called()

    def test_date_only_publication_is_conservatively_after_end_of_day(self):
        report = {**self.report, "published_at_utc": "2023-04-29"}
        fetch = self.fake_fetch()
        with tempfile.TemporaryDirectory() as directory:
            result = collect_one(report, self.archive, Path(directory), fetcher=fetch)
            self.assertEqual(result["status"], "needs_review")
            fetch.assert_not_called()

    def test_corrupt_cached_snapshot_is_detected_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            raw_dir = Path(directory)
            first = collect_one(self.report, self.archive, raw_dir, fetcher=self.fake_fetch())
            raw_path = raw_dir / first["archive_snapshot_filename"]
            raw_path.write_bytes(b"tampered")
            fetch = self.fake_fetch(body="replacement")
            second = collect_one(self.report, self.archive, raw_dir, fetcher=fetch)
            self.assertEqual(second["status"], "needs_review")
            self.assertNotIn("source_text", second)
            self.assertEqual(raw_path.read_bytes(), b"tampered")
            fetch.assert_not_called()
            self.assertEqual(len(list(raw_dir.glob("*.html"))), 1)

    def test_embedded_modification_after_capture_is_not_overridden_by_archive_date(self):
        changed = self.html.replace(
            "</head>",
            '<meta property="article:modified_time" content="2023-04-29T13:00:01Z"></head>',
        )
        with tempfile.TemporaryDirectory() as directory:
            result = collect_one(self.report, self.archive, Path(directory),
                                 fetcher=self.fake_fetch(body=changed))
            self.assertEqual(result["status"], "contaminated_or_ambiguous")
            self.assertNotIn("source_text", result)


if __name__ == "__main__":
    unittest.main()
