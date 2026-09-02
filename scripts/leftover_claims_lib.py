#!/usr/bin/env python3
"""Leftover CSLB / company-age / 4.9 / permit-city noindex cleanup.

Canonical facts (do not invent new ones):
- CSLB is #1086994 (C-57) only.
- SCWS founded 2020 by Brighton Scala and Travis Sego.
- Acquired shops support "60+ Years Family Heritage" — not SCWS company age.
- Keep Joe Fain. Keep well-age / equipment-age / city-incorporation dates.
- Do not call the Yelp 20-year highlight fake.
"""
from __future__ import annotations

import re
from pathlib import Path

CANONICAL_CSLB = "1086994"
CANONICAL_CSLB_HASH = f"#{CANONICAL_CSLB}"

# Never publish these as the SCWS license.
LEFTOVER_LICENSE_NUMBERS = (
    "1059498",
    "1129498",
    "1013597",
    "1115134",
    "1129130",
    "1124498",
    "1120029",
    "1098473",
    "1098422",
)

PERMIT_GUIDE_KEEP = {
    "well-permit-guide-san-diego.html",
    "well-permit-requirements-san-diego.html",
    "well-permit-denial-appeals.html",
    "well-permit-inspection-requirements.html",
    "well-permit-vs-replace.html",
    "well-permit-statistics-by-state.html",
    "well-permits-california.html",
    "well-permits-san-diego-county.html",
}

PERMIT_CITY_CANONICAL = "https://scwellservice.com/blog/well-permits-california.html"

SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "data",
    "recent-work",
    "_internal",
    "_photo_b64",
    "images",
    "assets",
    "videos",
    "downloads",
}

SKIP_SUFFIXES = {
    ".csv",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".pdf",
    ".woff",
    ".woff2",
    ".mp4",
    ".ico",
}

# well_data.json and DWR dumps stay untouched even if they sit outside data/.
SKIP_FILE_NAMES = {
    "well_data.json",
    "well_logs.csv",
}

_LEFTOVER_NUMS = "|".join(LEFTOVER_LICENSE_NUMBERS)
LICENSE_TOKEN_RE = re.compile(
    rf"(?:License|CSLB|license)\s*#\s*(?:{_LEFTOVER_NUMS})|#\s*(?:{_LEFTOVER_NUMS})",
    re.IGNORECASE,
)

CONCAT_LICENSE_RE = re.compile(
    rf"#1086994\s*[.#]\s*#?(?:{_LEFTOVER_NUMS})"
)

ROBOTS_NOINDEX_RE = re.compile(
    r"<meta\b[^>]*(?:name=[\"']robots[\"'][^>]*content=[\"'][^\"']*noindex|content=[\"'][^\"']*noindex[^\"']*[\"'][^>]*name=[\"']robots[\"'])",
    re.I,
)

CANONICAL_HREF_RE = re.compile(
    r"""(<link\b[^>]*rel=["']canonical["'][^>]*href=["'])([^"']+)(["'][^>]*>)|(<link\b[^>]*href=["'])([^"']+)(["'][^>]*rel=["']canonical["'][^>]*>)""",
    re.I,
)


def is_programmatic_well_permit(name: str) -> bool:
    if name in PERMIT_GUIDE_KEEP:
        return False
    return name.startswith("well-permit-") and name.endswith(".html")


def should_skip_path(path: Path) -> bool:
    if any(part in SKIP_DIR_NAMES for part in path.parts):
        return True
    if path.name in SKIP_FILE_NAMES:
        return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def replace_leftover_licenses(text: str) -> str:
    text = CONCAT_LICENSE_RE.sub(CANONICAL_CSLB_HASH, text)
    text = LICENSE_TOKEN_RE.sub(lambda m: _license_replacement(m.group(0)), text)
    # Bare leftover numbers next to License/CSLB already handled.
    # Catch remaining "#NNNNNNN" leftovers that lost their prefix during concat cleanup.
    for num in LEFTOVER_LICENSE_NUMBERS:
        text = re.sub(rf"#\s*{num}\b", CANONICAL_CSLB_HASH, text)
    return text


def _license_replacement(match: str) -> str:
    if re.search(r"license|cslb", match, re.I):
        prefix = re.match(r"(License|CSLB|license)\s*#\s*", match)
        if prefix:
            return f"{prefix.group(1)} {CANONICAL_CSLB_HASH}"
    return CANONICAL_CSLB_HASH


def replace_company_age_claims(text: str) -> str:
    """Rewrite leftover SCWS company-age claims. Leave well/equipment/city dates."""
    replacements = [
        (
            "with more than 30 years of experience and a 4.9-star reputation across",
            "(CSLB #1086994), founded in 2020, with 60+ years of family heritage across",
        ),
        (
            "with more than 30 years of work across",
            "(CSLB #1086994) serving",
        ),
        (
            "with more than 30 years serving",
            "(CSLB #1086994) serving",
        ),
        (
            "with more than 30 years of experience in",
            "(CSLB #1086994) serving",
        ),
        (
            "has been pulling these permits for property owners across the county for more than 30 years",
            "has been pulling these permits for property owners across the county since 2020",
        ),
        (
            "has been handling these permits for property owners across the county for more than 30 years",
            "has been handling these permits for property owners across the county since 2020",
        ),
        (
            "has handled these permits for property owners across the county for more than 30 years",
            "has handled these permits for property owners across the county since 2020",
        ),
        (
            "With more than 30 years drilling across the county",
            "Working across the county since 2020",
        ),
        (
            "has provided emergency well pump repair to San Diego County families for over 30 years",
            "has provided emergency well pump repair to San Diego County families since 2020",
        ),
        (
            "For over 30 years, San Diego County families have trusted Southern California Well Service",
            "Since 2020, San Diego County families have trusted Southern California Well Service",
        ),
        (
            "has over 40 years of experience drilling wells",
            "drills wells with 60+ years of family heritage",
        ),
        (
            "Professional well drilling and service since 1985",
            "Professional well drilling and service. Founded 2020; 60+ years family heritage",
        ),
        (
            "Serving San Diego and Riverside Counties since 1996",
            "Serving San Diego and Riverside Counties since 2020",
        ),
        (
            "FAMILY OWNED SINCE 2008",
            "FOUNDED 2020 · 60+ YEARS FAMILY HERITAGE",
        ),
        (
            "Family Owned Since 2008",
            "Founded 2020 · 60+ Years Family Heritage",
        ),
        (
            "we've responded to every major wildfire in our service area since 2007",
            "we respond to post-wildfire well emergencies across our service area",
        ),
        (
            "with 30+ years of high-desert well experience",
            "founded in 2020, with 60+ years of family heritage in high-desert well work",
        ),
        (
            "30+ years of experience",
            "founded in 2020, with 60+ years of family heritage",
        ),
        (
            ", 30+ years,",
            ", founded 2020,",
        ),
        (
            "Licensed C-57, 30+ years,",
            "Licensed C-57 (CSLB #1086994), founded 2020,",
        ),
        (
            "a 4.9-star reputation built over three decades of local well work",
            "CSLB #1086994 and 60+ years of family heritage",
        ),
        (
            "a 4.9-star reputation built on three decades of local well work",
            "CSLB #1086994 and 60+ years of family heritage",
        ),
        (
            "a 4.9-star reputation earned over three decades",
            "CSLB #1086994 and 60+ years of family heritage",
        ),
        (
            "a 4.9-star reputation built over three decades",
            "CSLB #1086994 and 60+ years of family heritage",
        ),
        (
            "4.9-star reputation built over three decades",
            "CSLB #1086994 and 60+ years of family heritage",
        ),
        (
            "SCWS has been drilling and servicing water wells in San Diego County for over 30 years.",
            "SCWS has been drilling and servicing water wells in San Diego County since 2020.",
        ),
        (
            "has spent more than 30 years",
            "has worked since 2020",
        ),
        (
            "has worked these high-desert wells for more than 30 years",
            "has worked these high-desert wells since 2020",
        ),
        (
            "With over 30 years of experience and a 4.9-star Google rating",
            "Founded in 2020, with 60+ years of family heritage",
        ),
        (
            "With over 30 years of experience",
            "Founded in 2020, with 60+ years of family heritage",
        ),
        (
            "with more than 30 years of experience and,",
            "founded in 2020, with 60+ years of family heritage,",
        ),
        (
            "with more than 30 years of experience",
            "founded in 2020, with 60+ years of family heritage",
        ),
        (
            "With more than 30 years of well experience and,",
            "Founded in 2020, with 60+ years of family heritage,",
        ),
        (
            "With more than 30 years of well experience",
            "Founded in 2020, with 60+ years of family heritage",
        ),
        (
            "With more than 30 years of experience",
            "Founded in 2020, with 60+ years of family heritage",
        ),
        (
            "with over 30 years of high-desert experience and a 4.9-star rating",
            "founded in 2020, with 60+ years of family heritage",
        ),
        (
            "with over 30 years of experience and,",
            "founded in 2020, with 60+ years of family heritage,",
        ),
        (
            "with over 30 years of experience",
            "founded in 2020, with 60+ years of family heritage",
        ),
        (
            "brings more than 30 years of high-desert experience",
            "brings 60+ years of family heritage in high-desert well work",
        ),
        (
            "over 30 years of high-desert experience",
            "60+ years of family heritage in high-desert well work",
        ),
        (
            "we have spent more than 30 years",
            "we have, since 2020,",
        ),
        (
            "We have spent more than 30 years",
            "Since 2020, we have",
        ),
        (
            "licensed C-57 well contractor, licensed C-57 (CSLB #1086994) by the well owners we serve",
            "licensed C-57 well contractor (CSLB #1086994) trusted by the well owners we serve",
        ),
        (
            "30+ years serving",
            "Founded 2020, serving",
        ),
        (
            "more than 30 years serving",
            "serving since 2020",
        ),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    text = re.sub(
        r"(Serving [^.<]{0,100}?) for over 30 years",
        r"\1 since 2020",
        text,
    )
    text = re.sub(
        r"(Serving [^.<]{0,100}?) for more than 30 years",
        r"\1 since 2020",
        text,
    )

    # Remaining leftover "since 2008" as SCWS service claim (not city incorporation).
    text = re.sub(
        r"(Southern California Well Service</strong> has been (?:repairing pumps|serving|working)[^.]{0,160}?) since 2008",
        r"\1 since 2020",
        text,
    )
    text = re.sub(
        r"(has been repairing (?:well )?pumps in (?:San Diego and Riverside County|[^.]{0,80}?)) since 2008",
        r"\1 since 2020",
        text,
    )
    text = re.sub(
        r"(Serving [^.<]{0,80}?) since 2008(?!</)",
        r"\1 since 2020",
        text,
    )
    return text


def replace_fake_rating_lines(text: str) -> str:
    """Drop leftover 4.9-star marketing lines. Do not invent a new combined count."""
    replacements = [
        (
            "Licensed C-57 contractor with 4.9★ rating.",
            "Licensed C-57 contractor (CSLB #1086994).",
        ),
        (
            "Licensed C-57 contractor with 4.9★ rating",
            "Licensed C-57 contractor (CSLB #1086994)",
        ),
        (
            "4.9★ rating, hundreds of reviews",
            "CSLB #1086994 · founded 2020",
        ),
        (
            ", 4.9-star rated,",
            ",",
        ),
        (
            ", 4.9-star rated",
            "",
        ),
        (
            "4.9-star rated, ",
            "",
        ),
        (
            "a 4.9-star rating, and ",
            "",
        ),
        (
            " a 4.9-star rating,",
            ",",
        ),
        (
            " and a 4.9-star reputation",
            "",
        ),
        (
            "4.9-star rated",
            "licensed C-57 (CSLB #1086994)",
        ),
        (
            "4.9★ Google Rating",
            "Licensed C-57 · CSLB #1086994",
        ),
        (
            " and a 4.9-star Google rating",
            "",
        ),
        (
            "a 4.9-star Google rating",
            "CSLB #1086994",
        ),
        (
            "4.9-star Google rating",
            "CSLB #1086994",
        ),
        (
            "rated 4.9 stars",
            "licensed C-57 (CSLB #1086994)",
        ),
        (
            " and a 4.9-star rating",
            "",
        ),
        (
            "a 4.9-star rating",
            "CSLB #1086994",
        ),
        (
            "4.9-star rating",
            "CSLB #1086994",
        ),
        (
            ", 4.9 stars,",
            ",",
        ),
        (
            ", 4.9 stars.",
            ".",
        ),
        (
            " 4.9 stars.",
            ".",
        ),
        (
            " 4.9 stars,",
            ",",
        ),
        (
            " 4.9 stars",
            "",
        ),
        (
            " | <strong>Rating:</strong> 4.9★ on Google",
            "",
        ),
        (
            "4.9★ on Google",
            "CSLB #1086994",
        ),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    text = re.sub(r"heritage and,\s+", "heritage, ", text)
    text = re.sub(r"experience and,\s+", "experience, ", text)
    return text


def ensure_permit_city_noindex(text: str) -> str:
    if ROBOTS_NOINDEX_RE.search(text):
        return text
    robots = '<meta name="robots" content="noindex, follow">\n'
    if re.search(r"</head>", text, re.I):
        return re.sub(r"</head>", robots + "</head>", text, count=1, flags=re.I)
    return robots + text


def retarget_permit_city_canonical(text: str) -> str:
    """Stop advertising thin city clones as their own indexable URL."""

    def _sub(match: re.Match[str]) -> str:
        if match.group(1):
            return f"{match.group(1)}{PERMIT_CITY_CANONICAL}{match.group(3)}"
        return f"{match.group(4)}{PERMIT_CITY_CANONICAL}{match.group(6)}"

    if CANONICAL_HREF_RE.search(text):
        return CANONICAL_HREF_RE.sub(_sub, text, count=1)
    # Insert a canonical if the thin clone never had one.
    tag = f'<link href="{PERMIT_CITY_CANONICAL}" rel="canonical"/>\n'
    if re.search(r"</head>", text, re.I):
        return re.sub(r"</head>", tag + "</head>", text, count=1, flags=re.I)
    return text


def ensure_permit_city_cslb(text: str) -> str:
    text = text.replace(
        "Licensed C-57 Water Well Drilling Contractor serving San Diego, Riverside, and San Bernardino Counties.",
        "Licensed C-57 (CSLB #1086994) Water Well Drilling Contractor serving San Diego, Riverside, and San Bernardino Counties.",
    )
    text = text.replace(
        "As a licensed California C-57 Water Well Drilling Contractor, we manage all permit requirements",
        "As a licensed California C-57 Water Well Drilling Contractor (CSLB #1086994), we manage all permit requirements",
    )
    text = re.sub(
        r"© 2025 Southern California Well Service\. All rights reserved\.",
        "© 2026 Southern California Well Service. CSLB #1086994. All rights reserved.",
        text,
    )
    if "1086994" not in text:
        text = text.replace(
            "Licensed C-57 Water Well Drilling Contractor",
            "Licensed C-57 (CSLB #1086994) Water Well Drilling Contractor",
        )
    return text


def process_html_text(text: str, filename: str) -> str:
    text = replace_leftover_licenses(text)
    text = replace_company_age_claims(text)
    text = replace_fake_rating_lines(text)
    if is_programmatic_well_permit(filename):
        text = ensure_permit_city_noindex(text)
        text = retarget_permit_city_canonical(text)
        text = ensure_permit_city_cslb(text)
    return text


def is_claim_file(path: Path) -> bool:
    """Age/4.9 rewrites stay on blog templates + leftover landing/generator copy."""
    if path.suffix.lower() not in {".html", ".js"}:
        return False
    rel = path.as_posix()
    if "/blog/" in rel or rel.startswith("blog/"):
        return True
    if path.name in {
        "emergency.html",
        "pump-repair.html",
        "expand-cities.js",
        "generate-city-pages.js",
    }:
        return True
    if "/pages/landing/" in rel:
        return True
    return False


def process_file(path: Path) -> bool:
    if should_skip_path(path):
        return False
    if path.suffix.lower() not in {".html", ".js", ".md"}:
        return False
    try:
        original = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    if is_claim_file(path):
        text = process_html_text(original, path.name)
    else:
        text = replace_leftover_licenses(original)
    if text == original:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def walk_and_fix(root: Path) -> list[Path]:
    changed: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if process_file(path):
            changed.append(path)
    return changed
