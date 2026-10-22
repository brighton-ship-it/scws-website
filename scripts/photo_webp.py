#!/usr/bin/env python3
"""Resize site photos to WebP and point pages at them with <picture>.

The original JPEG or PNG file stays in place and stays the <img src>, so existing
image URLs are not removed. WebP is an extra source. Width and height follow the
file's real pixels. The first content photo is eager; later photos are lazy.
"""
from __future__ import annotations

import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from recent_work_lib import image_pixel_size  # noqa: E402

PHOTO_ROOTS = (ROOT / "images", ROOT / "assets" / "images")
SKIP_NAMES = {"favicon-32.png", "apple-touch-icon.png", "favicon.ico"}
LARGE_MAX = 800
SMALL_MAX = 480
QUALITY = 70
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
ATTR_RE = r"""{name}\s*=\s*(['"])(.*?)\1"""
FOOTER_RE = re.compile(r"<footer\b[^>]*>[\s\S]*?</footer>", re.I)
MENU_RE = re.compile(r"<button\b[^>]*\bid=[\"']mobile-menu-btn[\"'][^>]*>", re.I)

HERO_OLD = "    .rw-hero img { width: 100%; height: 280px; object-fit: cover; display: block; }"
HERO_NEW = (
    "    .rw-hero picture, .rw-thumbs picture { display: block; }\n"
    "    .rw-hero img { width: 100%; height: auto; max-width: 100%; object-fit: contain; "
    "display: block; background: #1f3b4d; }"
)
THUMB_OLD = "    .rw-thumbs img { width: 100%; height: 110px; object-fit: cover; border-radius: 10px; background: #e5e7eb; }"
THUMB_NEW = "    .rw-thumbs img { width: 100%; height: auto; object-fit: contain; border-radius: 10px; background: #e5e7eb; }"
MQ_OLD = "        .rw-hero img { height: 460px; }\n"
LOGO_CSS = """
/* Keep the header logo's real aspect ratio. Fixed height plus max-width was stretching it. */
.site-logo-img{height:auto;width:auto;max-height:2rem;max-width:130px}
@media (min-width:640px){.site-logo-img{height:auto;max-height:2.5rem;max-width:200px}}
@media (min-width:1280px){.site-logo-img{height:auto;max-height:3rem;max-width:none}}
.blog-hero-image img{width:100%;height:auto;max-height:none;-o-object-fit:contain;object-fit:contain}
"""


def photo_files() -> list[Path]:
    found: list[Path] = []
    for root in PHOTO_ROOTS:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            if path.name in SKIP_NAMES:
                continue
            found.append(path)
    return found


def _resized(im, max_width: int):
    if im.width <= max_width:
        return im
    height = max(1, round(im.height * max_width / im.width))
    return im.resize((max_width, height), 1)  # LANCZOS is 1


def convert_one(path_str: str) -> str:
    from PIL import Image

    path = Path(path_str)
    try:
        im = Image.open(path)
        im.load()
    except Exception as exc:  # noqa: BLE001
        return f"err {path.name} {exc}"
    if max(im.size) < 2:
        return "tiny"
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
    stem = path.stem
    large_path = path.with_name(f"{stem}.webp")
    small_path = path.with_name(f"{stem}-480.webp")
    large = _resized(im, LARGE_MAX)
    large.save(large_path, "WEBP", quality=QUALITY, method=4)
    if im.width > SMALL_MAX:
        small = _resized(im, SMALL_MAX)
        small.save(small_path, "WEBP", quality=QUALITY, method=4)
    elif small_path.is_file():
        small_path.unlink()
    return "ok"


def convert_all() -> None:
    files = [str(path) for path in photo_files()]
    workers = min(8, os.cpu_count() or 2)
    ok = err = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, result in enumerate(pool.map(convert_one, files, chunksize=8), start=1):
            if result == "ok":
                ok += 1
            else:
                err += 1
                if err <= 12:
                    print(result, flush=True)
            if i % 400 == 0:
                print(f"converted {i}/{len(files)}", flush=True)
    print(f"convert done ok={ok} other={err} of {len(files)}", flush=True)


def _attr(tag: str, name: str) -> str | None:
    match = re.search(ATTR_RE.format(name=name), tag, re.I | re.S)
    return match.group(2) if match else None


def _set_attr(tag: str, name: str, value: str) -> str:
    pattern = re.compile(ATTR_RE.format(name=name), re.I | re.S)
    if pattern.search(tag):
        return pattern.sub(f'{name}="{value}"', tag, count=1)
    if tag.endswith("/>"):
        return tag[:-2] + f' {name}="{value}"/>'
    return tag[:-1] + f' {name}="{value}">'


def _del_attr(tag: str, name: str) -> str:
    return re.sub(r"\s+" + ATTR_RE.format(name=name), "", tag, count=1, flags=re.I | re.S)


def _resolve(html_path: Path, src: str) -> Path | None:
    clean = src.split("?", 1)[0].split("#", 1)[0]
    if not clean or clean.startswith(("data:", "http:", "https:", "//")):
        return None
    if clean.startswith("/"):
        path = ROOT / clean.lstrip("/")
    else:
        path = (html_path.parent / clean).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        return None
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        return None
    if not path.is_file() or path.name in SKIP_NAMES:
        return None
    return path


def _webp_sources(src: str, path: Path) -> list[tuple[str, int]]:
    original = path.stat().st_size
    stem = path.stem
    folder = str(Path(src.split("?", 1)[0]).parent)
    if folder in ("", "."):
        prefix = ""
    else:
        prefix = folder + "/"
    found: list[tuple[str, int]] = []
    seen: set[int] = set()
    for name in (f"{stem}-480.webp", f"{stem}.webp"):
        webp = path.with_name(name)
        if not webp.is_file() or webp.stat().st_size >= original:
            continue
        dim = image_pixel_size(webp)
        if not dim or dim[0] in seen:
            continue
        seen.add(dim[0])
        found.append((f"{prefix}{name}", dim[0]))
    found.sort(key=lambda item: item[1])
    return found


def _region(html: str, start: int, open_tag: str, close_tag: str) -> bool:
    head = html[:start].lower()
    return head.rfind(open_tag) > head.rfind(close_tag)


def rewrite_images(html: str, html_path: Path) -> str:
    matches = list(IMG_RE.finditer(html))
    if not matches:
        return html
    pieces: list[str] = []
    cursor = 0
    seen_lcp = False
    for match in matches:
        tag = match.group(0)
        pieces.append(html[cursor : match.start()])
        cursor = match.end()
        before = html[max(0, match.start() - 600) : match.start()].lower()
        if before.rfind("<picture") > before.rfind("</picture"):
            pieces.append(tag)
            continue
        src = _attr(tag, "src")
        path = _resolve(html_path, src or "")
        if path is None:
            pieces.append(tag)
            continue
        dim = image_pixel_size(path)
        if dim:
            tag = _set_attr(tag, "width", str(dim[0]))
            tag = _set_attr(tag, "height", str(dim[1]))
        in_header = _region(html, match.start(), "<header", "</header>")
        in_footer = _region(html, match.start(), "<footer", "</footer>")
        if in_header:
            tag = _del_attr(tag, "loading")
            tag = _del_attr(tag, "fetchpriority")
        elif in_footer or seen_lcp:
            tag = _del_attr(tag, "fetchpriority")
            if _attr(tag, "loading") is None:
                tag = _set_attr(tag, "loading", "lazy")
        else:
            seen_lcp = True
            tag = _del_attr(tag, "loading")
            tag = _set_attr(tag, "fetchpriority", "high")
        if _attr(tag, "decoding") is None:
            tag = _set_attr(tag, "decoding", "async")
        sources = _webp_sources(src or "", path)
        if not sources:
            pieces.append(tag)
            continue
        sizes = _attr(tag, "sizes")
        if not sizes:
            sizes = "100vw" if not in_header and not in_footer and "fetchpriority" in tag else "(min-width: 1024px) 40vw, 100vw"
            tag = _set_attr(tag, "sizes", sizes)
        srcset = ", ".join(f"{url} {width}w" for url, width in sources)
        pieces.append(
            f'<picture><source type="image/webp" srcset="{srcset}" sizes="{sizes}">{tag}</picture>'
        )
    pieces.append(html[cursor:])
    return "".join(pieces)


def close_heading_gaps(html: str) -> str:
    """Lower a heading that skips a level. Heading text stays the same."""
    chunks = re.split(
        r"(<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>)",
        html,
        flags=re.I,
    )
    heading = re.compile(r"<h([1-6])(\b[^>]*)>([\s\S]*?)</h\1>", re.I)
    state = {"prev": 0}

    def repl(match: re.Match[str]) -> str:
        level = int(match.group(1))
        new_level = level
        if state["prev"] and level > state["prev"] + 1:
            new_level = state["prev"] + 1
        state["prev"] = new_level
        if new_level == level:
            return match.group(0)
        return f"<h{new_level}{match.group(2)}>{match.group(3)}</h{new_level}>"

    rebuilt: list[str] = []
    for index, chunk in enumerate(chunks):
        if index % 2 == 1:
            rebuilt.append(chunk)
            continue
        rebuilt.append(heading.sub(repl, chunk))
    return "".join(rebuilt)


def demote_footer_headings(html: str) -> str:
    """Footer column titles were h4 under an h2, which skips a level."""

    def repl(match: re.Match[str]) -> str:
        block = match.group(0)
        block = re.sub(r"<h4(\s|>)", r"<h3\1", block, flags=re.I)
        block = re.sub(r"</h4>", "</h3>", block, flags=re.I)
        return block

    return FOOTER_RE.sub(repl, html, count=1)


def name_menu_button(html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        if re.search(r"aria-label\s*=", tag, re.I):
            return tag
        return tag[:-1] + ' aria-label="Open menu">'

    return MENU_RE.sub(repl, html)


def patch_job_css(html: str) -> str:
    html = html.replace(HERO_OLD, HERO_NEW)
    html = html.replace(THUMB_OLD, THUMB_NEW)
    html = html.replace(MQ_OLD, "")
    return html


def patch_styles() -> None:
    path = ROOT / "css" / "styles.css"
    text = path.read_text(encoding="utf-8")
    if "Keep the header logo's real aspect ratio" in text:
        return
    path.write_text(text + LOGO_CSS, encoding="utf-8")


def rewrite_pages() -> None:
    changed = 0
    for path in ROOT.rglob("*.html"):
        if ".git" in path.parts or "node_modules" in path.parts:
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = rewrite_images(original, path)
        updated = patch_job_css(updated)
        updated = name_menu_button(updated)
        if path.parts[-2:] and "blog" in path.parts:
            # Only the blog tree. The path check above is true for blog/*.html.
            if path.parent.name == "blog":
                updated = demote_footer_headings(updated)
                updated = close_heading_gaps(updated)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"rewrote {changed} html files", flush=True)


def main() -> None:
    convert_all()
    patch_styles()
    rewrite_pages()


if __name__ == "__main__":
    main()
