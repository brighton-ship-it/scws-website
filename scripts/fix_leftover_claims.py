#!/usr/bin/env python3
"""Apply leftover CSLB / age / 4.9 / permit-city noindex cleanup from repo root."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from leftover_claims_lib import walk_and_fix


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    changed = walk_and_fix(root)
    print(f"updated {len(changed)} files")
    for path in changed[:40]:
        print(f"  {path.relative_to(root)}")
    if len(changed) > 40:
        print(f"  ... {len(changed) - 40} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
