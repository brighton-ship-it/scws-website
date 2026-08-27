Thursday 2026-08-27 Recent Work backfill helpers

CARDS: concat JSON arrays cards_00.json … cards_06.json → 70 projects.
Ignore cards.json (placeholder stub).

URLS (192 photos):
  cat urls.b64.0 urls.b64.1 urls.b64.2 urls.b64.3 urls.b64.4 urls.b64.5 urls.b64.6 urls.b64.7 | base64 -d | gunzip > urls.txt
  Each line: filename SPACE signed_url

Then download, Pillow q=86 JPEG, merge projects.json (keep existing 280), generate pages, delete this _backfill/ folder, commit binaries with git, open PR, verify ffd8ff + full HTML, squash-merge only if real.
