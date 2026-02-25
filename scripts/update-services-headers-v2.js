#!/usr/bin/env node
/**
 * Update services city pages with alternate header format (bg-blue-900)
 */

const fs = require('fs');
const path = require('path');

const servicesDir = path.join(__dirname, '../services');

// Tailwind config to add before </head>
const tailwindConfig = `
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: '#1f3b4d',
                        accent: '#4e9271',
                    }
                }
            }
        }
    </script>`;

// New header HTML
const newHeader = `
    <!-- Emergency Banner -->
    <div class="bg-gradient-to-r from-red-600 to-red-700 text-white py-2.5">
        <div class="max-w-7xl mx-auto px-4 text-center flex items-center justify-center gap-2 flex-wrap">
            <span class="font-bold tracking-wide">🚨 No Water?</span>
            <span class="hidden sm:inline">Same-day emergency service available.</span>
            <a href="tel:7604630493" class="bg-white text-red-600 font-bold px-4 py-1 rounded-full text-sm hover:bg-red-100 transition ml-1">
                Call Now →
            </a>
        </div>
    </div>

    <!-- Header (sticky) -->
    <header class="bg-primary text-white sticky top-0 z-50 shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4">
                <a href="/" class="flex items-center space-x-3 shrink-0">
                    <img src="/images/logo.png" alt="Southern California Well Service" class="h-10 lg:h-12 w-auto">
                </a>
                <!-- Desktop Navigation -->
                <nav class="hidden lg:flex space-x-4 items-center">
                    <a href="/pages/services/well-drilling.html" class="text-white hover:text-accent transition whitespace-nowrap">Services</a>
                    <a href="/pages/service-area.html" class="text-white hover:text-accent transition whitespace-nowrap">Service Areas</a>
                    <a href="/blog/" class="text-white hover:text-accent transition whitespace-nowrap">Resources</a>
                    <a href="/faq.html" class="text-white hover:text-accent transition whitespace-nowrap">FAQ</a>
                    <a href="/contact.html" class="text-white hover:text-accent transition whitespace-nowrap">Contact</a>
                    <a href="/cost-calculator.html" class="text-white font-semibold hover:text-accent transition whitespace-nowrap">Free Estimate</a>
                    <a href="/pages/about.html" class="text-white hover:text-accent transition whitespace-nowrap">About</a>
                </nav>
                <div class="flex items-center gap-3">
                    <!-- Mobile Menu Button -->
                    <button id="mobile-menu-btn" class="lg:hidden p-2 hover:bg-white/10 rounded-lg transition" aria-label="Toggle menu">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                        </svg>
                    </button>
                    <a href="tel:7604630493" class="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 lg:px-6 rounded-lg transition whitespace-nowrap text-sm lg:text-base">
                        (760) 463-0493
                    </a>
                </div>
            </div>
        </div>
        <!-- Mobile Navigation Menu -->
        <div id="mobile-menu" class="hidden lg:hidden bg-primary/95 border-t border-white/10">
            <nav class="max-w-7xl mx-auto px-4 py-4 flex flex-col space-y-3">
                <a href="/pages/services/well-drilling.html" class="hover:text-accent transition py-2">Services</a>
                <a href="/pages/service-area.html" class="hover:text-accent transition py-2">Service Areas</a>
                <a href="/blog/" class="hover:text-accent transition py-2">Resources</a>
                <a href="/faq.html" class="hover:text-accent transition py-2">FAQ</a>
                <a href="/contact.html" class="hover:text-accent transition py-2">Contact</a>
                <a href="/cost-calculator.html" class="text-white font-semibold hover:text-accent transition py-2">Free Estimate</a>
                <a href="/pages/about.html" class="hover:text-accent transition py-2">About</a>
            </nav>
        </div>
    </header>
    <script>
        // Mobile menu toggle
        document.getElementById('mobile-menu-btn').addEventListener('click', function() {
            const menu = document.getElementById('mobile-menu');
            menu.classList.toggle('hidden');
        });
    </script>`;

// Pattern for alternate header format
const altHeaderPattern = /(\s*<!-- Header -->)?\s*<header class="bg-blue-900 text-white py-4">[\s\S]*?<\/header>/;

let updated = 0;
let skipped = 0;

function processDirectory(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    
    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory()) {
            processDirectory(fullPath);
        } else if (entry.name.endsWith('.html')) {
            let content = fs.readFileSync(fullPath, 'utf8');
            
            // Skip if already updated
            if (content.includes('<!-- Emergency Banner -->')) {
                skipped++;
                continue;
            }
            
            // Check for alternate header format
            if (content.includes('<header class="bg-blue-900 text-white py-4">')) {
                // These already use Tailwind, just replace header
                content = content.replace(altHeaderPattern, newHeader);
                fs.writeFileSync(fullPath, content);
                console.log(`✓ Updated: ${fullPath}`);
                updated++;
            }
        }
    }
}

console.log('Updating services pages with alternate header format...\n');
processDirectory(servicesDir);
console.log(`\nDone! Updated: ${updated}, Skipped: ${skipped}`);
