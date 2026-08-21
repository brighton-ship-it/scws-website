#!/usr/bin/env python3
"""Fix GA4 tracking on SCWS website"""
import os
import re
import glob

WEBSITE_DIR = '/Users/jarvis/clawd/scws-website'

# Correct GA4 snippet
GA4_SNIPPET = '''<script src="/js/ga4-filter.js"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-5LL1YRWT5T"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-5LL1YRWT5T');</script>'''

# Pages that need GA4 ID fixed (have wrong ID G-KR42LY3LF7)
PAGES_TO_FIX_ID = [
    'pages/brands-we-service.html',
    'pages/gallery.html',
    'pages/maintenance-program.html',
    'pages/reviews.html',
    'pages/service-area.html',
    'pages/videos.html',
    'pages/well-vs-city-water.html',
    'services/index.html',
]

# Pages missing GA4 entirely
PAGES_MISSING_GA4 = [
    'blog/well-pump-repair-alpine.html',
]

def fix_ga4_id(filepath):
    """Replace wrong GA4 ID with correct one"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace wrong GA4 ID
    new_content = content.replace('G-KR42LY3LF7', 'G-5LL1YRWT5T')
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ Fixed GA4 ID: {filepath}")
        return True
    return False

def add_ga4_to_page(filepath):
    """Add GA4 snippet after <head>"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if GA4 already present
    if 'G-5LL1YRWT5T' in content:
        print(f"  Already has GA4: {filepath}")
        return False
    
    # Insert after <head> tag
    if '<head>' in content:
        new_content = content.replace('<head>', '<head>\n' + GA4_SNIPPET, 1)
    elif '<head ' in content:
        # Handle <head with attributes
        new_content = re.sub(r'(<head[^>]*>)', r'\1\n' + GA4_SNIPPET, content, count=1)
    else:
        print(f"  No <head> tag found: {filepath}")
        return False
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✓ Added GA4: {filepath}")
    return True

def add_click_tracking_to_blog():
    """Phone taps are a single call_click from /js/call-tracking.js."""
    print("✓ Skipped inline click_to_call onclicks (call-tracking.js owns call_click)")
    return 0

def main():
    print("=== PART 1A: Fixing GA4 ID on pages with wrong ID ===")
    for page in PAGES_TO_FIX_ID:
        filepath = os.path.join(WEBSITE_DIR, page)
        if os.path.exists(filepath):
            fix_ga4_id(filepath)
        else:
            print(f"  File not found: {filepath}")
    
    print("\n=== PART 1A: Adding GA4 to pages missing it ===")
    for page in PAGES_MISSING_GA4:
        filepath = os.path.join(WEBSITE_DIR, page)
        if os.path.exists(filepath):
            add_ga4_to_page(filepath)
        else:
            print(f"  File not found: {filepath}")
    
    print("\n=== PART 1B: Adding click-to-call tracking to blog pages ===")
    add_click_tracking_to_blog()
    
    print("\n✓ Done!")

if __name__ == '__main__':
    main()
