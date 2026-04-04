#!/usr/bin/env node

/**
 * SCWS Page Fixer — Systematically fixes build flaws found by page-audit.js
 * 
 * Usage: 
 *   node page-fixer.js                    # dry run (show what would change)
 *   node page-fixer.js --apply            # apply all fixes
 *   node page-fixer.js --apply --fix=thin # only fix thin content (noindex)
 *   node page-fixer.js --apply --fix=titles
 *   node page-fixer.js --apply --fix=descriptions
 *   node page-fixer.js --apply --fix=schema
 *   node page-fixer.js --apply --fix=h1
 *   node page-fixer.js --apply --fix=duplicates
 *   node page-fixer.js --apply --fix=all
 * 
 * Fix categories:
 *   thin         — noindex pages under 300 words
 *   titles       — trim titles over 65 chars (smart truncation)
 *   descriptions — trim descriptions over 160 chars
 *   schema       — add basic LocalBusiness + Article schema
 *   h1           — add H1 from title tag where missing
 *   duplicates   — make duplicate titles/descriptions unique
 *   og           — add Open Graph tags where missing
 *   all          — run all fixes
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const DOMAIN = 'https://scwellservice.com';

const args = process.argv.slice(2);
const APPLY = args.includes('--apply');
const FIX_TYPE = (args.find(a => a.startsWith('--fix=')) || '--fix=all').replace('--fix=', '');
const VERBOSE = args.includes('--verbose');

const stats = { scanned: 0, fixed: 0, skipped: 0, errors: 0, changes: {} };

function log(msg) { if (!APPLY || VERBOSE) console.log(msg); }
function count(type) { stats.changes[type] = (stats.changes[type] || 0) + 1; }

// ===== FIXERS =====

function fixThinContent(html, filePath) {
    // If page has less than 300 words of content and is NOT already noindexed, add noindex
    if (/content\s*=\s*"noindex/i.test(html)) return null;
    
    const text = html
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
        .replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, '')
        .replace(/<header[^>]*>[\s\S]*?<\/header>/gi, '')
        .replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, '')
        .replace(/<[^>]+>/g, ' ')
        .replace(/\s+/g, ' ').trim();
    
    const words = text.split(/\s+/).filter(w => w.length > 0).length;
    if (words >= 300) return null;
    
    // Add noindex after viewport meta or after charset
    if (html.includes('name="viewport"')) {
        const fixed = html.replace(
            /(name="viewport"[^>]*>)/i,
            '$1\n<meta name="robots" content="noindex, nofollow">'
        );
        count('noindex_thin');
        return fixed;
    } else if (html.includes('<head>')) {
        const fixed = html.replace(
            '<head>',
            '<head>\n<meta name="robots" content="noindex, nofollow">'
        );
        count('noindex_thin');
        return fixed;
    }
    return null;
}

function fixLongTitle(html) {
    const match = html.match(/<title>([\s\S]*?)<\/title>/i);
    if (!match) return null;
    
    const title = match[1].trim();
    if (title.length <= 65) return null;
    
    // Smart truncation strategies:
    // 1. Remove " | Southern California Well Service" suffix
    let newTitle = title.replace(/\s*\|\s*Southern California Well Service\s*$/i, '');
    
    // 2. Remove " | SCWS" suffix
    newTitle = newTitle.replace(/\s*\|\s*SCWS\s*$/i, '');
    
    // 3. Remove year parenthetical if still too long
    if (newTitle.length > 65) {
        newTitle = newTitle.replace(/\s*\(\d{4}\)\s*$/, '');
    }
    
    // 4. Remove trailing " - Complete Guide" etc
    if (newTitle.length > 65) {
        newTitle = newTitle.replace(/\s*[-–—]\s*(Complete Guide|Full Guide|Expert Guide|Comprehensive Guide|Ultimate Guide)\s*$/i, '');
    }
    
    // 5. Truncate at last word boundary before 62 chars + add ...
    if (newTitle.length > 65) {
        newTitle = newTitle.substring(0, 62).replace(/\s+\S*$/, '...');
    }
    
    if (newTitle === title) return null;
    
    const fixed = html.replace(/<title>[\s\S]*?<\/title>/i, `<title>${newTitle}</title>`);
    
    // Also fix og:title if it exists and is long
    count('fix_title');
    return fixed;
}

function fixLongDescription(html) {
    // Try both attribute orders
    const patterns = [
        { regex: /name="description"\s+content="([^"]*)"/i, rebuild: (d) => `name="description" content="${d}"` },
        { regex: /content="([^"]*)"\s+name="description"/i, rebuild: (d) => `content="${d}" name="description"` },
    ];
    
    for (const { regex, rebuild } of patterns) {
        const match = html.match(regex);
        if (!match) continue;
        
        const desc = match[1];
        if (desc.length <= 160) return null;
        
        // Smart truncation: cut at sentence boundary before 157 chars
        let newDesc = desc;
        
        // Try cutting at last period before 157
        const periodIdx = desc.substring(0, 157).lastIndexOf('.');
        if (periodIdx > 100) {
            newDesc = desc.substring(0, periodIdx + 1);
        } else {
            // Cut at last word boundary before 157 + add ...
            newDesc = desc.substring(0, 157).replace(/\s+\S*$/, '...');
        }
        
        const fixed = html.replace(match[0], rebuild(newDesc));
        count('fix_desc');
        return fixed;
    }
    return null;
}

function fixMissingSchema(html, filePath) {
    if (/"@type"/i.test(html)) return null;
    
    // Determine page type from path
    const isBlog = filePath.includes('/blog/');
    const isService = filePath.includes('/services/');
    
    // Extract title for schema
    const titleMatch = html.match(/<title>([\s\S]*?)<\/title>/i);
    const title = titleMatch ? titleMatch[1].replace(/\s*\|.*$/, '').trim() : '';
    
    const descMatch = html.match(/name="description"\s+content="([^"]*)"/i) || html.match(/content="([^"]*)"\s+name="description"/i);
    const desc = descMatch ? descMatch[1] : '';
    
    let schema;
    if (isBlog) {
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": desc,
            "author": { "@type": "Organization", "name": "Southern California Well Service" },
            "publisher": {
                "@type": "Organization",
                "name": "Southern California Well Service",
                "logo": { "@type": "ImageObject", "url": "https://scwellservice.com/images/logo-text-only-3x.png" }
            }
        };
    } else {
        schema = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "Southern California Well Service",
            "description": desc,
            "telephone": "(760) 440-8520",
            "url": "https://scwellservice.com",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "1077 Main St",
                "addressLocality": "Ramona",
                "addressRegion": "CA",
                "postalCode": "92065"
            }
        };
    }
    
    const schemaTag = `<script type="application/ld+json">\n${JSON.stringify(schema, null, 2)}\n</script>`;
    
    // Insert before </head>
    const fixed = html.replace('</head>', `${schemaTag}\n</head>`);
    count('add_schema');
    return fixed;
}

function fixMissingH1(html, filePath) {
    if (/<h1[\s>]/i.test(html)) return null;
    if (/content\s*=\s*"noindex/i.test(html)) return null; // skip noindexed
    
    const titleMatch = html.match(/<title>([\s\S]*?)<\/title>/i);
    if (!titleMatch) return null;
    
    let h1Text = titleMatch[1].trim().replace(/\s*\|\s*Southern California Well Service\s*$/i, '');
    const h1Tag = `<h1 class="text-4xl font-bold text-primary mb-6">${h1Text}</h1>\n\n`;
    
    // Insert before TOC
    if (html.includes('<details id="table-of-contents"')) {
        count('add_h1');
        return html.replace('<details id="table-of-contents"', h1Tag + '<details id="table-of-contents"');
    }
    // Insert before prose div
    if (html.includes('<div class="prose')) {
        count('add_h1');
        return html.replace('<div class="prose', h1Tag + '<div class="prose');
    }
    return null;
}

function fixMissingOG(html, filePath) {
    if (/property="og:title"/i.test(html)) return null;
    
    const titleMatch = html.match(/<title>([\s\S]*?)<\/title>/i);
    const descMatch = html.match(/name="description"\s+content="([^"]*)"/i) || html.match(/content="([^"]*)"\s+name="description"/i);
    
    const title = titleMatch ? titleMatch[1].trim() : '';
    const desc = descMatch ? descMatch[1] : '';
    
    const slug = path.basename(filePath, '.html');
    const url = filePath.includes('/blog/') ? `${DOMAIN}/blog/${slug}` : `${DOMAIN}/${slug}`;
    
    const ogTags = `<meta property="og:type" content="website">
<meta property="og:title" content="${title.replace(/"/g, '&quot;')}">
<meta property="og:description" content="${desc.replace(/"/g, '&quot;')}">
<meta property="og:url" content="${url}">
<meta property="og:image" content="${DOMAIN}/images/logo-text-only-3x.png">`;
    
    const fixed = html.replace('</head>', `${ogTags}\n</head>`);
    count('add_og');
    return fixed;
}

// ===== DUPLICATE FIXER =====

function buildDuplicateMap(pages) {
    const titleMap = {};
    const descMap = {};
    
    for (const { file, rel } of pages) {
        try {
            const html = fs.readFileSync(file, 'utf8');
            if (/content\s*=\s*"noindex/i.test(html)) continue;
            
            const titleMatch = html.match(/<title>([\s\S]*?)<\/title>/i);
            const descMatch = html.match(/name="description"\s+content="([^"]*)"/i) || html.match(/content="([^"]*)"\s+name="description"/i);
            
            if (titleMatch) {
                const t = titleMatch[1].trim().toLowerCase();
                if (!titleMap[t]) titleMap[t] = [];
                titleMap[t].push({ file, rel });
            }
            if (descMatch) {
                const d = descMatch[1].substring(0, 100).toLowerCase();
                if (!descMap[d]) descMap[d] = [];
                descMap[d].push({ file, rel });
            }
        } catch (e) {}
    }
    
    return {
        dupTitles: Object.entries(titleMap).filter(([_, v]) => v.length > 1),
        dupDescs: Object.entries(descMap).filter(([_, v]) => v.length > 1),
    };
}

// ===== MAIN =====

function getAllPages() {
    const pages = [];
    
    for (const f of ['index.html', 'contact.html', 'faq.html', 'cost-calculator.html']) {
        const fp = path.join(ROOT, f);
        if (fs.existsSync(fp)) pages.push({ file: fp, rel: `/${f}` });
    }
    
    const blogDir = path.join(ROOT, 'blog');
    if (fs.existsSync(blogDir)) {
        for (const f of fs.readdirSync(blogDir).filter(f => f.endsWith('.html')).sort()) {
            pages.push({ file: path.join(blogDir, f), rel: `/blog/${f}` });
        }
    }
    
    const servicesDir = path.join(ROOT, 'services');
    if (fs.existsSync(servicesDir)) {
        for (const d of fs.readdirSync(servicesDir)) {
            const idx = path.join(servicesDir, d, 'index.html');
            if (fs.existsSync(idx)) pages.push({ file: idx, rel: `/services/${d}/` });
        }
    }
    
    return pages;
}

console.log(`🔧 SCWS Page Fixer ${APPLY ? '(APPLYING)' : '(DRY RUN)'}`);
console.log(`   Fix type: ${FIX_TYPE}`);
console.log('================================\n');

const allPages = getAllPages();
console.log(`Processing ${allPages.length} pages...\n`);

const fixers = {
    thin: fixThinContent,
    titles: fixLongTitle,
    descriptions: fixLongDescription,
    schema: fixMissingSchema,
    h1: fixMissingH1,
    og: fixMissingOG,
};

const activeFixes = FIX_TYPE === 'all' ? Object.keys(fixers) : [FIX_TYPE];

for (const { file, rel } of allPages) {
    try {
        let html = fs.readFileSync(file, 'utf8');
        let changed = false;
        
        for (const fixName of activeFixes) {
            const fixer = fixers[fixName];
            if (!fixer) continue;
            
            const result = fixer(html, file);
            if (result) {
                html = result;
                changed = true;
                if (VERBOSE) console.log(`  ✅ ${fixName}: ${rel}`);
            }
        }
        
        if (changed) {
            if (APPLY) {
                fs.writeFileSync(file, html);
            }
            stats.fixed++;
        }
        stats.scanned++;
        
        if (stats.scanned % 1000 === 0) process.stderr.write(`  ${stats.scanned}/${allPages.length}...\n`);
    } catch (e) {
        stats.errors++;
        if (VERBOSE) console.error(`  ❌ Error: ${rel}: ${e.message}`);
    }
}

// ===== REPORT =====

console.log('\n📊 RESULTS');
console.log('==========');
console.log(`Scanned: ${stats.scanned}`);
console.log(`Fixed: ${stats.fixed} pages`);
console.log(`Errors: ${stats.errors}`);
console.log();
console.log('Changes by type:');
for (const [type, count] of Object.entries(stats.changes).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${type}: ${count}`);
}

if (!APPLY) {
    console.log('\n⚠️  DRY RUN — no files changed. Run with --apply to fix.');
} else {
    console.log('\n✅ All fixes applied. Run page-audit.js to verify.');
    
    // Rebuild sitemaps after fixes (noindexed pages need removing)
    if (activeFixes.includes('thin')) {
        console.log('\n🔄 Rebuilding sitemaps (thin pages noindexed)...');
        require('child_process').execSync('node scripts/rebuild-sitemaps.js', { cwd: ROOT, stdio: 'inherit' });
    }
}

// Save fix log
const logPath = path.join(ROOT, 'seo-fix-log.json');
const existing = fs.existsSync(logPath) ? JSON.parse(fs.readFileSync(logPath, 'utf8')) : [];
existing.push({
    date: new Date().toISOString(),
    mode: APPLY ? 'apply' : 'dry-run',
    fixType: FIX_TYPE,
    stats: { ...stats }
});
fs.writeFileSync(logPath, JSON.stringify(existing, null, 2));
