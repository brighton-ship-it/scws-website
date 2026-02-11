#!/usr/bin/env python3
"""Add Free Estimate link to blog post navigation to match homepage"""

from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

# Current nav (missing Free Estimate)
OLD_NAV = '''<!-- Desktop Navigation -->
                <nav class="hidden lg:flex space-x-6">
                    <a href="../#services" class="hover:text-accent transition">Services</a>
                    <a href="../#areas" class="hover:text-accent transition">Service Areas</a>
                    <a href="../blog/" class="text-accent font-semibold">Resources</a>
                    <a href="../faq.html" class="hover:text-accent transition">FAQ</a>
                    <a href="../contact.html" class="hover:text-accent transition">Contact</a>
                    <a href="../pages/about.html" class="hover:text-accent transition">About</a>
                </nav>'''

# New nav (matches homepage - 7 items with Free Estimate highlighted)
NEW_NAV = '''<!-- Desktop Navigation -->
                <nav class="hidden lg:flex space-x-6">
                    <a href="../#services" class="hover:text-accent transition">Services</a>
                    <a href="../#areas" class="hover:text-accent transition">Service Areas</a>
                    <a href="../blog/" class="hover:text-accent transition">Resources</a>
                    <a href="../faq.html" class="hover:text-accent transition">FAQ</a>
                    <a href="../contact.html" class="hover:text-accent transition">Contact</a>
                    <a href="../cost-calculator.html" class="text-accent font-semibold hover:text-green-400 transition">Free Estimate</a>
                    <a href="../pages/about.html" class="hover:text-accent transition">About</a>
                </nav>'''

# Also update mobile nav
OLD_MOBILE = '''<nav class="flex flex-col space-y-2">
                    <a href="../#services" class="hover:text-accent transition py-2">Services</a>
                    <a href="../#areas" class="hover:text-accent transition py-2">Service Areas</a>
                    <a href="../blog/" class="text-accent font-semibold py-2">Resources</a>
                    <a href="../faq.html" class="hover:text-accent transition py-2">FAQ</a>
                    <a href="../contact.html" class="hover:text-accent transition py-2">Contact</a>
                    <a href="../pages/about.html" class="hover:text-accent transition py-2">About</a>
                </nav>'''

NEW_MOBILE = '''<nav class="flex flex-col space-y-2">
                    <a href="../#services" class="hover:text-accent transition py-2">Services</a>
                    <a href="../#areas" class="hover:text-accent transition py-2">Service Areas</a>
                    <a href="../blog/" class="hover:text-accent transition py-2">Resources</a>
                    <a href="../faq.html" class="hover:text-accent transition py-2">FAQ</a>
                    <a href="../contact.html" class="hover:text-accent transition py-2">Contact</a>
                    <a href="../cost-calculator.html" class="text-accent font-semibold hover:text-green-400 transition py-2">Free Estimate</a>
                    <a href="../pages/about.html" class="hover:text-accent transition py-2">About</a>
                </nav>'''

updated = 0

for filepath in BLOG_DIR.glob("*.html"):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changed = False
    if OLD_NAV in content:
        content = content.replace(OLD_NAV, NEW_NAV)
        changed = True
    
    if OLD_MOBILE in content:
        content = content.replace(OLD_MOBILE, NEW_MOBILE)
        changed = True
    
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        updated += 1

print(f"✓ Added Free Estimate to nav in {updated} blog posts")
