#!/usr/bin/env python3
"""Fix nav spacing - tighter to prevent wrapping"""

from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

# Make nav tighter: space-x-6 → space-x-4, add text-sm
OLD_NAV = 'class="hidden lg:flex space-x-6"'
NEW_NAV = 'class="hidden lg:flex space-x-4 text-sm"'

updated = 0

for filepath in BLOG_DIR.glob("*.html"):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if OLD_NAV in content:
        content = content.replace(OLD_NAV, NEW_NAV)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        updated += 1

print(f"✓ Updated nav spacing in {updated} files")
