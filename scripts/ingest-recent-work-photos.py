#!/usr/bin/env python3
"""Copy Jobber job photos into images/recent-work/, converting webp → jpg."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "images" / "recent-work"
SOURCES = [
    Path("/workspace/scws_photos"),
    Path("/workspace/../scws_photos"),
    Path.home() / "scws_photos",
    Path("/mnt/scws_photos"),
    ROOT / "scws_photos",
]

WANTED = {
    "job3049_1": "job3049_1.jpg",
    "job3049_2": "job3049_2.jpg",
    "job3174_1": "job3174_1.jpg",
    "job3174_2": "job3174_2.jpg",
    "job3139_1": "job3139_1.jpg",
    "job3141_1": "job3141_1.jpg",
    "job3141_2": "job3141_2.jpg",
    "job3115_1": "job3115_1.jpg",
    "job3115_2": "job3115_2.jpg",
    "job3145_1": "job3145_1.jpg",
    "job3145_2": "job3145_2.jpg",
    "job3159_1": "job3159_1.jpg",
    "job3134_1": "job3134_1.jpg",
    "job3134_2": "job3134_2.jpg",
}


def stem_key(path: Path) -> str:
    name = path.stem.lower()
    for key in WANTED:
        if name == key or name.startswith(key):
            return key
    return ""


def convert_or_copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in {".jpg", ".jpeg"}:
        shutil.copy2(src, dest)
        return
    try:
        from PIL import Image
    except ImportError:
        shutil.copy2(src, dest.with_suffix(src.suffix.lower()))
        return
    with Image.open(src) as im:
        rgb = im.convert("RGB")
        rgb.save(dest, "JPEG", quality=86, optimize=True)


def main() -> int:
    extra = [Path(p) for p in sys.argv[1:]]
    found = 0
    for folder in extra + SOURCES:
        if not folder.is_dir():
            continue
        print(f"scanning {folder}")
        for path in folder.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".webp", ".png"}:
                continue
            key = stem_key(path)
            if not key:
                continue
            dest = DEST / WANTED[key]
            convert_or_copy(path, dest)
            print(f"  {path.name} -> {dest.relative_to(ROOT)}")
            found += 1
    if not found:
        print("no matching job photos found")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
