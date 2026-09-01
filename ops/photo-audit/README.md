# Job photo audit (internal)

Brighton visually keeps or rejects Jobber job photos **before** anything is public.

- **Keep** → eligible for a Recent Work card and a GBP local post
- **Reject** → never publish
- Unreviewed photos are **not** published. This page is the audit, not auto-post.

Photos stay in Jobber. This does not create a second photo store. After a keep, the existing `scripts/publish-recent-work-from-jobber.py` may copy that photo into `images/recent-work/` the same way it already does.

## How Brighton opens this on his phone

1. Set the Vercel secrets below (once).
2. On your phone, open:

   **https://scwellservice.com/ops/photo-audit/**

3. Type the `PHOTO_AUDIT_KEY` (same value as the Vercel env var).
4. Bookmark it. The key stays in this browser for the session.
5. Tap **Keep** or **Reject**. Hidden junk (notebook, invoices, screens, permits) stays off until you tap **Show junk**.

The page is `noindex`. It is not in the sitemap. Do not share the key.

If photos do not load, you are on a host without the Vercel functions — use the scwellservice.com URL (this project is on Vercel).

## Secrets (Vercel project `scws-website`)

| Name | Why |
|---|---|
| `PHOTO_AUDIT_KEY` | Shared unlock key for the page + API |
| `PHOTO_AUDIT_GITHUB_TOKEN` | Fine-grained PAT, `contents:write` on `scws-website`, so keep/reject is saved to `ops/photo-audit/decisions.json` on `main` |
| `JOBBER_CLIENT_ID` + `JOBBER_CLIENT_SECRET` + `JOBBER_REFRESH_TOKEN` | Same Jobber app as Recent Work. Live photo list for today / last N days |

Optional: `JOBBER_ACCESS_TOKEN`, `JOBBER_GRAPHQL_VERSION`, `PHOTO_AUDIT_GITHUB_REPO`, `PHOTO_AUDIT_DECISIONS_REF` (default `main`).

GitHub Actions already has the Jobber secrets for the Recent Work publisher. Copy the same trio onto Vercel, then add the two `PHOTO_AUDIT_*` values.

## What the API returns

- `GET /api/photo-audit?days=1` — today’s (or last N) Jobber photos + current keep/reject
- `GET /api/photo-audit?eligible=1` — kept photos only (GBP / Recent Work handoff)
- `POST /api/photo-audit` `{ "id", "decision": "keep"|"reject", "caption?", "shop?" }`
- `GET /api/photo-audit-image?id=job1234:1` — proxy the Jobber bytes (no second store)

Handoff item shape (no last names, streets, prices, emails, or shop phone):

```json
{
  "id": "job4242:1",
  "jobId": "job4242",
  "shop": "ramona",
  "city": "Ramona",
  "caption": "Pump replacement in Ramona."
}
```

Shop routing (unknown shop is **not** a skip):

- Anza / high-desert → `anza`
- West / central San Diego → `ramona`
- Leftover / unknown → `ramona`

## GBP daily poster (handoff)

There is no GBP local-post writer in this repo. `scws-jobs` already has GBP OAuth for **ratings** (`src/lib/gbp.ts`) and the Ramona / Anza location IDs. It does not post updates.

Wire the existing ops poster (`gbp-daily-poster` or a new cron on `scws-jobs`) to:

1. `GET https://scwellservice.com/api/photo-audit?eligible=1` with `Authorization: Bearer $PHOTO_AUDIT_KEY`
2. Post **only** `eligible[]` items
3. Use `shop` to pick the Anza or Ramona location
4. Use `caption` as-is — do not append the shop phone (GBP already has a Call button)
5. Never post rejects, unaudited photos, or the permanent-skip job (Mike Daniels / job 3224 / invoice 5629)

## Recent Work publisher

`scripts/publish-recent-work-from-jobber.py` now publishes a job only when at least one of its photos is **keep** in `ops/photo-audit/decisions.json`. Rejected photos are never downloaded into `images/recent-work/`. The Monday Action is unchanged except it will no-op until Brighton keeps something.

## Permanent skip

Job **3224** / invoice **5629** / `gotmikedaniels@gmail.com` is never queued for keep, never a review-ask, and never featured.

## Local

```bash
python3 -m unittest scripts/test_photo_audit_lib.py scripts/test_recent_work_lib.py -v
node ops/photo-audit/server-lib.test.js
```
