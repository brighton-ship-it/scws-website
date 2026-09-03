#!/usr/bin/env python3
"""Noindex far-city city×topic factory pages. Do not delete the HTML.

Keep indexed: core shops (Ramona, Anza), ranking money cities (Temecula,
Valley Center, Escondido, Julian), homepage, real job pages, and local
problem guides that already rank (Ramona pump repair, Temecula drilling).
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = date.today().isoformat()

# High-desert / far-from-shop factory cities. Not core shops. Not the
# ranking west-SD / Temecula money set.
FAR_CITY_SLUGS = frozenset(
    {
        "adelanto",
        "apple-valley",
        "barstow",
        "victorville",
        "perris",
        "hesperia",
        "lucerne-valley",
        "oak-hills",
        "wrightwood",
        "yucca-valley",
        "joshua-tree",
        "twentynine-palms",
        "landers",
        "morongo-valley",
        "big-bear-lake",
        "lake-arrowhead",
        "crestline",
        "running-springs",
        "fontana",
        "colton",
        "rialto",
        "highland",
        "san-bernardino",
        "ontario",
        "upland",
        "rancho-cucamonga",
        "redlands",
        "loma-linda",
        "yucaipa",
        "palm-springs",
        "palm-desert",
        "cathedral-city",
        "indio",
        "la-quinta",
        "rancho-mirage",
    }
)

KEEP_CITY_SLUGS = frozenset(
    {
        "ramona",
        "anza",
        "temecula",
        "valley-center",
        "escondido",
        "julian",
    }
)

ROBOTS_NOINDEX_RE = re.compile(
    r"<meta\b[^>]*(?:name=[\"']robots[\"'][^>]*content=[\"'][^\"']*noindex|"
    r"content=[\"'][^\"']*noindex[^\"']*[\"'][^>]*name=[\"']robots[\"'])",
    re.I,
)
ROBOTS_META_RE = re.compile(r"<meta\b[^>]*\bname=[\"']robots[\"'][^>]*>", re.I)
NOINDEX_TAG = '<meta name="robots" content="noindex, follow">'


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def is_keep_path(path: Path) -> bool:
    rel = _rel(path)
    if rel == "index.html":
        return True
    if rel.startswith("recent-work/"):
        return True
    if rel.startswith("pages/services/"):
        return True
    parts = Path(rel).parts
    if len(parts) >= 2 and parts[0] == "services" and parts[1] in KEEP_CITY_SLUGS:
        return True
    if (
        len(parts) == 4
        and parts[0] == "pages"
        and parts[1] == "locations"
        and parts[2] == "cities"
        and Path(parts[3]).stem in KEEP_CITY_SLUGS
    ):
        return True
    if rel in {
        "blog/well-pump-repair-ramona.html",
        "blog/well-drilling-ramona.html",
        "blog/well-drilling-temecula.html",
        "blog/well-pump-repair-temecula.html",
    }:
        return True
    return False


def is_far_city_factory_path(path: Path) -> bool:
    if path.suffix.lower() != ".html":
        return False
    if is_keep_path(path):
        return False
    rel = _rel(path)
    parts = Path(rel).parts
    if len(parts) >= 2 and parts[0] == "services" and parts[1] in FAR_CITY_SLUGS:
        return True
    if (
        len(parts) == 4
        and parts[0] == "pages"
        and parts[1] == "locations"
        and parts[2] == "cities"
        and Path(parts[3]).stem in FAR_CITY_SLUGS
    ):
        return True
    if parts[0] == "blog":
        name = path.name
        for slug in FAR_CITY_SLUGS:
            if name.endswith(f"-{slug}.html"):
                return True
    return False


def ensure_noindex_follow(text: str) -> str:
    if ROBOTS_NOINDEX_RE.search(text):
        return text
    if ROBOTS_META_RE.search(text):
        return ROBOTS_META_RE.sub(NOINDEX_TAG, text, count=1)
    tag = NOINDEX_TAG + "\n"
    if re.search(r"</head>", text, re.I):
        return re.sub(r"</head>", tag + "</head>", text, count=1, flags=re.I)
    return tag + text


def html_is_noindex(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    lower = text.lower()
    end = lower.find("</head>")
    head = text[:end] if end != -1 else text[:8000]
    return bool(ROBOTS_NOINDEX_RE.search(head))


def iter_far_city_factory_paths(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    found: list[Path] = []
    services = root / "services"
    if services.is_dir():
        for slug in sorted(FAR_CITY_SLUGS):
            city_dir = services / slug
            if not city_dir.is_dir():
                continue
            found.extend(sorted(p for p in city_dir.glob("*.html") if is_far_city_factory_path(p)))
    cities = root / "pages" / "locations" / "cities"
    if cities.is_dir():
        for slug in sorted(FAR_CITY_SLUGS):
            path = cities / f"{slug}.html"
            if path.is_file() and is_far_city_factory_path(path):
                found.append(path)
    blog = root / "blog"
    if blog.is_dir():
        for path in sorted(blog.glob("*.html")):
            if is_far_city_factory_path(path):
                found.append(path)
    return found


def apply_far_city_noindex(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    changed: list[Path] = []
    for path in iter_far_city_factory_paths(root):
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        updated = ensure_noindex_follow(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def rebuild_services_sitemap(root: Path | None = None) -> int:
    """Keep city hubs that are still indexable. Drop noindex factory hubs."""
    root = root or ROOT
    services = root / "services"
    urls: list[str] = []
    if services.is_dir():
        for city_dir in sorted(p for p in services.iterdir() if p.is_dir()):
            index = city_dir / "index.html"
            if not index.is_file():
                continue
            if html_is_noindex(index):
                continue
            urls.append(f"https://scwellservice.com/services/{city_dir.name}/")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n',
    ]
    for url in urls:
        lines.append(
            f"  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod><priority>0.7</priority></url>\n"
        )
    lines.append("</urlset>\n")
    (root / "sitemap-services.xml").write_text("".join(lines), encoding="utf-8")
    return len(urls)
