#!/bin/bash

# Image audit script for SCWS blog posts

BLOG_DIR="/Users/jarvis/clawd/scws-website/blog"
IMAGE_DIR="/Users/jarvis/clawd/scws-website/images/blog"
REPORT_FILE="/Users/jarvis/clawd/scws-website/blog/image-audit-temp.txt"

echo "=== BLOG IMAGE AUDIT ===" > "$REPORT_FILE"
echo "Date: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "## BROKEN UNSPLASH URLS (Missing Photo ID)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

cd "$BLOG_DIR"

# Find broken Unsplash URLs (missing photo ID)
for file in *.html; do
    if grep -q 'images\.unsplash\.com/\?w=' "$file"; then
        echo "BROKEN: $file" >> "$REPORT_FILE"
        grep -o 'https\?://images\.unsplash\.com/\?w=[^"]*' "$file" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    fi
done

echo "" >> "$REPORT_FILE"
echo "## MISSING LOCAL IMAGES" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Find missing local images
for file in *.html; do
    # Extract local image paths
    grep -o '\.\./images/blog/[^"]*\.jpg' "$file" 2>/dev/null | while read -r img_path; do
        # Convert relative path to absolute
        full_path="${IMAGE_DIR}/$(basename "$img_path")"
        if [ ! -f "$full_path" ]; then
            echo "MISSING: $file -> $img_path" >> "$REPORT_FILE"
        fi
    done
done

echo "" >> "$REPORT_FILE"
echo "## ALL IMAGES BY FILE" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# List all images used
for file in *.html; do
    imgs=$(grep -o 'src="[^"]*\(unsplash\|images/blog\)[^"]*"' "$file" 2>/dev/null || true)
    if [ -n "$imgs" ]; then
        echo "FILE: $file" >> "$REPORT_FILE"
        echo "$imgs" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    fi
done

cat "$REPORT_FILE"
