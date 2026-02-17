#!/usr/bin/env python3
"""Fix inline headers missing logo image."""

import re
from pathlib import Path

# Pattern for inline header without logo image  
OLD_PATTERN = r'<header><nav><a href="[^"]*" class="logo">Southern California Well Service</a>'

# Replacement with logo image
NEW_HEADER = '''<header class="site-header">
        <div class="header-content">
            <a href="/" class="logo">
                <img src="/images/logo.png" alt="SCWS Logo" width="50" height="50">
                <span>Southern California Well Service</span>
            </a>
            <nav class="main-nav">'''

def fix_file(filepath):
    """Fix a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has logo.png
    if 'logo.png' in content:
        return False
    
    # Check if it has the inline header pattern
    if re.search(OLD_PATTERN, content):
        # Replace the old header start with new header
        new_content = re.sub(
            OLD_PATTERN, 
            NEW_HEADER,
            content
        )
        
        # Also fix the closing tags
        # Old: </nav></header>
        # New: </nav></div></header>
        new_content = new_content.replace('</nav></header>', '</nav>\n            </div>\n    </header>')
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    
    return False

def main():
    website_dir = Path('/Users/jarvis/clawd/scws-website')
    fixed = 0
    checked = 0
    
    # Process all HTML files in blog/
    blog_dir = website_dir / 'blog'
    for html_file in blog_dir.glob('*.html'):
        checked += 1
        if fix_file(html_file):
            fixed += 1
            print(f"Fixed: {html_file.name}")
    
    print(f"\nDone! Fixed {fixed} of {checked} blog files checked.")

if __name__ == '__main__':
    main()
