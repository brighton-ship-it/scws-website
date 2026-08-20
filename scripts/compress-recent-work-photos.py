#!/usr/bin/env python3
"""Recompress images/recent-work/*.jpg for the listing and job pages.

Keeps the existing JPEG pipeline (no WebP rename). Resizes long edge to
~1400px and writes quality ~80, targeting 200–400 KB. Does not invent
pixels or copy from gbp-photos.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PHOTO_DIR = ROOT / "images" / "recent-work"
LONG_EDGE = 1400
TARGET_MAX_KB = 400
MIN_QUALITY = 68
START_QUALITY = 80


def compress_one(path: Path) -> tuple[int, int, int]:
    before = path.stat().st_size
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        elif im.mode == "L":
            im = im.convert("RGB")
        w, h = im.size
        long_edge = max(w, h)
        if long_edge > LONG_EDGE:
            scale = LONG_EDGE / float(long_edge)
            im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        quality = START_QUALITY
        tmp = path.with_suffix(".jpg.tmp")
        while True:
            im.save(
                tmp,
                "JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
            size = tmp.stat().st_size
            if size <= TARGET_MAX_KB * 1024 or quality <= MIN_QUALITY:
                break
            quality -= 4
        tmp.replace(path)
    after = path.stat().st_size
    return before, after, quality


def main() -> int:
    files = sorted(PHOTO_DIR.glob("*.jpg")) + sorted(PHOTO_DIR.glob("*.jpeg"))
    if not files:
        print(f"no JPEGs in {PHOTO_DIR}", file=sys.stderr)
        return 1
    total_before = 0
    total_after = 0
    over = 0
    for path in files:
        before, after, quality = compress_one(path)
        total_before += before
        total_after += after
        kb = after / 1024
        flag = ""
        if after > TARGET_MAX_KB * 1024:
            over += 1
            flag = " OVER"
        print(f"{path.name}: {before/1024:.0f}KB -> {kb:.0f}KB q{quality}{flag}")
    print(
        f"done {len(files)} files, "
        f"{total_before/1024/1024:.1f}MB -> {total_after/1024/1024:.1f}MB, "
        f"{over} still over {TARGET_MAX_KB}KB"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
