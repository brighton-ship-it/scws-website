#!/usr/bin/env python3
"""Generate Recent Work job pages and per-city hubs from projects.json.

Thin jobs (boilerplate or under the word threshold in recent_work_lib) are
written with robots noindex,follow and left out of the sitemap. City hubs
and indexable job notes are sitemap URLs with a self-canonical.

    python3 scripts/generate-recent-work-pages.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recent_work_lib import (
    INDEX_HTML,
    ROOT,
    iter_city_hubs,
    job_is_indexable,
    load_projects,
    public_meta_descriptions,
    public_titles,
    update_index_html,
    update_sitemap,
)
from recent_work_render import render_city_hub, render_job_page

OUT_DIR = ROOT / "recent-work"
HUB_DIR = OUT_DIR / "areas"


def main() -> None:
    projects = load_projects().get("projects") or []
    titles = public_titles(projects)
    descriptions = public_meta_descriptions(projects)
    slugs = set()
    indexable = 0
    for project in projects:
        slug = project["slug"]
        slugs.add(slug)
        if job_is_indexable(project):
            indexable += 1
        path = OUT_DIR / f"{slug}.html"
        path.write_text(render_job_page(project, title=titles[slug], description=descriptions[slug]))
    for leftover in OUT_DIR.glob("*.html"):
        if leftover.name == "index.html" or leftover.name.startswith("page-"):
            continue
        if leftover.stem not in slugs:
            leftover.unlink()

    HUB_DIR.mkdir(parents=True, exist_ok=True)
    hub_names = set()
    for hub in iter_city_hubs(projects):
        hub_names.add(f"{hub['slug']}.html")
        (HUB_DIR / f"{hub['slug']}.html").write_text(render_city_hub(hub))
    for leftover in HUB_DIR.glob("*.html"):
        if leftover.name not in hub_names:
            leftover.unlink()

    if INDEX_HTML.exists():
        update_index_html(projects)
    update_sitemap(projects)
    from apply_technical_seo import refresh_sitemap_index_lastmod

    refresh_sitemap_index_lastmod()
    print(
        f"jobs {len(projects)} indexable {indexable} "
        f"noindex {len(projects) - indexable} hubs {len(hub_names)}"
    )


if __name__ == "__main__":
    main()
