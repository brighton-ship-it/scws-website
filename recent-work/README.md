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

**Brighton must keep a photo on the audit page before this publisher will
use it.** Rejected photos never publish. Unreviewed photos stay unpublished.
Phone audit: https://scwellservice.com/ops/photo-audit/ — see
`ops/photo-audit/README.md`.

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
   pages (default 3), and page size (default 20).
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
- Detail pages and per-city hubs via `scripts/generate-recent-work-pages.py`
- Sitemap URLs in `sitemap-pages.xml` for the index, pagination, city hubs, and indexable job notes only

## Index gate

A job page is **indexable** only when its public summary is a real job note:

- It is not the publisher boilerplate (`Something completed in City.`)
- It is at least **15 words** (`MIN_INDEXABLE_SUMMARY_WORDS` in `scripts/recent_work_lib.py`)

Anything thinner is still built, so the photo and city stay available, but the page gets `noindex, follow` and is left out of the sitemap. Those jobs show up as cards on `/recent-work/areas/{city}.html`. City hubs are indexable and link to `/services/{city}/` when that page exists.

Specs (horsepower, depth, flow, brand) are printed only when that number or name is already in the job note. The generator does not invent them.

## Photo gate

Heroes, cards, galleries, and social images skip anything listed in `recent-work/paperwork-photos.txt`: paper, invoices, forms, handwritten notes, shipping labels, and phone screenshots. The next real field photo is used. If a job has no field photo left, the card and hero use a plain brand-color block instead of that file.

The list is a visual audit. A brightness check also matches white tanks and motor nameplates, so those photos are not on the list. Notes written on a metal panel stay. A byte-identical copy of a listed photo is skipped even under a new filename.

To block another photo, add its filename (one per line) and rebuild:

```bash
python3 scripts/generate-recent-work-pages.py
```

Rebuild pages, hubs, the Recent Work index, and the Recent Work sitemap entries:

```bash
python3 scripts/generate-recent-work-pages.py
```

Run the publisher first when new Jobber jobs should be added. Then run the generator so new cards use this template and the same gate.

Existing job IDs are never overwritten, so the live August 2026 write-ups stay
as written.

## What we do not use

- The old `scws-jobs` / Supabase `job_attachments` live feed is still in
  `index.html` as a silent extra, but it is not the publish store. That API
  has been 401/RLS. Do not revive it unless someone confirms it is healthy.
- Do not change the public text number `760-219-5877` or voice `(760) 440-8520`.
