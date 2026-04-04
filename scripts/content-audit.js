#!/usr/bin/env node

/**
 * SCWS Content Quality Auditor
 * 
 * Not just "does the page exist" — does it actually serve the reader?
 * Scores every indexed page on real content quality signals.
 * 
 * Usage:
 *   node content-audit.js                      # audit all indexed pages
 *   node content-audit.js --filter=blog        # blog only
 *   node content-audit.js --min-score=60       # only show pages scoring below 60
 *   node content-audit.js --top=50             # show 50 worst pages
 *   node content-audit.js --page=/blog/xyz     # audit single page
 * 
 * Scoring (0-100):
 *   DEPTH (40 pts):
 *     - Word count (0-15 pts): <500=0, 500-1000=5, 1000-2000=10, 2000+=15
 *     - Heading structure (0-10 pts): H2 count, H3 usage, logical hierarchy
 *     - Paragraphs & sections (0-10 pts): proper content blocks, not walls of text
 *     - Lists/tables (0-5 pts): structured data for scannability
 *   
 *   SPECIFICITY (25 pts):
 *     - Numbers/data (0-8 pts): costs, measurements, percentages, stats
 *     - Local references (0-7 pts): San Diego, city names, CA, local context
 *     - Brand/product names (0-5 pts): Franklin, Grundfos, specific equipment
 *     - Phone/CTA present (0-5 pts): actionable next steps for reader
 *   
 *   STRUCTURE (20 pts):
 *     - Has intro paragraph (0-5 pts): hooks reader, sets expectations
 *     - Has FAQ section (0-5 pts): answers common questions
 *     - Internal links (0-5 pts): connects to related content
 *     - Images with context (0-5 pts): relevant images, not just decorative
 *   
 *   READABILITY (15 pts):
 *     - Sentence variety (0-5 pts): not all same length
 *     - Short paragraphs (0-5 pts): <150 words per paragraph avg
 *     - Active voice indicators (0-5 pts): direct, clear writing
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const args = process.argv.slice(2);
const FILTER = (args.find(a => a.startsWith('--filter=')) || '').replace('--filter=', '');
const MIN_SCORE = parseInt((args.find(a => a.startsWith('--min-score=')) || '--min-score=0').replace('--min-score=', ''));
const TOP_N = parseInt((args.find(a => a.startsWith('--top=')) || '--top=25').replace('--top=', ''));
const SINGLE_PAGE = (args.find(a => a.startsWith('--page=')) || '').replace('--page=', '');

// ===== LOCAL CONTEXT =====
const LOCAL_CITIES = [
    'ramona', 'anza', 'julian', 'fallbrook', 'temecula', 'murrieta', 'escondido',
    'valley center', 'poway', 'alpine', 'borrego', 'san diego', 'riverside',
    'san bernardino', 'hemet', 'aguanga', 'palomar', 'warner springs', 'lakeside',
    'el cajon', 'jamul', 'campo', 'descanso', 'pine valley', 'potrero', 'dulzura',
    'bonsall', 'vista', 'oceanside', 'carlsbad', 'encinitas', 'rancho santa fe',
    'menifee', 'winchester', 'sun city', 'perris', 'lake elsinore', 'wildomar',
    'redlands', 'yucaipa', 'beaumont', 'banning', 'calimesa', 'cherry valley',
    'san jacinto', 'idyllwild', 'mountain center', 'thermal', 'coachella',
    'southern california', 'socal', 'inland empire', 'north county'
];

const WELL_BRANDS = [
    'franklin', 'grundfos', 'goulds', 'sta-rite', 'pentair', 'flotec', 'red lion',
    'berkeley', 'myers', 'aermotor', 'dempster', 'gefco', 'speedstar',
    'submersible', 'jet pump', 'constant pressure', 'variable frequency', 'vfd'
];

// ===== HTML HELPERS =====

function stripToContent(html) {
    return html
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
        .replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, '')
        .replace(/<header[^>]*>[\s\S]*?<\/header>/gi, '')
        .replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, '');
}

function getText(html) {
    return stripToContent(html).replace(/<[^>]+>/g, ' ').replace(/&[a-z]+;/gi, ' ').replace(/\s+/g, ' ').trim();
}

function countPattern(text, patterns) {
    let count = 0;
    const lower = text.toLowerCase();
    for (const p of patterns) {
        const regex = new RegExp(`\\b${p}\\b`, 'gi');
        const matches = lower.match(regex);
        if (matches) count += matches.length;
    }
    return count;
}

// ===== SCORING =====

function auditContent(html, filePath) {
    const content = stripToContent(html);
    const text = getText(html);
    const textLower = text.toLowerCase();
    const words = text.split(/\s+/).filter(w => w.length > 0);
    const wordCount = words.length;
    
    const scores = {};
    const details = {};
    
    // ===== DEPTH (40 pts) =====
    
    // Word count (0-15)
    let wordScore = 0;
    if (wordCount >= 2500) wordScore = 15;
    else if (wordCount >= 2000) wordScore = 13;
    else if (wordCount >= 1500) wordScore = 11;
    else if (wordCount >= 1000) wordScore = 8;
    else if (wordCount >= 500) wordScore = 5;
    else if (wordCount >= 300) wordScore = 2;
    scores.wordCount = wordScore;
    details.wordCount = wordCount;
    
    // Heading structure (0-10)
    const h2Count = (content.match(/<h2[\s>]/gi) || []).length;
    const h3Count = (content.match(/<h3[\s>]/gi) || []).length;
    let headingScore = 0;
    if (h2Count >= 5) headingScore += 5;
    else if (h2Count >= 3) headingScore += 3;
    else if (h2Count >= 1) headingScore += 1;
    if (h3Count >= 3) headingScore += 3;
    else if (h3Count >= 1) headingScore += 1;
    if (h2Count > 0 && h3Count > 0) headingScore += 2; // hierarchy bonus
    headingScore = Math.min(10, headingScore);
    scores.headings = headingScore;
    details.h2Count = h2Count;
    details.h3Count = h3Count;
    
    // Paragraphs & sections (0-10)
    const paragraphs = (content.match(/<p[\s>]/gi) || []).length;
    let paraScore = 0;
    if (paragraphs >= 10) paraScore = 7;
    else if (paragraphs >= 5) paraScore = 4;
    else if (paragraphs >= 2) paraScore = 2;
    // Check for proper sections
    const sections = (content.match(/<section[\s>]/gi) || []).length;
    const divBlocks = (content.match(/<div[^>]*class="[^"]*(?:section|block|content|prose)[^"]*"/gi) || []).length;
    if (sections + divBlocks >= 3) paraScore += 3;
    else if (sections + divBlocks >= 1) paraScore += 1;
    paraScore = Math.min(10, paraScore);
    scores.paragraphs = paraScore;
    details.paragraphs = paragraphs;
    
    // Lists/tables (0-5)
    const lists = (content.match(/<(?:ul|ol)[\s>]/gi) || []).length;
    const tables = (content.match(/<table[\s>]/gi) || []).length;
    let listScore = 0;
    if (lists >= 3 || tables >= 1) listScore = 5;
    else if (lists >= 2) listScore = 3;
    else if (lists >= 1) listScore = 2;
    if (tables >= 1) listScore = Math.min(5, listScore + 2);
    scores.lists = listScore;
    details.lists = lists;
    details.tables = tables;
    
    // ===== SPECIFICITY (25 pts) =====
    
    // Numbers/data (0-8)
    const numbers = (text.match(/\$[\d,]+|\d+%|\d+ (?:feet|ft|gallons|gpm|psi|hp|inch|hours?|days?|years?|miles?)/gi) || []).length;
    const costMentions = (textLower.match(/cost|price|average|typically|ranges? from|starts? at|between \$/g) || []).length;
    let numberScore = 0;
    if (numbers >= 10) numberScore = 6;
    else if (numbers >= 5) numberScore = 4;
    else if (numbers >= 2) numberScore = 2;
    if (costMentions >= 3) numberScore += 2;
    else if (costMentions >= 1) numberScore += 1;
    numberScore = Math.min(8, numberScore);
    scores.numbers = numberScore;
    details.numberMentions = numbers;
    
    // Local references (0-7)
    const localCount = countPattern(textLower, LOCAL_CITIES);
    let localScore = 0;
    if (localCount >= 8) localScore = 7;
    else if (localCount >= 5) localScore = 5;
    else if (localCount >= 3) localScore = 3;
    else if (localCount >= 1) localScore = 1;
    scores.local = localScore;
    details.localRefs = localCount;
    
    // Brand/product names (0-5)
    const brandCount = countPattern(textLower, WELL_BRANDS);
    let brandScore = 0;
    if (brandCount >= 5) brandScore = 5;
    else if (brandCount >= 3) brandScore = 3;
    else if (brandCount >= 1) brandScore = 1;
    scores.brands = brandScore;
    details.brandRefs = brandCount;
    
    // Phone/CTA (0-5)
    const hasPhone = /760.*440.*8520|tel:/i.test(html);
    const hasCTA = /free estimate|call us|contact|get a quote|schedule|book/i.test(textLower);
    const hasCtaButton = /<a[^>]*class="[^"]*(?:btn|button|cta|bg-red|bg-primary)[^"]*"[^>]*>/i.test(content);
    let ctaScore = 0;
    if (hasPhone) ctaScore += 2;
    if (hasCTA) ctaScore += 1;
    if (hasCtaButton) ctaScore += 2;
    ctaScore = Math.min(5, ctaScore);
    scores.cta = ctaScore;
    details.hasPhone = hasPhone;
    details.hasCTA = hasCTA;
    
    // ===== STRUCTURE (20 pts) =====
    
    // Intro paragraph (0-5) — first <p> should be substantial
    const firstPMatch = content.match(/<p[^>]*>([\s\S]*?)<\/p>/i);
    const firstPText = firstPMatch ? firstPMatch[1].replace(/<[^>]+>/g, '').trim() : '';
    const firstPWords = firstPText.split(/\s+/).length;
    let introScore = 0;
    if (firstPWords >= 40) introScore = 5;
    else if (firstPWords >= 25) introScore = 3;
    else if (firstPWords >= 10) introScore = 1;
    scores.intro = introScore;
    details.introWords = firstPWords;
    
    // FAQ section (0-5)
    const hasFAQ = /faq|frequently asked|common questions/i.test(content);
    const hasSchemaFAQ = /"FAQPage"/i.test(html);
    let faqScore = 0;
    if (hasFAQ && hasSchemaFAQ) faqScore = 5;
    else if (hasFAQ) faqScore = 3;
    scores.faq = faqScore;
    
    // Internal links (0-5)
    const internalLinks = (content.match(/href="(?:\/|https?:\/\/(?:www\.)?scwellservice\.com)[^"]*"/gi) || []).length;
    let linkScore = 0;
    if (internalLinks >= 8) linkScore = 5;
    else if (internalLinks >= 4) linkScore = 3;
    else if (internalLinks >= 2) linkScore = 2;
    else if (internalLinks >= 1) linkScore = 1;
    scores.internalLinks = linkScore;
    details.internalLinks = internalLinks;
    
    // Images with context (0-5)
    const images = (content.match(/<img[^>]*>/gi) || []);
    const imagesWithAlt = images.filter(i => {
        const altMatch = i.match(/alt="([^"]*)"/i);
        return altMatch && altMatch[1].length > 10; // meaningful alt text
    }).length;
    let imgScore = 0;
    if (imagesWithAlt >= 3) imgScore = 5;
    else if (imagesWithAlt >= 2) imgScore = 3;
    else if (imagesWithAlt >= 1) imgScore = 2;
    scores.images = imgScore;
    details.images = images.length;
    details.imagesWithGoodAlt = imagesWithAlt;
    
    // ===== READABILITY (15 pts) =====
    
    // Sentence variety (0-5)
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 5);
    const sentLengths = sentences.map(s => s.trim().split(/\s+/).length);
    const avgSentLen = sentLengths.length > 0 ? sentLengths.reduce((a, b) => a + b, 0) / sentLengths.length : 0;
    const sentVariance = sentLengths.length > 1 ? 
        sentLengths.reduce((sum, l) => sum + Math.pow(l - avgSentLen, 2), 0) / sentLengths.length : 0;
    const sentStdDev = Math.sqrt(sentVariance);
    let sentScore = 0;
    if (sentStdDev >= 8) sentScore = 5;
    else if (sentStdDev >= 5) sentScore = 3;
    else if (sentStdDev >= 3) sentScore = 2;
    scores.sentenceVariety = sentScore;
    details.avgSentenceLength = Math.round(avgSentLen);
    
    // Short paragraphs (0-5)
    const pTexts = (content.match(/<p[^>]*>([\s\S]*?)<\/p>/gi) || [])
        .map(p => p.replace(/<[^>]+>/g, '').trim().split(/\s+/).length);
    const avgParaLen = pTexts.length > 0 ? pTexts.reduce((a, b) => a + b, 0) / pTexts.length : 0;
    let paraLenScore = 0;
    if (avgParaLen > 0 && avgParaLen <= 80) paraLenScore = 5;
    else if (avgParaLen <= 120) paraLenScore = 3;
    else if (avgParaLen <= 150) paraLenScore = 1;
    scores.paraLength = paraLenScore;
    details.avgParaWords = Math.round(avgParaLen);
    
    // Active voice / directness (0-5)
    const activePatterns = /\byou\b|\byour\b|\bwe\b|\bour\b|\bcall\b|\bcheck\b|\binstall\b|\breplace\b|\bfix\b/gi;
    const activeCount = (textLower.match(activePatterns) || []).length;
    const passivePatterns = /\bis done\b|\bwas installed\b|\bcan be\b|\bshould be\b|\bmay be\b/gi;
    const passiveCount = (textLower.match(passivePatterns) || []).length;
    let voiceScore = 0;
    const activeRatio = activeCount / Math.max(1, activeCount + passiveCount);
    if (activeRatio >= 0.8) voiceScore = 5;
    else if (activeRatio >= 0.6) voiceScore = 3;
    else if (activeRatio >= 0.4) voiceScore = 1;
    scores.voice = voiceScore;
    
    // ===== TOTAL =====
    const total = Object.values(scores).reduce((a, b) => a + b, 0);
    
    // Grade
    let grade;
    if (total >= 80) grade = 'A';
    else if (total >= 65) grade = 'B';
    else if (total >= 50) grade = 'C';
    else if (total >= 35) grade = 'D';
    else grade = 'F';
    
    return { total, grade, scores, details };
}

// ===== MAIN =====

function getAllPages() {
    const pages = [];
    
    if (!FILTER || FILTER === 'pages') {
        for (const f of ['index.html', 'contact.html', 'faq.html', 'cost-calculator.html']) {
            const fp = path.join(ROOT, f);
            if (fs.existsSync(fp)) pages.push({ file: fp, rel: `/${f}` });
        }
    }
    
    if (!FILTER || FILTER === 'blog') {
        const blogDir = path.join(ROOT, 'blog');
        if (fs.existsSync(blogDir)) {
            for (const f of fs.readdirSync(blogDir).filter(f => f.endsWith('.html')).sort()) {
                pages.push({ file: path.join(blogDir, f), rel: `/blog/${f.replace('.html', '')}` });
            }
        }
    }
    
    if (!FILTER || FILTER === 'services') {
        const servicesDir = path.join(ROOT, 'services');
        if (fs.existsSync(servicesDir)) {
            for (const d of fs.readdirSync(servicesDir)) {
                const idx = path.join(servicesDir, d, 'index.html');
                if (fs.existsSync(idx)) pages.push({ file: idx, rel: `/services/${d}/` });
            }
        }
    }
    
    return pages;
}

console.log('📝 SCWS Content Quality Auditor');
console.log('================================\n');

const allPages = getAllPages();
const results = [];

for (const { file, rel } of allPages) {
    try {
        const html = fs.readFileSync(file, 'utf8');
        if (/content\s*=\s*"noindex/i.test(html)) continue;
        
        if (SINGLE_PAGE && !rel.includes(SINGLE_PAGE)) continue;
        
        const result = auditContent(html, file);
        results.push({ path: rel, ...result });
    } catch (e) {}
    
    if (results.length % 500 === 0 && results.length > 0) {
        process.stderr.write(`  ${results.length} pages audited...\n`);
    }
}

// Sort by score ascending (worst first)
results.sort((a, b) => a.total - b.total);

// ===== OUTPUT =====

// Grade distribution
const grades = { A: 0, B: 0, C: 0, D: 0, F: 0 };
for (const r of results) grades[r.grade]++;

console.log(`Audited: ${results.length} indexed pages\n`);

console.log('📊 GRADE DISTRIBUTION:');
console.log(`  A (80-100): ${grades.A} pages  ${'█'.repeat(Math.ceil(grades.A / Math.max(1, results.length) * 50))}`);
console.log(`  B (65-79):  ${grades.B} pages  ${'█'.repeat(Math.ceil(grades.B / Math.max(1, results.length) * 50))}`);
console.log(`  C (50-64):  ${grades.C} pages  ${'█'.repeat(Math.ceil(grades.C / Math.max(1, results.length) * 50))}`);
console.log(`  D (35-49):  ${grades.D} pages  ${'█'.repeat(Math.ceil(grades.D / Math.max(1, results.length) * 50))}`);
console.log(`  F (0-34):   ${grades.F} pages  ${'█'.repeat(Math.ceil(grades.F / Math.max(1, results.length) * 50))}`);
console.log();

// Average scores by category
const catTotals = {};
const catCounts = {};
for (const r of results) {
    for (const [cat, score] of Object.entries(r.scores)) {
        catTotals[cat] = (catTotals[cat] || 0) + score;
        catCounts[cat] = (catCounts[cat] || 0) + 1;
    }
}

console.log('📈 AVERAGE SCORES BY CATEGORY:');
const maxPoints = {
    wordCount: 15, headings: 10, paragraphs: 10, lists: 5,
    numbers: 8, local: 7, brands: 5, cta: 5,
    intro: 5, faq: 5, internalLinks: 5, images: 5,
    sentenceVariety: 5, paraLength: 5, voice: 5
};
const categoryGroups = {
    'DEPTH (40pts)': ['wordCount', 'headings', 'paragraphs', 'lists'],
    'SPECIFICITY (25pts)': ['numbers', 'local', 'brands', 'cta'],
    'STRUCTURE (20pts)': ['intro', 'faq', 'internalLinks', 'images'],
    'READABILITY (15pts)': ['sentenceVariety', 'paraLength', 'voice']
};

for (const [group, cats] of Object.entries(categoryGroups)) {
    console.log(`  ${group}:`);
    for (const cat of cats) {
        const avg = catTotals[cat] / Math.max(1, catCounts[cat]);
        const max = maxPoints[cat];
        const pct = Math.round(avg / max * 100);
        const bar = '█'.repeat(Math.round(pct / 5)) + '░'.repeat(20 - Math.round(pct / 5));
        console.log(`    ${cat.padEnd(18)} ${avg.toFixed(1)}/${max}  ${bar} ${pct}%`);
    }
}
console.log();

// Worst pages
const showCount = SINGLE_PAGE ? results.length : Math.min(TOP_N, results.filter(r => MIN_SCORE ? r.total < MIN_SCORE : true).length);
const filtered = MIN_SCORE ? results.filter(r => r.total < MIN_SCORE) : results;

console.log(`🔴 ${SINGLE_PAGE ? 'PAGE DETAIL' : `BOTTOM ${showCount} PAGES`}:`);
console.log('-'.repeat(80));

for (const r of filtered.slice(0, showCount)) {
    console.log(`${r.grade} ${String(r.total).padStart(3)}/100  ${r.path}`);
    console.log(`         Words: ${r.details.wordCount} | H2: ${r.details.h2Count} | H3: ${r.details.h3Count} | Links: ${r.details.internalLinks} | Images: ${r.details.images}`);
    
    // Show weakest areas
    const weakest = Object.entries(r.scores)
        .map(([k, v]) => ({ cat: k, score: v, max: maxPoints[k], pct: v / maxPoints[k] }))
        .filter(s => s.pct < 0.4)
        .sort((a, b) => a.pct - b.pct)
        .slice(0, 3);
    
    if (weakest.length > 0) {
        console.log(`         Weak: ${weakest.map(w => `${w.cat} (${w.score}/${w.max})`).join(', ')}`);
    }
    console.log();
}

// Best pages (top 10)
if (!SINGLE_PAGE) {
    console.log(`\n🟢 TOP 10 PAGES:`);
    console.log('-'.repeat(80));
    for (const r of results.slice(-10).reverse()) {
        console.log(`${r.grade} ${String(r.total).padStart(3)}/100  ${r.path}`);
    }
}

// Save report
const reportPath = path.join(ROOT, 'content-quality-report.json');
fs.writeFileSync(reportPath, JSON.stringify({
    date: new Date().toISOString(),
    summary: { total: results.length, grades, avgScore: Math.round(results.reduce((s, r) => s + r.total, 0) / results.length) },
    pages: results.map(r => ({ path: r.path, score: r.total, grade: r.grade, wordCount: r.details.wordCount, scores: r.scores }))
}, null, 2));

console.log(`\n📁 Full report: content-quality-report.json`);
console.log(`📊 Average score: ${Math.round(results.reduce((s, r) => s + r.total, 0) / results.length)}/100`);
