#!/usr/bin/env python3
"""Sourced town × service sections. Does not rewrite pages."""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from far_city_factory_lib import html_is_noindex
from service_town_local import (
    BLOCK_RE,
    GAP_TOWNS,
    PHONE_DISPLAY,
    SERVICE_FILES,
    WellStats,
    assign_reviews,
    city_matches_slug,
    insert_block,
    job_matches,
    load_reviews,
    nearest_10,
    target_towns,
)

ROOT = Path(__file__).resolve().parents[1]
JSONLD_RE = re.compile(
    r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
    re.S,
)


class MatcherTests(unittest.TestCase):
    def test_drill_mud_is_not_drilling(self):
        project = {
            "title": "Well bail and brush",
            "summary": "Bailed gravel and drill mud and brushed the liner.",
            "category": "maintenance",
        }
        self.assertFalse(job_matches("well-drilling.html", project))
        self.assertFalse(job_matches("well-inspection.html", project))

    def test_pull_and_inspect_stays_on_pump_repair(self):
        project = {
            "title": "Pull and inspect pump",
            "summary": "Pulled the pump and motor for inspection.",
            "category": "pump",
        }
        self.assertTrue(job_matches("well-pump-repair.html", project))
        self.assertFalse(job_matches("well-inspection.html", project))

    def test_booster_title_is_not_well_pump_repair(self):
        project = {
            "title": "Booster pump upgrade",
            "summary": "Replaced the booster pump.",
            "category": "pump",
        }
        self.assertFalse(job_matches("well-pump-repair.html", project))
        self.assertTrue(job_matches("booster-pump.html", project))

    def test_booster_note_that_mentions_a_filter_is_not_treatment(self):
        project = {
            "title": "Booster pump upgrade",
            "summary": "Replaced the booster and added a spin-down sand separator.",
            "category": "pump",
        }
        self.assertFalse(job_matches("water-treatment.html", project))
        titled = {
            "title": "Spin-down filter replacement",
            "summary": "Installed a new spin-down filter.",
            "category": "water-quality",
        }
        self.assertTrue(job_matches("water-treatment.html", titled))

    def test_production_test_is_inspection(self):
        project = {
            "title": "Well production test",
            "summary": "Ran timed bucket tests.",
            "category": "maintenance",
        }
        self.assertTrue(job_matches("well-inspection.html", project))
        self.assertFalse(job_matches("water-testing.html", project))

    def test_city_match_allows_case_and_deluz_only(self):
        self.assertTrue(city_matches_slug("cuyamaca", "Cuyamaca"))
        self.assertFalse(city_matches_slug("cuyamaca", "CUYAMACA PEAK"))
        self.assertFalse(city_matches_slug("cuyamaca", "Lake Cuyamaca"))
        self.assertTrue(city_matches_slug("de-luz", "De Luz"))
        self.assertTrue(city_matches_slug("de-luz", "DeLuz"))
        self.assertTrue(city_matches_slug("de-luz", "Deluz"))
        self.assertFalse(city_matches_slug("rainbow", "RAINBOW, FALLBROOK"))
        self.assertTrue(city_matches_slug("idyllwild", "Idyllwild"))
        self.assertFalse(city_matches_slug("idyllwild", "Idyllwild-Pine Cove"))


class WellFileTests(unittest.TestCase):
    def test_moreno_valley_matches_published_quartiles(self):
        stats = WellStats("moreno-valley")
        self.assertEqual(stats.n, 52)
        self.assertEqual(stats.median_depth, 304)
        self.assertEqual(nearest_10(stats.q1), 270)
        self.assertEqual(nearest_10(stats.q3), 440)
        self.assertEqual(stats.n_yield, 49)
        self.assertEqual(stats.median_yield, 10)

    def test_mixed_case_towns_have_domestic_wells(self):
        self.assertGreater(WellStats("cuyamaca").n, 0)
        self.assertGreater(WellStats("de-luz").n, 0)
        self.assertGreater(WellStats("idyllwild").n, 0)
        self.assertGreater(WellStats("rainbow").n, 0)
        self.assertGreater(WellStats("temecula").n, 8)


class ReviewSourceTests(unittest.TestCase):
    def test_reviews_page_is_ramona_and_anza_only(self):
        reviews = load_reviews()
        self.assertEqual(len(reviews), 9)
        self.assertEqual({review["town"] for review in reviews}, {"ramona", "anza"})
        firsts = {review["first"] for review in reviews}
        self.assertEqual(
            firsts,
            {"Dennis", "Robert", "Sophie", "Dan", "Jerry", "John", "Jenise", "Rosalind", "Kathleen"},
        )
        for review in reviews:
            self.assertNotIn(review["full"].split()[-1], review["first"])
            self.assertEqual(len(review["first"].split()), 1)

    def test_other_towns_get_no_review(self):
        reviews = load_reviews()
        assigned = assign_reviews("temecula", reviews)
        self.assertTrue(all(review is None for review in assigned.values()))

    def test_ramona_pump_review_mentions_pump(self):
        reviews = load_reviews()
        assigned = assign_reviews("ramona", reviews)
        pump = assigned["well-pump-repair.html"]
        self.assertIsNotNone(pump)
        self.assertEqual(pump["first"], "Dennis")
        self.assertIn("pump", pump["text"].lower())


class InsertTests(unittest.TestCase):
    def test_insert_keeps_existing_copy_and_is_idempotent(self):
        page = "<main><p>Keep this sentence.</p></main>"
        block = "<!-- SERVICE_TOWN_LOCAL_START -->\n<section>Local</section>\n<!-- SERVICE_TOWN_LOCAL_END -->"
        once = insert_block(page, block)
        twice = insert_block(once, block)
        self.assertEqual(once, twice)
        self.assertIn("Keep this sentence.", twice)
        self.assertEqual(len(BLOCK_RE.findall(twice)), 1)
        self.assertLess(twice.find("Keep this sentence."), twice.find("SERVICE_TOWN_LOCAL_START"))


class RenderedPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sample = ROOT / "services" / "temecula" / "well-pump-repair.html"
        if "SERVICE_TOWN_LOCAL_START" not in sample.read_text(encoding="utf-8"):
            raise unittest.SkipTest("sections have not been generated")

    def test_scope_is_47_indexable_towns_plus_perris(self):
        towns = target_towns()
        self.assertEqual(len(towns), 48)
        for slug in GAP_TOWNS:
            self.assertIn(slug, towns)
        self.assertNotIn("palm-springs", towns)
        self.assertNotIn("cathedral-city", towns)
        self.assertNotIn("moreno-valley", towns)

    def test_every_target_page_has_one_sourced_section(self):
        last_names = ("Albert", "Gonzalez", "Duck", "Blosch", "Sanders", "Reveles", "Mastro", "Brooks", "Hefley")
        for town in target_towns():
            for name in SERVICE_FILES:
                path = ROOT / "services" / town / name
                page = path.read_text(encoding="utf-8")
                blocks = BLOCK_RE.findall(page)
                self.assertEqual(len(blocks), 1, path)
                block = blocks[0]
                self.assertIn("FAQPage", block, path)
                self.assertNotIn("AggregateRating", block, path)
                self.assertNotIn("463-0493", block, path)
                self.assertNotIn("recent-work-card", block, path)
                self.assertIn(PHONE_DISPLAY, block, path)
                self.assertIn("tel:+17604408520", block, path)
                self.assertNotIn("57174+CA-371", block, path)
                payload = json.loads(JSONLD_RE.search(block).group(1))
                self.assertEqual(payload["@type"], "FAQPage")
                questions = payload["mainEntity"]
                self.assertGreaterEqual(len(questions), 2, path)
                self.assertLessEqual(len(questions), 3, path)
                for question in questions:
                    self.assertIn(question["name"], block, path)
                    self.assertIn(question["acceptedAnswer"]["text"], block, path)
                for href in re.findall(r'href="(/recent-work/[^"]+)"', block):
                    self.assertTrue((ROOT / href.lstrip("/")).is_file(), href)
                if town in {"ramona", "anza"}:
                    self.assertIn("reviews page", block, path)
                    self.assertNotIn(town.title() + " Albert", block)
                else:
                    self.assertNotIn("<blockquote>", block, path)
                for last in last_names:
                    self.assertNotRegex(block, rf"<p>{last}|, {last},", path)
            if town == "perris":
                text = (ROOT / "services" / "perris" / "well-pump-repair.html").read_text(encoding="utf-8")
                self.assertTrue(html_is_noindex(ROOT / "services" / "perris" / "well-pump-repair.html"))
                self.assertIn('content="noindex, follow"', text)

    def test_same_town_services_are_not_copies(self):
        sections = []
        for name in SERVICE_FILES:
            page = (ROOT / "services" / "temecula" / name).read_text(encoding="utf-8")
            sections.append(BLOCK_RE.search(page).group(0))
        self.assertEqual(len(set(sections)), len(SERVICE_FILES))

    def test_far_city_pages_are_untouched(self):
        page = (ROOT / "services" / "palm-springs" / "well-pump-repair.html").read_text(encoding="utf-8")
        self.assertNotIn("SERVICE_TOWN_LOCAL_START", page)
        self.assertTrue(html_is_noindex(ROOT / "services" / "palm-springs" / "well-pump-repair.html"))


if __name__ == "__main__":
    unittest.main()
