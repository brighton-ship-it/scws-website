#!/usr/bin/env python3
"""Photo-audit rules for Recent Work + GBP eligibility.

Brighton visually keeps or rejects Jobber job photos before anything public.
This module does not store pixels. Photos stay in Jobber (and, after a keep,
the existing Recent Work publisher may copy them into images/recent-work/).

Public / handoff copy rules:
- Captions from the job photo context + city only
- No last names, streets, prices, emails, or shop phone
- Rejected photos are never eligible
- Unreviewed photos are not eligible (audit first, never auto-post)
- Unknown shop still routes: leftover → Ramona (do not skip the photo)
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from recent_work_lib import (
    collect_attachments,
    is_image_attachment,
    job_number,
    public_location,
    sanitize_public_text,
)

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "ops" / "photo-audit" / "rules.json"
DECISIONS_PATH = ROOT / "ops" / "photo-audit" / "decisions.json"
PACIFIC = ZoneInfo("America/Los_Angeles")

SHOP_PHONE_RE = re.compile(
    r"760[-.\s]?219[-.\s]?5877|760[-.\s]?440[-.\s]?8520|\(760\)\s*219[-.\s]?5877|\(760\)\s*440[-.\s]?8520",
    re.I,
)
INVOICE_HINT_RE = re.compile(r"\binvoice\s*#?\s*(\d+)\b", re.I)

_RULES: dict[str, Any] | None = None
_JUNK_RE: re.Pattern[str] | None = None


def load_rules(path: Path | None = None) -> dict[str, Any]:
    global _RULES, _JUNK_RE
    path = path or RULES_PATH
    if _RULES is not None and path == RULES_PATH:
        return _RULES
    data = json.loads(path.read_text())
    if path == RULES_PATH:
        _RULES = data
        _JUNK_RE = re.compile("|".join(f"(?:{p})" for p in data.get("junkFilename") or []), re.I)
    return data


def junk_filename_re() -> re.Pattern[str]:
    load_rules()
    assert _JUNK_RE is not None
    return _JUNK_RE


def load_decisions(path: Path | None = None) -> dict[str, Any]:
    path = path or DECISIONS_PATH
    if not path.exists():
        return {"version": 1, "updatedAt": None, "photos": {}}
    data = json.loads(path.read_text())
    data.setdefault("version", 1)
    data.setdefault("photos", {})
    return data


def dump_decisions(data: dict[str, Any], path: Path | None = None) -> None:
    path = path or DECISIONS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "updatedAt": data.get("updatedAt") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "photos": data.get("photos") or {},
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


def photo_id(job_id: str, index: int) -> str:
    return f"{job_id}:{index}"


def normalize_job_id(number: str | int) -> str:
    raw = str(number or "").strip()
    digits = re.sub(r"\D+", "", raw) or raw
    return f"job{digits}" if digits and not raw.lower().startswith("job") else (raw or "jobunknown")


def _haystack(job: dict[str, Any]) -> str:
    bits = [
        str(job.get("jobNumber") or ""),
        str(job.get("title") or ""),
        str(job.get("instructions") or ""),
        str(job.get("id") or ""),
    ]
    client = job.get("client") or {}
    if isinstance(client, dict):
        bits.append(str(client.get("firstName") or ""))
        bits.append(str(client.get("lastName") or ""))
        bits.append(str(client.get("name") or ""))
        emails = client.get("emails") or []
        if isinstance(emails, list):
            for item in emails:
                if isinstance(item, dict):
                    bits.append(str(item.get("address") or ""))
                elif isinstance(item, str):
                    bits.append(item)
        elif isinstance(emails, str):
            bits.append(emails)
    return " ".join(bits).lower()


def permanent_skip_reason(job: dict[str, Any], rules: dict[str, Any] | None = None) -> str | None:
    """Return a skip reason or None. Never include the customer name in public output."""
    rules = rules or load_rules()
    skip = rules.get("permanentSkip") or {}
    number = str(job_number(job))
    if number in {str(n) for n in skip.get("jobNumbers") or []}:
        return "permanent-skip-job"
    hay = _haystack(job)
    for email in skip.get("emails") or []:
        if email.lower() in hay:
            return "permanent-skip-client"
    for frag in skip.get("nameFragments") or []:
        if frag.lower() in hay:
            return "permanent-skip-client"
    invoices = {str(n) for n in skip.get("invoiceNumbers") or []}
    for match in INVOICE_HINT_RE.finditer(hay):
        if match.group(1) in invoices:
            return "permanent-skip-invoice"
    if any(num in hay for num in invoices) and "invoice" in hay:
        return "permanent-skip-invoice"
    return None


def is_junk_filename(name: str, content_type: str = "") -> tuple[bool, str | None]:
    name = name or ""
    content_type = content_type or ""
    if not is_image_attachment(name, content_type) or name.lower().endswith(".pdf"):
        return True, "not-an-image"
    if junk_filename_re().search(name):
        return True, "filename-looks-like-paperwork"
    return False, None


def assign_shop(city: str | None, rules: dict[str, Any] | None = None) -> str:
    """Anza/high-desert → anza; west/central SD → ramona; leftover → ramona.

    Unknown or missing city is still Ramona. Never used as a reason to drop a
    good photo.
    """
    rules = rules or load_rules()
    city_l = (city or "").strip().lower()
    city_l = re.sub(r"\s+", " ", city_l)
    if "," in city_l:
        city_l = city_l.split(",")[0].strip()
    if city_l:
        for name in rules.get("anzaCities") or []:
            if city_l == name or name in city_l:
                return "anza"
        for name in rules.get("ramonaCities") or []:
            if city_l == name or name in city_l:
                return "ramona"
    return "ramona"


def shop_location_label(city: str | None, shop: str) -> str:
    safe = public_location(city or "")
    if safe:
        return safe
    return "Anza area" if shop == "anza" else "Ramona area"


def caption_for_photo(
    *,
    title: str,
    city: str,
    filename: str = "",
    index: int = 1,
    taken: set[str] | None = None,
) -> str:
    """Unique public caption from the job context + city. No shop phone."""
    taken = taken if taken is not None else set()
    work = sanitize_public_text((title or "").strip(), fallback="")
    work = SHOP_PHONE_RE.sub("", work)
    work = re.sub(r"\s+", " ", work).strip(" \t\n,;-")
    if not work or len(work) < 4:
        work = "Well service"
    loc = public_location(city) or city.strip() or "Southern California"
    loc = SHOP_PHONE_RE.sub("", loc).strip()
    base = f"{work} in {loc}"
    if not base.endswith("."):
        base += "."
    base = sanitize_public_text(base, fallback=f"Well service in {loc}.")
    base = SHOP_PHONE_RE.sub("", base).strip()
    if not base.endswith("."):
        base += "."

    candidate = base
    n = 2
    file_hint = sanitize_public_text(Path(filename or "").stem.replace("_", " ").replace("-", " "))
    while candidate.lower() in {t.lower() for t in taken}:
        if file_hint and n == 2 and len(file_hint) >= 4 and not junk_filename_re().search(file_hint):
            extra = file_hint[:32]
            candidate = f"{work} ({extra}) in {loc}."
        else:
            candidate = f"{work} in {loc} — field photo {index + n - 2}."
        candidate = sanitize_public_text(candidate, fallback=base)
        candidate = SHOP_PHONE_RE.sub("", candidate).strip()
        if not candidate.endswith("."):
            candidate += "."
        n += 1
        if n > 8:
            break
    taken.add(candidate)
    return candidate


def decision_for(photo_key: str, decisions: dict[str, Any] | None = None) -> str:
    decisions = decisions or load_decisions()
    row = (decisions.get("photos") or {}).get(photo_key) or {}
    value = str(row.get("decision") or "pending").lower()
    if value in {"keep", "reject", "pending"}:
        return value
    return "pending"


def is_publish_eligible(photo_key: str, decisions: dict[str, Any] | None = None) -> bool:
    return decision_for(photo_key, decisions) == "keep"


def record_decision(
    photo_key: str,
    decision: str,
    *,
    caption: str | None = None,
    shop: str | None = None,
    job_id: str | None = None,
    decisions: dict[str, Any] | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    if decision not in {"keep", "reject"}:
        raise ValueError("decision must be keep or reject")
    data = decisions or load_decisions(path)
    photos = data.setdefault("photos", {})
    existing = dict(photos.get(photo_key) or {})
    if caption:
        caption = sanitize_public_text(SHOP_PHONE_RE.sub("", caption), fallback=existing.get("caption") or "")
        caption = SHOP_PHONE_RE.sub("", caption).strip()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    photos[photo_key] = {
        **existing,
        "decision": decision,
        "at": now,
        "jobId": job_id or existing.get("jobId") or photo_key.split(":")[0],
        "shop": shop or existing.get("shop") or "ramona",
        "caption": caption or existing.get("caption") or "",
    }
    data["updatedAt"] = now
    dump_decisions(data, path)
    return photos[photo_key]


def public_job_title(job: dict[str, Any]) -> str:
    title = sanitize_public_text((job.get("title") or "").strip(), fallback="")
    title = SHOP_PHONE_RE.sub("", title).strip()
    if title and len(title) >= 4:
        return title
    return "Well service"


def queue_item_from_attachment(
    job: dict[str, Any],
    attachment: dict[str, Any],
    index: int,
    *,
    decisions: dict[str, Any] | None = None,
    taken_captions: set[str] | None = None,
) -> dict[str, Any] | None:
    rules = load_rules()
    skip = permanent_skip_reason(job, rules)
    job_id = normalize_job_id(job_number(job))
    key = photo_id(job_id, index)
    name = attachment.get("name") or f"photo-{index}"
    ctype = attachment.get("contentType") or ""
    junk, junk_reason = is_junk_filename(name, ctype)
    city_raw = ((job.get("property") or {}).get("address") or {}).get("city") or ""
    city = public_location(city_raw)
    shop = assign_shop(city or city_raw, rules)
    location = shop_location_label(city or city_raw, shop)
    title = public_job_title(job)
    caption = caption_for_photo(
        title=title,
        city=location,
        filename=name,
        index=index,
        taken=taken_captions,
    )
    if skip:
        # Permanent skip: never a keep candidate. Do not expose client identity.
        return {
            "id": key,
            "jobId": job_id,
            "jobNumber": job_number(job),
            "title": title,
            "city": location,
            "shop": shop,
            "completedAt": job.get("completedAt") or job.get("endAt") or "",
            "filename": name,
            "url": "",
            "junk": True,
            "junkReason": skip,
            "skipped": True,
            "skipReason": skip,
            "caption": "",
            "decision": "reject",
        }

    existing = decision_for(key, decisions)
    if existing == "reject":
        # Already rejected — keep the row so Brighton can undo, but hide by default.
        junk = True
        junk_reason = junk_reason or "rejected"
    return {
        "id": key,
        "jobId": job_id,
        "jobNumber": job_number(job),
        "title": title,
        "city": location,
        "shop": shop,
        "completedAt": job.get("completedAt") or job.get("endAt") or "",
        "filename": name,
        "url": attachment.get("url") or "",
        "junk": junk,
        "junkReason": junk_reason,
        "skipped": False,
        "skipReason": None,
        "caption": caption,
        "decision": existing,
    }


def build_queue(
    jobs: list[dict[str, Any]],
    *,
    decisions: dict[str, Any] | None = None,
    include_permanent_skips: bool = False,
) -> list[dict[str, Any]]:
    decisions = decisions or load_decisions()
    taken: set[str] = set()
    items: list[dict[str, Any]] = []
    for job in jobs:
        skip = permanent_skip_reason(job)
        attachments = collect_attachments(job)
        if skip and not include_permanent_skips:
            continue
        if skip and include_permanent_skips:
            items.append(
                queue_item_from_attachment(
                    job,
                    {"name": "skipped", "contentType": "image/jpeg", "url": ""},
                    1,
                    decisions=decisions,
                    taken_captions=taken,
                )
            )
            continue
        for i, attachment in enumerate(attachments, start=1):
            item = queue_item_from_attachment(
                job,
                attachment,
                i,
                decisions=decisions,
                taken_captions=taken,
            )
            if item:
                items.append(item)
    return items


def kept_photo_indexes(job_id: str, decisions: dict[str, Any] | None = None) -> set[int]:
    decisions = decisions or load_decisions()
    kept: set[int] = set()
    prefix = f"{job_id}:"
    for key, row in (decisions.get("photos") or {}).items():
        if not str(key).startswith(prefix):
            continue
        if str((row or {}).get("decision") or "") != "keep":
            continue
        try:
            kept.add(int(str(key).split(":")[1]))
        except (IndexError, ValueError):
            continue
    return kept


def eligible_handoff(decisions: dict[str, Any] | None = None, queue: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Payload for GBP / Recent Work: kept photos only."""
    decisions = decisions or load_decisions()
    by_id = {item["id"]: item for item in (queue or [])}
    out = []
    for key, row in (decisions.get("photos") or {}).items():
        if str((row or {}).get("decision") or "") != "keep":
            continue
        item = by_id.get(key) or {}
        caption = sanitize_public_text(SHOP_PHONE_RE.sub("", row.get("caption") or item.get("caption") or ""))
        caption = SHOP_PHONE_RE.sub("", caption).strip()
        if not caption:
            continue
        out.append(
            {
                "id": key,
                "jobId": row.get("jobId") or item.get("jobId") or key.split(":")[0],
                "shop": row.get("shop") or item.get("shop") or "ramona",
                "city": item.get("city") or "",
                "caption": caption,
                "filename": item.get("filename") or "",
            }
        )
    return out


def now_pacific() -> datetime:
    return datetime.now(PACIFIC)
