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
    apply_money_page_recent_work,
    money_page_section_html,
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
    """Homepage-style photo cards. Title + city only; real Jobber photos."""
    return money_page_section_html(
        projects,
        heading,
        "Real jobs. Real photos.",
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
    money = apply_money_page_recent_work(projects)
    for path in money:
        print(f"updated money-page photo cards on {path.relative_to(ROOT)}")
    money_set = {p.resolve() for p in money}
    for slug, city, path in CITY_PAGES:
        if path.resolve() in money_set:
            continue
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
        if path.resolve() in money_set:
            continue
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


ROBOTS_META_RE = re.compile(r"<meta\b[^>]*\bname=[\"']robots[\"'][^>]*>", re.I)
ROBOTS_META_SWAPPED_RE = re.compile(
    r"<meta\b[^>]*content=[\"'][^\"']*noindex[^\"']*[\"'][^>]*name=[\"']robots[\"']",
    re.I,
)
CANONICAL_RE = re.compile(
    r"""<link\b[^>]*rel=["']canonical["'][^>]*href=["']([^"']+)["']|<link\b[^>]*href=["']([^"']+)["'][^>]*rel=["']canonical["']""",
    re.I,
)
BROKEN_NAME_RE = re.compile(r"\s+\(\d+\)")


def html_head(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    end = lower.find("</head>")
    return text[:end] if end != -1 else text[:20000]


def html_is_noindex(path: Path) -> bool:
    head = html_head(path)
    if ROBOTS_META_SWAPPED_RE.search(head):
        return True
    return any("noindex" in tag.lower() for tag in ROBOTS_META_RE.findall(head))


def blog_file_for_url(url: str) -> Path | None:
    rel = url.replace("https://scwellservice.com/", "").split("?")[0]
    if rel in {"blog", "blog/"}:
        path = ROOT / "blog" / "index.html"
        return path if path.is_file() else None
    if rel.endswith(".html"):
        path = ROOT / rel
    else:
        path = ROOT / f"{rel}.html"
    return path if path.is_file() else None


def blog_canonical_url(path: Path) -> str:
    if path.name == "index.html":
        return "https://scwellservice.com/blog/"
    own = f"https://scwellservice.com/blog/{path.name}"
    match = CANONICAL_RE.search(html_head(path))
    if not match:
        return own
    href = match.group(1) or match.group(2)
    if " " in href or "(" in href:
        return own
    if not href.startswith("https://scwellservice.com/blog/"):
        return own
    target = blog_file_for_url(href)
    # Never advertise a noindex or city-well-depth target.
    if target is None:
        return own
    if html_is_noindex(target):
        return own
    if target.name.startswith("average-well-depth-"):
        return own
    return href



PERMIT_GUIDE_KEEP = {
    "well-permit-guide-san-diego.html",
    "well-permit-requirements-san-diego.html",
    "well-permit-denial-appeals.html",
    "well-permit-inspection-requirements.html",
    "well-permit-vs-replace.html",
    "well-permit-statistics-by-state.html",
    "well-permits-california.html",
    "well-permits-san-diego-county.html",
}


def is_programmatic_well_permit(name: str) -> bool:
    """City/neighborhood well-permit clones. Keep the real permit guides."""
    if name in PERMIT_GUIDE_KEEP:
        return False
    return name.startswith("well-permit-") and name.endswith(".html")


def indexable_blog_urls() -> list[str]:
    """Indexable blog URLs only: no robots noindex, no -OLD, no permit-city junk."""
    urls: list[str] = []
    seen: set[str] = set()
    for path in sorted((ROOT / "blog").glob("*.html")):
        if BROKEN_NAME_RE.search(path.name) or " " in path.name:
            continue
        if "-OLD" in path.name:
            continue
        if path.name.startswith("average-well-depth-"):
            continue
        if is_programmatic_well_permit(path.name):
            continue
        if html_is_noindex(path):
            continue
        url = blog_canonical_url(path)
        target = blog_file_for_url(url)
        if target is not None and (
            html_is_noindex(target)
            or target.name.startswith("average-well-depth-")
            or "-OLD" in target.name
            or BROKEN_NAME_RE.search(target.name)
            or is_programmatic_well_permit(target.name)
        ):
            continue
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls



def existing_blog_lastmods() -> dict[str, str]:
    mods: dict[str, str] = {}
    for i in range(1, 5):
        path = ROOT / f"sitemap-blog-{i}.xml"
        if not path.exists():
            continue
        for loc, lastmod in re.findall(
            r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>", path.read_text(encoding="utf-8")
        ):
            mods[loc] = lastmod
    return mods


def write_blog_sitemaps(urls: list[str], parts: int = 4) -> None:
    today = TODAY
    lastmods = existing_blog_lastmods()
    n = max(len(urls), 1)
    size = (n + parts - 1) // parts
    chunks = [urls[i : i + size] for i in range(0, len(urls), size)] or [[]]
    while len(chunks) < parts:
        chunks.append([])
    for i in range(parts):
        path = ROOT / f"sitemap-blog-{i + 1}.xml"
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n',
        ]
        for url in chunks[i] if i < len(chunks) else []:
            lastmod = lastmods.get(url, today)
            lines.append(
                f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod><priority>0.6</priority></url>\n"
            )
        lines.append("</urlset>\n")
        path.write_text("".join(lines), encoding="utf-8")
        print(f"{path.name}: {len(chunks[i]) if i < len(chunks) else 0} indexable URLs")


def clean_blog_sitemaps() -> None:
    urls = indexable_blog_urls()
    write_blog_sitemaps(urls)
    print(f"blog sitemap total indexable: {len(urls)}")
    index = ROOT / "sitemap.xml"
    xml = index.read_text(encoding="utf-8")
    xml = re.sub(
        r"(<loc>https://scwellservice.com/sitemap-blog-[1-4]\.xml</loc><lastmod>)[^<]+",
        rf"\g<1>{TODAY}",
        xml,
    )
    index.write_text(xml, encoding="utf-8")


def drop_city_well_depth_from_index() -> None:
    index = ROOT / "sitemap.xml"
    xml = index.read_text(encoding="utf-8")
    new = re.sub(
        r"  <sitemap><loc>https://scwellservice.com/sitemap-city-well-depth.xml</loc>.*?</sitemap>\n?",
        "",
        xml,
        flags=re.S,
    )
    if new != xml:
        index.write_text(new, encoding="utf-8")
        print("removed sitemap-city-well-depth.xml from sitemap index")
    empty = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "</urlset>\n"
    )
    (ROOT / "sitemap-city-well-depth.xml").write_text(empty, encoding="utf-8")
    print("emptied sitemap-city-well-depth.xml (300 noindex city-well-depth URLs)")


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
    drop_city_well_depth_from_index()
    fix_company_age_copy()
    align_review_count()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
