#!/usr/bin/env python3
"""Verify catalog hashes against tracked bundles and optionally audit published bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


REPO = "OneclickEB/nv-plugins-marketplace"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/main"
PLUGIN_CODE_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def canonical_bundle_url(plugin_code: str, version: str) -> str:
    if not PLUGIN_CODE_RE.fullmatch(plugin_code):
        raise ValueError(f"invalid plugin_code: {plugin_code!r}")
    if not VERSION_RE.fullmatch(version):
        raise ValueError(f"invalid version: {version!r}")
    return f"{BASE_URL}/plugins/{plugin_code}/{version}/bundle.json"


def fetch_published_bundle(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "nv-marketplace-integrity-check"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError(f"published bundle fetch failed: {type(exc).__name__}") from exc


def audit_catalog(
    catalog: dict,
    repo_root: Path,
    *,
    sync_remote: bool = False,
    remote_fetcher=fetch_published_bundle,
) -> tuple[list[str], list[tuple[str, str]]]:
    errors: list[str] = []
    corrected: list[tuple[str, str]] = []
    catalog_versions: set[tuple[str, str]] = set()
    plugins = catalog.get("plugins")
    if not isinstance(plugins, list):
        return ["catalog.plugins must be a list"], corrected

    for plugin in plugins:
        if not isinstance(plugin, dict):
            errors.append("catalog contains a non-object plugin entry")
            continue
        plugin_code = str(plugin.get("plugin_code") or "")
        if not PLUGIN_CODE_RE.fullmatch(plugin_code):
            errors.append(f"invalid plugin_code: {plugin_code!r}")
            continue
        versions = plugin.get("versions")
        if not isinstance(versions, list):
            errors.append(f"{plugin_code}: versions must be a list")
            continue

        for version_info in versions:
            if not isinstance(version_info, dict):
                errors.append(f"{plugin_code}: version entry must be an object")
                continue
            version = str(version_info.get("version") or "")
            try:
                expected_url = canonical_bundle_url(plugin_code, version)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            key = (plugin_code, version)
            if key in catalog_versions:
                errors.append(f"duplicate catalog version: {plugin_code} {version}")
                continue
            catalog_versions.add(key)

            if version_info.get("download_url") != expected_url:
                errors.append(f"{plugin_code} {version}: download_url is not the canonical repository URL")
                continue

            bundle_path = repo_root / "plugins" / plugin_code / version / "bundle.json"
            if not bundle_path.is_file():
                errors.append(f"{plugin_code} {version}: tracked bundle is missing")
                continue

            local_bytes = bundle_path.read_bytes()
            local_sha = hashlib.sha256(local_bytes).hexdigest()
            expected_sha = str(version_info.get("sha256") or "")
            if not SHA256_RE.fullmatch(expected_sha):
                expected_sha = ""

            actual_sha = local_sha
            if sync_remote:
                try:
                    remote_sha = hashlib.sha256(remote_fetcher(expected_url)).hexdigest()
                except ValueError as exc:
                    errors.append(f"{plugin_code} {version}: {exc}")
                    continue
                if remote_sha != local_sha:
                    errors.append(
                        f"{plugin_code} {version}: published bundle differs from tracked bundle; manual review required"
                    )
                    continue
                actual_sha = remote_sha

            if expected_sha.lower() != actual_sha:
                if sync_remote:
                    version_info["sha256"] = actual_sha
                    corrected.append(key)
                else:
                    errors.append(f"{plugin_code} {version}: catalog SHA-256 does not match tracked bundle")

    tracked_versions = {
        (bundle.parent.parent.name, bundle.parent.name)
        for bundle in (repo_root / "plugins").glob("*/*/bundle.json")
    }
    for plugin_code, version in sorted(tracked_versions - catalog_versions):
        errors.append(f"{plugin_code} {version}: tracked bundle is missing from catalog.json")
    for plugin_code, version in sorted(catalog_versions - tracked_versions):
        errors.append(f"{plugin_code} {version}: catalog entry has no tracked bundle")

    return errors, corrected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="compare catalog SHA values with tracked bundles")
    mode.add_argument(
        "--sync-remote",
        action="store_true",
        help="audit published bundle bytes and update only stale SHA fields when they match tracked files",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="marketplace repository root")
    args = parser.parse_args()

    root = args.root.resolve()
    catalog_path = root / "catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read catalog.json: {type(exc).__name__}", file=sys.stderr)
        return 2

    errors, corrected = audit_catalog(catalog, root, sync_remote=args.sync_remote)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if corrected:
        catalog["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        catalog_path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Updated {len(corrected)} SHA-256 value(s) in catalog.json")
        for plugin_code, version in corrected:
            print(f"- {plugin_code} {version}")
    else:
        print("Marketplace catalog integrity check passed; no checksum changes needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
