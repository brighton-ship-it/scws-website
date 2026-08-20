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
2. Optional inputs: look-back days (default 21) and max new jobs (default 8).
3. The workflow opens a **PR to `main`**. Do not merge until you have checked
   the photos and the public wording.
4. After merge, GitHub Pages updates https://scwellservice.com/recent-work/.

A Monday 15:00 UTC schedule is enabled. It is a no-op when there is nothing new.

**Local**

```bash
# env vars only — do not write them into the repo
export JOBBER_CLIENT_ID=...
export JOBBER_CLIENT_SECRET=...
export JOBBER_REFRESH_TOKEN=...

python3 scripts/publish-recent-work-from-jobber.py
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
