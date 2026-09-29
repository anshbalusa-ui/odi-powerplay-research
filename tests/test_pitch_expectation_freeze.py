"""No outcome-modeling release can be frozen from incomplete or changed passes."""

import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from odi_powerplay.pitch_expectation import assessment_input, canonical_json, rubric_hash, rubric_version  # noqa: E402
from build_pitch_expectation_inputs import _source_coverage  # noqa: E402
from audit_pitch_expectations import main as audit_inputs  # noqa: E402
from build_pitch_expectation_consensus import main as build_consensus  # noqa: E402
from freeze_pitch_expectation_measurement import main as freeze_measurement  # noqa: E402


class FrozenMeasurementTests(unittest.TestCase):
    def create_measurement(self, root):
        inputs = root / "inputs.jsonl"
        screen = root / "screen.jsonl"
        archive_index = root / "archive_index.json"
        text = "The pitch should offer seam movement early in the match."
        report = {
            "cricsheet_match_id": "123", "match_date": "2024-03-01",
            "event_name": "Series", "competition_type": "bilateral_series",
            "venue": "Oval", "city": "Town", "team_1": "Alpha", "team_2": "Beta",
            "source_url": "https://example.org/preview", "source_title": "Match preview",
            "published_at_utc": "2024-02-29T09:00:00Z",
            "accessed_at_utc": "2026-09-28T00:00:00Z",
            "scheduled_start_utc": "2024-03-01T08:00:00Z",
        }
        payload = assessment_input(report, report, text, hashlib.sha256(text.encode()).hexdigest())
        inputs.write_text(canonical_json(payload) + "\n", encoding="utf-8")
        screen.write_text('{"cricsheet_match_id":"123"}\n', encoding="utf-8")
        archive_index.write_text('[]\n', encoding="utf-8")
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        sources = [
            {"cricsheet_match_id": "123", "source_status": "assessable",
             "source_access_route": "live_original", "year": "2024",
             "provider": "example.org", "split": "validation"},
            {"cricsheet_match_id": "124", "source_status": "timing_ambiguous",
             "source_access_route": "no_eligible_source", "year": "2024",
             "provider": "example.org", "split": "validation"},
        ]
        manifest = {
            "source_protocol_version": "PE-006-v1", "locked_test_scored": False,
            "input_sha256": digest(inputs), "source_screen_sha256": digest(screen),
            "rubric_sha256": rubric_hash(), "rubric_version": rubric_version(),
            "assessable_count": 1, "eligible_source_count": 1,
            "registry_candidate_count": 2, "source_statuses": {
                "assessable": 1, "timing_ambiguous": 1,
            }, "sources": sources, "source_access_route_counts": {
                "live_original": 1, "no_eligible_source": 1,
            }, "source_coverage_counts": _source_coverage(sources),
            "year_counts": {"2024": 2}, "provider_counts": {"example.org": 2},
            "split_counts": {"validation": 2}, "source_registry_sha256": {},
        }
        (root / "input_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        answer = {
            "batting_expectation": "uncertain", "pace_seam_expectation": "high",
            "spin_expectation": "uncertain", "slow_two_paced_expectation": "uncertain",
            "overall_expected_environment": "pace_seam_favorable", "confidence": 80,
            "evidence": "The pre-match preview expects seam movement.",
            "reasoning_basis": ["explicit_playing_effect_statement"],
            "rationale": "Seam assistance is forecast before play.",
        }
        for label in "ABC":
            model = "gpt-6-sol" if label == "C" else "gpt-5.6-luna"
            record = {
                "cricsheet_match_id": "123", "assessor_id": label,
                "model_name": model, "model_version": model,
                "reasoning_effort": "high", "prompt_hash": rubric_hash(),
                "source_hash": payload["source_hash"],
                "source_release_sha256": manifest["input_sha256"],
                "run_id": f"fresh-{label}", "assessed_at_utc": "2026-09-28T12:00:00Z",
                "assessment": answer,
            }
            pass_file = root / f"pass_{label.lower()}.jsonl"
            pass_file.write_text(canonical_json(record) + "\n", encoding="utf-8")
            pass_manifest = {
                "assessor_id": label, "model_name": model,
                "model_versions": [model], "model_identity_source": "provider_response",
                "reasoning_effort": "high", "run_id": f"fresh-{label}",
                "prompt_hash": rubric_hash(), "rubric_version": rubric_version(),
                "input_sha256": manifest["input_sha256"],
                "output_sha256": digest(pass_file), "record_count": 1,
                "locked_test_scored": False,
            }
            (root / f"pass_{label.lower()}_manifest.json").write_text(
                json.dumps(pass_manifest), encoding="utf-8"
            )
        consensus = root / "consensus.csv"
        agreement = root / "agreement.json"
        worksheet = root / "human_audit.csv"
        audit = root / "leakage_audit_passed.json"
        with patch.object(sys, "argv", ["audit", "--inputs", str(inputs),
                                        "--manifest", str(root / "input_manifest.json"),
                                        "--output", str(audit)]):
            audit_inputs()
        with patch.object(sys, "argv", ["consensus", "--input-dir", str(root),
                                        "--consensus-output", str(consensus),
                                        "--agreement-output", str(agreement),
                                        "--worksheet-output", str(worksheet)]):
            build_consensus()
        return screen, archive_index, consensus, agreement, worksheet, audit

    def test_freeze_rejects_tampered_pass_and_preserves_existing_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screen, archive_index, consensus, agreement, worksheet, audit = self.create_measurement(root)
            output = root / "final_manifest.json"
            args = ["freeze", "--input-dir", str(root), "--source-screen", str(screen),
                    "--archive-index", str(archive_index), "--consensus", str(consensus),
                    "--agreement", str(agreement), "--worksheet", str(worksheet),
                    "--leakage-audit", str(audit), "--output", str(output)]
            with patch.object(sys, "argv", args):
                freeze_measurement()
            frozen_bytes = output.read_bytes()
            frozen = json.loads(frozen_bytes)
            self.assertFalse(frozen["locked_test_scored"])
            self.assertEqual(frozen["source_eligibility_protocol_version"], "PE-006-v1")
            self.assertEqual(frozen["source_release_sha256"],
                             json.loads((root / "input_manifest.json").read_text())["input_sha256"])
            self.assertEqual(frozen["excluded_row_dispositions"]["timing_ambiguous"], 1)
            (root / "pass_a.jsonl").write_text('{"changed":"after assessment"}\n')
            with patch.object(sys, "argv", [*args[:-1], str(root / "second_manifest.json")]):
                with self.assertRaises(ValueError):
                    freeze_measurement()
            self.assertFalse((root / "second_manifest.json").exists())
            with patch.object(sys, "argv", args):
                with self.assertRaises(FileExistsError):
                    freeze_measurement()
            self.assertEqual(output.read_bytes(), frozen_bytes)

    def test_freeze_rejects_unobserved_cli_model_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screen, archive_index, consensus, agreement, worksheet, audit = self.create_measurement(root)
            path = root / "pass_a_manifest.json"
            manifest = json.loads(path.read_text())
            manifest["model_identity_source"] = "requested_route"
            path.write_text(json.dumps(manifest))
            report = json.loads(agreement.read_text())
            report["assessor_manifests"]["A"] = manifest
            agreement.write_text(json.dumps(report))
            output = root / "final_manifest.json"
            args = ["freeze", "--input-dir", str(root), "--source-screen", str(screen),
                    "--archive-index", str(archive_index), "--consensus", str(consensus),
                    "--agreement", str(agreement), "--worksheet", str(worksheet),
                    "--leakage-audit", str(audit), "--output", str(output)]
            with patch.object(sys, "argv", args), self.assertRaisesRegex(ValueError, "provider response model"):
                freeze_measurement()
            self.assertFalse(output.exists())

    def test_freeze_rejects_rehashed_but_nonmechanical_consensus(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screen, archive_index, consensus, agreement, worksheet, audit = self.create_measurement(root)
            with consensus.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fields = reader.fieldnames
                rows = list(reader)
            rows[0]["overall_expected_environment"] = "balanced"
            with consensus.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            report = json.loads(agreement.read_text())
            report["consensus_sha256"] = hashlib.sha256(consensus.read_bytes()).hexdigest()
            agreement.write_text(json.dumps(report))
            output = root / "invalid_frozen_manifest.json"
            args = ["freeze", "--input-dir", str(root), "--source-screen", str(screen),
                    "--archive-index", str(archive_index), "--consensus", str(consensus),
                    "--agreement", str(agreement), "--worksheet", str(worksheet),
                    "--leakage-audit", str(audit), "--output", str(output)]
            with patch.object(sys, "argv", args), self.assertRaisesRegex(ValueError, "mechanical consensus"):
                freeze_measurement()
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
