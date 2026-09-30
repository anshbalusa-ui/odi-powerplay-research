#!/usr/bin/env python3
"""Quarantine fetched HTML; emit only temporally screened article-condition candidates.

This curator-side transport NEVER supplies raw HTML, historical labels, or results to
assessment models. Candidate text requires separate source review before release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.pitch_expectation import (  # noqa: E402
    META_FIELDS, canonical_json, eligible_sources, extract_source_candidate,
)
from build_pitch_expectation_inputs import selected_csv  # noqa: E402


def acquire(report: dict, raw_dir: Path, retry_transient: bool = False) -> dict:
    """Reuse immutable snapshots; optionally append a new attempt after a timeout."""
    key = report["cricsheet_match_id"]
    prior = sorted(raw_dir.glob(f"{key}.*.json"))
    if prior:
        metadata = json.loads(prior[-1].read_text(encoding="utf-8"))
        if metadata["source_url"] != report["source_url"] or metadata["cricsheet_match_id"] != key:
            raise ValueError(f"{key}: cached source identity differs from frozen registry")
        raw_path = raw_dir / metadata["snapshot_filename"]
        raw = raw_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != metadata["raw_sha256"]:
            raise ValueError(f"{key}: immutable source snapshot hash mismatch")
    if not prior or (retry_transient and metadata["curl_exit_status"] == 28
                     and metadata["http_status"] == "000"):
        proc = subprocess.run(
            ["curl", "--proto", "=https", "--proto-redir", "=https",
             "--location", "--silent", "--show-error", "--fail",
             "--max-redirs", "3", "--connect-timeout", "6", "--max-time", "20",
             "--max-filesize", "2000000", "--user-agent", "ODI-powerplay-research/1.0",
             "--write-out", "%{http_code}", report["source_url"]],
            capture_output=True, timeout=25, check=False,
        )
        received = datetime.now(timezone.utc).isoformat()
        http_code = proc.stdout[-3:].decode("ascii", errors="replace")
        raw = proc.stdout[:-3] if http_code.isdigit() else b""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        raw_dir.mkdir(parents=True, exist_ok=True)
        snapshot = f"{key}.{stamp}.html"
        metadata = {
            "cricsheet_match_id": key,
            "source_url": report["source_url"],
            "retrieved_at_utc": received,
            "http_status": http_code,
            "curl_exit_status": proc.returncode,
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "snapshot_filename": snapshot,
        }
        # Raw snapshots and metadata stay ignored. Never overwrite an earlier capture.
        with (raw_dir / snapshot).open("xb") as handle:
            handle.write(raw)
        with (raw_dir / f"{key}.{stamp}.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    result = {
        "cricsheet_match_id": key,
        "source_url": report["source_url"],
        "source_title": report["source_title"],
        "published_at_utc": report["published_at_utc"],
        "scheduled_start_utc": report["scheduled_start_utc"],
        "retrieved_at_utc": metadata["retrieved_at_utc"],
        "raw_sha256": metadata["raw_sha256"],
        "http_status": metadata["http_status"],
    }
    if metadata["curl_exit_status"] != 0 or not raw:
        code = metadata["http_status"]
        status = "unavailable" if code in {"404", "410"} else "needs_review"
        return {**result, "status": status,
                "reason": f"source retrieval returned HTTP {code} / curl exit {metadata['curl_exit_status']}"}
    parsed = extract_source_candidate(report, raw.decode("utf-8", errors="replace"))
    return {**result, **parsed}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, default=ROOT / "data/manual/pitch_reports_verified.csv")
    parser.add_argument("--starts", type=Path, default=ROOT / "data/manual/match_start_times_verified.csv")
    parser.add_argument("--registry", type=Path, default=ROOT / "data/manual/pitch_code_reaudit.csv")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/pitch_expectations")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "artifacts/pitch_expectations/source_candidates.jsonl")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--retry-transient", action="store_true",
                        help="Append a new HTTPS snapshot only after a cached curl timeout")
    args = parser.parse_args()
    reports = selected_csv(args.reports, tuple(field for field in META_FIELDS
                                               if field != "scheduled_start_utc") + ("pre_match_verified",))
    starts = selected_csv(args.starts, ("cricsheet_match_id", "start_time_status", "scheduled_start_utc"))
    registry = selected_csv(args.registry, ("cricsheet_match_id", "reaudit_status"))
    timing_exclusions: list[str] = []
    universe = eligible_sources(reports, starts, registry, timing_exclusions)
    selected = universe[:args.limit] if args.limit is not None else universe
    if args.workers < 1 or args.limit is not None and args.limit < 1:
        raise ValueError("workers and optional limit must be positive")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        candidates = list(pool.map(lambda row: acquire(row, args.raw_dir, args.retry_transient), selected))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(canonical_json(row) + "\n" for row in candidates), encoding="utf-8")
    from collections import Counter
    print(json.dumps({
        "registry_candidates": len(universe) + len(timing_exclusions),
        "timing_ambiguous": len(timing_exclusions),
        "fetched": len(candidates),
        "source_statuses": dict(sorted(Counter(row["status"] for row in candidates).items())),
        "locked_test_scored": False,
    }, indent=2))


if __name__ == "__main__":
    main()
