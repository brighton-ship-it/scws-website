#!/usr/bin/env python3
"""Unit tests for the Jobber → Recent Work publisher (no network, no secrets)."""
from __future__ import annotations

import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from photo_webp import close_heading_gaps, demote_footer_headings
from recent_work_lib import (
    MIN_INDEXABLE_SUMMARY_WORDS,
    MONEY_PAGE_SLUGS,
    PAGE_SIZE,
    build_project,
    card_city_only,
    card_html,
    categorize_job,
    collect_attachments,
    is_public_safe_title,
    job_h1,
    job_is_indexable,
    jsonld_items,
    load_projects,
    merge_projects,
    money_page_card_html,
    money_page_section_html,
    money_page_specs,
    pick_money_page_projects,
    replace_recent_jobs_section,
    paginate_projects,
    projects_by_slugs,
    extract_project_facts,
    public_location,
    public_meta_descriptions,
    public_titles,
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

    def test_clean_title_drops_customer_words_and_keeps_service_calls(self):
        from recent_work_lib import clean_public_title

        self.assertEqual(clean_public_title("Service Call Please call with ETA"), "")
        self.assertEqual(clean_public_title("Site Visit Storage Tank"), "")
        self.assertEqual(
            clean_public_title("Pull pump at 400 ft ( no charge) 8:30 AM BS"),
            "Pull pump",
        )
        self.assertNotIn("His", clean_public_title("Set His Power Pole"))
        self.assertIn("Pump", clean_public_title("Replace Pump, Motor & Control – Job #3625"))
        self.assertNotIn("3625", clean_public_title("Replace Pump, Motor & Control – Job #3625"))

    def test_safeguards_stay(self):
        from recent_work_lib import SITEMAP_EXCLUDED_HUB_SLUGS
        from recent_work_render import TYPO_HUB_ALIASES

        self.assertIn("owonga", SITEMAP_EXCLUDED_HUB_SLUGS)
        self.assertIn("marietta", SITEMAP_EXCLUDED_HUB_SLUGS)
        self.assertEqual(TYPO_HUB_ALIASES["owonga"], "aguanga")
        self.assertEqual(TYPO_HUB_ALIASES["marietta"], "murrieta")

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
        site_visit = dict(base, title="Site Visit Storage Tank", jobNumber=3635)
        self.assertIsNone(build_project(site_visit, ["job3635_1.jpg"], taken_slugs=[]))
        generic = dict(base, title="Well service")
        self.assertIsNone(build_project(generic, ["job1_1.jpg"], taken_slugs=[]))

    def test_completed_at_uses_pacific_calendar_day(self):
        from recent_work_lib import format_date_label, parse_jobber_dt

        # job 3616 completed 2026-10-21 01:27 UTC, which is still October 20 in California.
        self.assertEqual(
            format_date_label(None, parse_jobber_dt("2026-10-21T01:27:11Z")),
            ("2026-10-20", "October 20, 2026"),
        )

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

    def test_paperwork_photo_is_not_a_card_image(self):
        from recent_work_lib import public_photos

        project = {
            "id": "job3149",
            "slug": "ramona-well-service",
            "title": "Well service",
            "location": "Ramona",
            "date": "2026-08-20",
            "dateLabel": "August 20, 2026",
            "category": "pump",
            "categoryLabel": "Pump Service",
            "summary": "Pump Service in Ramona on August 20, 2026. Job type: Well service.",
            "photos": [
                {"file": "job3149_1.jpg"},
                {"file": "job3149_2.jpg"},
                {"file": "job3149_3.jpg"},
            ],
        }
        self.assertEqual(
            [photo["file"] for photo in public_photos(project)],
            ["job3149_2.jpg"],
        )
        markup = card_html(project, image_prefix="/images/recent-work/")
        self.assertNotIn("job3149_1.jpg", markup)
        self.assertNotIn("job3149_3.jpg", markup)
        self.assertIn("job3149_2.jpg", markup)
        self.assertIn("project-photos single", markup)

        paper_only = dict(project, photos=[{"file": "job3149_1.jpg"}])
        fallback = card_html(paper_only)
        self.assertNotIn("job3149_1.jpg", fallback)
        self.assertIn("photo-fallback", fallback)
        self.assertIn("project-photos empty", fallback)
        self.assertNotIn("760-823-7963", markup)
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
        self.assertIn("7608237963", text)
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
            expected_pages = max(1, (len(data["projects"]) + PAGE_SIZE - 1) // PAGE_SIZE)
            self.assertEqual(len(pages), expected_pages)
            self.assertIn("7608237963", rewritten)
            self.assertIn("(760) 440-8520", rewritten)
            rewritten_listing = rewritten + "\n".join(
                page.read_text() for page in Path(tmp).glob("page-*.html")
            )
            self.assertIn('data-job="job3174"', rewritten_listing)
            self.assertIn('data-town=', rewritten)


class DryRunCliTests(unittest.TestCase):
    def test_fixture_dry_run_skips_unreviewed_field_photo(self):
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
            import photo_audit_lib

            original = photo_audit_lib.DECISIONS_PATH
            photo_audit_lib.DECISIONS_PATH = Path(tmp) / "decisions.json"
            photo_audit_lib.DECISIONS_PATH.write_text(json.dumps({"version": 1, "photos": {}}))
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    code = _cli.main(["--fixture", str(path), "--dry-run"])
            finally:
                photo_audit_lib.DECISIONS_PATH = original
        out = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("New publishable jobs: 0", out)
        self.assertIn("waiting for photo-audit keep", out)

    def test_fixture_dry_run_exits_zero_when_kept(self):
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
            import photo_audit_lib

            original = photo_audit_lib.DECISIONS_PATH
            photo_audit_lib.DECISIONS_PATH = Path(tmp) / "decisions.json"
            photo_audit_lib.DECISIONS_PATH.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "photos": {
                            "job8888:1": {
                                "decision": "keep",
                                "shop": "anza",
                                "caption": "Pressure tank replacement in Anza.",
                            }
                        },
                    }
                )
            )
            try:
                code = _cli.main(["--fixture", str(path), "--dry-run"])
            finally:
                photo_audit_lib.DECISIONS_PATH = original
        self.assertEqual(code, 0)

class MoneyPageCardTests(unittest.TestCase):
    def test_card_city_strips_street_parenthetical(self):
        self.assertEqual(card_city_only("Ramona (Cathedral Way area)"), "Ramona")
        self.assertEqual(card_city_only("Ramona, CA"), "Ramona")

    def test_curated_slugs_exist_with_photos(self):
        projects = load_projects()["projects"]
        for rel, slugs in MONEY_PAGE_SLUGS.items():
            hits = projects_by_slugs(projects, slugs)
            self.assertGreaterEqual(len(hits), 3, rel)
            self.assertLessEqual(len(hits), max(6, len(slugs)), rel)
            titles = [p["title"] for p in hits]
            dupes = sorted({title for title in titles if titles.count(title) > 1})
            if rel == "services/ramona/index.html":
                self.assertEqual(dupes, ["Well service"])
            else:
                self.assertEqual(dupes, [], rel)

    def test_ramona_hub_rebuild_keeps_restored_and_neighbor_cards(self):
        projects = load_projects()["projects"]
        spec = money_page_specs()["services/ramona/index.html"]
        hits = pick_money_page_projects(projects, spec)
        slugs = [p["slug"] for p in hits]
        self.assertEqual(
            slugs,
            [
                "ramona-pressure-switch-gauge-replacement",
                "ramona-control-panel-contactor-replacement",
                "ramona-two-well-system-evaluation",
                "ramona-pressure-switch-replacement",
                "el-cajon-well-contactor-replacement",
                "alpine-pull-and-replace-deep-set-pump",
                "ramona-well-service",
                "ramona-well-service-2",
            ],
        )

    def test_indexable_only_skips_noindex_jobs(self):
        projects = load_projects()["projects"]
        spec = {
            "city": "Hemet",
            "prefer": ["hemet-electrical-disconnect-replacement"],
            "indexable_only": True,
        }
        hits = pick_money_page_projects(projects, spec, limit=6)
        slugs = [p["slug"] for p in hits]
        self.assertNotIn("hemet-electrical-disconnect-replacement", slugs)
        self.assertIn("hemet-pressure-tank-plumbing-repair", slugs)
        self.assertGreaterEqual(len(hits), 3)
        open_spec = dict(spec)
        open_spec["indexable_only"] = False
        open_hits = pick_money_page_projects(projects, open_spec, limit=6)
        self.assertIn(
            "hemet-electrical-disconnect-replacement",
            [p["slug"] for p in open_hits],
        )

    def test_catalog_picker_fills_city_pages_without_frozen_slugs(self):
        projects = load_projects()["projects"]
        spec = money_page_specs()["services/valley-center/index.html"]
        hits = pick_money_page_projects(projects, spec)
        self.assertGreaterEqual(len(hits), 3)
        self.assertLessEqual(len(hits), 6)
        for project in hits:
            loc = (project.get("location") or "").lower()
            self.assertTrue(
                "valley center" in loc or "escondido" in loc or "pauma" in loc,
                project.get("location"),
            )

    def test_insert_before_footer_keeps_cta_tail(self):
        src = (
            "<main><p>body</p></main>\n"
            "<footer class=\"footer\">shop</footer>\n"
            "<div id=\"sticky-cta\"><a class=\"cta-call\" href=\"tel:+17604408520\">Call</a>"
            "<a class=\"cta-est\" href=\"/contact.html\">Estimate</a></div>\n"
        )
        project = {
            "slug": "ramona-pressure-switch-gauge-replacement",
            "title": "Pressure switch and gauge replacement",
            "location": "Ramona",
            "photos": [{"file": "job3175_1.jpg"}],
        }
        block = money_page_section_html([project], "Recent jobs", "Real photos.")
        out = replace_recent_jobs_section(src, block)
        self.assertIn('id="recent-jobs"', out)
        self.assertIn("<footer class=\"footer\">shop</footer>", out)
        self.assertIn("cta-call", out)
        self.assertIn("cta-est", out)
        self.assertTrue(out.endswith("</div>\n"))

    def test_card_html_has_no_pii(self):
        project = {
            "slug": "ramona-pressure-switch-gauge-replacement",
            "title": "Pressure switch and gauge replacement",
            "location": "Ramona (Hanson Lane area)",
            "photos": [{"file": "job3175_1.jpg", "alt": "New pressure switch and gauge installed in Ramona"}],
        }
        html_out = money_page_card_html(project)
        self.assertIn("recent-work-card", html_out)
        self.assertIn("/images/recent-work/job3175_1.jpg", html_out)
        self.assertIn("Ramona", html_out)
        self.assertIn('alt="Pressure switch and gauge replacement in Ramona"', html_out)
        self.assertNotIn("Hanson", html_out)
        self.assertNotIn("Lane", html_out)
        self.assertNotIn("$", html_out)

    def test_live_money_pages_have_photo_cards(self):
        root = Path(__file__).resolve().parents[1]
        projects = load_projects()["projects"]
        pii = re.compile(
            r"\b(Hanson|Cathedral Way|Highland Valley)\b|\$\d|\(\d{3}\)\s*\d{3}"
        )
        before = {rel: (root / rel).read_bytes() for rel in MONEY_PAGE_SLUGS}
        for rel, slugs in MONEY_PAGE_SLUGS.items():
            html_out = (root / rel).read_text(encoding="utf-8")
            self.assertIn('class="recent-work-card"', html_out)
            self.assertIn('id="recent-jobs"', html_out)
            cards = re.findall(r'class="recent-work-card"', html_out)
            self.assertGreaterEqual(len(cards), 3, rel)
            self.assertLessEqual(len(cards), max(6, len(slugs)), rel)
            section = html_out.split('id="recent-jobs"', 1)[1].split("</section>", 1)[0]
            self.assertIsNone(pii.search(section), rel)
            # A preferred slug with no public field photo is left off the card row.
            # Every curated slug that does have a photo has to stay on the page.
            photo_slugs = [p["slug"] for p in projects_by_slugs(projects, slugs)]
            for slug in photo_slugs:
                self.assertIn(f"/recent-work/{slug}.html", section, rel)
            self.assertIn("cta-call", html_out)
            self.assertIn("cta-est", html_out)
            self.assertNotIn("FLAG under 60%", html_out)
            self.assertNotIn("1059498", html_out)
        after = {rel: (root / rel).read_bytes() for rel in MONEY_PAGE_SLUGS}
        self.assertEqual(before, after)

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


class QualityGateTests(unittest.TestCase):
    def test_boilerplate_is_not_indexable(self):
        project = {
            "title": "Well service",
            "location": "Ramona",
            "summary": "Well service completed in Ramona.",
            "dateLabel": "August 21, 2026",
            "categoryLabel": "Pump Service",
            "id": "job1",
            "slug": "ramona-well-service",
        }
        self.assertFalse(job_is_indexable(project))
        self.assertEqual(extract_project_facts(project["summary"]), [])

    def test_real_note_is_indexable_and_facts_come_from_the_note(self):
        summary = (
            "Crew pulled a submersible pump set at 320 ft in a 354-ft well and "
            "installed a new 2 HP Goulds motor. Amp draw was 9.4 A."
        )
        project = {
            "title": "Pump replacement",
            "location": "Ramona",
            "summary": summary,
            "dateLabel": "August 20, 2026",
            "categoryLabel": "Pump Service",
            "id": "job2",
            "slug": "ramona-pump",
        }
        self.assertGreaterEqual(len(summary.split()), MIN_INDEXABLE_SUMMARY_WORDS)
        self.assertTrue(job_is_indexable(project))
        labels = dict(extract_project_facts(summary))
        self.assertEqual(labels["Pump setting"], "320 ft")
        self.assertEqual(labels["Well depth"], "354 ft")
        self.assertEqual(labels["Pump / motor"], "2 HP")
        self.assertIn("Goulds", labels["Equipment"])

    def test_titles_are_unique(self):
        projects = load_projects()["projects"]
        titles = public_titles(projects)
        descriptions = public_meta_descriptions(projects)
        self.assertEqual(len(titles), len(set(titles.values())))
        self.assertEqual(len(descriptions), len(set(descriptions.values())))
        indexable = [p for p in projects if job_is_indexable(p)]
        self.assertGreaterEqual(len(indexable), 80)
        self.assertLess(len(indexable), 200)
        thin = next(p for p in projects if p["slug"] == "ramona-well-service-99")
        self.assertFalse(job_is_indexable(thin))
        kept = next(p for p in projects if p["slug"] == "torrey-hill-pump-replacement")
        self.assertTrue(job_is_indexable(kept))
        self.assertIn("Torrey Hill", titles[kept["slug"]])
        self.assertIn("SCWS", titles[kept["slug"]])
        street = next(p for p in projects if "Hanson" in (p.get("location") or ""))
        self.assertNotIn("Hanson", titles[street["slug"]])
        self.assertIn("Ramona", titles[street["slug"]])
        thin_desc = descriptions[thin["slug"]]
        self.assertNotIn("field photos", thin_desc)
        self.assertIn("Ramona shop", thin_desc)
        self.assertNotIn("Hanson", descriptions[street["slug"]])
        page = Path(__file__).resolve().parents[1] / "recent-work" / "lakeside-pull-pump.html"
        html = page.read_text(encoding="utf-8")
        self.assertIn("<!-- JOB_DETAILS_START -->", html)
        self.assertIn("<h2>Project details</h2>", html)
        self.assertIn("1077 Main St, Unit B, Ramona, CA 92065", html)
        self.assertNotIn("with field photos", html)
        self.assertNotIn("463-0493", html)


class PhotoMarkupTests(unittest.TestCase):
    def test_pixel_size_and_picture_keep_the_jpeg(self):
        import recent_work_lib

        jpg = bytes.fromhex(
            "ffd8ffe000104a46494600010100000100010000ffdb004300100b0c0e0c0a100e0d0e1211101318281a181616183123251d283a333d3c3933383740485c4e404457453738506d51575f626768673e4d71797064785c656763ffdb0043011112121815182f1a1a2f634238426363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363ffc00011080004000803012200021101031101ffc4001f0000010501010101010100000000000000000102030405060708090a0bffc400b5100002010303020403050504040000017d01020300041105122131410613516107227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455565758595a636465666768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffc4001f0100030101010101010101010000000000000102030405060708090a0bffc400b51100020102040403040705040400010277000102031104052131061241510761711322328108144291a1b1c109233352f0156272d10a162434e125f11718191a262728292a35363738393a434445464748494a535455565758595a636465666768696a737475767778797a82838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae2e3e4e5e6e7e8e9eaf2f3f4f5f6f7f8f9faffda000c03010002110311003f00e468a28ad8c4ffd9"
        )
        webp = bytes.fromhex(
            "524946462c0000005745425056503820200000005001009d012a0400020003805a25004e80280000fef0e8e8b51254bc9fa23000"
        )
        self.assertEqual(recent_work_lib._jpeg_size(jpg), (8, 4))
        self.assertEqual(recent_work_lib._webp_size(webp), (4, 2))
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "pump.jpg").write_bytes(jpg)
            (folder / "pump.webp").write_bytes(webp)
            (folder / "pump-480.webp").write_bytes(webp)
            original = recent_work_lib.PHOTO_DIR
            recent_work_lib.PHOTO_DIR = folder
            try:
                hero = recent_work_lib.responsive_photo_html(
                    "pump.jpg", "Pull pump", prefix="/images/recent-work/", lazy=False, sizes="100vw"
                )
                thumb = recent_work_lib.responsive_photo_html(
                    "pump.jpg", "Pull pump", prefix="/images/recent-work/", lazy=True, sizes="140px"
                )
            finally:
                recent_work_lib.PHOTO_DIR = original
        self.assertIn("<picture>", hero)
        self.assertIn('src="/images/recent-work/pump.jpg"', hero)
        self.assertIn('type="image/webp"', hero)
        self.assertIn('width="8"', hero)
        self.assertIn('height="4"', hero)
        self.assertIn('fetchpriority="high"', hero)
        self.assertNotIn("loading=", hero)
        self.assertIn('loading="lazy"', thumb)
        self.assertNotIn("fetchpriority", thumb)

    def test_blog_footer_headings_do_not_skip(self):
        html = "<article><h2>Job</h2></article><footer><h4 class=\"x\">Ramona Office</h4><h4>Anza Office</h4></footer>"
        fixed = demote_footer_headings(html)
        self.assertIn("<h3 class=\"x\">Ramona Office</h3>", fixed)
        self.assertIn("<h3>Anza Office</h3>", fixed)
        self.assertNotIn("<h4", fixed)
        self.assertIn("<h2>Job</h2>", fixed)

    def test_heading_gaps_close_without_changing_text(self):
        html = "<h1>Guide</h1><h3>First section</h3><script><h4>ignore</h4></script><h2>Next</h2><h4>Detail</h4>"
        fixed = close_heading_gaps(html)
        self.assertIn("<h2>First section</h2>", fixed)
        self.assertIn("<h3>Detail</h3>", fixed)
        self.assertIn("<h2>Next</h2>", fixed)
        self.assertIn("<h4>ignore</h4>", fixed)


if __name__ == "__main__":
    unittest.main()
