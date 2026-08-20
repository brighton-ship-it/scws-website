#!/usr/bin/env python3
"""Unit tests for the Jobber → Recent Work publisher (no network, no secrets)."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recent_work_lib import (
    PAGE_SIZE,
    build_project,
    card_html,
    categorize_job,
    collect_attachments,
    is_public_safe_title,
    job_h1,
    jsonld_items,
    merge_projects,
    paginate_projects,
    public_location,
    sanitize_public_text,
    slugify,
    trim_meta_description,
    unique_slug,
)

_cli_path = Path(__file__).resolve().parent / "publish-recent-work-from-jobber.py"
_spec = importlib.util.spec_from_file_location("publish_recent_work_cli", _cli_path)
_cli = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_cli)


class SanitizeTests(unittest.TestCase):
    def test_strips_price_address_url_and_phone(self):
        raw = (
            "Replaced pump at 123 Main Street for $1,240. "
            "See https://secure.getjobber.com/jobs/1 — call 760-555-0100."
        )
        out = sanitize_public_text(raw)
        self.assertNotIn("$", out)
        self.assertNotIn("123 Main", out)
        self.assertNotIn("jobber", out.lower())
        self.assertNotIn("760-555-0100", out)
        self.assertIn("Replaced pump", out)

    def test_city_only_location(self):
        self.assertEqual(public_location("Ramona"), "Ramona")
        self.assertEqual(public_location("Ramona, CA 92065"), "Ramona")
        self.assertEqual(public_location("123 Oak Ln"), "")
        self.assertEqual(public_location(""), "")

    def test_public_safe_title(self):
        self.assertTrue(is_public_safe_title("Pull & replace pump and motor"))
        self.assertFalse(is_public_safe_title("Smith residence"))
        self.assertFalse(is_public_safe_title("123 Oak Lane pump"))
        self.assertFalse(is_public_safe_title("Quote $2400"))

    def test_category(self):
        self.assertEqual(categorize_job("New well drilling"), "drilling")
        self.assertEqual(categorize_job("Pressure tank replacement"), "tank")
        self.assertEqual(categorize_job("Pumptec Plus controller"), "pump")
        self.assertEqual(categorize_job("Water treatment system"), "water-quality")


class ProjectBuildTests(unittest.TestCase):
    def test_build_project_from_jobber_shape(self):
        job = {
            "id": "abc",
            "jobNumber": 4242,
            "title": "Pull & replace pump and motor",
            "completedAt": "2026-08-18T20:00:00Z",
            "startAt": "2026-08-18T15:00:00Z",
            "instructions": "Installed a new Goulds pump. System restored.",
            "property": {"address": {"city": "Lake Elsinore"}},
        }
        project = build_project(job, ["job4242_1.jpg"], taken_slugs=[])
        self.assertIsNotNone(project)
        assert project is not None
        self.assertEqual(project["id"], "job4242")
        self.assertEqual(project["location"], "Lake Elsinore")
        self.assertEqual(project["category"], "pump")
        self.assertNotIn("$", project["summary"])
        self.assertTrue(project["slug"].startswith("lake-elsinore"))
        self.assertEqual(project["photos"][0]["file"], "job4242_1.jpg")

    def test_rejects_missing_city_or_photos_or_unsafe_title(self):
        base = {
            "jobNumber": 1,
            "title": "Pull & replace pump and motor",
            "completedAt": "2026-08-18T20:00:00Z",
            "property": {"address": {"city": "Ramona"}},
        }
        self.assertIsNone(build_project(base, [], taken_slugs=[]))
        no_city = dict(base, property={"address": {"city": ""}})
        self.assertIsNone(build_project(no_city, ["job1_1.jpg"], taken_slugs=[]))
        bad_title = dict(base, title="Customer follow-up")
        self.assertIsNone(build_project(bad_title, ["job1_1.jpg"], taken_slugs=[]))

    def test_merge_keeps_existing_copy(self):
        existing = [
            {
                "id": "job3049",
                "slug": "torrey-hill-pump-replacement",
                "title": "Well pump & motor replacement",
                "location": "San Diego County (Torrey Hill area)",
                "date": "2026-08-20",
                "summary": "Curated copy",
                "photos": [],
            }
        ]
        incoming = [
            {
                "id": "job3049",
                "title": "SHOULD NOT REPLACE",
                "date": "2026-08-21",
                "summary": "overwrite",
                "photos": [],
            },
            {
                "id": "job9999",
                "title": "New pump install",
                "location": "Anza",
                "date": "2026-08-22",
                "summary": "New",
                "photos": [],
            },
        ]
        merged = merge_projects(existing, incoming)
        ids = [p["id"] for p in merged]
        self.assertEqual(ids[0], "job9999")
        kept = next(p for p in merged if p["id"] == "job3049")
        self.assertEqual(kept["summary"], "Curated copy")
        self.assertEqual(kept["title"], "Well pump & motor replacement")

    def test_unique_slug(self):
        self.assertEqual(unique_slug("ramona-pump", ["ramona-pump"]), "ramona-pump-2")
        self.assertEqual(slugify("Well pump & motor"), "well-pump-and-motor")


class AttachmentTests(unittest.TestCase):
    def test_collects_images_skips_pdfs(self):
        job = {
            "noteAttachments": {
                "nodes": [
                    {
                        "fileName": "wellhead.jpg",
                        "url": "https://files.example/a.jpg",
                        "contentType": "image/jpeg",
                    },
                    {
                        "fileName": "contract.pdf",
                        "url": "https://files.example/c.pdf",
                        "contentType": "application/pdf",
                    },
                    {
                        "fileName": "invoice-scan.png",
                        "url": "https://files.example/i.png",
                        "contentType": "image/png",
                    },
                ]
            }
        }
        files = collect_attachments(job)
        self.assertEqual([f["name"] for f in files], ["wellhead.jpg"])


class HeadingMetaTests(unittest.TestCase):
    def test_h1_includes_city(self):
        self.assertEqual(
            job_h1({"title": "Well diagnostic", "location": "Anza"}),
            "Well diagnostic in Anza",
        )
        self.assertEqual(
            job_h1({"title": "Well diagnostic in Anza", "location": "Anza"}),
            "Well diagnostic in Anza",
        )

    def test_meta_trims_on_word_not_inch_mark(self):
        long = (
            "Repaired a hole in the pressure-tank piping and replaced a rotting "
            "union with stainless 1-1/4\" fittings plus extra words to force a "
            "cutoff somewhere after the inch mark and more filler text here."
        )
        out = trim_meta_description(long, limit=80)
        self.assertLessEqual(len(out), 81)
        self.assertNotIn('"', out)
        self.assertTrue(out.endswith("."))
        self.assertNotEqual(out[-2], "\"")


class HtmlTests(unittest.TestCase):
    def test_card_matches_existing_structure(self):
        project = {
            "id": "job4242",
            "slug": "lake-elsinore-pump",
            "title": "Pull & replace pump",
            "location": "Lake Elsinore",
            "date": "2026-08-18",
            "dateLabel": "August 18, 2026",
            "category": "pump",
            "categoryLabel": "Pump Service",
            "summary": "System restored.",
            "photos": [{"file": "job4242_1.jpg", "alt": "Pump work in Lake Elsinore"}],
        }
        markup = card_html(project)
        self.assertIn('data-job="job4242"', markup)
        self.assertIn('data-static="1"', markup)
        self.assertIn("project-photos single", markup)
        self.assertIn("../images/recent-work/job4242_1.jpg", markup)
        self.assertIn("lake-elsinore-pump.html", markup)
        self.assertNotIn("760-219-5877", markup)
        self.assertNotIn("(760) 440-8520", markup)
        self.assertNotIn("jobber", markup.lower())
        items = jsonld_items([project])
        self.assertIn("numberOfItems", items)
        json.loads("{" + items + "}")

    def test_existing_live_projects_json_still_valid(self):
        path = Path(__file__).resolve().parents[1] / "recent-work" / "projects.json"
        data = json.loads(path.read_text())
        self.assertGreaterEqual(len(data["projects"]), 107)
        for project in data["projects"]:
            self.assertTrue(project["id"].startswith("job"))
            self.assertTrue(project["title"])
            self.assertTrue(project["location"])
            self.assertTrue(project["photos"])
            self.assertNotIn("jobber", project["title"].lower())
            self.assertNotIn("$", project["summary"])

    def test_index_markers_and_rewrite(self):
        import recent_work_lib
        from recent_work_lib import CARD_MARKERS, update_index_html

        index = Path(__file__).resolve().parents[1] / "recent-work" / "index.html"
        text = index.read_text()
        self.assertIn(CARD_MARKERS[0], text)
        self.assertIn(CARD_MARKERS[1], text)
        self.assertLessEqual(text.count('class="project-card"'), PAGE_SIZE)
        self.assertGreaterEqual(text.count('class="project-card"'), 1)
        self.assertIn("job3174", text)
        self.assertIn("7602195877", text)
        self.assertIn("(760) 440-8520", text)
        listing_text = "\n".join(
            p.read_text()
            for p in [index, *sorted((index.parent).glob("page-*.html"))]
        )
        for job_id in (
            "job3049",
            "job3174",
            "job3139",
            "job3141",
            "job3115",
            "job3145",
            "job3159",
            "job3134",
        ):
            self.assertIn(f'data-job="{job_id}"', listing_text)
        self.assertIn("San Diego County (Torrey Hill area)", listing_text)

        data = json.loads(
            (Path(__file__).resolve().parents[1] / "recent-work" / "projects.json").read_text()
        )
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "index.html"
            copy.write_text(text)
            original = recent_work_lib.INDEX_HTML
            recent_work_lib.INDEX_HTML = copy
            try:
                update_index_html(data["projects"])
            finally:
                recent_work_lib.INDEX_HTML = original
            rewritten = copy.read_text()
            pages = paginate_projects(data["projects"])
            self.assertLessEqual(rewritten.count('class="project-card"'), PAGE_SIZE)
            self.assertTrue((Path(tmp) / "page-2.html").exists())
            self.assertEqual(len(pages), 5)
        self.assertIn("7602195877", rewritten)
        self.assertIn("(760) 440-8520", rewritten)
        self.assertIn('data-job="job3174"', rewritten)


class DryRunCliTests(unittest.TestCase):
    def test_fixture_dry_run_exits_zero(self):
        fixture = {
            "jobs": [
                {
                    "jobNumber": 8888,
                    "title": "Pressure tank replacement",
                    "completedAt": "2026-08-19T18:00:00Z",
                    "instructions": "Installed a new 86-gallon tank. System tested good.",
                    "property": {"address": {"city": "Anza"}},
                    "noteAttachments": {
                        "nodes": [
                            {
                                "fileName": "tank.jpg",
                                "url": "https://example.com/tank.jpg",
                                "contentType": "image/jpeg",
                            }
                        ]
                    },
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            path.write_text(json.dumps(fixture))
            code = _cli.main(["--fixture", str(path), "--dry-run"])
        self.assertEqual(code, 0)

    def test_missing_secrets_exits_2(self):
        import os

        keys = (
            "JOBBER_ACCESS_TOKEN",
            "JOBBER_CLIENT_ID",
            "JOBBER_CLIENT_SECRET",
            "JOBBER_REFRESH_TOKEN",
        )
        saved = {key: os.environ.pop(key, None) for key in keys}
        try:
            self.assertEqual(_cli.main(["--days", "1", "--limit", "1"]), 2)
        finally:
            for key, value in saved.items():
                if value is not None:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
