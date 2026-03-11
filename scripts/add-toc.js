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
    .slice(0, 20); // Top 20 by size

console.log(`Processing ${files.length} blog posts for TOC...`);

let processed = 0;
let skipped = 0;

files.forEach(file => {
    const html = fs.readFileSync(file.path, 'utf8');
    const dom = new JSDOM(html);
    const document = dom.window.document;

    // Skip if TOC already exists
    if (document.getElementById('table-of-contents')) {
        console.log(`⏭️  Skipping ${file.name} - TOC already exists`);
        skipped++;
        return;
    }

    // Find all h2 tags in the main content
    const h2s = Array.from(document.querySelectorAll('h2'));
    
    if (h2s.length < 3) {
        console.log(`⏭️  Skipping ${file.name} - only ${h2s.length} h2 tags`);
        skipped++;
        return;
    }

    // Create slugified IDs for each h2
    const tocItems = h2s.map(h2 => {
        const text = h2.textContent.trim();
        const id = text
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, '');
        
        // Set the ID on the h2
        h2.id = id;
        
        return { text, id };
    });

    // Build TOC HTML
    const tocHTML = `
<div id="table-of-contents" class="bg-gray-50 rounded-xl p-6 my-8 border border-gray-200">
    <h3 class="font-bold text-primary text-lg mb-3">📋 In This Guide</h3>
    <ul class="space-y-2">
        ${tocItems.map(item => 
            `<li><a href="#${item.id}" class="text-accent hover:text-green-700 font-medium">${item.text}</a></li>`
        ).join('\n        ')}
    </ul>
</div>`;

    // Find the first <p> tag after the first <h1>
    const h1 = document.querySelector('h1');
    if (!h1) {
        console.log(`⚠️  No h1 found in ${file.name}`);
        skipped++;
        return;
    }

    // Find first <p> after h1
    let insertPoint = h1.nextElementSibling;
    while (insertPoint && insertPoint.tagName !== 'P') {
        insertPoint = insertPoint.nextElementSibling;
    }

    if (!insertPoint) {
        console.log(`⚠️  No <p> found after h1 in ${file.name}`);
        skipped++;
        return;
    }

    // Insert TOC after the first paragraph
    const tocElement = JSDOM.fragment(tocHTML).firstChild;
    insertPoint.parentNode.insertBefore(tocElement, insertPoint.nextSibling);

    // Write the modified HTML back
    fs.writeFileSync(file.path, dom.serialize(), 'utf8');
    console.log(`✅ Added TOC to ${file.name} (${tocItems.length} sections)`);
    processed++;
});

console.log(`\n✨ Done! Processed: ${processed}, Skipped: ${skipped}`);
