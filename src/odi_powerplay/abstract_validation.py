"""Validate an SSAC27 abstract against the approved evidence ledger."""

from __future__ import annotations

import re
from typing import Any

WORD_PATTERN = re.compile(r"\S+")
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)")
HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
FIGURE_TABLE_PATTERN = re.compile(r"^\s*(?:Figure|Table)\s+\d+\b", re.IGNORECASE | re.MULTILINE)
PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TODO|TBD|TBA|XXX|PLACEHOLDER|INSERT|FIXME)\b|\[\s*(?:insert|add|fill)",
    re.IGNORECASE,
)
CAUSAL_PATTERN = re.compile(
    r"\b(?:cause|causes|caused|causal|impact|drives|determines|led to|leads to|improves|improved)\b",
    re.IGNORECASE,
)
LOCKED_RESULT_PATTERN = re.compile(
    r"(?:2025|2026|locked).{0,50}(?:outcome|win|auc|probability|metric|score|result)"
    r"|(?:outcome|win|auc|probability|metric|score|result).{0,50}(?:2025|2026|locked)",
    re.IGNORECASE | re.DOTALL,
)

REQUIRED_HEADINGS = ("Introduction", "Methods", "Results", "Conclusion")


def _numeric_values(evidence: dict[str, Any]) -> list[float]:
    total = evidence["cohort"]
    validation = evidence["validation"]
    benchmark = evidence["models"]["powerplay_benchmark"]
    m1 = evidence["models"]["m1_context_powerplay"]
    m2 = evidence["models"]["m2_prespecified_interactions"]
    return [
        float(total["matches"]),
        float(total["rows"]),
        float(validation["matches"]),
        float(validation["rows"]),
        float(benchmark["roc_auc"]),
        float(m1["roc_auc"]),
        float(m2["roc_auc"]),
    ]


def _contains_number(text: str, expected: float) -> bool:
    for token in NUMBER_PATTERN.findall(text):
        try:
            observed = float(token.replace(",", ""))
        except ValueError:
            continue
        if abs(observed - expected) <= 0.0011:
            return True
    return False


def validate_ssac_abstract(text: str, evidence: dict[str, Any]) -> dict[str, Any]:
    """Return machine-readable abstract validation results; no edits are made."""

    issues: list[dict[str, str]] = []

    def issue(code: str, message: str) -> None:
        issues.append({"code": code, "message": message})

    words = WORD_PATTERN.findall(text)
    if not words:
        issue("empty", "abstract is empty")
    word_count = len(words)
    if word_count > 499:
        issue("word_limit", f"abstract has {word_count} words; maximum is 499 including title")

    headings = [heading.strip() for heading in HEADING_PATTERN.findall(text)]
    if not headings or headings[0].casefold() == "introduction":
        issue("title", "first nonblank line must be a title before the required headings")
    for heading in REQUIRED_HEADINGS:
        if headings.count(heading) != 1:
            issue("heading", f"required heading must appear exactly once: {heading}")
    if [heading for heading in headings if heading in REQUIRED_HEADINGS] != list(REQUIRED_HEADINGS):
        issue("heading_order", "required headings must appear in Introduction/Methods/Results/Conclusion order")

    figure_table_count = len(FIGURE_TABLE_PATTERN.findall(text))
    if figure_table_count > 2:
        issue("figure_table_limit", f"abstract references {figure_table_count} tables/figures; maximum is 2")
    if PLACEHOLDER_PATTERN.search(text):
        issue("placeholder", "placeholder language remains")
    if not re.search(r"\bassociated\b|\bobservational\b", text, re.IGNORECASE):
        issue("observational_language", "abstract must state an associational/observational interpretation")

    causal_matches = CAUSAL_PATTERN.findall(text)
    if causal_matches and not re.search(r"\bnot\s+causal\b|\bno\s+causal\b", text, re.IGNORECASE):
        issue("causal_language", "causal wording is not permitted without an explicit noncausal guardrail")
    safe_locked_statement = re.search(
        r"(?:without|withheld|unscored|not\s+(?:scored|used|reported)|reserved).{0,60}"
        r"(?:locked|2025|2026)|(?:locked|2025|2026).{0,60}"
        r"(?:withheld|unscored|not\s+(?:scored|used|reported))",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if LOCKED_RESULT_PATTERN.search(text) and not safe_locked_statement:
        issue("locked_outcome", "text appears to report or score a locked-period result")
    if evidence.get("locked_test_scored") is not False:
        issue("evidence_gate", "evidence artifact does not certify locked_test_scored=false")

    required_numeric = _numeric_values(evidence)
    missing_numeric = [value for value in required_numeric if not _contains_number(text, value)]
    if missing_numeric:
        issue(
            "evidence_numbers",
            "abstract is missing canonical evidence values: "
            + ", ".join(f"{value:.3f}" if value < 10 else str(int(value)) for value in missing_numeric),
        )

    pitch_allowed = bool(evidence["pitch_measurement"]["pitch_interaction_claim_allowed"])
    if not pitch_allowed:
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            if re.search(r"\bpitch\b", sentence, re.IGNORECASE) and not re.search(
                r"pending|blocked|withheld|not reported|not cleared|reliability|reconciliation|prespecified|analysis",
                sentence,
                re.IGNORECASE,
            ):
                issue("pitch_gate", "pitch sentence makes a substantive claim before reliability/reconciliation clearance")
                break

    return {
        "valid": not issues,
        "word_count_including_title": word_count,
        "headings": headings,
        "figure_table_count": figure_table_count,
        "canonical_evidence_values_present": len(required_numeric) - len(missing_numeric),
        "canonical_evidence_values_required": len(required_numeric),
        "issues": issues,
    }
