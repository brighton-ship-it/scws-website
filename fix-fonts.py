#!/usr/bin/env python3
"""
Fix Google Fonts render-blocking by:
1. Adding font-display: swap (optional) parameter
2. Using preload with onload hack for non-blocking loading
"""
import re
import glob

def fix_fonts(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Pattern to find Google Fonts link
    font_pattern = r'<link href="(https://fonts\.googleapis\.com/css2\?[^"]+)" rel="stylesheet">'
    
    def replace_font_link(match):
        url = match.group(1)
        # Return preload version with fallback
        return f'''<link rel="preload" href="{url}" as="style" onload="this.onload=null;this.rel='stylesheet'">
    <noscript><link rel="stylesheet" href="{url}"></noscript>'''
    
    content = re.sub(font_pattern, replace_font_link, content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

updated = 0
for pattern in ['*.html', 'blog/*.html']:
    for filepath in glob.glob(pattern):
        if fix_fonts(filepath):
            print(f"Fixed: {filepath}")
            updated += 1

print(f"\nTotal: {updated} files fixed")
