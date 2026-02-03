#!/bin/bash
DOMAIN="https://scwellservice.com"
OUTPUT="sitemap.xml"
TODAY=$(date +%Y-%m-%d)

echo '<?xml version="1.0" encoding="UTF-8"?>' > $OUTPUT
echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' >> $OUTPUT

# Homepage
echo "  <url>
    <loc>$DOMAIN/</loc>
    <lastmod>$TODAY</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>" >> $OUTPUT

# Main pages (non-index)
for page in pages/about.html pages/estimate.html pages/contact.html contact.html faq.html; do
  if [ -f "$page" ]; then
    echo "  <url>
    <loc>$DOMAIN/$page</loc>
    <lastmod>$TODAY</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>" >> $OUTPUT
  fi
done

# Services index
if [ -f "pages/services/index.html" ]; then
  echo "  <url>
    <loc>$DOMAIN/pages/services/</loc>
    <lastmod>$TODAY</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>" >> $OUTPUT
fi

# Service pages
for page in pages/services/*.html; do
  if [ -f "$page" ] && [ "$(basename $page)" != "index.html" ]; then
    echo "  <url>
    <loc>$DOMAIN/$page</loc>
    <lastmod>$TODAY</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>" >> $OUTPUT
  fi
done

# Location pages
for page in $(find pages/locations -name "*.html" 2>/dev/null); do
  if [ -f "$page" ]; then
    echo "  <url>
    <loc>$DOMAIN/$page</loc>
    <lastmod>$TODAY</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>" >> $OUTPUT
  fi
done

# Blog index
echo "  <url>
    <loc>$DOMAIN/blog/</loc>
    <lastmod>$TODAY</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>" >> $OUTPUT

# Blog posts
for post in blog/*.html; do
  if [ -f "$post" ] && [ "$(basename $post)" != "index.html" ]; then
    echo "  <url>
    <loc>$DOMAIN/$post</loc>
    <lastmod>$TODAY</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>" >> $OUTPUT
  fi
done

# Tools/landing pages
for page in $(find tools -name "*.html" 2>/dev/null) $(find pages/landing -name "*.html" 2>/dev/null); do
  if [ -f "$page" ]; then
    echo "  <url>
    <loc>$DOMAIN/$page</loc>
    <lastmod>$TODAY</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>" >> $OUTPUT
  fi
done

echo '</urlset>' >> $OUTPUT
echo "Generated sitemap with $(grep -c '<url>' $OUTPUT) URLs"
