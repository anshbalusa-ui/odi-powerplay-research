"""Prespecified unlocked-cohort ODI run–wicket trade-off analysis."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from datetime import date as calendar_date
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from .evaluation import (
    calibration_coefficients,
    calibration_table,
    cluster_bootstrap_metrics,
    compute_metrics,
)
from .modeling import ModelSpec, fit_model, predict_model

SEED = 20250905
PRIMARY_REPS = 1000
VALIDATION_REPS = 2000
NUMERIC = (
    "pp_runs", "pp_wickets", "batting_first", "batting_team_won_toss", "year",
    "elo_difference", "team_prior_matches", "opponent_prior_matches",
    "team_prior20_win_rate", "opponent_prior20_win_rate",
)
CATEGORICAL = ("venue", "rule_era", "competition_type", "toss_decision")
VENUE_NUMERIC = (
    "venue_history_available", "venue_prior_matches", "venue_prior_pp_runs_mean",
    "venue_prior_pp_wickets_mean",
)
PRIMARY_INTERACTIONS = (
    ("pp_runs", "batting_first"), ("pp_wickets", "batting_first"),
    ("pp_runs", "elo_difference"), ("pp_wickets", "elo_difference"),
    ("pp_runs", "venue_prior_pp_runs_mean"), ("pp_wickets", "venue_prior_pp_runs_mean"),
)


def assert_unlocked_rows(rows: Iterable[dict[str, Any]]) -> None:
    """Fail closed before fitting if an input includes locked-era rows."""
    for row in rows:
        raw_date = str(row.get("match_date", ""))
        split = str(row.get("split", ""))
        try:
            parsed = calendar_date.fromisoformat(raw_date)
        except ValueError as error:
            raise ValueError("unverified match date forbidden in tradeoff analysis") from error
        if parsed.isoformat() != raw_date or parsed < calendar_date(2015, 1, 1):
            raise ValueError("unverified match date forbidden in tradeoff analysis")
        if parsed >= calendar_date(2025, 1, 1) or split in {"locked_test", "locked", "test"}:
            raise ValueError("locked-period row forbidden in tradeoff analysis")
        if (split == "development" and parsed.year > 2023
                or split == "validation" and parsed.year != 2024):
            raise ValueError("unverified chronological split in tradeoff analysis")
        if split not in {"development", "validation"}:
            raise ValueError(f"unexpected split for unlocked analysis: {split!r}")


def _number(row: dict[str, Any], name: str) -> float | None:
    value = row.get(name)
    if value in (None, ""):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _stats(rows: Sequence[dict[str, Any]], name: str) -> tuple[float, float, float]:
    values = sorted(v for row in rows if (v := _number(row, name)) is not None)
    if not values:
        raise ValueError(f"development feature {name} has no observed values")
    median = _quantile(values, 0.5)
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
    return mean, sd, median


def _quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires values")
    ordered = sorted(values)
    at = (len(ordered) - 1) * probability
    lower, upper = math.floor(at), math.ceil(at)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (at - lower)


def local_support(
    rows: Sequence[dict[str, Any]], *, innings: int, wickets: int, elo: float,
    venue_runs: float, elo_mean: float, elo_sd: float, venue_mean: float,
    venue_sd: float, minimum_neighbors: int = 20,
) -> dict[str, Any]:
    """Apply the frozen one-SD, exact-wicket support rule and 5–95% run envelope."""
    if elo_sd <= 0 or venue_sd <= 0:
        return {"supported": False, "reason": "zero_context_standard_deviation", "n": 0}
    neighbors: list[tuple[str, float]] = []
    for index, row in enumerate(rows):
        if _number(row, "batting_first") != innings or _number(row, "pp_wickets") != wickets:
            continue
        e, v = _number(row, "elo_difference"), _number(row, "venue_prior_pp_runs_mean")
        if _number(row, "venue_history_available") != 1 or e is None or v is None:
            continue
        if abs((e - elo_mean) / elo_sd - (elo - elo_mean) / elo_sd) <= 1 and abs((v - venue_mean) / venue_sd - (venue_runs - venue_mean) / venue_sd) <= 1:
            run = _number(row, "pp_runs")
            if run is not None:
                neighbors.append((str(row.get("match_id", index)), run))
    unique_ids = {match_id for match_id, _ in neighbors}
    if len(unique_ids) < minimum_neighbors:
        return {"supported": False, "reason": "insufficient_local_wicket_stratum_matches", "n": len(neighbors), "n_matches": len(unique_ids)}
    values = [run for _, run in neighbors]
    return {"supported": True, "reason": None, "n": len(neighbors), "n_matches": len(unique_ids),
            "run_min": _quantile(values, .05), "run_max": _quantile(values, .95)}


def solve_nonnegative_root(
    function: Callable[[float], float], *, upper_delta: float, tolerance: float = 0.01,
    max_iterations: int = 100,
) -> dict[str, Any]:
    """Deterministic bisection; undefined unless supported endpoints bracket zero."""
    if upper_delta < 0:
        return {"defined": False, "delta": None, "reason": "starting_run_outside_supported_envelope"}
    lo, hi = 0.0, float(upper_delta)
    flo, fhi = function(lo), function(hi)
    if abs(flo) <= 1e-12:
        return {"defined": True, "delta": 0.0, "reason": None, "iterations": 0}
    if abs(fhi) <= 1e-12:
        return {"defined": True, "delta": hi, "reason": None, "iterations": 0}
    if flo * fhi > 0:
        return {"defined": False, "delta": None, "reason": "no_bracketed_nonnegative_root", "lower_value": flo, "upper_value": fhi}
    iterations = 0
    while hi - lo > tolerance and iterations < max_iterations:
        mid = (lo + hi) / 2
        fm = function(mid)
        if abs(fm) <= 1e-12:
            lo = hi = mid
            break
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
        iterations += 1
    return {"defined": True, "delta": (lo + hi) / 2, "reason": None, "iterations": iterations}


def draw_match_bootstrap_rows(
    rows: Sequence[dict[str, Any]], *, sampled_match_ids: Sequence[str]
) -> list[dict[str, Any]]:
    by_match: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_match[str(row["match_id"])].append(row)
    if any(len(by_match[mid]) != 2 for mid in set(sampled_match_ids)):
        raise ValueError("each sampled match must contribute both innings rows")
    return [row for match_id in sampled_match_ids for row in by_match[str(match_id)]]


def _model_spec(name: str, *, interactions: Sequence[tuple[str, str]] = (), extra_num: Sequence[str] = (), extra_cat: Sequence[str] = (), estimator: str = "logistic", include_venue_history: bool = False) -> ModelSpec:
    history_features = VENUE_NUMERIC if include_venue_history else ()
    return ModelSpec(name, tuple(dict.fromkeys((*NUMERIC, *history_features, *extra_num))), tuple(dict.fromkeys((*CATEGORICAL, *extra_cat))), tuple(interactions), estimator)


def _prepare_rows(rows: Sequence[dict[str, Any]], *, dev: Sequence[dict[str, Any]],
                  interactions: Sequence[tuple[str, str]], strengths: str = "elo",
                  spline_knots: Sequence[float] | None = None, boundary_dot: bool = False,
                  estimator: str = "logistic") -> tuple[list[dict[str, Any]], ModelSpec, dict[str, Any]]:
    if spline_knots is not None and (
            len(spline_knots) != 3 or
            not spline_knots[0] < spline_knots[1] < spline_knots[2]):
        raise ValueError("non_distinct_development_knots")
    means: dict[str, tuple[float, float]] = {}
    medians: dict[str, float] = {}
    operands = sorted({operand for pair in interactions for operand in pair if operand != "batting_first"})
    for operand in operands:
        vals = [_number(row, operand) for row in dev]
        present = [v for v in vals if v is not None]
        mean = sum(present) / len(present) if present else 0.0
        sd = math.sqrt(sum((v - mean) ** 2 for v in present) / len(present)) if present else 0.0
        if sd <= 0:
            raise ValueError(f"interaction operand has zero development variance: {operand}")
        means[operand] = mean, sd
        medians[operand] = _quantile(present, 0.5)
    output = []
    extra_num = [f"_interaction_{idx}" for idx in range(len(interactions))]
    # Interaction products are materialized from development-standardized operands.
    for original in rows:
        row = dict(original)
        # Products are supplied for every fit/predict row, including synthetic contexts.
        for idx, (left, right) in enumerate(interactions):
            def transform(field: str) -> float:
                value = _number(original, field)
                if value is None:
                    value = medians.get(field, 0.0)
                if field in means:
                    mean, sd = means[field]
                    return (value - mean) / sd
                return value
            row[f"_interaction_{idx}"] = transform(left) * transform(right)
        if strengths == "win_rate":
            row["elo_difference"] = None
        if spline_knots is not None:
            # Three ordered knots yield ONE nonlinear natural-cubic basis
            # in addition to the main linear pp_runs term.
            x = _number(original, "pp_runs") or 0.0
            k1, k2, k3 = spline_knots
            def d(k: float) -> float:
                return max(x - k, 0.0) ** 3
            span = k3 - k1
            row["_spline_1"] = (
                d(k1) - d(k2) * span / (k3-k2)
                + d(k3) * (k2-k1) / (k3-k2)
            ) / span ** 3
            if "_spline_1" not in extra_num:
                extra_num.append("_spline_1")
        if boundary_dot:
            for field in ("pp_boundary_pct", "pp_dot_ball_pct"):
                if field not in extra_num:
                    extra_num.append(field)
        output.append(row)
    if spline_knots is not None:
        import numpy as np
        spline_design = np.array([
            (1.0, float(row["pp_runs"]), row["_spline_1"])
            for row in output[:len(dev)] if _number(row, "pp_runs") is not None
        ])
        if len(spline_design) < 3 or np.linalg.matrix_rank(spline_design) < 3:
            raise ValueError("rank_deficient_development_spline")
    include_history = any("venue_prior" in operand for pair in interactions for operand in pair)
    spec = _model_spec("tradeoff", extra_num=extra_num, extra_cat=(), estimator=estimator, include_venue_history=include_history)
    if strengths == "win_rate":
        spec = ModelSpec(spec.name, tuple(n for n in spec.numeric_features if n != "elo_difference"), spec.categorical_features, estimator=spec.estimator)
    return output, spec, {
        "interaction_operand_mean_sd": means,
        "interaction_operand_medians": medians,
        "interaction_terms": [list(pair) for pair in interactions],
    }


def _fit_primary_model(rows: Sequence[dict[str, Any]]) -> tuple[ModelSpec, Any, dict[str, Any]]:
    """Fit only development rows, independent of CSV order or 2024 labels."""
    development = [row for row in rows if row["split"] == "development"]
    prepared, spec, decisions = _prepare_rows(
        development, dev=development, interactions=PRIMARY_INTERACTIONS)
    return spec, fit_model(spec, prepared), decisions


def _prob(model_spec: ModelSpec, model: Any, row: dict[str, Any]) -> float:
    return predict_model(model_spec, model, [row])[0]


def _fixed_context(dev: Sequence[dict[str, Any]]) -> dict[str, Any]:
    def mode(name: str) -> Any:
        counts = Counter(str(row.get(name, "")) for row in dev if row.get(name) not in (None, ""))
        if not counts:
            return None
        maximum = max(counts.values())
        return sorted(value for value, count in counts.items() if count == maximum)[0]
    contexts: dict[str, Any] = {}
    for field in CATEGORICAL:
        contexts[field] = mode(field)
    for field in NUMERIC + VENUE_NUMERIC:
        vals = [v for row in dev if (v := _number(row, field)) is not None]
        contexts[field] = _quantile(vals, 0.5) if vals else None
    toss_states = Counter(int(_number(row, "batting_team_won_toss") or 0) for row in dev if _number(row, "batting_team_won_toss") is not None)
    contexts["batting_team_won_toss"] = min((state for state, count in toss_states.items() if count == max(toss_states.values())), default=None)
    elo_mean, elo_sd, elo_med = _stats(dev, "elo_difference")
    history = [v for row in dev if _number(row, "venue_history_available") == 1 and (v := _number(row, "venue_prior_pp_runs_mean")) is not None]
    if not history:
        raise ValueError("development has no available prior venue history")
    runs = [_number(row, "pp_runs") for row in dev]
    run_reference = math.floor(_quantile([v for v in runs if v is not None], .5) + .5)
    contexts.update({
        "elo_mean": elo_mean, "elo_sd": elo_sd,
        "elo_states": [elo_med - elo_sd, elo_med, elo_med + elo_sd],
        "venue_states": [_quantile(history, q) for q in (.25, .5, .75)],
        "run_reference": run_reference,
        "venue_history_rows": len(history),
    })
    return contexts


def _context_row(context: dict[str, Any], *, runs: float, wickets: int, innings: int,
                 elo: float, venue_runs: float) -> dict[str, Any]:
    row = {key: context[key] for key in (*NUMERIC, *VENUE_NUMERIC, *CATEGORICAL) if key in context}
    row.update({"pp_runs": runs, "pp_wickets": wickets, "batting_first": innings,
                "elo_difference": elo, "venue_prior_pp_runs_mean": venue_runs,
                "venue_history_available": 1})
    means = context["interaction_operand_mean_sd"]
    for idx, (left, right) in enumerate(PRIMARY_INTERACTIONS):
        def transformed(field: str) -> float:
            value = float(row[field])
            if field in means:
                mean, sd = means[field]
                return (value - mean) / sd
            return value
        row[f"_interaction_{idx}"] = transformed(left) * transformed(right)
    return row


def _summaries(dev: Sequence[dict[str, Any]], contexts: dict[str, Any], spec: ModelSpec,
               model: Any, interactions: Sequence[tuple[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cells, curves, curve_inputs = [], [], []
    categorical_ok = contexts.get("batting_team_won_toss") is not None and all(contexts.get(field) is not None and contexts[field] in {str(r.get(field)) for r in dev} for field in CATEGORICAL)
    venue_mean, venue_sd, _ = _stats(dev, "venue_prior_pp_runs_mean")
    for innings in (1, 0):
        for elo_idx, elo in enumerate(contexts["elo_states"], 1):
            for venue_idx, venue in enumerate(contexts["venue_states"], 1):
                base = {"innings": innings, "elo_state": elo_idx, "elo_difference": elo,
                        "venue_state": venue_idx, "venue_prior_pp_runs_mean": venue}
                for w0, w1, label in ((1, 2, "primary_1_to_2"), (0, 1, "sensitivity_0_to_1"), (2, 3, "sensitivity_2_to_3")):
                    start = contexts["run_reference"]
                    s0 = local_support(dev, innings=innings, wickets=w0, elo=elo, venue_runs=venue,
                                       elo_mean=contexts["elo_mean"], elo_sd=contexts["elo_sd"],
                                       venue_mean=venue_mean, venue_sd=venue_sd)
                    s1 = local_support(dev, innings=innings, wickets=w1, elo=elo, venue_runs=venue,
                                       elo_mean=contexts["elo_mean"], elo_sd=contexts["elo_sd"],
                                       venue_mean=venue_mean, venue_sd=venue_sd)
                    support = categorical_ok and s0["supported"] and s1["supported"]
                    reason = None if support else ("fixed_categorical_level_absent_from_development" if not categorical_ok else (s0.get("reason") if not s0["supported"] else s1.get("reason")))
                    record = {**base, "contrast": label, "wickets_from": w0, "wickets_to": w1,
                              "run_reference": start, "support_start": s0, "support_target": s1,
                              "defined": False, "reason": reason, "runs_per_wicket": None}
                    if support and (not interactions or (s0["supported"] and s1["supported"])):
                        lo = max(s0["run_min"], s1["run_min"])
                        hi = min(s0["run_max"], s1["run_max"])
                        if lo > hi:
                            record["reason"] = "disjoint_wicket_run_support"
                            cells.append(record)
                            continue
                        if start < lo or start > hi:
                            record["reason"] = "starting_run_outside_common_supported_envelope"
                            cells.append(record)
                            continue
                        row0 = _context_row(contexts, runs=start, wickets=w0, innings=innings, elo=elo, venue_runs=venue)
                        row1 = _context_row(contexts, runs=start, wickets=w1, innings=innings, elo=elo, venue_runs=venue)
                        p0, p1 = _prob(spec, model, row0), _prob(spec, model, row1)
                        record.update({"probability_fixed_run_from": p0, "probability_fixed_run_to": p1,
                                       "probability_difference_fixed_run": p1-p0})
                        record["probability_fixed_wicket_low"] = _prob(spec, model, _context_row(contexts,runs=lo,wickets=w0,innings=innings,elo=elo,venue_runs=venue))
                        record["probability_fixed_wicket_high"] = _prob(spec, model, _context_row(contexts,runs=hi,wickets=w0,innings=innings,elo=elo,venue_runs=venue))
                        record["fixed_wicket_run_min"] = lo
                        record["fixed_wicket_run_max"] = hi
                        upper = min(s1["run_max"], hi) - start
                        root = solve_nonnegative_root(lambda delta: _prob(spec, model, _context_row(contexts,runs=start+delta,wickets=w1,innings=innings,elo=elo,venue_runs=venue))-p0, upper_delta=upper)
                        record.update({"defined": root["defined"], "runs_per_wicket": root["delta"], "reason": root["reason"], "root_iterations": root.get("iterations")})
                        for run in range(math.ceil(lo), math.floor(hi)+1):
                            curves.append({**base, "wickets": w0, "runs": run})
                            curve_inputs.append(_context_row(contexts,runs=run,wickets=w0,innings=innings,elo=elo,venue_runs=venue))
                    cells.append(record)
    if curve_inputs:
        for point, probability in zip(curves, predict_model(spec, model, curve_inputs)):
            point["predicted_win_probability"] = probability
    return cells, curves


def _bootstrap_refit(dev: Sequence[dict[str, Any]], contexts: dict[str, Any], spec: ModelSpec,
                     interactions: Sequence[tuple[str, str]], point_cells: list[dict[str, Any]],
                     *, repetitions: int, seed: int) -> dict[str, Any]:
    """Match-resample development, refitting preprocessing and model each replicate."""
    ids = sorted({str(row["match_id"]) for row in dev})
    if not ids or repetitions < 1:
        return {"requested": repetitions, "valid": 0, "failed": repetitions, "seed": seed}
    rng = random.Random(seed)
    values: dict[tuple[int,int,int,int,str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    eligible = [cell for cell in point_cells
                if cell.get("probability_difference_fixed_run") is not None]
    failures = 0
    for _ in range(repetitions):
        sampled = [rng.choice(ids) for _ in ids]
        sample_rows = draw_match_bootstrap_rows(dev, sampled_match_ids=sampled)
        try:
            prepared, bs_spec, bs_decisions = _prepare_rows(
                sample_rows, dev=sample_rows, interactions=interactions)
            fitted = fit_model(bs_spec, prepared)
            bs_contexts = {**contexts,
                           "interaction_operand_mean_sd": bs_decisions["interaction_operand_mean_sd"]}

            def context_at(cell: dict[str, Any], runs: float, wickets: int) -> dict[str, Any]:
                return _context_row(
                    bs_contexts, runs=runs, wickets=wickets, innings=cell["innings"],
                    elo=cell["elo_difference"], venue_runs=cell["venue_prior_pp_runs_mean"])

            requests = []
            for cell in eligible:
                start = cell["run_reference"]
                w0, w1 = cell["wickets_from"], cell["wickets_to"]
                lo, hi = cell["fixed_wicket_run_min"], cell["fixed_wicket_run_max"]
                requests.extend((context_at(cell, start, w0), context_at(cell, start, w1),
                                 context_at(cell, lo, w0), context_at(cell, hi, w0)))
            probabilities = predict_model(bs_spec, fitted, requests) if requests else []
            current: dict[tuple[int, int, int, int, str], dict[str, float]] = {}
            root_candidates = []
            for index, cell in enumerate(eligible):
                key = (cell["innings"], cell["elo_state"], cell["venue_state"],
                       cell["wickets_from"], cell["contrast"])
                p0, p1, p_low, p_high = probabilities[4*index:4*index+4]
                current[key] = {
                    "fixed_run_probability_from": p0,
                    "fixed_run_probability_to": p1,
                    "fixed_run_probability_difference": p1-p0,
                    "fixed_wicket_probability_low": p_low,
                    "fixed_wicket_probability_high": p_high,
                    "fixed_wicket_probability_difference": p_high-p_low,
                }
                if cell.get("defined"):
                    upper = cell["fixed_wicket_run_max"] - cell["run_reference"]
                    if upper >= 0:
                        root_candidates.append({"cell": cell, "key": key, "p0": p0,
                                                "lo": 0.0, "hi": upper})
            if root_candidates:
                endpoints = [
                    context_at(candidate["cell"], candidate["cell"]["run_reference"] + delta,
                               candidate["cell"]["wickets_to"])
                    for candidate in root_candidates for delta in (0.0, candidate["hi"])
                ]
                endpoint_prob = predict_model(bs_spec, fitted, endpoints)
                pending = []
                for index, candidate in enumerate(root_candidates):
                    flo = endpoint_prob[2*index] - candidate["p0"]
                    fhi = endpoint_prob[2*index+1] - candidate["p0"]
                    if abs(flo) <= 1e-12:
                        current[candidate["key"]]["runs_per_wicket"] = 0.0
                    elif abs(fhi) <= 1e-12:
                        current[candidate["key"]]["runs_per_wicket"] = candidate["hi"]
                    elif flo * fhi <= 0:
                        candidate["flo"] = flo
                        pending.append(candidate)
                for _step in range(100):
                    active = [candidate for candidate in pending
                              if candidate["hi"] - candidate["lo"] > 0.01]
                    if not active:
                        break
                    midpoints = [(candidate["lo"] + candidate["hi"]) / 2
                                 for candidate in active]
                    middle_rows = [
                        context_at(candidate["cell"],
                                   candidate["cell"]["run_reference"] + midpoint,
                                   candidate["cell"]["wickets_to"])
                        for candidate, midpoint in zip(active, midpoints)
                    ]
                    middle_prob = predict_model(bs_spec, fitted, middle_rows)
                    for candidate, midpoint, probability in zip(
                            active, midpoints, middle_prob):
                        fm = probability - candidate["p0"]
                        if abs(fm) <= 1e-12:
                            candidate["lo"] = candidate["hi"] = midpoint
                        elif candidate["flo"] * fm <= 0:
                            candidate["hi"] = midpoint
                        else:
                            candidate["lo"], candidate["flo"] = midpoint, fm
                for candidate in pending:
                    current[candidate["key"]]["runs_per_wicket"] = (
                        candidate["lo"] + candidate["hi"]) / 2
            for key, measurements in current.items():
                for metric, result in measurements.items():
                    values[key][metric].append(result)
        except (ValueError, ArithmeticError):
            failures += 1
    intervals = {}
    for key, metrics in values.items():
        intervals["|".join(map(str,key))] = {
            metric: {"lower_95":_quantile(vals,.025),"upper_95":_quantile(vals,.975),"valid_replicates":len(vals)}
            for metric, vals in metrics.items() if vals
        }
    return {"requested":repetitions,"valid":repetitions-failures,"failed":failures,"seed":seed,"estimand_intervals":intervals}


def _validation(dev_rows: Sequence[dict[str, Any]], val_rows: Sequence[dict[str, Any]], *, reps: int, seed: int) -> dict[str, Any]:
    report = {}
    dev_runs=sorted(v for row in dev_rows if (v := _number(row, "pp_runs")) is not None)
    knots = [_quantile(dev_runs, q) for q in (.1, .5, .9)]
    six_terms = PRIMARY_INTERACTIONS
    models = {
        "additive_benchmark": ((), "elo", None, False, "logistic"),
        "four_term_interaction": ((('pp_runs','batting_first'),('pp_wickets','batting_first'),('pp_runs','elo_difference'),('pp_wickets','elo_difference')),"elo",None,False,"logistic"),
        "six_term_primary": (six_terms,"elo",None,False,"logistic"),
        "strength_prior20_sensitivity": ((),"win_rate",None,False,"logistic"),
        "boundary_dot_sensitivity": ((),"elo",None,True,"logistic"),
        "restricted_cubic_spline_sensitivity": (six_terms, "elo", knots, False, "logistic"),
        "random_forest_challenger": ((), "elo", None, True, "random_forest"),
        "xgboost_challenger": ((), "elo", None, True, "xgboost"),
    }
    for name,(terms,strength,spline_knots,boundary,estimator) in models.items():
        if name == "restricted_cubic_spline_sensitivity" and len(set(knots)) != 3:
            report[name] = {"status": "undefined", "reason": "non_distinct_development_knots"}
            continue
        try:
            fitted_rows,spec,decisions=_prepare_rows([*dev_rows,*val_rows],dev=dev_rows,interactions=terms,strengths=strength,spline_knots=spline_knots,boundary_dot=boundary,estimator=estimator)
            train, val = fitted_rows[:len(dev_rows)], fitted_rows[len(dev_rows):]
            model=fit_model(spec,train)
            probabilities=predict_model(spec,model,val)
            labels=[int(r["batting_team_won"]) for r in val_rows]
            preds=[{"match_id":str(r["match_id"]),"label":y,"probability":p} for r,y,p in zip(val_rows,labels,probabilities)]
            metric=compute_metrics(labels,probabilities)
            calibration=calibration_coefficients(labels,probabilities)
            bins=calibration_table(labels,probabilities,bins=10)
            # validation bootstrap with frozen probabilities
            rng=random.Random(seed); ids=sorted({r["match_id"] for r in preds}); by=defaultdict(list)
            for row in preds: by[row["match_id"]].append(row)
            boot=defaultdict(list); bin_boot=defaultdict(lambda: defaultdict(list)); failed=0
            for _ in range(reps):
                sample=[item for mid in [rng.choice(ids) for _ in ids] for item in by[mid]]
                try:
                    sample_labels=[r["label"] for r in sample]
                    sample_probs=[r["probability"] for r in sample]
                    m=compute_metrics(sample_labels,sample_probs)
                    c=calibration_coefficients(sample_labels,sample_probs)
                    for key,value in {**m,**c}.items():
                        if value is not None: boot[key].append(value)
                    for bin_row in calibration_table(sample_labels,sample_probs,bins=10):
                        index=int(bin_row["bin"])
                        bin_boot[index]["mean_probability"].append(float(bin_row["mean_probability"]))
                        bin_boot[index]["observed_rate"].append(float(bin_row["observed_rate"]))
                except ValueError: failed+=1
            intervals={key:{"lower_95":_quantile(vals,.025),"upper_95":_quantile(vals,.975),"valid_replicates":len(vals)} for key,vals in boot.items() if vals}
            for bin_row in bins:
                vals=bin_boot[int(bin_row["bin"])]
                bin_row["bootstrap_ci"]={key:{"lower_95":_quantile(values,.025),"upper_95":_quantile(values,.975),"valid_replicates":len(values)} for key,values in vals.items() if values}
            report[name]={"status":"fit","n_rows":len(val_rows),"n_matches":len(ids),"development_rows":len(dev_rows),"development_matches":len({r['match_id'] for r in dev_rows}),"class_balance":dict(Counter(map(str,labels))),"missing_history_rows":sum(_number(r,'venue_history_available')!=1 for r in val_rows),"metrics":metric,"calibration":calibration,"validation_bootstrap":{"requested":reps,"valid":reps-failed,"failed":failed,"seed":seed,"metrics":intervals},"reliability_bins":bins,"decisions":decisions}
            if name=="six_term_primary":
                report[name]["predictions"]=[{"match_id":str(r["match_id"]),"label":y,"probability":p} for r,y,p in zip(val_rows,labels,probabilities)]
        except (ValueError, KeyError) as exc:
            report[name]={"status":"undefined","reason":str(exc)}
    return report


def _write_figure(cells: Sequence[dict[str, Any]], path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    primary = [r for r in cells if r.get("contrast") == "primary_1_to_2"]
    rows = [r for r in primary if r.get("defined")]
    fig, ax = plt.subplots(figsize=(10, max(2.8, 1.1 * len(rows) + 1.8)))
    if rows:
        labels = [
            f"{'First' if r['innings'] else 'Chase'} · Elo {r['elo_difference']:+.0f}"
            f" · prior venue {r['venue_prior_pp_runs_mean']:.1f} runs"
            for r in rows
        ]
        for index, row in enumerate(rows):
            interval = (row.get("bootstrap_ci") or {}).get("runs_per_wicket")
            if interval:
                ax.hlines(index, interval["lower_95"], interval["upper_95"],
                          color="#235789", linewidth=2)
            ax.scatter(row["runs_per_wicket"], index, color="#235789", s=42, zorder=3)
        ax.set_yticks(range(len(rows)), labels)
        ax.set_ylim(-0.6, len(rows) - 0.4)
    else:
        ax.text(.5, .5, "No supported nonnegative 1→2 wicket roots",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_yticks([])
    ax.set_xlabel("Extra first-10-over runs per additional wicket lost")
    ax.set_title(f"Supported 1→2 wicket roots: {len(rows)} of {len(primary)} prespecified contexts")
    ax.grid(axis="x", alpha=.25)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def run_pipeline(input_path: str | Path, output_dir: str | Path, *, bootstrap_repetitions: int = PRIMARY_REPS, validation_repetitions: int = VALIDATION_REPS, seed: int = SEED) -> dict[str, Any]:
    """Run only on the parent-provided unlocked 2015–2024 model table."""
    input_path, output_dir = Path(input_path), Path(output_dir)
    rows=[]
    with input_path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            # Check date/split before outcome or predictor fields are consumed.
            assert_unlocked_rows([row])
            rows.append(row)
    dev=[r for r in rows if r["split"]=="development"]
    val=[r for r in rows if r["split"]=="validation"]
    if not dev or not val:
        raise ValueError("both development and 2024 validation rows are required")
    if any(str(r["match_date"])[:4] > "2023" for r in dev) or any(str(r["match_date"])[:4] != "2024" for r in val):
        raise ValueError("development must end by 2023 and validation must contain 2024 only")
    if any(int(r["batting_team_won"]) not in (0,1) for r in rows):
        raise ValueError("outcomes must be binary decided innings")
    grouped=_groups(rows)
    if any(len(group)!=2 for group in grouped.values()):
        raise ValueError("each match must contain exactly two team-innings rows")
    if any(len({r["split"] for r in group}) != 1 for group in grouped.values()):
        raise ValueError("both innings of each match must share a split")
    output_dir.mkdir(parents=True,exist_ok=True)
    interactions = PRIMARY_INTERACTIONS
    spec, model, decisions = _fit_primary_model(rows)
    contexts=_fixed_context(dev)
    contexts["interaction_operand_mean_sd"] = decisions["interaction_operand_mean_sd"]
    cells,curves=_summaries(dev,contexts,spec,model,interactions)
    # Complete-case full primary fit is an explicit sensitivity; failures are explicit.
    required=(*NUMERIC,*VENUE_NUMERIC,*CATEGORICAL,"batting_team_won")
    cc_ids={mid for mid, group in grouped.items() if len(group)==2 and all(all(r.get(f) not in (None,"") for f in required) for r in group)}
    cc=[r for r in rows if str(r["match_id"]) in cc_ids]
    cc_dev=[r for r in cc if r["split"]=="development"]
    cc_val=[r for r in cc if r["split"]=="validation"]
    cc_report={"rows":len(cc),"matches":len(cc_ids),"excluded_rows":len(rows)-len(cc),"excluded_matches":len(grouped)-len(cc_ids)}
    try:
        cc_all,cc_spec,_=_prepare_rows([*cc_dev,*cc_val],dev=cc_dev,interactions=interactions)
        cc_model=fit_model(cc_spec,cc_all[:len(cc_dev)])
        cc_prob=predict_model(cc_spec,cc_model,cc_all[len(cc_dev):])
        cc_labels=[int(r["batting_team_won"]) for r in cc_val]
        cc_report["validation"]={"rows":len(cc_val),"matches":len({r["match_id"] for r in cc_val}),"metrics":compute_metrics(cc_labels,cc_prob),"calibration":calibration_coefficients(cc_labels,cc_prob)}
        cc_report["validation"]["bootstrap"] = cluster_bootstrap_metrics(
            ({"match_id": r["match_id"], "label": label, "probability": probability}
             for r, label, probability in zip(cc_val, cc_labels, cc_prob)),
            repetitions=validation_repetitions, seed=seed,
        )
    except (ValueError,KeyError) as exc:
        cc_report["validation"]={"status":"undefined","reason":str(exc)}
    # Spline knots are development-only, and distinctness/rank failures are reported, never searched.
    runvals=sorted(_number(r,"pp_runs") for r in dev if _number(r,"pp_runs") is not None)
    knots=[_quantile(runvals,q) for q in (.1,.5,.9)]
    spline={"status":"undefined","reason":"non_distinct_development_knots","knots":knots}
    if len(set(knots))==3:
        try:
            spline_rows,spline_spec,spline_decisions=_prepare_rows(dev,dev=dev,interactions=interactions,spline_knots=knots)
            spline_model=fit_model(spline_spec,spline_rows[:len(dev)])
            spline={"status":"fit","knots":knots,"decisions":spline_decisions,"development_rows":len(dev)}
        except (ValueError,KeyError) as exc: spline={"status":"undefined","knots":knots,"reason":str(exc)}
    validation=_validation(dev,val,reps=validation_repetitions,seed=seed)
    bootstrap=_bootstrap_refit(dev,contexts,spec,interactions,cells,repetitions=bootstrap_repetitions,seed=seed)
    for cell in cells:
        key="|".join(map(str,(cell["innings"],cell["elo_state"],cell["venue_state"],cell["wickets_from"],cell["contrast"])))
        cell["bootstrap_ci"]=bootstrap.get("estimand_intervals",{}).get(key)
    all_pred=validation.get("six_term_primary",{}).pop("predictions",[])
    pairings=[]
    by=defaultdict(list)
    for r in all_pred: by[r["match_id"]].append(r)
    for mid, pair in sorted(by.items()): pairings.append({"match_id":mid,"innings":pair})
    manifest={"analysis":"SSAC27 amended-source unlocked cohort run-wicket tradeoff","source_table":str(input_path),"source_sha256":hashlib.sha256(input_path.read_bytes()).hexdigest(),"input_rows":len(rows),"development_rows":len(dev),"development_matches":len({r['match_id'] for r in dev}),"validation_rows":len(val),"validation_matches":len({r['match_id'] for r in val}),"locked_rows_read":0,"seed":seed,"primary_bootstrap_requested":bootstrap_repetitions,"validation_bootstrap_requested":validation_repetitions,"model":{"estimator":"L2 logistic C=1 liblinear max_iter=2000","primary":"six interactions, fit development only","interactions":[list(pair) for pair in interactions]},"reference_contexts":contexts,"interaction_decisions":decisions,"validation":validation,"development_refit_bootstrap":bootstrap,"spline_sensitivity":spline,"complete_case_sensitivity":cc_report,"venue_history":{"development_unavailable_rows":sum(_number(r,"venue_history_available")!=1 for r in dev),"validation_unavailable_rows":sum(_number(r,"venue_history_available")!=1 for r in val)},"claim_boundary":"Associational/predictive conditional contrasts; no causal effect. Both innings are paired complementary outcomes; match is inference cluster.","caveat":"Retrospective specification adopted after preliminary outcome modeling; amended September 29 source, not reproduction of absent September 10 archive."}
    outputs={"analysis_manifest.json":manifest,"context_exchange_rates.json":cells,"probability_contrasts.csv":curves,"validation_pairings.json":pairings}
    for filename,data in outputs.items():
        target=output_dir/filename
        if filename.endswith(".csv"):
            fields=sorted({key for row in data for key in row})
            with target.open("w",newline="",encoding="utf-8") as dest:
                writer=csv.DictWriter(dest,fieldnames=fields);writer.writeheader();writer.writerows(data)
        else: target.write_text(json.dumps(data,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    figure_path=output_dir/"primary_exchange_rates.png"
    _write_figure(cells,figure_path)
    manifest["artifact_sha256"]={
        name:hashlib.sha256((output_dir/name).read_bytes()).hexdigest()
        for name in ("context_exchange_rates.json","probability_contrasts.csv","validation_pairings.json","primary_exchange_rates.png")
    }
    (output_dir/"analysis_manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return manifest


def _groups(rows: Sequence[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str,list[dict[str,Any]]]=defaultdict(list)
    for row in rows: grouped[str(row["match_id"])].append(row)
    return grouped
