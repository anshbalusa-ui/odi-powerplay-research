"""Independent audits for the unlocked non-pitch analysis cohort."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

from .model_table import FORBIDDEN_PREDICTORS
from .modeling import make_model_specs, validate_model_specs
from .quality import audit_powerplay_rows

UNLOCKED_SPLITS = {"development", "validation"}
ALL_SPLITS = UNLOCKED_SPLITS | {"locked_test"}


def audit_unlocked_model_rows(
    rows: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Audit cohort identity, pair structure, metric invariants, and feature safety.

    Locked rows are used only for split/match accounting. Their outcome-bearing fields
    are intentionally absent when called by the command-line reader.
    """

    materialized = list(rows)
    issues: list[dict[str, Any]] = []

    def issue(scope: str, field: str, expected: Any, actual: Any) -> None:
        issues.append(
            {
                "scope": scope,
                "field": field,
                "expected": expected,
                "actual": actual,
            }
        )

    by_match: dict[str, list[dict[str, Any]]] = defaultdict(list)
    split_rows: Counter[str] = Counter()
    for row in materialized:
        match_id = str(row.get("match_id", "")).strip()
        split = str(row.get("split", "")).strip()
        if not match_id:
            issue("row", "match_id", "non-empty", match_id)
            continue
        if split not in ALL_SPLITS:
            issue(match_id, "split", sorted(ALL_SPLITS), split)
        by_match[match_id].append(row)
        split_rows[split] += 1

    split_matches: Counter[str] = Counter()
    for match_id, match_rows in by_match.items():
        observed_splits = {str(row.get("split", "")).strip() for row in match_rows}
        if len(observed_splits) != 1:
            issue(match_id, "split_consistency", "one split", sorted(observed_splits))
        split = next(iter(observed_splits), "")
        split_matches[split] += 1
        if len(match_rows) != 2:
            issue(match_id, "innings_row_count", 2, len(match_rows))
            continue
        innings_numbers = sorted(str(row.get("innings_number", "")).strip() for row in match_rows)
        if innings_numbers != ["1", "2"]:
            issue(match_id, "innings_numbers", ["1", "2"], innings_numbers)

    unlocked_rows = [
        row for row in materialized if str(row.get("split", "")).strip() in UNLOCKED_SPLITS
    ]
    for row in unlocked_rows:
        match_id = str(row.get("match_id", "")).strip()
        for field, expected in (
            ("gender", "male"),
            ("match_type", "ODI"),
            ("analysis_eligible_primary", "1"),
            ("is_super_over", "0"),
            ("pp_complete", "1"),
        ):
            actual = str(row.get(field, "")).strip()
            if actual != expected:
                issue(match_id, field, expected, actual)

    metric_summary, metric_issues = audit_powerplay_rows(unlocked_rows)
    for metric_issue in metric_issues:
        issues.append({"scope": "powerplay_metrics", **metric_issue})

    specs = make_model_specs(include_pitch=False)
    try:
        validate_model_specs(specs, forbidden=FORBIDDEN_PREDICTORS)
    except ValueError as error:
        issue("model_specs", "validation", "valid fixed non-pitch specs", str(error))
    model_features = sorted(
        {
            feature
            for spec in specs
            for feature in (*spec.numeric_features, *spec.categorical_features)
        }
    )
    forbidden_used = sorted(set(model_features) & FORBIDDEN_PREDICTORS)
    if forbidden_used:
        issue("model_specs", "forbidden_predictors", [], forbidden_used)
    if unlocked_rows:
        missing_features = sorted(
            set(model_features) - set(unlocked_rows[0])
        )
        if missing_features:
            issue("model_table", "missing_predictors", [], missing_features)

    summary = {
        "locked_test_scored": False,
        "locked_test_outcomes_loaded": False,
        "rows_checked_for_structure": len(materialized),
        "matches_checked_for_structure": len(by_match),
        "unlocked_rows_checked_for_metrics": len(unlocked_rows),
        "unlocked_matches_checked_for_metrics": len(
            {str(row.get("match_id", "")) for row in unlocked_rows}
        ),
        "rows_by_split": dict(sorted(split_rows.items())),
        "matches_by_split": dict(sorted(split_matches.items())),
        "powerplay_metric_audit": metric_summary,
        "model_spec_names": [spec.name for spec in specs],
        "model_feature_allowlist": model_features,
        "forbidden_predictors_used": forbidden_used,
        "issue_count": len(issues),
    }
    return summary, issues
