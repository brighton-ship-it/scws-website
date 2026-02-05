#!/bin/bash
echo '<?xml version="1.0" encoding="UTF-8"?>'
echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
for f in blog/*.html; do
  name=$(basename "$f" .html)
  echo "  <url><loc>https://www.scwellservice.com/blog/${name}</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>"
done
echo '</urlset>'
