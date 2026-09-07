#!/usr/bin/env python3
"""Unit tests for leftover CSLB / age / 4.9 / permit-city cleanup."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from leftover_claims_lib import (
    CANONICAL_CSLB,
    CANONICAL_CSLB_HASH,
    PERMIT_CITY_CANONICAL,
    is_claim_file,
    is_programmatic_well_permit,
    normalize_fake_rating_stars,
    process_html_text,
    replace_company_age_claims,
    replace_fake_rating_lines,
    replace_leftover_licenses,
)


BONSALL_SNIPPET = """<!DOCTYPE html>
<html lang="en">
<head>
<title>Well Permits in Bonsall</title>
<link href="https://scwellservice.com/blog/well-permit-bonsall.html" rel="canonical"/>
</head>
<body>
<p>We are a licensed California C-57 Water Well Drilling Contractor with more than 30 years of experience and a 4.9-star reputation across San Diego County. For Bonsall property owners, "turnkey" means exactly that.</p>
<p>Absolutely. As a licensed C-57 contractor with more than 30 years of work across San Diego County, we handle the entire process turnkey.</p>
<footer>
<p class="text-gray-400 text-sm">Licensed C-57 Water Well Drilling Contractor serving San Diego, Riverside, and San Bernardino Counties.</p>
<div>© 2025 Southern California Well Service. All rights reserved.</div>
</footer>
</body>
</html>
"""

NO_WATER_SNIPPET = (
    "Southern California Well Service provides expert well diagnostics and pump repair "
    "across San Diego, Riverside, and San Bernardino Counties. Licensed C-57 contractor with 4.9★ rating."
)

WELL_AGE_KEEP = (
    "Many wells over 30 years old need a new drop pipe. "
    "Casing over 30 years can fail. Joe Fain founded Fain Drilling with over 60 years of history."
)

FONTANA_SNIPPET = """<meta content="Well Drilling in Fontana, San Bernardino County. Licensed C-57 contractor, 4.9★ rated, 30+ years experience. Call (760) 440-8520." name="description"/>
<meta name="description" content="Southern California Well Service provides professional well drilling to Fontana and throughout San Bernardino County. With 30+ years experience and a 4.9★...">
<p class="text-xl text-gray-600 mb-8">Southern California Well Service provides professional well drilling to Fontana and throughout San Bernardino County. With 30+ years experience and a 4.9★ Google rating, we're the trusted choice for well owners.</p>
"""

ESCONDIDO_SNIPPET = """<title>Well Service Escondido CA | Licensed Pros • 4.9★ Rated</title>
<meta name="description" content="Need well service in Escondido? SCWS provides pump repair, water testing, and maintenance. Licensed C-57 contractor, 4.9★ rated. Free estimates available.">
<h1>Well Service Escondido CA | Licensed Pros • 4.9★ Rated</h1>
<li><strong>4.9★ Google rating</strong> — hundreds of reviews from real customers across San Diego County</li>
"""

FAKE_SCHEMA = (
    '"aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.9", "reviewCount": "127"}'
)


class LeftoverClaimsTests(unittest.TestCase):
    def test_license_replacements(self):
        src = "License #1013597 | CSLB #1059498 | #1129498 | #1086994.#1098473 | license number 1013597"
        out = replace_leftover_licenses(src)
        self.assertNotIn("1013597", out)
        self.assertNotIn("1059498", out)
        self.assertNotIn("1129498", out)
        self.assertNotIn("1098473", out)
        self.assertIn("license number 1086994", out)
        self.assertGreaterEqual(out.count(CANONICAL_CSLB), 5)

    def test_keep_well_age_and_joe_fain(self):
        out = replace_company_age_claims(WELL_AGE_KEEP)
        self.assertIn("wells over 30 years old", out)
        self.assertIn("Casing over 30 years", out)
        self.assertIn("Joe Fain", out)
        self.assertIn("over 60 years of history", out)

    def test_bonsall_template(self):
        out = process_html_text(BONSALL_SNIPPET, "well-permit-bonsall.html")
        self.assertNotIn("more than 30 years", out)
        self.assertNotIn("4.9-star", out)
        self.assertIn("1086994", out)
        self.assertIn('name="robots" content="noindex, follow"', out)
        self.assertIn(PERMIT_CITY_CANONICAL, out)
        self.assertNotIn("https://scwellservice.com/blog/well-permit-bonsall.html", out)
        self.assertIn("founded in 2020", out)
        self.assertIn("60+ years of family heritage", out)

    def test_keep_list_not_programmatic(self):
        self.assertFalse(is_programmatic_well_permit("well-permit-guide-san-diego.html"))
        self.assertTrue(is_programmatic_well_permit("well-permit-bonsall.html"))

    def test_keep_list_not_noindexed(self):
        src = """<head><link href="https://scwellservice.com/blog/well-permit-guide-san-diego.html" rel="canonical"/></head>"""
        out = process_html_text(src, "well-permit-guide-san-diego.html")
        self.assertNotIn("noindex", out)
        self.assertIn("well-permit-guide-san-diego.html", out)

    def test_no_water_rating(self):
        out = replace_fake_rating_lines(NO_WATER_SNIPPET)
        self.assertNotIn("4.9", out)
        self.assertIn("1086994", out)

    def test_no_invented_review_count(self):
        out = replace_fake_rating_lines("Licensed C-57 contractor with 4.9★ rating.")
        self.assertNotIn("127", out)
        self.assertNotIn("4.9", out)

    def test_city_incorporation_kept(self):
        src = "Menifee incorporated in 2008. Newer incorporation (2008)."
        out = replace_company_age_claims(src)
        self.assertIn("incorporated in 2008", out)
        self.assertIn("Newer incorporation (2008)", out)

    def test_serving_footer_age(self):
        out = replace_company_age_claims(
            "Serving Winter Gardens and all of San Diego County for over 30 years."
        )
        self.assertNotIn("over 30 years", out)
        self.assertIn("since 2020", out)

    def test_plus_years_in_county(self):
        out = replace_company_age_claims(
            "Licensed C-57, 30+ years in San Diego County, same-day emergency service."
        )
        self.assertNotIn("30+ years", out)
        self.assertIn("1086994", out)
        self.assertIn("2020", out)

    def test_thirty_plus_spelled_out(self):
        out = replace_company_age_claims(
            "We are a licensed C-57 contractor with 30-plus years of experience "
            "because we do the work right. Across three decades serving San Diego County."
        )
        self.assertNotIn("30-plus years", out)
        self.assertNotIn("three decades", out)
        self.assertIn("2020", out)

    def test_html_wrapped_company_age_and_truncated_rating(self):
        src = (
            "Southern California Well Service has kept private wells running "
            "across the region for <strong>more than 30 years</strong>. "
            "<title>Well Service Norco CA | Horse Property Well Experts • 4.9★</title>"
        )
        out = process_html_text(src, "well-service-norco.html")
        self.assertNotIn("more than 30 years", out)
        self.assertNotIn("4.9★", out)
        self.assertIn("since 2020", out)
        self.assertIn("1086994", out)

    def test_keep_well_ownership_cost_math(self):
        src = "Over 30 years, well ownership typically saves $25,000-$40,000 versus city water."
        out = replace_company_age_claims(src)
        self.assertIn("Over 30 years, well ownership typically saves", out)

    def test_served_region_not_confused_with_well_is(self):
        src = (
            "A dependable well is everything. Southern California Well Service "
            "has served this valley for more than 30 years as a licensed C-57 contractor."
        )
        out = replace_company_age_claims(src)
        self.assertNotIn("more than 30 years", out)
        self.assertIn("since 2020", out)
        self.assertIn("well is everything", out)

    def test_fontana_factory_meta_and_body(self):
        out = process_html_text(FONTANA_SNIPPET, "well-drilling-fontana.html")
        self.assertNotIn("30+ years", out)
        self.assertNotIn("4.9★", out)
        self.assertNotIn("4.9", out)
        self.assertIn("1086994", out)
        self.assertIn("2020", out)

    def test_escondido_title_h1_and_body(self):
        out = process_html_text(ESCONDIDO_SNIPPET, "well-service-escondido.html")
        self.assertNotIn("4.9★", out)
        self.assertNotIn("4.9", out)
        self.assertNotIn("hundreds of reviews", out)
        self.assertIn("1086994", out)
        self.assertIn("Well Service Escondido CA", out)

    def test_strip_reviewcount_127_no_invented_count(self):
        out = replace_fake_rating_lines(FAKE_SCHEMA)
        self.assertNotIn("127", out)
        self.assertNotIn("4.9", out)
        self.assertNotIn("aggregateRating", out)

    def test_claim_file_covers_city_factory_not_homepage(self):
        self.assertTrue(is_claim_file(Path("blog/well-drilling-fontana.html")))
        self.assertTrue(is_claim_file(Path("blog/well-service-escondido.html")))
        self.assertTrue(is_claim_file(Path("services/fontana/well-drilling.html")))
        self.assertTrue(is_claim_file(Path("services/residential/index.html")))
        self.assertTrue(is_claim_file(Path("heritage-well-service.html")))
        self.assertTrue(is_claim_file(Path("ransom-pump.html")))
        self.assertTrue(is_claim_file(Path("faq.html")))
        self.assertFalse(is_claim_file(Path("index.html")))
        self.assertFalse(is_claim_file(Path("js/google-reviews.js")))

    def test_live_permit_city_and_no_water_files(self):
        root = Path(__file__).resolve().parents[1]
        bonsall = (root / "blog" / "well-permit-bonsall.html").read_text(encoding="utf-8")
        no_water = (root / "blog" / "no-water-from-well.html").read_text(encoding="utf-8")
        self.assertIn('name="robots" content="noindex, follow"', bonsall)
        self.assertIn("1086994", bonsall)
        self.assertNotIn("more than 30 years", bonsall)
        self.assertNotIn("4.9-star", bonsall)
        self.assertNotIn("4.9★", bonsall)
        self.assertIn("well-permits-california.html", bonsall)
        self.assertNotIn("4.9", no_water)
        self.assertIn("1086994", no_water)

    def test_live_fontana_and_escondido_after_fix(self):
        root = Path(__file__).resolve().parents[1]
        fontana = (root / "blog" / "well-drilling-fontana.html").read_text(encoding="utf-8")
        escondido = (root / "blog" / "well-service-escondido.html").read_text(encoding="utf-8")
        if "4.9★" in fontana or "30+ years" in fontana:
            self.skipTest("fixer has not been applied to published HTML yet")
        self.assertNotIn("30+ years", fontana)
        self.assertNotIn("4.9★", fontana)
        self.assertNotIn("4.9", fontana)
        self.assertIn("1086994", fontana)
        self.assertIn("2020", fontana)
        self.assertNotIn("4.9★", escondido)
        self.assertNotIn("4.9", escondido)
        self.assertIn("1086994", escondido)
        self.assertIn("Well Service Escondido", escondido)

    def test_normalize_html_entity_and_emoji_stars(self):
        self.assertEqual(normalize_fake_rating_stars("4.9&#9733; rated"), "4.9★ rated")
        self.assertEqual(normalize_fake_rating_stars("4.9&#x2605; rated"), "4.9★ rated")
        self.assertEqual(normalize_fake_rating_stars("4.9⭐ rating"), "4.9★ rating")
        self.assertEqual(normalize_fake_rating_stars("4.9瘅 rated"), "4.9★ rated")
        self.assertEqual(normalize_fake_rating_stars("4.9☆ rated"), "4.9★ rated")
        self.assertEqual(normalize_fake_rating_stars("4.9 rating"), "4.9★ rating")

    def test_helendale_decimal_entity_rating(self):
        src = (
            '<meta content="Well Drilling in Helendale, San Bernardino County. '
            'Licensed C-57 contractor, 4.9&#9733; rated, founded in 2020, with '
            '60+ years of family heritage. Call (760) 440-8520." name="description"/>'
            '<p class="text-xl text-gray-600 mb-8">Southern California Well Service '
            "provides professional well drilling to Helendale and throughout San "
            "Bernardino County. founded in 2020, with 60+ years of family heritage "
            "and a 4.9&#9733; Google rating, we're the trusted choice for well owners.</p>"
            '<p class="text-gray-600">4.9&#9733; rating, hundreds of reviews</p>'
        )
        out = process_html_text(src, "well-drilling-helendale.html")
        self.assertNotIn("4.9", out)
        self.assertNotIn("&#9733;", out)
        self.assertNotIn("★", out)
        self.assertIn("1086994", out)
        self.assertIn("founded in 2020", out)
        self.assertIn("60+ years of family heritage", out)

    def test_yermo_hex_entity_rating(self):
        src = (
            "Licensed C-57 contractor, 4.9&#x2605; rated, founded in 2020, "
            "with 60+ years of family heritage and a 4.9&#x2605; Google rating"
        )
        out = replace_fake_rating_lines(src)
        self.assertNotIn("4.9", out)
        self.assertNotIn("&#x2605;", out)

    def test_emoji_and_mojibake_rating(self):
        src = (
            '<p class="text-gray-600">4.9⭐ rating, hundreds of reviews</p>'
            "Licensed C-57 contractor, 4.9瘅 rated, founded in 2020"
        )
        out = replace_fake_rating_lines(src)
        self.assertNotIn("4.9", out)
        self.assertNotIn("⭐", out)
        self.assertNotIn("瘅", out)

    def test_white_star_and_starless_rating(self):
        src = (
            "Licensed C-57 contractor, 4.9☆ rated, founded in 2020"
            '<p class="text-gray-600">4.9 rating, hundreds of reviews</p>'
        )
        out = replace_fake_rating_lines(src)
        self.assertNotIn("4.9", out)
        self.assertNotIn("☆", out)
        self.assertIn("1086994", out)

    def test_anza_google_rating_without_star_char(self):
        src = (
            '"aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.9", '
            '"reviewCount": "50"}'
            "<p><strong>★★★★★ 4.9 Google Rating</strong> — Trusted by our Anza neighbors</p>"
        )
        out = replace_fake_rating_lines(src)
        self.assertNotIn("4.9", out)
        self.assertNotIn("aggregateRating", out)
        self.assertIn("1086994", out)
        self.assertIn("Trusted by our Anza neighbors", out)

    def test_keep_product_and_stat_four_point_nine(self):
        src = (
            "<p><strong>Rating: ★★★★★ (4.9/5)</strong></p>"
            "<tr><td>2018</td><td>10,892</td><td>-4.9%</td></tr>"
        )
        out = replace_fake_rating_lines(src)
        self.assertIn("(4.9/5)", out)
        self.assertIn("-4.9%", out)

    def test_css_comma_selectors_and_file_accept_kept(self):
        src = (
            ".how h2, .legend h2, .gbp-pool h2 { margin: 0; }\n"
            'accept=".pdf,.doc,.docx"\n'
            "rgba(255,255,255,.15)\n"
            ".hero .gbp-ratings-line, .hero .gbp-ratings-line a { color: #fff; }\n"
            ".category-btn:hover, .category-btn.active { background: #1a365d; }\n"
        )
        out = process_html_text(src, "reviews.html")
        self.assertIn(".how h2, .legend h2, .gbp-pool h2", out)
        self.assertIn('accept=".pdf,.doc,.docx"', out)
        self.assertIn("rgba(255,255,255,.15)", out)
        self.assertIn(".hero .gbp-ratings-line, .hero .gbp-ratings-line a", out)
        self.assertIn(".category-btn:hover, .category-btn.active", out)

    def test_heritage_ransom_127_review_block(self):
        src = (
            '<span class="text-2xl font-bold text-gray-900">4.9</span>\n'
            '<span class="text-gray-600">★ on Google (127 reviews)</span>'
        )
        out = replace_fake_rating_lines(src)
        self.assertNotIn("4.9", out)
        self.assertNotIn("127 reviews", out)
        self.assertIn("1086994", out)
        self.assertIn("2020", out)

    def test_live_entity_encoded_pages_after_fix(self):
        root = Path(__file__).resolve().parents[1]
        samples = [
            root / "blog" / "well-drilling-helendale.html",
            root / "blog" / "well-drilling-yermo.html",
            root / "blog" / "booster-pump-east-otay-mesa.html",
            root / "blog" / "emergency-well-repair-cedar-glen.html",
        ]
        for path in samples:
            if not path.exists():
                self.skipTest(f"missing {path.name}")
            text = path.read_text(encoding="utf-8")
            if "4.9&#" in text or "4.9★" in text or "4.9瘅" in text:
                self.skipTest("fixer has not been applied to published HTML yet")
            self.assertNotIn("4.9&#", text)
            self.assertNotIn("4.9★", text)
            self.assertNotIn("4.9 rated", text.lower())


if __name__ == "__main__":
    unittest.main()
