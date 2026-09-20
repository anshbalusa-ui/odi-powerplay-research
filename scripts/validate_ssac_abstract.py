#!/usr/bin/env python3
"""Validate a draft SSAC27 abstract against canonical evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.abstract_validation import validate_ssac_abstract  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abstract", type=Path, required=True)
    parser.add_argument(
        "--evidence",
        type=Path,
        default=ROOT / "artifacts/abstract/ssac27_evidence.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/abstract/ssac27_validation.json",
    )
    args = parser.parse_args()

    text = args.abstract.read_text(encoding="utf-8")
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    result = validate_ssac_abstract(text, evidence)
    result["abstract"] = str(args.abstract)
    result["evidence"] = str(args.evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(not result["valid"])


if __name__ == "__main__":
    raise SystemExit(main())
