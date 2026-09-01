#!/usr/bin/env python3
"""Unit tests for the Jobber photo audit (no network, no secrets)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from photo_audit_lib import (
    SHOP_PHONE_RE,
    assign_shop,
    build_queue,
    caption_for_photo,
    eligible_handoff,
    is_junk_filename,
    is_publish_eligible,
    kept_photo_indexes,
    permanent_skip_reason,
    photo_id,
    record_decision,
    shop_location_label,
)


def _job(**overrides):
    base = {
        "id": "gid://job/1",
        "jobNumber": 4242,
        "title": "Pull & replace pump and motor",
        "completedAt": "2026-09-01T18:00:00Z",
        "property": {"address": {"city": "Ramona"}},
        "noteAttachments": {
            "nodes": [
                {
                    "fileName": "wellhead.jpg",
                    "url": "https://files.example/wellhead.jpg",
                    "contentType": "image/jpeg",
                }
            ]
        },
    }
    base.update(overrides)
    return base


class SkipTests(unittest.TestCase):
    def test_mike_daniels_job_number(self):
        reason = permanent_skip_reason(_job(jobNumber=3224))
        self.assertEqual(reason, "permanent-skip-job")

    def test_mike_daniels_email(self):
        job = _job(
            client={"emails": [{"address": "gotmikedaniels@gmail.com"}]}
        )
        self.assertEqual(permanent_skip_reason(job), "permanent-skip-client")

    def test_mike_daniels_name(self):
        job = _job(client={"firstName": "Mike", "lastName": "Daniels"})
        self.assertEqual(permanent_skip_reason(job), "permanent-skip-client")

    def test_invoice_5629(self):
        job = _job(instructions="See invoice 5629 for payment.")
        self.assertEqual(permanent_skip_reason(job), "permanent-skip-invoice")

    def test_normal_job_not_skipped(self):
        self.assertIsNone(permanent_skip_reason(_job()))


class JunkTests(unittest.TestCase):
    def test_hides_paperwork_filenames(self):
        for name in (
            "notebook-page.jpg",
            "handwritten-notes.png",
            "customer-email.JPG",
            "well-permit-scan.jpg",
            "WCR-2024.jpg",
            "invoice-5629.png",
            "jobber-screenshot.jpg",
            "iphone screenshot.PNG",
        ):
            junk, reason = is_junk_filename(name, "image/jpeg")
            self.assertTrue(junk, name)
            self.assertTrue(reason, name)

    def test_keeps_field_photos(self):
        junk, reason = is_junk_filename("wellhead.jpg", "image/jpeg")
        self.assertFalse(junk)
        self.assertIsNone(reason)


class ShopTests(unittest.TestCase):
    def test_anza_and_high_desert(self):
        self.assertEqual(assign_shop("Anza"), "anza")
        self.assertEqual(assign_shop("Aguanga"), "anza")
        self.assertEqual(assign_shop("Apple Valley"), "anza")
        self.assertEqual(assign_shop("Yucca Valley, CA"), "anza")

    def test_west_central_sd(self):
        self.assertEqual(assign_shop("Ramona"), "ramona")
        self.assertEqual(assign_shop("Poway"), "ramona")
        self.assertEqual(assign_shop("San Diego"), "ramona")
        self.assertEqual(assign_shop("Escondido"), "ramona")

    def test_unknown_city_still_routes_ramona(self):
        self.assertEqual(assign_shop(""), "ramona")
        self.assertEqual(assign_shop("Unincorporated Somewhere"), "ramona")
        self.assertEqual(shop_location_label("", "ramona"), "Ramona area")
        self.assertEqual(shop_location_label("", "anza"), "Anza area")


class CaptionTests(unittest.TestCase):
    def test_city_plus_work_no_pii_or_phone(self):
        out = caption_for_photo(
            title="Pull & replace pump at 123 Oak Street for $1,200 — call 760-219-5877",
            city="Ramona",
        )
        self.assertIn("Ramona", out)
        self.assertNotIn("123", out)
        self.assertNotIn("$", out)
        self.assertNotIn("760-219-5877", out)
        self.assertNotIn("760-440-8520", out)
        self.assertFalse(SHOP_PHONE_RE.search(out))

    def test_unique_when_same_title_city(self):
        taken: set[str] = set()
        a = caption_for_photo(title="Well diagnostic", city="Anza", filename="a.jpg", taken=taken)
        b = caption_for_photo(title="Well diagnostic", city="Anza", filename="pressure-tank.jpg", taken=taken)
        self.assertNotEqual(a.lower(), b.lower())
        self.assertIn("Anza", a)
        self.assertIn("Anza", b)


class PageAndRobotsTests(unittest.TestCase):
    def test_audit_page_is_noindex_and_not_in_sitemap(self):
        page = Path(__file__).resolve().parents[1] / "ops" / "photo-audit" / "index.html"
        html = page.read_text()
        self.assertIn('name="robots" content="noindex, nofollow, noarchive"', html)
        self.assertNotIn("googletagmanager", html)
        self.assertNotIn("760-219-5877", html)
        self.assertNotIn("gotmikedaniels", html.lower())
        robots = (Path(__file__).resolve().parents[1] / "robots.txt").read_text()
        self.assertIn("Disallow: /ops/photo-audit", robots)
        sitemap = (Path(__file__).resolve().parents[1] / "sitemap-pages.xml").read_text()
        self.assertNotIn("/ops/photo-audit", sitemap)


class QueueAndDecisionTests(unittest.TestCase):
    def test_queue_hides_permanent_skip_by_default(self):
        jobs = [_job(jobNumber=3224), _job()]
        items = build_queue(jobs, decisions={"photos": {}})
        ids = [i["jobId"] for i in items]
        self.assertNotIn("job3224", ids)
        self.assertIn("job4242", ids)
        self.assertNotIn("gotmikedaniels", json.dumps(items).lower())
        self.assertNotIn("mike daniels", json.dumps(items).lower())

    def test_unknown_shop_job_still_queued(self):
        job = _job(property={"address": {"city": ""}})
        items = build_queue([job], decisions={"photos": {}})
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["shop"], "ramona")
        self.assertEqual(items[0]["city"], "Ramona area")

    def test_keep_is_eligible_reject_and_pending_are_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decisions.json"
            path.write_text(json.dumps({"version": 1, "photos": {}}))
            key = photo_id("job4242", 1)
            self.assertFalse(is_publish_eligible(key, {"photos": {}}))
            record_decision(key, "keep", caption="Pump work in Ramona.", shop="ramona", path=path)
            data = json.loads(path.read_text())
            self.assertTrue(is_publish_eligible(key, data))
            record_decision(key, "reject", path=path)
            data = json.loads(path.read_text())
            self.assertFalse(is_publish_eligible(key, data))
            self.assertEqual(data["photos"][key]["decision"], "reject")

    def test_kept_indexes_and_handoff_omit_rejects(self):
        decisions = {
            "photos": {
                "job4242:1": {
                    "decision": "keep",
                    "shop": "ramona",
                    "caption": "Pump work in Ramona.",
                    "jobId": "job4242",
                },
                "job4242:2": {
                    "decision": "reject",
                    "shop": "ramona",
                    "caption": "Nope.",
                    "jobId": "job4242",
                },
            }
        }
        self.assertEqual(kept_photo_indexes("job4242", decisions), {1})
        handoff = eligible_handoff(decisions, queue=[])
        self.assertEqual([h["id"] for h in handoff], ["job4242:1"])
        self.assertNotIn("760", json.dumps(handoff))


if __name__ == "__main__":
    unittest.main()
