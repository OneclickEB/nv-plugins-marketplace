#!/usr/bin/env python3
"""
Genera catalog.json a partir de plugins/*/metadata.json y plugins/*/<version>/bundle.json
Ejecutado por la GitHub Action en cada push a plugins/**
"""
import json
import pathlib
import hashlib
import datetime

REPO = "OneclickEB/nv-plugins-marketplace"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/main"

plugins_dir = pathlib.Path("plugins")
plugins = []

for meta_file in sorted(plugins_dir.glob("*/metadata.json")):
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"SKIP {meta_file}: {e}")
        continue

    plugin_code = meta_file.parent.name
    versions = []

    for bundle_file in sorted(meta_file.parent.glob("*/bundle.json"), reverse=True):
        version = bundle_file.parent.name
        bundle_bytes = bundle_file.read_bytes()
        sha256 = hashlib.sha256(bundle_bytes).hexdigest()
        download_url = f"{BASE_URL}/plugins/{plugin_code}/{version}/bundle.json"
        versions.append({
            "version": version,
            "download_url": download_url,
            "sha256": sha256,
            "min_nv_version": "2.7.0",
            "release_notes": "",
            "released_at": datetime.date.today().isoformat(),
        })

    plugins.append({**meta, "versions": versions})
    print(f"  {plugin_code}: {len(versions)} versión(es)")

catalog = {
    "catalog_version": "1",
    "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
    "plugins": plugins,
}

output = pathlib.Path("catalog.json")
output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\ncatalog.json generado: {len(plugins)} plugins")
