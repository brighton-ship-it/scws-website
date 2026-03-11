#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

// Get all HTML files in blog directory, sorted by file size (largest first)
const blogDir = path.join(__dirname, '../blog');
const files = fs.readdirSync(blogDir)
    .filter(f => f.endsWith('.html'))
    .map(f => ({
        name: f,
        path: path.join(blogDir, f),
        size: fs.statSync(path.join(blogDir, f)).size
    }))
    .sort((a, b) => b.size - a.size)
    .slice(0, 50); // Top 50 by size

console.log(`Processing ${files.length} blog posts for CTA boxes...`);

let processed = 0;
let skipped = 0;

const ctaHTML = `
<div id="blog-cta" class="bg-primary text-white rounded-xl p-6 my-8">
    <h3 class="font-bold text-lg mb-2">Need Help With Your Well?</h3>
    <p class="text-gray-300 text-sm mb-4">Our experts are ready to help. Free estimates, same-day emergency service.</p>
    <a href="tel:7604408520" class="block bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg text-center transition mb-2">📞 (760) 440-8520</a>
    <a href="/contact.html" class="block bg-accent hover:bg-green-600 text-white font-bold py-3 px-4 rounded-lg text-center transition text-sm">Get Free Estimate →</a>
</div>`;

files.forEach(file => {
    const html = fs.readFileSync(file.path, 'utf8');
    const dom = new JSDOM(html);
    const document = dom.window.document;

    // Skip if CTA already exists
    if (document.getElementById('blog-cta')) {
        console.log(`⏭️  Skipping ${file.name} - CTA already exists`);
        skipped++;
        return;
    }

    // Try to find TOC first (preferred insertion point)
    let insertPoint = document.getElementById('table-of-contents');
    
    if (!insertPoint) {
        // No TOC, find the third <p> tag after <h1> as fallback
        const h1 = document.querySelector('h1');
        if (!h1) {
            console.log(`⚠️  No h1 found in ${file.name}`);
            skipped++;
            return;
        }

        let paragraphCount = 0;
        let el = h1.nextElementSibling;
        while (el && paragraphCount < 3) {
            if (el.tagName === 'P') {
                paragraphCount++;
                if (paragraphCount === 3) {
                    insertPoint = el;
                    break;
                }
            }
            el = el.nextElementSibling;
        }
    }

    if (!insertPoint) {
        console.log(`⚠️  No suitable insertion point in ${file.name}`);
        skipped++;
        return;
    }

    // Insert CTA after the insertion point
    const ctaElement = JSDOM.fragment(ctaHTML).firstChild;
    insertPoint.parentNode.insertBefore(ctaElement, insertPoint.nextSibling);

    // Write the modified HTML back
    fs.writeFileSync(file.path, dom.serialize(), 'utf8');
    console.log(`✅ Added CTA to ${file.name}`);
    processed++;
});

console.log(`\n✨ Done! Processed: ${processed}, Skipped: ${skipped}`);
