#!/usr/bin/env python3
"""Apply far-city factory noindex and drop those hubs from sitemap-services."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_seo_do_now import clean_blog_sitemaps
from far_city_factory_lib import apply_far_city_noindex, rebuild_services_sitemap


def main() -> int:
    changed = apply_far_city_noindex()
    kept = rebuild_services_sitemap()
    clean_blog_sitemaps()
    print(f"noindexed {len(changed)} far-city factory pages")
    print(f"sitemap-services.xml: {kept} indexable city hubs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
