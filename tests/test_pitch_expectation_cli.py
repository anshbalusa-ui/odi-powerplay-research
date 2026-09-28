"""CLI assessment must never accept tool use, peer data or malformed final answers."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import ASSESSMENT_KEYS, BASES, CATEGORIES  # noqa: E402
from run_pitch_expectation_agents_codex import parse_agent_events  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
