Thursday 2026-08-27 Recent Work backfill helper files.
1. Read _backfill/cards.json (70 projects) and _backfill/photo-urls.txt (192 lines: filename SPACE url).
2. Download each URL into images/recent-work/<filename>; compress with Pillow RGB JPEG quality=86 optimize=True; verify FF D8 FF.
3. Merge cards into recent-work/projects.json (keep existing 280; skip duplicate ids); regenerate js/recent-work-projects.js, index, page-*.html, sitemap via scripts/recent_work_lib.py write_site_files and scripts/generate-recent-work-pages.py.
4. Full ~13KB detail HTML only — no stubs. Do not touch homepage/hero/ratings/widget.
5. git add images + HTML/JSON/JS/sitemap; commit real JPEG binaries (not MCP push_files for binaries).
6. DELETE this entire _backfill/ directory before the final commit (do not leave helper files on main).
7. Push branch recent-work/thu-2026-08-27-backfill, open PR titled "Recent Work: +70 Jobber field-photo cards (Thu 2026-08-27 backfill)", verify raw JPEG magic ffd8ff on PR branch, squash-merge ONLY if JPEGs+full HTML present.
