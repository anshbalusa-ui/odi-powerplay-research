"""A selected clean unlocked cohort can have no excluded matches."""

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UnlockedCohortBuildTests(unittest.TestCase):
    def test_clean_only_input_writes_empty_exclusion_header_and_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw"
            raw.mkdir()
            delivery = {"runs": {"total": 0, "batter": 0, "extras": 0}}
            overs = [{"over": index, "deliveries": [delivery.copy() for _ in range(6)]}
                     for index in range(10)]
            match = {
                "info": {
                    "match_type": "ODI", "gender": "male", "dates": ["2023-10-05"],
                    "venue": "Example Oval", "city": "Town",
                    "teams": ["Alpha", "Beta"],
                    "outcome": {"winner": "Alpha"}, "event": {"name": "World Cup"},
                    "toss": {"winner": "Beta", "decision": "field"},
                    "balls_per_over": 6,
                },
                "innings": [{"team": team, "overs": overs} for team in ("Alpha", "Beta")],
            }
            (raw / "111.json").write_text(json.dumps(match))
            (raw / "source_manifest.json").write_text(json.dumps({
                "archive_sha256": "fixture-source", "json_file_count": 1,
            }))
            processed = root / "processed"
            run = subprocess.run([
                sys.executable, str(ROOT / "scripts/build_clean_dataset.py"),
                "--input-dir", str(raw), "--interim-dir", str(root / "interim"),
                "--processed-dir", str(processed),
            ], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            summary = json.loads(run.stdout)
            self.assertEqual(summary["primary_matches"], 1)
            self.assertEqual(summary["excluded_matches"], 0)
            with (processed / "match_exclusions.csv").open(newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertIn("match_id", reader.fieldnames)
                self.assertEqual(list(reader), [])


if __name__ == "__main__":
    unittest.main()
