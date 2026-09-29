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


def validate_pass_output_hash(manifest: dict, path: Path) -> None:
    if manifest.get("output_sha256") != sha256(path):
        raise ValueError(f"assessor output hash does not match manifest: {path.name}")

def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def cross_model_consensus_summary(answers: list[dict[str, str]]) -> dict:
    """Compare Sol (C) with either Luna (A/B), separately from 2/3 majority."""
    if not answers:
        return {
            "cross_model_consensus": {"count": 0, "proportion": None},
            "ordinary_majority": {"count": 0, "proportion": None},
            "three_of_three": {"count": 0, "proportion": None},
        }
    cross = sum(row["C"] in {row["A"], row["B"]} for row in answers)
    majority = sum(Counter(row.values()).most_common(1)[0][1] >= 2 for row in answers)
    unanimous = sum(len(set(row.values())) == 1 for row in answers)
    n = len(answers)
    return {
        "cross_model_consensus": {"count": cross, "proportion": cross / n},
        "ordinary_majority": {"count": majority, "proportion": majority / n},
        "three_of_three": {"count": unanimous, "proportion": unanimous / n},
    }


def validate_pass_release(payloads: list[dict], passes: dict[str, list[dict]],
                          manifests: dict[str, dict], input_manifest: dict) -> None:
    """Verify complete, independent passes bound to the exact frozen source release."""
    release_hash = input_manifest["input_sha256"]
    if input_manifest.get("source_protocol_version") != "PE-006-v1":
        raise ValueError("source protocol version does not match PE-006-v1")
    if set(passes) != set("ABC") or set(manifests) != set("ABC"):
        raise ValueError("three complete A/B/C passes and manifests are required")
    run_ids = [manifests[label].get("run_id") for label in "ABC"]
    if any(not isinstance(value, str) or not value.strip() for value in run_ids) or len(set(run_ids)) != 3:
        raise ValueError("assessor passes must have distinct nonempty run IDs")
    models = {label: str(manifests[label].get("model_name", "")).lower() for label in "ABC"}
    if ("luna" not in models["A"] or "luna" not in models["B"] or "sol" not in models["C"]):
        raise ValueError("A/B must use Luna and C must use Sol")
    expected_ids = {row["cricsheet_match_id"] for row in payloads}
    if len(expected_ids) != len(payloads):
        raise ValueError("duplicate IDs in frozen input release")
    for label in "ABC":
        manifest = manifests[label]
        if (manifest.get("assessor_id") != label
                or manifest.get("input_sha256") != release_hash
                or manifest.get("prompt_hash") != rubric_hash()):
            raise ValueError(f"assessor {label} manifest provenance mismatch")
        row_ids = [row.get("cricsheet_match_id") for row in passes[label]]
        if len(row_ids) != len(expected_ids) or set(row_ids) != expected_ids:
            raise ValueError(f"assessor {label} ID set differs from frozen inputs")
        for row in passes[label]:
            if (row.get("source_release_sha256") != release_hash
                    or row.get("prompt_hash") != manifest["prompt_hash"]
                    or row.get("run_id") != manifest["run_id"]
                    or row.get("model_name") != manifest.get("model_name")):
                raise ValueError(f"assessor {label} row provenance mismatch")
    validate_passes(payloads, passes, release_hash)

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
        manifest = json.loads(
            (args.input_dir / f"pass_{assessor.lower()}_manifest.json").read_text(encoding="utf-8")
        )
        validate_pass_output_hash(manifest, path)
        if (manifest["assessor_id"] != assessor or manifest["locked_test_scored"] is not False
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
    validate_pass_release(payloads, passes, manifests, input_manifest)
    indexed = {label: {row["cricsheet_match_id"]: row for row in rows}
               for label, rows in passes.items()}
    assessable_statuses = [row for row in input_manifest["sources"]
                           if row.get("source_status") == "assessable"]
    route_by_id = {
        row["cricsheet_match_id"]: row["source_access_route"]
        for row in assessable_statuses
    }
    payload_ids = {row["cricsheet_match_id"] for row in payloads}
    if (len(route_by_id) != len(assessable_statuses) or set(route_by_id) != payload_ids
            or any(route not in {"live_original", "archived_original"}
                   for route in route_by_id.values())):
        raise ValueError("assessable source routes do not match the frozen inputs")
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
            "rubric_version": rubric_version(), "source_access_route": route_by_id[key],
            **{field: result[field] for field in CATEGORIES},
            "confidence": result["confidence"],
            **{field: int(result[field]) for field in (
                "primary_eligible", "broad_eligible", "high_confidence_eligible",
                "unanimous_eligible")},
            "overall_agreement_count": result["agreement_by_field"]["overall_expected_environment"],
            "cross_model_consensus": int(
                indexed["C"][key]["assessment"]["overall_expected_environment"] in {
                    indexed["A"][key]["assessment"]["overall_expected_environment"],
                    indexed["B"][key]["assessment"]["overall_expected_environment"]}),
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
    field_stability = {}
    for field in CATEGORIES:
        values = [{
            label: indexed[label][row["cricsheet_match_id"]]["assessment"][field]
            for label in "ABC"
        } for row in release]
        field_stability[field] = cross_model_consensus_summary(values)
    route_stability = {}
    for route in ("live_original", "archived_original"):
        route_rows = [row for row in release if row["source_access_route"] == route]
        route_answers = [{
            label: indexed[label][row["cricsheet_match_id"]]["assessment"]["overall_expected_environment"]
            for label in "ABC"
        } for row in route_rows]
        route_stability[route] = {
            "n": len(route_rows),
            **cross_model_consensus_summary(route_answers),
            "by_field": {
                field: cross_model_consensus_summary([{
                    label: indexed[label][row["cricsheet_match_id"]]["assessment"][field]
                    for label in "ABC"
                } for row in route_rows])
                for field in CATEGORIES
            },
        }
    excluded_sources = [row for row in input_manifest["sources"]
                        if row.get("source_status") != "assessable"]
    source_universe_counts = {
        key: input_manifest[key] for key in (
            "eligible_source_count", "source_statuses", "source_access_route_counts",
            "year_counts", "provider_counts", "split_counts",
        ) if key in input_manifest
    }
    source_universe_counts["excluded_status_counts"] = dict(sorted(Counter(
        row.get("source_status", "unknown") for row in excluded_sources).items()))
    report = {
        "measurement": "independent model-assessment agreement, not true pitch accuracy",
        "locked_test_scored": False,
        "source_protocol_version": input_manifest["source_protocol_version"],
        "input_sha256": input_manifest["input_sha256"],
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
        "cross_model_consensus": cross_model_consensus_summary([{
            label: indexed[label][row["cricsheet_match_id"]]["assessment"]["overall_expected_environment"]
            for label in "ABC"
        } for row in release]),
        "cross_model_consensus_by_field": field_stability,
        "assessment_stability_by_source_route": route_stability,
        "outcome_blind_source_universe_counts": source_universe_counts,
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
            "source_access_route", "overall_expected_environment", "confidence",
            "overall_agreement_count", "cross_model_consensus")},
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
