#!/usr/bin/env python3
"""Plan or run the pitch interaction analysis behind reliability gates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.modeling import make_model_specs  # noqa: E402
from odi_powerplay.pitch import PITCH_FIELDS  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate_status(
    reliability_path: Path,
    reconciliation_path: Path,
    model_table_path: Path,
    model_manifest_path: Path,
) -> dict[str, object]:
    reasons: list[str] = []
    reliability: dict[str, object] = {}
    if not reliability_path.exists():
        reasons.append("reliability summary is not available")
    else:
        reliability = json.loads(reliability_path.read_text(encoding="utf-8"))
        if int(reliability.get("validation_issue_count", 0)) != 0:
            reasons.append("reliability input validation has unresolved issues")
        if not bool(reliability.get("meets_minimum_double_coding_target", False)):
            reasons.append("independent double-coding target is not met")
    reconciliation_rows: list[dict[str, str]] = []
    if not reconciliation_path.exists():
        reasons.append("reconciliation worksheet is not available")
    else:
        reconciliation_rows = read_csv(reconciliation_path)
        if not reconciliation_rows:
            reasons.append("reconciliation worksheet has no paired rows")
        pending = [
            row.get("cricsheet_match_id", "")
            for row in reconciliation_rows
            if row.get("reconciliation_status", "") == "pending"
        ]
        if pending:
            reasons.append(f"reconciliation has {len(pending)} pending rows")
        for row in reconciliation_rows:
            if row.get("reconciliation_status") == "completed":
                if not row.get("reconciled_by", "").strip():
                    reasons.append(
                        f"{row.get('cricsheet_match_id', '')}: completed row lacks reconciled_by"
                    )
                if not row.get("reconciled_at_utc", "").strip():
                    reasons.append(
                        f"{row.get('cricsheet_match_id', '')}: completed row lacks reconciled_at_utc"
                    )
                if not row.get("reconciliation_note", "").strip():
                    reasons.append(
                        f"{row.get('cricsheet_match_id', '')}: completed row lacks reconciliation_note"
                    )
            if row.get("reconciliation_status") not in {"completed", "no_change_required"}:
                reasons.append(
                    f"{row.get('cricsheet_match_id', '')}: unsupported reconciliation status"
                )
            for field in PITCH_FIELDS:
                if f"reconciled_{field}" not in row:
                    reasons.append(
                        f"{row.get('cricsheet_match_id', '')}: missing reconciled_{field}"
                    )
    if not model_table_path.exists():
        reasons.append("reconciled model table is not available")
    if not model_manifest_path.exists():
        reasons.append("reconciled model-table manifest is not available")
    else:
        manifest = json.loads(model_manifest_path.read_text(encoding="utf-8"))
        if manifest.get("reconciled_pitch_release") is not True:
            reasons.append("model table was not built from a reconciliation release")
        expected_sha256 = str(manifest.get("pitch_model_table_sha256", "")).strip()
        if expected_sha256 != sha256(model_table_path):
            reasons.append("model-table hash does not match its manifest")
    return {
        "passed": not reasons,
        "reasons": reasons,
        "reliability_summary": str(reliability_path),
        "reconciliation_worksheet": str(reconciliation_path),
        "model_table": str(model_table_path),
        "model_manifest": str(model_manifest_path),
        "paired_reconciliation_rows": len(reconciliation_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-table",
        type=Path,
        default=ROOT / "data/processed/model_team_innings_pitch.csv",
    )
    parser.add_argument(
        "--model-manifest",
        type=Path,
        default=ROOT / "data/processed/model_table_manifest.json",
    )
    parser.add_argument(
        "--reliability-summary",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_reliability.json",
    )
    parser.add_argument(
        "--reconciliation-input",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_reconciliation_worksheet.csv",
    )
    parser.add_argument(
        "--plan-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_interaction_analysis_plan.json",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts/models/pitch_final_validation_frozen",
    )
    parser.add_argument(
        "--predictions-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_final_validation_predictions.csv",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--rolling-origin-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_final_rolling_origin_metrics.json",
    )
    args = parser.parse_args()
    args.manifest_output = args.manifest_output or args.output_dir / "manifest.json"

    gate = gate_status(
        args.reliability_summary,
        args.reconciliation_input,
        args.model_table,
        args.model_manifest,
    )
    specs = make_model_specs(include_pitch=True)
    plan = {
        "analysis": "prespecified pitch effect interaction analysis",
        "status": (
            "ready"
            if gate["passed"]
            else "blocked_until_reliability_reconciliation_and_release_provenance"
        ),
        "locked_test_scored": False,
        "model_table": str(args.model_table),
        "model_manifest": str(args.model_manifest),
        "model_specs": [
            {
                "name": spec.name,
                "numeric_features": list(spec.numeric_features),
                "categorical_features": list(spec.categorical_features),
                "interaction_features": [list(pair) for pair in spec.interaction_features],
                "estimator": spec.estimator,
            }
            for spec in specs
        ],
        "gate": gate,
        "execution_command": [
            sys.executable,
            "scripts/train_models.py",
            "--fit-without-locked-test",
            "--input",
            str(args.model_table),
            "--model-dir",
            str(args.output_dir),
            "--predictions-output",
            str(args.predictions_output),
            "--manifest-output",
            str(args.manifest_output),
            "--rolling-origin-output",
            str(args.rolling_origin_output),
        ],
    }
    args.plan_output.parent.mkdir(parents=True, exist_ok=True)
    args.plan_output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.execute:
        if not gate["passed"]:
            print(json.dumps(plan, indent=2, sort_keys=True))
            return 2
        args.output_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(plan["execution_command"], cwd=ROOT, check=True)
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
