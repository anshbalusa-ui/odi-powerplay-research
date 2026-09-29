#!/usr/bin/env python3
"""Collect pre-start Wayback captures for sources that failed live retrieval.

Raw archived HTML is kept in ignored, append-only snapshots. This script emits only
short candidates screened by the existing article parser; raw pages never enter the
review/assessment output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import canonical_json, extract_source_candidate  # noqa: E402

MAX_ARCHIVE_BYTES = 2_000_000
_ARCHIVE_URL = re.compile(
    r"https?://web\.archive\.org/web/(\d{14})/(https?://[^\s]+)\Z"
)
_REPLAY_URL = re.compile(
    r"https://web\.archive\.org/web/(\d{14})id_/(https?://[^\s]+)\Z"
)
_DATE_ONLY = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_FULL_UTC = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:\d{2})\Z"
)
_SCREENED_ROW_FIELDS = (
    "source_text", "article_published_at_utc", "article_modified_at_utc", "reason",
)


class ArchiveError(ValueError):
    """A capture cannot be safely identified, bounded, or verified."""


@dataclass(frozen=True)
class FetchResult:
    body: bytes
    final_url: str
    http_status: int
    retrieved_at_utc: str
    content_length: int | None = None


class _IdentityRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow only HTTPS Wayback redirects to the same timestamp and source URL."""

    def __init__(self, timestamp: str, source_url: str):
        super().__init__()
        self.timestamp = timestamp
        self.source_url = source_url

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _is_same_replay_identity(newurl, self.timestamp, self.source_url):
            raise urllib.error.HTTPError(
                newurl, code, "Wayback redirect changed capture identity", headers, fp
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _parse_time(value: str, *, date_only_start: bool = False) -> datetime:
    """Parse a full timezone-aware timestamp, or a conservative registry date."""
    if not isinstance(value, str):
        raise ArchiveError("registry timestamp is missing")
    if _DATE_ONLY.fullmatch(value):
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError as exc:
            raise ArchiveError("registry date is invalid") from exc
        boundary = parsed_date if date_only_start else parsed_date + timedelta(days=1)
        return datetime.combine(boundary, time.min, timezone.utc)
    if not _FULL_UTC.fullmatch(value):
        raise ArchiveError("registry timestamp is not a strict full date")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ArchiveError("registry timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise ArchiveError("registry timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def _timestamp_datetime(timestamp: str) -> datetime:
    if not isinstance(timestamp, str) or not re.fullmatch(r"\d{14}", timestamp):
        raise ArchiveError("archive timestamp must contain 14 digits")
    try:
        parsed = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
    except ValueError as exc:
        raise ArchiveError("archive timestamp is invalid") from exc
    if parsed.strftime("%Y%m%d%H%M%S") != timestamp:
        raise ArchiveError("archive timestamp is invalid")
    return parsed.replace(tzinfo=timezone.utc)


def _is_same_replay_identity(url: str, timestamp: str, source_url: str) -> bool:
    match = _REPLAY_URL.fullmatch(url)
    return bool(match and match.group(1) == timestamp and match.group(2) == source_url)


def raw_replay_url(archive_url: str, source_url: str) -> str:
    """Translate an exact index replay URL to its HTTPS, raw ``id_`` replay."""
    match = _ARCHIVE_URL.fullmatch(archive_url) if isinstance(archive_url, str) else None
    if not match or match.group(2) != source_url:
        raise ArchiveError("archive URL does not identify the frozen original URL")
    return f"https://web.archive.org/web/{match.group(1)}id_/{source_url}"


def _validated_record(report: dict, record: dict) -> tuple[str, str, str]:
    key = str(report.get("cricsheet_match_id", ""))
    if record.get("status") != "prestart_hit":
        raise ArchiveError("archive index record is not a prestart hit")
    if str(record.get("match_id", "")) != key:
        raise ArchiveError("archive index match identity differs from frozen registry")
    if record.get("source_url") != report.get("source_url"):
        raise ArchiveError("archive index source URL differs from frozen registry")
    if str(record.get("archive_status", "")) != "200":
        raise ArchiveError("archive index did not report HTTP 200")
    timestamp = record.get("archive_timestamp", "")
    archive_dt = _timestamp_datetime(timestamp)
    archive_url = record.get("archive_url", "")
    raw_url = raw_replay_url(archive_url, report["source_url"])
    match = _ARCHIVE_URL.fullmatch(archive_url)
    if not match or match.group(1) != timestamp:
        raise ArchiveError("archive URL timestamp differs from archive index")
    publication = _parse_time(report.get("published_at_utc", ""))
    scheduled_start = _parse_time(
        report.get("scheduled_start_utc", ""), date_only_start=True
    )
    if archive_dt < publication:
        raise ArchiveError("archive capture predates frozen source publication")
    if archive_dt >= scheduled_start:
        raise ArchiveError("archive capture is not strictly before scheduled start")
    return timestamp, archive_url, raw_url


def _retrieval_time() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _retrieval_token(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ArchiveError("retrieval timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise ArchiveError("retrieval timestamp has no timezone")
    return parsed.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def fetch_archive(raw_url: str) -> FetchResult:
    """Fetch bounded raw Wayback bytes with TLS verification and identity-safe redirects."""
    match = _REPLAY_URL.fullmatch(raw_url)
    if not match:
        raise ArchiveError("raw replay URL is not an HTTPS Wayback capture")
    request = urllib.request.Request(
        raw_url,
        headers={"User-Agent": "ODI-powerplay-research/1.0", "Accept": "text/html"},
    )
    opener = urllib.request.build_opener(_IdentityRedirectHandler(match.group(1), match.group(2)))
    try:
        with opener.open(request, timeout=25) as response:
            status = int(response.getcode())
            final_url = response.geturl()
            length = response.headers.get("Content-Length")
            try:
                declared_length = int(length) if length is not None else None
            except ValueError:
                declared_length = None
            body = (b"" if declared_length is not None and declared_length > MAX_ARCHIVE_BYTES
                    else response.read(MAX_ARCHIVE_BYTES + 1))
            return FetchResult(
                body, final_url, status, _retrieval_time(), declared_length
            )
    except urllib.error.HTTPError as exc:
        return FetchResult(b"", exc.geturl(), int(exc.code), _retrieval_time())


def _failure_row(report: dict, reason: str, status: str = "needs_review") -> dict:
    row = {key: value for key, value in report.items() if key not in _SCREENED_ROW_FIELDS}
    row["status"] = status
    row["reason"] = reason
    return row

def _snapshot_paths(raw_dir: Path, key: str, timestamp: str) -> list[Path]:
    return sorted(raw_dir.glob(f"{key}.{timestamp}.*.json"))


def _load_snapshot(
    raw_dir: Path, report: dict, archive_url: str, timestamp: str,
) -> tuple[dict, bytes] | None:
    metadata_files = _snapshot_paths(raw_dir, str(report["cricsheet_match_id"]), timestamp)
    if not metadata_files:
        return None
    metadata_path = metadata_files[-1]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise ArchiveError("cached archive metadata is invalid")
        snapshot_name = metadata["snapshot_filename"]
        if not isinstance(snapshot_name, str) or Path(snapshot_name).name != snapshot_name:
            raise ArchiveError("cached archive snapshot path is invalid")
        token = _retrieval_token(metadata.get("retrieved_at_utc"))
        expected_stem = f"{report['cricsheet_match_id']}.{timestamp}.{token}"
        if (metadata_path.name != f"{expected_stem}.json"
                or snapshot_name != f"{expected_stem}.html"):
            raise ArchiveError("cached archive snapshot filename mismatch")
        body = (raw_dir / snapshot_name).read_bytes()
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ArchiveError("cached archive snapshot is incomplete") from exc
    if (metadata.get("cricsheet_match_id") != str(report["cricsheet_match_id"])
            or metadata.get("source_url") != report.get("source_url")
            or metadata.get("archive_url") != archive_url
            or metadata.get("archive_timestamp") != timestamp
            or metadata.get("http_status") != 200
            or not _is_same_replay_identity(
                metadata.get("effective_url", ""), timestamp, report["source_url"]
            )):
        raise ArchiveError("cached archive snapshot identity mismatch")
    digest = hashlib.sha256(body).hexdigest()
    if (len(body) > MAX_ARCHIVE_BYTES or len(body) != metadata.get("size_bytes")
            or digest != metadata.get("raw_sha256")):
        raise ArchiveError("cached archive snapshot checksum or size mismatch")
    return metadata, body


def _save_snapshot(
    raw_dir: Path, report: dict, archive_url: str, timestamp: str, result: FetchResult,
) -> dict:
    body = result.body
    if result.http_status != 200:
        raise ArchiveError(f"archive replay returned HTTP {result.http_status}")
    if not _is_same_replay_identity(result.final_url, timestamp, report["source_url"]):
        raise ArchiveError("archive replay redirect changed capture identity")
    if result.content_length is not None and result.content_length > MAX_ARCHIVE_BYTES:
        raise ArchiveError("archive replay exceeds the 2 MB limit")
    if len(body) > MAX_ARCHIVE_BYTES:
        raise ArchiveError("archive replay exceeds the 2 MB limit")
    if result.content_length is not None and result.content_length != len(body):
        raise ArchiveError("archive replay body is incomplete")
    token = _retrieval_token(result.retrieved_at_utc)
    key = str(report["cricsheet_match_id"])
    snapshot_name = f"{key}.{timestamp}.{token}.html"
    metadata_name = f"{key}.{timestamp}.{token}.json"
    metadata = {
        "archive_timestamp": timestamp,
        "archive_url": archive_url,
        "cricsheet_match_id": key,
        "effective_url": result.final_url,
        "http_status": result.http_status,
        "raw_sha256": hashlib.sha256(body).hexdigest(),
        "retrieved_at_utc": result.retrieved_at_utc,
        "size_bytes": len(body),
        "snapshot_filename": snapshot_name,
        "source_url": report["source_url"],
    }
    raw_dir.mkdir(parents=True, exist_ok=True)
    with (raw_dir / snapshot_name).open("xb") as handle:
        handle.write(body)
    with (raw_dir / metadata_name).open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return metadata


def collect_one(
    report: dict, record: dict, raw_dir: Path, *, fetcher=fetch_archive,
) -> dict:
    """Fetch or verify one capture and release only its screened candidate text."""
    try:
        timestamp, archive_url, raw_url = _validated_record(report, record)
    except (ArchiveError, KeyError, TypeError) as exc:
        return _failure_row(report, str(exc))

    try:
        cached = _load_snapshot(raw_dir, report, archive_url, timestamp)
        if cached is None:
            result = fetcher(raw_url)
            metadata = _save_snapshot(raw_dir, report, archive_url, timestamp, result)
            body = result.body
        else:
            metadata, body = cached
    except (ArchiveError, OSError, urllib.error.URLError, TimeoutError,
            ValueError, KeyError, TypeError) as exc:
        return _failure_row(report, str(exc) or "archive retrieval failed")

    provenance = {
        "archive_url": archive_url,
        "archive_timestamp": timestamp,
        "archive_http_status": metadata["http_status"],
        "archive_retrieved_at_utc": metadata["retrieved_at_utc"],
        "retrieved_at_utc": metadata["retrieved_at_utc"],
        "raw_sha256": metadata["raw_sha256"],
        "source_access_route": "archived_original",
        "archive_raw_sha256": metadata["raw_sha256"],
        "archive_snapshot_filename": metadata["snapshot_filename"],
        "archive_effective_url": metadata["effective_url"],
    }
    try:
        screened = extract_source_candidate(
            report, body.decode("utf-8", errors="replace"),
            archived_at_utc=f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}T"
                            f"{timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:14]}Z",
        )
    except (ValueError, TypeError, UnicodeError) as exc:
        return {**_failure_row(report, "archived content could not be screened"), **provenance}
    if screened.get("status") != "pre_match_candidate" or not screened.get("source_text"):
        reason = screened.get("reason", "archived content did not pass source screening")
        status = screened.get("status", "needs_review")
        if status not in {"needs_review", "contaminated_or_ambiguous"}:
            status = "needs_review"
        return {**_failure_row(report, str(reason), status), **provenance}

    row = {key: value for key, value in report.items() if key not in _SCREENED_ROW_FIELDS}
    row.update(provenance)
    row.update({
        key: screened[key] for key in (
            "status", "source_text", "article_published_at_utc", "article_modified_at_utc"
        ) if key in screened
    })
    return row


def merge_candidates(
    base_rows: list[dict], archive_records: list[dict], raw_dir: Path, *, fetcher=fetch_archive,
) -> list[dict]:
    """Replace only base rows with explicit prestart hits; preserve the full universe."""
    by_key: dict[str, dict] = {}
    for row in base_rows:
        key = str(row.get("cricsheet_match_id", ""))
        if not key or key in by_key:
            raise ValueError("base screen must have unique, non-empty match IDs")
        by_key[key] = row
    archive_by_key: dict[str, dict] = {}
    for record in archive_records:
        key = str(record.get("match_id", ""))
        if not key or key in archive_by_key:
            raise ValueError("archive index must have unique, non-empty match IDs")
        archive_by_key[key] = record
    unknown_hits = {
        key for key, record in archive_by_key.items()
        if record.get("status") == "prestart_hit" and key not in by_key
    }
    if unknown_hits:
        raise ValueError("archive index prestart hit is absent from the base screen")
    merged = []
    for base in base_rows:
        record = archive_by_key.get(str(base["cricsheet_match_id"]))
        if record is not None and record.get("status") == "prestart_hit":
            if base.get("status") != "needs_review" or base.get("http_status") != "403":
                raise ValueError("archive recovery requires failed live retrieval HTTP 403")
            merged.append(collect_one(base, record, raw_dir, fetcher=fetcher))
        else:
            merged.append(dict(base))
    return merged


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_number}") from exc
    return rows


def run(base_screen: Path, archive_index: Path, raw_dir: Path, output: Path) -> list[dict]:
    base_rows = _read_jsonl(base_screen)
    records = json.loads(archive_index.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("archive index must be a JSON list")
    merged = merge_candidates(base_rows, records, raw_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        handle.write("".join(canonical_json(row) + "\n" for row in merged))
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-screen", type=Path, required=True,
                        help="227-row source candidate baseline JSONL")
    parser.add_argument("--archive-index", type=Path, required=True,
                        help="Wayback metadata-only availability index JSON")
    parser.add_argument("--raw-dir", type=Path, required=True,
                        help="ignored directory for immutable raw snapshots and metadata")
    parser.add_argument("--output", type=Path, required=True,
                        help="new versioned source-candidate JSONL (never overwritten)")
    args = parser.parse_args()
    merged = run(args.base_screen, args.archive_index, args.raw_dir, args.output)
    from collections import Counter
    counts = Counter(row.get("status", "missing") for row in merged)
    print(json.dumps({
        "candidate_count": len(merged),
        "unique_match_ids": len({row["cricsheet_match_id"] for row in merged}),
        "source_statuses": dict(sorted(counts.items())),
        "raw_html_in_output": False,
    }, indent=2))


if __name__ == "__main__":
    main()
