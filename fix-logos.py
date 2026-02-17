#!/usr/bin/env python3
"""Add logo image to all pages missing it."""

import os
import re
from pathlib import Path

# Old header pattern (text-only logo)
OLD_HEADER = '''<header>
        <nav>
            <a href="/" class="logo">Southern California Well Service</a>
            <a href="/services/">Services</a>
            <a href="/blog/">Resources</a>
            <a href="/contact/">Contact</a>
            <a href="tel:7604408520" class="cta-phone">(760) 440-8520</a>
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
    
    # Replace old header with new
    if OLD_HEADER in content:
        new_content = content.replace(OLD_HEADER, NEW_HEADER)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    
    return False

def main():
    website_dir = Path('/Users/jarvis/clawd/scws-website')
    fixed = 0
    checked = 0
    
    # Process all HTML files
    for html_file in website_dir.rglob('*.html'):
        # Skip node_modules and .git
        if 'node_modules' in str(html_file) or '.git' in str(html_file):
            continue
        
        checked += 1
        if fix_file(html_file):
            fixed += 1
            print(f"Fixed: {html_file.relative_to(website_dir)}")
    
    print(f"\nDone! Fixed {fixed} of {checked} files checked.")

if __name__ == '__main__':
    main()
