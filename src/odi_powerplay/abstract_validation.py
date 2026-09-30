"""Validate current SSAC27 abstract content against corrected release evidence."""
from __future__ import annotations

import re
from typing import Any

WORD_PATTERN = re.compile(r"\S+")
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])[-+−]?(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)")
FIGURE_TABLE_PATTERN = re.compile(r"\b(?:Figure|Table)\s+\d+\b", re.IGNORECASE)
HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
PLACEHOLDER_PATTERN = re.compile(r"\b(?:TODO|TBD|TBA|XXX|PLACEHOLDER|INSERT|FIXME)\b|\[\s*(?:insert|add|fill)", re.I)
CAUSAL_PATTERN = re.compile(r"\b(?:cause[sd]?|causal(?:ly)?|impact(?:s|ed)?|drives?|determines?|led to|leads to|improves?|improved|reduces?|reduced|increas(?:e|es|ed)|decreas(?:e|es|ed)|lowers?|lowered|raises?|raised|boosts?|boosted)\b", re.I)
PITCH_PATTERN = re.compile(r"\bpitch(?:es)?\b|playing environment", re.I)
LOCKED_PATTERN = re.compile(r"\b(?:2025|2026|locked[- ]period)\b.{0,80}\b(?:outcome|win|auc|probability|metric|score|result|validation)\w*|\b(?:outcome|win|auc|probability|metric|score|result|validation)\w*.{0,80}\b(?:2025|2026|locked[- ]period)\b", re.I | re.S)
LOCKED_YEAR = r"\b(?:2025\+(?=\s|$)|2025 onward|2025 and later)"
REQUIRED_HEADINGS = ("Introduction", "Methods", "Results", "Conclusion")
EXPECTED_TITLE = "What Is a Powerplay Wicket Worth? Context-Dependent Run-Wicket Tradeoffs in ODI Cricket"


def _has(text: str, value: float) -> bool:
    if value == 3 and re.search(r"\bthree\b", text, re.I):
        return True
    for token in NUMBER_PATTERN.findall(text):
        try:
            if abs(float(token.replace(",", "").replace("−", "-")) - value) < .00051:
                return True
        except ValueError:
            continue


def _schema_ok(e: dict[str, Any]) -> bool:
    cohort, est, models = e.get("cohort"), e.get("primary_estimand"), e.get("validation_models")
    sources, ledger = e.get("source_artifacts"), e.get("evidence_ledger")
    if not (e.get("artifact_version") == 2 and e.get("analysis_scope") == "amended_source_unlocked_2015_2024_only"
            and e.get("locked_test_scored") is False and e.get("locked_test_outcomes_loaded") is False
            and isinstance(cohort, dict) and cohort.get("matches") == 942 and cohort.get("rows") == 1884
            and cohort.get("development") == {"matches": 871, "rows": 1742}
            and cohort.get("validation") == {"matches": 71, "rows": 142}
            and isinstance(est, dict) and est.get("starting_runs") == 47 and est.get("wickets_from") == 1
            and est.get("wickets_to") == 2 and est.get("contexts_total") == 18
            and est.get("defined_roots") == 3 and est.get("undefined_roots") == 15
            and isinstance(models, dict) and isinstance(sources, dict) and bool(sources)
            and all(not PathLike.is_absolute(str(p)) and re.fullmatch(r"[0-9a-f]{64}", str(v)) for p, v in sources.items())
            and e.get("release_manifest_sha256") == "99574bd3b67b20ee68face49ad58e155c08811b5f6229a9e7b2084b3effdcdcf"
            and e.get("canonical_handoff") == "docs/ssac27_numeric_handoff.md"
            and sources.get("artifacts/ssac27_tradeoff/release_manifest.json") == e.get("release_manifest_sha256")
            and sources.get("docs/ssac27_numeric_handoff.md") == "9c4fffc1bfb1c75734c9546f2a47ab4de9a9de7de74811a2e3ce64160ec4c909"
            and isinstance(ledger, list) and any(isinstance(r, dict) and r.get("status") == "blocked" for r in ledger)
            and any(isinstance(r, dict) and r.get("status") == "historical_only" for r in ledger)
            and e.get("pitch_measurement", {}).get("pitch_interaction_claim_allowed") is False):
        return False
    expected_models = {"six_term_primary": (.6626, .6726), "additive_benchmark": (.6737, .6650), "four_term_interaction": (.6784, .6669)}
    if any(not isinstance(models.get(name), dict) or abs(models[name].get("roc_auc", -1) - auc) > .00051 or abs(models[name].get("log_loss", -1) - loss) > .00051 for name, (auc, loss) in expected_models.items()):
        return False
    root_specs = [(13.248, 4.713, 17.481, 758), (14.143, 4.124, 18.450, 735), (29.763, 13.844, 30.934, 563)]
    roots = est.get("roots")
    if not isinstance(roots, list) or len(roots) != 3:
        return False
    for root, expected in zip(roots, root_specs):
        if any(abs(root.get(key, -999) - value) > .00051 for key, value in zip(("runs_per_wicket", "ci_lower", "ci_upper", "valid_refits"), expected)):
            return False
    neutral = e.get("neutral_fixed_run_contrasts")
    paired = e.get("neutral_paired_context_difference")
    if not isinstance(neutral, dict) or not isinstance(paired, dict):
        return False
    for key, values in {"batting_first": (.5046, .3995, -10.505, -15.473, -7.215), "chase": (.5578, .4009, -15.690, -20.614, -12.698)}.items():
        row = neutral.get(key)
        if not isinstance(row, dict) or any(abs(row.get(field, -999) * (100 if field in ("difference", "ci_lower", "ci_upper") else 1) - value) > .00051 for field, value in zip(("probability_from", "probability_to", "difference", "ci_lower", "ci_upper"), values)):
            return False
    return (abs(paired.get("estimate", -999) * 100 - 5.185) <= .00051
            and abs(paired.get("lower_95", -999) * 100 - (-.457)) <= .00051
            and abs(paired.get("upper_95", -999) * 100 - 11.182) <= .00051
            and paired.get("valid_paired_replicates") == 1000)


class PathLike:
    @staticmethod
    def is_absolute(value: str) -> bool:
        return value.startswith("/") or bool(re.match(r"^[A-Za-z]:[\\/]", value))


def validate_ssac_abstract(text: str, evidence: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    def issue(code: str, message: str) -> None:
        issues.append({"code": code, "message": message})
    if not _schema_ok(evidence):
        issue("evidence_gate", "evidence must be a verified version-2 amended-source release with locked outcomes unscored")
    words = WORD_PATTERN.findall(text)
    if not words: issue("empty", "abstract is empty")
    if len(words) > 499: issue("word_limit", f"abstract has {len(words)} words; maximum is 499 including title")
    headings = [h.strip() for h in HEADING_PATTERN.findall(text)]
    if not headings or headings[0].casefold() == "introduction": issue("title", "first nonblank line must be a title before required headings")
    elif headings[0].casefold() != EXPECTED_TITLE.casefold(): issue("title", "title does not match the approved current title")
    for h in REQUIRED_HEADINGS:
        if sum(x.casefold() == h.casefold() for x in headings) != 1: issue("heading", f"required heading must appear exactly once: {h}")
    if [h.casefold() for h in headings if h.casefold() in {x.casefold() for x in REQUIRED_HEADINGS}] != [x.casefold() for x in REQUIRED_HEADINGS]: issue("heading_order", "required headings must appear in Introduction/Methods/Results/Conclusion order")
    figs = len(FIGURE_TABLE_PATTERN.findall(text))
    if figs > 2: issue("figure_table_limit", f"abstract references {figs} tables/figures; maximum is 2")
    if PLACEHOLDER_PATTERN.search(text): issue("placeholder", "placeholder language remains")
    if not re.search(r"\bassociated\b|\bobservational\b", text, re.I): issue("observational_language", "abstract must state associational/observational interpretation")
    sentences = re.split(r"(?<=[.!?])\s+", text)
    causal_sentences = [s for s in sentences if CAUSAL_PATTERN.search(s)]
    guarded_causal = re.compile(r"\b(?:not|no)\s+causal(?:ly)?\b|\b(?:did|does|do)\s+not\s+improve\b", re.I)
    if any(CAUSAL_PATTERN.search(guarded_causal.sub("", sentence)) for sentence in causal_sentences):
        issue("causal_language", "causal wording is not permitted; disclaimers do not cancel positive claims")
    for sentence in sentences:
        positive_locked = re.search(r"\b(?:we|model|analysis)\s+(?:scored|evaluated|reported|fit)\s+(?:the\s+)?(?:2025|2026|locked)\b", sentence, re.I)
        safe_locked = re.search(LOCKED_YEAR + r".{0,100}\b(?:metadata.only|no outcomes|not opened|unscored|not scored|not fit|not loaded(?:\s+or\s+scored)?)\b|\b(?:metadata.only|no outcomes|not opened|unscored|not scored|not fit|not loaded(?:\s+or\s+scored)?)\b.{0,100}" + LOCKED_YEAR, sentence, re.I)
        if positive_locked or (LOCKED_PATTERN.search(sentence) and not safe_locked):
            issue("locked_outcome", "text appears to report or score a locked-period result")
            break
    if evidence.get("locked_test_scored") is not False or evidence.get("locked_test_outcomes_loaded") is not False: issue("evidence_gate", "locked-period outcomes must remain unscored and unloaded")

    expected = [942, 1884, 871, 1742, 71, 142, 47, 1, 2, 18, 3, 15, 14.143, 4.124, 18.450, 735, 13.248, 4.713, 17.481, 758, 29.763, 13.844, 30.934, 563, .6626, .5461, .7681, .6726, .6737, .6650, .6784, .6669, -15.473, -7.215, -20.614, -12.698, -.457, 11.182]
    for n in expected:
        if not _has(text, n): issue("evidence_numbers", f"required corrected evidence value missing: {n}")
    if any(_has(text, value) for value in (.740, .708, .710, .082, -.126, 1094)):
        issue("stale_result", "superseded preliminary cohort or model result must not appear")
    if not _has(text, .5046) or not _has(text, .3995) or not _has(text, -10.505) or not _has(text, .5578) or not _has(text, .4009) or not _has(text, -15.690) or not _has(text, 5.185):
        issue("evidence_numbers", "required neutral-context probability contrasts are missing")
    body = text.partition("\n")[2]
    universal_pattern = re.compile(r"\b(?:a|the|one|each|every|universal|fixed|constant)\s+(?:powerplay\s+)?wicket(?:'s)?\s+(?:is\s+)?(?:worth|price|value)\b|\b(?:universal|constant)\s+(?:run[- ]wicket|wicket[- ]run)\s+(?:rate|exchange|price)\b", re.I)
    if any(not re.search(r"\b(?:not|no|never|cannot|can't|does not|do not)\b.{0,45}$", body[max(0, match.start() - 55):match.start()], re.I) for match in universal_pattern.finditer(body)):
        issue("universal_rate", "a universal wicket price is unsupported")
    if re.search(r"\bundefined\b.{0,40}\b(?:is|are|equals?|means?)\s+(?:exactly\s+)?zero\b|\bzero\s+runs?\s+(?:is|are)\s+(?:the\s+)?undefined", text, re.I):
        issue("unsupported_root", "undefined roots must not be reported as zero")
    if re.search(r"\b(?:15|fifteen)\b.{0,60}\b(?:roots?|rates?|exchange rates?)\b.{0,50}\b(?:assigned|set|coded|reported|given|treated as|valued at)\b.{0,25}\bzero\b", text, re.I):
        issue("unsupported_root", "unavailable root estimates cannot be assigned a zero run value")
    if not re.search(r"\b(?:15|fifteen)\b.{0,60}\b(?:undefined|no bounded|no nonnegative)\b|\b(?:undefined|no bounded|no nonnegative)\b.{0,60}\b(?:15|fifteen)\b", text, re.I):
        issue("unsupported_root", "state that the other 15 of 18 roots are undefined, not zero")
    for sentence in sentences:
        if re.search(r"\b(?:root|exchange.rate)\b.{0,100}\b(?:paired|joint)\b.{0,100}\b(?:CI|interval)\b|\b(?:paired|joint)\b.{0,100}\b(?:root|exchange.rate)\b.{0,100}\b(?:CI|interval)\b", sentence, re.I) and not re.search(r"\b(?:no|neither|not|undefined|unavailable)\b", sentence, re.I):
            issue("unsupported_root", "neither paired root-difference interval passed the frozen stability gate")
            break
    # Detect substantive pitch findings sentence-by-sentence, while allowing explicit exclusion/guardrail language.
    # Exclusion statements are safe; a positive pitch result in that same sentence is not.
    for sentence in sentences:
        positive_pitch = re.search(r"\b(?:pitch|playing environment)\b.{0,90}\b(?:improv\w*|increas\w*|decreas\w*|predict\w*|significant)\b", sentence, re.I)
        guarded_pitch = re.search(r"\b(?:excluded|not\s+(?:measured|analyzed|analysed|included|tested|used|approved)|no\s+(?:pitch|playing.environment)|historical.*separate)\b", sentence, re.I)
        substantive_pitch = PITCH_PATTERN.search(sentence) and re.search(r"\b(?:effect|associat\w*|predict\w*|increas\w*|decreas\w*|stronger|improv\w*|impact\w*|interaction|relationship|significant|result|finding|estimate)\b", sentence, re.I)
        if (positive_pitch and not re.search(r"\b(?:not|no)\s+\w{0,12}\b.{0,20}$", sentence[:positive_pitch.end()], re.I)) or (substantive_pitch and not guarded_pitch):
            issue("pitch_gate", "substantive pitch/playing-environment outcome claims are not permitted")
            break
    if not re.search(r"\bpitch\b.{0,80}\bexcluded\b|\bexcluded\b.{0,80}\bpitch\b", text, re.I): issue("pitch_gate", "state that pitch is excluded")
    if not re.search(LOCKED_YEAR + r".{0,100}\b(?:metadata.only|no outcomes|not opened|unscored|unfit|not scored|not loaded(?:\s+or\s+scored)?)\b|\b(?:metadata.only|no outcomes|not opened|unscored|unfit|not scored|not loaded(?:\s+or\s+scored)?)\b.{0,100}" + LOCKED_YEAR, text, re.I): issue("locked_outcome", "state that 2025+ outcomes were not opened or scored")
    return {"valid": not issues, "word_count_including_title": len(words), "figure_table_count": figs, "canonical_evidence_values_present": len(expected) - sum(1 for n in expected if not _has(text, n)), "issues": issues}
