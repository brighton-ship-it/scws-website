#!/usr/bin/env python3
"""Wire homepage-style Recent Work photo cards onto money pages."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recent_work_lib import apply_money_page_recent_work


def main() -> int:
    changed = apply_money_page_recent_work()
    for path in changed:
        print(f"updated {path}")
    print(f"money pages with photo cards: {len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
