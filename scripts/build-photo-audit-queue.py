#!/usr/bin/env python3
"""Build the photo-audit queue from completed Jobber jobs.

Writes ops/photo-audit/queue.json (metadata only — no second photo store).
Does not publish Recent Work cards and does not post to GBP.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from jobber_recent_work import JobberError, fetch_jobs  # noqa: E402
from photo_audit_lib import build_queue, load_decisions  # noqa: E402

QUEUE_PATH = ROOT / "ops" / "photo-audit" / "queue.json"


def _jobs_from_fixture(path: Path) -> list[dict]:
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=1, help="Look back this many days (default 1)")
    parser.add_argument("--pages", type=int, default=5)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--stdout", action="store_true", help="Print JSON instead of writing queue.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fixture:
        jobs = _jobs_from_fixture(args.fixture)
    else:
        try:
            jobs = fetch_jobs(days=args.days, pages=args.pages, page_size=args.page_size)
        except JobberError as exc:
            print(exc, file=sys.stderr)
            return 2

    items = build_queue(jobs, decisions=load_decisions())
    payload = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "days": args.days,
        "count": len(items),
        "photos": items,
    }
    text = json.dumps(payload, indent=2) + "\n"
    if args.stdout:
        sys.stdout.write(text)
        return 0
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(text)
    print(f"Wrote {len(items)} audit photos to {QUEUE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
