#!/usr/bin/env python3
"""
SEO Improvements Script
1. Add lastmod dates to blog sitemap
2. Add breadcrumb schema to blog posts
"""

import os
import re
from datetime import datetime
from pathlib import Path

WEBSITE_DIR = Path("/Users/jarvis/clawd/scws-website")
BLOG_DIR = WEBSITE_DIR / "blog"
SITEMAP_PATH = WEBSITE_DIR / "sitemap-blog.xml"

def get_file_dates():
    """Get modification dates for all blog HTML files"""
    dates = {}
    for f in BLOG_DIR.glob("*.html"):
        if f.name == "index.html":
            continue
        mtime = os.path.getmtime(f)
        date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        dates[f.name] = date_str
    return dates

def update_blog_sitemap():
    """Add lastmod dates to blog sitemap"""
    print("Updating blog sitemap with lastmod dates...")
    
    dates = get_file_dates()
    
    with open(SITEMAP_PATH, 'r') as f:
        content = f.read()
    
    # Pattern to match URL entries
    pattern = r'<url><loc>(https://scwellservice\.com/blog/([^<]+))</loc><changefreq>monthly</changefreq><priority>0\.6</priority></url>'
    
    def add_lastmod(match):
        full_url = match.group(1)
        filename = match.group(2)
        date = dates.get(filename, "2026-02-10")  # Default date if not found
        return f'<url><loc>{full_url}</loc><lastmod>{date}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>'
    
    new_content = re.sub(pattern, add_lastmod, content)
    
    with open(SITEMAP_PATH, 'w') as f:
        f.write(new_content)
    
    print(f"  ✓ Updated {len(dates)} URLs with lastmod dates")

def get_breadcrumb_schema(title, url, is_location=False):
    """Generate breadcrumb schema for a blog post"""
    if is_location:
        # Location pages: Home > Service Areas > [City]
        breadcrumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://scwellservice.com/"},
                {"@type": "ListItem", "position": 2, "name": "Service Areas", "item": "https://scwellservice.com/blog/"},
                {"@type": "ListItem", "position": 3, "name": title}
            ]
        }
    else:
        # Regular blog: Home > Blog > [Title]
        breadcrumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://scwellservice.com/"},
                {"@type": "ListItem", "position": 2, "name": "Resources", "item": "https://scwellservice.com/blog/"},
                {"@type": "ListItem", "position": 3, "name": title}
            ]
        }
    return breadcrumb

def add_breadcrumbs_to_blog():
    """Add breadcrumb schema to all blog posts that don't have it"""
    import json
    
    print("Adding breadcrumb schema to blog posts...")
    
    updated = 0
    skipped = 0
    
    for filepath in BLOG_DIR.glob("*.html"):
        if filepath.name == "index.html":
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has breadcrumb schema
        if '"BreadcrumbList"' in content:
            skipped += 1
            continue
        
        # Extract title from the page
        title_match = re.search(r'<title>([^<]+)</title>', content)
        if not title_match:
            continue
        title = title_match.group(1).split(' | ')[0].split(' - ')[0].strip()
        
        # Check if it's a location page (well-service-[city].html pattern)
        is_location = filepath.name.startswith('well-service-') or filepath.name.startswith('well-drilling-') and any(city in filepath.name for city in ['ramona', 'escondido', 'valley-center', 'poway', 'fallbrook', 'julian', 'temecula', 'murrieta', 'hemet', 'alpine', 'lakeside'])
        
        # Generate breadcrumb schema
        breadcrumb = get_breadcrumb_schema(title, f"https://scwellservice.com/blog/{filepath.name}", is_location)
        schema_script = f'''    <!-- Breadcrumb Schema -->
    <script type="application/ld+json">
    {json.dumps(breadcrumb, indent=4)}
    </script>'''
        
        # Insert after the last </script> in <head> before </head>
        # Find position to insert (after Article or FAQ schema)
        insert_pos = content.rfind('</script>', 0, content.find('</head>'))
        if insert_pos != -1:
            insert_pos = content.find('\n', insert_pos) + 1
            new_content = content[:insert_pos] + schema_script + '\n' + content[insert_pos:]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated += 1
    
    print(f"  ✓ Added breadcrumbs to {updated} posts, {skipped} already had them")

if __name__ == "__main__":
    print("=" * 50)
    print("SEO Improvements for scwellservice.com")
    print("=" * 50)
    print()
    
    update_blog_sitemap()
    print()
    add_breadcrumbs_to_blog()
    print()
    print("Done! Don't forget to commit and push changes.")
