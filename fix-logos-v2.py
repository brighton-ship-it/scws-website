#!/usr/bin/env python3
"""Add header with logo to pages missing headers entirely."""

import os
from pathlib import Path

# Header to insert after </head>
HEADER_HTML = '''<header class="site-header">
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
    </header>

    '''

def fix_file(filepath):
    """Fix a single file by adding header after </head><body>."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has logo.png
    if 'logo.png' in content:
        return False
    
    # Find </head> and <body> - insert header right after <body>
    if '</head>' in content and '<body>' in content:
        # Insert header after <body>
        new_content = content.replace('<body>\n    <article>', '<body>\n    ' + HEADER_HTML + '<main class="blog-post">\n    <article>')
        
        # Also need to close </main> before </body>
        if '</body>' in new_content and '</main>' not in new_content:
            new_content = new_content.replace('</body>', '</main>\n</body>')
        
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
