"""Create, validate, and merge source-audited pre-match pitch conditions."""

from __future__ import annotations

import hashlib
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse


PITCH_FIELDS = (
    "pitch_primary_category",
    "batting_ease",
    "pace_seam_support",
    "spin_support",
    "bounce_profile",
    "two_paced_expected",
    "dew_expected",
)
ALLOWED_VALUES = {
    "pitch_primary_category": {
        "batting_friendly",
        "balanced",
        "pace_seam",
        "spin",
        "slow_two_paced",
        "unknown",
    },
    "batting_ease": {"", "0", "1", "2"},
    "pace_seam_support": {"", "0", "1", "2"},
    "spin_support": {"", "0", "1", "2"},
    "bounce_profile": {"", "low", "standard", "steep", "variable"},
    "two_paced_expected": {"", "0", "1"},
    "dew_expected": {"", "0", "1"},
    "coder_confidence": {"high", "medium", "low"},
}
ESPN_LINKAGE_VALUES = {
    "unverified_candidate",
    "verified_match",
    "not_espn_id",
    "wrong_match",
    "not_available",
}
PITCH_QUEUE_FIELDS = (
    "cricsheet_match_id",
    "match_date",
    "event_name",
    "competition_type",
    "venue",
    "city",
    "team_1",
    "team_2",
    "espn_match_id_candidate",
    "espn_legacy_match_url_candidate",
    "espn_match_id_verified",
    "espn_match_url_verified",
    "espn_linkage_status",
    "source_search_query",
    "source_url",
    "source_title",
    "published_at_utc",
    "accessed_at_utc",
    "pre_match_verified",
    "coder_id",
    "coder_confidence",
    *PITCH_FIELDS,
    "short_paraphrased_note",
    "exclusion_reason",
)
PITCH_SET_ASIDE_FIELDS = (
    "cricsheet_match_id",
    "match_date",
    "event_name",
    "competition_type",
    "venue",
    "city",
    "team_1",
    "team_2",
    "source_search_query",
    "review_status",
    "exclusion_reason",
)


def espn_link_candidate(match_id: Any) -> dict[str, str]:
    """Return an unfetched ESPN linkage candidate for a probable numeric Cricinfo ID."""

    identifier = str(match_id or "").strip()
    if not identifier.isascii() or not identifier.isdigit():
        return {
            "espn_match_id_candidate": "",
            "espn_legacy_match_url_candidate": "",
            "espn_match_id_verified": "",
            "espn_match_url_verified": "",
            "espn_linkage_status": "not_available",
        }
    return {
        "espn_match_id_candidate": identifier,
        "espn_legacy_match_url_candidate": (
            f"https://www.espncricinfo.com/ci/engine/match/{identifier}.html"
        ),
        "espn_match_id_verified": "",
        "espn_match_url_verified": "",
        "espn_linkage_status": "unverified_candidate",
    }


def _is_espncricinfo_url(value: Any) -> bool:
    parsed = urlparse(str(value or "").strip())
    host = (parsed.hostname or "").casefold()
    if parsed.scheme not in {"http", "https"} or not host:
        return False
    if host == "espncricinfo.com" or host.endswith(".espncricinfo.com"):
        return True
    espn_domains = ("espn.com", "espn.in", "espn.com.au", "espn.co.uk")
    if not any(host == domain or host.endswith(f".{domain}") for domain in espn_domains):
        return False
    if parsed.path.startswith("/cricket/"):
        return True
    print_ids = parse_qs(parsed.query).get("id", [])
    return (
        parsed.path == "/espn/print"
        and len(print_ids) == 1
        and print_ids[0].isascii()
        and print_ids[0].isdigit()
    )


def validate_espn_linkage_rows(
    rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Validate unfetched candidates and human-verified ESPN match mappings."""

    issues: list[dict[str, str]] = []
    seen: set[str] = set()

    def issue(match_id: str, field: str, message: str) -> None:
        issues.append({"cricsheet_match_id": match_id, "field": field, "message": message})

    for row in rows:
        match_id = str(row.get("cricsheet_match_id", "")).strip()
        if not match_id:
            issue("", "cricsheet_match_id", "missing match ID")
            continue
        if match_id in seen:
            issue(match_id, "cricsheet_match_id", "duplicate match ID")
        seen.add(match_id)

        status = str(row.get("espn_linkage_status", "")).strip()
        if status not in ESPN_LINKAGE_VALUES:
            issue(match_id, "espn_linkage_status", f"unsupported value: {status}")
            continue
        candidate_id = str(row.get("espn_match_id_candidate", "")).strip()
        candidate_url = str(row.get("espn_legacy_match_url_candidate", "")).strip()
        verified_id = str(row.get("espn_match_id_verified", "")).strip()
        verified_url = str(row.get("espn_match_url_verified", "")).strip()

        if status == "unverified_candidate":
            expected = espn_link_candidate(match_id)
            if expected["espn_linkage_status"] != "unverified_candidate":
                issue(
                    match_id,
                    "espn_linkage_status",
                    "nonnumeric Cricsheet ID cannot be an ESPN ID candidate",
                )
            if candidate_id != expected["espn_match_id_candidate"]:
                issue(
                    match_id,
                    "espn_match_id_candidate",
                    "candidate must equal the numeric Cricsheet ID",
                )
            if candidate_url != expected["espn_legacy_match_url_candidate"]:
                issue(
                    match_id,
                    "espn_legacy_match_url_candidate",
                    "candidate URL does not match the unfetched legacy URL template",
                )
        elif status == "not_available" and (candidate_id or candidate_url):
            issue(
                match_id,
                "espn_linkage_status",
                "not_available rows cannot contain candidate linkage",
            )

        if status == "verified_match":
            if not verified_id.isascii() or not verified_id.isdigit():
                issue(
                    match_id,
                    "espn_match_id_verified",
                    "verified ESPN linkage requires a numeric match ID",
                )
            if not _is_espncricinfo_url(verified_url):
                issue(
                    match_id,
                    "espn_match_url_verified",
                    "verified ESPN linkage requires an ESPNcricinfo match URL",
                )
        elif verified_id or verified_url:
            issue(
                match_id,
                "espn_linkage_status",
                "verified ESPN ID or URL requires verified_match status",
            )

    return issues


def espn_linkage_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Summarize linkage state without fetching ESPN or reading outcomes."""

    materialized = list(rows)
    statuses = Counter(str(row.get("espn_linkage_status", "")).strip() for row in materialized)
    verified = statuses["verified_match"]
    return {
        "rows": len(materialized),
        "candidate_rows": sum(
            bool(str(row.get("espn_match_id_candidate", "")).strip()) for row in materialized
        ),
        "human_verified_rows": verified,
        "human_verified_pct": (
            round(100 * verified / len(materialized), 6) if materialized else 0.0
        ),
        "status_counts": dict(sorted(statuses.items())),
        "network_requests_performed": 0,
    }


def build_pitch_collection_queue(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one outcome-blind source-collection row per eligible match."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["match_id"])].append(row)

    queue: list[dict[str, Any]] = []
    for match_id in sorted(grouped, key=lambda value: (grouped[value][0]["match_date"], value)):
        match_rows = sorted(grouped[match_id], key=lambda row: int(row["innings_number"]))
        if len(match_rows) != 2:
            raise ValueError(f"Match {match_id} does not have exactly two innings rows")
        first = match_rows[0]
        team_1 = str(first["batting_team"])
        team_2 = str(first["opponent"])
        search_query = (
            f'site:espncricinfo.com "{team_1}" "{team_2}" '
            f'"{first["match_date"]}" preview pitch conditions'
        )
        espn_candidate = espn_link_candidate(match_id)
        queue.append(
            {
                "cricsheet_match_id": match_id,
                "match_date": first["match_date"],
                "event_name": first["event_name"],
                "competition_type": first["competition_type"],
                "venue": first["venue"],
                "city": first["city"],
                "team_1": team_1,
                "team_2": team_2,
                **espn_candidate,
                "source_search_query": search_query,
                "source_url": "",
                "source_title": "",
                "published_at_utc": "",
                "accessed_at_utc": "",
                "pre_match_verified": "",
                "coder_id": "",
                "coder_confidence": "",
                "pitch_primary_category": "",
                "batting_ease": "",
                "pace_seam_support": "",
                "spin_support": "",
                "bounce_profile": "",
                "two_paced_expected": "",
                "dew_expected": "",
                "short_paraphrased_note": "",
                "exclusion_reason": "",
            }
        )
    return queue


def select_next_pitch_batch(
    rows: Iterable[dict[str, Any]],
    *,
    completed_match_ids: set[str] | None = None,
    n: int = 25,
    seed: int = 20250905,
) -> list[dict[str, Any]]:
    """Select a deterministic outcome-blind batch with year and competition coverage."""

    if n < 1:
        raise ValueError("Batch size must be positive")
    completed = {str(value) for value in completed_match_ids or set()}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    seen: set[str] = set()
    for row in rows:
        match_id = str(row.get("cricsheet_match_id", "")).strip()
        if not match_id:
            raise ValueError("Queue row is missing cricsheet_match_id")
        if match_id in seen:
            raise ValueError(f"Duplicate queue match ID: {match_id}")
        seen.add(match_id)
        if match_id in completed:
            continue
        safe_row = {field: row.get(field, "") for field in PITCH_QUEUE_FIELDS}
        stratum = (
            str(safe_row["match_date"])[:4],
            str(safe_row["competition_type"]),
        )
        grouped[stratum].append(safe_row)

    random_generator = random.Random(seed)
    for values in grouped.values():
        values.sort(key=lambda row: str(row["cricsheet_match_id"]))
        random_generator.shuffle(values)

    selected: list[dict[str, Any]] = []
    positions = {stratum: 0 for stratum in grouped}
    strata = sorted(grouped)
    random_generator.shuffle(strata)

    def take(stratum: tuple[str, str]) -> bool:
        position = positions[stratum]
        values = grouped[stratum]
        if position >= len(values) or len(selected) >= n:
            return False
        selected.append({**values[position], "batch_sequence": len(selected) + 1})
        positions[stratum] += 1
        return True

    years = sorted({stratum[0] for stratum in strata})
    random_generator.shuffle(years)
    for year in years:
        candidates = [
            stratum
            for stratum in strata
            if stratum[0] == year and positions[stratum] < len(grouped[stratum])
        ]
        random_generator.shuffle(candidates)
        if candidates:
            take(candidates[0])

    represented_competitions = {str(row["competition_type"]) for row in selected}
    competitions = sorted({stratum[1] for stratum in strata} - represented_competitions)
    random_generator.shuffle(competitions)
    for competition in competitions:
        candidates = [
            stratum
            for stratum in strata
            if stratum[1] == competition and positions[stratum] < len(grouped[stratum])
        ]
        random_generator.shuffle(candidates)
        if candidates:
            take(candidates[0])

    while len(selected) < n:
        added = False
        for stratum in strata:
            added = take(stratum) or added
            if len(selected) == n:
                break
        if not added:
            break
    return selected


def _parse_timestamp(value: Any) -> datetime | None:
    normalized = str(value or "").strip().replace("Z", "+00:00")
    if not normalized:
        return None
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def validate_pitch_rows(
    rows: Iterable[dict[str, Any]],
    *,
    eligible_match_ids: set[str] | None = None,
    match_start_by_id: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    """Return validation issues; only verified pre-match rows may enter a model table."""

    issues: list[dict[str, str]] = []
    seen: set[str] = set()

    def issue(match_id: str, field: str, message: str) -> None:
        issues.append({"cricsheet_match_id": match_id, "field": field, "message": message})

    for row in rows:
        match_id = str(row.get("cricsheet_match_id", "")).strip()
        if not match_id:
            issue("", "cricsheet_match_id", "missing match ID")
            continue
        if match_id in seen:
            issue(match_id, "cricsheet_match_id", "duplicate match ID")
        seen.add(match_id)
        if eligible_match_ids is not None and match_id not in eligible_match_ids:
            issue(match_id, "cricsheet_match_id", "match is outside the eligible primary cohort")

        verified = str(row.get("pre_match_verified", "")).strip()
        if verified not in {"0", "1"}:
            issue(match_id, "pre_match_verified", "must be 0 or 1")
            continue
        if verified == "0":
            if not str(row.get("exclusion_reason", "")).strip():
                issue(match_id, "exclusion_reason", "required when source is not verified")
            continue

        source_url = str(row.get("source_url", "")).strip()
        parsed_url = urlparse(source_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            issue(match_id, "source_url", "verified rows require an HTTP(S) source URL")
        for field in ("source_title", "coder_id", "coder_confidence", "pitch_primary_category"):
            if not str(row.get(field, "")).strip():
                issue(match_id, field, "required for verified rows")

        espn_status = str(row.get("espn_linkage_status", "")).strip()
        if espn_status and espn_status not in ESPN_LINKAGE_VALUES:
            issue(match_id, "espn_linkage_status", f"unsupported value: {espn_status}")
        if _is_espncricinfo_url(source_url) and espn_status != "verified_match":
            issue(
                match_id,
                "espn_linkage_status",
                "ESPN source rows require independently verified match linkage",
            )
        verified_espn_id = str(row.get("espn_match_id_verified", "")).strip()
        verified_espn_url = str(row.get("espn_match_url_verified", "")).strip()
        if espn_status == "verified_match":
            if not verified_espn_id.isascii() or not verified_espn_id.isdigit():
                issue(
                    match_id,
                    "espn_match_id_verified",
                    "verified ESPN linkage requires a numeric match ID",
                )
            if not _is_espncricinfo_url(verified_espn_url):
                issue(
                    match_id,
                    "espn_match_url_verified",
                    "verified ESPN linkage requires an ESPNcricinfo match URL",
                )
        elif verified_espn_id or verified_espn_url:
            issue(
                match_id,
                "espn_linkage_status",
                "verified ESPN ID or URL requires verified_match status",
            )

        published_at = _parse_timestamp(row.get("published_at_utc"))
        accessed_at = _parse_timestamp(row.get("accessed_at_utc"))
        if published_at is None:
            issue(match_id, "published_at_utc", "must be an ISO-8601 timestamp")
        if accessed_at is None:
            issue(match_id, "accessed_at_utc", "must be an ISO-8601 timestamp")
        if published_at and accessed_at and published_at > accessed_at:
            issue(match_id, "published_at_utc", "cannot be after access time")

        if match_start_by_id is not None:
            match_start = _parse_timestamp(match_start_by_id.get(match_id))
            if match_start is None:
                issue(
                    match_id, "match_start_utc", "verified timing requires a match start timestamp"
                )
            elif published_at and published_at >= match_start:
                issue(match_id, "published_at_utc", "source was not published before match start")

        for field, allowed in ALLOWED_VALUES.items():
            value = str(row.get(field, "")).strip()
            if field in {"coder_confidence", "pitch_primary_category"} and not value:
                continue
            if value not in allowed:
                issue(match_id, field, f"unsupported value: {value}")

        note = str(row.get("short_paraphrased_note", "")).strip()
        if not note:
            issue(match_id, "short_paraphrased_note", "verified rows require a short paraphrase")
        elif len(note) > 300:
            issue(match_id, "short_paraphrased_note", "must not exceed 300 characters")

    return issues


def pitch_coverage_summary(
    rows: Iterable[dict[str, Any]],
    *,
    eligible_match_count: int | None = None,
) -> dict[str, Any]:
    """Summarize verified coverage without using match outcomes."""

    materialized = list(rows)
    verified = [row for row in materialized if str(row.get("pre_match_verified", "")) == "1"]
    denominator = len(materialized) if eligible_match_count is None else eligible_match_count
    if denominator < len(verified):
        raise ValueError("Eligible match count cannot be smaller than verified pitch count")
    by_year = Counter(str(row.get("match_date", ""))[:4] for row in verified)
    by_category = Counter(str(row.get("pitch_primary_category", "")) for row in verified)
    return {
        "attempted_matches": len(materialized),
        "eligible_cohort_matches": denominator,
        "verified_pitch_matches": len(verified),
        "coverage_pct": round(100 * len(verified) / denominator, 6) if denominator else 0.0,
        "verified_by_year": dict(sorted(by_year.items())),
        "verified_by_primary_category": dict(sorted(by_category.items())),
    }


def build_pitch_set_aside(rows: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Project excluded attempts into an outcome-blind follow-up queue."""

    set_aside: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        match_id = str(row.get("cricsheet_match_id", "")).strip()
        if not match_id:
            raise ValueError("Pitch row is missing cricsheet_match_id")
        if match_id in seen:
            raise ValueError(f"Duplicate pitch match ID: {match_id}")
        seen.add(match_id)

        verified = str(row.get("pre_match_verified", "")).strip()
        if verified not in {"0", "1"}:
            raise ValueError(f"Match {match_id}: pre_match_verified must be 0 or 1")
        if verified == "1":
            continue

        exclusion_reason = str(row.get("exclusion_reason", "")).strip()
        if not exclusion_reason:
            raise ValueError(f"Match {match_id}: excluded row is missing exclusion_reason")
        output = {
            field: ("set_aside" if field == "review_status" else str(row.get(field, "")).strip())
            for field in PITCH_SET_ASIDE_FIELDS
        }
        set_aside.append(output)

    return sorted(
        set_aside,
        key=lambda row: (row["match_date"], row["cricsheet_match_id"]),
    )


def _verified_pitch_rows_by_match(
    rows: Iterable[dict[str, Any]],
    *,
    coding_set: str,
) -> tuple[int, dict[str, dict[str, Any]]]:
    materialized = list(rows)
    verified: dict[str, dict[str, Any]] = {}
    for row in materialized:
        match_id = str(row.get("cricsheet_match_id", "")).strip()
        flag = str(row.get("pre_match_verified", "")).strip()
        if flag not in {"0", "1"}:
            raise ValueError(f"{coding_set}: pre_match_verified must be 0 or 1")
        if flag == "0":
            continue
        if not match_id:
            raise ValueError(f"{coding_set}: verified row is missing cricsheet_match_id")
        if match_id in verified:
            raise ValueError(f"{coding_set}: duplicate verified match ID {match_id}")
        if not str(row.get("coder_id", "")).strip():
            raise ValueError(f"{coding_set}: verified match {match_id} is missing coder_id")
        for field in PITCH_FIELDS:
            value = str(row.get(field, "")).strip()
            if value not in ALLOWED_VALUES[field]:
                raise ValueError(
                    f"{coding_set}: verified match {match_id} has unsupported "
                    f"{field} value {value!r}"
                )
        verified[match_id] = row
    return len(materialized), verified


def _categorical_agreement(
    first: list[str],
    second: list[str],
) -> dict[str, int | float | None]:
    comparable = [
        (left, right) for left, right in zip(first, second, strict=True) if left and right
    ]
    n = len(comparable)
    if not n:
        return {
            "comparable_pairs": 0,
            "agreement_count": 0,
            "agreement_pct": None,
            "cohen_kappa": None,
        }

    agreements = sum(left == right for left, right in comparable)
    first_counts = Counter(left for left, _ in comparable)
    second_counts = Counter(right for _, right in comparable)
    labels = first_counts.keys() | second_counts.keys()
    expected = sum(first_counts[label] * second_counts[label] for label in labels) / (n * n)
    observed = agreements / n
    kappa = None if math.isclose(expected, 1.0) else (observed - expected) / (1.0 - expected)
    return {
        "comparable_pairs": n,
        "agreement_count": agreements,
        "agreement_pct": round(100 * observed, 6),
        "cohen_kappa": round(kappa, 6) if kappa is not None else None,
    }


def pitch_intercoder_reliability(
    reference_rows: Iterable[dict[str, Any]],
    recoded_rows: Iterable[dict[str, Any]],
    *,
    minimum_double_coded_fraction: float = 0.2,
) -> dict[str, Any]:
    """Compare independently coded verified rows without reading match outcomes."""

    if not 0 < minimum_double_coded_fraction <= 1:
        raise ValueError("minimum_double_coded_fraction must be in (0, 1]")

    reference_received, reference = _verified_pitch_rows_by_match(
        reference_rows,
        coding_set="reference",
    )
    recoded_received, recoded = _verified_pitch_rows_by_match(
        recoded_rows,
        coding_set="recoded",
    )
    paired_ids = sorted(reference.keys() & recoded.keys())
    for match_id in paired_ids:
        reference_coder = str(reference[match_id].get("coder_id", "")).strip()
        recoded_coder = str(recoded[match_id].get("coder_id", "")).strip()
        if reference_coder == recoded_coder:
            raise ValueError(
                f"match {match_id} was not independently coded: coder_id is "
                f"{reference_coder!r} in both sets"
            )

    field_metrics: dict[str, dict[str, int | float | None]] = {}
    total_comparable = 0
    total_agreements = 0
    for field in PITCH_FIELDS:
        first = [str(reference[match_id].get(field, "")).strip() for match_id in paired_ids]
        second = [str(recoded[match_id].get(field, "")).strip() for match_id in paired_ids]
        metrics = _categorical_agreement(first, second)
        comparable = int(metrics["comparable_pairs"])
        field_metrics[field] = {
            **metrics,
            "paired_matches": len(paired_ids),
            "missing_either": len(paired_ids) - comparable,
            "completion_pct": (round(100 * comparable / len(paired_ids), 6) if paired_ids else 0.0),
        }
        total_comparable += comparable
        total_agreements += int(metrics["agreement_count"])

    reference_count = len(reference)
    paired_count = len(paired_ids)
    minimum_pairs = math.ceil(reference_count * minimum_double_coded_fraction)
    paired_ids_sha256 = hashlib.sha256("\n".join(paired_ids).encode()).hexdigest()
    return {
        "reference_rows_received": reference_received,
        "recoded_rows_received": recoded_received,
        "reference_verified_matches": reference_count,
        "recoded_verified_matches": len(recoded),
        "paired_verified_matches": paired_count,
        "unpaired_reference_matches": len(reference.keys() - recoded.keys()),
        "orphan_recoded_matches": len(recoded.keys() - reference.keys()),
        "paired_match_ids_sha256": paired_ids_sha256,
        "minimum_double_coded_fraction": minimum_double_coded_fraction,
        "minimum_double_coded_matches": minimum_pairs,
        "double_coded_pct": (
            round(100 * paired_count / reference_count, 6) if reference_count else 0.0
        ),
        "meets_minimum_double_coding_target": (
            reference_count > 0 and paired_count >= minimum_pairs
        ),
        "overall_comparable_items": total_comparable,
        "overall_agreement_count": total_agreements,
        "overall_agreement_pct": (
            round(100 * total_agreements / total_comparable, 6) if total_comparable else None
        ),
        "fields": field_metrics,
    }


def merge_pitch_conditions(
    innings_rows: Iterable[dict[str, Any]],
    pitch_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Left-join verified pitch codes to innings without source prose or outcomes."""

    pitch_by_match = {
        str(row["cricsheet_match_id"]): row
        for row in pitch_rows
        if str(row.get("pre_match_verified", "")) == "1"
    }
    merged: list[dict[str, Any]] = []
    for innings in innings_rows:
        output = dict(innings)
        pitch = pitch_by_match.get(str(innings["match_id"]))
        output["pitch_available"] = int(pitch is not None)
        for field in PITCH_FIELDS:
            output[field] = pitch.get(field, "") if pitch else ""
        merged.append(output)
    return merged
