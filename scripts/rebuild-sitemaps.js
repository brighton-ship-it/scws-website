#!/usr/bin/env node

/**
 * Rebuild sitemaps — only include pages that are NOT noindexed
 * Fixes SEO-001 (noindexed in sitemaps) and SEO-004 (sitemap bloat)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const DOMAIN = 'https://scwellservice.com';
const ROOT = path.join(__dirname, '..');
const TODAY = new Date().toISOString().split('T')[0];

function isNoindexed(filePath) {
    try {
        const html = fs.readFileSync(filePath, 'utf8');
        return /content\s*=\s*"noindex/i.test(html);
    } catch (e) {
        return true; // skip files we can't read
    }
}

function getFiles(dir, ext = '.html') {
    const full = path.join(ROOT, dir);
    if (!fs.existsSync(full)) return [];
    return fs.readdirSync(full)
        .filter(f => f.endsWith(ext) && f !== 'index.html')
        .map(f => path.join(full, f));
}

function buildUrlset(urls) {
    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';
    for (const u of urls) {
        xml += `  <url><loc>${u.loc}</loc><lastmod>${u.lastmod || TODAY}</lastmod><priority>${u.priority || '0.6'}</priority></url>\n`;
    }
    xml += '</urlset>';
    return xml;
}

// ===== PAGES SITEMAP =====
const pageUrls = [];

// Homepage
pageUrls.push({ loc: `${DOMAIN}/`, priority: '1.0', lastmod: TODAY });

// Static pages
const staticPages = [
    { file: 'contact.html', priority: '0.9' },
    { file: 'faq.html', priority: '0.8' },
    { file: 'cost-calculator.html', priority: '0.8' },
    { file: 'pages/about.html', priority: '0.8' },
    { file: 'blog/index.html', loc: `${DOMAIN}/blog/`, priority: '0.8' },
    { file: 'services/index.html', loc: `${DOMAIN}/services/`, priority: '0.9' },
];

for (const p of staticPages) {
    const filePath = path.join(ROOT, p.file);
    if (fs.existsSync(filePath) && !isNoindexed(filePath)) {
        pageUrls.push({ loc: p.loc || `${DOMAIN}/${p.file}`, priority: p.priority });
    }
}

fs.writeFileSync(path.join(ROOT, 'sitemap-pages.xml'), buildUrlset(pageUrls));
console.log(`sitemap-pages.xml: ${pageUrls.length} URLs`);

// ===== BLOG SITEMAP (only indexed pages) =====
const blogUrls = [];
const blogDir = path.join(ROOT, 'blog');
const blogFiles = fs.readdirSync(blogDir)
    .filter(f => f.endsWith('.html') && f !== 'index.html')
    .sort();

for (const f of blogFiles) {
    const filePath = path.join(blogDir, f);
    if (!isNoindexed(filePath)) {
        const slug = f.replace('.html', '');
        blogUrls.push({ loc: `${DOMAIN}/blog/${slug}`, priority: '0.6' });
    }
}

// Split into chunks of 2500 (sitemap limit is 50,000 but keep manageable)
const CHUNK = 2500;
const blogChunks = [];
for (let i = 0; i < blogUrls.length; i += CHUNK) {
    blogChunks.push(blogUrls.slice(i, i + CHUNK));
}

// Remove old blog sitemaps
for (let i = 1; i <= 10; i++) {
    const old = path.join(ROOT, `sitemap-blog-${i}.xml`);
    if (fs.existsSync(old)) fs.unlinkSync(old);
}

for (let i = 0; i < blogChunks.length; i++) {
    const filename = `sitemap-blog-${i + 1}.xml`;
    fs.writeFileSync(path.join(ROOT, filename), buildUrlset(blogChunks[i]));
    console.log(`${filename}: ${blogChunks[i].length} URLs`);
}

// ===== SERVICES SITEMAP (only indexed) =====
const serviceUrls = [];
const servicesDir = path.join(ROOT, 'services');
if (fs.existsSync(servicesDir)) {
    const serviceDirs = fs.readdirSync(servicesDir).filter(d => {
        const full = path.join(servicesDir, d);
        return fs.statSync(full).isDirectory();
    });
    
    for (const d of serviceDirs) {
        const indexFile = path.join(servicesDir, d, 'index.html');
        if (fs.existsSync(indexFile) && !isNoindexed(indexFile)) {
            serviceUrls.push({ loc: `${DOMAIN}/services/${d}/`, priority: '0.7' });
        }
    }
}

fs.writeFileSync(path.join(ROOT, 'sitemap-services.xml'), buildUrlset(serviceUrls));
console.log(`sitemap-services.xml: ${serviceUrls.length} URLs`);

// ===== CITY WELL DEPTH (keep existing if not noindexed) =====
// These are in blog/ so already handled above

// ===== SITEMAP INDEX =====
let indexXml = '<?xml version="1.0" encoding="UTF-8"?>\n';
indexXml += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';

const sitemapFiles = [
    'sitemap-pages.xml',
    ...blogChunks.map((_, i) => `sitemap-blog-${i + 1}.xml`),
    'sitemap-services.xml',
];

// Only include city-well-depth if it exists and has content
if (fs.existsSync(path.join(ROOT, 'sitemap-city-well-depth.xml'))) {
    sitemapFiles.push('sitemap-city-well-depth.xml');
}

for (const f of sitemapFiles) {
    indexXml += `  <sitemap><loc>${DOMAIN}/${f}</loc><lastmod>${TODAY}</lastmod></sitemap>\n`;
}

indexXml += '</sitemapindex>';
fs.writeFileSync(path.join(ROOT, 'sitemap.xml'), indexXml);

// Remove old sitemap-blog.xml if exists
const oldBlog = path.join(ROOT, 'sitemap-blog.xml');
if (fs.existsSync(oldBlog)) fs.unlinkSync(oldBlog);

// Remove old sitemap-index.xml if exists  
const oldIndex = path.join(ROOT, 'sitemap-index.xml');
if (fs.existsSync(oldIndex)) fs.unlinkSync(oldIndex);

const totalUrls = pageUrls.length + blogUrls.length + serviceUrls.length;
console.log(`\nsitemap.xml: ${sitemapFiles.length} sub-sitemaps`);
console.log(`Total indexed URLs: ${totalUrls}`);
console.log(`\nNoindexed pages excluded: ${blogFiles.length - blogUrls.length} blog pages`);
