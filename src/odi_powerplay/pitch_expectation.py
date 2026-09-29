"""Separate, outcome-blind pre-match expectation measurement (never legacy pitch codes)."""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
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
FORBIDDEN_INPUT_KEYS = {
    "winner", "winning_team", "batting_team_won", "batting_team_won_toss",
    "result", "match_result", "match_status", "result_method",
    "score", "scores", "scorecard", "final_score", "runs", "runs_scored", "innings",
    "innings_total", "innings_runs", "innings_1_runs", "innings_2_runs",
    "team_1_score", "team_2_score", "first_innings_total", "second_innings_total",
    "powerplay", "powerplay_runs", "powerplay_wickets", "pp_runs", "pp_wickets",
    "pp_legal_balls", "pp_delivery_events", "pp_run_rate", "pp_boundary_balls",
    "pp_boundary_pct", "pp_dot_balls",
    "pp_dot_ball_pct", "pp_complete", "pp0_runs", "pp0_wickets", "pp1_runs",
    "pp1_wickets", "pp2_runs", "pp2_wickets", "boundary_pct", "dot_pct",
    "chase", "chased", "chasing", "target", "old_pitch_code", "pitch_code",
    "pitch_primary_category", "batting_ease", "pace_seam_support", "spin_support",
    "bounce_profile", "two_paced_expected", "dew_expected", "pitch_effect",
    "pitch_effects", "effect_evidence_note", "pitch_confidence", "pitch_code_confidence",
    "coder_id", "coder_confidence", "confidence", "evidence",
    "pitch_evidence", "pitch_code_evidence",
    "pitch_reconciliation", "pitch_code_reconciliation", "original_spin_support",
    "reaudited_spin_support", "short_paraphrased_note", "reconciliation",
    "peer_output", "peer_assessment", "consensus", "assessment",
    "original_pitch_primary_category", "original_batting_ease",
    "original_pace_seam_support", "original_spin_support", "original_bounce_profile",
    "original_two_paced_expected", "original_dew_expected",
    "reaudited_pitch_primary_category", "reaudited_batting_ease",
    "reaudited_pace_seam_support", "reaudited_spin_support",
    "reaudited_bounce_profile", "reaudited_two_paced_expected",
    "reaudited_dew_expected", "coder1_pitch_primary_category", "coder2_pitch_primary_category",
    "reconciled_pitch_primary_category", "reconciliation_changed_from_coder1",
}
# Fail closed on obvious result/live coverage. This is NOT a substitute for source review.
CONTAMINATION = re.compile(
    r"\b(?:final score|match result|match report|post.match|live commentary|"
    r"scorecard|as it happened|won by \d+ (?:runs|wickets)|"
    r"won|lost|beat|beaten|defeats?|defeated|victor(?:y|ies)|conceded|clinched|"
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

def _article_timestamp(text: str) -> datetime:
    """Require a complete, offset-bearing ISO timestamp for source metadata."""
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        text,
    ):
        raise ValueError("article timestamps must include seconds and a UTC offset")
    return _utc(text)


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
    if FORBIDDEN_INPUT_KEYS & (set(report) | set(start)):
        raise ValueError("source input contains forbidden outcome or legacy assessment fields")
    projected = {field: report[field] for field in META_FIELDS if field != "scheduled_start_utc"}
    projected["scheduled_start_utc"] = start["scheduled_start_utc"]
    projected.update(source_text=text, source_hash=source_hash)
    if set(projected) != INPUT_KEYS or FORBIDDEN_INPUT_KEYS & set(projected):
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

def validate_screened_capture(report: dict, candidate: dict, capture: dict) -> None:
    """A newly screened source can revoke, but never itself grant, human approval."""
    key = report["cricsheet_match_id"]
    if (candidate.get("cricsheet_match_id") != key
            or any(candidate.get(field) != report[field] for field in (
                "source_url", "published_at_utc", "scheduled_start_utc"
            ))
            or not re.fullmatch(r"[0-9a-f]{64}", candidate.get("raw_sha256", ""))):
        raise ValueError(f"{key}: screened source identity or snapshot hash differs")
    route = candidate.get("source_access_route")
    if route is not None and route not in {"live_original", "archived_original"}:
        raise ValueError(f"{key}: unsupported source access route")
    if route == "archived_original":
        stamp = candidate.get("archive_timestamp")
        try:
            if not isinstance(stamp, str) or not re.fullmatch(r"\d{14}", stamp):
                raise ValueError("archive timestamp must contain 14 digits")
            archived = datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            _utc(candidate["retrieved_at_utc"])
            if (archived < latest_publication_utc(report["published_at_utc"])
                    or archived >= _utc(report["scheduled_start_utc"])
                    or candidate.get("http_status") != "403"
                    or candidate.get("archive_http_status") != 200
                    or candidate.get("archive_raw_sha256") != candidate["raw_sha256"]
                    or candidate.get("archive_retrieved_at_utc") != candidate["retrieved_at_utc"]
                    or candidate.get("archive_url") not in {
                        f"http://web.archive.org/web/{stamp}/{report['source_url']}",
                        f"https://web.archive.org/web/{stamp}/{report['source_url']}",
                    }
                    or candidate.get("archive_effective_url") !=
                    f"https://web.archive.org/web/{stamp}id_/{report['source_url']}"):
                raise ValueError("archive capture provenance differs from original source")
        except (KeyError, ValueError, TypeError):
            raise ValueError(f"{key}: archived original lacks verified prestart provenance") from None
    if capture.get("review_status") == "pre_match_content_verified":
        if (candidate.get("status") != "pre_match_candidate"
                or capture.get("retrieved_at_utc") != candidate.get("retrieved_at_utc")
                or not isinstance(capture.get("source_text"), str)
                or capture["source_text"] not in candidate.get("source_text", "")):
            raise ValueError(f"{key}: reviewed excerpt no longer passes current source screen")



def validate_passes(
    payloads: list[dict], passes: dict[str, list[dict]], source_release_sha256: str
) -> None:
    """Fail closed if any pass is incomplete or bound to different inputs/rubric."""
    if not isinstance(source_release_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", source_release_sha256
    ):
        raise ValueError("source release hash must be a lowercase SHA-256 digest")

    if set(passes) != {"A", "B", "C"}:
        raise ValueError("three separate assessor passes A/B/C are required")
    inputs = {row["cricsheet_match_id"]: row for row in payloads}
    if len(inputs) != len(payloads):
        raise ValueError("duplicate source IDs")
    if any(set(row) != INPUT_KEYS or FORBIDDEN_INPUT_KEYS & set(row) for row in payloads):
        raise ValueError("assessor input contains extra or forbidden fields")
    record_keys = {
        "cricsheet_match_id", "assessor_id", "model_name", "model_version",
        "reasoning_effort", "prompt_hash", "source_hash", "source_release_sha256",
        "run_id", "assessed_at_utc", "assessment",
    }
    frozen_hash = rubric_hash()
    run_ids = set()
    for assessor, rows in passes.items():
        if len(rows) != len(inputs):
            raise ValueError(f"pass {assessor} is incomplete")
        ids = set()
        for row in rows:
            key = row.get("cricsheet_match_id")
            if (set(row) != record_keys or key not in inputs or key in ids
                    or row["assessor_id"] != assessor
                    or row["source_hash"] != inputs[key]["source_hash"]
                    or row["source_release_sha256"] != source_release_sha256
                    or row["prompt_hash"] != frozen_hash):
                raise ValueError(f"pass {assessor} contains an invalid record")
            ids.add(key)
            if any(not isinstance(row[field], str) or not row[field].strip() for field in (
                "model_name", "model_version", "reasoning_effort", "run_id"
            )):
                raise ValueError("model/protocol provenance is incomplete")
            if row["run_id"] in run_ids:
                raise ValueError("run IDs must be distinct across assessor passes")
            run_ids.add(row["run_id"])
            _utc(row["assessed_at_utc"])
            validate_assessment(row["assessment"])
        if ids != set(inputs):
            raise ValueError(f"pass {assessor} source IDs differ")

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
    """Deterministically cover source routes and assessment quality dimensions."""
    if size <= 0:
        raise ValueError("size must be positive")
    candidates = sorted(rows, key=lambda row: row["cricsheet_match_id"])
    if len({row["cricsheet_match_id"] for row in candidates}) != len(candidates):
        raise ValueError("duplicate match in audit candidate set")
    target = min(size, len(candidates))
    selected: list[dict] = []
    used: set[str] = set()

    def add(row: dict) -> None:
        key = row["cricsheet_match_id"]
        if key not in used and len(selected) < target:
            selected.append(row)
            used.add(key)

    def choose(pool: list[dict], count: int) -> None:
        remaining = [row for row in pool if row["cricsheet_match_id"] not in used]
        for row in remaining[:max(0, min(count, target - len(selected)))]:
            add(row)

    for route in ("archived_original", "live_original"):
        routed = [row for row in candidates if row.get("source_access_route") == route]
        choose(routed, min(3, len(routed)))

    providers = sorted({
        urlparse(row["source_url"]).hostname or "" for row in candidates
    } - {""})
    for provider in providers[:2]:
        choose([row for row in candidates
                if (urlparse(row["source_url"]).hostname or "") == provider], 1)

    choose([row for row in candidates if not row["broad_eligible"]], 1)
    choose([row for row in candidates
            if row.get("overall_expected_environment") == "uncertain"], 1)
    choose([row for row in candidates if row["confidence"] >= 75], 1)

    seen: set[str] = set()
    while len(selected) < target:
        remaining = [row for row in candidates if row["cricsheet_match_id"] not in used]
        if not remaining:
            break

        def attributes(row: dict) -> set[str]:
            return {
                "category:" + row["overall_expected_environment"],
                "confidence:" + ("high" if row["confidence"] >= 75 else "lower"),
                "agreement:" + ("majority" if row["broad_eligible"] else "disagreement"),
                "year:" + row["match_date"][:4],
                "provider:" + (urlparse(row["source_url"]).hostname or ""),
                "route:" + str(row.get("source_access_route", "unknown")),
            }


        candidate = max(
            remaining,
            key=lambda row: (len(attributes(row) - seen),
                             -sum(str(row["cricsheet_match_id"]).encode("utf-8"))),
        )
        add(candidate)
        seen.update(attributes(candidate))
    return selected


class _ArticleParser(HTMLParser):
    """Collect article metadata and body text, excluding navigation cards."""

    def __init__(self, source_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.source_url = source_url
        self.published: list[str] = []
        self.modified: list[str] = []
        self.paragraphs: list[str] = []
        self.archive_paragraphs: list[str] = []
        self._elements: list[tuple[str, dict[str, str | None]]] = []
        self._article_depth = 0
        self._in_paragraph = False
        self._parts: list[str] = []
        self._jsonld = False
        self._jsonld_parts: list[str] = []
        self._jsonld_signature: tuple[object, object, object] | None = None
        self._jsonld_conflict = False
    def _inside_excluded_region(self) -> bool:
        excluded_tags = {"aside", "nav", "footer", "header"}
        excluded_classes = {
            "sidebar", "related", "related-story", "related-stories",
            "live-score", "live-scores", "scorecard", "navigation",
            "recommendations", "recommended", "widget", "story-card",
            "article-card", "latest-stories", "more-stories",
        }
        for tag, attrs in self._elements:
            markers = {
                marker.lower()
                for value in (attrs.get("class") or "", attrs.get("id") or "")
                for marker in re.split(r"[\s_-]+", value)
                if marker
            }
            values = " ".join((attrs.get("class") or "", attrs.get("id") or "")).lower()
            if (
                tag in excluded_tags
                or bool(excluded_classes & markers)
                or any(marker.startswith("related") for marker in markers)
                or any(marker in values for marker in ("live-score", "live-scorecard"))
            ):
                return True
        return False


    def _in_verified_body_container(
        self, tag: str, values: dict[str, str | None]
    ) -> bool:
        hostname = (urlparse(self.source_url).hostname or "").lower()
        if hostname.startswith("www."):
            hostname = hostname[4:]
        nodes = [*self._elements, (tag, values)]
        if hostname == "sportingnews.com":
            return any(
                name == "section" and attrs.get("id") == "article-body"
                for name, attrs in nodes
            )
        if hostname == "thenews.com.pk":
            return any(
                name == "div" and "story-detail" in (attrs.get("class") or "").split()
                for name, attrs in nodes
            )
        if hostname == "latestly.com":
            return any(
                parent_tag == "div"
                and "article-text" in (parent_attrs.get("class") or "").split()
                and child_tag == "div"
                and "main-body" in (child_attrs.get("class") or "").split()
                for (parent_tag, parent_attrs), (child_tag, child_attrs)
                in zip(nodes, nodes[1:])
            )
        if hostname == "thesportsrush.com":
            return any(
                name == "div"
                and {"prose", "content-part"} <= set((attrs.get("class") or "").split())
                for name, attrs in nodes
            )
        return False

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
        if tag == "time" and values.get("itemprop", "").lower() in {
            "datepublished", "datemodified"
        }:
            value = values.get("datetime")
            if value:
                target = (self.published if values["itemprop"].lower() == "datepublished"
                          else self.modified)
                target.append(value)
        if tag == "script" and (values.get("type") or "").split(";")[0].strip().lower() == (
            "application/ld+json"
        ):
            self._jsonld = True
            self._jsonld_parts = []
        if tag == "article":
            self._article_depth += 1
        if tag == "p" and not self._inside_excluded_region() and (
            self._article_depth or self._in_verified_body_container(tag, values)
        ):
            self._in_paragraph = True
            self._parts = []
        if tag not in {
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr",
        }:
            self._elements.append((tag, values))

    def handle_data(self, data: str) -> None:
        if self._jsonld:
            self._jsonld_parts.append(data)
        if self._in_paragraph:
            self._parts.append(data)

    @staticmethod
    def _objects(value: object):
        if isinstance(value, list):
            for item in value:
                yield from _ArticleParser._objects(item)
        elif isinstance(value, dict):
            yield value
            graph = value.get("@graph")
            if isinstance(graph, (dict, list)):
                yield from _ArticleParser._objects(graph)

    @staticmethod
    def _article_type(value: object) -> bool:
        types = value if isinstance(value, list) else [value]
        return any(
            isinstance(item, str)
            and item.rstrip("/").rsplit("/", 1)[-1].lower() in {
                "article", "newsarticle", "reportagearticle", "analysisnewsarticle",
                "reviewnewsarticle", "backgroundnewsarticle",
            }
            for item in types
        )

    @staticmethod
    def _url_values(value: object):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for key in ("@id", "url"):
                if isinstance(value.get(key), str):
                    yield value[key]

    def _same_article(self, value: dict) -> bool:
        expected = urlparse(self.source_url)
        expected_path = expected.path.rstrip("/") or "/"
        for raw_url in (*self._url_values(value.get("url")),
                        *self._url_values(value.get("mainEntityOfPage"))):
            actual = urlparse(raw_url)
            if (actual.scheme in {"http", "https"}
                    and actual.hostname
                    and actual.hostname.lower() == (expected.hostname or "").lower()
                    and actual.path.rstrip("/") == expected_path):
                return True
        return False

    def _consume_jsonld(self) -> None:
        try:
            data = json.loads("".join(self._jsonld_parts))
        except (json.JSONDecodeError, TypeError):
            return
        focal = [
            item for item in self._objects(data)
            if self._article_type(item.get("@type")) and self._same_article(item)
        ]
        for item in focal:
            published = item.get("datePublished")
            modified = item.get("dateModified")
            body = item.get("articleBody")
            signature = (published, modified, body)
            if self._jsonld_signature is not None and signature != self._jsonld_signature:
                self._jsonld_conflict = True
                continue
            self._jsonld_signature = signature
            if not isinstance(published, str) or not published.strip():
                continue
            self.published.append(published)
            if isinstance(modified, str) and modified.strip():
                self.modified.append(modified)
            if isinstance(body, str) and body.strip():
                target = (
                    self.paragraphs
                    if isinstance(modified, str) and modified.strip()
                    else self.archive_paragraphs
                )
                target.extend(
                    text.strip() for text in re.split(r"\n+", body) if text.strip()
                )

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._jsonld:
            self._consume_jsonld()
            self._jsonld = False
            self._jsonld_parts = []
        if tag == "p" and self._in_paragraph:
            paragraph = " ".join(" ".join(self._parts).split())
            if paragraph:
                self.paragraphs.append(paragraph)
            self._parts = []
            self._in_paragraph = False
        if tag == "article" and self._article_depth:
            self._article_depth -= 1
        for index in range(len(self._elements) - 1, -1, -1):
            if self._elements[index][0] == tag:
                del self._elements[index:]
                break

_CONDITION = re.compile(
    r"\b(?:pitch|surface|strip|conditions|seam|spin|turn|bounce|grass|"
    r"dust|tacky|moist|slow|dew|weather)\b", re.IGNORECASE
)
_RESULT = re.compile(
    r"\b(?:won|defeats?|victor(?:y|ies)|result|scorecard|final score|live commentary|"
    r"chase[ds]?|scored?|wickets?|highest ever|innings)\b|"
    r"\b\d{1,3}/\d{1,2}\b|\b\d{2,3}\b", re.IGNORECASE
)
_HARD_RESULT = re.compile(
    r"\b(?:final score|match result|match report|post.match|live commentary|"
    r"live scores?|live updates?|scorecard|as it happened|won by \d+ (?:runs|wickets)|"
    r"(?:innings|match) highlights)\b",
    re.IGNORECASE,
)



def extract_source_candidate(
    report: dict, html_text: str, archived_at_utc: str | None = None
) -> dict:
    """Quarantine unsafe pages; expose only short condition text after temporal checks.

    An archive capture may bound missing modification metadata, but does not
    override any modification metadata embedded in the captured page.
    """
    parser = _ArticleParser(report["source_url"])
    parser.feed(html_text)
    archived = None
    if archived_at_utc is not None:
        try:
            archived = _article_timestamp(archived_at_utc)
            scheduled = _utc(report["scheduled_start_utc"])
        except (ValueError, TypeError):
            return {"status": "needs_review", "reason": "archive timestamp cannot be verified"}
        if archived >= scheduled:
            return {"status": "contaminated_or_ambiguous", "reason": "archive capture is not pre-match"}
    if parser._jsonld_conflict:
        return {"status": "needs_review", "reason": "conflicting focal article structured metadata"}
    if not parser.published:
        return {"status": "needs_review", "reason": "article publication time missing"}
    if not parser.modified and archived_at_utc is None:
        return {"status": "needs_review", "reason": "article publication or modification time missing"}
    try:
        published = [_article_timestamp(value) for value in parser.published]
        modified = [_article_timestamp(value) for value in parser.modified]
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
    if max(published) >= scheduled:
        return {"status": "contaminated_or_ambiguous", "reason": "article could contain later edits"}
    if archived is not None and max(published) > archived:
        return {"status": "needs_review", "reason": "archive capture predates article publication"}
    if modified and (
        max(modified) >= scheduled
        or (archived is not None and max(modified) > archived)
    ):
        return {"status": "contaminated_or_ambiguous", "reason": "article could contain later edits"}
    if CONTAMINATION.search(report["source_title"]):
        return {"status": "contaminated_or_ambiguous", "reason": "source title resembles result coverage"}
    sentences = []
    unsafe_condition = False
    paragraphs = parser.paragraphs
    if archived is not None:
        paragraphs = [*paragraphs, *parser.archive_paragraphs]
    for paragraph in paragraphs:
        if _HARD_RESULT.search(paragraph):
            return {"status": "contaminated_or_ambiguous",
                    "reason": "article contains result or live-coverage markers"}
        for sentence in re.split(r"(?<=[.!?])\s+", html.unescape(paragraph)):
            if not _CONDITION.search(sentence):
                continue
            if CONTAMINATION.search(sentence) or _RESULT.search(sentence):
                unsafe_condition = True
                continue
            sentences.append(sentence.strip())
    sentences = list(dict.fromkeys(sentences))
    snippet = " ".join(sentences)
    if len(snippet.split()) < 8 or len(snippet) > 900:
        return {
            "status": "contaminated_or_ambiguous" if unsafe_condition and not sentences else "needs_review",
            "reason": ("no outcome-blind condition sentence" if unsafe_condition and not sentences
                       else "no concise article-scoped condition evidence"),
        }
    result = {
        "status": "pre_match_candidate",
        "source_text": snippet,
        "article_published_at_utc": min(published).isoformat(),
    }
    if modified:
        result["article_modified_at_utc"] = max(modified).isoformat()
    return result


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
