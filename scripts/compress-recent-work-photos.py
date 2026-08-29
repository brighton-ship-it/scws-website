#!/usr/bin/env python3
"""Recompress images/recent-work/*.jpg for the listing and job pages.

Keeps the existing JPEG pipeline (no WebP rename). Resizes long edge to
~1400px and writes quality ~80, targeting ≤200 KB. Files that stay over
200 KB get a tighter pass (edge 1200/1000/900, quality down to 55).
Does not invent pixels or copy from gbp-photos. Skips files already
at or under 200 KB.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PHOTO_DIR = ROOT / "images" / "recent-work"
LONG_EDGE = 1400
TARGET_MAX_KB = 200
MIN_QUALITY = 55
START_QUALITY = 80
EDGE_STEPS = (1400, 1200, 1000, 900)


def compress_one(path: Path) -> tuple[int, int, int]:
    before = path.stat().st_size
    if before <= TARGET_MAX_KB * 1024:
        return before, before, START_QUALITY
    target = TARGET_MAX_KB * 1024
    best: bytes | None = None
    best_quality = START_QUALITY
    with Image.open(path) as raw:
        im = ImageOps.exif_transpose(raw)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        elif im.mode == "L":
            im = im.convert("RGB")
        w0, h0 = im.size
        for edge in EDGE_STEPS:
            work = im
            long_edge = max(w0, h0)
            if long_edge > edge:
                scale = edge / float(long_edge)
                work = im.resize(
                    (max(1, int(w0 * scale)), max(1, int(h0 * scale))),
                    Image.Resampling.LANCZOS,
                )
            quality = START_QUALITY
            while quality >= MIN_QUALITY:
                buf = io.BytesIO()
                work.save(
                    buf,
                    "JPEG",
                    quality=quality,
                    optimize=True,
                    progressive=True,
                )
                data = buf.getvalue()
                if best is None or len(data) < len(best):
                    best = data
                    best_quality = quality
                if len(data) <= target:
                    break
                quality -= 5
            if best is not None and len(best) <= target:
                break
    if best is not None and len(best) < before:
        path.write_bytes(best)
    after = path.stat().st_size
    return before, after, best_quality


def main() -> int:
    files = sorted(PHOTO_DIR.glob("*.jpg")) + sorted(PHOTO_DIR.glob("*.jpeg"))
    if not files:
        print(f"no JPEGs in {PHOTO_DIR}", file=sys.stderr)
        return 1
    total_before = 0
    total_after = 0
    over = 0
    changed = 0
    for path in files:
        before, after, quality = compress_one(path)
        total_before += before
        total_after += after
        kb = after / 1024
        flag = ""
        if after > TARGET_MAX_KB * 1024:
            over += 1
            flag = " OVER"
        if before != after or flag:
            changed += 1
            print(f"{path.name}: {before/1024:.0f}KB -> {kb:.0f}KB q{quality}{flag}")
    print(f"changed {changed} of {len(files)} files")
    print(
        f"done {len(files)} files, "
        f"{total_before/1024/1024:.1f}MB -> {total_after/1024/1024:.1f}MB, "
        f"{over} still over {TARGET_MAX_KB}KB"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
