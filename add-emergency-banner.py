#!/usr/bin/env python3
"""Add emergency banner BEFORE header on all blog posts to match homepage"""

from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

# What we're looking for (header comes right after body)
OLD_START = '''<body class="bg-white">
    <!-- Header -->
    <header'''

# What we want (emergency banner first, then header)
NEW_START = '''<body class="bg-white">
    <!-- Emergency Banner -->
    <div class="bg-gradient-to-r from-red-600 to-red-700 text-white py-2.5">
        <div class="max-w-7xl mx-auto px-4 text-center flex items-center justify-center gap-2 flex-wrap">
            <span class="font-bold tracking-wide">🚨 No Water?</span>
            <span class="hidden sm:inline">Same-day emergency service available.</span>
            <a href="tel:7604408520" class="bg-white text-red-600 font-bold px-4 py-1 rounded-full text-sm hover:bg-red-100 transition ml-1">
                Call Now →
            </a>
        </div>
    </div>

    <!-- Header (sticky) -->
    <header'''

updated = 0
already_has = 0

for filepath in BLOG_DIR.glob("*.html"):
    if filepath.name == "index.html":
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has the emergency banner at the start
    if 'bg-gradient-to-r from-red-600 to-red-700' in content[:2000]:
        already_has += 1
        continue
    
    if OLD_START in content:
        new_content = content.replace(OLD_START, NEW_START, 1)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated += 1

print(f"✓ Added emergency banner to {updated} blog posts")
print(f"  {already_has} already had it")
