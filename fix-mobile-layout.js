#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { glob } = require('glob');

// Inline CSS to force edge-to-edge layout
const edgeToEdgeStyle = `    <style>
        /* Force edge-to-edge layout on mobile Safari */
        html, body {
            margin: 0 !important;
            padding: 0 !important;
            overflow-x: hidden;
        }
    </style>`;

let filesProcessed = 0;
let filesModified = 0;
let heroImagesUpdated = 0;
let stylesAdded = 0;

async function processHTMLFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    let modified = false;
    let newContent = content;
    
    // 1. Add cache-busting to hero images
    // Match: hero-*.jpg (not already versioned)
    const heroImagePattern = /(hero-[a-z0-9-]+\.jpg)(?!\?v=)/gi;
    const heroMatches = content.match(heroImagePattern);
    
    if (heroMatches && heroMatches.length > 0) {
        newContent = newContent.replace(heroImagePattern, '$1?v=2');
        heroImagesUpdated += heroMatches.length;
        modified = true;
        console.log(`  ✓ Added cache-busting to ${heroMatches.length} hero image(s)`);
    }
    
    // 2. Add edge-to-edge style if not present
    // Check if the style block already exists
    if (!content.includes('Force edge-to-edge layout') && !content.includes('html, body {')) {
        // Find </head> and insert before it
        if (content.includes('</head>')) {
            newContent = newContent.replace('</head>', `${edgeToEdgeStyle}\n</head>`);
            stylesAdded++;
            modified = true;
            console.log(`  ✓ Added edge-to-edge CSS`);
        }
    }
    
    // 3. Write back if modified
    if (modified) {
        fs.writeFileSync(filePath, newContent, 'utf8');
        filesModified++;
    }
    
    filesProcessed++;
}

async function main() {
    console.log('🔧 Fixing SCWS Website: Edge-to-Edge Layout + Hero Image Cache Busting\n');
    
    // Find all HTML files, excluding node_modules
    const htmlFiles = await glob('**/*.html', {
        ignore: ['node_modules/**', '**/node_modules/**'],
        cwd: __dirname
    });
    
    console.log(`Found ${htmlFiles.length} HTML files to process\n`);
    
    for (const file of htmlFiles) {
        const filePath = path.join(__dirname, file);
        console.log(`Processing: ${file}`);
        try {
            await processHTMLFile(filePath);
        } catch (error) {
            console.error(`  ✗ Error: ${error.message}`);
        }
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ COMPLETE');
    console.log('='.repeat(60));
    console.log(`Files processed: ${filesProcessed}`);
    console.log(`Files modified: ${filesModified}`);
    console.log(`Hero images cache-busted: ${heroImagesUpdated}`);
    console.log(`Edge-to-edge styles added: ${stylesAdded}`);
    console.log('='.repeat(60));
}

main().catch(console.error);
