import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_catalog import build_catalog


class BuildCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        plugin_dir = self.root / "plugins" / "sample_plugin"
        (plugin_dir / "metadata.json").parent.mkdir(parents=True)
        (plugin_dir / "metadata.json").write_text(
            json.dumps({"plugin_code": "sample_plugin", "name": "Sample"}),
            encoding="utf-8",
        )
        for version, payload in (("1.0.9", b"old"), ("1.0.12", b"new")):
            version_dir = plugin_dir / version
            version_dir.mkdir()
            (version_dir / "bundle.json").write_bytes(payload)
        self.existing_catalog = {
            "catalog_version": "1",
            "updated_at": "2026-01-01T00:00:00Z",
            "plugins": [{
                "plugin_code": "sample_plugin",
                "versions": [{
                    "version": "1.0.9",
                    "min_nv_version": "2.4.0",
                    "release_notes": "original release",
                    "released_at": "2025-12-01",
                }],
            }],
        }
        (self.root / "catalog.json").write_text(
            json.dumps(self.existing_catalog),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_preserves_release_metadata_and_sorts_versions_numerically(self):
        catalog = build_catalog(self.root, today="2026-10-08")
        versions = catalog["plugins"][0]["versions"]

        self.assertEqual([version["version"] for version in versions], ["1.0.12", "1.0.9"])
        old = versions[1]
        self.assertEqual(old["min_nv_version"], "2.4.0")
        self.assertEqual(old["release_notes"], "original release")
        self.assertEqual(old["released_at"], "2025-12-01")
        self.assertEqual(versions[0]["released_at"], "2026-10-08")

    def test_catalog_updated_at_stays_stable_when_generated_content_is_unchanged(self):
        plugin_dir = self.root / "plugins" / "sample_plugin"
        (self.root / "catalog.json").write_text(
            json.dumps(build_catalog(self.root, today="2026-10-08")),
            encoding="utf-8",
        )
        first = json.loads((self.root / "catalog.json").read_text(encoding="utf-8"))
        generated = build_catalog(self.root, today="2027-01-01")

        self.assertEqual(generated["updated_at"], first["updated_at"])
        latest = generated["plugins"][0]["versions"][0]
        self.assertEqual(latest["sha256"], hashlib.sha256(b"new").hexdigest())


if __name__ == "__main__":
    unittest.main()
