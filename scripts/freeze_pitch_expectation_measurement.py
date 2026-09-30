#!/usr/bin/env python3
"""Freeze outcome-blind measurement provenance after three complete fresh passes.

This gate never opens match outcomes or approves the separate human evidence audit.
The manifest is write-once; any source, rubric, pass, or consensus change needs a
new release and all three assessor passes again.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import (  # noqa: E402
    CATEGORIES, INPUT_KEYS, RUBRIC, audit_sample, consensus as mechanical_consensus,
    rubric_hash, rubric_version,
)
from build_pitch_expectation_consensus import (  # noqa: E402
    records, sha256, validate_pass_output_hash, validate_pass_release,
)
from build_pitch_expectation_inputs import _source_coverage  # noqa: E402

PROTOCOL_VERSION = "PE-006-v1"
CONSENSUS_VERSION = "per_field_two_of_three_v1"


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected an object")
    return value


def _csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def freeze(
    input_dir: Path, source_screen: Path, archive_index: Path, consensus: Path,
    agreement: Path, worksheet: Path, leakage_audit: Path, output: Path,
) -> dict:
    if output.exists():
        raise FileExistsError(f"frozen measurement manifest already exists: {output}")
    inputs = input_dir / "inputs.jsonl"
    source_manifest = _json(input_dir / "input_manifest.json")
    if (source_manifest.get("locked_test_scored") is not False
            or source_manifest.get("source_protocol_version") != PROTOCOL_VERSION
            or source_manifest.get("input_sha256") != sha256(inputs)
            or source_manifest.get("source_screen_sha256") != sha256(source_screen)
            or source_manifest.get("rubric_sha256") != rubric_hash()
            or source_manifest.get("rubric_version") != rubric_version()):
        raise ValueError("source screen, prompt or locked outcome boundary changed")
    payloads = records(inputs)
    if (not payloads or len(payloads) != source_manifest.get("assessable_count")
            or any(set(row) != INPUT_KEYS for row in payloads)):
        raise ValueError("frozen assessor release is empty, incomplete or contaminated")
    sources = source_manifest.get("sources", [])
    if (len(sources) != source_manifest.get("registry_candidate_count")
            or len({row["cricsheet_match_id"] for row in sources}) != len(sources)
            or dict(sorted(Counter(row["source_status"] for row in sources).items()))
            != source_manifest.get("source_statuses")
            or _source_coverage(sources) != source_manifest.get("source_coverage_counts")
            or dict(sorted(Counter(row["source_access_route"] for row in sources).items()))
            != source_manifest.get("source_access_route_counts")):
        raise ValueError("source dispositions or archive/live coverage changed")
    audit = _json(leakage_audit)
    if (audit.get("passed_structural_blinding_audit") is not True
            or audit.get("issues") != []
            or audit.get("locked_test_scored") is not False
            or audit.get("input_sha256") != source_manifest["input_sha256"]
            or audit.get("source_protocol_version") != PROTOCOL_VERSION):
        raise ValueError("frozen input leakage audit is incomplete or failed")
    manifests = {}
    passes = {}
    for assessor in "ABC":
        path = input_dir / f"pass_{assessor.lower()}.jsonl"
        manifest = _json(input_dir / f"pass_{assessor.lower()}_manifest.json")
        validate_pass_output_hash(manifest, path)
        if (manifest.get("locked_test_scored") is not False
                or manifest.get("rubric_version") != rubric_version()
                or manifest.get("record_count") != len(payloads)):
            raise ValueError(f"pass {assessor} is not a complete locked release")
        manifests[assessor] = manifest
        passes[assessor] = records(path)
    schema_hashes = {manifest.get("output_schema_sha256") for manifest in manifests.values()}
    schema = ROOT / "config/pitch_expectation_output_schema.json"
    if schema_hashes not in ({None}, {sha256(schema)}):
        raise ValueError("assessor output schemas differ or changed")
    validate_pass_release(payloads, passes, manifests, source_manifest)
    for assessor in "ABC":
        versions = manifests[assessor].get("model_versions")
        if (manifests[assessor].get("model_identity_source") != "provider_response"
                or not isinstance(versions, list) or not versions
                or any(not isinstance(version, str) or not version.strip() for version in versions)
                or {row.get("model_version") for row in passes[assessor]} != set(versions)):
            raise ValueError(f"assessor {assessor} lacks a verified provider response model ID")
    agreement_data = _json(agreement)
    if (agreement_data.get("locked_test_scored") is not False
            or agreement_data.get("consensus_sha256") != sha256(consensus)
            or agreement_data.get("input_sha256") != source_manifest["input_sha256"]
            or agreement_data.get("prompt_hash") != rubric_hash()
            or agreement_data.get("source_protocol_version") != PROTOCOL_VERSION
            or agreement_data.get("assessor_manifests") != manifests
            or agreement_data.get("successfully_assessed_count") != len(payloads)):
        raise ValueError("consensus is not bound to all three frozen passes")
    release = _csv(consensus)
    input_ids = [row["cricsheet_match_id"] for row in payloads]
    if len(release) != len(input_ids) or [row["cricsheet_match_id"] for row in release] != input_ids:
        raise ValueError("consensus rows differ from frozen input order or IDs")
    by_input = {row["cricsheet_match_id"]: row for row in payloads}
    by_pass = {
        label: {row["cricsheet_match_id"]: row for row in passes[label]}
        for label in "ABC"
    }
    by_source = {row["cricsheet_match_id"]: row for row in sources}
    for row in release:
        key = row["cricsheet_match_id"]
        expected = mechanical_consensus([by_pass[label][key]["assessment"] for label in "ABC"])
        expected_cross_model = int(
            by_pass["C"][key]["assessment"]["overall_expected_environment"] in {
                by_pass["A"][key]["assessment"]["overall_expected_environment"],
                by_pass["B"][key]["assessment"]["overall_expected_environment"],
            }
        )
        if (row["source_hash"] != by_input[key]["source_hash"]
                or row["source_access_route"] != by_source[key]["source_access_route"]
                or row["prompt_hash"] != rubric_hash()
                or row["rubric_version"] != rubric_version()
                or any(row[field] != expected[field] for field in CATEGORIES)
                or int(row["confidence"]) != expected["confidence"]
                or int(row["overall_agreement_count"]) !=
                expected["agreement_by_field"]["overall_expected_environment"]
                or int(row["cross_model_consensus"]) != expected_cross_model
                or any(int(row[field]) != int(expected[field]) for field in (
                    "primary_eligible", "broad_eligible", "high_confidence_eligible",
                    "unanimous_eligible"
                ))):
            raise ValueError("mechanical consensus differs from the three frozen pass outputs")
    sample_rows = [{**row, "confidence": int(row["confidence"]),
                    "broad_eligible": bool(int(row["broad_eligible"]))} for row in release]
    sample_ids = [row["cricsheet_match_id"] for row in audit_sample(sample_rows, size=15)]
    audit_rows = _csv(worksheet)
    if ([row["cricsheet_match_id"] for row in audit_rows] != sample_ids
            or any(row["source_access_route"] != release[input_ids.index(row["cricsheet_match_id"])]["source_access_route"]
                   for row in audit_rows)):
        raise ValueError("human evidence worksheet differs from prespecified audit sample")
    rubric = _json(RUBRIC)
    if (any(set(rubric["output_schema"].get(field, [])) != allowed
            for field, allowed in CATEGORIES.items())
            or ">=60" not in rubric["consensus"]["primary"]
            or ">=75" not in rubric["consensus"]["high_confidence"]):
        raise ValueError("category definitions or confidence thresholds changed")
    excluded = [row for row in sources if row["source_status"] != "assessable"]
    route_coverage = source_manifest["source_coverage_counts"]["by_route"]
    result = {
        "construct": source_manifest["construct"] if "construct" in source_manifest else rubric["construct"],
        "source_release_sha256": source_manifest["input_sha256"],
        "source_screen_sha256": source_manifest["source_screen_sha256"],
        "source_eligibility_protocol_version": PROTOCOL_VERSION,
        "source_registry_sha256": source_manifest.get("source_registry_sha256", {}),
        "archive_index_sha256": sha256(archive_index),
        "canonical_prompt_sha256": rubric_hash(),
        "rubric_version": rubric_version(),
        "assessor_manifests": manifests,
        "assessor_manifest_sha256": {
            label: sha256(input_dir / f"pass_{label.lower()}_manifest.json") for label in "ABC"
        },
        "consensus_implementation_version": CONSENSUS_VERSION,
        "consensus_implementation_sha256": {
            "core": sha256(ROOT / "src/odi_powerplay/pitch_expectation.py"),
            "builder": sha256(ROOT / "scripts/build_pitch_expectation_consensus.py"),
        },
        "consensus_sha256": sha256(consensus),
        "agreement_sha256": sha256(agreement),
        "leakage_audit_sha256": sha256(leakage_audit),
        "confidence_thresholds": {"primary": 60, "high_confidence": 75},
        "category_definitions": {field: rubric["output_schema"][field] for field in CATEGORIES},
        "uncertainty_rule": {"no_two_of_three": "uncertain",
                             "weak_source_evidence": rubric["uncertainty_policy"]},
        "archive_access_route_counts": route_coverage,
        "source_coverage_counts": source_manifest["source_coverage_counts"],
        "excluded_row_dispositions": dict(sorted(Counter(row["source_status"] for row in excluded).items())),
        "excluded_sources": [
            {key: row[key] for key in ("cricsheet_match_id", "source_status", "source_access_route")}
            for row in excluded
        ],
        "human_audit_sample_definition": {
            "method": "deterministic route/provider/disagreement/uncertainty/confidence diversity",
            "target_size": 15, "minimum_archived_if_available": 3,
            "minimum_live_if_available": 3, "selected_match_ids": sample_ids,
            "worksheet_sha256": sha256(worksheet),
            "human_rating_status": "not_approved_by_measurement_manifest",
        },
        "model_identity_requirement": "provider_response",
        "model_identity_limitation": (
            "Provider response model IDs are retained verbatim; an alias does not identify "
            "an independently observed provider-side build. CLI requested routes cannot "
            "satisfy this release's identity requirement."
        ),
        "locked_test_scored": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--source-screen", type=Path, required=True)
    parser.add_argument("--archive-index", type=Path, required=True)
    parser.add_argument("--consensus", type=Path, required=True)
    parser.add_argument("--agreement", type=Path, required=True)
    parser.add_argument("--worksheet", type=Path, required=True)
    parser.add_argument("--leakage-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = freeze(
        args.input_dir, args.source_screen, args.archive_index, args.consensus,
        args.agreement, args.worksheet, args.leakage_audit, args.output,
    )
    print(json.dumps({
        "source_release_sha256": result["source_release_sha256"],
        "assessor_count": len(result["assessor_manifests"]),
        "locked_test_scored": result["locked_test_scored"],
    }, indent=2))


if __name__ == "__main__":
    main()
