"""Only outcome-unlocked registry members may be opened from a raw ODI ZIP."""

import csv
import hashlib
import json
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from materialize_ssac27_unlocked_raw import materialize_unlocked  # noqa: E402


class UnlockedSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.registry = self.root / "match_start_times_template.csv"
        with self.registry.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["cricsheet_match_id", "match_date"])
            writer.writeheader()
            writer.writerows([
                {"cricsheet_match_id": "111", "match_date": "2023-10-05"},
                {"cricsheet_match_id": "222", "match_date": "2024-02-03"},
                {"cricsheet_match_id": "333", "match_date": "2025-05-01"},
            ])
        self.archive = self.root / "odis_json.zip"
        with zipfile.ZipFile(self.archive, "w") as zipped:
            for match_id, date in (("111", "2023-10-05"), ("222", "2024-02-03")):
                zipped.writestr(f"{match_id}.json", json.dumps({
                    "info": {"dates": [date], "gender": "male", "match_type": "ODI"},
                    "innings": [],
                }))
            zipped.writestr("333.json", b"locked-member-must-never-be-opened")
        self.digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.output = self.root / "extracted"

    def test_reads_exactly_unlocked_members_and_never_opens_locked_payload(self):
        actual_read = zipfile.ZipFile.read

        def guarded_read(zipped, member, *args, **kwargs):
            if str(member).endswith("333.json"):
                raise AssertionError("locked outcome member opened")
            return actual_read(zipped, member, *args, **kwargs)

        with patch.object(zipfile.ZipFile, "read", guarded_read):
            manifest = materialize_unlocked(
                self.archive, self.registry, self.output,
                expected_archive_sha256=self.digest, expected_unlocked_matches=2,
            )
        self.assertEqual({item.name for item in self.output.glob("*.json")},
                         {"111.json", "222.json", "source_manifest.json"})
        self.assertEqual(manifest["json_file_count"], 2)
        self.assertFalse(manifest["locked_test_scored"])
        self.assertEqual(manifest["archive_sha256"], self.digest)
        self.assertEqual(set(manifest["unlocked_member_sha256"]), {"111", "222"})

    def test_rejects_changed_archive_missing_member_and_date_mismatch_without_release(self):
        with self.assertRaisesRegex(ValueError, "archive SHA"):
            materialize_unlocked(
                self.archive, self.registry, self.output,
                expected_archive_sha256="0" * 64, expected_unlocked_matches=2,
            )
        self.assertFalse(self.output.exists())
        self.registry.write_text(
            "cricsheet_match_id,match_date\n111,2023-10-06\n222,2024-02-03\n333,2025-05-01\n"
        )
        with self.assertRaisesRegex(ValueError, "registry date"):
            materialize_unlocked(
                self.archive, self.registry, self.output,
                expected_archive_sha256=self.digest, expected_unlocked_matches=2,
            )
        self.assertFalse(self.output.exists())
        self.registry.write_text(
            "cricsheet_match_id,match_date\n111,2023-10-05\n444,2024-02-03\n333,2025-05-01\n"
        )
        with self.assertRaisesRegex(ValueError, "missing unlocked"):
            materialize_unlocked(
                self.archive, self.registry, self.output,
                expected_archive_sha256=self.digest, expected_unlocked_matches=2,
            )
        self.assertFalse(self.output.exists())

    def test_duplicate_unlocked_member_is_never_silently_selected(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.archive, "a") as zipped:
                zipped.writestr("111.json", '{"info":{"dates":["2023-10-05"],"gender":"male","match_type":"ODI"}}')
        with self.assertRaisesRegex(ValueError, "duplicate unlocked"):
            materialize_unlocked(
                self.archive, self.registry, self.output,
                expected_archive_sha256=hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                expected_unlocked_matches=2,
            )
        self.assertFalse(self.output.exists())

    def test_never_overwrites_existing_raw_release(self):
        self.output.mkdir()
        marker = self.output / "111.json"
        marker.write_bytes(b"previous raw snapshot")
        with self.assertRaises(FileExistsError):
            materialize_unlocked(
                self.archive, self.registry, self.output,
                expected_archive_sha256=self.digest, expected_unlocked_matches=2,
            )
        self.assertEqual(marker.read_bytes(), b"previous raw snapshot")


if __name__ == "__main__":
    unittest.main()
