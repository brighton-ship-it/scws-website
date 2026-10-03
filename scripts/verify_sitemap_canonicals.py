#!/usr/bin/env python3
"""Every sitemap URL must resolve to a page whose canonical is that URL and that is not noindex."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://scwellservice.com"
CANON_RE = re.compile(
    r'<link\b[^>]*\brel=["\']canonical["\'][^>]*>|<link\b[^>]*\bhref=["\'][^"\']+["\'][^>]*\brel=["\']canonical["\'][^>]*>',
    re.I,
)
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
ROBOTS_RE = re.compile(r'<meta\b[^>]*name=["\']robots["\'][^>]*>', re.I)


def url_to_path(url: str) -> Path:
    path = url.split("?", 1)[0].replace(SITE, "")
    if path in ("", "/"):
        return ROOT / "index.html"
    if path.endswith("/"):
        return ROOT / path.strip("/") / "index.html"
    return ROOT / path.lstrip("/")


def child_sitemaps() -> list[Path]:
    return sorted(path for path in ROOT.glob("sitemap-*.xml") if path.name != "sitemap.xml")


def collect() -> tuple[list[str], dict[str, list[str]]]:
    ordered: list[str] = []
    where: dict[str, list[str]] = defaultdict(list)
    for sitemap in child_sitemaps():
        for loc in re.findall(r"<loc>([^<]+)</loc>", sitemap.read_text(encoding="utf-8")):
            ordered.append(loc)
            where[loc].append(sitemap.name)
    return ordered, where


def main() -> int:
    ordered, where = collect()
    missing = []
    noindex = []
    bad_canon = []
    dups = {url: names for url, names in where.items() if len(names) > 1}
    for loc in where:
        path = url_to_path(loc)
        if not path.is_file():
            missing.append((loc, str(path)))
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        head = html[:20000]
        robots = ROBOTS_RE.search(head)
        if robots and "noindex" in robots.group(0).lower():
            noindex.append(loc)
        canon = CANON_RE.search(head) or CANON_RE.search(html)
        href = HREF_RE.search(canon.group(0)).group(1) if canon else None
        if href != loc:
            bad_canon.append((loc, href))
    print(f"sitemap locs {len(ordered)} unique {len(where)}")
    print(f"missing {len(missing)} noindex {len(noindex)} canonical mismatches {len(bad_canon)} cross-sitemap dups {len(dups)}")
    for item in missing[:20]:
        print(" MISSING", item)
    for item in noindex[:20]:
        print(" NOINDEX", item)
    for loc, href in bad_canon[:30]:
        print(" CANON", loc, "->", href)
    for url, names in list(dups.items())[:20]:
        print(" DUP", url, names)
    if missing or noindex or bad_canon or dups:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
