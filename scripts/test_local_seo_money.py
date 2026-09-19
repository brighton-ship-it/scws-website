#!/usr/bin/env python3
"""Local-intent SEO: emergency guides, money-page jobs, crawl waste."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_seo_do_now import html_is_noindex, indexable_blog_urls, is_programmatic_well_permit
from far_city_factory_lib import FAR_CITY_SLUGS, html_is_noindex as far_html_is_noindex
from leftover_claims_lib import CANONICAL_CSLB
from recent_work_lib import MONEY_PAGE_SLUGS, apply_money_page_recent_work, money_page_specs

ROOT = Path(__file__).resolve().parents[1]

EMERGENCY_GUIDES = (
    "blog/no-water-from-well.html",
    "blog/well-pump-runs-but-no-water.html",
    "blog/well-pump-running-but-no-water.html",
    "blog/emergency-well-no-water.html",
    "blog/no-water-emergency.html",
)

LOCAL_HINT = re.compile(r"San Diego County|Ramona|Anza", re.I)
FAKE_RATING = re.compile(r"4\.9\s*★|4\.9-star|4\.9 star", re.I)
FAKE_AGE = re.compile(
    r"for decades|30\+\s*years|since the 1960s|since the 1980s|drilled since 196",
    re.I,
)
TWENTY_FOUR_HOUR_HERO = re.compile(r"24-Hour Emergency|24-Hour hero", re.I)


def _title(html: str) -> str:
    match = re.search(r"<title>([^<]+)</title>", html, re.I)
    return match.group(1) if match else ""


def _h1(html: str) -> str:
    match = re.search(r"<h1\b[^>]*>(.*?)</h1>", html, re.I | re.S)
    return re.sub(r"<[^>]+>", "", match.group(1)).strip() if match else ""


def _meta_desc(html: str) -> str:
    match = re.search(
        r'<meta\b[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.I,
    )
    if match:
        return match.group(1)
    match = re.search(
        r'<meta\b[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description["\']',
        html,
        re.I,
    )
    return match.group(1) if match else ""


def _sitemap_locs(*names: str) -> set[str]:
    found: set[str] = set()
    for name in names:
        path = ROOT / name
        if not path.is_file():
            continue
        found.update(re.findall(r"<loc>([^<]+)</loc>", path.read_text(encoding="utf-8")))
    return found


class EmergencyGuideTests(unittest.TestCase):
    def test_guides_are_local_intent_with_three_ctas(self):
        for rel in EMERGENCY_GUIDES:
            html = (ROOT / rel).read_text(encoding="utf-8")
            title = _title(html)
            h1 = _h1(html)
            desc = _meta_desc(html)
            self.assertTrue(LOCAL_HINT.search(title), rel)
            self.assertTrue(LOCAL_HINT.search(h1), rel)
            self.assertTrue(LOCAL_HINT.search(desc), rel)
            self.assertLess(len(title), 70, rel)
            self.assertNotRegex(title, r"(Causes & Quick Fixes|9 Causes & Fixes|How to Fix \(2026\))")
            self.assertIn('id="shop-lead-cta"', html)
            aside = html.split('id="shop-lead-cta"', 1)[1].split("</aside>", 1)[0]
            self.assertIn("tel:+17604408520", aside)
            self.assertIn("sms:7602195877", aside)
            self.assertIn("/contact.html", aside)
            self.assertIn("hero-cta-short", aside)
            self.assertIn(">Call<", aside)
            self.assertIn(">Text<", aside)
            self.assertRegex(aside, r">Get Estimate<|>Estimate<")
            self.assertIn(CANONICAL_CSLB, html)
            self.assertIsNone(FAKE_RATING.search(html), rel)
            self.assertIsNone(FAKE_AGE.search(html), rel)
            self.assertNotIn("Joe Fain", html)  # these guides never had him; do not invent
            self.assertIsNone(TWENTY_FOUR_HOUR_HERO.search(html), rel)
            self.assertGreater(len(html), 8000, rel)

    def test_guides_stay_indexable(self):
        for rel in EMERGENCY_GUIDES:
            path = ROOT / rel
            self.assertFalse(html_is_noindex(path), rel)
            self.assertFalse(is_programmatic_well_permit(path.name), rel)


class MoneyPageJobLinkTests(unittest.TestCase):
    def test_city_and_service_money_pages_have_job_cards(self):
        apply_money_page_recent_work()
        expected = {
            "services/ramona/index.html",
            "services/anza/index.html",
            "pages/services/pump-repair.html",
            "pages/services/well-drilling.html",
            "pages/services/emergency-well-service.html",
            "services/ramona/well-pump-repair.html",
            "services/ramona/well-drilling.html",
            "services/ramona/emergency-well-service.html",
            "services/anza/well-pump-repair.html",
            "services/anza/well-drilling.html",
            "services/anza/emergency-well-service.html",
            "services/valley-center/index.html",
            "services/aguanga/index.html",
            "services/temecula/index.html",
            "services/escondido/index.html",
            "services/julian/index.html",
        }
        specs = money_page_specs()
        self.assertTrue(expected.issubset(specs))
        self.assertTrue(
            {
                "services/ramona/index.html",
                "services/anza/index.html",
                "pages/services/pump-repair.html",
            }.issubset(MONEY_PAGE_SLUGS)
        )
        for rel in expected:
            html = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn('id="recent-jobs"', html, rel)
            cards = re.findall(r'class="recent-work-card"', html)
            self.assertGreaterEqual(len(cards), 3, rel)
            self.assertLessEqual(len(cards), 6, rel)
            self.assertIn("/recent-work/", html)
            self.assertNotIn("4.9★", html.split('id="recent-jobs"', 1)[1].split("</section>", 1)[0])

    def test_high_intent_pages_have_unique_depth_and_ctas(self):
        pages = (
            "services/ramona/index.html",
            "services/anza/index.html",
            "services/valley-center/index.html",
            "services/aguanga/index.html",
            "services/temecula/index.html",
            "pages/services/pump-repair.html",
            "pages/services/well-drilling.html",
            "pages/services/emergency-well-service.html",
            "services/ramona/well-pump-repair.html",
            "pages/locations/cities/valley-center.html",
        )
        for rel in pages:
            html = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn('id="shop-local-note"', html, rel)
            note = html.split('id="shop-local-note"', 1)[1].split("</section>", 1)[0]
            words = re.findall(r"[A-Za-z0-9']+", re.sub(r"<[^>]+>", " ", note))
            self.assertGreaterEqual(len(words), 120, rel)
            self.assertIn("tel:+17604408520", note)
            self.assertIn("sms:7602195877", note)
            self.assertIn("/contact.html", note)
            self.assertIn("1086994", note)
            self.assertIsNone(FAKE_RATING.search(note), rel)
            self.assertIsNone(FAKE_AGE.search(note), rel)
            self.assertNotIn("Since 2006", html)


class CrawlWasteTests(unittest.TestCase):
    def test_far_city_hubs_noindex_and_off_services_sitemap(self):
        services_xml = (ROOT / "sitemap-services.xml").read_text(encoding="utf-8")
        for slug in ("barstow", "victorville", "adelanto"):
            self.assertIn(slug, FAR_CITY_SLUGS)
            hub = ROOT / "services" / slug / "index.html"
            self.assertTrue(hub.is_file(), slug)
            self.assertTrue(far_html_is_noindex(hub), slug)
            self.assertNotIn(f"/services/{slug}/", services_xml)

    def test_noindex_permit_spam_not_in_blog_sitemaps(self):
        locs = _sitemap_locs(
            "sitemap-blog-1.xml",
            "sitemap-blog-2.xml",
            "sitemap-blog-3.xml",
            "sitemap-blog-4.xml",
        )
        indexable = set(indexable_blog_urls())
        self.assertEqual(locs, indexable)
        for loc in locs:
            name = loc.rsplit("/", 1)[-1]
            if is_programmatic_well_permit(name):
                self.fail(f"permit spam still in sitemap: {loc}")
            path = ROOT / "blog" / name
            if path.is_file():
                self.assertFalse(html_is_noindex(path), loc)
        self.assertIn("https://scwellservice.com/blog/no-water-from-well.html", locs)
        self.assertIn("https://scwellservice.com/blog/well-pump-runs-but-no-water.html", locs)
        self.assertNotIn("https://scwellservice.com/blog/well-permit-bonsall.html", locs)
        self.assertNotIn("https://scwellservice.com/blog/well-permit-barstow.html", locs)


if __name__ == "__main__":
    unittest.main()
