#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// City name formatting helper
function formatCityName(dirname) {
    return dirname
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Get all city directories dynamically
const servicesDir = path.join(__dirname, 'services');
const excludeDirs = ['agricultural', 'commercial', 'hoa', 'new-construction', 'residential'];

const cities = fs.readdirSync(servicesDir)
    .filter(dir => {
        const stat = fs.statSync(path.join(servicesDir, dir));
        return stat.isDirectory() && !excludeDirs.includes(dir);
    })
    .sort();

let successCount = 0;
let errorCount = 0;

console.log(`Processing ${cities.length} city pages...\n`);

for (const cityDir of cities) {
    const filePath = path.join(__dirname, 'services', cityDir, 'index.html');
    
    if (!fs.existsSync(filePath)) {
        console.log(`❌ ${cityDir}: File not found`);
        errorCount++;
        continue;
    }

    try {
        let html = fs.readFileSync(filePath, 'utf8');
        const cityName = formatCityName(cityDir);
        
        // Create new title and meta description
        const newTitle = `${cityName} Well Pump Repair & Drilling | 24/7 | SCWS`;
        const newMetaDesc = `Expert well pump repair, water well drilling & maintenance in ${cityName}, CA. Same-day service, fair pricing. Call (760) 440-8520 for free estimate.`;
        
        // Check if title is too long
        if (newTitle.length > 60) {
            console.log(`⚠️  ${cityDir}: Title too long (${newTitle.length} chars): "${newTitle}"`);
        }
        
        // Check if meta desc is too long
        if (newMetaDesc.length > 155) {
            console.log(`⚠️  ${cityDir}: Meta desc too long (${newMetaDesc.length} chars)`);
        }
        
        // Replace the title tag
        const titleRegex = /<title>.*?<\/title>/;
        if (titleRegex.test(html)) {
            html = html.replace(titleRegex, `<title>${newTitle}</title>`);
        } else {
            console.log(`⚠️  ${cityDir}: No title tag found`);
        }
        
        // Check if meta description exists
        const hasMetaDesc = html.includes('<meta content="') && html.includes('name="description"');
        const hasMetaDesc2 = html.includes('<meta name="description"');
        
        if (hasMetaDesc || hasMetaDesc2) {
            // Replace existing meta description (both formats)
            html = html.replace(
                /<meta\s+content="[^"]*"\s+name="description"\s*\/>/,
                `<meta content="${newMetaDesc}" name="description"/>`
            );
            html = html.replace(
                /<meta\s+name="description"\s+content="[^"]*"\s*\/>/,
                `<meta name="description" content="${newMetaDesc}"/>`
            );
        } else {
            // Add meta description after title tag
            html = html.replace(
                /<\/title>/,
                `</title>\n<meta name="description" content="${newMetaDesc}"/>`
            );
        }
        
        // Also update og:title and og:description if they exist
        html = html.replace(
            /<meta\s+content="[^"]*"\s+property="og:title"\s*\/>/,
            `<meta content="${newTitle}" property="og:title"/>`
        );
        html = html.replace(
            /<meta\s+content="[^"]*"\s+property="og:description"\s*\/>/,
            `<meta content="${newMetaDesc}" property="og:description"/>`
        );
        
        // Write the updated file
        fs.writeFileSync(filePath, html, 'utf8');
        console.log(`✅ ${cityDir}: Updated`);
        successCount++;
        
    } catch (error) {
        console.log(`❌ ${cityDir}: Error - ${error.message}`);
        errorCount++;
    }
}

console.log(`\n✅ Success: ${successCount}`);
console.log(`❌ Errors: ${errorCount}`);
console.log(`📊 Total: ${cities.length}`);
