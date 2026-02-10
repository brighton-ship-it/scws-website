#!/usr/bin/env python3
import os
import re
from datetime import date

blog_dir = "blog"
sitemap_file = "sitemap.xml"

# Get all HTML blog files
blog_files = [f for f in os.listdir(blog_dir) if f.endswith('.html') and f != 'index.html']

# Read current sitemap
with open(sitemap_file, 'r') as f:
    sitemap = f.read()

# Find existing blog URLs
existing = set(re.findall(r'<loc>https://scwellservice\.com/blog/([^<]+)</loc>', sitemap))

# Find new files to add
new_files = [f for f in blog_files if f not in existing]

print(f"Total blog files: {len(blog_files)}")
print(f"Already in sitemap: {len(existing)}")
print(f"New files to add: {len(new_files)}")

if new_files:
    today = date.today().isoformat()
    
    # Generate new URL entries
    new_entries = ""
    for f in sorted(new_files):
        new_entries += f'''  <url>
    <loc>https://scwellservice.com/blog/{f}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
'''
    
    # Insert before closing </urlset>
    sitemap = sitemap.replace('</urlset>', new_entries + '</urlset>')
    
    with open(sitemap_file, 'w') as f:
        f.write(sitemap)
    
    print(f"\nAdded {len(new_files)} new URLs to sitemap")
    for f in sorted(new_files)[:10]:
        print(f"  + {f}")
    if len(new_files) > 10:
        print(f"  ... and {len(new_files) - 10} more")
else:
    print("No new files to add")
