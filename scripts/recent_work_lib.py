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
PAGINATION_MARKERS = (
    "<!-- RECENT_WORK_PAGINATION_START -->",
    "<!-- RECENT_WORK_PAGINATION_END -->",
)
JSONLD_ITEMLIST_RE = re.compile(
    r'"numberOfItems":\s*\d+\s*,\s*"itemListElement":\s*\[.*?\]',
    re.S,
)
PAGE_SIZE = 24
CANONICAL_RE = re.compile(
    r'<link href="https://scwellservice\.com/recent-work/[^"]*" rel="canonical"/>'
)
OG_URL_RE = re.compile(
    r'<meta content="https://scwellservice\.com/recent-work/[^"]*" property="og:url"/>'
)
TITLE_RE = re.compile(r"<title>[^<]*</title>")
OG_TITLE_RE = re.compile(r'<meta content="[^"]*" property="og:title"/>')
PAGINATION_LINK_RE = re.compile(r'<link rel="(?:prev|next)" href="[^"]*"/>\n?')

CATEGORY_SERVICE_PAGES = {
    "pump": ("/pages/services/pump-repair.html", "pump repair"),
    "drilling": ("/pages/services/well-drilling.html", "well drilling"),
    "tank": ("/pages/services/pump-repair.html", "pressure tank"),
    "water-quality": ("/pages/services/water-testing.html", "water testing"),
    "maintenance": ("/pages/services/maintenance.html", "maintenance"),
}

SERVICE_PAGE_MATCHERS = {
    "pump-repair": {"pump", "tank"},
    "emergency-well-service": {"pump", "maintenance"},
    "well-drilling": {"drilling"},
    "maintenance": {"maintenance"},
}

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


def job_h1(project: dict[str, Any]) -> str:
    title = (project.get("title") or "").strip()
    location = (project.get("location") or "").strip()
    if not location:
        return title
    if location.lower() in title.lower():
        return title
    return f"{title} in {location}"


def trim_meta_description(text: str, limit: int = 158) -> str:
    """Word-boundary trim to ~150–160 chars. Avoid cutting on inch marks."""
    raw = (text or "").replace("\n", " ").strip()
    raw = raw.replace('"', " inch")
    raw = re.sub(r"\s+", " ", raw)
    if len(raw) <= limit:
        return raw
    cut = raw[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    cut = cut.rstrip(" ,;:-")
    if cut.endswith("."):
        return cut
    return cut + "."


def city_slug_from_location(location: str) -> str:
    loc = (location or "").strip()
    area = re.search(r"\(([^)]+?)(?:\s+area)?\)", loc)
    if area:
        area_slug = slugify(area.group(1))
        if (ROOT / "services" / area_slug / "index.html").exists():
            return area_slug
    city = re.sub(r"\s*\([^)]*\)\s*", "", loc).split(",")[0].strip()
    return slugify(city)


def city_service_href(location: str) -> str | None:
    slug = city_slug_from_location(location)
    if not slug:
        return None
    if (ROOT / "services" / slug / "index.html").exists():
        return f"/services/{slug}/"
    return None


def service_page_href(project: dict[str, Any]) -> tuple[str, str] | None:
    category = project.get("category") or ""
    pair = CATEGORY_SERVICE_PAGES.get(category)
    if not pair:
        return None
    href, label = pair
    if (ROOT / href.lstrip("/")).exists():
        return href, label
    return None


# Curated money-page cards: real published jobs only. City-only location
# on the card (strip "Hanson Lane area" / street parentheticals).
MONEY_PAGE_SLUGS = {
    "services/ramona/index.html": [
        "ramona-pressure-switch-gauge-replacement",
        "ramona-control-panel-contactor-replacement",
        "ramona-two-well-system-evaluation",
        "ramona-pressure-switch-replacement",
        "el-cajon-well-contactor-replacement",
        "alpine-pull-and-replace-deep-set-pump",
    ],
    "services/anza/index.html": [
        "anza-pull-and-inspect-pump",
        "anza-well-diagnostic",
        "anza-storage-tank-float-inspection",
        "anza-control-box-service",
        "aguanga-pump-installation",
        "aguanga-low-yield-well-diagnostic",
    ],
    "pages/services/pump-repair.html": [
        "anza-pull-and-inspect-pump",
        "ramona-cathedral-pump-replacement",
        "murrieta-vfd-controller-replacement",
        "aguanga-pump-installation",
        "fallbrook-booster-pump-diagnostic",
        "alpine-pull-and-replace-deep-set-pump",
    ],
    "pages/services/well-drilling.html": [
        "jamul-well-production-test",
        "aguanga-low-yield-well-diagnostic",
        "santa-ysabel-well-bail-and-brush",
        "ramona-two-well-system-evaluation",
        "temecula-pull-30-hp-pump-and-motor",
        "alpine-pull-and-replace-deep-set-pump",
    ],
}

MONEY_PAGE_HEADINGS = {
    "services/ramona/index.html": (
        "Recent jobs in Ramona",
        "Real Ramona and west San Diego jobs. Real photos.",
    ),
    "services/anza/index.html": (
        "Recent jobs in Anza",
        "Real Anza and high-desert jobs. Real photos.",
    ),
    "pages/services/pump-repair.html": (
        "Recent pump jobs",
        "Real pump, motor, and pressure jobs. Real photos.",
    ),
    "pages/services/well-drilling.html": (
        "Recent well jobs",
        "Real field work on wells we already service. New-drill cards publish here when those jobs do.",
    ),
}

RECENT_JOBS_SECTION_RE = re.compile(
    r'<section\b[^>]*(?:id=["\']recent-jobs["\']|class=["\'][^"\']*recent-jobs)[^>]*>.*?</section>\s*',
    re.I | re.S,
)
MONEY_CARD_MARKERS = (
    "<!-- MONEY_PAGE_RECENT_WORK_START -->",
    "<!-- MONEY_PAGE_RECENT_WORK_END -->",
)


def card_city_only(location: str) -> str:
    """Public card location: city/area name only, no street parentheticals."""
    loc = (location or "").strip()
    loc = re.sub(r"\s*\([^)]*\)\s*", "", loc)
    return loc.split(",")[0].strip()


def projects_by_slugs(
    projects: list[dict[str, Any]], slugs: list[str]
) -> list[dict[str, Any]]:
    by_slug = {str(p.get("slug")): p for p in projects if p.get("slug")}
    out: list[dict[str, Any]] = []
    for slug in slugs:
        project = by_slug.get(slug)
        if not project:
            continue
        photos = [ph for ph in (project.get("photos") or []) if ph.get("file")]
        if not photos:
            continue
        photo_path = PHOTO_DIR / photos[0]["file"]
        if not photo_path.is_file():
            continue
        out.append(project)
    return out


def money_page_card_html(project: dict[str, Any]) -> str:
    photos = list(project.get("photos") or [])
    photo = photos[0] if photos else {}
    file_name = photo.get("file") or ""
    title = (project.get("title") or "").strip()
    city = card_city_only(project.get("location") or "")
    # City-only alt. Do not reuse photo alts that name a street or area.
    alt = f"{title} in {city}" if city else title
    slug = html.escape(project["slug"])
    return (
        f'<a class="recent-work-card" href="/recent-work/{slug}.html">\n'
        f'<img src="/images/recent-work/{html.escape(file_name)}" '
        f'alt="{html.escape(alt, quote=True)}" width="800" height="450" loading="lazy">\n'
        f'<div class="rw-body">\n'
        f"<h3>{html.escape(title)}</h3>\n"
        f"<p>{html.escape(city)}</p>\n"
        f"</div>\n"
        f"</a>"
    )


def money_page_section_html(
    projects: list[dict[str, Any]], heading: str, lede: str
) -> str:
    cards = "\n".join(money_page_card_html(p) for p in projects)
    start, end = MONEY_CARD_MARKERS
    return (
        f"{start}\n"
        f'<section class="recent-jobs-cards" id="recent-jobs">\n'
        f"<h2>{html.escape(heading)}</h2>\n"
        f'<p class="rw-lede">{html.escape(lede)}</p>\n'
        f'<div class="recent-work-grid">\n'
        f"{cards}\n"
        f"</div>\n"
        f'<p class="rw-all"><a href="/recent-work/">See all recent work →</a></p>\n'
        f"</section>\n"
        f"{end}\n"
    )


def replace_recent_jobs_section(text: str, block: str) -> str:
    start, end = MONEY_CARD_MARKERS
    if start in text and end in text:
        return re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            lambda _: block.rstrip() + "\n",
            text,
            count=1,
            flags=re.S,
        )
    if RECENT_JOBS_SECTION_RE.search(text):
        return RECENT_JOBS_SECTION_RE.sub(block, text, count=1)
    match = re.search(r"<footer\b", text, re.I)
    if match:
        return text[: match.start()] + block + text[match.start()]
    return text + block


def apply_money_page_recent_work(
    projects: list[dict[str, Any]] | None = None,
) -> list[Path]:
    """Wire homepage-style photo cards onto the four money pages."""
    projects = projects if projects is not None else load_projects().get("projects", [])
    changed: list[Path] = []
    for rel, slugs in MONEY_PAGE_SLUGS.items():
        path = ROOT / rel
        if not path.is_file():
            continue
        hits = projects_by_slugs(projects, slugs)
        if len(hits) < 3:
            raise RuntimeError(f"{rel} has only {len(hits)} real photo jobs")
        heading, lede = MONEY_PAGE_HEADINGS[rel]
        block = money_page_section_html(hits, heading, lede)
        original = path.read_text(encoding="utf-8")
        updated = replace_recent_jobs_section(original, block)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def projects_for_city(projects: list[dict[str, Any]], city: str, limit: int = 6) -> list[dict[str, Any]]:
    city_l = city.lower()
    hits = [p for p in projects if city_l in (p.get("location") or "").lower()]
    return hits[:limit]


def projects_for_service(projects: list[dict[str, Any]], service_key: str, limit: int = 6) -> list[dict[str, Any]]:
    cats = SERVICE_PAGE_MATCHERS.get(service_key, {service_key})
    hits = [p for p in projects if p.get("category") in cats]
    if service_key == "well-drilling":
        wellish = [
            p
            for p in projects
            if re.search(
                r"drill|deepen|bail|brush|deep-set|well production|well diagnostic|pull well",
                p.get("title") or "",
                re.I,
            )
        ]
        hits = wellish or hits
    if service_key == "emergency-well-service":
        emergencyish = [
            p
            for p in projects
            if re.search(r"diagnostic|emergency|no water|not producing|fault|overload", p.get("title") or "", re.I)
        ]
        # Prefer diagnostic/emergency titles, then the category matches.
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()
        for p in emergencyish + hits:
            if p["id"] in seen:
                continue
            seen.add(p["id"])
            merged.append(p)
        hits = merged
    return hits[:limit]


def paginate_projects(projects: list[dict[str, Any]], size: int = PAGE_SIZE) -> list[list[dict[str, Any]]]:
    if not projects:
        return [[]]
    return [projects[i : i + size] for i in range(0, len(projects), size)]


def listing_page_href(page_num: int) -> str:
    return "./" if page_num <= 1 else f"page-{page_num}.html"


def pagination_html(page_num: int, total_pages: int) -> str:
    if total_pages <= 1:
        return ""
    bits = ['<nav class="recent-work-pagination" aria-label="Recent work pages">']
    if page_num > 1:
        bits.append(f'<a class="page-link" href="{listing_page_href(page_num - 1)}">← Previous</a>')
    for i in range(1, total_pages + 1):
        href = listing_page_href(i)
        if i == page_num:
            bits.append(f'<span class="page-link current" aria-current="page">{i}</span>')
        else:
            bits.append(f'<a class="page-link" href="{href}">{i}</a>')
    if page_num < total_pages:
        bits.append(f'<a class="page-link" href="{listing_page_href(page_num + 1)}">Next →</a>')
    bits.append("</nav>")
    return "\n".join(bits)


def _replace_cards(text: str, projects_page: list[dict[str, Any]]) -> str:
    start, end = CARD_MARKERS
    cards = "\n".join(card_html(p) for p in projects_page)
    block = f"{start}\n{cards}\n{end}"
    return re.sub(
        re.escape(start) + r".*?" + re.escape(end),
        lambda _: block,
        text,
        count=1,
        flags=re.S,
    )


def _replace_pagination(text: str, page_num: int, total_pages: int) -> str:
    start, end = PAGINATION_MARKERS
    nav = pagination_html(page_num, total_pages)
    block = f"{start}\n{nav}\n{end}"
    if start in text and end in text:
        return re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            lambda _: block,
            text,
            count=1,
            flags=re.S,
        )
    # First run: insert after the projects grid.
    insert = (
        "</div>\n"
        f"{block}\n"
        '<p class="live-feed-note hidden" id="live-feed-note"></p>'
    )
    if '<p class="live-feed-note hidden" id="live-feed-note"></p>' in text:
        return text.replace(
            '<p class="live-feed-note hidden" id="live-feed-note"></p>',
            insert[len("</div>\n") :],
            1,
        )
    return text.replace(CARD_MARKERS[1], f"{CARD_MARKERS[1]}\n{block}", 1)


def _set_listing_head(text: str, page_num: int, total_pages: int) -> str:
    if page_num <= 1:
        canonical = "https://scwellservice.com/recent-work/"
        title = "Recent Work &amp; Projects | Southern California Well Service"
    else:
        canonical = f"https://scwellservice.com/recent-work/page-{page_num}.html"
        title = f"Recent Work &amp; Projects — Page {page_num} | Southern California Well Service"
    if CANONICAL_RE.search(text):
        text = CANONICAL_RE.sub(f'<link href="{canonical}" rel="canonical"/>', text, count=1)
    if OG_URL_RE.search(text):
        text = OG_URL_RE.sub(
            f'<meta content="{canonical}" property="og:url"/>',
            text,
            count=1,
        )
    if TITLE_RE.search(text):
        text = TITLE_RE.sub(f"<title>{title}</title>", text, count=1)
    if OG_TITLE_RE.search(text):
        text = OG_TITLE_RE.sub(
            f'<meta content="{title}" property="og:title"/>',
            text,
            count=1,
        )
    text = PAGINATION_LINK_RE.sub("", text)
    links = ""
    if page_num > 1:
        prev = "https://scwellservice.com/recent-work/" if page_num == 2 else (
            f"https://scwellservice.com/recent-work/page-{page_num - 1}.html"
        )
        links += f'<link rel="prev" href="{prev}"/>\n'
    if page_num < total_pages:
        nxt = f"https://scwellservice.com/recent-work/page-{page_num + 1}.html"
        links += f'<link rel="next" href="{nxt}"/>\n'
    if links:
        text = text.replace(
            f'<link href="{canonical}" rel="canonical"/>',
            f'<link href="{canonical}" rel="canonical"/>\n{links.rstrip()}',
            1,
        )
    return text


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
    pages = paginate_projects(projects)
    total_pages = len(pages)
    replacement = jsonld_items(projects)
    if not JSONLD_ITEMLIST_RE.search(text):
        raise RuntimeError("Could not find JSON-LD item list in recent-work/index.html")

    page1 = _replace_cards(text, pages[0])
    page1 = _replace_pagination(page1, 1, total_pages)
    page1 = _set_listing_head(page1, 1, total_pages)
    page1 = JSONLD_ITEMLIST_RE.sub(lambda _: replacement, page1, count=1)
    INDEX_HTML.write_text(page1)

    out_dir = INDEX_HTML.parent
    stale = {
        p
        for p in out_dir.glob("page-*.html")
        if re.fullmatch(r"page-\d+\.html", p.name)
    }
    for page_num, chunk in enumerate(pages[1:], start=2):
        page = _replace_cards(page1, chunk)
        page = _replace_pagination(page, page_num, total_pages)
        page = _set_listing_head(page, page_num, total_pages)
        page = JSONLD_ITEMLIST_RE.sub(lambda _: jsonld_items(chunk), page, count=1)
        dest = out_dir / f"page-{page_num}.html"
        dest.write_text(page)
        stale.discard(dest)
    for leftover in stale:
        leftover.unlink()


def update_sitemap(projects: list[dict[str, Any]]) -> None:
    if not SITEMAP_PAGES.exists():
        return
    xml = SITEMAP_PAGES.read_text()
    today = date.today().isoformat()
    existing = set(re.findall(r"<loc>(https://scwellservice\.com/recent-work/[^<]+)</loc>", xml))
    additions = []
    wanted = ["https://scwellservice.com/recent-work/"]
    total_pages = max(1, (len(projects) + PAGE_SIZE - 1) // PAGE_SIZE)
    for page_num in range(2, total_pages + 1):
        wanted.append(f"https://scwellservice.com/recent-work/page-{page_num}.html")
    for project in projects:
        wanted.append(f"https://scwellservice.com/recent-work/{project['slug']}.html")
    for url in wanted:
        if url in existing:
            continue
        priority = "0.6" if url.rstrip("/").endswith("recent-work") or "/page-" in url else "0.5"
        additions.append(
            f"  <url><loc>{url}</loc><lastmod>{today}</lastmod><priority>{priority}</priority></url>\n"
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
