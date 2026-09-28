#!/usr/bin/env python3
"""Audit exactly what can enter an assessor, without opening outcomes or old codes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import (  # noqa: E402
    CONTAMINATION, INPUT_KEYS, _utc, latest_publication_utc, rubric_hash, rubric_version,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, default=ROOT / "artifacts/pitch_expectations/inputs.jsonl")
    parser.add_argument("--manifest", type=Path, default=ROOT / "artifacts/pitch_expectations/input_manifest.json")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/tables/pitch_expectation_leakage_audit.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    problems = []
    if (manifest.get("locked_test_scored") is not False
            or manifest.get("rubric_sha256") != rubric_hash()
            or manifest.get("rubric_version") != rubric_version()):
        problems.append("rubric or locked-test manifest mismatch")
    if hashlib.sha256(args.inputs.read_bytes()).hexdigest() != manifest.get("input_sha256"):
        problems.append("input content hash mismatch")
    rows = [json.loads(line) for line in args.inputs.read_text(encoding="utf-8").splitlines()]
    if len(rows) != manifest.get("assessable_count"):
        problems.append("assessable row count mismatch")
    ids = set()
    for row in rows:
        key = row.get("cricsheet_match_id", "")
        if not key or key in ids:
            problems.append(f"duplicate or empty source ID: {key}")
        ids.add(key)
        if set(row) != INPUT_KEYS:
            problems.append(f"{key}: forbidden/missing payload key")
            continue
        if not row["source_text"].strip() or CONTAMINATION.search(row["source_text"]):
            problems.append(f"{key}: source text absent or obviously contaminated")
        if CONTAMINATION.search(row["source_title"]):
            problems.append(f"{key}: source title looks post-match")
        if hashlib.sha256(row["source_text"].encode("utf-8")).hexdigest() != row["source_hash"]:
            problems.append(f"{key}: source content hash mismatch")
        if latest_publication_utc(row["published_at_utc"]) >= _utc(row["scheduled_start_utc"]):
            problems.append(f"{key}: source not before scheduled start")
    audit = {
        "locked_test_scored": False,
        "input_sha256": manifest.get("input_sha256"),
        "rubric_sha256": rubric_hash(),
        "rubric_version": rubric_version(),
        "assessment_payload_count": len(rows),
        "allowlisted_keys": sorted(INPUT_KEYS),
        "forbidden_key_count": sum(bool(set(row) - INPUT_KEYS) for row in rows),
        "issues": problems,
        "passed_structural_blinding_audit": not problems,
        "content_review_limitation": "Automated checks cannot establish that a live article is unamended; source reviewers must certify pre-match-only text before assessment.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"assessment_payload_count": len(rows), "issues": problems,
                      "locked_test_scored": False}, indent=2))
    if problems:
        raise SystemExit("assessor input leakage audit failed")


if __name__ == "__main__":
    main()
