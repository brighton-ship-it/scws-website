#!/usr/bin/env python3
"""Far-city factory noindex + keep-list tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from far_city_factory_lib import (
    FAR_CITY_SLUGS,
    KEEP_CITY_SLUGS,
    apply_far_city_noindex,
    ensure_noindex_follow,
    html_is_noindex,
    is_far_city_factory_path,
    is_keep_path,
    rebuild_services_sitemap,
)

ROOT = Path(__file__).resolve().parents[1]


class ClassifierTests(unittest.TestCase):
    def test_named_far_cities_are_factory(self):
        for slug in ("barstow", "victorville", "adelanto", "apple-valley", "perris"):
            self.assertIn(slug, FAR_CITY_SLUGS)
            self.assertTrue(is_far_city_factory_path(ROOT / "services" / slug / "index.html"))
            self.assertTrue(
                is_far_city_factory_path(ROOT / "services" / slug / "well-pump-repair.html")
            )

    def test_keep_shops_and_money_cities(self):
        for slug in KEEP_CITY_SLUGS:
            self.assertNotIn(slug, FAR_CITY_SLUGS)
            self.assertTrue(is_keep_path(ROOT / "services" / slug / "index.html"))
            self.assertFalse(is_far_city_factory_path(ROOT / "services" / slug / "index.html"))
        self.assertTrue(is_keep_path(ROOT / "services" / "temecula" / "well-drilling.html"))
        self.assertTrue(is_keep_path(ROOT / "services" / "ramona" / "well-pump-repair.html"))
        self.assertFalse(is_far_city_factory_path(ROOT / "index.html"))
        self.assertFalse(
            is_far_city_factory_path(ROOT / "recent-work" / "perris-pump-replacement.html")
        )
        self.assertFalse(is_far_city_factory_path(ROOT / "pages" / "services" / "pump-repair.html"))
        self.assertFalse(is_far_city_factory_path(ROOT / "blog" / "well-pump-repair-ramona.html"))
        self.assertFalse(is_far_city_factory_path(ROOT / "blog" / "well-drilling-temecula.html"))

    def test_blog_far_city_suffix(self):
        self.assertTrue(is_far_city_factory_path(ROOT / "blog" / "well-pump-repair-barstow.html"))
        self.assertTrue(is_far_city_factory_path(ROOT / "blog" / "low-water-pressure-adelanto.html"))


class NoindexApplyTests(unittest.TestCase):
    def test_ensure_inserts_noindex_follow(self):
        src = "<html><head><title>x</title></head><body></body></html>"
        out = ensure_noindex_follow(src)
        self.assertIn('name="robots" content="noindex, follow"', out)
        self.assertEqual(out, ensure_noindex_follow(out))

    def test_live_keep_pages_not_noindexed(self):
        keep = [
            ROOT / "services" / "ramona" / "index.html",
            ROOT / "services" / "anza" / "index.html",
            ROOT / "services" / "temecula" / "well-drilling.html",
            ROOT / "services" / "valley-center" / "index.html",
            ROOT / "services" / "escondido" / "index.html",
            ROOT / "services" / "julian" / "index.html",
            ROOT / "blog" / "well-pump-repair-ramona.html",
            ROOT / "blog" / "well-drilling-temecula.html",
            ROOT / "index.html",
        ]
        for path in keep:
            self.assertTrue(path.is_file(), path)
            self.assertFalse(html_is_noindex(path), path)

    def test_live_far_city_hubs_noindexed_and_kept_on_disk(self):
        for slug in ("barstow", "victorville", "adelanto", "apple-valley", "perris"):
            path = ROOT / "services" / slug / "index.html"
            self.assertTrue(path.is_file(), path)
            self.assertTrue(html_is_noindex(path), path)
            self.assertIn("noindex, follow", path.read_text(encoding="utf-8"))

    def test_sitemap_services_dropped_far_kept_money(self):
        xml = (ROOT / "sitemap-services.xml").read_text(encoding="utf-8")
        for slug in ("barstow", "victorville", "adelanto", "apple-valley", "perris"):
            self.assertNotIn(f"/services/{slug}/", xml)
        for slug in ("ramona", "anza", "temecula", "valley-center", "escondido", "julian"):
            self.assertIn(f"https://scwellservice.com/services/{slug}/", xml)

    def test_apply_does_not_delete_files(self):
        before = {p for p in (ROOT / "services" / "barstow").glob("*.html")}
        apply_far_city_noindex()
        after = {p for p in (ROOT / "services" / "barstow").glob("*.html")}
        self.assertEqual(before, after)
        self.assertGreaterEqual(rebuild_services_sitemap(), 20)

    def test_job_pages_stay_in_pages_sitemap(self):
        xml = (ROOT / "sitemap-pages.xml").read_text(encoding="utf-8")
        self.assertIn("recent-work/perris-pump-replacement.html", xml)


class GeneratorDisabledTests(unittest.TestCase):
    def test_service_page_generator_exits(self):
        src = (ROOT / "scripts" / "generate-service-pages.py").read_text(encoding="utf-8")
        self.assertIn("Disabled", src)
        self.assertIn("do not generate", src.lower())

    def test_enrich_and_sb_generators_disabled(self):
        enrich = (ROOT / "scripts" / "enrich-all-cities.py").read_text(encoding="utf-8")
        sb = (ROOT / "scripts" / "create-sanbernardino-pages.py").read_text(encoding="utf-8")
        self.assertIn("Disabled", enrich)
        self.assertIn("Disabled", sb)


if __name__ == "__main__":
    unittest.main()
