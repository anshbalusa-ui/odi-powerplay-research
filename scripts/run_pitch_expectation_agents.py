#!/usr/bin/env python3
"""Run one isolated assessor pass against strictly sanitized inputs via Responses API."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import (  # noqa: E402
    INPUT_KEYS, RUBRIC, assessment_input, canonical_json, rubric_hash, rubric_version, validate_assessment,
)


def assess(payload: dict, rubric: str, model: str, reasoning_effort: str, token: str) -> tuple[dict, str]:
    """Send exactly the allowlisted row and frozen rubric, never peer/legacy files."""
    request_body = {
        "model": model,
        "reasoning": {"effort": reasoning_effort},
        "input": [
            {"role": "system", "content": rubric},
            {"role": "user", "content": canonical_json(payload)},
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=canonical_json(request_body).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    texts = [content["text"] for item in result.get("output", [])
             if item.get("type") == "message" for content in item.get("content", [])
             if content.get("type") == "output_text"]
    if len(texts) != 1 or not result.get("model"):
        raise ValueError("response lacks a single structured answer or model identity")
    answer = json.loads(texts[0])
    validate_assessment(answer)
    return answer, result["model"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assessor", choices=("A", "B", "C"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", choices=("low", "medium", "high"), required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--inputs", type=Path, default=ROOT / "artifacts/pitch_expectations/inputs.jsonl")
    parser.add_argument("--input-manifest", type=Path, default=ROOT / "artifacts/pitch_expectations/input_manifest.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/pitch_expectations")
    args = parser.parse_args()
    output = args.output_dir / f"pass_{args.assessor.lower()}.jsonl"
    manifest_path = args.output_dir / f"pass_{args.assessor.lower()}_manifest.json"
    if output.exists() or manifest_path.exists():
        raise FileExistsError(f"existing pass {args.assessor} must not be overwritten")
    token = os.environ.get("OPENAI_API_KEY", "")
    if not token:
        raise RuntimeError("OPENAI_API_KEY is required; no simulated assessor or empty pass")
    input_manifest = json.loads(args.input_manifest.read_text(encoding="utf-8"))
    if (input_manifest["locked_test_scored"] is not False
            or input_manifest["rubric_sha256"] != rubric_hash()
            or input_manifest["rubric_version"] != rubric_version()):
        raise ValueError("input manifest does not match frozen rubric or lock")
    if hashlib.sha256(args.inputs.read_bytes()).hexdigest() != input_manifest["input_sha256"]:
        raise ValueError("sanitized inputs changed after manifest")
    rows = [json.loads(line) for line in args.inputs.read_text(encoding="utf-8").splitlines()]
    if not rows or len(rows) != input_manifest["assessable_count"]:
        raise ValueError("refusing empty or incomplete input release")
    if len({row["cricsheet_match_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate match IDs in input release")
    rubric = RUBRIC.read_text(encoding="utf-8")
    records = []
    for row in rows:
        if set(row) != INPUT_KEYS:
            raise ValueError("assessor input contains forbidden fields")
        # Reapply positive projection even if the JSONL input file was substituted.
        row = assessment_input(row, row, row["source_text"], row["source_hash"])
        answer, version = assess(row, rubric, args.model, args.reasoning_effort, token)
        records.append({
            "cricsheet_match_id": row["cricsheet_match_id"], "assessor_id": args.assessor,
            "model_name": args.model, "model_version": version,
            "reasoning_effort": args.reasoning_effort, "prompt_hash": rubric_hash(),
            "source_hash": row["source_hash"], "run_id": args.run_id,
            "assessed_at_utc": datetime.now(timezone.utc).isoformat(), "assessment": answer,
        })
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # Persist only complete passes; failures cannot masquerade as a valid release.
    output.write_text("".join(canonical_json(row) + "\n" for row in records), encoding="utf-8")
    manifest_path.write_text(json.dumps({
        "assessor_id": args.assessor, "model_name": args.model,
        "model_versions": sorted({row["model_version"] for row in records}),
        "reasoning_effort": args.reasoning_effort, "run_id": args.run_id,
        "prompt_hash": rubric_hash(), "rubric_version": rubric_version(),
        "input_sha256": input_manifest["input_sha256"],
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "record_count": len(records), "locked_test_scored": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Pass {args.assessor}: {len(records)} assessments, model versions verified")


if __name__ == "__main__":
    main()
