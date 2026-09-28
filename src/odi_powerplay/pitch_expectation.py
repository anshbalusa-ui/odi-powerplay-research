"""Separate, outcome-blind pre-match expectation measurement (never legacy pitch codes)."""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

RUBRIC = Path(__file__).resolve().parents[2] / "config/pitch_expectation_agent.json"
META_FIELDS = (
    "cricsheet_match_id", "match_date", "event_name", "competition_type",
    "venue", "city", "team_1", "team_2", "source_url", "source_title",
    "published_at_utc", "accessed_at_utc", "scheduled_start_utc",
)
CATEGORIES = {
    "batting_expectation": {"difficult", "neutral", "favorable", "uncertain"},
    "pace_seam_expectation": {"low", "neutral", "high", "uncertain"},
    "spin_expectation": {"low", "neutral", "high", "uncertain"},
    "slow_two_paced_expectation": {"unlikely", "possible", "likely", "uncertain"},
    "overall_expected_environment": {
        "batting_favorable", "balanced", "pace_seam_favorable", "spin_slow_favorable", "uncertain"
    },
}
BASES = {
    "explicit_playing_effect_statement", "physical_surface_description",
    "contextual_pre_match_inference",
}
ASSESSMENT_KEYS = set(CATEGORIES) | {"confidence", "evidence", "reasoning_basis", "rationale"}
INPUT_KEYS = set(META_FIELDS) | {"source_text", "source_hash"}
# Fail closed on obvious result/live coverage. This is NOT a substitute for source review.
CONTAMINATION = re.compile(
    r"\b(?:final score|match result|match report|post.match|live commentary|"
    r"scorecard|as it happened|won by \d+ (?:runs|wickets)|"
    r"won|lost|beat|beaten|defeated|conceded|clinched|"
    r"(?:innings|match) highlights)\b", re.IGNORECASE
)


def rubric_hash(path: Path = RUBRIC) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rubric_version(path: Path = RUBRIC) -> str:
    return str(json.loads(path.read_text(encoding="utf-8"))["version"])


def _utc(text: str) -> datetime:
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("source and scheduled timestamps require UTC offsets")
    return parsed


def latest_publication_utc(published: str) -> datetime:
    """Conservatively bound a date-only report to the end of that UTC day."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", published):
        return datetime.fromisoformat(published + "T23:59:59.999999+00:00")
    return _utc(published)


def eligible_sources(
    reports: list[dict], starts: list[dict], registry: list[dict],
    timing_exclusions: list[str] | None = None,
) -> list[dict]:
    """Project the frozen universe; date-only publications need a conservative upper bound."""
    by_start = {row["cricsheet_match_id"]: row for row in starts}
    by_status = {row["cricsheet_match_id"]: row["reaudit_status"] for row in registry}
    if len(by_start) != len(starts) or len(by_status) != len(registry):
        raise ValueError("duplicate match-level start or registry row")
    out = []
    ids = set()
    for report in reports:
        key = report["cricsheet_match_id"]
        if key in ids:
            raise ValueError("duplicate match-level source row")
        ids.add(key)
        if report["pre_match_verified"] != "1" or by_status.get(key) == "source_unavailable":
            continue
        if by_status.get(key) not in {"passed_revised", "passed_unchanged", "current_standard"}:
            raise ValueError(f"{key}: missing approved source-universe status")
        start = by_start.get(key)
        if not start or start["start_time_status"] != "verified":
            raise ValueError(f"{key}: scheduled start not verified")
        published = report["published_at_utc"]
        latest_publication = latest_publication_utc(published)
        if latest_publication >= _utc(start["scheduled_start_utc"]):
            if timing_exclusions is not None and len(published) == 10:
                timing_exclusions.append(key)
                continue
            raise ValueError(f"{key}: report not demonstrably published before play")
        projected = {field: report[field] for field in META_FIELDS if field != "scheduled_start_utc"}
        projected["scheduled_start_utc"] = start["scheduled_start_utc"]
        if not urlparse(projected["source_url"]).scheme == "https":
            raise ValueError(f"{key}: source URL must be HTTPS")
        out.append(projected)
    return out


def assessment_input(report: dict, start: dict, text: str, source_hash: str) -> dict:
    """Strict positive allowlist; never forward optional caller keys to an assessor."""
    if not text.strip() or not source_hash.strip():
        raise ValueError("source text and content hash are required")
    if source_hash != hashlib.sha256(text.encode("utf-8")).hexdigest():
        raise ValueError("source content hash does not match assessor text")
    if CONTAMINATION.search(text) or CONTAMINATION.search(report["source_title"]):
        raise ValueError("possible post-match or result contamination")
    projected = {field: report[field] for field in META_FIELDS if field != "scheduled_start_utc"}
    projected["scheduled_start_utc"] = start["scheduled_start_utc"]
    projected.update(source_text=text, source_hash=source_hash)
    if set(projected) != INPUT_KEYS:
        raise ValueError("assessment input is not strictly allowlisted")
    return projected


def validate_assessment(answer: dict) -> None:
    if set(answer) != ASSESSMENT_KEYS:
        raise ValueError("assessment schema has missing or extra fields")
    for field, allowed in CATEGORIES.items():
        if answer[field] not in allowed:
            raise ValueError(f"unsupported {field}")
    if type(answer["confidence"]) is not int or not 0 <= answer["confidence"] <= 100:
        raise ValueError("confidence must be an integer between 0 and 100")
    if not isinstance(answer["reasoning_basis"], list) or not answer["reasoning_basis"]:
        raise ValueError("reasoning_basis must be a nonempty list")
    if set(answer["reasoning_basis"]) - BASES or not all(
        isinstance(value, str) for value in answer["reasoning_basis"]
    ):
        raise ValueError("unsupported reasoning_basis")
    for field in ("evidence", "rationale"):
        if not isinstance(answer[field], str) or not answer[field].strip() or len(answer[field]) > 600:
            raise ValueError(f"{field} must be a short nonempty statement")


def consensus(answers: list[dict]) -> dict:
    if len(answers) != 3:
        raise ValueError("exactly three independent assessments required")
    for answer in answers:
        validate_assessment(answer)
    result = {}
    support = {}
    for field in CATEGORIES:
        winner, count = Counter(answer[field] for answer in answers).most_common(1)[0]
        support[field] = count
        result[field] = winner if count >= 2 else "uncertain"
    median = sorted(answer["confidence"] for answer in answers)[1]
    agreed = support["overall_expected_environment"] >= 2
    result.update(
        confidence=median, agreement_by_field=support,
        primary_eligible=agreed and median >= 60,
        broad_eligible=agreed,
        high_confidence_eligible=agreed and median >= 75,
        unanimous_eligible=all(n == 3 for n in support.values()),
    )
    return result


def source_snapshot(report: dict, capture: dict) -> dict:
    """Accept only a reviewed, contemporaneous capture of the original report."""
    required = {
        "source_url", "source_text", "retrieved_at_utc", "review_status",
        "reviewer_id", "published_at_utc",
    }
    if set(capture) != required or capture["review_status"] != "pre_match_content_verified":
        raise ValueError("source capture requires independent pre-match content verification")
    if not capture["reviewer_id"].strip() or capture["source_url"] != report["source_url"]:
        raise ValueError("source capture provenance does not match the verified report")
    if capture["published_at_utc"] != report["published_at_utc"]:
        raise ValueError("source capture publication timestamp changed")
    _utc(capture["retrieved_at_utc"])
    text = capture["source_text"]
    if not isinstance(text, str) or not text.strip() or CONTAMINATION.search(text):
        raise ValueError("unavailable or possibly contaminated source capture")
    return {
        "source_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "retrieved_at_utc": capture["retrieved_at_utc"],
        "reviewer_id": capture["reviewer_id"],
        "source_text": text,
    }


def source_disposition(report: dict, capture: dict) -> dict:
    """Require an auditable retrieval attempt for a non-assessed source."""
    required = {
        "source_url", "retrieved_at_utc", "review_status", "reviewer_id", "status_note",
    }
    if set(capture) != required or capture["review_status"] not in {
        "unavailable", "contaminated_or_ambiguous", "needs_review",
    }:
        raise ValueError("non-assessment needs a supported source disposition")
    if capture["source_url"] != report["source_url"]:
        raise ValueError("disposition URL differs from frozen registry")
    if not capture["reviewer_id"].strip() or not capture["status_note"].strip():
        raise ValueError("source disposition lacks reviewer or concrete reason")
    _utc(capture["retrieved_at_utc"])
    return {
        "source_status": capture["review_status"],
        "retrieved_at_utc": capture["retrieved_at_utc"],
        "reviewer_id": capture["reviewer_id"],
        "status_note": capture["status_note"],
    }


def validate_passes(payloads: list[dict], passes: dict[str, list[dict]]) -> None:
    """Fail closed if any pass is incomplete or bound to different inputs/rubric."""
    if set(passes) != {"A", "B", "C"}:
        raise ValueError("three separate assessor passes A/B/C are required")
    inputs = {row["cricsheet_match_id"]: row for row in payloads}
    if len(inputs) != len(payloads):
        raise ValueError("duplicate source IDs")
    record_keys = {
        "cricsheet_match_id", "assessor_id", "model_name", "model_version",
        "reasoning_effort", "prompt_hash", "source_hash", "run_id",
        "assessed_at_utc", "assessment",
    }
    frozen_hash = rubric_hash()
    for assessor, rows in passes.items():
        if len(rows) != len(inputs):
            raise ValueError(f"pass {assessor} is incomplete")
        ids = set()
        for row in rows:
            key = row.get("cricsheet_match_id")
            if (set(row) != record_keys or key not in inputs or key in ids
                    or row["assessor_id"] != assessor
                    or row["source_hash"] != inputs[key]["source_hash"]
                    or row["prompt_hash"] != frozen_hash):
                raise ValueError(f"pass {assessor} contains an invalid record")
            ids.add(key)
            if any(not isinstance(row[field], str) or not row[field].strip() for field in (
                "model_name", "model_version", "reasoning_effort", "run_id"
            )):
                raise ValueError("model/protocol provenance is incomplete")
            _utc(row["assessed_at_utc"])
            validate_assessment(row["assessment"])


def pairwise_agreement(pairs: list[tuple[str, str]]) -> dict:
    """Observed exact agreement and Cohen's kappa where expected agreement <1."""
    if not pairs:
        return {"n": 0, "exact_agreement": None, "cohens_kappa": None}
    n = len(pairs)
    observed = sum(left == right for left, right in pairs) / n
    left_counts = Counter(left for left, _ in pairs)
    right_counts = Counter(right for _, right in pairs)
    expected = sum(left_counts[value] * right_counts[value] for value in
                   left_counts.keys() | right_counts.keys()) / (n * n)
    return {
        "n": n, "exact_agreement": observed,
        "cohens_kappa": (observed - expected) / (1 - expected) if expected < 1 else None,
    }


def audit_sample(rows: list[dict], size: int = 15) -> list[dict]:
    """Deterministic diversity sample using only measurement metadata."""
    if size <= 0:
        raise ValueError("size must be positive")
    candidates = sorted(rows, key=lambda row: row["cricsheet_match_id"])
    selected = []
    used = set()
    seen = set()
    while candidates and len(selected) < size:
        def attributes(row: dict) -> set[str]:
            return {
                "category:" + row["overall_expected_environment"],
                "confidence:" + ("high" if row["confidence"] >= 75 else "lower"),
                "agreement:" + ("majority" if row["broad_eligible"] else "disagreement"),
                "year:" + row["match_date"][:4],
                "provider:" + (urlparse(row["source_url"]).hostname or ""),
            }

        candidate = max(
            candidates,
            key=lambda row: (len(attributes(row) - seen),
                             -sum(str(row["cricsheet_match_id"]).encode("utf-8"))),
        )
        key = candidate["cricsheet_match_id"]
        if key in used:
            raise ValueError("duplicate match in audit candidate set")
        selected.append(candidate)
        used.add(key)
        seen.update(attributes(candidate))
        candidates.remove(candidate)
    return selected


class _ArticleParser(HTMLParser):
    """Collect metadata and article-scoped paragraphs, never navigation cards."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.published: list[str] = []
        self.modified: list[str] = []
        self.paragraphs: list[str] = []
        self._article_depth = 0
        self._in_paragraph = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta":
            marker = (values.get("property") or values.get("itemprop")
                      or values.get("name") or "").lower()
            content = values.get("content") or ""
            if marker in {"article:published_time", "datepublished"}:
                self.published.append(content)
            elif marker in {"article:modified_time", "datemodified"}:
                self.modified.append(content)
        if tag == "article":
            self._article_depth += 1
        if tag == "p" and self._article_depth:
            self._in_paragraph = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._in_paragraph:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._in_paragraph:
            paragraph = " ".join(" ".join(self._parts).split())
            if paragraph:
                self.paragraphs.append(paragraph)
            self._parts = []
            self._in_paragraph = False
        if tag == "article" and self._article_depth:
            self._article_depth -= 1


_CONDITION = re.compile(
    r"\b(?:pitch|surface|strip|conditions|seam|spin|turn|bounce|grass|"
    r"dust|tacky|moist|slow|dew|weather)\b", re.IGNORECASE
)
_RESULT = re.compile(
    r"\b(?:won|defeat|victory|result|scorecard|final score|live commentary|"
    r"chase[ds]?|scored?|wickets?|highest ever|innings)\b|"
    r"\b\d{1,3}/\d{1,2}\b|\b\d{2,3}\b", re.IGNORECASE
)


def extract_source_candidate(report: dict, html_text: str) -> dict:
    """Quarantine unsafe pages; expose only short condition text after temporal checks.

    This is a source-review candidate, never an independent review or assessment.
    """
    parser = _ArticleParser()
    parser.feed(html_text)
    if not parser.published or not parser.modified:
        return {"status": "needs_review", "reason": "article publication or modification time missing"}
    try:
        published = [_utc(value) for value in parser.published]
        modified = [_utc(value) for value in parser.modified]
        scheduled = _utc(report["scheduled_start_utc"])
        original = report["published_at_utc"]
        published_matches = (
            any(value.date().isoformat() == original for value in published)
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", original)
            else any(value == _utc(original) for value in published)
        )
    except (ValueError, TypeError):
        return {"status": "needs_review", "reason": "article timestamps cannot be verified"}
    if not published_matches:
        return {"status": "needs_review", "reason": "current publication differs from verified release"}
    if max(modified) >= scheduled or max(published) >= scheduled:
        return {"status": "contaminated_or_ambiguous", "reason": "article could contain later edits"}
    if CONTAMINATION.search(report["source_title"]):
        return {"status": "contaminated_or_ambiguous", "reason": "source title resembles result coverage"}
    sentences = []
    for paragraph in parser.paragraphs:
        if _CONDITION.search(paragraph) and (
            CONTAMINATION.search(paragraph) or _RESULT.search(paragraph)
        ):
            return {"status": "contaminated_or_ambiguous",
                    "reason": "article condition section contains a result/score marker"}
        for sentence in re.split(r"(?<=[.!?])\s+", html.unescape(paragraph)):
            if not _CONDITION.search(sentence):
                continue
            if CONTAMINATION.search(sentence) or _RESULT.search(sentence):
                return {"status": "contaminated_or_ambiguous",
                        "reason": "article condition section contains a result/score marker"}
            sentences.append(sentence.strip())
    snippet = " ".join(sentences)
    if len(snippet.split()) < 8 or len(snippet) > 900:
        return {"status": "needs_review", "reason": "no concise article-scoped condition evidence"}
    return {
        "status": "pre_match_candidate",
        "source_text": snippet,
        "article_published_at_utc": min(published).isoformat(),
        "article_modified_at_utc": max(modified).isoformat(),
    }


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
