#!/usr/bin/env python3
"""Unit tests for leftover CSLB / age / 4.9 / permit-city cleanup."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from leftover_claims_lib import (
    CANONICAL_CSLB_HASH,
    PERMIT_CITY_CANONICAL,
    is_programmatic_well_permit,
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


class LeftoverClaimsTests(unittest.TestCase):
    def test_license_replacements(self):
        src = "License #1013597 | CSLB #1059498 | #1129498 | #1086994.#1098473"
        out = replace_leftover_licenses(src)
        self.assertNotIn("1013597", out)
        self.assertNotIn("1059498", out)
        self.assertNotIn("1129498", out)
        self.assertNotIn("1098473", out)
        self.assertEqual(out.count(CANONICAL_CSLB_HASH), 4)

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


if __name__ == "__main__":
    unittest.main()
