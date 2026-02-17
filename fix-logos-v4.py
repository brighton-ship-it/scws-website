#!/usr/bin/env python3
"""Fix multi-line headers with text-only logo."""

import re
from pathlib import Path

# Pattern for multi-line header with text logo (../index.html variant)
OLD_HEADER_V1 = '''<header>
        <nav>
            <a href="../index.html" class="logo">Southern California Well Service</a>
            <a href="tel:(760) 440-8520" class="phone-link">(760) 440-8520</a>
        </nav>
    </header>'''

# Pattern for multi-line header with text logo (/ variant)
OLD_HEADER_V2 = '''<header>
        <nav>
            <a href="/" class="logo">Southern California Well Service</a>
            <a href="tel:(760) 440-8520" class="phone-link">(760) 440-8520</a>
        </nav>
    </header>'''

# New header with logo image
NEW_HEADER = '''<header class="site-header">
        <div class="header-content">
            <a href="/" class="logo">
                <img src="/images/logo.png" alt="SCWS Logo" width="50" height="50">
                <span>Southern California Well Service</span>
            </a>
            <nav class="main-nav">
                <a href="/">Home</a>
                <a href="/services/">Services</a>
                <a href="/blog/">Resources</a>
                <a href="/contact/">Contact</a>
                <a href="tel:7604408520" class="cta-phone">(760) 440-8520</a>
            </nav>
        </div>
    </header>'''

def fix_file(filepath):
    """Fix a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has logo.png
    if 'logo.png' in content:
        return False
    
    # Try both patterns
    new_content = content
    if OLD_HEADER_V1 in content:
        new_content = content.replace(OLD_HEADER_V1, NEW_HEADER)
    elif OLD_HEADER_V2 in content:
        new_content = content.replace(OLD_HEADER_V2, NEW_HEADER)
    
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
