#!/usr/bin/env node

/**
 * Update sitemap with city well depth pages
 */

const fs = require('fs');
const path = require('path');

// Load generated pages list
const generatedPages = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'generated-pages-list.json'), 'utf8')
);

console.log(`Updating sitemap for ${generatedPages.length} city pages...`);

// Generate sitemap XML for city pages
const today = new Date().toISOString().split('T')[0];

let sitemapXml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
`;

generatedPages.forEach(({ filename }) => {
  sitemapXml += `  <url><loc>https://scwellservice.com/blog/${filename}</loc><lastmod>${today}</lastmod><priority>0.7</priority></url>\n`;
});

sitemapXml += `</urlset>`;

// Write city pages sitemap
const cityPagesSitemapPath = path.join(__dirname, '../sitemap-city-well-depth.xml');
fs.writeFileSync(cityPagesSitemapPath, sitemapXml, 'utf8');
console.log(`Created sitemap-city-well-depth.xml with ${generatedPages.length} URLs`);

// Update main sitemap index
const sitemapIndexPath = path.join(__dirname, '../sitemap.xml');
let sitemapIndex = fs.readFileSync(sitemapIndexPath, 'utf8');

// Check if already added
if (!sitemapIndex.includes('sitemap-city-well-depth.xml')) {
  // Add new sitemap before closing tag
  const newEntry = `  <sitemap><loc>https://scwellservice.com/sitemap-city-well-depth.xml</loc><lastmod>${today}</lastmod></sitemap>\n`;
  sitemapIndex = sitemapIndex.replace('</sitemapindex>', newEntry + '</sitemapindex>');
  
  fs.writeFileSync(sitemapIndexPath, sitemapIndex, 'utf8');
  console.log('✅ Updated sitemap.xml with new city pages sitemap');
} else {
  console.log('City pages sitemap already in index (not re-added)');
}

console.log('\n✅ Sitemap update complete!');
