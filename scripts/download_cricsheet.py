#!/usr/bin/env python3
"""Download and safely extract the official Cricsheet ODI JSON archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_URL = "https://cricsheet.org/downloads/odis_json.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_extract(archive: Path, destination: Path) -> None:
    destination_resolved = destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        for member in zipped.infolist():
            target = (destination / member.filename).resolve()
            if destination_resolved not in target.parents and target != destination_resolved:
                raise ValueError(f"Unsafe archive member: {member.filename}")
        zipped.extractall(destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_json = list(output_dir.rglob("*.json"))
    if existing_json and not args.force:
        raise SystemExit(
            f"{output_dir} already contains JSON files. Use --force only after preserving raw data."
        )

    with tempfile.TemporaryDirectory(prefix="cricsheet_download_") as temp:
        archive = Path(temp) / "odis_json.zip"
        with urllib.request.urlopen(args.url, timeout=120) as response, archive.open("wb") as out:
            shutil.copyfileobj(response, out)
        digest = sha256(archive)
        safe_extract(archive, output_dir)

    manifest = {
        "source_url": args.url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_sha256": digest,
        "json_file_count": len(list(output_dir.rglob("*.json"))),
    }
    manifest_path = output_dir / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {manifest['json_file_count']} JSON files; manifest: {manifest_path}")


if __name__ == "__main__":
    main()

