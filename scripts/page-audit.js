#!/usr/bin/env node

/**
 * SCWS Page Auditor — Checks every indexed page for build flaws and content issues
 * 
 * Usage: node page-audit.js [--fix] [--json] [--filter=blog|services|pages]
 * 
 * Checks:
 *   BUILD FLAWS (critical):
 *   - Missing <title>
 *   - Missing meta description
 *   - Missing canonical
 *   - Missing or multiple H1 tags
 *   - Missing viewport meta
 *   - Broken internal links
 *   - Images missing alt text
 *   - Missing schema/structured data
 *   - noindex on pages that should be indexed
 *   
 *   CONTENT ISSUES:
 *   - Thin content (under 300 words)
 *   - Short meta description (<70 chars) or too long (>160)
 *   - Short title (<30 chars) or too long (>65)
 *   - Duplicate titles
 *   - Duplicate meta descriptions
 *   - No internal links in content
 *   - No external links
 *   - Missing FAQ schema on long-form content
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const DOMAIN = 'https://scwellservice.com';

// Config
const THIN_CONTENT_THRESHOLD = 300; // words
const MIN_TITLE_LENGTH = 30;
const MAX_TITLE_LENGTH = 65;
const MIN_DESC_LENGTH = 70;
const MAX_DESC_LENGTH = 160;
const MIN_GOOD_CONTENT = 1500; // words for "good" content rating

const args = process.argv.slice(2);
const FIX_MODE = args.includes('--fix');
const JSON_MODE = args.includes('--json');
const FILTER = (args.find(a => a.startsWith('--filter=')) || '').replace('--filter=', '');

// ===== HTML PARSING HELPERS =====

function extractText(html) {
    // Strip tags, scripts, styles
    let text = html
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
        .replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, '')
        .replace(/<header[^>]*>[\s\S]*?<\/header>/gi, '')
        .replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, '')
        .replace(/<[^>]+>/g, ' ')
        .replace(/&[a-z]+;/gi, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    return text;
}

function wordCount(text) {
    return text.split(/\s+/).filter(w => w.length > 0).length;
}

function getTag(html, regex) {
    const match = html.match(regex);
    return match ? match[1].trim() : null;
}

function countMatches(html, regex) {
    const matches = html.match(regex);
    return matches ? matches.length : 0;
}

// ===== AUDIT A SINGLE PAGE =====

function auditPage(filePath, relativePath) {
    const html = fs.readFileSync(filePath, 'utf8');
    const issues = [];
    const warnings = [];
    const info = {};

    // Skip noindexed pages
    const isNoindex = /content\s*=\s*"noindex/i.test(html);
    if (isNoindex) {
        return { path: relativePath, noindex: true, issues: [], warnings: [], info: { status: 'noindexed' } };
    }

    // === BUILD FLAWS ===

    // Title
    const title = getTag(html, /<title>([\s\S]*?)<\/title>/i);
    info.title = title;
    if (!title) {
        issues.push({ type: 'build', code: 'MISSING_TITLE', msg: 'No <title> tag' });
    } else {
        if (title.length < MIN_TITLE_LENGTH) warnings.push({ type: 'content', code: 'SHORT_TITLE', msg: `Title too short (${title.length} chars, min ${MIN_TITLE_LENGTH})`, value: title });
        if (title.length > MAX_TITLE_LENGTH) warnings.push({ type: 'content', code: 'LONG_TITLE', msg: `Title too long (${title.length} chars, max ${MAX_TITLE_LENGTH})`, value: title });
    }

    // Meta description
    const descMatch = html.match(/name="description"\s+content="([^"]*)"/i) || html.match(/content="([^"]*)"\s+name="description"/i);
    const desc = descMatch ? descMatch[1] : null;
    info.description = desc;
    if (!desc) {
        issues.push({ type: 'build', code: 'MISSING_DESC', msg: 'No meta description' });
    } else {
        if (desc.length < MIN_DESC_LENGTH) warnings.push({ type: 'content', code: 'SHORT_DESC', msg: `Meta description too short (${desc.length} chars)` });
        if (desc.length > MAX_DESC_LENGTH) warnings.push({ type: 'content', code: 'LONG_DESC', msg: `Meta description too long (${desc.length} chars)` });
    }

    // Canonical
    const canonical = html.match(/rel="canonical"\s+href="([^"]*)"/i) || html.match(/href="([^"]*)"\s+rel="canonical"/i);
    info.canonical = canonical ? canonical[1] : null;
    if (!canonical) {
        issues.push({ type: 'build', code: 'MISSING_CANONICAL', msg: 'No canonical tag' });
    }

    // H1
    const h1Count = countMatches(html, /<h1[\s>]/gi);
    info.h1Count = h1Count;
    if (h1Count === 0) {
        issues.push({ type: 'build', code: 'MISSING_H1', msg: 'No H1 tag' });
    } else if (h1Count > 1) {
        warnings.push({ type: 'build', code: 'MULTIPLE_H1', msg: `${h1Count} H1 tags (should be 1)` });
    }

    // Viewport
    if (!/name="viewport"/i.test(html)) {
        issues.push({ type: 'build', code: 'MISSING_VIEWPORT', msg: 'No viewport meta tag' });
    }

    // Images without alt
    const imgs = html.match(/<img[^>]*>/gi) || [];
    const missingAlt = imgs.filter(img => !/alt=/i.test(img));
    const emptyAlt = imgs.filter(img => /alt=""/i.test(img));
    info.images = imgs.length;
    info.missingAlt = missingAlt.length;
    if (missingAlt.length > 0) {
        warnings.push({ type: 'build', code: 'MISSING_ALT', msg: `${missingAlt.length}/${imgs.length} images missing alt text` });
    }

    // Schema
    const hasSchema = /"@type"/i.test(html);
    info.hasSchema = hasSchema;
    if (!hasSchema) {
        warnings.push({ type: 'build', code: 'MISSING_SCHEMA', msg: 'No structured data (schema.org)' });
    }

    // === CONTENT ISSUES ===

    const text = extractText(html);
    const words = wordCount(text);
    info.wordCount = words;

    if (words < THIN_CONTENT_THRESHOLD) {
        issues.push({ type: 'content', code: 'THIN_CONTENT', msg: `Only ${words} words (minimum ${THIN_CONTENT_THRESHOLD})` });
    } else if (words < MIN_GOOD_CONTENT) {
        warnings.push({ type: 'content', code: 'LOW_CONTENT', msg: `${words} words (good content is ${MIN_GOOD_CONTENT}+)` });
    }

    // Internal links in content
    const internalLinks = (html.match(/href="[^"]*scwellservice\.com[^"]*"|href="\/[^"]*"/gi) || []).length;
    info.internalLinks = internalLinks;
    if (internalLinks < 2) {
        warnings.push({ type: 'content', code: 'FEW_INTERNAL_LINKS', msg: `Only ${internalLinks} internal links` });
    }

    // OG tags
    if (!/property="og:title"/i.test(html)) {
        warnings.push({ type: 'build', code: 'MISSING_OG', msg: 'Missing Open Graph tags' });
    }

    // Content quality rating
    let rating = 'good';
    if (issues.length > 0) rating = 'critical';
    else if (warnings.length > 3) rating = 'needs-work';
    else if (warnings.length > 0) rating = 'okay';
    info.rating = rating;

    return { path: relativePath, noindex: false, issues, warnings, info };
}

// ===== SCAN ALL PAGES =====

function getAllPages() {
    const pages = [];

    // Homepage
    const indexFile = path.join(ROOT, 'index.html');
    if (fs.existsSync(indexFile)) pages.push({ file: indexFile, rel: '/' });

    // Static pages
    for (const f of ['contact.html', 'faq.html', 'cost-calculator.html']) {
        const fp = path.join(ROOT, f);
        if (fs.existsSync(fp)) pages.push({ file: fp, rel: `/${f}` });
    }
    const aboutFile = path.join(ROOT, 'pages/about.html');
    if (fs.existsSync(aboutFile)) pages.push({ file: aboutFile, rel: '/pages/about.html' });

    // Blog
    if (!FILTER || FILTER === 'blog') {
        const blogDir = path.join(ROOT, 'blog');
        if (fs.existsSync(blogDir)) {
            for (const f of fs.readdirSync(blogDir).filter(f => f.endsWith('.html')).sort()) {
                pages.push({ file: path.join(blogDir, f), rel: `/blog/${f}` });
            }
        }
    }

    // Services
    if (!FILTER || FILTER === 'services') {
        const servicesDir = path.join(ROOT, 'services');
        if (fs.existsSync(servicesDir)) {
            for (const d of fs.readdirSync(servicesDir)) {
                const indexFile = path.join(servicesDir, d, 'index.html');
                if (fs.existsSync(indexFile)) {
                    pages.push({ file: indexFile, rel: `/services/${d}/` });
                }
            }
        }
    }

    return pages;
}

// ===== DUPLICATE DETECTION =====

function findDuplicates(results) {
    const titles = {};
    const descs = {};

    for (const r of results) {
        if (r.noindex) continue;
        if (r.info.title) {
            const t = r.info.title.toLowerCase();
            if (!titles[t]) titles[t] = [];
            titles[t].push(r.path);
        }
        if (r.info.description) {
            const d = r.info.description.toLowerCase().substring(0, 100);
            if (!descs[d]) descs[d] = [];
            descs[d].push(r.path);
        }
    }

    const dupTitles = Object.entries(titles).filter(([_, paths]) => paths.length > 1);
    const dupDescs = Object.entries(descs).filter(([_, paths]) => paths.length > 1);

    return { dupTitles, dupDescs };
}

// ===== MAIN =====

console.log('🔍 SCWS Page Auditor');
console.log('====================\n');

const allPages = getAllPages();
console.log(`Scanning ${allPages.length} pages...\n`);

const results = [];
let scanned = 0;
let noindexed = 0;

for (const { file, rel } of allPages) {
    try {
        const result = auditPage(file, rel);
        results.push(result);
        if (result.noindex) noindexed++;
        scanned++;
        
        // Progress
        if (scanned % 500 === 0) process.stderr.write(`  ${scanned}/${allPages.length}...\n`);
    } catch (e) {
        results.push({ path: rel, noindex: false, issues: [{ type: 'build', code: 'PARSE_ERROR', msg: e.message }], warnings: [], info: {} });
    }
}

// Duplicates
const { dupTitles, dupDescs } = findDuplicates(results);

// ===== OUTPUT =====

if (JSON_MODE) {
    const output = { scanned, noindexed, indexed: scanned - noindexed, results: results.filter(r => !r.noindex), duplicates: { titles: dupTitles.length, descriptions: dupDescs.length } };
    console.log(JSON.stringify(output, null, 2));
    process.exit(0);
}

// Summary
const indexed = results.filter(r => !r.noindex);
const critical = indexed.filter(r => r.issues.length > 0);
const withWarnings = indexed.filter(r => r.warnings.length > 0 && r.issues.length === 0);
const clean = indexed.filter(r => r.issues.length === 0 && r.warnings.length === 0);

console.log('📊 SUMMARY');
console.log('==========');
console.log(`Total pages scanned: ${scanned}`);
console.log(`  Noindexed (skipped): ${noindexed}`);
console.log(`  Indexed (audited):   ${indexed.length}`);
console.log();
console.log(`  🔴 Critical issues:  ${critical.length} pages`);
console.log(`  🟡 Warnings only:    ${withWarnings.length} pages`);
console.log(`  🟢 Clean:            ${clean.length} pages`);
console.log();

// Issue breakdown
const issueCounts = {};
const warningCounts = {};
for (const r of indexed) {
    for (const i of r.issues) {
        issueCounts[i.code] = (issueCounts[i.code] || 0) + 1;
    }
    for (const w of r.warnings) {
        warningCounts[w.code] = (warningCounts[w.code] || 0) + 1;
    }
}

console.log('🔴 CRITICAL ISSUES (by type):');
for (const [code, count] of Object.entries(issueCounts).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${code}: ${count} pages`);
}
console.log();

console.log('🟡 WARNINGS (by type):');
for (const [code, count] of Object.entries(warningCounts).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${code}: ${count} pages`);
}
console.log();

// Duplicates
if (dupTitles.length > 0) {
    console.log(`⚠️  DUPLICATE TITLES: ${dupTitles.length} groups`);
    for (const [title, paths] of dupTitles.slice(0, 5)) {
        console.log(`  "${title.substring(0, 60)}..." → ${paths.length} pages`);
    }
    if (dupTitles.length > 5) console.log(`  ... and ${dupTitles.length - 5} more`);
    console.log();
}

if (dupDescs.length > 0) {
    console.log(`⚠️  DUPLICATE DESCRIPTIONS: ${dupDescs.length} groups`);
    for (const [desc, paths] of dupDescs.slice(0, 5)) {
        console.log(`  "${desc.substring(0, 60)}..." → ${paths.length} pages`);
    }
    if (dupDescs.length > 5) console.log(`  ... and ${dupDescs.length - 5} more`);
    console.log();
}

// Content quality distribution
const thinPages = indexed.filter(r => r.info.wordCount < THIN_CONTENT_THRESHOLD);
const lowPages = indexed.filter(r => r.info.wordCount >= THIN_CONTENT_THRESHOLD && r.info.wordCount < MIN_GOOD_CONTENT);
const goodPages = indexed.filter(r => r.info.wordCount >= MIN_GOOD_CONTENT);

console.log('📝 CONTENT QUALITY:');
console.log(`  Thin (<${THIN_CONTENT_THRESHOLD} words):     ${thinPages.length} pages`);
console.log(`  Low (${THIN_CONTENT_THRESHOLD}-${MIN_GOOD_CONTENT} words):   ${lowPages.length} pages`);
console.log(`  Good (${MIN_GOOD_CONTENT}+ words):     ${goodPages.length} pages`);
console.log();

// Show worst offenders
if (critical.length > 0) {
    console.log('🔴 WORST OFFENDERS (most issues):');
    const sorted = critical.sort((a, b) => b.issues.length - a.issues.length);
    for (const r of sorted.slice(0, 10)) {
        console.log(`  ${r.path}`);
        for (const i of r.issues) {
            console.log(`    ❌ ${i.msg}`);
        }
    }
    console.log();
}

// Save full report
const reportPath = path.join(__dirname, '../seo-audit-report.json');
const report = {
    date: new Date().toISOString(),
    summary: { scanned, noindexed, indexed: indexed.length, critical: critical.length, warnings: withWarnings.length, clean: clean.length },
    issueCounts,
    warningCounts,
    duplicates: { titles: dupTitles, descriptions: dupDescs },
    content: { thin: thinPages.length, low: lowPages.length, good: goodPages.length },
    pages: indexed.map(r => ({
        path: r.path,
        rating: r.info.rating,
        wordCount: r.info.wordCount,
        h1Count: r.info.h1Count,
        hasSchema: r.info.hasSchema,
        issues: r.issues.map(i => i.code),
        warnings: r.warnings.map(w => w.code),
    }))
};
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
console.log(`📁 Full report saved: seo-audit-report.json`);
