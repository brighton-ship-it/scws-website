#!/usr/bin/env python3
"""Add full navigation header to all blog posts"""

import os
from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

OLD_HEADER = '''<header class="bg-primary text-white py-4">
        <div class="max-w-7xl mx-auto px-4 flex justify-between items-center">
            <a href="../index.html">
                <img src="../images/logo.png" alt="Southern California Well Service" class="h-10" loading="lazy">
            </a>
            <a href="tel:7604408520" class="bg-accent hover:bg-green-700 px-4 py-2 rounded font-semibold transition text-white">
                (760) 440-8520
            </a>
        </div>
    </header>'''

NEW_HEADER = '''<header class="bg-primary text-white sticky top-0 z-50 shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4">
                <a href="../" class="flex items-center space-x-3 shrink-0">
                    <img src="../images/logo.png" alt="Southern California Well Service" class="h-10 lg:h-12 w-auto" loading="lazy">
                </a>
                <!-- Desktop Navigation -->
                <nav class="hidden lg:flex space-x-6">
                    <a href="../#services" class="hover:text-accent transition">Services</a>
                    <a href="../#areas" class="hover:text-accent transition">Service Areas</a>
                    <a href="../blog/" class="text-accent font-semibold">Resources</a>
                    <a href="../faq.html" class="hover:text-accent transition">FAQ</a>
                    <a href="../contact.html" class="hover:text-accent transition">Contact</a>
                    <a href="../pages/about.html" class="hover:text-accent transition">About</a>
                </nav>
                <div class="flex items-center gap-3">
                    <!-- Mobile Menu Button -->
                    <button class="lg:hidden p-2 hover:bg-white/10 rounded-lg transition" aria-label="Toggle menu" onclick="document.getElementById('mobile-menu').classList.toggle('hidden')">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                        </svg>
                    </button>
                    <a href="tel:7604408520" class="bg-accent hover:bg-green-600 text-white font-semibold py-2 px-4 lg:px-6 rounded-lg transition whitespace-nowrap text-sm lg:text-base">
                        (760) 440-8520
                    </a>
                </div>
            </div>
            <!-- Mobile Menu -->
            <div id="mobile-menu" class="hidden lg:hidden pb-4">
                <nav class="flex flex-col space-y-2">
                    <a href="../#services" class="hover:text-accent transition py-2">Services</a>
                    <a href="../#areas" class="hover:text-accent transition py-2">Service Areas</a>
                    <a href="../blog/" class="text-accent font-semibold py-2">Resources</a>
                    <a href="../faq.html" class="hover:text-accent transition py-2">FAQ</a>
                    <a href="../contact.html" class="hover:text-accent transition py-2">Contact</a>
                    <a href="../pages/about.html" class="hover:text-accent transition py-2">About</a>
                </nav>
            </div>
        </div>
    </header>'''

updated = 0
skipped = 0

for filepath in BLOG_DIR.glob("*.html"):
    if filepath.name == "index.html":
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if OLD_HEADER in content:
        new_content = content.replace(OLD_HEADER, NEW_HEADER)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated += 1
    else:
        skipped += 1

print(f"✓ Updated {updated} blog posts with full navigation header")
print(f"  Skipped {skipped} (already updated or different structure)")
