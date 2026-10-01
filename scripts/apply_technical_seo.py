#!/usr/bin/env python3
"""One-shot technical SEO fixes that GitHub Pages can honor without redirects.

- Self-canonical the 21 blog posts that pointed at the dead socalwellservices.com domain.
- Self-canonical blog posts that were pointed at a different, still-useful article.
- Point /services/{city}/ canonicals at the trailing-slash sitemap URL.
- Canonical duplicate /pages/locations/cities/{city}.html pages at /services/{city}/
  and drop the duplicates from the sitemap.
- Canonical the weaker no-water post at the stronger "runs" URL and drop it
  from the sitemap.
- Remove URLs that appear in two child sitemaps.
- Point /privacy and /terms at the files GitHub Pages actually serves.
- Refresh sitemap index lastmod from each child sitemap.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://scwellservice.com"
TODAY = date.today().isoformat()

DEAD_DOMAIN_POSTS = [
    "pressure-gauge-stuck-at-zero.html",
    "squealing-noise-from-well-pump.html",
    "well-pressure-tank-losing-air.html",
    "well-pump-buzzing-sound.html",
    "well-pump-humming-not-starting.html",
    "well-pump-motor-hot-to-touch.html",
    "well-pump-running-continuously.html",
    "well-pump-starts-by-itself.html",
    "well-pump-trips-gfci.html",
    "well-water-black-particles.html",
    "well-water-brown-after-power-outage.html",
    "well-water-burns-eyes-in-shower.html",
    "well-water-foams-when-running.html",
    "well-water-leaves-green-stains.html",
    "well-water-leaves-orange-stains.html",
    "well-water-pressure-different-each-faucet.html",
    "well-water-pressure-drops-at-night.html",
    "well-water-pressure-only-40-psi.html",
    "well-water-smells-after-sitting.html",
    "well-water-smells-like-gasoline.html",
    "well-water-smells-musty.html",
]

# These are distinct articles (cost vs. how-it-works, checklist vs. buyer guide).
# Pointing them at another URL was wrong. Keep each one self-canonical.
SELF_CANONICAL_BLOGS = [
    "how-much-to-drill-a-well.html",
    "well-casing-collapse-repair.html",
    "buying-home-with-well-checklist.html",
    "buying-property-with-well.html",
    "constant-pressure-system-cost.html",
]

TRAILING_SLASH_CITIES = ["temecula", "escondido", "fallbrook", "julian"]
DUPLICATE_CITY_PAGES = [
    "ramona",
    "anza",
    "valley-center",
    "aguanga",
    "temecula",
    "escondido",
    "julian",
]

CANON_HREF_RE = re.compile(
    r'(<link\b[^>]*\bhref=["\'])([^"\']+)(["\'][^>]*\brel=["\']canonical["\'][^>]*>)'
    r'|(<link\b[^>]*\brel=["\']canonical["\'][^>]*\bhref=["\'])([^"\']+)(["\'][^>]*>)',
    re.I,
)
URL_LINE_RE = re.compile(r"  <url><loc>([^<]+)</loc>.*?</url>\n?")


def _set_canonical(text: str, url: str) -> str:
    def repl(match: re.Match[str]) -> str:
        if match.group(1):
            return f"{match.group(1)}{url}{match.group(3)}"
        return f"{match.group(4)}{url}{match.group(6)}"

    updated, n = CANON_HREF_RE.subn(repl, text, count=1)
    if n != 1:
        raise RuntimeError(f"canonical tag not updated for {url}")
    return updated


def fix_dead_domain_blogs() -> int:
    changed = 0
    for name in DEAD_DOMAIN_POSTS:
        path = ROOT / "blog" / name
        text = path.read_text(encoding="utf-8")
        url = f"{SITE}/blog/{name}"
        text = text.replace("https://socalwellservices.com", SITE)
        text = _set_canonical(text, url)
        path.write_text(text, encoding="utf-8")
        changed += 1
    return changed


def fix_wrong_internal_blog_canonicals() -> int:
    changed = 0
    for name in SELF_CANONICAL_BLOGS:
        path = ROOT / "blog" / name
        text = path.read_text(encoding="utf-8")
        url = f"{SITE}/blog/{name}"
        text = _set_canonical(text, url)
        path.write_text(text, encoding="utf-8")
        changed += 1
    return changed


def fix_trailing_slash_service_canonicals() -> int:
    changed = 0
    for city in TRAILING_SLASH_CITIES:
        path = ROOT / "services" / city / "index.html"
        text = path.read_text(encoding="utf-8")
        url = f"{SITE}/services/{city}/"
        text = text.replace(f"{SITE}/services/{city}/index.html", url)
        text = _set_canonical(text, url)
        text = re.sub(
            r'(<meta\b[^>]*property=["\']og:url["\'][^>]*content=["\'])([^"\']+)(["\'])',
            rf"\1{url}\3",
            text,
            count=1,
            flags=re.I,
        )
        text = re.sub(
            r'(<meta\b[^>]*content=["\'])([^"\']+)(["\'][^>]*property=["\']og:url["\'])',
            rf"\1{url}\3",
            text,
            count=1,
            flags=re.I,
        )
        path.write_text(text, encoding="utf-8")
        changed += 1
    return changed


def fix_duplicate_city_canonicals() -> int:
    changed = 0
    for city in DUPLICATE_CITY_PAGES:
        path = ROOT / "pages" / "locations" / "cities" / f"{city}.html"
        text = path.read_text(encoding="utf-8")
        target = f"{SITE}/services/{city}/"
        old = f"{SITE}/pages/locations/cities/{city}.html"
        text = _set_canonical(text, target)
        text = text.replace(old, target)
        path.write_text(text, encoding="utf-8")
        changed += 1
    return changed


def fix_no_water_duplicate() -> None:
    """Keep the stronger 'runs' URL. Canonical the weaker 'running' URL at it."""
    path = ROOT / "blog" / "well-pump-running-but-no-water.html"
    text = path.read_text(encoding="utf-8")
    target = f"{SITE}/blog/well-pump-runs-but-no-water.html"
    text = _set_canonical(text, target)
    note = (
        '<p class="text-lg text-gray-700 mb-6">This page is the shorter twin of our main guide. '
        f'<a href="{target}">Well pump runs but no water</a> is the one to use. '
        "It includes the shutoff steps, the gauge readings, closed valves, and mountain freezes.</p>\n"
    )
    marker = "<h1>Pump Running But No Water? What San Diego County Shops Check</h1>"
    if note.strip() not in text and marker in text:
        text = text.replace(marker, marker + "\n" + note, 1)
    path.write_text(text, encoding="utf-8")


def fix_extensionless_pages() -> None:
    for stem in ("privacy", "terms"):
        path = ROOT / f"{stem}.html"
        text = path.read_text(encoding="utf-8")
        text = _set_canonical(text, f"{SITE}/{stem}.html")
        text = text.replace(f"{SITE}/{stem}\"", f"{SITE}/{stem}.html\"")
        text = text.replace(f"{SITE}/{stem}'", f"{SITE}/{stem}.html'")
        path.write_text(text, encoding="utf-8")


def _child_sitemaps() -> list[Path]:
    return sorted(
        path
        for path in ROOT.glob("sitemap-*.xml")
        if path.name != "sitemap.xml"
    )


def _preferred_sitemap(url: str, names: list[str]) -> str:
    if url.rstrip("/").endswith("/blog"):
        return "sitemap-pages.xml" if "sitemap-pages.xml" in names else names[0]
    if "/blog/" in url:
        blogs = [name for name in names if name.startswith("sitemap-blog")]
        return blogs[0] if blogs else names[0]
    if "/services/" in url and "sitemap-services.xml" in names:
        return "sitemap-services.xml"
    return names[0]


def dedupe_child_sitemaps() -> int:
    files = _child_sitemaps()
    locs: dict[str, list[str]] = {}
    bodies: dict[str, str] = {}
    for path in files:
        text = path.read_text(encoding="utf-8")
        bodies[path.name] = text
        for loc in re.findall(r"<loc>([^<]+)</loc>", text):
            locs.setdefault(loc, []).append(path.name)
    removed = 0
    drop_urls = {
        f"{SITE}/blog/well-pump-running-but-no-water.html",
        f"{SITE}/privacy",
        f"{SITE}/terms",
    }
    for city in DUPLICATE_CITY_PAGES:
        drop_urls.add(f"{SITE}/pages/locations/cities/{city}.html")
    for url, names in locs.items():
        if len(names) < 2 and url not in drop_urls:
            continue
        if url in drop_urls:
            keep = None
        else:
            keep = _preferred_sitemap(url, names)
        for name in names:
            if name == keep:
                continue
            pattern = re.compile(
                r"  <url><loc>" + re.escape(url) + r"</loc>.*?</url>\n?"
            )
            new_body, n = pattern.subn("", bodies[name])
            if n:
                bodies[name] = new_body
                removed += n
    # Within-file duplicates (recent-work/ was repeated inside sitemap-pages).
    for name, text in list(bodies.items()):
        seen: set[str] = set()

        def keep_first(match: re.Match[str]) -> str:
            loc = match.group(1)
            if loc in seen:
                return ""
            seen.add(loc)
            return match.group(0)

        bodies[name] = URL_LINE_RE.sub(keep_first, text)
    pages = bodies.get("sitemap-pages.xml", "")
    if f"{SITE}/privacy.html" not in pages:
        pages = pages.replace(
            "</urlset>",
            f"  <url><loc>{SITE}/privacy.html</loc><lastmod>{TODAY}</lastmod><priority>0.4</priority></url>\n"
            f"  <url><loc>{SITE}/terms.html</loc><lastmod>{TODAY}</lastmod><priority>0.4</priority></url>\n"
            "</urlset>",
        )
        bodies["sitemap-pages.xml"] = pages
    for path in files:
        path.write_text(bodies[path.name], encoding="utf-8")
    return removed


def refresh_sitemap_index_lastmod() -> None:
    index_path = ROOT / "sitemap.xml"
    text = index_path.read_text(encoding="utf-8")
    for child in _child_sitemaps():
        lastmods = re.findall(r"<lastmod>([^<]+)</lastmod>", child.read_text(encoding="utf-8"))
        if not lastmods:
            continue
        latest = max(lastmods)
        text, n = re.subn(
            rf"(<loc>{re.escape(SITE)}/{re.escape(child.name)}</loc><lastmod>)[^<]+",
            rf"\g<1>{latest}",
            text,
            count=1,
        )
        if n != 1 and f"{SITE}/{child.name}" in text:
            raise RuntimeError(f"could not refresh lastmod for {child.name}")
    index_path.write_text(text, encoding="utf-8")


def main() -> None:
    print(f"dead-domain canonicals fixed: {fix_dead_domain_blogs()}")
    print(f"internal blog canonicals fixed: {fix_wrong_internal_blog_canonicals()}")
    print(f"trailing-slash service canonicals: {fix_trailing_slash_service_canonicals()}")
    print(f"duplicate city canonicals: {fix_duplicate_city_canonicals()}")
    fix_no_water_duplicate()
    fix_extensionless_pages()
    print(f"cross-sitemap urls removed: {dedupe_child_sitemaps()}")
    refresh_sitemap_index_lastmod()
    print("sitemap index lastmod refreshed")


if __name__ == "__main__":
    main()
