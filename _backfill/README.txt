Thursday 2026-08-27 Recent Work backfill helpers.
Load cards: parse and concat cards_00.json .. cards_06.json (each a JSON array) into one 70-item array.
Load urls: concat urls_00.txt .. urls_05.txt (filename SPACE url per line) = 192 photos.
Then: download+Pillow JPEG q=86 optimize; merge into recent-work/projects.json (keep existing 280); generate pages via scripts/recent_work_lib.py write_site_files + scripts/generate-recent-work-pages.py; git commit real JPEG binaries (not MCP push_files for binaries); DELETE entire _backfill/ before final commit; push branch; open PR titled "Recent Work: +70 Jobber field-photo cards (Thu 2026-08-27 backfill)"; verify raw JPEG magic ffd8ff; squash-merge ONLY if real JPEGs + full ~13KB HTML present. Do not touch homepage/hero/ratings/widget.
