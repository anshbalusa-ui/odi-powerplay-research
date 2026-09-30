#!/usr/bin/env python3
"""Index contemporaneous originals for *every* frozen HTTP-403 source.

This outcome-blind metadata-only step uses the same two public Wayback availability
anchors for every year and publisher. An index match never grants article approval;
`collect_pitch_expectation_archives.py` separately verifies exact raw replay bytes.
Store the versioned index and do not re-query to increase the eventual sample size.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import _utc, latest_publication_utc  # noqa: E402
from collect_pitch_expectation_archives import raw_replay_url  # noqa: E402

MAX_INDEX_BYTES = 100_000


def fetch_index(original_url: str, timestamp: str) -> tuple[dict, str, str]:
    query = urllib.parse.urlencode({"url": original_url, "timestamp": timestamp})
    request = urllib.request.Request(
        "https://archive.org/wayback/available?" + query,
        headers={"User-Agent": "ODI-powerplay-research/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        body = response.read(MAX_INDEX_BYTES + 1)
    if len(body) > MAX_INDEX_BYTES:
        raise ValueError("Wayback metadata response exceeds size limit")
    parsed = json.loads(body)
    return (parsed, hashlib.sha256(body).hexdigest(),
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))


def discover_original(report: dict, *, fetcher=fetch_index) -> dict:
    """Query near start, then near publication iff the first hit is ineligible."""
    if report.get("http_status") != "403" or report.get("status") != "needs_review":
        raise ValueError("archive indexing is restricted to failed frozen originals")
    original = report["source_url"]
    if urllib.parse.urlparse(original).scheme != "https":
        raise ValueError("frozen original source URL must use HTTPS")
    start = _utc(report["scheduled_start_utc"])
    publication = latest_publication_utc(report["published_at_utc"])
    if publication >= start:
        raise ValueError("source publication is not demonstrably before play")
    near_start = start - timedelta(seconds=1)
    near_publication = min(publication + timedelta(hours=1), near_start)
    anchors = (near_start.strftime("%Y%m%d%H%M%S"),
               near_publication.strftime("%Y%m%d%H%M%S"))
    key = report["cricsheet_match_id"]
    provenance = []
    for anchor in dict.fromkeys(anchors):
        try:
            metadata, digest, retrieved = fetcher(original, anchor)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            provenance.append({"anchor": anchor, "error": type(exc).__name__})
            continue
        entry = {
            "anchor": anchor, "retrieved_at_utc": retrieved,
            "response_sha256": digest,
        }
        provenance.append(entry)
        try:
            closest = metadata.get("archived_snapshots", {}).get("closest", {})
            timestamp = closest.get("timestamp", "")
            archive_url = closest.get("url", "")
            entry.update(closest_timestamp=timestamp, closest_status=closest.get("status", ""))
            if (closest.get("status") != "200" or not isinstance(timestamp, str)
                    or not re.fullmatch(r"\d{14}", timestamp)):
                continue
            archived = datetime.strptime(timestamp, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            if not publication <= archived < start:
                continue
            # Both index URL and raw replay must identify exactly this frozen original.
            raw_replay_url(archive_url, original)
            if not archive_url.endswith(f"/web/{timestamp}/{original}"):
                continue
            return {
                "match_id": key, "source_url": original, "status": "prestart_hit",
                "archive_status": "200", "archive_timestamp": timestamp,
                "archive_url": archive_url, "index_api": "availability_two_anchor",
                "index_queries": provenance,
            }
        except (AttributeError, ValueError, TypeError, KeyError) as exc:
            entry["rejection"] = type(exc).__name__
    return {
        "match_id": key, "source_url": original,
        "status": "index_error" if all("error" in q for q in provenance) else "none_or_late",
        "archive_status": "", "archive_timestamp": "", "archive_url": "",
        "index_api": "availability_two_anchor", "index_queries": provenance,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-screen", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if args.workers not in range(1, 7):
        raise ValueError("archive metadata workers must be 1..6")
    screens = [json.loads(line) for line in
               args.base_screen.read_text(encoding="utf-8").splitlines()]
    if len({row["cricsheet_match_id"] for row in screens}) != len(screens):
        raise ValueError("frozen source screen contains duplicate IDs")
    blocked = [row for row in screens if row.get("http_status") == "403"
               and row.get("status") == "needs_review"]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(discover_original, blocked))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(records, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "blocked_original_urls": len(blocked),
        "archive_index_statuses": dict(sorted(Counter(row["status"] for row in records).items())),
        "locked_test_scored": False,
    }, indent=2))


if __name__ == "__main__":
    main()
