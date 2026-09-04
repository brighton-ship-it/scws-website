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
    rf"(?:License|CSLB|license)(?:\s*#|\s+number)\s*(?:{_LEFTOVER_NUMS})|#\s*(?:{_LEFTOVER_NUMS})",
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
    if re.search(r"license number", match, re.I):
        return f"license number {CANONICAL_CSLB}"
    if re.search(r"license|cslb", match, re.I):
        prefix = re.match(r"(License|CSLB|license)\s*#\s*", match)
        if prefix:
            return f"{prefix.group(1)} {CANONICAL_CSLB_HASH}"
    return CANONICAL_CSLB_HASH


# Company-age leftovers that must NEVER be rewritten (well/equipment/city facts).
KEEP_AGE_NEAR_RE = re.compile(
    r"(?i)(?:"
    r"wells?\s+(?:over|more than)\s+\d|"
    r"wells?\s+(?:are|is|typically)\s+(?:over|more than|\d{2})|"
    r"(?:over|more than)\s+(?:20|30|40)\+?\s+years\s+old|"
    r"30\+\s*years\s+old|"
    r"casing over|"
    r"incorporated|"
    r"incorporation|"
    r"typically last|"
    r"can last|"
    r"may last|"
    r"often last|"
    r"regularly deliver|"
    r"lifespan|"
    r"last(?:s|ing)?\s+\d|"
    r"Joe Fain|"
    r"Fain Drilling|"
    r"family heritage|"
    r"60\+\s*Years Family"
    r")"
)

# High-volume factory leftovers PR #48 missed (no "of" in "30+ years experience").
FACTORY_AGE_REPLACEMENTS = [
    (
        "Licensed C-57 contractor, 4.9★ rated, 30+ years experience.",
        "Licensed C-57 contractor (CSLB #1086994), founded 2020.",
    ),
    (
        "Licensed C-57 contractor, 4.9★ rated, 30+ years experience",
        "Licensed C-57 contractor (CSLB #1086994), founded 2020",
    ),
    (
        "Licensed, 4.9★ rated, 30+ years experience.",
        "Licensed C-57 (CSLB #1086994), founded 2020.",
    ),
    (
        "Licensed, 4.9 star rated, 30+ years experience.",
        "Licensed C-57 (CSLB #1086994), founded 2020.",
    ),
    (
        "Licensed, 4.9★ rated, 30+ years experience",
        "Licensed C-57 (CSLB #1086994), founded 2020",
    ),
    (
        "With 30+ years experience and a 4.9★ Google rating",
        "Founded in 2020, with 60+ years of family heritage",
    ),
    (
        "With 30+ years experience and a 4.9★...",
        "Founded in 2020, with 60+ years of family heritage...",
    ),
    (
        "with 30+ years experience and a 4.9★ Google rating",
        "founded in 2020, with 60+ years of family heritage",
    ),
    (
        "Licensed C-57 contractor with 30+ years experience.",
        "Licensed C-57 contractor (CSLB #1086994), founded 2020.",
    ),
    (
        "Licensed C-57 contractor with 30+ years experience",
        "Licensed C-57 contractor (CSLB #1086994), founded 2020",
    ),
    (
        "<li><strong>30+ Years Experience:</strong>",
        "<li><strong>Founded 2020 · 60+ Years Family Heritage:</strong>",
    ),
    (
        "<span class=\"font-semibold\">40+ Years Experience</span>",
        "<span class=\"font-semibold\">Founded 2020</span>",
    ),
    (
        "Based on 40+ years of well service experience",
        "Based on work since 2020 and 60+ years of family heritage",
    ),
    (
        "licensed water well drilling contractor with 40+ years experience",
        "licensed C-57 water well drilling contractor (CSLB #1086994), founded 2020",
    ),
    (
        "brings 40+ years of well drilling experience",
        "brings 60+ years of family heritage in well drilling",
    ),
    (
        "based on 40+ years of drilling experience",
        "based on work since 2020 and 60+ years of family heritage",
    ),
    (
        "With over 40 years serving agricultural clients",
        "Since 2020, serving agricultural clients",
    ),
    (
        "has been the trusted choice for San Diego well drilling for over 40 years",
        "has been the trusted choice for San Diego well drilling since 2020",
    ),
    (
        "has served Hillcrest homeowners for over 40 years",
        "has served Hillcrest homeowners since 2020",
    ),
    (
        "As a C-57 licensed well contractor with over 40 years of experience",
        "As a C-57 licensed well contractor (CSLB #1086994), founded in 2020",
    ),
    (
        "with more than 30 years of local experience, a 4.9-star reputation",
        "founded in 2020, with 60+ years of family heritage",
    ),
    (
        "with more than 30 years of hands-on experience",
        "founded in 2020, with 60+ years of family heritage",
    ),
    (
        "with more than 30 years of local experience",
        "founded in 2020, with 60+ years of family heritage",
    ),
    (
        "with more than 30 years behind us and a 4.9-star record",
        "founded in 2020, with 60+ years of family heritage",
    ),
    (
        "with more than 30 years behind us",
        "founded in 2020",
    ),
    (
        "family-run for more than 30 years",
        "founded in 2020",
    ),
    (
        "backed by more than 30 years of experience",
        "founded in 2020, with 60+ years of family heritage",
    ),
    (
        "With more than 30 years in business, a 4.9-star reputation",
        "Founded in 2020, with CSLB #1086994",
    ),
    (
        "with more than 30 years in business",
        "founded in 2020",
    ),
    (
        "more than 30 years in the field",
        "since 2020",
    ),
    (
        "more than 30 years in <strong>San Diego County</strong>",
        "since 2020 in <strong>San Diego County</strong>",
    ),
    (
        "has more than 30 years of experience in exactly this terrain",
        "has served this terrain since 2020",
    ),
    (
        "Local expertise since 2008",
        "Local expertise since 2020",
    ),
    (
        "<strong>Local expertise since 2008</strong>",
        "<strong>Local expertise since 2020</strong>",
    ),
    (
        "specialists since 2008",
        "specialists since 2020",
    ),
    (
        "contractor since 2008",
        "contractor since 2020",
    ),
    (
        "Since '08",
        "Founded 2020",
    ),
]


def replace_company_age_claims(text: str) -> str:
    """Rewrite leftover SCWS company-age claims. Leave well/equipment/city dates."""
    replacements = FACTORY_AGE_REPLACEMENTS + [
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

    # Broader leftover company-tenure lines. Skip well/equipment/city-date windows.
    def _age_fallback(match: re.Match[str]) -> str:
        start = max(0, match.start() - 80)
        end = min(len(match.string), match.end() + 80)
        window = match.string[start:end]
        if KEEP_AGE_NEAR_RE.search(window):
            return match.group(0)
        token = match.group(0)
        if re.search(r"(?i)since\s+(?:2008|'08|1985|1996|2007|1987)", token):
            return "since 2020" if token[:1].islower() else "Since 2020"
        if re.search(r"(?i)for\s+(?:more than|over)\s+30\s+years|for\s+30\+\s*years", token):
            return "since 2020"
        return "founded in 2020, with 60+ years of family heritage"

    text = re.sub(
        r"(?i)\b(?:with\s+)?30\+\s*years(?:\s+of)?\s+(?:high-desert\s+|local\s+|hands-on\s+|well\s+)?experience\b",
        _age_fallback,
        text,
    )
    text = re.sub(
        r"(?i)\b(?:more than|over)\s+30\s+years\s+of\s+(?:local\s+|hands-on\s+|well\s+|high-desert\s+)?experience\b",
        _age_fallback,
        text,
    )
    text = re.sub(
        r"(?i)\bfor\s+(?:more than|over)\s+30\s+years\b",
        _age_fallback,
        text,
    )
    text = re.sub(
        r"(?i)\bfor\s+30\+\s*years\b",
        _age_fallback,
        text,
    )
    text = re.sub(
        r"(?i)\b(?:more than|over)\s+30\s+years\s+in\s+(?:the field|business)\b",
        "since 2020",
        text,
    )
    text = re.sub(
        r"(?i)\b40\+\s*years(?:\s+of)?\s+(?:well\s+)?(?:drilling\s+|service\s+)?experience\b",
        _age_fallback,
        text,
    )
    text = re.sub(
        r"(?i)\bover\s+40\s+years\s+of\s+experience\b",
        _age_fallback,
        text,
    )
    text = re.sub(
        r"(?i)(?<!incorporated in )(?<!incorporation \()\bsince\s+2008\b",
        _age_fallback,
        text,
    )
    text = re.sub(
        r"(?i)\bsince\s+(?:1985|1996|2007|1987)\b",
        _age_fallback,
        text,
    )
    # Landing-page leftover "20+ Years Experience" as company tenure (not equipment life).
    text = re.sub(
        r"(?i)>20\+</div>\s*<div class=\"text-gray-600\">Years Experience</div>",
        ">2020</div>\n                    <div class=\"text-gray-600\">Founded</div>",
        text,
    )
    text = re.sub(
        r"(?i)>20\+\s*Years Experience<",
        ">Founded 2020<",
        text,
    )

    # HTML-wrapped and longer leftover company-tenure lines.
    text = re.sub(
        r"(?i)for\s+<strong>more than 30 years</strong>",
        "since 2020",
        text,
    )
    text = re.sub(
        r"(?i)with more than 30 years</strong> of experience",
        "founded in 2020, with 60+ years of family heritage</strong>",
        text,
    )
    text = re.sub(
        r"(?i)with over 30 years</strong> of experience",
        "founded in 2020, with 60+ years of family heritage</strong>",
        text,
    )
    text = re.sub(
        r"(?i)With more than 30 years and a C-57 license",
        "Founded in 2020, with a C-57 license (CSLB #1086994)",
        text,
    )
    text = re.sub(
        r"(?i)With over 30 years and a C-57 license",
        "Founded in 2020, with a C-57 license (CSLB #1086994)",
        text,
    )
    text = re.sub(
        r"(?i)with more than 30 years of [^.<]{0,60}?experience",
        "founded in 2020, with 60+ years of family heritage",
        text,
    )
    text = re.sub(
        r"(?i)with over 30 years of (?:expertise|region-specific expertise|experience)",
        "founded in 2020, with 60+ years of family heritage",
        text,
    )
    text = re.sub(
        r"(?i)(?:with |bringing )?over 30 years of [^.<]{0,40}expertise",
        "founded in 2020, with 60+ years of family heritage",
        text,
    )
    text = re.sub(
        r"(?i)with more than 30 years in ",
        "since 2020 in ",
        text,
    )
    text = re.sub(
        r"(?i)(?:and |with )?over 30 years (?:serving|in) ",
        "since 2020 serving ",
        text,
    )
    text = re.sub(
        r"(?i)with over 30 years serving ",
        "serving since 2020 in ",
        text,
    )

    def _remaining_company_thirty(match: re.Match[str]) -> str:
        start = max(0, match.start() - 90)
        end = min(len(match.string), match.end() + 90)
        window = match.string[start:end]
        if KEEP_AGE_NEAR_RE.search(window):
            return match.group(0)
        # Cost-comparison math ("over 30 years, well ownership typically saves") is not company age.
        if re.search(r"(?i)(?:well ownership|typically saves|versus city water|saves \$)", window):
            return match.group(0)
        token = match.group(0)
        if re.match(r"(?i)for\b", token):
            return "since 2020"
        if re.search(r"(?i)drawing on|based on|built on|comes from|after|judgment", window):
            return "since 2020"
        return "founded in 2020"

    text = re.sub(
        r"(?i)(?:for\s+)?(?:<strong>)?(?:more than|over)\s+30\s+years(?:</strong>)?",
        _remaining_company_thirty,
        text,
    )
    text = re.sub(
        r"(?i)Licensed C-57, 30\+\s*years in ",
        "Licensed C-57 (CSLB #1086994), founded 2020, serving ",
        text,
    )
    text = re.sub(
        r"(?i)with 30\+\s*years in ",
        "founded in 2020, serving ",
        text,
    )
    text = re.sub(
        r"(?i)with 30\+\s*years and,",
        "founded in 2020,",
        text,
    )
    text = re.sub(
        r"(?i)with 30\+\s*years of local [^.<]{0,40}?experience",
        "founded in 2020, with 60+ years of family heritage",
        text,
    )

    def _remaining_plus_thirty(match: re.Match[str]) -> str:
        start = max(0, match.start() - 90)
        end = min(len(match.string), match.end() + 90)
        window = match.string[start:end]
        if KEEP_AGE_NEAR_RE.search(window):
            return match.group(0)
        if re.search(r"(?i)(?:well ownership|typically saves|versus city water|saves \$)", window):
            return match.group(0)
        return "founded in 2020"

    text = re.sub(r"(?i)\b30\+\s*years\b", _remaining_plus_thirty, text)
    return text


FACTORY_RATING_REPLACEMENTS = [
    (
        "• 4.9★ Rated",
        "• CSLB #1086994",
    ),
    (
        "4.9★ Rated",
        "CSLB #1086994",
    ),
    (
        "Licensed C-57, 4.9★ rated.",
        "Licensed C-57 (CSLB #1086994).",
    ),
    (
        "Licensed C-57, 4.9★ rated",
        "Licensed C-57 (CSLB #1086994)",
    ),
    (
        ", 4.9★ rated, ",
        ", ",
    ),
    (
        ", 4.9★ rated.",
        ".",
    ),
    (
        ", 4.9★ rated",
        "",
    ),
    (
        "4.9★ rated, ",
        "",
    ),
    (
        "4.9★ rated.",
        "licensed C-57 (CSLB #1086994).",
    ),
    (
        "4.9★ rated",
        "licensed C-57 (CSLB #1086994)",
    ),
    (
        "4.9 star rated, ",
        "",
    ),
    (
        "4.9 star rated",
        "licensed C-57 (CSLB #1086994)",
    ),
    (
        "<li><strong>Quality Work:</strong> 4.9★ rating on Google Reviews</li>",
        "<li><strong>Quality Work:</strong> Licensed C-57 (CSLB #1086994)</li>",
    ),
    (
        "<li><strong>4.9★ Google rating</strong> — hundreds of reviews from real customers across San Diego County</li>",
        "<li><strong>Licensed C-57 (CSLB #1086994)</strong> — founded 2020, with 60+ years of family heritage</li>",
    ),
    (
        "<li><strong>4.9★ Google rating</strong> — hundreds of reviews from San Diego and Riverside County customers</li>",
        "<li><strong>Licensed C-57 (CSLB #1086994)</strong> — founded 2020, with 60+ years of family heritage</li>",
    ),
    (
        "<li><strong>4.9★ Google rating</strong> from hundreds of verified customers</li>",
        "<li><strong>Licensed C-57 (CSLB #1086994)</strong> — founded 2020</li>",
    ),
    (
        '<p class="text-gray-600">4.9★ Google rating, hundreds of reviews</p>',
        '<p class="text-gray-600">CSLB #1086994 · founded 2020</p>',
    ),
    (
        '<p class="text-gray-600">4.9 star rating, hundreds of reviews</p>',
        '<p class="text-gray-600">CSLB #1086994 · founded 2020</p>',
    ),
    (
        "4.9★ rating on Google Reviews",
        "CSLB #1086994",
    ),
    (
        "4.9★ Google Rating (120+ reviews)",
        "Licensed C-57 · CSLB #1086994",
    ),
    (
        "4.9★ Google Rating (50+ Reviews)",
        "Licensed C-57 · CSLB #1086994",
    ),
    (
        "Google Rating (50+ Reviews)",
        "CSLB #1086994",
    ),
    (
        "✓ 4.9★ Google Rating",
        "✓ Licensed C-57 · CSLB #1086994",
    ),
    (
        "✓ 4.9-Star Rating",
        "✓ Licensed C-57 · CSLB #1086994",
    ),
    (
        "4.9 Star Rating",
        "CSLB #1086994",
    ),
    (
        "4.9★ Google rating, hundreds of reviews",
        "CSLB #1086994 · founded 2020",
    ),
    (
        "4.9 star rating, hundreds of reviews",
        "CSLB #1086994 · founded 2020",
    ),
    (
        "and a 4.9-star track record",
        "",
    ),
    (
        ", and a 4.9-star track record",
        "",
    ),
    (
        "a 4.9-star track record",
        "CSLB #1086994",
    ),
    (
        "a 4.9-star record",
        "CSLB #1086994",
    ),
    (
        ", a 4.9-star reputation,",
        ",",
    ),
    (
        " a 4.9-star reputation,",
        ",",
    ),
    (
        "a 4.9-star reputation,",
        "CSLB #1086994,",
    ),
    (
        "a 4.9-star reputation",
        "CSLB #1086994",
    ),
    (
        "our 4.9-star reputation",
        "our C-57 license (CSLB #1086994)",
    ),
    (
        "<strong>4.9-star</strong>",
        "<strong>CSLB #1086994</strong>",
    ),
    (
        "<strong>4.9 stars</strong>",
        "<strong>CSLB #1086994</strong>",
    ),
    (
        "From San Diego's 4.9★ rated well contractor.",
        "From San Diego's licensed C-57 well contractor (CSLB #1086994).",
    ),
    (
        "With 4.9★ Google rating and decades of experience,",
        "Founded in 2020, with 60+ years of family heritage,",
    ),
    (
        '<div class="text-4xl font-bold text-accent mb-2">4.9★</div>',
        '<div class="text-4xl font-bold text-accent mb-2">2020</div>',
    ),
    (
        '<div class="text-2xl font-bold text-primary">4.9★</div>',
        '<div class="text-2xl font-bold text-primary">2020</div>',
    ),
    (
        '<div class="text-3xl font-bold text-blue-600">4.9★</div>',
        '<div class="text-3xl font-bold text-blue-600">2020</div>',
    ),
    (
        '<div class="text-sm text-gray-600">Google Rating</div>',
        '<div class="text-sm text-gray-600">Founded</div>',
    ),
    (
        '<div class="text-gray-600">Google Rating</div>',
        '<div class="text-gray-600">Founded</div>',
    ),
]


def strip_fake_aggregate_rating(text: str) -> str:
    """Drop leftover schema.org 4.9 / reviewCount 127 blocks. Do not invent a new count."""

    def _drop(match: re.Match[str]) -> str:
        block = match.group(0)
        if re.search(r"4\.9", block) and re.search(r"127", block):
            return ""
        if re.search(r"reviewCount[\"']?\s*:\s*[\"']?127", block):
            return ""
        return block

    text = re.sub(
        r''',\s*"aggregateRating"\s*:\s*\{[^{}]*\}''',
        _drop,
        text,
        flags=re.I,
    )
    text = re.sub(
        r'''"aggregateRating"\s*:\s*\{[^{}]*\}\s*,?''',
        _drop,
        text,
        flags=re.I,
    )
    return text


def replace_fake_rating_lines(text: str) -> str:
    """Drop leftover 4.9-star marketing lines. Do not invent a new combined count."""
    text = strip_fake_aggregate_rating(text)
    replacements = FACTORY_RATING_REPLACEMENTS + [
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
    # Remaining leftover 4.9 marketing (do not invent a review count).
    text = re.sub(
        r"(?i),?\s*(?:and\s+)?a\s+4\.9(?:★|-star)?\s+(?:Google\s+)?(?:rating|reputation|record|track record)\b",
        "",
        text,
    )
    text = re.sub(
        r"(?i)\b4\.9(?:★|-star)\s+(?:Google\s+)?(?:rating|rated|reputation|record|track record)\b",
        "CSLB #1086994",
        text,
    )
    # ★ is non-word, so do not require a trailing \b.
    text = re.sub(r"(?i)4\.9★(?:\s*R(?:at(?:ed?)?)?)?(?:\.\.\.)?", "CSLB #1086994", text)
    text = re.sub(r"(?i)\b4\.9-star\b", "CSLB #1086994", text)
    text = re.sub(
        r'(?i)<div class="text-3xl font-bold text-accent">CSLB #1086994</div>\s*<div class="text-sm text-gray-300">Customer Rating</div>',
        '<div class="text-3xl font-bold text-accent">2020</div>\n                    <div class="text-sm text-gray-300">Founded</div>',
        text,
    )
    text = re.sub(r"(?i)✓\s*CSLB #1086994 Customer Rating", "✓ Licensed C-57 · CSLB #1086994", text)
    text = re.sub(r"heritage and,\s+", "heritage, ", text)
    text = re.sub(r"experience and,\s+", "experience, ", text)
    text = re.sub(r"heritage,\s+and\s+", "heritage ", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r",\s*\.", ".", text)
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
    """Age/4.9 rewrites stay on factory/blog/service pages. Skip homepage hero."""
    if path.suffix.lower() not in {".html", ".js"}:
        return False
    if path.name == "index.html" and "blog" not in path.parts and "locations" not in path.parts:
        return False
    rel = path.as_posix()
    if "/blog/" in rel or rel.startswith("blog/"):
        return True
    if "/services/" in rel or rel.startswith("services/"):
        return True
    if "/pages/landing/" in rel:
        return True
    if "/locations/" in rel or rel.startswith("locations/"):
        return True
    if path.name in {
        "emergency.html",
        "pump-repair.html",
        "faq.html",
        "cost-calculator.html",
        "expand-cities.js",
        "generate-city-pages.js",
    }:
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
