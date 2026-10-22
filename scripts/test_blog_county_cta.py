#!/usr/bin/env python3
"""County blog CTA and the extra service links. Does not rewrite posts."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from blog_county_cta import (
    CTA_END,
    CTA_START,
    LINK_END,
    LINK_START,
    SERVICE_LINKS,
    hub_links,
    indexable_hubs,
)

ROOT = Path(__file__).resolve().parents[1]
BLOCK_RE = re.compile(re.escape(CTA_START) + r".*?" + re.escape(CTA_END), re.S)


class BlogCtaTests(unittest.TestCase):
    def test_murrieta_post_links_riverside_hubs_and_keeps_old_cta(self):
        text = (ROOT / "blog" / "well-service-murrieta.html").read_text(encoding="utf-8")
        self.assertIn("Need Help With Your Well?", text)
        blocks = BLOCK_RE.findall(text)
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertIn("Need a pro in San Diego or Riverside County?", block)
        self.assertIn("tel:+17604408520", block)
        self.assertIn("(760) 440-8520", block)
        self.assertIn('class="scws-book-online"', block)
        self.assertIn("/js/book-online.js", block)
        self.assertIn('href="/services/murrieta/"', block)
        self.assertIn('href="/services/temecula/"', block)
        self.assertNotIn("463-0493", block)
        self.assertNotIn("AggregateRating", block)
        self.assertLess(text.find("Need Help With Your Well?"), text.find(CTA_START))

    def test_generic_guide_links_both_counties(self):
        text = (ROOT / "blog" / "well-pump-sizing-calculator.html").read_text(encoding="utf-8")
        block = BLOCK_RE.search(text).group(0)
        for slug in ("ramona", "escondido", "temecula", "murrieta"):
            self.assertIn(f'href="/services/{slug}/"', block)

    def test_twenty_new_service_links_and_prior_flagship_link_remains(self):
        self.assertEqual(len(SERVICE_LINKS), 20)
        for name in SERVICE_LINKS:
            text = (ROOT / "blog" / name).read_text(encoding="utf-8")
            self.assertIn(LINK_START, text, name)
            self.assertIn(LINK_END, text, name)
            self.assertLess(text.find(LINK_START), text.find(CTA_START), name)
        flagship = (ROOT / "blog" / "well-pump-sizing-calculator.html").read_text(encoding="utf-8")
        self.assertIn("/pages/services/pump-repair.html", flagship)
        self.assertNotIn(LINK_START, flagship)

    def test_book_online_points_blog_links_without_editing_call_tracking(self):
        script = (ROOT / "js" / "book-online.js").read_text(encoding="utf-8")
        self.assertIn("var onBlog = path.indexOf('/blog/') !== -1;", script)
        self.assertIn("if (!onService) return;", script)
        self.assertIn("7c569177-85d0-4bac-9c7f-e2afe6652ee1", script)
        tracking = (ROOT / "js" / "call-tracking.js").read_text(encoding="utf-8")
        self.assertIn("463-0493", tracking)

    def test_noindex_town_is_not_a_hub_link(self):
        hubs = set(indexable_hubs())
        self.assertNotIn("palm-springs", hubs)
        links = [slug for slug, _label in hub_links("emergency-well-repair-palm-springs.html", hubs, {})]
        self.assertNotIn("palm-springs", links)
        self.assertIn("ramona", links)


if __name__ == "__main__":
    unittest.main()
