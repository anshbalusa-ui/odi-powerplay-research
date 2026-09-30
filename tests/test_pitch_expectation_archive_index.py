"""The same two-anchor archive discovery rule applies to every blocked original."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from index_pitch_expectation_archives import discover_original  # noqa: E402


class ArchiveIndexTests(unittest.TestCase):
    def report(self, year, provider):
        return {
            "cricsheet_match_id": str(year),
            "source_url": f"https://{provider}/preview",
            "published_at_utc": f"{year}-03-01T10:00:00Z",
            "scheduled_start_utc": f"{year}-03-02T10:00:00Z",
            "http_status": "403", "status": "needs_review",
        }

    def test_late_closest_at_first_anchor_checks_published_anchor_uniformly(self):
        for year, provider in ((2024, "a.example"), (2023, "b.example")):
            with self.subTest(year=year):
                report = self.report(year, provider)
                calls = []

                def fetch(original, anchor):
                    calls.append((original, anchor))
                    timestamp = (f"{year}0303110000" if len(calls) == 1
                                 else f"{year}0301110000")
                    return {
                        "archived_snapshots": {"closest": {
                            "status": "200", "timestamp": timestamp,
                            "url": f"http://web.archive.org/web/{timestamp}/{original}",
                        }}
                    }, "a" * 64, f"2026-09-28T0{len(calls)}:00:00Z"

                found = discover_original(report, fetcher=fetch)
                self.assertEqual(found["status"], "prestart_hit")
                self.assertEqual(found["archive_timestamp"], f"{year}0301110000")
                self.assertEqual([anchor for _, anchor in calls],
                                 [f"{year}0302095959", f"{year}0301110000"])
                self.assertEqual(len(found["index_queries"]), 2)
                self.assertTrue(all(original == report["source_url"] for original, _ in calls))

    def test_mismatched_original_or_only_poststart_archive_never_passes(self):
        report = self.report(2024, "a.example")
        calls = []

        def wrong(original, anchor):
            calls.append(anchor)
            timestamp = "20240301110000" if len(calls) == 1 else "20240302110000"
            url = f"http://web.archive.org/web/{timestamp}/https://other.example/preview"
            return {"archived_snapshots": {"closest": {
                "status": "200", "timestamp": timestamp, "url": url,
            }}}, "b" * 64, "2026-09-28T01:00:00Z"

        found = discover_original(report, fetcher=wrong)
        self.assertEqual(found["status"], "none_or_late")
        self.assertEqual(len(found["index_queries"]), 2)
        self.assertEqual(len(calls), 2)
        self.assertFalse(discover_original(report, fetcher=lambda original, anchor:
                          ({"archived_snapshots": {}}, "c" * 64, "2026-09-28T01:00:00Z"))
                         ["archive_timestamp"])

if __name__ == "__main__":
    unittest.main()
