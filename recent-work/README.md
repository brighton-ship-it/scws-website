# Recent Work cards from Jobber

Live page: https://scwellservice.com/recent-work/

Cards are static HTML + JSON. Photos live in `/images/recent-work/jobXXXX_N.jpg`.
The live site is GitHub Pages from `main`. Brighton reviews there — not a Cursor preview.

This folder already has a first batch of mid-August 2026 jobs. Those cards keep
working even if you never run the publisher.

## Publish path (the one command)

`scripts/publish-recent-work-from-jobber.py` pulls **completed / archived Jobber
jobs** and their **note photo attachments**, writes public-safe cards, and
commits images. It does **not** invent photos and does **not** use Google
Business / gbp-photos copies.

Public copy is title + city/area only. No customer last names, no full street
addresses, no prices, no Jobber URLs.

### 1. Add GitHub Actions secrets

Repo → Settings → Secrets and variables → Actions.

Preferred (Jarvis Integration OAuth app, client `1ba9f07d-f004-4ee2-862e-426f6ac7e4c2`):

| Secret | What it is |
|---|---|
| `JOBBER_CLIENT_ID` | OAuth app client id |
| `JOBBER_CLIENT_SECRET` | OAuth app secret |
| `JOBBER_REFRESH_TOKEN` | Current refresh token for Southern California Well Service |

Or a short-lived token instead of the refresh trio:

| Secret | What it is |
|---|---|
| `JOBBER_ACCESS_TOKEN` | Bearer token (expires; refresh flow is better) |

Optional: `JOBBER_GRAPHQL_VERSION` (defaults to `2025-04-16`).

Never commit tokens. `.gitignore` already blocks `**/.env` and `**/jobber_credentials.json`.

### 2. Run it

**GitHub Action (normal path)**

1. Actions → **Publish Recent Work from Jobber** → Run workflow.
2. Optional inputs: look-back days (default 21), max new jobs (default 8),
   pages (default 3), and page size (default 20). For the next ~80-card
   month batch use **days=40**, **limit=80**, **pages=20**. Default
   `pages=3` only fetches 60 newest jobs — most of those IDs are already live.
3. The workflow opens a **PR to `main`**. Do not merge until you have checked
   the photos and the public wording.
4. After merge, GitHub Pages updates https://scwellservice.com/recent-work/.

A Monday 15:00 UTC schedule is enabled. It is a no-op when there is nothing new.

**Historical backfill (thousands of completed jobs)**

The weekly Action stays small. To walk years of completed / archived Jobber
jobs and publish many more cards from real job photos, run the same Action
with larger inputs (or the local command below):

| Input | Suggested backfill |
|---|---|
| days | `1825` (5 years) |
| limit | `200` (max new cards this run) |
| pages | `80` |
| page_size | `50` |

That scans up to 4,000 jobs and adds at most 200 new public-safe cards.
Already published job IDs are skipped, so you can re-run to continue. Do not
invent photos. Review the PR before merge.

**Local**

```bash
# env vars only — do not write them into the repo
export JOBBER_CLIENT_ID=...
export JOBBER_CLIENT_SECRET=...
export JOBBER_REFRESH_TOKEN=...

python3 scripts/publish-recent-work-from-jobber.py
python3 scripts/generate-recent-work-pages.py

# Historical backfill — real Jobber photos only
python3 scripts/publish-recent-work-from-jobber.py --days 1825 --limit 200 --pages 80 --page-size 50
python3 scripts/generate-recent-work-pages.py
```

Dry-run (no writes):

```bash
python3 scripts/publish-recent-work-from-jobber.py --dry-run
```

### 3. What the script writes

- New JPEGs in `images/recent-work/jobXXXX_N.jpg` (Jobber bytes, converted)
- New / updated entries in `recent-work/projects.json` (existing curated copy is kept)
- `js/recent-work-projects.js` (same data)
- Cards inside `recent-work/index.html` (`RECENT_WORK_CARDS_*` markers)
- Detail pages via `scripts/generate-recent-work-pages.py`
- New URLs appended to `sitemap-pages.xml`

Existing job IDs are never overwritten, so the live August 2026 write-ups stay
as written.

## What we do not use

- The old `scws-jobs` / Supabase `job_attachments` live feed is still in
  `index.html` as a silent extra, but it is not the publish store. That API
  has been 401/RLS. Do not revive it unless someone confirms it is healthy.
- Do not change the public text number `760-219-5877` or voice `(760) 440-8520`.
- The homepage six-card teaser in `index.html` is hand-picked. The publisher
  and `generate-recent-work-pages.py` do **not** rewrite it.

## 2026-08-23 batch attempt — Jobber auth missing in this VM

Tried to add ~80 **new** cards from completed jobs roughly 2026-07-22 to
2026-08-21 (job numbers in the 2900–3185 range that are not already
published). Titles stay city + job type only. No customer names, streets,
phones, prices, or Joe Fain. Real Jobber photos only — none were invented.

### Dry-run

```bash
python3 scripts/publish-recent-work-from-jobber.py --days 40 --limit 80 --pages 15 --dry-run
```

Exit code **2**:

```
Need JOBBER_ACCESS_TOKEN, or JOBBER_CLIENT_ID + JOBBER_CLIENT_SECRET + JOBBER_REFRESH_TOKEN
```

### What was checked

| Check | Result |
|---|---|
| `JOBBER_*` env in this VM | unset |
| `**/.env` / `**/jobber_credentials.json` | none (and gitignored) |
| `gh secret list` | HTTP 403 — this token cannot read Actions secrets. They may still exist. |
| `gh workflow run "Publish Recent Work from Jobber"` | HTTP 403 — cannot dispatch from here |
| Prior `publish-recent-work.yml` runs | none in the recent Actions history |
| Google Drive Jobber dumps | older April 2026 exports only; no current photo-bearing job catalog |

### Current live set (unchanged)

- 107 published cards (`job2811`–`job3184`)
- 94 of those are already in the 2900–3185 window and dated 2026-07-22 or later
- Homepage teasers left alone (publisher does not update them)

### How to finish this batch

If Actions secrets are already set, run the workflow (do not merge until review):

1. Actions → **Publish Recent Work from Jobber** → Run workflow
2. Inputs: `days=40`, `limit=80`, `pages=20` (page_size can stay 20)
3. Review the PR the Action opens. Confirm real Jobber JPEGs and city-only copy.

Local equivalent once env vars are in the shell (never commit them):

```bash
python3 scripts/publish-recent-work-from-jobber.py --days 40 --limit 80 --pages 20
python3 scripts/generate-recent-work-pages.py
```

The publisher skips existing job IDs, so the 107 live cards stay as written.
