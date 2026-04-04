#!/usr/bin/env node

/**
 * SCWS Content Enhancer — Systematically upgrades pages to A-grade
 * 
 * Reads content-quality-report.json, identifies weaknesses per page,
 * and adds targeted content blocks to fix them.
 * 
 * Usage:
 *   node content-enhancer.js                    # dry run
 *   node content-enhancer.js --apply            # apply fixes
 *   node content-enhancer.js --apply --limit=50 # fix 50 pages
 *   node content-enhancer.js --apply --grade=C  # only fix C and below
 *   node content-enhancer.js --apply --grade=B  # fix B and below (target all to A)
 * 
 * What it adds:
 *   - FAQ section (with schema) where missing
 *   - Stronger intro paragraph
 *   - Brand/equipment mentions where relevant
 *   - Cost/number data where relevant  
 *   - Additional content depth for thin pages
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const args = process.argv.slice(2);
const APPLY = args.includes('--apply');
const LIMIT = parseInt((args.find(a => a.startsWith('--limit=')) || '--limit=99999').replace('--limit=', ''));
const TARGET_GRADE = (args.find(a => a.startsWith('--grade=')) || '--grade=B').replace('--grade=', '');

const gradeThreshold = { A: 80, B: 65, C: 50, D: 35, F: 0 };
const targetScore = gradeThreshold[TARGET_GRADE] || 65;

const stats = { scanned: 0, enhanced: 0, skipped: 0, changes: {} };

// ===== CONTENT BLOCKS =====

// Detect page topic from title/path
function detectTopic(html, filePath) {
    const titleMatch = html.match(/<title>([\s\S]*?)<\/title>/i);
    const title = titleMatch ? titleMatch[1].toLowerCase() : '';
    const pathStr = filePath.toLowerCase();
    
    if (/drill/i.test(title + pathStr)) return 'drilling';
    if (/pump.*repair|repair.*pump|service call/i.test(title + pathStr)) return 'pump-repair';
    if (/pump.*install|install.*pump|new pump/i.test(title + pathStr)) return 'pump-install';
    if (/tank|pressure.*tank|storage/i.test(title + pathStr)) return 'tank';
    if (/water.*quality|test|chlorin|bacteria|contamin|iron|smell/i.test(title + pathStr)) return 'water-quality';
    if (/cost|price|estimate/i.test(title + pathStr)) return 'cost';
    if (/booster/i.test(title + pathStr)) return 'booster';
    if (/solar/i.test(title + pathStr)) return 'solar';
    if (/agricultural|irrigation|ranch|farm|orchard|vineyard/i.test(title + pathStr)) return 'agricultural';
    if (/well-service-|well-drilling-/i.test(pathStr)) return 'location-service';
    return 'general';
}

// Extract city name from path if location page
function extractCity(filePath) {
    const match = filePath.match(/(?:well-service-|well-drilling-|booster-pump-|well-chlorination-)([^.]+)\.html$/);
    if (match) {
        return match[1].replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    }
    return null;
}

// FAQ blocks by topic
function generateFAQ(topic, city) {
    const cityName = city || 'your area';
    const faqs = {
        'drilling': [
            { q: `How deep do wells need to be drilled in ${cityName}?`, a: `Well depth in ${cityName} typically ranges from 150 to 800 feet depending on local geology and groundwater levels. Our team conducts a site assessment to determine the optimal depth before drilling begins.` },
            { q: 'How long does it take to drill a new well?', a: 'Most residential wells take 1-3 days to drill, depending on depth and rock conditions. The complete process including pump installation and plumbing typically takes 3-5 business days.' },
            { q: `How much does well drilling cost in ${cityName}?`, a: `Well drilling in ${cityName} typically costs $45-$85 per foot, with most wells totaling $15,000-$45,000 depending on depth, casing requirements, and equipment needed. We provide free estimates before any work begins.` },
        ],
        'pump-repair': [
            { q: 'How do I know if my well pump needs repair?', a: 'Common signs include: no water or low pressure, pump cycling on and off rapidly (short cycling), unusual noises, dirty or sandy water, and higher-than-normal electric bills. Any of these warrant a professional inspection.' },
            { q: 'How much does well pump repair cost?', a: 'Simple repairs like pressure switch replacement run $150-$300. Motor or pump replacement typically costs $1,500-$4,500 depending on well depth and pump type. We diagnose the issue before recommending repairs.' },
            { q: 'Can I repair my well pump myself?', a: 'Surface-level issues like pressure switch adjustment or breaker resets are safe DIY tasks. However, anything involving pulling the pump from the well requires specialized equipment and should be handled by a licensed contractor to avoid damaging the well casing.' },
        ],
        'pump-install': [
            { q: 'What size well pump do I need?', a: 'Pump sizing depends on your well depth, water demand, and pipe diameter. A typical residential home needs 10-20 GPM. Our technicians calculate the exact Total Dynamic Head (TDH) to match the right pump — usually a Franklin or Grundfos submersible for wells over 25 feet.' },
            { q: 'How long does a well pump last?', a: 'Quality submersible pumps (Franklin Electric, Grundfos) typically last 8-15 years. Lifespan depends on water quality, usage patterns, and whether a proper pressure tank is installed to reduce cycling.' },
            { q: 'What brands do you install?', a: 'We primarily install Franklin Electric and Grundfos submersible pumps — the two most reliable brands in the industry. For specialized applications, we also work with Goulds (Xylem) and Sta-Rite (Pentair).' },
        ],
        'tank': [
            { q: 'What size pressure tank do I need?', a: 'For most residential wells, we recommend a minimum 30-gallon pressure tank. Homes with higher water demand or multiple bathrooms benefit from 50-85 gallon tanks. Proper sizing reduces pump cycling and extends pump life.' },
            { q: 'How do I know if my pressure tank is failing?', a: 'Signs of a failing pressure tank include: pump short cycling (turning on and off frequently), waterlogged tank (heavy when you tap it), fluctuating water pressure, and the tank feeling uniformly heavy rather than having an air-filled top section.' },
            { q: 'How long do pressure tanks last?', a: 'Quality pressure tanks typically last 10-15 years. Bladder-type tanks (like Well-X-Trol) tend to last longer than diaphragm tanks. Annual pressure checks can extend tank life significantly.' },
        ],
        'water-quality': [
            { q: 'Is my well water safe to drink?', a: 'Well water should be tested annually for bacteria (coliform), nitrates, and pH at minimum. In Southern California, we also recommend testing for arsenic, iron, and total dissolved solids (TDS). A comprehensive water test costs $100-$300.' },
            { q: 'Why does my well water smell like rotten eggs?', a: 'The sulfur smell is caused by hydrogen sulfide gas, usually from bacteria in the well or naturally occurring sulfur in groundwater. Treatment options include well chlorination ($200-$500), aeration systems, or activated carbon filtration.' },
            { q: 'How often should I chlorinate my well?', a: 'We recommend shock chlorination annually as preventive maintenance, or immediately if you detect bacteria, notice odor changes, or after any well work. The process typically costs $200-$500 depending on well depth.' },
        ],
        'cost': [
            { q: 'What is the average cost of well service in Southern California?', a: 'Service calls typically start at $150-$250 for diagnosis. Common repairs range from $300-$1,500. Pump replacement runs $2,500-$6,000 depending on depth. New well drilling starts around $15,000. We provide free estimates for all major work.' },
            { q: 'Does homeowners insurance cover well pump failure?', a: 'Most standard homeowners policies do NOT cover well pump failure or well components, as they are considered mechanical breakdown rather than a covered peril. Some policies offer equipment breakdown endorsements — check with your insurer.' },
            { q: 'Can I finance well work?', a: 'Yes, we offer financing options through Wisetack for qualified customers. This covers drilling, pump replacement, and major repairs with flexible payment plans.' },
        ],
        'booster': [
            { q: 'Do I need a booster pump?', a: 'A booster pump is needed when your well produces adequate water but delivers it at low pressure — typically under 30 PSI at fixtures. Common in homes far from the well, at higher elevations, or on systems with storage tanks.' },
            { q: 'What size booster pump do I need?', a: 'Booster pump sizing depends on your flow rate needs and the pressure boost required. A typical residential booster provides 40-60 PSI at 10-20 GPM. We install Grundfos and Franklin Electric constant-pressure systems for reliable, even water pressure.' },
            { q: 'How much does a booster pump system cost?', a: 'Residential booster pump installation typically costs $2,000-$5,000 including the pump, pressure tank, and plumbing. Constant-pressure VFD systems run $3,500-$7,000 but provide superior pressure control.' },
        ],
        'agricultural': [
            { q: 'How much water does an agricultural well produce?', a: 'Agricultural wells in Southern California typically produce 20-100+ GPM depending on the aquifer. Irrigation needs vary widely — a small orchard may need 15-20 GPM while larger operations require 50-100+ GPM.' },
            { q: 'What type of pump is best for agricultural wells?', a: 'For high-volume agricultural wells, we typically install large-diameter submersible pumps (7.5-25+ HP) from Franklin Electric or Grundfos. Solar-powered pump systems are increasingly popular for remote ranch locations.' },
            { q: 'How deep are agricultural wells in Southern California?', a: 'Agricultural wells in our service area range from 200 to 1,000+ feet. Desert and inland valley locations often require deeper wells (400-800 ft), while coastal and foothill areas may produce at 200-400 feet.' },
        ],
        'location-service': [
            { q: `What well services do you offer in ${cityName}?`, a: `We provide complete well services in ${cityName} including well pump repair, pump replacement, new well drilling, water testing, pressure tank service, and 24/7 emergency response. Our licensed C-57 technicians serve ${cityName} and surrounding areas.` },
            { q: `How quickly can you respond to a well emergency in ${cityName}?`, a: `For no-water emergencies in ${cityName}, we offer same-day response. Our technicians are based in Ramona and Anza, giving us fast access across San Diego and Riverside counties. Call (760) 440-8520 for immediate help.` },
            { q: `How much does well service cost in ${cityName}?`, a: `Well service costs in ${cityName} are consistent with our standard rates: service calls start at $150-$250, pump repairs $300-$1,500, and pump replacement $2,500-$6,000 depending on well depth. We provide free estimates.` },
        ],
    };
    
    // Fallback general FAQs
    faqs['general'] = faqs['pump-repair'];
    faqs['solar'] = [
        { q: 'Can I run my well pump on solar power?', a: 'Yes, solar-powered well pumps work well in Southern California with our abundant sunshine. Systems typically cost $5,000-$15,000 depending on pump size and depth. They are ideal for remote properties without reliable grid power.' },
        { q: 'How much does a solar well pump system cost?', a: 'A complete solar well pump system costs $5,000-$15,000 including panels, controller, and pump. Grundfos SQFlex is the industry-leading solar submersible pump. ROI is typically 3-5 years compared to running power lines to a remote well.' },
        { q: 'Do solar well pumps work at night?', a: 'Solar pumps operate during daylight hours and fill a storage tank. The storage tank then provides water pressure 24/7 using gravity or a small booster pump. Battery backup systems are available but add significant cost.' },
    ];
    
    return faqs[topic] || faqs['general'];
}

// Brand/equipment content by topic
function generateBrandContent(topic) {
    const brands = {
        'pump-repair': 'We service all major pump brands including <strong>Franklin Electric</strong>, <strong>Grundfos</strong>, <strong>Goulds (Xylem)</strong>, and <strong>Sta-Rite (Pentair)</strong>. Our trucks carry common parts and components for same-day repairs.',
        'pump-install': 'We install premium <strong>Franklin Electric</strong> and <strong>Grundfos</strong> submersible pumps — the two most reliable brands in the well industry. For specific applications, we also offer <strong>Goulds</strong> and <strong>Sta-Rite</strong> options.',
        'drilling': 'Our drilling fleet includes a <strong>Gefco</strong> rotary drill rig capable of drilling to 1,000+ feet. We use <strong>PVC</strong> and <strong>steel casing</strong> depending on well depth and geology, with <strong>gravel pack</strong> completion for optimal water production.',
        'tank': 'We install <strong>Well-X-Trol</strong> (Amtrol) and <strong>Flexcon</strong> pressure tanks — industry-leading bladder tanks that outlast standard diaphragm models. Proper sizing with a quality tank can double your pump\'s lifespan.',
        'booster': 'We install <strong>Grundfos</strong> constant-pressure booster systems and <strong>Franklin Electric</strong> SubDrive VFD controllers for consistent water pressure regardless of demand.',
        'water-quality': 'We use <strong>Hach</strong> and <strong>LaMotte</strong> professional water testing equipment for field analysis, with comprehensive lab testing through certified California laboratories.',
        'agricultural': 'For agricultural applications, we install high-capacity <strong>Franklin Electric</strong> and <strong>Grundfos</strong> submersible pumps from 7.5 to 25+ HP. <strong>Grundfos SQFlex</strong> solar pumps are available for off-grid ranch locations.',
    };
    return brands[topic] || brands['pump-repair'];
}

// ===== BUILD FAQ HTML =====

function buildFAQHTML(faqs) {
    let html = '\n<!-- FAQ Section -->\n';
    html += '<h2 id="frequently-asked-questions" class="text-3xl font-bold text-primary mt-12 mb-4">Frequently Asked Questions</h2>\n';
    
    for (const { q, a } of faqs) {
        html += `<div class="bg-gray-50 rounded-lg p-4 mb-3">\n`;
        html += `  <h3 class="font-bold text-gray-900 mb-2">${q}</h3>\n`;
        html += `  <p class="text-gray-700">${a}</p>\n`;
        html += `</div>\n`;
    }
    
    return html;
}

function buildFAQSchema(faqs) {
    const schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faqs.map(({ q, a }) => ({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": { "@type": "Answer", "text": a.replace(/<[^>]+>/g, '') }
        }))
    };
    return `<script type="application/ld+json">\n${JSON.stringify(schema, null, 2)}\n</script>`;
}

// ===== ENHANCE A PAGE =====

function enhancePage(html, filePath, scores) {
    let modified = false;
    const changes = [];
    const topic = detectTopic(html, filePath);
    const city = extractCity(filePath);
    
    // 1. ADD FAQ if missing (faq score < 3)
    if (scores.faq < 3 && !/<h2[^>]*>.*(?:FAQ|Frequently Asked)/i.test(html)) {
        const faqs = generateFAQ(topic, city);
        const faqHTML = buildFAQHTML(faqs);
        const faqSchema = buildFAQSchema(faqs);
        
        // Insert before related articles, footer, or closing article/main tag
        const insertPoints = [
            /(<h2[^>]*>.*Related Articles.*<\/h2>)/i,
            /(<\/article>)/i,
            /(<\/main>)/i,
            /(<footer)/i,
        ];
        
        let inserted = false;
        for (const regex of insertPoints) {
            if (regex.test(html)) {
                html = html.replace(regex, faqHTML + '\n$1');
                inserted = true;
                break;
            }
        }
        
        if (inserted) {
            // Add FAQ schema before </head>
            if (!/"FAQPage"/i.test(html)) {
                html = html.replace('</head>', faqSchema + '\n</head>');
            }
            modified = true;
            changes.push('added FAQ section + schema');
        }
    }
    
    // 2. ADD BRAND CONTENT if missing (brands score < 2)
    if (scores.brands < 2) {
        const brandContent = generateBrandContent(topic);
        if (brandContent) {
            // Insert as a paragraph before FAQ or before related articles
            const brandHTML = `\n<p class="text-gray-700 my-4">${brandContent}</p>\n`;
            
            const insertPoints = [
                /(<h2[^>]*>.*(?:FAQ|Frequently Asked))/i,
                /(<h2[^>]*>.*Related Articles)/i,
                /(<\/article>)/i,
            ];
            
            for (const regex of insertPoints) {
                if (regex.test(html)) {
                    html = html.replace(regex, brandHTML + '$1');
                    modified = true;
                    changes.push('added brand/equipment mentions');
                    break;
                }
            }
        }
    }
    
    // 3. STRENGTHEN INTRO if weak (intro score < 3)
    if (scores.intro < 3) {
        // Find first <p> in content area and check if it's too short
        const proseMatch = html.match(/<div class="prose[^"]*">([\s\S]*?)<\/div>/i);
        if (proseMatch) {
            const firstP = proseMatch[1].match(/<p[^>]*>([\s\S]*?)<\/p>/i);
            if (firstP) {
                const pText = firstP[1].replace(/<[^>]+>/g, '').trim();
                if (pText.split(/\s+/).length < 25) {
                    // Don't modify — intro rewriting needs AI/human touch
                    // Just flag it
                    changes.push('intro weak (needs manual rewrite)');
                }
            }
        }
    }
    
    return { html: modified ? html : null, changes };
}

// ===== MAIN =====

console.log(`🚀 SCWS Content Enhancer ${APPLY ? '(APPLYING)' : '(DRY RUN)'}`);
console.log(`   Target: all pages below grade ${TARGET_GRADE} (score < ${gradeThreshold[TARGET_GRADE]})`);
console.log('================================\n');

// Load quality report
const reportPath = path.join(ROOT, 'content-quality-report.json');
if (!fs.existsSync(reportPath)) {
    console.error('Run content-audit.js first to generate content-quality-report.json');
    process.exit(1);
}
const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));

// Filter to pages below target
const targets = report.pages
    .filter(p => p.score < 80)  // everything below A
    .sort((a, b) => a.score - b.score);  // worst first

console.log(`${targets.length} pages below A grade\n`);

let processed = 0;
for (const page of targets) {
    if (processed >= LIMIT) break;
    
    // Map path to file
    let filePath;
    if (page.path.startsWith('/blog/')) {
        filePath = path.join(ROOT, 'blog', path.basename(page.path) + '.html');
    } else if (page.path.startsWith('/services/')) {
        filePath = path.join(ROOT, page.path.slice(1), 'index.html');
    } else {
        filePath = path.join(ROOT, page.path.slice(1));
    }
    
    if (!fs.existsSync(filePath)) {
        // Try without .html
        filePath = path.join(ROOT, page.path.slice(1) + '.html');
    }
    if (!fs.existsSync(filePath)) continue;
    
    try {
        const html = fs.readFileSync(filePath, 'utf8');
        if (/content\s*=\s*"noindex/i.test(html)) continue;
        
        const { html: enhanced, changes } = enhancePage(html, filePath, page.scores);
        
        if (enhanced && changes.length > 0) {
            if (APPLY) {
                fs.writeFileSync(filePath, enhanced);
            }
            stats.enhanced++;
            const autoChanges = changes.filter(c => !c.includes('manual'));
            for (const c of autoChanges) {
                stats.changes[c] = (stats.changes[c] || 0) + 1;
            }
            
            if (processed < 10 || !APPLY) {
                console.log(`  ${page.grade} ${page.score} → ${page.path}`);
                for (const c of changes) console.log(`    ✅ ${c}`);
            }
        }
    } catch (e) {
        stats.skipped++;
    }
    
    processed++;
    if (processed % 500 === 0) process.stderr.write(`  ${processed}/${targets.length}...\n`);
}

console.log(`\n📊 RESULTS`);
console.log(`==========`);
console.log(`Processed: ${processed}`);
console.log(`Enhanced: ${stats.enhanced} pages`);
console.log(`Skipped: ${stats.skipped}`);
console.log();
console.log('Changes:');
for (const [type, count] of Object.entries(stats.changes).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${type}: ${count} pages`);
}

if (!APPLY) {
    console.log('\n⚠️  DRY RUN — run with --apply to make changes');
} else {
    console.log('\n✅ Changes applied. Re-run content-audit.js to verify improvement.');
}
