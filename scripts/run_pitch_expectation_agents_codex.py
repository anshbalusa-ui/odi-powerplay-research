#!/usr/bin/env python3
"""Run one independent, tool-free Codex CLI assessor pass on frozen inputs.

The requested model identifier is routed by the installed Codex CLI. The CLI
provides no provider-side model build/version identifier; record that limitation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import (  # noqa: E402
    INPUT_KEYS, RUBRIC, assessment_input, canonical_json, rubric_hash, rubric_version, validate_assessment,
)

CLI = Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex")
SCHEMA = ROOT / "config/pitch_expectation_output_schema.json"


def parse_agent_events(events: list[dict]) -> tuple[dict, str]:
    """Fail closed if CLI invokes tools or does not complete exactly one answer."""
    thread_ids = [event["thread_id"] for event in events if event.get("type") == "thread.started"]
    completed = [event for event in events if event.get("type") == "turn.completed"]
    messages = []
    for event in events:
        if event.get("type") in {"item.started", "item.completed", "item.updated"}:
            item = event.get("item", {})
            if item.get("type") != "agent_message":
                raise ValueError("assessor invoked a tool or produced a non-message item")
            if event["type"] == "item.completed":
                messages.append(item.get("text", ""))
        if event.get("type") in {"turn.failed", "error"}:
            raise ValueError("assessor turn failed")
    if len(thread_ids) != 1 or len(completed) != 1 or len(messages) != 1:
        raise ValueError("assessor did not complete one tool-free answer")
    answer = json.loads(messages[0])
    validate_assessment(answer)
    return answer, thread_ids[0]


def assess(row: dict, rubric: str, model: str, assessor: str, run_id: str,
           source_release_sha256: str) -> dict:
    # No repository path or peer output is provided to the child process.
    with tempfile.TemporaryDirectory(prefix="odi-pitch-assessor-") as cwd:
        process = subprocess.run([
            str(CLI), "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "--skip-git-repo-check", "-C", cwd, "-s", "read-only",
            "-m", model, "-c", 'model_reasoning_effort="high"', "--json",
            "--output-schema", str(SCHEMA), rubric + "\n" + canonical_json(row),
        ], capture_output=True, text=True, timeout=240, check=False)
    if process.returncode:
        raise RuntimeError(f"Codex CLI exited {process.returncode} for {row['cricsheet_match_id']}: "
                           f"{process.stderr[-600:]}")
    events = [json.loads(line) for line in process.stdout.splitlines() if line.strip()]
    answer, _ = parse_agent_events(events)
    return {
        "cricsheet_match_id": row["cricsheet_match_id"], "assessor_id": assessor,
        "model_name": model, "model_version": model,
        "reasoning_effort": "high", "prompt_hash": rubric_hash(),
        "source_hash": row["source_hash"], "source_release_sha256": source_release_sha256,
        "run_id": run_id,
        "assessed_at_utc": datetime.now(timezone.utc).isoformat(), "assessment": answer,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assessor", choices=("A", "B", "C"), required=True)
    parser.add_argument("--model", choices=("gpt-5.6-luna", "gpt-6-sol"), required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--smoke", action="store_true", help="Assess first row without writing a pass")
    parser.add_argument("--inputs", type=Path, default=ROOT / "artifacts/pitch_expectations/inputs.jsonl")
    parser.add_argument("--input-manifest", type=Path, default=ROOT / "artifacts/pitch_expectations/input_manifest.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/pitch_expectations")
    args = parser.parse_args()
    if args.assessor in "AB" and args.model != "gpt-5.6-luna" or args.assessor == "C" and args.model != "gpt-6-sol":
        raise ValueError("A and B require Luna; C requires Sol")
    if args.workers not in range(1, 7):
        raise ValueError("workers must be between 1 and 6")
    output = args.output_dir / f"pass_{args.assessor.lower()}.jsonl"
    manifest_path = args.output_dir / f"pass_{args.assessor.lower()}_manifest.json"
    if not args.smoke and (output.exists() or manifest_path.exists()):
        raise FileExistsError(f"existing pass {args.assessor} must not be overwritten")
    manifest = json.loads(args.input_manifest.read_text(encoding="utf-8"))
    if (manifest["locked_test_scored"] is not False
            or manifest["rubric_sha256"] != rubric_hash()
            or manifest["rubric_version"] != rubric_version()
            or manifest.get("source_protocol_version") != "PE-006-v1"):
        raise ValueError("input manifest does not match frozen source protocol, rubric or lock")
    if hashlib.sha256(args.inputs.read_bytes()).hexdigest() != manifest["input_sha256"]:
        raise ValueError("sanitized inputs changed after manifest")
    rows = [json.loads(line) for line in args.inputs.read_text(encoding="utf-8").splitlines()]
    if not rows or len(rows) != manifest["assessable_count"] or len({row["cricsheet_match_id"] for row in rows}) != len(rows):
        raise ValueError("refusing empty, incomplete or duplicate input release")
    for row in rows:
        if set(row) != INPUT_KEYS:
            raise ValueError("assessor input contains forbidden fields")
        assessment_input(row, row, row["source_text"], row["source_hash"])
    cli_version = subprocess.run([str(CLI), "--version"], capture_output=True, text=True, check=True).stdout.strip()
    rubric = RUBRIC.read_text(encoding="utf-8")
    if args.smoke:
        record = assess(rows[0], rubric, args.model, args.assessor, args.run_id,
                        manifest["input_sha256"])
        print(canonical_json({"smoke": "valid tool-free answer", "model_requested": args.model,
                              "cli_version": cli_version, "match_id": record["cricsheet_match_id"]}))
        return
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(
            lambda row: assess(row, rubric, args.model, args.assessor, args.run_id,
                               manifest["input_sha256"]), rows))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # No partial pass is persisted on any error; never overwrite a completed pass.
    with output.open("x", encoding="utf-8") as handle:
        handle.write("".join(canonical_json(row) + "\n" for row in records))
    metadata = {
        "assessor_id": args.assessor, "model_name": args.model,
        "model_versions": [args.model], "model_version_note": "requested CLI route; provider build unavailable",
        "model_identity_source": "requested_route",
        "cli_version": cli_version, "reasoning_effort": "high", "run_id": args.run_id,
        "prompt_hash": rubric_hash(), "rubric_version": rubric_version(),
        "output_schema_sha256": hashlib.sha256(SCHEMA.read_bytes()).hexdigest(),
        "input_sha256": manifest["input_sha256"],
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "sampling_controls_note": "Temperature and seed controls are unsupported by this CLI route.",
        "record_count": len(records), "locked_test_scored": False,
    }
    with manifest_path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(canonical_json({"assessor": args.assessor, "records": len(records),
                          "model_requested": args.model, "cli_version": cli_version,
                          "provider_build_known": False, "locked_test_scored": False}))


if __name__ == "__main__":
    main()
