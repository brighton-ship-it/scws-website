#!/usr/bin/env python3
"""Helpers for publishing Recent Work cards from Jobber jobs.

Public output rules (do not relax these):
- Title + city/area only
- No customer last names, full street addresses, prices, or Jobber URLs
- Photos must be real Jobber attachments (never invented pixels)
"""
from __future__ import annotations

import html
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_JSON = ROOT / "recent-work" / "projects.json"
PROJECTS_JS = ROOT / "js" / "recent-work-projects.js"
INDEX_HTML = ROOT / "recent-work" / "index.html"
PHOTO_DIR = ROOT / "images" / "recent-work"
SITEMAP_PAGES = ROOT / "sitemap-pages.xml"
PACIFIC = ZoneInfo("America/Los_Angeles")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/heic",
    "image/heif",
}
DOC_NAME_RE = re.compile(
    r"contract|docusign|agreement|invoice|estimate|permit|proposal|"
    r"receipt|signature|\.pdf$|document|envelope|lien|notice|cancellation",
    re.I,
)
PRICE_RE = re.compile(
    r"\$\s*[\d,]+(?:\.\d{1,2})?|\b\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?\s*(?:dollars?)?\b|"
    r"\b\d+\.\d{2}\s*(?:dollars?)?\b",
    re.I,
)
STREET_RE = re.compile(
    r"\b\d{1,6}\s+[A-Za-z0-9.'-]+(?:\s+[A-Za-z0-9.'-]+){0,4}\s+"
    r"(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Way|Ct|Court|"
    r"Blvd|Boulevard|Hwy|Highway|Cir|Circle|Pl|Place|Ter|Terrace|Pkwy|Parkway)\b\.?",
    re.I,
)
JOBBER_URL_RE = re.compile(r"https?://\S*jobber\S*", re.I)
URL_RE = re.compile(r"https?://\S+", re.I)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
LAST_NAME_HINT_RE = re.compile(
    r"\b(?:mr|mrs|ms|miss|for the)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"
)
CARD_MARKERS = ("<!-- RECENT_WORK_CARDS_START -->", "<!-- RECENT_WORK_CARDS_END -->")
JSONLD_ITEMLIST_RE = re.compile(
    r'"numberOfItems":\s*\d+\s*,\s*"itemListElement":\s*\[.*?\]',
    re.S,
)

CATEGORY_LABELS = {
    "pump": "Pump Service",
    "drilling": "Well Drilling",
    "tank": "Pressure Tanks",
    "water-quality": "Water Quality",
    "maintenance": "Maintenance",
}

PUBLIC_TITLE_RE = re.compile(
    r"pump|well|tank|motor|drill|filter|treatment|inspect|maintenance|"
    r"wire|controller|booster|chlorin|pressure|install|repair|replace",
    re.I,
)


def load_projects() -> dict[str, Any]:
    if not PROJECTS_JSON.exists():
        return {
            "generatedFrom": "Jobber",
            "note": "Public copy only. No customer names, street addresses, prices, or Jobber URLs.",
            "projects": [],
        }
    return json.loads(PROJECTS_JSON.read_text())


def existing_project_ids(data: dict[str, Any] | None = None) -> set[str]:
    data = data or load_projects()
    return {str(p.get("id")) for p in data.get("projects", []) if p.get("id")}


def categorize_job(title: str) -> str:
    t = (title or "").lower()
    if "drill" in t:
        return "drilling"
    if any(w in t for w in ("tank", "pressure")) and "pump" not in t:
        return "tank"
    if any(w in t for w in ("filter", "treatment", "water quality", "softener")):
        return "water-quality"
    if any(w in t for w in ("maintenance", "inspect", "chlorin")):
        return "maintenance"
    return "pump"


def is_public_safe_title(title: str) -> bool:
    if not title:
        return False
    t = title.strip()
    if JOBBER_URL_RE.search(t) or URL_RE.search(t):
        return False
    if STREET_RE.search(t) or re.search(r"\b\d{3,5}\s+\w+", t):
        return False
    if PRICE_RE.search(t):
        return False
    return bool(PUBLIC_TITLE_RE.search(t))


def sanitize_public_text(text: str, *, fallback: str = "") -> str:
    if not text:
        return fallback
    out = JOBBER_URL_RE.sub("", text)
    out = URL_RE.sub("", out)
    out = EMAIL_RE.sub("", out)
    out = PHONE_RE.sub("", out)
    out = PRICE_RE.sub("", out)
    out = STREET_RE.sub("", out)
    out = LAST_NAME_HINT_RE.sub("", out)
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    out = re.sub(r"\s+,", ",", out)
    out = re.sub(r"\s+\.", ".", out)
    out = out.strip(" \t\n,;-")
    return out or fallback


def slugify(text: str) -> str:
    slug = (text or "").lower()
    slug = re.sub(r"&", " and ", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug[:72] or "job"


def unique_slug(base: str, taken: Iterable[str]) -> str:
    taken_set = set(taken)
    slug = base
    n = 2
    while slug in taken_set:
        slug = f"{base}-{n}"
        n += 1
    return slug


def parse_jobber_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PACIFIC)


def format_date_label(start: datetime | None, end: datetime | None) -> tuple[str, str]:
    day = end or start
    if not day:
        today = datetime.now(PACIFIC).date()
        return today.isoformat(), today.strftime("%B %-d, %Y").replace(" 0", " ")
    date_iso = day.date().isoformat()
    if start and end and start.date() != end.date():
        if start.year == end.year and start.month == end.month:
            label = f"{start.strftime('%B')} {start.day}–{end.day}, {end.year}"
        else:
            label = f"{_mdy(start.date())}–{_mdy(end.date())}"
        return date_iso, label
    return date_iso, _mdy(day.date())


def _mdy(d: date) -> str:
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def public_location(city: str | None) -> str:
    city = sanitize_public_text((city or "").strip())
    if not city:
        return ""
    if "," in city:
        city = city.split(",")[0].strip()
    if STREET_RE.search(city) or re.search(r"\d", city):
        return ""
    return city


def is_image_attachment(name: str, content_type: str) -> bool:
    name = (name or "").lower()
    content_type = (content_type or "").lower()
    if DOC_NAME_RE.search(name) or name.endswith(".pdf"):
        return False
    if content_type.startswith("image/") or content_type in IMAGE_TYPES:
        return True
    suffix = Path(name).suffix.lower()
    return suffix in IMAGE_EXTS


def pick_attachment_url(node: dict[str, Any]) -> str:
    for key in ("url", "fileUrl", "downloadUrl", "publicUrl", "uri"):
        value = node.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    file_obj = node.get("file")
    if isinstance(file_obj, dict):
        return pick_attachment_url(file_obj)
    return ""


def pick_attachment_name(node: dict[str, Any], fallback: str) -> str:
    for key in ("fileName", "filename", "name"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    file_obj = node.get("file")
    if isinstance(file_obj, dict):
        return pick_attachment_name(file_obj, fallback)
    return fallback


def pick_attachment_type(node: dict[str, Any]) -> str:
    for key in ("contentType", "fileType", "mimeType"):
        value = node.get(key)
        if isinstance(value, str):
            return value
    file_obj = node.get("file")
    if isinstance(file_obj, dict):
        return pick_attachment_type(file_obj)
    return ""


def collect_attachments(job: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_nodes(nodes: Any) -> None:
        if not isinstance(nodes, list):
            return
        for i, node in enumerate(nodes, start=1):
            if not isinstance(node, dict):
                continue
            url = pick_attachment_url(node)
            name = pick_attachment_name(node, f"attachment-{i}")
            ctype = pick_attachment_type(node)
            if not url or not is_image_attachment(name, ctype):
                continue
            key = url.split("?", 1)[0]
            if key in seen:
                continue
            seen.add(key)
            found.append({"url": url, "name": name, "contentType": ctype})

    notes = job.get("noteAttachments") or {}
    add_nodes(notes.get("nodes") if isinstance(notes, dict) else notes)
    visits = ((job.get("visits") or {}).get("nodes")) if isinstance(job.get("visits"), dict) else []
    for visit in visits or []:
        if not isinstance(visit, dict):
            continue
        vnotes = visit.get("noteAttachments") or {}
        add_nodes(vnotes.get("nodes") if isinstance(vnotes, dict) else vnotes)
    return found


def job_number(job: dict[str, Any]) -> str:
    number = job.get("jobNumber")
    if number not in (None, ""):
        return str(number)
    encoded = str(job.get("id") or "")
    digits = re.findall(r"\d+", encoded)
    return digits[-1] if digits else "unknown"


def build_project(
    job: dict[str, Any],
    photo_files: list[str],
    *,
    taken_slugs: Iterable[str],
) -> dict[str, Any] | None:
    title = sanitize_public_text((job.get("title") or "").strip())
    if not is_public_safe_title(title):
        return None
    city = public_location(((job.get("property") or {}).get("address") or {}).get("city"))
    if not city:
        return None
    if not photo_files:
        return None

    start = parse_jobber_dt(job.get("startAt"))
    end = parse_jobber_dt(job.get("completedAt") or job.get("endAt"))
    date_iso, date_label = format_date_label(start, end)
    category = categorize_job(title)
    instructions = sanitize_public_text(job.get("instructions") or "")
    if len(instructions) < 40 or not is_public_safe_title(instructions):
        summary = f"{title} completed in {city}."
    else:
        summary = instructions
        if not summary.endswith("."):
            summary += "."
    slug = unique_slug(slugify(f"{city}-{title}"), taken_slugs)
    number = job_number(job)
    photos = [
        {"file": name, "alt": f"{title} in {city}"}
        for name in photo_files
    ]
    return {
        "id": f"job{number}",
        "slug": slug,
        "title": title,
        "location": city,
        "date": date_iso,
        "dateLabel": date_label,
        "category": category,
        "categoryLabel": CATEGORY_LABELS[category],
        "summary": summary,
        "photos": photos,
    }


def merge_projects(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {p["id"]: p for p in existing}
    for project in incoming:
        if project["id"] in by_id:
            continue
        by_id[project["id"]] = project
    return sorted(by_id.values(), key=lambda p: p.get("date") or "", reverse=True)


def dump_projects_json(projects: list[dict[str, Any]]) -> None:
    payload = {
        "generatedFrom": "Jobber completed/archived jobs via scripts/publish-recent-work-from-jobber.py",
        "note": "Public copy only. No customer names, street addresses, prices, or Jobber URLs.",
        "projects": projects,
    }
    PROJECTS_JSON.write_text(json.dumps(payload, indent=2) + "\n")


def dump_projects_js(projects: list[dict[str, Any]]) -> None:
    body = json.dumps(projects, indent=4)
    # Match the existing IIFE style; keep it valid JS.
    PROJECTS_JS.write_text(
        "/**\n"
        " * Curated public recent-work posts.\n"
        " * Generated from recent-work/projects.json. Do not add customer names,\n"
        " * street addresses, prices, or Jobber URLs.\n"
        " */\n"
        "(function (root) {\n"
        f"  root.SCWS_RECENT_WORK = {body};\n"
        "})(window);\n"
    )


def card_html(project: dict[str, Any]) -> str:
    photos = list(project.get("photos") or [])[:3]
    grid = {0: "empty", 1: "single", 2: "double"}.get(len(photos), "triple")
    img_bits = []
    for photo in photos:
        src = f"../images/recent-work/{photo['file']}"
        alt = html.escape(photo.get("alt") or project["title"], quote=True)
        img_bits.append(
            f'<img src="{src}" alt="{alt}" width="800" height="450" loading="lazy" '
            f'onclick="openLightbox(\'{src}\')" style="cursor:pointer">'
        )
    photos_html = "\n".join(img_bits)
    title = html.escape(project["title"])
    location = html.escape(project["location"])
    summary = html.escape(project["summary"])
    slug = html.escape(project["slug"])
    return (
        f'<article class="project-card" data-category="{html.escape(project["category"])}" '
        f'data-static="1" data-job="{html.escape(project["id"])}">\n'
        f'<div class="project-photos {grid}">\n'
        f"{photos_html}\n"
        f"</div>\n"
        f'<div class="p-4">\n'
        f'<div class="flex items-center justify-between mb-2 gap-2">\n'
        f'<span class="service-badge">{html.escape(project["categoryLabel"])}</span>\n'
        f'<time class="text-xs text-gray-400" datetime="{html.escape(project["date"])}">'
        f'{html.escape(project["dateLabel"])}</time>\n'
        f"</div>\n"
        f'<h3 class="font-semibold text-gray-900 mb-1">'
        f'<a class="hover:text-accent" href="{slug}.html">{title}</a></h3>\n'
        f'<p class="text-sm text-gray-500 mb-2">📍 {location}</p>\n'
        f'<p class="text-sm text-gray-600 leading-relaxed">{summary}</p>\n'
        f'<p class="mt-3"><a class="text-accent text-sm font-semibold hover:underline" '
        f'href="{slug}.html">View project →</a></p>\n'
        f"</div>\n"
        f"</article>"
    )


def jsonld_items(projects: list[dict[str, Any]]) -> str:
    items = []
    for i, project in enumerate(projects, start=1):
        name = f"{project['title']} — {project['location']}"
        items.append(
            {
                "@type": "ListItem",
                "position": i,
                "url": f"https://scwellservice.com/recent-work/{project['slug']}.html",
                "name": name,
            }
        )
    dumped = json.dumps(items, indent=16)
    # Keep the existing indent style inside the script tag.
    dumped = dumped.replace("\n", "\n                ")
    return (
        f'"numberOfItems": {len(projects)},\n'
        f'            "itemListElement": {dumped}'
    )


def update_index_html(projects: list[dict[str, Any]]) -> None:
    text = INDEX_HTML.read_text()
    start, end = CARD_MARKERS
    if start not in text or end not in text:
        raise RuntimeError(
            f"{INDEX_HTML} is missing {start} / {end} markers. "
            "Add them around the #projects-grid cards."
        )
    cards = "\n".join(card_html(p) for p in projects)
    block = f"{start}\n{cards}\n{end}"
    text = re.sub(
        re.escape(start) + r".*?" + re.escape(end),
        lambda _: block,
        text,
        count=1,
        flags=re.S,
    )
    replacement = jsonld_items(projects)
    if not JSONLD_ITEMLIST_RE.search(text):
        raise RuntimeError("Could not find JSON-LD item list in recent-work/index.html")
    text = JSONLD_ITEMLIST_RE.sub(lambda _: replacement, text, count=1)
    INDEX_HTML.write_text(text)


def update_sitemap(projects: list[dict[str, Any]]) -> None:
    if not SITEMAP_PAGES.exists():
        return
    xml = SITEMAP_PAGES.read_text()
    today = date.today().isoformat()
    existing = set(re.findall(r"<loc>(https://scwellservice\.com/recent-work/[^<]+)</loc>", xml))
    additions = []
    index_url = "https://scwellservice.com/recent-work/"
    if index_url not in existing:
        additions.append(
            f"  <url><loc>{index_url}</loc><lastmod>{today}</lastmod><priority>0.6</priority></url>\n"
        )
    for project in projects:
        url = f"https://scwellservice.com/recent-work/{project['slug']}.html"
        if url in existing:
            continue
        additions.append(
            f"  <url><loc>{url}</loc><lastmod>{today}</lastmod><priority>0.5</priority></url>\n"
        )
    if not additions:
        return
    xml = xml.replace("</urlset>", "".join(additions) + "</urlset>")
    SITEMAP_PAGES.write_text(xml)


def write_site_files(projects: list[dict[str, Any]]) -> None:
    dump_projects_json(projects)
    dump_projects_js(projects)
    update_index_html(projects)
    update_sitemap(projects)
