#!/usr/bin/env python3
"""Run the unlocked SSAC27 run–wicket trade-off pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from odi_powerplay.tradeoff import PRIMARY_REPS, SEED, VALIDATION_REPS, run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/model_team_innings.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/ssac27_tradeoff"))
    parser.add_argument("--bootstrap-repetitions", type=int, default=PRIMARY_REPS)
    parser.add_argument("--validation-repetitions", type=int, default=VALIDATION_REPS)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    result = run_pipeline(args.input, args.output_dir,
                          bootstrap_repetitions=args.bootstrap_repetitions,
                          validation_repetitions=args.validation_repetitions, seed=args.seed)
    print(json.dumps({"output_dir": str(args.output_dir), "input_rows": result["input_rows"],
                      "development_rows": result["development_rows"],
                      "validation_rows": result["validation_rows"],
                      "locked_rows_read": result["locked_rows_read"]}, indent=2))


if __name__ == "__main__":
    main()
