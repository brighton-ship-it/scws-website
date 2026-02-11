#!/usr/bin/env python3
"""Inject header into blog posts that have no header at all"""

import re
from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

HEADER_TEMPLATE = '''<body class="bg-white">
    <!-- Emergency Banner -->
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
                    <img src="../images/logo.png" alt="Southern California Well Service" class="h-10 lg:h-12 w-auto">
                </a>
                <nav class="hidden lg:flex space-x-6">
                    <a href="../#services" class="hover:text-accent transition">Services</a>
                    <a href="../#areas" class="hover:text-accent transition">Service Areas</a>
                    <a href="./" class="hover:text-accent transition">Resources</a>
                    <a href="../faq.html" class="hover:text-accent transition">FAQ</a>
                    <a href="../contact.html" class="hover:text-accent transition">Contact</a>
                    <a href="../cost-calculator.html" class="text-accent font-semibold hover:text-green-400 transition">Free Estimate</a>
                    <a href="../pages/about.html" class="hover:text-accent transition">About</a>
                </nav>
                <div class="flex items-center gap-3">
                    <button id="mobile-menu-btn" class="lg:hidden p-2 hover:bg-white/10 rounded-lg transition" aria-label="Toggle menu">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                        </svg>
                    </button>
                    <a href="tel:7604408520" class="bg-accent hover:bg-green-600 text-white font-semibold py-2 px-4 lg:px-6 rounded-lg transition whitespace-nowrap text-sm lg:text-base">
                        (760) 440-8520
                    </a>
                </div>
            </div>
        </div>
        <div id="mobile-menu" class="hidden lg:hidden bg-primary/95 border-t border-white/10">
            <nav class="max-w-7xl mx-auto px-4 py-4 flex flex-col space-y-3">
                <a href="../#services" class="hover:text-accent transition py-2">Services</a>
                <a href="../#areas" class="hover:text-accent transition py-2">Service Areas</a>
                <a href="./" class="hover:text-accent transition py-2">Resources</a>
                <a href="../faq.html" class="hover:text-accent transition py-2">FAQ</a>
                <a href="../contact.html" class="hover:text-accent transition py-2">Contact</a>
                <a href="../cost-calculator.html" class="text-accent font-semibold hover:text-green-400 transition py-2">Free Estimate</a>
                <a href="../pages/about.html" class="hover:text-accent transition py-2">About</a>
            </nav>
        </div>
    </header>
    <script>
        document.getElementById('mobile-menu-btn').addEventListener('click', function() {
            document.getElementById('mobile-menu').classList.toggle('hidden');
        });
    </script>
    
    <main class="max-w-4xl mx-auto px-4 py-8">'''

updated = 0

for filepath in BLOG_DIR.glob("*.html"):
    if filepath.name == "index.html":
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if this file has no header (just <body> followed by <h1>)
    if '<body>\n    <h1>' in content or '<body>\n<h1>' in content:
        # Replace <body> with our full header template
        new_content = content.replace('<body>\n    <h1>', HEADER_TEMPLATE + '\n    <h1>')
        new_content = new_content.replace('<body>\n<h1>', HEADER_TEMPLATE + '\n<h1>')
        
        # Add closing main and footer if not present
        if '</main>' not in new_content:
            new_content = new_content.replace('</body>', '</main>\n</body>')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated += 1

print(f"✓ Injected headers into {updated} blog posts")
