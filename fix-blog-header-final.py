#!/usr/bin/env python3
"""Replace blog post header with EXACT homepage structure"""

import re
from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

# The exact header structure from homepage (adjusted paths for blog subdirectory)
HOMEPAGE_HEADER = '''<body class="bg-white">
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
                <!-- Desktop Navigation -->
                <nav class="hidden lg:flex space-x-6">
                    <a href="../#services" class="hover:text-accent transition">Services</a>
                    <a href="../#areas" class="hover:text-accent transition">Service Areas</a>
                    <a href="../blog/" class="hover:text-accent transition">Resources</a>
                    <a href="../faq.html" class="hover:text-accent transition">FAQ</a>
                    <a href="../contact.html" class="hover:text-accent transition">Contact</a>
                    <a href="../cost-calculator.html" class="text-accent font-semibold hover:text-green-400 transition">Free Estimate</a>
                    <a href="../pages/about.html" class="hover:text-accent transition">About</a>
                </nav>
                <div class="flex items-center gap-3">
                    <!-- Mobile Menu Button -->
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
        <!-- Mobile Navigation Menu -->
        <div id="mobile-menu" class="hidden lg:hidden bg-primary/95 border-t border-white/10">
            <nav class="max-w-7xl mx-auto px-4 py-4 flex flex-col space-y-3">
                <a href="../#services" class="hover:text-accent transition py-2">Services</a>
                <a href="../#areas" class="hover:text-accent transition py-2">Service Areas</a>
                <a href="../blog/" class="hover:text-accent transition py-2">Resources</a>
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
    </script>'''

updated = 0

for filepath in BLOG_DIR.glob("*.html"):
    if filepath.name == "index.html":
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the header section (from <body> to after </header> and emergency banner)
    # Pattern: body tag through the emergency banner
    pattern = r'<body class="bg-white">\s*<!-- Header -->.*?</header>\s*<!-- Emergency Banner -->.*?</div>\s*</div>'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, HOMEPAGE_HEADER, content, flags=re.DOTALL)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated += 1

print(f"✓ Updated {updated} blog posts with exact homepage header")
