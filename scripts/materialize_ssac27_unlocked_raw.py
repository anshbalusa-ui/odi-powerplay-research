#!/usr/bin/env python3
"""Materialize only prespecified 2015–2024 ODI IDs from a hashed raw ZIP.

ZIP membership is metadata; no 2025+ JSON member is opened, extracted or scored.
The source archive and any existing raw release are immutable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = "https://cricsheet.org/downloads/odis_json.zip"
FROZEN_ARCHIVE_SHA256 = "f8423531b24183bc2cfc1e3e27f9bd29ad7c4d5a4bdc2469bf681d7fe2f5c5ce"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def unlocked_registry(registry: Path) -> tuple[dict[str, str], int]:
    selected: dict[str, str] = {}
    seen: set[str] = set()
    locked_count = 0
    with registry.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"cricsheet_match_id", "match_date"}.issubset(reader.fieldnames or ()):
            raise ValueError("registry lacks match ID/date metadata")
        for row in reader:
            match_id = row["cricsheet_match_id"]
            date = row["match_date"]
            if not match_id.isdecimal() or len(date) != 10:
                raise ValueError("registry contains invalid match ID/date")
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValueError("registry contains invalid match date") from exc
            if parsed_date.isoformat() != date or match_id in seen:
                raise ValueError("registry contains duplicate ID or noncanonical date")
            seen.add(match_id)
            if date >= "2025-01-01":
                locked_count += 1
            elif date >= "2015-01-01":
                selected[match_id] = date
            else:
                raise ValueError("registry contains unexpected pre-2015 match")
    if not selected:
        raise ValueError("registry contains no unlocked matches")
    return selected, locked_count


def materialize_unlocked(
    archive: Path, registry: Path, output_dir: Path, *,
    expected_archive_sha256: str, expected_unlocked_matches: int,
    source_url: str = DEFAULT_SOURCE,
) -> dict:
    """Validate source/IDs/dates, then atomically install an immutable raw subset."""
    if output_dir.exists():
        raise FileExistsError(f"raw release already exists: {output_dir}")
    digest = sha256(archive)
    if digest != expected_archive_sha256:
        raise ValueError("archive SHA-256 differs from prespecified source version")
    unlocked, locked_count = unlocked_registry(registry)
    if len(unlocked) != expected_unlocked_matches:
        raise ValueError("unlocked match count differs from frozen registry")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zipped:
        # Inspect only central-directory filenames for all members. The ZIP API
        # opens a file body below ONLY for an explicitly unlocked registry ID.
        wanted = {f"{match_id}.json" for match_id in unlocked}
        counts = Counter(entry.filename for entry in zipped.infolist()
                         if entry.filename in wanted)
        duplicates = sorted(name for name, count in counts.items() if count != 1)
        if duplicates:
            raise ValueError(f"duplicate unlocked archive members: {duplicates}")
        missing = sorted(wanted - counts.keys())
        if missing:
            raise ValueError(f"missing unlocked members: {len(missing)}")
        with tempfile.TemporaryDirectory(prefix="ssac27_unlocked_", dir=output_dir.parent) as temp:
            staging = Path(temp)
            hashes: dict[str, str] = {}
            for match_id, date in sorted(unlocked.items()):
                raw = zipped.read(f"{match_id}.json")
                try:
                    report = json.loads(raw)
                    info = report["info"]
                    dates = info["dates"]
                    if (not dates or dates[0] != date or info.get("gender") != "male"
                            or info.get("match_type") != "ODI"):
                        raise ValueError("registry date or ODI match identity differs from raw member")
                except (KeyError, TypeError, IndexError, json.JSONDecodeError) as exc:
                    raise ValueError("unlocked raw match identity cannot be verified") from exc
                (staging / f"{match_id}.json").write_bytes(raw)
                hashes[match_id] = hashlib.sha256(raw).hexdigest()
            mapping_bytes = "".join(f"{key}:{hashes[key]}\n" for key in sorted(hashes)).encode()
            result = {
                "source_url": source_url,
                "source_archive": str(archive),
                "archive_sha256": digest,
                "archive_file_mtime_utc": datetime.fromtimestamp(
                    archive.stat().st_mtime, timezone.utc).isoformat(),
                "registry_sha256": sha256(registry),
                "unlocked_mapping_sha256": hashlib.sha256(mapping_bytes).hexdigest(),
                "unlocked_member_sha256": hashes,
                "json_file_count": len(hashes),
                "locked_registry_match_count_metadata_only": locked_count,
                "locked_test_scored": False,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "source_version_note": (
                    "2026-09-29 official archive, NOT the missing 2026-09-10 fixed archive; "
                    "only 2015-2024 prespecified registry members opened"
                ),
            }
            (staging / "source_manifest.json").write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            if output_dir.exists():
                raise FileExistsError(f"raw release appeared during extraction: {output_dir}")
            os.replace(staging, output_dir)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=PROJECT_ROOT / "data/raw/cricsheet/odis_json_20260929.zip")
    parser.add_argument("--registry", type=Path,
                        default=PROJECT_ROOT / "data/manual/match_start_times_template.csv")
    parser.add_argument("--output-dir", type=Path,
                        default=PROJECT_ROOT / "data/raw/cricsheet/unlocked_20260929")
    parser.add_argument("--expected-archive-sha256", default=FROZEN_ARCHIVE_SHA256)
    parser.add_argument("--expected-unlocked-matches", type=int, default=942)
    args = parser.parse_args()
    result = materialize_unlocked(
        args.archive, args.registry, args.output_dir,
        expected_archive_sha256=args.expected_archive_sha256,
        expected_unlocked_matches=args.expected_unlocked_matches,
    )
    print(json.dumps({key: result[key] for key in (
        "archive_sha256", "unlocked_mapping_sha256", "json_file_count",
        "locked_registry_match_count_metadata_only", "locked_test_scored",
    )}, indent=2))


if __name__ == "__main__":
    main()
