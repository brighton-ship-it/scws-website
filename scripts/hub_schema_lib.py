#!/usr/bin/env python3
"""City-hub JSON-LD: real shops on Ramona and Anza, Service everywhere else.

Indexable /services/{city}/ pages used to emit LocalBusiness named
"Southern California Well Service - {City}" with no street address. That
reads as a shop that does not exist. Ramona and Anza are the only shops.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HYPERLOCAL_PATH = ROOT / "scripts" / "city-hyperlocal-data.json"
SITE = "https://scwellservice.com"

# Not city hubs. Leave their schema alone.
NON_CITY_SLUGS = frozenset({"agricultural", "hoa", "residential", "vineyard"})

# Explicit serving shop from the Oct 7, 2026 job mix. Wins over hyperlocal.
SPEC_SHOP = {
    "hemet": "anza",
    "menifee": "anza",
    "desert-hot-springs": "anza",
    "mountain-center": "anza",
    "el-cajon": "ramona",
    "warner-springs": "ramona",
    "rancho-santa-fe": "ramona",
    "santa-ysabel": "ramona",
}

SHOPS = {
    "ramona": {
        "id": f"{SITE}/#ramona-shop",
        "name": "Southern California Well Service — Ramona Shop",
        "street": "1077 Main St Unit B",
        "locality": "Ramona",
        "postal": "92065",
        "lat": "33.0425",
        "lng": "-116.8681",
    },
    "anza": {
        "id": f"{SITE}/#anza-shop",
        "name": "Southern California Well Service — Anza Shop",
        "street": "57174 CA-371 (US Hwy 79)",
        "locality": "Anza",
        "postal": "92539",
        "lat": "33.5539",
        "lng": "-116.6747",
    },
}

PHONE = "(760) 440-8520"
CSLB = "1086994"

NOINDEX_RE = re.compile(
    r"<meta\b[^>]*(?:name=[\"']robots[\"'][^>]*content=[\"'][^\"']*noindex|"
    r"content=[\"'][^\"']*noindex[^\"']*[\"'][^>]*name=[\"']robots[\"'])",
    re.I,
)
JSONLD_RE = re.compile(
    r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>\s*(.*?)\s*</script>",
    re.I | re.S,
)
CANONICAL_RE = re.compile(
    r"""<link\b[^>]*rel=["']canonical["'][^>]*>|<link\b[^>]*href=["'][^"']+["'][^>]*rel=["']canonical["'][^>]*>""",
    re.I,
)

_HYPERLOCAL: dict | None = None


def _hyperlocal() -> dict:
    global _HYPERLOCAL
    if _HYPERLOCAL is None:
        _HYPERLOCAL = json.loads(HYPERLOCAL_PATH.read_text(encoding="utf-8"))
    return _HYPERLOCAL


def city_display_name(slug: str) -> str:
    row = _hyperlocal().get(slug) or {}
    name = row.get("full_name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return slug.replace("-", " ").title()


def serving_shop(slug: str) -> str:
    if slug in ("ramona", "anza"):
        return slug
    if slug in SPEC_SHOP:
        return SPEC_SHOP[slug]
    office = (_hyperlocal().get(slug) or {}).get("nearest_office")
    if office in SHOPS:
        return office
    raise KeyError(f"no serving shop for {slug}")


def _shop_node(shop_key: str) -> dict:
    shop = SHOPS[shop_key]
    return {
        "@type": "LocalBusiness",
        "@id": shop["id"],
        "name": shop["name"],
        "telephone": PHONE,
        "url": SITE,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": shop["street"],
            "addressLocality": shop["locality"],
            "addressRegion": "CA",
            "postalCode": shop["postal"],
            "addressCountry": "US",
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": shop["lat"],
            "longitude": shop["lng"],
        },
        "hasCredential": {
            "@type": "EducationalOccupationalCredential",
            "credentialCategory": "license",
            "name": "CSLB C-57",
            "identifier": CSLB,
        },
    }


def hub_schema(slug: str) -> dict:
    """Schema object for one indexable city hub."""
    city = city_display_name(slug)
    url = f"{SITE}/services/{slug}/"
    area = {
        "@type": "City",
        "name": city,
        "containedInPlace": {"@type": "State", "name": "California"},
    }
    if slug in ("ramona", "anza"):
        node = {"@context": "https://schema.org"}
        node.update(_shop_node(slug))
        node["url"] = url
        node["areaServed"] = area
        return node
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": f"Well service in {city}",
        "serviceType": "Water well service",
        "url": url,
        "areaServed": area,
        "provider": _shop_node(serving_shop(slug)),
    }


def schema_script(slug: str) -> str:
    body = json.dumps(hub_schema(slug), indent=2, ensure_ascii=False)
    return f'<script type="application/ld+json">\n{body}\n</script>'


def _head(text: str) -> str:
    lower = text.lower()
    end = lower.find("</head>")
    return text[:end] if end != -1 else text[:20000]


def html_is_noindex(text: str) -> bool:
    return bool(NOINDEX_RE.search(_head(text)))


def _is_hub_business_block(data: object) -> bool:
    if not isinstance(data, dict):
        return False
    kind = data.get("@type")
    if isinstance(kind, list):
        kind = kind[0] if kind else ""
    return kind in {"LocalBusiness", "Service"}


def ensure_self_canonical(text: str, slug: str) -> str:
    url = f"{SITE}/services/{slug}/"
    head = _head(text)
    if CANONICAL_RE.search(head):
        return text
    tag = f'<link href="{url}" rel="canonical"/>\n'
    lower = text.lower()
    end = lower.find("</head>")
    if end == -1:
        return tag + text
    return text[:end] + tag + text[end:]


def replace_hub_schema(text: str, slug: str) -> str:
    """Swap the hub LocalBusiness/Service block. Leave FAQ and breadcrumbs."""
    schema = hub_schema(slug)
    matches = list(JSONLD_RE.finditer(text))
    for match in matches:
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not _is_hub_business_block(data):
            continue
        if data == schema:
            return text
        return text[: match.start()] + schema_script(slug) + text[match.end() :]
    # No business block yet. Insert before </head>.
    script = schema_script(slug) + "\n"
    lower = text.lower()
    end = lower.find("</head>")
    if end == -1:
        return script + text
    return text[:end] + script + text[end:]


def apply_hub_schema(root: Path | None = None) -> list[Path]:
    """Rewrite indexable city-hub schema and add a self-canonical if missing.

    Noindex hubs are not edited. Non-city sections (agricultural, HOA,
    residential, vineyard) are not edited.
    """
    root = root or ROOT
    changed: list[Path] = []
    services = root / "services"
    if not services.is_dir():
        return changed
    for city_dir in sorted(p for p in services.iterdir() if p.is_dir()):
        slug = city_dir.name
        if slug in NON_CITY_SLUGS:
            continue
        path = city_dir / "index.html"
        if not path.is_file():
            continue
        original = path.read_text(encoding="utf-8")
        if html_is_noindex(original):
            continue
        try:
            serving_shop(slug)
        except KeyError:
            continue
        updated = ensure_self_canonical(original, slug)
        updated = replace_hub_schema(updated, slug)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def main() -> int:
    changed = apply_hub_schema()
    print(f"hub schema updated: {len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
