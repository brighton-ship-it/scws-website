#!/usr/bin/env python3
"""One-shot approved SEO do-now helpers: NAP, sitemaps, city/service links, copy."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recent_work_lib import (
    projects_for_city,
    projects_for_service,
)

ROOT = Path(__file__).resolve().parents[1]
ANZA_LINE = "57174 CA-371 (US Hwy 79), Anza, CA 92539"
ANZA_STREET = "57174 CA-371 (US Hwy 79)"
TODAY = date.today().isoformat()
MONEY_URLS = [
    ("https://scwellservice.com/locations/", "0.8"),
    ("https://scwellservice.com/pages/services/maintenance.html", "0.9"),
    ("https://scwellservice.com/pages/services/diagnostics.html", "0.8"),
    ("https://scwellservice.com/pages/services/controls.html", "0.8"),
    ("https://scwellservice.com/pages/services/water-testing.html", "0.8"),
    ("https://scwellservice.com/pages/locations/san-diego.html", "0.8"),
]
CITY_PAGES = [
    ("ramona", "Ramona", ROOT / "services" / "ramona" / "index.html"),
    ("anza", "Anza", ROOT / "services" / "anza" / "index.html"),
    ("valley-center", "Valley Center", ROOT / "services" / "valley-center" / "index.html"),
    ("aguanga", "Aguanga", ROOT / "services" / "aguanga" / "index.html"),
    ("temecula", "Temecula", ROOT / "services" / "temecula" / "index.html"),
]
SERVICE_PAGES = [
    ("pump-repair", "pump repair", ROOT / "pages" / "services" / "pump-repair.html"),
    ("emergency-well-service", "emergency well service", ROOT / "pages" / "services" / "emergency-well-service.html"),
    ("well-drilling", "well drilling", ROOT / "pages" / "services" / "well-drilling.html"),
    ("maintenance", "maintenance", ROOT / "pages" / "services" / "maintenance.html"),
]
SKIP_NAP_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".svg",
    ".pdf",
    ".woff",
    ".woff2",
    ".mp4",
    ".json",
}


def load_projects() -> list[dict]:
    return json.loads((ROOT / "recent-work" / "projects.json").read_text())["projects"]


def lock_anza_nap() -> int:
    changed = 0
    text_exts = {".html", ".js", ".xml", ".txt", ".md"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_exts:
            continue
        if any(part in {".git", "node_modules"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        original = text
        # Already-canonical street should not be doubled.
        text = text.replace("57174 CA-371 (US Hwy 79) (US Hwy 79)", ANZA_STREET)
        replacements = [
            ("57174 US Highway 79, Anza, CA 92539", ANZA_LINE),
            ("57174 US Hwy 79, Anza, CA 92539", ANZA_LINE),
            ("57174 Highway 79, Anza, CA 92539", ANZA_LINE),
            ("57174 CA-371, Anza, CA 92539", ANZA_LINE),
            ('"streetAddress": "57174 CA-371"', f'"streetAddress": "{ANZA_STREET}"'),
            ("57174 US Highway 79", ANZA_STREET),
            ("57174 US Hwy 79", ANZA_STREET),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        text = text.replace("57174 CA-371 (US Hwy 79) (US Hwy 79)", ANZA_STREET)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1
    return changed


def jobs_list_html(projects: list[dict], heading: str) -> str:
    items = []
    for project in projects:
        href = f"/recent-work/{project['slug']}.html"
        label = f"{project['title']} in {project['location']}"
        items.append(f'  <li><a href="{href}">{label}</a></li>')
    return (
        f'<section class="recent-jobs-links" id="recent-jobs" style="margin:2rem 0;padding:1.5rem;background:#f8fafc;border-radius:12px;">\n'
        f"  <h2>{heading}</h2>\n"
        f"  <ul>\n" + "\n".join(items) + "\n  </ul>\n"
        f'  <p><a href="/recent-work/">See all recent work →</a></p>\n'
        f"</section>\n"
    )


def insert_before_footer(path: Path, block: str, marker: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return False
    match = re.search(r"<footer\b", text, re.I)
    if not match:
        return False
    path.write_text(text[: match.start()] + block + text[match.start()], encoding="utf-8")
    return True


def add_city_and_service_links(projects: list[dict]) -> None:
    for slug, city, path in CITY_PAGES:
        hits = projects_for_city(projects, city, limit=6)
        if not hits:
            print(f"no jobs for {city}")
            continue
        block = jobs_list_html(hits, f"Recent jobs in {city}")
        if insert_before_footer(path, block, 'id="recent-jobs"'):
            print(f"added city jobs on {path.relative_to(ROOT)}")
        else:
            print(f"skipped city jobs on {path.relative_to(ROOT)}")
    for key, label, path in SERVICE_PAGES:
        hits = projects_for_service(projects, key, limit=6)
        if not hits:
            print(f"no jobs for {key}")
            continue
        block = jobs_list_html(hits, f"See real {label} jobs")
        if insert_before_footer(path, block, 'id="recent-jobs"'):
            print(f"added service jobs on {path.relative_to(ROOT)}")
        else:
            print(f"skipped service jobs on {path.relative_to(ROOT)}")


def add_money_urls_to_sitemap() -> None:
    path = ROOT / "sitemap-pages.xml"
    xml = path.read_text(encoding="utf-8")
    existing = set(re.findall(r"<loc>([^<]+)</loc>", xml))
    additions = []
    for url, priority in MONEY_URLS:
        local = ROOT / url.replace("https://scwellservice.com/", "")
        if url.endswith("/"):
            local = ROOT / url.replace("https://scwellservice.com/", "") / "index.html"
        if not local.exists():
            print(f"skip missing money url {url}")
            continue
        if url in existing:
            continue
        additions.append(
            f"  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod><priority>{priority}</priority></url>\n"
        )
    if additions:
        xml = xml.replace("</urlset>", "".join(additions) + "</urlset>")
        path.write_text(xml, encoding="utf-8")
        print(f"added {len(additions)} money URLs to sitemap-pages.xml")
    else:
        print("sitemap-pages.xml already has money URLs")


def html_is_noindex(url: str) -> bool:
    rel = url.replace("https://scwellservice.com/", "")
    candidates = [
        ROOT / rel,
        ROOT / f"{rel}.html",
        ROOT / rel / "index.html",
    ]
    if rel.endswith("/"):
        candidates.append(ROOT / rel[:-1] / "index.html")
    for path in candidates:
        if path.is_file():
            head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
            return bool(re.search(r'name=["\']robots["\'][^>]*noindex|content=["\']noindex', head, re.I))
    return False


def clean_blog_sitemaps() -> None:
    old_re = re.compile(r"-OLD(?:</loc>|[\?#])")
    for path in sorted(ROOT.glob("sitemap-blog-*.xml")):
        xml = path.read_text(encoding="utf-8")
        urls = re.findall(r"  <url>.*?</url>\n?", xml, flags=re.S)
        kept = []
        dropped = []
        for block in urls:
            loc_m = re.search(r"<loc>([^<]+)</loc>", block)
            if not loc_m:
                kept.append(block)
                continue
            loc = loc_m.group(1)
            slug = loc.rsplit("/", 1)[-1]
            if slug.endswith("-OLD") or "-OLD" in slug:
                dropped.append(loc)
                continue
            if "well-permit-" in slug or html_is_noindex(loc):
                dropped.append(loc)
                continue
            kept.append(block)
        new_xml = re.sub(r"  <url>.*?</url>\n?", "", xml, flags=re.S)
        new_xml = new_xml.replace("</urlset>", "".join(kept) + "</urlset>")
        path.write_text(new_xml, encoding="utf-8")
        print(f"{path.name}: kept {len(kept)}, dropped {len(dropped)}")


def fix_company_age_copy() -> None:
    """About/meta and money-page company-age claims. Leave pump-lifespan copy alone."""
    targets = [
        ROOT / "pages" / "about.html",
        ROOT / "pages" / "locations" / "san-diego.html",
        ROOT / "pages" / "locations" / "cities" / "temecula.html",
        ROOT / "pages" / "locations" / "cities" / "san-diego.html",
        ROOT / "pages" / "locations" / "cities" / "jamul.html",
        ROOT / "pages" / "locations" / "cities" / "oceanside.html",
        ROOT / "pages" / "locations" / "cities" / "escondido.html",
        ROOT / "pages" / "locations" / "cities" / "menifee.html",
        ROOT / "pages" / "locations" / "cities" / "perris.html",
        ROOT / "pages" / "locations" / "cities" / "hemet.html",
        ROOT / "pages" / "locations" / "cities" / "poway.html",
        ROOT / "pages" / "locations" / "cities" / "banning.html",
        ROOT / "pages" / "locations" / "cities" / "bonsall.html",
        ROOT / "pages" / "locations" / "cities" / "carlsbad.html",
        ROOT / "pages" / "locations" / "cities" / "beaumont.html",
        ROOT / "pages" / "locations" / "cities" / "anza.html",
    ]
    repls = [
        (
            "Family-owned well service company serving San Diego, Riverside &amp; San Bernardino Counties for over 20 years.",
            "Family-owned well service company (founded 2020) serving San Diego, Riverside &amp; San Bernardino Counties. 60+ years family heritage.",
        ),
        (
            "Family-owned well service company serving San Diego, Riverside & San Bernardino Counties for over 20 years.",
            "Family-owned well service company (founded 2020) serving San Diego, Riverside & San Bernardino Counties. 60+ years family heritage.",
        ),
        (
            "has been serving San Diego County for over 20 years",
            "has served San Diego County since 2020, with 60+ years of family heritage in well work",
        ),
        (
            "We've drilled throughout Riverside County Wine Country for over 20 years",
            "We've drilled throughout Riverside County Wine Country since 2020, drawing on 60+ years of family heritage",
        ),
        (
            "Serving Jamul's ranches and estates for over 20 years",
            "Serving Jamul's ranches and estates since 2020",
        ),
        (
            "we've been working with the county for over 20 years",
            "we've been working with the county since 2020",
        ),
        (
            "Trusted by Escondido residents for over 20 years",
            "Trusted by Escondido residents since 2020",
        ),
        (
            "We've drilled throughout southwest Riverside County for over 20 years",
            "We've drilled throughout southwest Riverside County since 2020, with 60+ years of family heritage",
        ),
        (
            "We've drilled throughout Riverside County for over 20 years",
            "We've drilled throughout Riverside County since 2020, with 60+ years of family heritage",
        ),
        (
            "Serving Hemet and the San Jacinto Valley for over 20 years",
            "Serving Hemet and the San Jacinto Valley since 2020",
        ),
        (
            "Serving Poway's rural properties for over 20 years",
            "Serving Poway's rural properties since 2020",
        ),
        (
            "Our C-57 licensed team has drilled throughout Riverside County for over 20 years.",
            "Our C-57 licensed team has drilled throughout Riverside County since 2020.",
        ),
        (
            "We've drilled throughout North County for over 20 years",
            "We've drilled throughout North County since 2020, with 60+ years of family heritage",
        ),
        (
            "High-desert specialists with 20+ years experience.",
            "High-desert specialists. Founded 2020; 60+ years family heritage.",
        ),
        (
            "we've been serving San Diego County for over 20 years",
            "we've served San Diego County since 2020",
        ),
    ]
    for path in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in repls:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"updated company-age copy on {path.relative_to(ROOT)}")


def align_review_count() -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace("on Google (100+ reviews)", "on Google (127 reviews)")
    path.write_text(text, encoding="utf-8")
    well = ROOT / "well-drilling.html"
    if well.exists():
        w = well.read_text(encoding="utf-8")
        w2 = w.replace("with 100+ reviews", "with 127 reviews")
        if w2 != w:
            well.write_text(w2, encoding="utf-8")


def main() -> int:
    projects = load_projects()
    print(f"projects: {len(projects)}")
    print(f"anza nap files changed: {lock_anza_nap()}")
    add_city_and_service_links(projects)
    add_money_urls_to_sitemap()
    clean_blog_sitemaps()
    fix_company_age_copy()
    align_review_count()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
