#!/usr/bin/env python3
"""Add the county call-to-action to blog posts, plus service links on 20 guides.

The first 30 flagship posts already link to service pages. These 20 bring
that set to 50. Existing blog CTA boxes stay. call-tracking.js is not used.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from hub_schema_lib import city_display_name, html_is_noindex

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "blog"
PHONE_TEL = "tel:+17604408520"
PHONE = "(760) 440-8520"
BOOK_URL = (
    "https://clienthub.getjobber.com/hubs/7c569177-85d0-4bac-9c7f-e2afe6652ee1"
    "/public/requests/1604593/new"
)
CTA_START = "<!-- BLOG_COUNTY_CTA_START -->"
CTA_END = "<!-- BLOG_COUNTY_CTA_END -->"
LINK_START = "<!-- BLOG_SERVICE_LINK_START -->"
LINK_END = "<!-- BLOG_SERVICE_LINK_END -->"
CTA_RE = re.compile(re.escape(CTA_START) + r".*?" + re.escape(CTA_END), re.S)
LINK_RE = re.compile(re.escape(LINK_START) + r".*?" + re.escape(LINK_END), re.S)
BODY_RE = re.compile(r"</body>", re.I)

# Major indexable hubs used when a post names a town in that county.
SD_HUBS = (
    "ramona",
    "escondido",
    "poway",
    "alpine",
    "lakeside",
    "fallbrook",
    "valley-center",
    "el-cajon",
    "jamul",
    "julian",
)
RIV_HUBS = (
    "temecula",
    "murrieta",
    "menifee",
    "hemet",
    "anza",
    "perris",
    "wildomar",
    "lake-elsinore",
    "san-jacinto",
    "beaumont",
)
GENERIC_HUBS = ("ramona", "escondido", "temecula", "murrieta")

# Posts that did not get a service link in the flagship batch.
SERVICE_LINKS = {
    "cost-of-well-installation.html": (
        "What that price covers is the work on our "
        '<a href="/pages/services/well-drilling.html">well drilling</a> page, including '
        '<a href="/services/ramona/well-drilling.html">drilling in Ramona</a> and '
        '<a href="/services/temecula/well-drilling.html">drilling in Temecula</a>.'
    ),
    "submersible-pump-cost-installed.html": (
        "Installed submersible pumps are the work on our "
        '<a href="/pages/services/pump-repair.html">pump repair and replacement</a> page, including '
        '<a href="/services/ramona/well-pump-repair.html">pump repair in Ramona</a> and '
        '<a href="/services/temecula/well-pump-repair.html">pump repair in Temecula</a>.'
    ),
    "well-pump-replacement-cost-guide.html": (
        "Replacement is scheduled from our "
        '<a href="/pages/services/pump-repair.html">pump repair and replacement</a> page, including '
        '<a href="/services/ramona/well-pump-repair.html">pump repair in Ramona</a> and '
        '<a href="/services/murrieta/well-pump-repair.html">pump repair in Murrieta</a>.'
    ),
    "well-pump-replacement-cost-statistics.html": (
        "Those replacement jobs are the same work listed on our "
        '<a href="/pages/services/pump-repair.html">pump repair and replacement</a> page.'
    ),
    "emergency-well-service.html": (
        "A no-water call is handled on our "
        '<a href="/pages/services/emergency-well-service.html">emergency well service</a> page, including '
        '<a href="/services/ramona/emergency-well-service.html">emergency service in Ramona</a> and '
        '<a href="/services/temecula/emergency-well-service.html">emergency service in Temecula</a>.'
    ),
    "24-hour-well-service.html": (
        "After-hours no-water calls go through our "
        '<a href="/pages/services/emergency-well-service.html">emergency well service</a> page.'
    ),
    "24-hour-emergency-well-service.html": (
        "The emergency crew is the service on our "
        '<a href="/pages/services/emergency-well-service.html">emergency well service</a> page, including '
        '<a href="/services/anza/emergency-well-service.html">emergency service in Anza</a>.'
    ),
    "no-water-emergency.html": (
        "If the house has no water, start with our "
        '<a href="/pages/services/emergency-well-service.html">emergency well service</a> page and the '
        '<a href="/pages/services/pump-repair.html">pump repair</a> page.'
    ),
    "urgent-well-pump-repair.html": (
        "An urgent pump failure is the work on our "
        '<a href="/pages/services/pump-repair.html">pump repair</a> page and our '
        '<a href="/pages/services/emergency-well-service.html">emergency well service</a> page.'
    ),
    "how-to-choose-well-pump.html": (
        "Choosing the pump is part of the work on our "
        '<a href="/pages/services/pump-repair.html">pump repair and replacement</a> page, including '
        '<a href="/pages/services/pump-installation.html">pump installation</a>.'
    ),
    "pressure-tank-service.html": (
        "Tank replacement and precharge checks are on our "
        '<a href="/pages/services/pressure-tanks.html">pressure tank</a> page, including '
        '<a href="/services/ramona/pressure-tank.html">pressure tanks in Ramona</a> and '
        '<a href="/services/temecula/pressure-tank.html">pressure tanks in Temecula</a>.'
    ),
    "well-abandonment-service.html": (
        "Abandonment permits and the county rules we follow are on our "
        '<a href="/pages/services/well-destruction.html">well destruction</a> page.'
    ),
    "deep-water-well-drilling-cost.html": (
        "Deep wells are drilled from our "
        '<a href="/pages/services/well-drilling.html">well drilling</a> page, including '
        '<a href="/services/ramona/well-drilling.html">drilling in Ramona</a> and '
        '<a href="/services/julian/well-drilling.html">drilling in Julian</a>.'
    ),
    "water-treatment-system-cost-statistics.html": (
        "Filters and treatment equipment are the work on our "
        '<a href="/water-treatment.html">water treatment</a> page and our '
        '<a href="/pages/services/water-testing.html">water testing</a> page.'
    ),
    "iron-bacteria-toilet-tank.html": (
        "A lab sample is the service on our "
        '<a href="/pages/services/water-testing.html">water testing</a> page. Treatment equipment is on our '
        '<a href="/water-treatment.html">water treatment</a> page.'
    ),
    "hot-water-smells-like-rotten-eggs.html": (
        "Odor complaints start with a sample. That is our "
        '<a href="/pages/services/water-testing.html">water testing</a> page.'
    ),
    "well-inspection-costs-california.html": (
        "A sale or a video look is the work on our "
        '<a href="/pages/services/well-inspection.html">well inspection</a> page, including '
        '<a href="/services/ramona/well-inspection.html">inspections in Ramona</a> and '
        '<a href="/services/temecula/well-inspection.html">inspections in Temecula</a>.'
    ),
    "solar-well-pump-adoption-statistics.html": (
        "Solar pumping gear is the service on our "
        '<a href="/pages/services/solar-well-pumps.html">solar well pumps</a> page.'
    ),
    "preventive-maintenance-extends-well-life.html": (
        "A scheduled visit is the work on our "
        '<a href="/pages/services/maintenance.html">maintenance</a> page.'
    ),
    "well-pump-running-constantly.html": (
        "A pump that will not shut off is diagnosed from our "
        '<a href="/pages/services/pump-repair.html">pump repair</a> page and our '
        '<a href="/pages/services/pressure-tanks.html">pressure tank</a> page.'
    ),
}


def _hyperlocal() -> dict:
    import json

    return json.loads((ROOT / "scripts" / "city-hyperlocal-data.json").read_text(encoding="utf-8"))


def indexable_hubs() -> list[str]:
    found = []
    for path in sorted((ROOT / "services").iterdir()):
        index = path / "index.html"
        if not index.is_file():
            continue
        if html_is_noindex(index.read_text(encoding="utf-8")):
            continue
        found.append(path.name)
    return found


def town_from_filename(name: str, slugs: list[str]) -> str | None:
    stem = Path(name).stem.lower()
    stem = re.sub(r" \(\d+\)$", "", stem)
    for slug in sorted(slugs, key=len, reverse=True):
        if stem == slug or stem.endswith("-" + slug):
            return slug
    return None


def hub_links(name: str, hubs: set[str], hyper: dict) -> list[tuple[str, str]]:
    town = town_from_filename(name, list(hubs))
    county = (hyper.get(town) or {}).get("county") if town else None
    pool = SD_HUBS if county == "San Diego" else RIV_HUBS if county == "Riverside" else ()
    chosen: list[str] = []
    if town and town in hubs:
        chosen.append(town)
    for slug in pool:
        if slug in hubs and slug not in chosen:
            chosen.append(slug)
        if len(chosen) >= 3:
            break
    if not chosen:
        chosen = [slug for slug in GENERIC_HUBS if slug in hubs]
    return [(slug, city_display_name(slug)) for slug in chosen]


def cta_block(links: list[tuple[str, str]]) -> str:
    anchors = ", ".join(
        f'<a href="/services/{html.escape(slug)}/" style="color:#fff;">{html.escape(label)}</a>'
        for slug, label in links
    )
    return (
        f"{CTA_START}\n"
        '<aside id="need-a-pro" class="blog-county-cta" '
        'style="max-width:720px;margin:2rem auto;padding:1.25rem 1.5rem;background:#1a365d;'
        'color:#fff;border-radius:12px;line-height:1.5;">\n'
        '<h2 style="color:#fff;font-size:1.35rem;margin:0 0 0.5rem;">'
        "Need a pro in San Diego or Riverside County?</h2>\n"
        f'<p style="margin:0.5rem 0;">Call <a href="{PHONE_TEL}" style="color:#fff;font-weight:700;">'
        f"{PHONE}</a> or book a visit online.</p>\n"
        f'<p style="margin:0.75rem 0;"><a class="scws-book-online" href="{BOOK_URL}" '
        'style="display:inline-block;background:#ed8936;color:#fff;font-weight:700;'
        'padding:0.65rem 1rem;border-radius:8px;text-decoration:none;">Book online</a></p>\n'
        f'<p style="margin:0.5rem 0;">Town pages: {anchors}.</p>\n'
        "</aside>\n"
        '<script src="/js/book-online.js" defer></script>\n'
        f"{CTA_END}"
    )


def link_block(sentence: str) -> str:
    return f"{LINK_START}\n<p>{sentence}</p>\n{LINK_END}"


def _replace_or_insert(text: str, pattern: re.Pattern[str], block: str, before: str | None) -> str | None:
    if pattern.search(text):
        return pattern.sub(block, text, count=1)
    if before and before in text:
        return text.replace(before, block + "\n" + before, 1)
    match = None
    for match in BODY_RE.finditer(text):
        pass
    if match is None:
        return None
    return text[: match.start()] + block + "\n" + text[match.start() :]


def apply_blog_cta() -> dict[str, int]:
    hubs = set(indexable_hubs())
    hyper = _hyperlocal()
    changed = 0
    unchanged = 0
    skipped = 0
    linked = 0
    for path in sorted(BLOG.glob("*.html")):
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            skipped += 1
            continue
        if BODY_RE.search(original) is None:
            skipped += 1
            continue
        links = hub_links(path.name, hubs, hyper)
        block = cta_block(links)
        updated = _replace_or_insert(original, CTA_RE, block, None)
        if updated is None:
            skipped += 1
            continue
        sentence = SERVICE_LINKS.get(path.name)
        if sentence:
            link = link_block(sentence)
            updated = _replace_or_insert(updated, LINK_RE, link, CTA_START)
            if updated is None:
                skipped += 1
                continue
            linked += 1
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
        else:
            unchanged += 1
    return {"changed": changed, "unchanged": unchanged, "skipped": skipped, "service_links": linked}


def check_service_targets() -> None:
    missing = []
    for sentence in SERVICE_LINKS.values():
        for href in re.findall(r'href="([^"]+)"', sentence):
            if not (ROOT / href.lstrip("/")).is_file():
                missing.append(href)
    if missing:
        raise SystemExit("missing service targets: " + ", ".join(missing))


if __name__ == "__main__":
    import json

    check_service_targets()
    print(json.dumps(apply_blog_cta()))
