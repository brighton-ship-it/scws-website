#!/usr/bin/env python3
"""Apply the money-page SEO package: Recent Work cards, depth, sitemaps."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_money_page_depth import apply_depth, apply_h1_fixes
from apply_seo_do_now import add_money_urls_to_sitemap
from recent_work_lib import apply_money_page_recent_work


def main() -> int:
    apply_h1_fixes()
    apply_depth()
    changed = apply_money_page_recent_work()
    add_money_urls_to_sitemap()
    print(f"recent-work money pages updated: {len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
