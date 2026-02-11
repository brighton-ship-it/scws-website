#!/usr/bin/env python3
"""Fix nav breakpoint - use xl: instead of lg: to prevent wrapping"""

from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

# Changes to make:
# 1. hidden lg:flex → hidden xl:flex (desktop nav)
# 2. lg:hidden → xl:hidden (mobile button)
# 3. space-x-6 → space-x-4 (tighter spacing)

replacements = [
    ('class="hidden lg:flex space-x-6"', 'class="hidden xl:flex space-x-4"'),
    ('class="lg:hidden p-2', 'class="xl:hidden p-2'),
    ('class="hidden lg:hidden pb-4"', 'class="hidden xl:hidden pb-4"'),
    ('class="hidden lg:hidden bg-primary/95', 'class="hidden xl:hidden bg-primary/95'),
]

updated = 0

for filepath in BLOG_DIR.glob("*.html"):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        updated += 1

print(f"✓ Updated nav breakpoints in {updated} files")
