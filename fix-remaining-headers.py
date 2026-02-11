#!/usr/bin/env python3
"""Fix the remaining 85 blog posts with different structure"""

import re
from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

# Files that need fixing (bg-gray-50 body)
problem_files = [
    "emergency-well-repair-carlsbad.html", "emergency-well-repair-vista.html", 
    "well-pump-tripping-breaker.html", "emergency-well-repair-valley-center.html",
    "emergency-well-repair-el-cajon.html", "well-pump-repair-vista.html",
    "how-to-adjust-pressure-switch.html", "well-pump-repair-alpine.html",
    "well-drilling-santee.html", "cost-to-drill-100-foot-well.html",
    "well-drilling-lakeside.html", "submersible-vs-jet-pump.html",
    "well-pump-repair-temecula.html", "well-drilling-alpine.html",
    "well-drilling-san-marcos.html", "well-pump-repair-santee.html",
    "emergency-well-repair-santee.html", "well-drilling-carlsbad.html",
    "california-well-statistics.html", "well-drilling-el-cajon.html",
    "well-pump-repair-murrieta.html", "cost-to-drill-500-foot-well.html",
    "how-to-measure-well-depth.html", "emergency-well-repair-alpine.html",
    "well-pump-installation-cost-local.html", "how-to-increase-well-water-pressure.html",
    "emergency-well-repair-lakeside.html", "well-drilling-valley-center.html",
    "jet-pump-cost.html", "well-drilling-oceanside.html",
    "emergency-well-repair-escondido.html", "emergency-well-repair-oceanside.html",
    "24-hour-emergency-well-service.html", "well-drilling-escondido.html",
    "well-pump-making-noise.html", "how-to-chlorinate-well-yourself.html",
    "emergency-well-repair-encinitas.html", "emergency-well-repair-hemet.html",
    "well-pump-repair-san-marcos.html", "well-permit-san-diego.html",
    "well-drilling-encinitas.html", "well-check-valve-guide.html",
    "how-to-test-well-water-at-home.html", "well-pump-repair-fallbrook.html",
    "well-water-smells-bad.html", "emergency-well-repair-poway.html",
    "cost-to-drill-400-foot-well.html", "submersible-pump-cost.html",
    "pressure-tank-sizing-guide.html", "well-drilling-cost-per-foot-california.html",
    "well-drilling-la-mesa.html", "emergency-well-repair-ramona.html",
    "san-diego-county-well-statistics.html", "emergency-well-repair-murrieta.html",
    "well-drilling-vista.html", "well-pump-wont-turn-off.html",
    "emergency-well-repair-san-marcos.html", "low-water-pressure-well.html",
    "emergency-well-repair-julian.html", "how-to-winterize-well-pump.html",
    "cost-to-drill-300-foot-well.html", "how-to-check-pressure-tank.html",
    "well-pump-repair-lakeside.html", "well-pump-repair-el-cajon.html",
    "well-pump-repair-carlsbad.html", "well-drilling-ramona.html",
    "emergency-well-repair-temecula.html", "well-pump-repair-julian.html",
    "well-pump-repair-ramona.html", "cost-to-drill-200-foot-well.html",
    "well-drilling-cost-statistics.html", "well-pump-repair-oceanside.html",
    "how-to-find-buried-well.html", "well-pressure-switch-guide.html",
    "well-pump-repair-encinitas.html", "emergency-well-repair-la-mesa.html",
    "well-pump-wont-turn-on.html", "emergency-well-repair-san-diego.html",
    "emergency-well-repair-fallbrook.html", "well-drilling-poway.html",
    "well-pump-repair-san-jacinto.html", "well-water-vs-city-water-cost.html",
    "how-to-reset-well-pump.html", "well-pump-repair-la-mesa.html",
    "well-pump-overheating.html"
]

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
                <!-- Desktop Navigation -->
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
    </script>'''

updated = 0

for filename in problem_files:
    filepath = BLOG_DIR / filename
    if not filepath.exists():
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace from <body to </header>
    pattern = r'<body class="bg-gray-50">\s*<!-- Header -->.*?</header>'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, HEADER_TEMPLATE, content, flags=re.DOTALL)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated += 1
    else:
        print(f"Still can't match: {filename}")

print(f"✓ Fixed {updated} remaining blog posts")
