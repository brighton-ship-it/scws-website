#!/usr/bin/env python3
"""Comprehensive blog image audit script"""

import os
import re
from pathlib import Path
from collections import defaultdict

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")
IMAGE_DIR = Path("/Users/jarvis/clawd/scws-website/images/blog")

# Track issues
broken_unsplash = []
missing_local = []
all_images = defaultdict(list)

# Process all HTML files
html_files = sorted(BLOG_DIR.glob("*.html"))
print(f"Scanning {len(html_files)} blog posts...\n")

for html_file in html_files:
    try:
        content = html_file.read_text()
        
        # Find all image sources
        img_pattern = r'src="([^"]*(?:unsplash|images/blog)[^"]*)"'
        matches = re.findall(img_pattern, content)
        
        for img_src in matches:
            all_images[html_file.name].append(img_src)
            
            # Check for broken Unsplash URLs (missing photo ID)
            if 'unsplash.com/?' in img_src:
                broken_unsplash.append({
                    'file': html_file.name,
                    'url': img_src,
                    'line': content[:content.find(img_src)].count('\n') + 1
                })
            
            # Check for missing local images
            elif '../images/blog/' in img_src:
                img_filename = img_src.split('/')[-1]
                local_path = IMAGE_DIR / img_filename
                if not local_path.exists():
                    missing_local.append({
                        'file': html_file.name,
                        'path': img_src,
                        'expected': str(local_path)
                    })
    
    except Exception as e:
        print(f"Error processing {html_file.name}: {e}")

# Print results
print("=" * 80)
print("BLOG IMAGE AUDIT RESULTS")
print("=" * 80)
print()

print(f"📊 SUMMARY")
print(f"  Total blog posts scanned: {len(html_files)}")
print(f"  Posts with images: {len(all_images)}")
print(f"  Broken Unsplash URLs: {len(broken_unsplash)}")
print(f"  Missing local images: {len(missing_local)}")
print()

if broken_unsplash:
    print("🚨 BROKEN UNSPLASH URLS (Missing Photo ID)")
    print("-" * 80)
    for item in broken_unsplash:
        print(f"  File: {item['file']}")
        print(f"  Line: {item['line']}")
        print(f"  URL:  {item['url']}")
        print()

if missing_local:
    print("❌ MISSING LOCAL IMAGES")
    print("-" * 80)
    for item in missing_local:
        print(f"  File: {item['file']}")
        print(f"  Path: {item['path']}")
        print(f"  Expected at: {item['expected']}")
        print()

# Save detailed results
with open(BLOG_DIR / "audit-results.txt", "w") as f:
    f.write("BROKEN UNSPLASH URLS\n")
    f.write("=" * 80 + "\n\n")
    for item in broken_unsplash:
        f.write(f"{item['file']} (line {item['line']}): {item['url']}\n")
    
    f.write("\n\nMISSING LOCAL IMAGES\n")
    f.write("=" * 80 + "\n\n")
    for item in missing_local:
        f.write(f"{item['file']}: {item['path']}\n")
    
    f.write(f"\n\nTOTAL FILES WITH IMAGES: {len(all_images)}\n")

print(f"\n✅ Detailed results saved to: {BLOG_DIR}/audit-results.txt")
