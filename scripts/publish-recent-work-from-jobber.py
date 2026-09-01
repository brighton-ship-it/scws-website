#!/usr/bin/env python3
"""Publish Recent Work cards from Jobber completed jobs + photo attachments.

How Brighton / Jarvis run this
==============================
One-time GitHub setup (Settings → Secrets and variables → Actions):

  Preferred refresh flow (Jarvis Integration OAuth app):
    JOBBER_CLIENT_ID
    JOBBER_CLIENT_SECRET
    JOBBER_REFRESH_TOKEN

  Or a short-lived token:
    JOBBER_ACCESS_TOKEN

Then either:
  1) GitHub → Actions → "Publish Recent Work from Jobber" → Run workflow
     The workflow pulls jobs, writes cards/images, and opens a PR to main.
     It does not push to main. Review the PR on GitHub; the live site
     (scwellservice.com, GitHub Pages from main) updates after merge.

  2) Locally, with env vars set (never commit them):
       python3 scripts/publish-recent-work-from-jobber.py

Existing cards stay as-is until this command actually adds a new job.
Photos are downloaded from Jobber note attachments — not GBP copies,
not generated pixels. Public text is title + city/area only.

A photo is published only after Brighton taps Keep on
https://scwellservice.com/ops/photo-audit/ (see ops/photo-audit/README.md).
Rejected and unreviewed photos are skipped. Job 3224 is never featured.

See recent-work/README.md for the full checklist.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from jobber_recent_work import JobberError, access_token, download_bytes, fetch_jobs  # noqa: E402
from photo_audit_lib import (  # noqa: E402
    assign_shop,
    kept_photo_indexes,
    load_decisions,
    normalize_job_id,
    permanent_skip_reason,
    shop_location_label,
)
from recent_work_lib import (  # noqa: E402
    PHOTO_DIR,
    build_project,
    collect_attachments,
    existing_project_ids,
    job_number,
    load_projects,
    merge_projects,
    public_location,
    write_site_files,
)


def save_jpeg(data: bytes, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
    except ImportError:
        if data[:3] == b"\xff\xd8\xff":
            dest.write_bytes(data)
            return True
        print("Pillow is required to convert non-JPEG Jobber photos (pip install pillow)")
        return False
    try:
        image = Image.open(BytesIO(data))
        image = image.convert("RGB")
        image.thumbnail((1600, 1600))
        image.save(dest, "JPEG", quality=86, optimize=True)
        return True
    except Exception as exc:  # noqa: BLE001 — skip bad files, keep the run going
        print(f"  skip unreadable image {dest.name}: {exc}")
        return False


def download_job_photos(job: dict, *, max_photos: int, only_indexes: set[int] | None = None) -> list[str]:
    number = job_number(job)
    saved: list[str] = []
    token = None
    try:
        token = access_token()
    except JobberError:
        token = None
    for i, attachment in enumerate(collect_attachments(job), start=1):
        if only_indexes is not None and i not in only_indexes:
            continue
        if len(saved) >= max_photos:
            break
        filename = f"job{number}_{i}.jpg"
        dest = PHOTO_DIR / filename
        if dest.exists() and dest.stat().st_size > 1024:
            saved.append(filename)
            continue
        print(f"  download {attachment['name']} -> {filename}")
        try:
            raw = download_bytes(attachment["url"], token=None)
            if raw[:1] in (b"<", b"{") and token:
                raw = download_bytes(attachment["url"], token=token)
        except JobberError as exc:
            print(f"  {exc}")
            continue
        if len(raw) < 1024:
            print(f"  skip tiny download ({len(raw)} bytes): {filename}")
            continue
        if save_jpeg(raw, dest):
            saved.append(filename)
    return saved


def jobs_from_fixture(path: Path) -> list[dict]:
    payload = json.loads(path.read_text())
    if isinstance(payload, dict) and "jobs" in payload:
        jobs = payload["jobs"]
        if isinstance(jobs, dict):
            return list(jobs.get("nodes") or [])
        return list(jobs)
    if isinstance(payload, list):
        return payload
    raise SystemExit(f"Unrecognized fixture shape in {path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=21, help="Look back this many days (default 21)")
    parser.add_argument("--limit", type=int, default=8, help="Max new jobs to add (default 8)")
    parser.add_argument("--pages", type=int, default=3, help="Max Jobber pages to walk (default 3)")
    parser.add_argument("--page-size", type=int, default=20, help="Jobs per GraphQL page")
    parser.add_argument("--max-photos", type=int, default=4, help="Max photos per job")
    parser.add_argument("--fixture", type=Path, help="Use a local Jobber JSON fixture instead of the API")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be added; write nothing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    existing = load_projects()
    taken_ids = existing_project_ids(existing)
    taken_slugs = [p.get("slug") or "" for p in existing.get("projects", [])]

    if args.fixture:
        jobs = jobs_from_fixture(args.fixture)
        print(f"Loaded {len(jobs)} jobs from {args.fixture}")
    else:
        try:
            jobs = fetch_jobs(days=args.days, pages=args.pages, page_size=args.page_size)
        except JobberError as exc:
            print(exc, file=sys.stderr)
            print(
                "\nSet JOBBER_ACCESS_TOKEN or the refresh trio "
                "(JOBBER_CLIENT_ID / JOBBER_CLIENT_SECRET / JOBBER_REFRESH_TOKEN).",
                file=sys.stderr,
            )
            return 2
        print(f"Fetched {len(jobs)} Jobber jobs")

    decisions = load_decisions()
    incoming = []
    skipped = []
    for job in jobs:
        number = job_number(job)
        job_id = normalize_job_id(number)
        if job_id in taken_ids:
            skipped.append(f"{job_id} already published")
            continue
        skip = permanent_skip_reason(job)
        if skip:
            skipped.append(f"{job_id} {skip}")
            continue
        attachments = collect_attachments(job)
        if not attachments:
            skipped.append(f"{job_id} no image attachments")
            continue
        kept = kept_photo_indexes(job_id, decisions)
        if not kept:
            skipped.append(f"{job_id} waiting for photo-audit keep")
            continue
        if not any(i in kept for i in range(1, len(attachments) + 1)):
            skipped.append(f"{job_id} no kept photos")
            continue
        raw_city = ((job.get("property") or {}).get("address") or {}).get("city") or ""
        if not public_location(raw_city):
            shop = assign_shop(raw_city)
            job = {
                **job,
                "property": {
                    **(job.get("property") or {}),
                    "address": {
                        **((job.get("property") or {}).get("address") or {}),
                        "city": shop_location_label(raw_city, shop),
                    },
                },
            }
        if args.dry_run:
            photo_files = [f"{job_id}_{i}.jpg" for i in sorted(kept)[: args.max_photos]]
        else:
            photo_files = download_job_photos(
                job, max_photos=args.max_photos, only_indexes=kept
            )
        if not photo_files:
            skipped.append(f"{job_id} kept photos failed to download")
            continue
        project = build_project(job, photo_files, taken_slugs=taken_slugs)
        if not project:
            skipped.append(f"{job_id} failed public-safety / city checks")
            continue
        taken_slugs.append(project["slug"])
        incoming.append(project)
        if len(incoming) >= args.limit:
            break

    print(f"New publishable jobs: {len(incoming)}")
    for project in incoming:
        print(f"  + {project['id']} {project['title']} — {project['location']} ({len(project['photos'])} photos)")
    if skipped:
        print("Skipped:")
        for line in skipped[:20]:
            print(f"  - {line}")
        if len(skipped) > 20:
            print(f"  … {len(skipped) - 20} more")

    if args.dry_run:
        print("Dry run — no files written.")
        return 0
    if not incoming:
        print("Nothing new to publish. Existing Recent Work cards are unchanged.")
        return 0

    merged = merge_projects(existing.get("projects") or [], incoming)
    write_site_files(merged)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate-recent-work-pages.py")],
        check=True,
    )
    print("Wrote cards, photos, projects.json, and detail pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
