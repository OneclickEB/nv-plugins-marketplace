#!/usr/bin/env python3
"""Generate catalog.json from plugin metadata and versioned bundles."""

import datetime
import hashlib
import json
import pathlib
import re


REPO = "OneclickEB/nv-plugins-marketplace"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/main"
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")


def _version_key(version: str) -> tuple:
    match = VERSION_RE.fullmatch(version)
    if not match:
        raise ValueError(f"Versión SemVer inválida: {version}")
    major, minor, patch, prerelease = match.groups()
    # A stable release sorts after its prereleases with the same numeric version.
    return int(major), int(minor), int(patch), prerelease is None, prerelease or ""


def build_catalog(repo_root: pathlib.Path | str = ".", today: str | None = None) -> dict:
    root = pathlib.Path(repo_root)
    catalog_path = root / "catalog.json"
    old_catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {}
    old_plugins = {
        plugin.get("plugin_code"): plugin
        for plugin in old_catalog.get("plugins", [])
        if isinstance(plugin, dict) and plugin.get("plugin_code")
    }
    published_at = today or datetime.date.today().isoformat()
    plugins = []

    for metadata_path in sorted((root / "plugins").glob("*/metadata.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        plugin_code = metadata_path.parent.name
        old_versions = {
            item.get("version"): item
            for item in old_plugins.get(plugin_code, {}).get("versions", [])
            if isinstance(item, dict) and item.get("version")
        }
        version_files = list(metadata_path.parent.glob("*/bundle.json"))
        version_files.sort(key=lambda path: _version_key(path.parent.name), reverse=True)
        versions = []

        for bundle_path in version_files:
            version = bundle_path.parent.name
            old_version = old_versions.get(version, {})
            bundle_bytes = bundle_path.read_bytes()
            versions.append({
                "version": version,
                "download_url": f"{BASE_URL}/plugins/{plugin_code}/{version}/bundle.json",
                "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
                "min_nv_version": old_version.get(
                    "min_nv_version",
                    metadata.get("min_nv_version", "2.7.0"),
                ),
                "release_notes": old_version.get(
                    "release_notes",
                    metadata.get("release_notes", ""),
                ),
                "released_at": old_version.get("released_at", published_at),
            })
        plugins.append({**metadata, "versions": versions})

    catalog_content = {
        "catalog_version": old_catalog.get("catalog_version", "1"),
        "plugins": plugins,
    }
    old_without_timestamp = {key: value for key, value in old_catalog.items() if key != "updated_at"}
    if old_without_timestamp == catalog_content and old_catalog.get("updated_at"):
        updated_at = old_catalog["updated_at"]
    else:
        updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    catalog = {
        "catalog_version": catalog_content["catalog_version"],
        "updated_at": updated_at,
        "plugins": plugins,
    }
    return catalog


def main() -> int:
    root = pathlib.Path.cwd()
    catalog = build_catalog(root)
    (root / "catalog.json").write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"catalog.json generado: {len(catalog['plugins'])} plugins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
