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


NEW_SERVICE_PAGES = (
    "pages/services/water-storage-tanks.html",
    "pages/services/booster-pumps.html",
    "pages/services/pressure-tanks.html",
)
NEW_CITY_HUBS = (
    "services/desert-hot-springs/index.html",
    "services/mountain-center/index.html",
)
DEEPENED_HUBS = (
    "services/hemet/index.html",
    "services/el-cajon/index.html",
    "services/menifee/index.html",
    "services/warner-springs/index.html",
    "services/rancho-santa-fe/index.html",
    "services/santa-ysabel/index.html",
)
BRIEF_RECENT_WORK = {
    "pages/services/water-storage-tanks.html": [
        "/recent-work/poway-storage-tank-replacement.html",
        "/recent-work/escondido-storage-tank-float-repair.html",
        "/recent-work/pine-valley-storage-tank-adapter-repair.html",
        "/recent-work/anza-storage-tank-float-inspection.html",
        "/recent-work/menifee-tank-float-replacement.html",
        "/recent-work/menifee-pump-down-float-replacement.html",
        "/recent-work/fallbrook-tank-float-inspection.html",
        "/recent-work/aguanga-float-and-pressure-switch-replacement.html",
    ],
    "pages/services/booster-pumps.html": [
        "/recent-work/ramona-booster-pump-replacement.html",
        "/recent-work/ramona-highland-booster-motor.html",
        "/recent-work/ramona-booster-pump-evaluation.html",
        "/recent-work/fallbrook-booster-pump-diagnostic.html",
        "/recent-work/warner-springs-booster-and-tank-diagnostic.html",
        "/recent-work/descanso-well-and-booster-plumbing-evaluation.html",
        "/recent-work/ramona-locked-booster-pump-replacement.html",
        "/recent-work/winchester-booster-pump-replacement.html",
    ],
    "pages/services/pressure-tanks.html": [
        "/recent-work/ramona-hanson-pressure-tank.html",
        "/recent-work/hemet-pressure-tank-plumbing-repair.html",
        "/recent-work/murrieta-pressure-tank-evaluation.html",
        "/recent-work/wildomar-pressure-tank-switch-service.html",
        "/recent-work/temecula-transducer-and-pressure-tank-replacement.html",
        "/recent-work/warner-springs-pressure-loss-diagnostic.html",
        "/recent-work/corona-pressure-tank-and-switch-adjustment.html",
        "/recent-work/thermal-pressure-switch-replacement.html",
    ],
}


def _json_ld_blocks(html: str) -> list:
    import json

    blocks = []
    for raw in re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.I | re.S,
    ):
        blocks.append(json.loads(raw))
    return blocks


class ExpansionPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from apply_money_page_depth import apply_depth
        from recent_work_lib import apply_money_page_recent_work

        apply_depth()
        apply_money_page_recent_work()

    def test_new_service_pages_are_indexable_money_pages(self):
        for rel in NEW_SERVICE_PAGES:
            html = (ROOT / rel).read_text(encoding="utf-8")
            title = _title(html)
            self.assertLessEqual(len(title), 60, rel)
            self.assertTrue(_h1(html), rel)
            self.assertTrue(_meta_desc(html), rel)
            self.assertIn(f"https://scwellservice.com/{rel}", html)
            self.assertIn("tel:+17604408520", html)
            self.assertIn("sms:7602195877", html)
            self.assertIn("/contact.html", html)
            self.assertIn("1086994", html)
            self.assertIsNone(FAKE_RATING.search(html), rel)
            self.assertIsNone(FAKE_AGE.search(html), rel)
            self.assertNotIn("24/7", html, rel)
            self.assertNotIn("$", html, rel)
            self.assertFalse(html_is_noindex(ROOT / rel), rel)
            types = {block.get("@type") for block in _json_ld_blocks(html)}
            self.assertIn("Service", types, rel)
            self.assertIn("BreadcrumbList", types, rel)
            self.assertIn("FAQPage", types, rel)
            self.assertIn('id="shop-local-note"', html, rel)
            self.assertGreaterEqual(len(re.findall(r'class="recent-work-card"', html)), 4, rel)
            self.assertLessEqual(len(re.findall(r'class="recent-work-card"', html)), 8, rel)
            for href in BRIEF_RECENT_WORK[rel]:
                self.assertIn(href, html, rel)
                target = ROOT / href.lstrip("/")
                self.assertTrue(target.is_file(), href)
                self.assertFalse(html_is_noindex(target), href)

    def test_new_and_deepened_hubs_have_unique_copy_and_cards(self):
        card_minimums = {
            "services/hemet/index.html": 3,
            "services/el-cajon/index.html": 3,
            "services/warner-springs/index.html": 3,
            "services/rancho-santa-fe/index.html": 3,
            "services/menifee/index.html": 2,
            "services/santa-ysabel/index.html": 2,
        }
        area_links = {
            "services/desert-hot-springs/index.html": [
                "/recent-work/areas/desert-hot-springs.html",
                "/recent-work/areas/rancho-mirage.html",
                "/recent-work/areas/palm-desert.html",
                "/recent-work/areas/la-quinta.html",
                "/recent-work/areas/thousand-palms.html",
                "/recent-work/areas/thermal.html",
                "/recent-work/thermal-pressure-switch-replacement.html",
            ],
            "services/mountain-center/index.html": [
                "/recent-work/areas/mountain-center.html",
                "/recent-work/areas/idyllwild.html",
                "/recent-work/areas/idyllwild-pine-cove.html",
            ],
        }
        h1s = []
        for rel in DEEPENED_HUBS + NEW_CITY_HUBS:
            html = (ROOT / rel).read_text(encoding="utf-8")
            h1 = _h1(html)
            h1s.append(h1)
            self.assertFalse(h1.startswith("Well Services in "), rel)
            self.assertIn('id="shop-local-note"', html, rel)
            self.assertIn("tel:+17604408520", html)
            self.assertFalse(html_is_noindex(ROOT / rel), rel)
            if rel in card_minimums:
                self.assertIn('id="recent-jobs"', html, rel)
                self.assertGreaterEqual(
                    len(re.findall(r'class="recent-work-card"', html)),
                    card_minimums[rel],
                    rel,
                )
            else:
                self.assertNotIn('class="recent-work-card"', html, rel)
            for href in area_links.get(rel, []):
                self.assertIn(href, html, rel)
            for match in re.findall(r'href="(/recent-work/[^"]+)"', html):
                target = ROOT / match.lstrip("/")
                self.assertTrue(target.is_file(), match)
                self.assertFalse(html_is_noindex(target), match)
        self.assertEqual(len(h1s), len(set(h1s)))

    def test_new_urls_are_in_sitemaps_and_indexes(self):
        pages = (ROOT / "sitemap-pages.xml").read_text(encoding="utf-8")
        services = (ROOT / "sitemap-services.xml").read_text(encoding="utf-8")
        for url in (
            "https://scwellservice.com/pages/services/water-storage-tanks.html",
            "https://scwellservice.com/pages/services/booster-pumps.html",
            "https://scwellservice.com/pages/services/pressure-tanks.html",
            "https://scwellservice.com/services/desert-hot-springs/",
            "https://scwellservice.com/services/mountain-center/",
        ):
            self.assertIn(url, pages)
        self.assertIn("https://scwellservice.com/services/desert-hot-springs/", services)
        self.assertIn("https://scwellservice.com/services/mountain-center/", services)
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        service_index = (ROOT / "pages" / "services" / "index.html").read_text(encoding="utf-8")
        city_index = (ROOT / "services" / "index.html").read_text(encoding="utf-8")
        locations = (ROOT / "locations" / "index.html").read_text(encoding="utf-8")
        riverside = (ROOT / "pages" / "locations" / "riverside.html").read_text(encoding="utf-8")
        anza = (ROOT / "services" / "anza" / "index.html").read_text(encoding="utf-8")
        for href in (
            "water-storage-tanks.html",
            "booster-pumps.html",
            "pressure-tanks.html",
        ):
            self.assertIn(href, home)
            self.assertIn(href, service_index)
        self.assertIn("/services/desert-hot-springs/", city_index)
        self.assertIn("/services/mountain-center/", city_index)
        self.assertIn("/services/desert-hot-springs/", locations)
        self.assertIn("/services/mountain-center/", locations)
        self.assertIn("/services/desert-hot-springs/", riverside)
        self.assertIn("/services/mountain-center/", riverside)
        self.assertIn("/services/desert-hot-springs/", anza)
        self.assertIn("/services/mountain-center/", anza)
        idyllwild = (ROOT / "services" / "idyllwild" / "index.html").read_text(encoding="utf-8")
        mountain = (ROOT / "services" / "mountain-center" / "index.html").read_text(encoding="utf-8")
        self.assertIn("/services/mountain-center/", idyllwild)
        self.assertIn("/services/idyllwild/", mountain)


class FinancingPageTests(unittest.TestCase):
    def test_financing_page_states_wisetack_without_invented_terms(self):
        html = (ROOT / "pages" / "financing.html").read_text(encoding="utf-8")
        title = _title(html)
        self.assertLessEqual(len(title.replace("&amp;", "&")), 60)
        self.assertIn("well drilling financing near me", html.lower())
        self.assertIn("https://scwellservice.com/pages/financing.html", html)
        self.assertIn("https://www.wisetack.com/", html)
        self.assertIn("Wisetack", html)
        self.assertNotIn("Wisestack", html)
        self.assertIn("qualified customers", html.lower())
        self.assertIn("tel:+17604408520", html)
        self.assertIn("sms:7602195877", html)
        self.assertIn("/contact.html", html)
        self.assertIn("1086994", html)
        self.assertNotIn("$", html)
        self.assertNotIn("%", html)
        self.assertNotIn("APR", html)
        self.assertNotIn("no credit", html.lower())
        self.assertNotIn("credit check", html.lower())
        self.assertFalse(html_is_noindex(ROOT / "pages" / "financing.html"))
        types = {block.get("@type") for block in _json_ld_blocks(html)}
        self.assertIn("Service", types)
        self.assertIn("BreadcrumbList", types)
        self.assertNotIn("FAQPage", types)
        pages = (ROOT / "sitemap-pages.xml").read_text(encoding="utf-8")
        self.assertIn("https://scwellservice.com/pages/financing.html", pages)
        for rel in (
            "index.html",
            "pages/services/index.html",
            "pages/services/well-drilling.html",
            "pages/services/pump-repair.html",
            "pages/services/booster-pumps.html",
            "services/index.html",
            "services/ramona/well-drilling.html",
            "services/anza/well-drilling.html",
        ):
            self.assertIn("/pages/financing.html", (ROOT / rel).read_text(encoding="utf-8"), rel)

    def test_pump_repair_cost_section_has_no_prices(self):
        html = (ROOT / "pages" / "services" / "pump-repair.html").read_text(encoding="utf-8")
        self.assertIn('id="pump-replacement-cost"', html)
        section = html.split('id="pump-replacement-cost"', 1)[1].split("</section>", 1)[0]
        self.assertIn("What affects well pump replacement cost", section)
        for phrase in (
            "Well depth",
            "horsepower",
            "gallons per minute",
            "Wire run",
            "control box",
            "Pressure tank",
            "Access and pull rig",
            "Emergency timing",
        ):
            self.assertIn(phrase, section)
        self.assertNotIn("$", section)
        self.assertNotRegex(section, r"\$\s*\d")


if __name__ == "__main__":
    unittest.main()
