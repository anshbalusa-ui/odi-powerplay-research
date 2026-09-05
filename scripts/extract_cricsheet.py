#!/usr/bin/env python3
"""CLI for extracting ODI powerplay features from Cricsheet JSON files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.extract_cricsheet import extract_directory, write_csv  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rows = extract_directory(args.input_dir)
    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} team-innings rows to {args.output}")


if __name__ == "__main__":
    main()

