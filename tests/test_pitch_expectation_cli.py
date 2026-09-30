"""CLI assessment must never accept tool use, peer data or malformed final answers."""

import json
import hashlib
import sys
import unittest
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import ASSESSMENT_KEYS, BASES, CATEGORIES, rubric_hash  # noqa: E402
from run_pitch_expectation_agents_codex import parse_agent_events  # noqa: E402
from build_pitch_expectation_consensus import (  # noqa: E402
    validate_pass_output_hash, validate_pass_release,
)


class CodexAssessorTests(unittest.TestCase):
    def setUp(self):
        self.answer = {
            "batting_expectation": "uncertain", "pace_seam_expectation": "uncertain",
            "spin_expectation": "uncertain", "slow_two_paced_expectation": "uncertain",
            "overall_expected_environment": "uncertain", "confidence": 25,
            "evidence": "Source contains mixed condition cues.",
            "reasoning_basis": ["physical_surface_description"],
            "rationale": "Neither cue resolves a favored playing environment.",
        }
        self.messages = [
            {"type": "thread.started", "thread_id": "thread"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(self.answer)}},
            {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}},
        ]

    def test_structured_output_matches_assessment_contract(self):
        schema = json.loads((ROOT / "config/pitch_expectation_output_schema.json").read_text())
        self.assertEqual(set(schema["required"]), ASSESSMENT_KEYS)
        self.assertEqual(set(schema["properties"]), ASSESSMENT_KEYS)
        self.assertEqual(schema["properties"]["reasoning_basis"]["minItems"], 1)
        self.assertEqual(set(schema["properties"]["reasoning_basis"]["items"]["enum"]), BASES)
        for field, allowed in CATEGORIES.items():
            self.assertEqual(set(schema["properties"][field]["enum"]), allowed)

    def test_complete_tool_free_response_is_schema_valid(self):
        answer, thread = parse_agent_events(self.messages)
        self.assertEqual(thread, "thread")
        self.assertEqual(answer["overall_expected_environment"], "uncertain")

    def test_any_tool_invocation_or_missing_complete_turn_is_rejected(self):
        for events in (
            self.messages[:1] + [{"type": "item.started", "item": {"type": "command_execution"}}] + self.messages[1:],
            self.messages[:-1],
            self.messages + [{"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}}],
            self.messages[:1] + [{"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}}] + self.messages[2:],
        ):
            with self.subTest(events=events), self.assertRaises(ValueError):
                parse_agent_events(events)

    def test_consensus_rejects_incomplete_or_mismatched_pass_provenance(self):
        source_text = "Grass and seam movement."
        source_hash = hashlib.sha256(source_text.encode()).hexdigest()
        release_hash = hashlib.sha256(b"frozen input release").hexdigest()
        payloads = [{
            "cricsheet_match_id": "m1", "match_date": "2023-01-01",
            "event_name": "event", "competition_type": "league", "venue": "ground",
            "city": "city", "team_1": "one", "team_2": "two",
            "source_url": "https://example.org/p", "source_title": "Preview",
            "published_at_utc": "2022-12-31T00:00:00+00:00",
            "accessed_at_utc": "2023-01-01T00:00:00+00:00",
            "scheduled_start_utc": "2023-01-02T00:00:00+00:00",
            "source_text": source_text, "source_hash": source_hash,
        }]
        assessment = {
            "batting_expectation": "uncertain", "pace_seam_expectation": "uncertain",
            "spin_expectation": "uncertain", "slow_two_paced_expectation": "uncertain",
            "overall_expected_environment": "uncertain", "confidence": 25,
            "evidence": "Mixed cues.", "reasoning_basis": ["physical_surface_description"],
            "rationale": "No favored environment.",
        }
        passes = {label: [{
            "cricsheet_match_id": "m1", "assessor_id": label,
            "model_name": "gpt-5.6-luna" if label in "AB" else "gpt-6-sol",
            "model_version": "version", "reasoning_effort": "high", "prompt_hash": rubric_hash(),
            "source_hash": source_hash, "source_release_sha256": release_hash, "run_id": label,
            "assessed_at_utc": "2024-01-01T00:00:00+00:00", "assessment": assessment,
        }] for label in "ABC"}
        manifests = {label: {
            "assessor_id": label, "run_id": label,
            "model_name": "gpt-5.6-luna" if label in "AB" else "gpt-6-sol",
            "input_sha256": release_hash, "prompt_hash": rubric_hash(),
        } for label in "ABC"}
        input_manifest = {"input_sha256": release_hash, "source_protocol_version": "PE-006-v1"}
        validate_pass_release(payloads, passes, manifests, input_manifest)
        cases = []
        cases.append(({**passes, "C": []}, manifests))
        cases.append(({**passes, "C": [dict(passes["C"][0], cricsheet_match_id="extra")]}, manifests))
        bad_hash = {**passes, "B": [dict(passes["B"][0], source_release_sha256="other")]}
        cases.append((bad_hash, manifests))
        bad_prompt = {**passes, "B": [dict(passes["B"][0], prompt_hash="other")]}
        cases.append((bad_prompt, manifests))
        cases.append((passes, {**manifests, "B": dict(manifests["B"], input_sha256="other")}))
        cases.append((passes, {**manifests, "B": dict(manifests["B"], prompt_hash="other")}))
        repeated_run = {**manifests, "B": dict(manifests["B"], run_id="A")}
        cases.append((passes, repeated_run))
        for bad_passes, bad_manifests in cases:
            with self.subTest(bad_passes=bad_passes, bad_manifests=bad_manifests):
                with self.assertRaises(ValueError):
                    validate_pass_release(payloads, bad_passes, bad_manifests, input_manifest)

    def test_consensus_requires_pass_files_to_match_manifest_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pass.jsonl"
            path.write_text('{"row":1}\n')
            manifest = {"output_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            validate_pass_output_hash(manifest, path)
            path.write_text('{"row":2}\n')
            with self.assertRaises(ValueError):
                validate_pass_output_hash(manifest, path)


if __name__ == "__main__":
    unittest.main()
