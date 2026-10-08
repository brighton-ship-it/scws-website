#!/usr/bin/env python3
"""City-hub schema: real shops only, Service everywhere else."""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from far_city_factory_lib import html_is_noindex
from hub_schema_lib import (
    NON_CITY_SLUGS,
    apply_hub_schema,
    hub_schema,
    replace_hub_schema,
)

ROOT = Path(__file__).resolve().parents[1]
JSONLD_RE = re.compile(
    r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>\s*(.*?)\s*</script>",
    re.I | re.S,
)
CANONICAL_RE = re.compile(
    r"""<link\b[^>]*rel=["']canonical["'][^>]*href=["']([^"']+)["']"""
    r"""|<link\b[^>]*href=["']([^"']+)["'][^>]*rel=["']canonical["']""",
    re.I,
)
FAKE_CITY_BUSINESS = re.compile(
    r"Southern California Well Service\s*-\s*[A-Z]"
)


def _blocks(text: str) -> list[dict]:
    out = []
    for match in JSONLD_RE.finditer(text):
        out.append(json.loads(match.group(1)))
    return out


def _business(text: str) -> dict:
    for block in _blocks(text):
        kind = block.get("@type")
        if kind in {"LocalBusiness", "Service"}:
            return block
    raise AssertionError("no hub business schema")


class HubSchemaUnitTests(unittest.TestCase):
    def test_ramona_and_anza_are_real_shops(self):
        ramona = hub_schema("ramona")
        anza = hub_schema("anza")
        self.assertEqual(ramona["@type"], "LocalBusiness")
        self.assertEqual(anza["@type"], "LocalBusiness")
        self.assertEqual(ramona["address"]["streetAddress"], "1077 Main St Unit B")
        self.assertEqual(ramona["address"]["addressLocality"], "Ramona")
        self.assertEqual(ramona["address"]["postalCode"], "92065")
        self.assertIn("57174 CA-371", anza["address"]["streetAddress"])
        self.assertEqual(anza["address"]["addressLocality"], "Anza")
        self.assertEqual(anza["address"]["postalCode"], "92539")
        self.assertEqual(ramona["hasCredential"]["identifier"], "1086994")
        self.assertEqual(anza["hasCredential"]["identifier"], "1086994")
        self.assertNotIn(" - ", ramona["name"])
        self.assertNotIn(" - ", anza["name"])

    def test_other_hubs_are_service_with_serving_shop(self):
        hemet = hub_schema("hemet")
        cajon = hub_schema("el-cajon")
        dhs = hub_schema("desert-hot-springs")
        mountain = hub_schema("mountain-center")
        for block, city, shop_city in (
            (hemet, "Hemet", "Anza"),
            (cajon, "El Cajon", "Ramona"),
            (dhs, "Desert Hot Springs", "Anza"),
            (mountain, "Mountain Center", "Anza"),
        ):
            self.assertEqual(block["@type"], "Service", city)
            self.assertEqual(block["areaServed"]["name"], city)
            self.assertEqual(block["provider"]["@type"], "LocalBusiness")
            self.assertEqual(block["provider"]["address"]["addressLocality"], shop_city)
            self.assertNotRegex(block["provider"]["name"], FAKE_CITY_BUSINESS)

    def test_replace_is_idempotent_and_parses(self):
        src = """<head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Southern California Well Service - Hemet",
  "telephone": "(760) 440-8520",
  "areaServed": "Hemet, CA"
}
</script>
</head>"""
        once = replace_hub_schema(src, "hemet")
        twice = replace_hub_schema(once, "hemet")
        self.assertEqual(once, twice)
        block = _business(once)
        self.assertEqual(block["@type"], "Service")
        self.assertEqual(block["areaServed"]["name"], "Hemet")
        self.assertNotIn("Southern California Well Service - Hemet", once)

    def test_generator_template_uses_shop_schema(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "generate_service_pages",
            ROOT / "scripts" / "generate-service-pages.py",
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        src = (ROOT / "scripts" / "generate-service-pages.py").read_text(encoding="utf-8")
        self.assertNotIn("Southern California Well Service - {city_name}", src)
        with tempfile.TemporaryDirectory() as tmp:
            module.generate_city_index("hemet", Path(tmp))
            html = (Path(tmp) / "hemet" / "index.html").read_text(encoding="utf-8")
        block = _business(html)
        self.assertEqual(block["@type"], "Service")
        self.assertEqual(block["provider"]["address"]["addressLocality"], "Anza")
        self.assertIn('rel="canonical" href="https://scwellservice.com/services/hemet/"', html)


class LiveHubSchemaTests(unittest.TestCase):
    def test_indexable_hubs_match_shop_rules(self):
        apply_hub_schema()
        services = ROOT / "services"
        seen = 0
        for city_dir in sorted(p for p in services.iterdir() if p.is_dir()):
            slug = city_dir.name
            if slug in NON_CITY_SLUGS:
                continue
            path = city_dir / "index.html"
            if not path.is_file() or html_is_noindex(path):
                continue
            text = path.read_text(encoding="utf-8")
            for match in JSONLD_RE.finditer(text):
                json.loads(match.group(1))
            block = _business(text)
            self.assertIsNone(FAKE_CITY_BUSINESS.search(json.dumps(block)), slug)
            if slug in {"ramona", "anza"}:
                self.assertEqual(block["@type"], "LocalBusiness", slug)
                self.assertIn(slug.title() if slug != "anza" else "Anza", block["address"]["addressLocality"])
                self.assertTrue(block["address"]["streetAddress"])
            else:
                self.assertEqual(block["@type"], "Service", slug)
                self.assertEqual(block["areaServed"]["@type"], "City")
                self.assertIn(
                    block["provider"]["address"]["addressLocality"],
                    {"Ramona", "Anza"},
                    slug,
                )
            canon = CANONICAL_RE.search(text)
            self.assertIsNotNone(canon, slug)
            href = (canon.group(1) or canon.group(2)).rstrip("/")
            self.assertEqual(href, f"https://scwellservice.com/services/{slug}", slug)
            seen += 1
        self.assertGreaterEqual(seen, 45)

    def test_noindex_coachella_hubs_stay_noindex(self):
        for slug in (
            "rancho-mirage",
            "palm-desert",
            "la-quinta",
            "indio",
            "cathedral-city",
            "palm-springs",
        ):
            path = ROOT / "services" / slug / "index.html"
            self.assertTrue(path.is_file(), slug)
            self.assertTrue(html_is_noindex(path), slug)

    def test_second_apply_is_a_no_op(self):
        self.assertEqual(apply_hub_schema(), [])


if __name__ == "__main__":
    unittest.main()
