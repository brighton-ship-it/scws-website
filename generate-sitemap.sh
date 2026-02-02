#!/bin/bash
DOMAIN="https://scwellservice.com"
OUTPUT="sitemap.xml"

echo '<?xml version="1.0" encoding="UTF-8"?>' > $OUTPUT
echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' >> $OUTPUT

# Add main pages
for page in index.html $(find pages -name "*.html" 2>/dev/null); do
  if [ -f "$page" ]; then
    url="${page/index.html/}"
    url="${url/.html/}"
    echo "  <url><loc>$DOMAIN/$url</loc><priority>1.0</priority></url>" >> $OUTPUT
  fi
done

# Add blog posts
for post in blog/*.html; do
  if [ -f "$post" ] && [ "$(basename $post)" != "index.html" ]; then
    echo "  <url><loc>$DOMAIN/$post</loc><priority>0.8</priority></url>" >> $OUTPUT
  fi
done

echo '</urlset>' >> $OUTPUT
echo "Generated sitemap with $(grep -c '<url>' $OUTPUT) URLs"
