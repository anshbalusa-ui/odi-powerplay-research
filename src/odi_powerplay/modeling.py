"""Nested, leakage-safe model specifications for chronological ODI prediction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ModelSpec:
    name: str
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    interaction_features: tuple[tuple[str, str], ...] = ()
    estimator: str = "logistic"

    @property
    def interaction_names(self) -> tuple[str, ...]:
        return tuple(f"{left}__x__{right}" for left, right in self.interaction_features)

    @property
    def all_features(self) -> tuple[str, ...]:
        return self.numeric_features + self.categorical_features

    @property
    def model_numeric_features(self) -> tuple[str, ...]:
        return self.numeric_features + self.interaction_names

    @property
    def model_features(self) -> tuple[str, ...]:
        return self.model_numeric_features + self.categorical_features


def make_model_specs(
    *, include_pitch: bool = False, include_nonlinear: bool = True
) -> list[ModelSpec]:
    """Return fixed nested specifications; no outcome or post-powerplay fields."""

    context_numeric = (
        "elo_difference",
        "team_prior_matches",
        "opponent_prior_matches",
        "team_prior20_win_rate",
        "opponent_prior20_win_rate",
        "batting_first",
        "batting_team_won_toss",
        "year",
    )
    context_categorical = ("toss_decision", "venue", "rule_era", "competition_type")
    venue_history_numeric = (
        "venue_history_available",
        "venue_prior_matches",
        "venue_prior_pp_runs_mean",
        "venue_prior_pp_wickets_mean",
        "venue_prior_boundary_pct",
        "venue_prior_dot_ball_pct",
    )
    interactions = [
        ("pp_runs", "batting_first"),
        ("pp_wickets", "batting_first"),
    ]
    if include_pitch:
        context_numeric += (
            "batting_ease",
            "pace_seam_support",
            "spin_support",
            "two_paced_expected",
            "dew_expected",
        )
        context_categorical += ("pitch_primary_category", "bounce_profile")
        interactions.extend(
            [
                ("pp_runs", "batting_ease"),
                ("pp_wickets", "batting_ease"),
                ("pp_wickets", "pace_seam_support"),
                ("pp_wickets", "spin_support"),
            ]
        )
    specs = [
        ModelSpec("intercept_only", (), (), estimator="dummy"),
        ModelSpec("m0_pre_match", context_numeric, context_categorical),
        ModelSpec("powerplay_benchmark", ("pp_runs", "pp_wickets"), ()),
        ModelSpec(
            "m1_context_powerplay",
            context_numeric + ("pp_runs", "pp_wickets"),
            context_categorical,
        ),
        ModelSpec(
            "venue_history_powerplay_sensitivity",
            context_numeric + venue_history_numeric + ("pp_runs", "pp_wickets"),
            context_categorical,
        ),
        ModelSpec(
            "m2_prespecified_interactions",
            context_numeric + ("pp_runs", "pp_wickets"),
            context_categorical,
            tuple(interactions),
        ),
        ModelSpec(
            "scoring_process_sensitivity",
            context_numeric + ("pp_wickets", "pp_boundary_pct", "pp_dot_ball_pct"),
            context_categorical,
        ),
    ]
    if include_nonlinear:
        challenger_numeric = context_numeric + (
            "pp_runs",
            "pp_wickets",
            "pp_boundary_pct",
            "pp_dot_ball_pct",
        )
        specs.extend(
            [
                ModelSpec(
                    "random_forest_challenger",
                    challenger_numeric,
                    context_categorical,
                    estimator="random_forest",
                ),
                ModelSpec(
                    "xgboost_challenger",
                    challenger_numeric,
                    context_categorical,
                    estimator="xgboost",
                ),
            ]
        )
    return specs


def validate_model_specs(specs: Iterable[ModelSpec], *, forbidden: set[str]) -> None:
    """Reject leakage and deterministic run/run-rate duplication before fitting."""

    names: set[str] = set()
    for spec in specs:
        if spec.name in names:
            raise ValueError(f"Duplicate model specification: {spec.name}")
        names.add(spec.name)
        predictors = set(spec.all_features)
        leaked = sorted(predictors & forbidden)
        if leaked:
            raise ValueError(f"Forbidden predictors in {spec.name}: {', '.join(leaked)}")
        if {"pp_runs", "pp_run_rate"}.issubset(predictors):
            raise ValueError(f"{spec.name} contains deterministic run and run-rate features")
        invalid_interactions = [
            pair
            for pair in spec.interaction_features
            if pair[0] not in spec.numeric_features or pair[1] not in spec.numeric_features
        ]
        if invalid_interactions:
            raise ValueError(f"Interaction operands must be numeric in {spec.name}")
        if spec.estimator not in {"dummy", "logistic", "random_forest", "xgboost"}:
            raise ValueError(f"Unknown estimator in {spec.name}: {spec.estimator}")
        if spec.estimator == "dummy" and spec.all_features:
            raise ValueError(f"Dummy specification {spec.name} must not contain predictors")


def partition_chronological_rows(
    rows: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Select fit/evaluation rows without reading labels from the locked period."""

    development: list[dict[str, Any]] = []
    validation: list[dict[str, Any]] = []
    locked_test_ids: set[str] = set()
    for row in rows:
        split = str(row["split"])
        if split == "development":
            development.append(row)
        elif split == "validation":
            validation.append(row)
        elif split == "locked_test":
            locked_test_ids.add(str(row["match_id"]))
        else:
            raise ValueError(f"Unknown chronological split: {split}")
    return development, validation, sorted(locked_test_ids)


def rolling_origin_splits(
    rows: Iterable[dict[str, Any]],
    *,
    validation_years: tuple[int, ...] = (2021, 2022, 2023),
) -> list[tuple[list[dict[str, Any]], list[dict[str, Any]]]]:
    """Build expanding-year folds while keeping complete matches together."""

    materialized = list(rows)
    folds: list[tuple[list[dict[str, Any]], list[dict[str, Any]]]] = []
    for validation_year in validation_years:
        training = [
            row for row in materialized if int(str(row["match_date"])[:4]) < validation_year
        ]
        validation = [
            row for row in materialized if int(str(row["match_date"])[:4]) == validation_year
        ]
        if not training or not validation:
            raise ValueError(f"Empty rolling-origin fold for {validation_year}")
        training_ids = {str(row["match_id"]) for row in training}
        validation_ids = {str(row["match_id"]) for row in validation}
        if training_ids & validation_ids:
            raise ValueError(f"Match crosses rolling-origin fold for {validation_year}")
        folds.append((training, validation))
    return folds


def fit_model(
    spec: ModelSpec,
    rows: Iterable[dict[str, Any]],
    *,
    label: str = "batting_team_won",
    random_state: int = 20250905,
):
    """Fit one fixed model with preprocessing learned only from supplied rows."""

    import pandas as pd
    from sklearn.compose import ColumnTransformer
    from sklearn.dummy import DummyClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    frame = pd.DataFrame(list(rows))
    if frame.empty:
        raise ValueError("Training rows are empty")
    labels = frame[label].astype(int)
    if labels.nunique() != 2:
        raise ValueError("Training labels must contain both classes")
    for feature in spec.numeric_features:
        frame[feature] = pd.to_numeric(frame[feature], errors="coerce")
    for name, (left, right) in zip(spec.interaction_names, spec.interaction_features):
        frame[name] = frame[left] * frame[right]

    if not spec.all_features:
        model = DummyClassifier(strategy="prior")
        model.fit([[0.0]] * len(frame), labels)
        return model

    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessing = ColumnTransformer(
        [
            ("numeric", numeric_pipeline, list(spec.model_numeric_features)),
            ("categorical", categorical_pipeline, list(spec.categorical_features)),
        ]
    )
    if spec.estimator == "logistic":
        classifier = LogisticRegression(
            C=1.0,
            max_iter=2000,
            penalty="l2",
            random_state=random_state,
            solver="liblinear",
        )
    elif spec.estimator == "random_forest":
        classifier = RandomForestClassifier(
            n_estimators=500,
            max_depth=6,
            min_samples_leaf=20,
            max_features="sqrt",
            n_jobs=1,
            random_state=random_state,
        )
    elif spec.estimator == "xgboost":
        from xgboost import XGBClassifier

        classifier = XGBClassifier(
            objective="binary:logistic",
            eval_metric="logloss",
            n_estimators=400,
            max_depth=3,
            learning_rate=0.05,
            min_child_weight=10,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            n_jobs=1,
            random_state=random_state,
        )
    else:
        raise ValueError(f"Unsupported estimator: {spec.estimator}")
    model = Pipeline(
        [
            ("preprocessing", preprocessing),
            ("classifier", classifier),
        ]
    )
    model.fit(frame[list(spec.model_features)], labels)
    return model


def predict_model(spec: ModelSpec, model: Any, rows: Iterable[dict[str, Any]]) -> list[float]:
    """Return positive-class probabilities for supplied rows."""

    import pandas as pd

    frame = pd.DataFrame(list(rows))
    if frame.empty:
        return []
    for feature in spec.numeric_features:
        frame[feature] = pd.to_numeric(frame[feature], errors="coerce")
    for name, (left, right) in zip(spec.interaction_names, spec.interaction_features):
        frame[name] = frame[left] * frame[right]
    matrix = [[0.0]] * len(frame) if not spec.all_features else frame[list(spec.model_features)]
    return [float(value) for value in model.predict_proba(matrix)[:, 1]]
