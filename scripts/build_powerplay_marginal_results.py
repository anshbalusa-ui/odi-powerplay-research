#!/usr/bin/env python3
"""Build fixed-model, standardized powerplay association outputs for the unlocked cohort."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.model_table import FORBIDDEN_PREDICTORS  # noqa: E402
from odi_powerplay.modeling import fit_model, make_model_specs, predict_model, validate_model_specs  # noqa: E402


def read_unlocked_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        positions = {field: index for index, field in enumerate(header)}
        required = {"match_id", "split", "pp_runs", "pp_wickets", "batting_team_won"}
        missing = sorted(required - positions.keys())
        if missing:
            raise ValueError(f"Model table is missing required fields: {', '.join(missing)}")
        rows: list[dict[str, str]] = []
        for values in reader:
            if values[positions["split"]] != "locked_test":
                rows.append(dict(zip(header, values, strict=True)))
    if not rows:
        raise ValueError("No unlocked model rows found")
    return rows


def empirical_quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(len(ordered) - 1, lower + 1)
    weight = position - lower
    return ordered[lower] + weight * (ordered[upper] - ordered[lower])


def quantile_grid(values: list[float], *, integer: bool) -> list[float | int]:
    grid: list[float | int] = []
    for probability in (0.1, 0.25, 0.5, 0.75, 0.9):
        value = empirical_quantile(values, probability)
        candidate: float | int = int(round(value)) if integer else round(value, 6)
        if candidate not in grid:
            grid.append(candidate)
    return grid


def standardized_probability(
    model: Any,
    spec: Any,
    rows: list[dict[str, str]],
    *,
    runs: float | int | None = None,
    wickets: float | int | None = None,
) -> float:
    counterfactual = []
    for row in rows:
        updated = dict(row)
        if runs is not None:
            updated["pp_runs"] = str(runs)
        if wickets is not None:
            updated["pp_wickets"] = str(wickets)
        counterfactual.append(updated)
    probabilities = predict_model(spec, model, counterfactual)
    return sum(probabilities) / len(probabilities)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-table",
        type=Path,
        default=ROOT / "data/processed/model_team_innings.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/tables/powerplay_marginal_results.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/powerplay_marginal_results.json",
    )
    args = parser.parse_args()

    rows = read_unlocked_rows(args.model_table)
    spec = next(
        spec for spec in make_model_specs(include_pitch=False) if spec.name == "powerplay_benchmark"
    )
    validate_model_specs([spec], forbidden=FORBIDDEN_PREDICTORS)
    model = fit_model(spec, rows)
    run_grid = quantile_grid([float(row["pp_runs"]) for row in rows], integer=True)
    wicket_grid = quantile_grid([float(row["pp_wickets"]) for row in rows], integer=True)

    output: list[dict[str, object]] = []
    for run_value in run_grid:
        output.append(
            {
                "scenario": "runs_marginal",
                "pp_runs": run_value,
                "pp_wickets": "observed",
                "standardized_predicted_win_probability": standardized_probability(
                    model, spec, rows, runs=run_value
                ),
                "grid_basis": "empirical quantile of unlocked rows",
            }
        )
    for wicket_value in wicket_grid:
        output.append(
            {
                "scenario": "wickets_marginal",
                "pp_runs": "observed",
                "pp_wickets": wicket_value,
                "standardized_predicted_win_probability": standardized_probability(
                    model, spec, rows, wickets=wicket_value
                ),
                "grid_basis": "empirical quantile of unlocked rows",
            }
        )
    for run_value in run_grid:
        for wicket_value in wicket_grid:
            output.append(
                {
                    "scenario": "joint_grid",
                    "pp_runs": run_value,
                    "pp_wickets": wicket_value,
                    "standardized_predicted_win_probability": standardized_probability(
                        model, spec, rows, runs=run_value, wickets=wicket_value
                    ),
                    "grid_basis": "empirical quantile of unlocked rows",
                }
            )

    run_mid = run_grid[len(run_grid) // 2]
    wicket_mid = wicket_grid[len(wicket_grid) // 2]
    run_low = run_grid[1] if len(run_grid) > 1 else run_grid[0]
    run_high = run_grid[-2] if len(run_grid) > 1 else run_grid[0]
    wicket_low = wicket_grid[1] if len(wicket_grid) > 1 else wicket_grid[0]
    wicket_high = wicket_grid[-2] if len(wicket_grid) > 1 else wicket_grid[0]
    run_low_probability = standardized_probability(model, spec, rows, runs=run_low, wickets=wicket_mid)
    run_high_probability = standardized_probability(model, spec, rows, runs=run_high, wickets=wicket_mid)
    wicket_low_probability = standardized_probability(
        model, spec, rows, runs=run_mid, wickets=wicket_low
    )
    wicket_high_probability = standardized_probability(
        model, spec, rows, runs=run_mid, wickets=wicket_high
    )

    fields = list(output[0])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)
    summary = {
        "analysis_scope": "primary_mens_odi_2015_through_2024_unlocked",
        "locked_test_scored": False,
        "locked_test_outcomes_loaded": False,
        "model": spec.name,
        "model_fit_rows": len(rows),
        "model_fit_matches": len({row["match_id"] for row in rows}),
        "run_quantile_grid": run_grid,
        "wicket_quantile_grid": wicket_grid,
        "contrasts": {
            "runs_low_to_high_at_middle_wickets": {
                "low_runs": run_low,
                "high_runs": run_high,
                "middle_wickets": wicket_mid,
                "low_probability": run_low_probability,
                "high_probability": run_high_probability,
                "difference": run_high_probability - run_low_probability,
            },
            "wickets_low_to_high_at_middle_runs": {
                "middle_runs": run_mid,
                "low_wickets": wicket_low,
                "high_wickets": wicket_high,
                "low_probability": wicket_low_probability,
                "high_probability": wicket_high_probability,
                "difference": wicket_high_probability - wicket_low_probability,
            },
        },
        "interpretation_guardrail": (
            "Model-standardized observational association; not a causal effect or coaching rule."
        ),
        "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
