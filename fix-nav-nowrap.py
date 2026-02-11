#!/usr/bin/env python3
"""Fix nav - add whitespace-nowrap to prevent text wrapping within links"""

from pathlib import Path
import re

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

updated = 0

for filepath in BLOG_DIR.glob("*.html"):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Add whitespace-nowrap to nav links that don't have it
    # Match: class="hover:text-accent transition">Service Areas</a>
    # Replace with: class="hover:text-accent transition whitespace-nowrap">Service Areas</a>
    
    # For regular nav links
    content = re.sub(
        r'class="hover:text-accent transition">(Services|Service Areas|Resources|FAQ|Contact|About)</a>',
        r'class="hover:text-accent transition whitespace-nowrap">\1</a>',
        content
    )
    
    # For the Free Estimate link (green)
    content = re.sub(
        r'class="text-accent font-semibold hover:text-green-400 transition">Free Estimate</a>',
        r'class="text-accent font-semibold hover:text-green-400 transition whitespace-nowrap">Free Estimate</a>',
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        updated += 1

print(f"✓ Added whitespace-nowrap to nav links in {updated} files")
