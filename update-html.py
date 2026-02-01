#!/usr/bin/env python3
import re
import os
import glob

def update_html(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # 1. Remove Tailwind CDN script line
    content = re.sub(r'\s*<script src="https://cdn\.tailwindcss\.com"></script>\s*\n?', '\n', content)
    
    # 2. Remove tailwind.config script block
    content = re.sub(
        r'\s*<script>\s*tailwind\.config\s*=\s*\{[^}]*\{[^}]*\}[^}]*\}\s*</script>\s*',
        '\n',
        content,
        flags=re.DOTALL
    )
    
    # 3. Remove inline <style> block (we moved it to CSS file)
    content = re.sub(
        r'\s*<style>\s*body \{ font-family:.*?</style>\s*',
        '\n',
        content,
        flags=re.DOTALL
    )
    
    # 4. Add CSS link after favicon if not already present
    if 'css/styles.css' not in content:
        content = re.sub(
            r'(<link rel="icon"[^>]*>)',
            r'\1\n    <link rel="stylesheet" href="css/styles.css">',
            content
        )
        # For blog posts, use relative path
        if '/blog/' in filepath:
            content = content.replace('href="css/styles.css"', 'href="../css/styles.css"')
    
    # 5. Ensure Google Fonts has display=swap
    content = re.sub(
        r'(fonts\.googleapis\.com/css2\?family=[^"]+)(?<!display=swap)"',
        r'\1&display=swap"',
        content
    )
    # Fix double display=swap
    content = content.replace('&display=swap&display=swap', '&display=swap')
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

# Process all HTML files
updated = 0
for pattern in ['*.html', 'blog/*.html']:
    for filepath in glob.glob(pattern):
        if update_html(filepath):
            print(f"Updated: {filepath}")
            updated += 1

print(f"\nTotal: {updated} files updated")
