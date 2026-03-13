#!/usr/bin/env python3
"""
Fix blog page headers and content containers to match the reference template.
"""

import os
import re
from pathlib import Path

# Reference header HTML (from Emergency Banner through mobile menu JS)
CORRECT_HEADER = '''    <!-- Emergency Banner -->
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
    <header class="bg-primary text-white sticky top-0 z-50 shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4">
                <a href="../" class="flex items-center space-x-3 shrink-0">
                    <img width="840" height="150" loading="lazy" src="../images/logo-text-only-3x.png" alt="Southern California Well Service" class="h-10 lg:h-12 w-auto">
                </a>
                <!-- Desktop Navigation -->
                <nav class="hidden lg:flex space-x-4 items-center">
                    <a href="../#services" class="text-white hover:text-accent transition whitespace-nowrap">Services</a>
                    <a href="../#areas" class="text-white hover:text-accent transition whitespace-nowrap">Service Areas</a>
                    <a href="./" class="text-white hover:text-accent transition whitespace-nowrap">Resources</a>
                    <a href="../faq.html" class="text-white hover:text-accent transition whitespace-nowrap">FAQ</a>
                    <a href="../contact.html" class="text-white hover:text-accent transition whitespace-nowrap">Contact</a>
                    <a href="../cost-calculator.html" class="text-white font-semibold hover:text-accent transition whitespace-nowrap">Free Estimate</a>
                    <a href="../pages/about.html" class="text-white hover:text-accent transition whitespace-nowrap">About</a>
                </nav>
                <div class="flex items-center gap-3">
                    <!-- Mobile Menu Button -->
                    <button id="mobile-menu-btn" class="lg:hidden p-2 hover:bg-white/10 rounded-lg transition" aria-label="Toggle menu">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                        </svg>
                    </button>
                    <a href="tel:7604408520" class="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 lg:px-6 rounded-lg transition whitespace-nowrap text-sm lg:text-base">
                        (760) 440-8520
                    </a>
                </div>
            </div>
        </div>
        <!-- Mobile Navigation Menu -->
        <div id="mobile-menu" class="hidden lg:hidden bg-primary/95 border-t border-white/10">
            <nav class="max-w-7xl mx-auto px-4 py-4 flex flex-col space-y-3">
                <a href="../#services" class="hover:text-accent transition py-2">Services</a>
                <a href="../#areas" class="hover:text-accent transition py-2">Service Areas</a>
                <a href="./" class="hover:text-accent transition py-2">Resources</a>
                <a href="../faq.html" class="hover:text-accent transition py-2">FAQ</a>
                <a href="../contact.html" class="hover:text-accent transition py-2">Contact</a>
                <a href="../cost-calculator.html" class="text-white font-semibold hover:text-accent transition py-2">Free Estimate</a>
                <a href="../pages/about.html" class="hover:text-accent transition py-2">About</a>
            </nav>
        </div>
    </header>
    <script>
        document.getElementById('mobile-menu-btn').addEventListener('click', function() {
            document.getElementById('mobile-menu').classList.toggle('hidden');
        });
    </script>'''

MOBILE_MENU_JS = '''<script>
document.getElementById('mobile-menu-btn')?.addEventListener('click', function() {
    document.getElementById('mobile-menu')?.classList.toggle('hidden');
});
</script>'''

def process_file(filepath):
    """Process a single blog HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    modified = False
    
    # Check if already has correct header (mobile-menu-btn is the indicator)
    if 'mobile-menu-btn' not in content:
        print(f"  → Fixing header in {filepath.name}")
        
        # Find and replace the header section
        # Match from <body> tag or start of content through first </header> or </script> after header
        # Pattern: everything from body tag through the first closing header tag and its associated script
        
        # Try to find existing header section to replace
        # Look for patterns like <header...> through </header> and possibly a following <script>
        header_pattern = r'(<body[^>]*>.*?)(?=<!--\s*Breadcrumb|<div class="bg-gray|<article|<main)'
        
        def replace_header(match):
            body_tag = match.group(1)
            # Find where body tag ends
            body_end = body_tag.find('>') + 1
            body_opening = body_tag[:body_end]
            return body_opening + '\n' + CORRECT_HEADER + '\n\n    '
        
        content = re.sub(header_pattern, replace_header, content, count=1, flags=re.DOTALL)
        modified = True
    
    # Check if content wrapper is needed
    if '<main class="blog-post"><article>' in content and 'max-w-4xl' not in content:
        print(f"  → Adding content wrapper in {filepath.name}")
        
        # Add wrapper after <article> and before </article>
        content = content.replace(
            '<main class="blog-post"><article>',
            '<main class="blog-post"><article>\n        <div class="max-w-4xl mx-auto px-4">'
        )
        content = re.sub(
            r'</article>',
            '        </div>\n    </article>',
            content,
            count=1
        )
        modified = True
    
    # Check if mobile menu JS is present before </body>
    if 'mobile-menu-btn' in content and "getElementById('mobile-menu-btn')" not in content.split('</header>')[-1]:
        print(f"  → Adding mobile menu JS in {filepath.name}")
        content = content.replace('</body>', f'{MOBILE_MENU_JS}\n</body>')
        modified = True
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    blog_dir = Path('/Users/jarvis/clawd/scws-website/blog')
    
    # Get all HTML files in blog directory
    html_files = sorted(blog_dir.glob('*.html'))
    
    print(f"Found {len(html_files)} HTML files in blog directory\n")
    
    fixed_count = 0
    skipped_count = 0
    
    for filepath in html_files:
        # Skip index/listing pages
        if filepath.name in ['index.html', 'all-articles.html']:
            print(f"Skipping {filepath.name} (index page)")
            skipped_count += 1
            continue
        
        # Skip the reference template
        if filepath.name == 'spring-well-maintenance-checklist.html':
            print(f"Skipping {filepath.name} (reference template)")
            skipped_count += 1
            continue
        
        if process_file(filepath):
            fixed_count += 1
    
    print(f"\n✅ Processing complete!")
    print(f"   Fixed: {fixed_count} files")
    print(f"   Skipped: {skipped_count} files")
    print(f"   Total processed: {len(html_files)} files")

if __name__ == '__main__':
    main()
