import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.verify_catalog_integrity import BASE_URL, audit_catalog


class CatalogIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.plugin_code = "sample_plugin"
        self.version = "1.2.3"
        self.bundle = b'{"nv_plugin_bundle_v1":true}'
        bundle_path = self.root / "plugins" / self.plugin_code / self.version / "bundle.json"
        bundle_path.parent.mkdir(parents=True)
        bundle_path.write_bytes(self.bundle)
        self.url = f"{BASE_URL}/plugins/{self.plugin_code}/{self.version}/bundle.json"
        self.catalog = {
            "plugins": [{
                "plugin_code": self.plugin_code,
                "versions": [{
                    "version": self.version,
                    "download_url": self.url,
                    "sha256": hashlib.sha256(self.bundle).hexdigest(),
                }],
            }],
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_check_passes_when_catalog_matches_tracked_bundle(self):
        errors, corrected = audit_catalog(self.catalog, self.root)
        self.assertEqual(errors, [])
        self.assertEqual(corrected, [])

    def test_check_fails_when_catalog_checksum_is_stale(self):
        self.catalog["plugins"][0]["versions"][0]["sha256"] = "0" * 64
        errors, corrected = audit_catalog(self.catalog, self.root)
        self.assertTrue(any("SHA-256 does not match" in error for error in errors))
        self.assertEqual(corrected, [])

    def test_sync_updates_only_checksum_after_remote_and_tracked_bytes_match(self):
        self.catalog["plugins"][0]["versions"][0]["sha256"] = "0" * 64
        errors, corrected = audit_catalog(
            self.catalog,
            self.root,
            sync_remote=True,
            remote_fetcher=lambda _url: self.bundle,
        )
        self.assertEqual(errors, [])
        self.assertEqual(corrected, [(self.plugin_code, self.version)])
        self.assertEqual(
            self.catalog["plugins"][0]["versions"][0]["sha256"],
            hashlib.sha256(self.bundle).hexdigest(),
        )

    def test_sync_refuses_to_bless_remote_bundle_that_differs_from_tracked_source(self):
        self.catalog["plugins"][0]["versions"][0]["sha256"] = "0" * 64
        errors, corrected = audit_catalog(
            self.catalog,
            self.root,
            sync_remote=True,
            remote_fetcher=lambda _url: b'{"unexpected":true}',
        )
        self.assertTrue(any("differs from tracked bundle" in error for error in errors))
        self.assertEqual(corrected, [])
        self.assertEqual(self.catalog["plugins"][0]["versions"][0]["sha256"], "0" * 64)

    def test_rejects_noncanonical_download_urls(self):
        self.catalog["plugins"][0]["versions"][0]["download_url"] = "https://example.com/bundle.json"
        errors, _ = audit_catalog(self.catalog, self.root)
        self.assertTrue(any("canonical repository URL" in error for error in errors))

    def test_detects_tracked_bundle_missing_from_catalog(self):
        self.catalog["plugins"] = []
        errors, _ = audit_catalog(self.catalog, self.root)
        self.assertTrue(any("tracked bundle is missing from catalog" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
