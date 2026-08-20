#!/usr/bin/env python3
"""Sitemap rebuild: indexable blog locs only; jobs stay in sitemap-pages."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_seo_do_now import (
    BROKEN_NAME_RE,
    blog_file_for_url,
    html_is_noindex,
    indexable_blog_urls,
)

ROOT = Path(__file__).resolve().parents[1]


class SitemapRebuildTests(unittest.TestCase):
    def test_indexable_urls_exclude_noindex_old_broken_and_well_depth(self):
        urls = indexable_blog_urls()
        self.assertGreater(len(urls), 2500)
        self.assertLess(len(urls), 4000)
        joined = "\n".join(urls)
        self.assertNotIn("-OLD", joined)
        self.assertNotIn("average-well-depth-", joined)
        self.assertFalse(any(" " in u or "(" in u for u in urls))
        for url in urls:
            path = blog_file_for_url(url)
            self.assertIsNotNone(path, url)
            assert path is not None
            self.assertFalse(html_is_noindex(path), url)
            self.assertFalse(BROKEN_NAME_RE.search(path.name), path.name)

    def test_written_blog_sitemaps_match_indexable_set(self):
        expected = set(indexable_blog_urls())
        found: set[str] = set()
        for i in range(1, 5):
            xml = (ROOT / f"sitemap-blog-{i}.xml").read_text()
            found.update(re.findall(r"<loc>([^<]+)</loc>", xml))
        self.assertEqual(found, expected)

    def test_city_well_depth_removed_and_emptied(self):
        index = (ROOT / "sitemap.xml").read_text()
        self.assertNotIn("sitemap-city-well-depth.xml", index)
        self.assertEqual(
            len(re.findall(r"<loc>", (ROOT / "sitemap-city-well-depth.xml").read_text())),
            0,
        )

    def test_sitemap_pages_keeps_jobs_and_money_urls(self):
        xml = (ROOT / "sitemap-pages.xml").read_text()
        jobs = set(re.findall(r"recent-work/([a-z0-9-]+)\.html", xml))
        jobs -= {f"page-{n}" for n in range(2, 6)}
        self.assertEqual(len(jobs), 107)
        self.assertIn("https://scwellservice.com/recent-work/", xml)
        for url in (
            "https://scwellservice.com/locations/",
            "https://scwellservice.com/pages/services/maintenance.html",
            "https://scwellservice.com/pages/services/diagnostics.html",
            "https://scwellservice.com/pages/services/controls.html",
            "https://scwellservice.com/pages/services/water-testing.html",
            "https://scwellservice.com/pages/locations/san-diego.html",
        ):
            self.assertIn(url, xml)

    def test_noindex_html_not_deleted(self):
        noindex = [
            p
            for p in (ROOT / "blog").glob("*.html")
            if html_is_noindex(p)
        ]
        self.assertGreater(len(noindex), 5000)


if __name__ == "__main__":
    unittest.main()
