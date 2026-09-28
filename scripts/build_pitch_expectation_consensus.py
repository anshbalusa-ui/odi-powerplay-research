#!/usr/bin/env python3
"""Build strictly mechanical consensus, model stability diagnostics and human worksheet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import (  # noqa: E402
    CATEGORIES, audit_sample, consensus, pairwise_agreement, rubric_hash, rubric_version, validate_passes,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=ROOT / "artifacts/pitch_expectations")
    parser.add_argument("--consensus-output", type=Path,
                        default=ROOT / "data/processed/pitch_expectation_consensus.csv")
    parser.add_argument("--agreement-output", type=Path,
                        default=ROOT / "artifacts/tables/pitch_expectation_agreement.json")
    parser.add_argument("--worksheet-output", type=Path,
                        default=ROOT / "artifacts/tables/pitch_expectation_human_audit.csv")
    args = parser.parse_args()
    inputs = args.input_dir / "inputs.jsonl"
    input_manifest = json.loads((args.input_dir / "input_manifest.json").read_text(encoding="utf-8"))
    if (input_manifest["locked_test_scored"] is not False
            or input_manifest["input_sha256"] != sha256(inputs)
            or input_manifest["rubric_sha256"] != rubric_hash()
            or input_manifest["rubric_version"] != rubric_version()):
        raise ValueError("sanitized input manifest integrity or lock failure")
    payloads = records(inputs)
    if not payloads:
        raise ValueError("no assessable pre-match sources; do not manufacture consensus")
    passes = {}
    manifests = {}
    for assessor in "ABC":
        path = args.input_dir / f"pass_{assessor.lower()}.jsonl"
        manifest = json.loads((args.input_dir / f"pass_{assessor.lower()}_manifest.json").read_text(encoding="utf-8"))
        if (manifest["assessor_id"] != assessor or manifest["locked_test_scored"] is not False
                or manifest["output_sha256"] != sha256(path)
                or manifest["input_sha256"] != input_manifest["input_sha256"]
                or manifest["prompt_hash"] != rubric_hash()
                or manifest["rubric_version"] != rubric_version()):
            raise ValueError(f"assessor {assessor} manifest does not match frozen inputs")
        passes[assessor] = records(path)
        manifests[assessor] = manifest
    schemas = {manifest.get("output_schema_sha256") for manifest in manifests.values()}
    if len(schemas) != 1:
        raise ValueError("assessor passes used different output schemas")
    if schemas != {None}:
        schema = ROOT / "config/pitch_expectation_output_schema.json"
        if schemas != {sha256(schema)}:
            raise ValueError("assessor output schema changed after assessment")
    validate_passes(payloads, passes)
    indexed = {label: {row["cricsheet_match_id"]: row for row in rows}
               for label, rows in passes.items()}
    release = []
    for payload in payloads:
        key = payload["cricsheet_match_id"]
        assessments = [indexed[label][key]["assessment"] for label in "ABC"]
        result = consensus(assessments)
        release.append({
            "cricsheet_match_id": key, "match_date": payload["match_date"],
            "competition_type": payload["competition_type"],
            "source_url": payload["source_url"], "source_title": payload["source_title"],
            "source_hash": payload["source_hash"], "prompt_hash": rubric_hash(),
            "rubric_version": rubric_version(),
            **{field: result[field] for field in CATEGORIES},
            "confidence": result["confidence"],
            **{field: int(result[field]) for field in (
                "primary_eligible", "broad_eligible", "high_confidence_eligible",
                "unanimous_eligible")},
            "overall_agreement_count": result["agreement_by_field"]["overall_expected_environment"],
        })
    write_csv(args.consensus_output, release, list(release[0]))
    by_split: dict[str, list[dict]] = defaultdict(list)
    for row in release:
        year = int(row["match_date"][:4])
        by_split["locked" if year >= 2025 else "validation" if year == 2024 else "development"].append(row)
    pairwise = {
        f"{left}{right}": {
            field: pairwise_agreement([(indexed[left][row["cricsheet_match_id"]]["assessment"][field],
                                        indexed[right][row["cricsheet_match_id"]]["assessment"][field])
                                       for row in release])
            for field in CATEGORIES
        }
        for left, right in combinations("ABC", 2)
    }
    report = {
        "measurement": "independent model-assessment agreement, not true pitch accuracy",
        "locked_test_scored": False,
        "eligible_source_count": input_manifest["eligible_source_count"],
        "source_statuses": input_manifest["source_statuses"],
        "successfully_assessed_count": len(release),
        "prompt_hash": rubric_hash(),
        "rubric_version": rubric_version(),
        "assessor_manifests": manifests,
        "consensus_sha256": sha256(args.consensus_output),
        "overall_agreement_counts": dict(sorted(Counter(row["overall_agreement_count"] for row in release).items())),
        "unanimous_all_fields_count": sum(row["unanimous_eligible"] for row in release),
        "uncertain_by_field": {field: sum(row[field] == "uncertain" for row in release)
                               for field in CATEGORIES},
        "majority_by_field": {field: sum(consensus([indexed[a][row["cricsheet_match_id"]]["assessment"]
                                                 for a in "ABC"])["agreement_by_field"][field] >= 2
                                   for row in release) for field in CATEGORIES},
        "pairwise_model_assessment_agreement": pairwise,
        "assessor_categories": {label: {field: dict(Counter(row["assessment"][field] for row in rows))
                                          for field in CATEGORIES} for label, rows in passes.items()},
        "category_counts": {field: dict(Counter(row[field] for row in release)) for field in CATEGORIES},
        "confidence_counts": dict(sorted(Counter(row["confidence"] for row in release).items())),
        "confidence_by_assessor": {label: dict(sorted(Counter(row["assessment"]["confidence"]
                                                         for row in rows).items()))
                                   for label, rows in passes.items()},
        "year_counts": dict(sorted(Counter(row["match_date"][:4] for row in release).items())),
        "provider_counts": dict(sorted(Counter(urlparse(row["source_url"]).hostname or ""
                                               for row in release).items())),
        "competition_type_counts": dict(sorted(Counter(row["competition_type"] for row in release).items())),
        "split_counts": {split: len(rows) for split, rows in by_split.items()},
        "split_categories": {split: dict(Counter(row["overall_expected_environment"] for row in rows))
                             for split, rows in by_split.items()},
        "split_primary_categories": {split: dict(Counter(row["overall_expected_environment"]
                                                          for row in rows if row["primary_eligible"]))
                                     for split, rows in by_split.items()},
        "sparse_cells_under_10_matches": {
            split: {category: count for category, count in Counter(
                row["overall_expected_environment"] for row in rows if row["primary_eligible"]
            ).items() if count < 10}
            for split, rows in by_split.items()
        },
        "cohort_pairing_verified": False,
        "note": "Source-match counts only; primary-cohort eligibility and innings pairing require the frozen Cricsheet snapshot before outcome modeling.",
    }
    args.agreement_output.parent.mkdir(parents=True, exist_ok=True)
    args.agreement_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    audited = audit_sample(release, size=15)
    worksheet = [{
        **{field: row[field] for field in (
            "cricsheet_match_id", "match_date", "source_url", "source_title",
            "overall_expected_environment", "confidence", "overall_agreement_count")},
        "assessor_evidence_paraphrases": " | ".join(
            indexed[label][row["cricsheet_match_id"]]["assessment"]["evidence"] for label in "ABC"),
        "pre_match_relevant": "", "evidence_supported": "", "expectation_reasonable": "",
        "leakage_or_hallucination": "", "human_rating_pass_questionable_fail": "", "note": "",
    } for row in audited]
    write_csv(args.worksheet_output, worksheet, list(worksheet[0]))
    print(json.dumps({"successfully_assessed_count": len(release),
                      "worksheet_count": len(worksheet), "locked_test_scored": False}, indent=2))


if __name__ == "__main__":
    main()
