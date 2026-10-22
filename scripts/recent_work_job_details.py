#!/usr/bin/env python3
"""Add a factual Job details section to short Recent Work job pages.

Visible body copy under 300 words gets the section. Meta descriptions on
those pages are rewritten from the job record when they still use the
generic field-photos line. Project details and the job note stay.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from recent_work_lib import ROOT, public_meta_descriptions
from recent_work_render import job_details_section

START = "<!-- JOB_DETAILS_START -->"
END = "<!-- JOB_DETAILS_END -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)
WORD_RE = re.compile(r"[A-Za-z0-9']+")
META_RES = (
    re.compile(r'(<meta\b[^>]*\bcontent=")([^"]*)("[^>]*\bname="description")', re.I),
    re.compile(r'(<meta\b[^>]*\bname="description"[^>]*\bcontent=")([^"]*)(")', re.I),
    re.compile(r'(<meta\b[^>]*\bcontent=")([^"]*)("[^>]*\bproperty="og:description")', re.I),
    re.compile(r'(<meta\b[^>]*\bproperty="og:description"[^>]*\bcontent=")([^"]*)(")', re.I),
)
JSON_DESC_RE = re.compile(r'("description"\s*:\s*")((?:\\.|[^"\\])*)(")')


def visible_body_words(html: str) -> int:
    chunk = html
    start = html.find("<h1>")
    end = html.lower().find("<footer")
    if start != -1 and end != -1 and end > start:
        chunk = html[start:end]
    chunk = re.sub(r"<script[\s\S]*?</script>", " ", chunk, flags=re.I)
    chunk = re.sub(r"<style[\s\S]*?</style>", " ", chunk, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", chunk)
    return len(WORD_RE.findall(text))


def _attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _json_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)[1:-1]


def replace_descriptions(html: str, description: str) -> str:
    attr = _attr(description)
    for pattern in META_RES:
        html = pattern.sub(lambda match, attr=attr: match.group(1) + attr + match.group(3), html)
    encoded = _json_string(description)

    def json_sub(match: re.Match[str]) -> str:
        return match.group(1) + encoded + match.group(3)

    return JSON_DESC_RE.sub(json_sub, html)


def upsert_section(html: str, section: str) -> str:
    if START in html:
        return BLOCK_RE.sub(section + "\n", html, count=1)
    token = "<h2>What we did</h2>"
    idx = html.find(token)
    if idx == -1:
        raise ValueError("job page has no What we did section")
    sec = html.rfind("<section", 0, idx)
    if sec == -1:
        raise ValueError("job page has no section before What we did")
    return html[:sec] + section + "\n" + html[sec:]


def apply_job_details(root: Path | None = None) -> dict[str, int]:
    root = root or ROOT
    projects = json.loads((root / "recent-work" / "projects.json").read_text(encoding="utf-8"))["projects"]
    descriptions = public_meta_descriptions(projects)
    changed = 0
    unchanged = 0
    skipped = 0
    for project in projects:
        path = root / "recent-work" / f"{project['slug']}.html"
        if not path.is_file():
            skipped += 1
            continue
        original = path.read_text(encoding="utf-8")
        if START not in original and visible_body_words(original) >= 300:
            skipped += 1
            continue
        updated = upsert_section(original, job_details_section(project))
        updated = replace_descriptions(updated, descriptions[project["slug"]])
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
        else:
            unchanged += 1
    return {"changed": changed, "unchanged": unchanged, "skipped": skipped}


if __name__ == "__main__":
    print(json.dumps(apply_job_details()))
