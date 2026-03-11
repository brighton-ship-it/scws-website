#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const stats = JSON.parse(fs.readFileSync(path.join(__dirname, 'city-well-stats.json'), 'utf8'));

function slug(city) {
  return city.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
}

function geologySummary(city, data) {
  const avg = data.avgDepth;
  const county = data.county;
  if (avg > 400) {
    return `${city} sits in an area with deep bedrock, typically requiring wells to penetrate granite or metamorphic formations. The average depth of ${avg} feet reflects the need to drill through hard rock layers to reach productive aquifers. These deeper wells often require air rotary or DTH (down-the-hole) hammer drilling methods. Well depths vary significantly\u2014from ${data.minDepth} to ${data.maxDepth} feet\u2014reflecting diverse geological conditions across the area.`;
  } else if (avg > 200) {
    return `Wells in ${city} reach moderate depths, averaging ${avg} feet. The area features a mix of alluvial deposits and bedrock formations, with depth varying based on specific location and proximity to fracture zones. ${county} County geology in this region typically involves decomposed granite overlaying harder rock, with groundwater found in fractures and weathered zones.`;
  } else {
    return `${city} benefits from relatively shallow groundwater, with wells averaging just ${avg} feet deep. The area's alluvial deposits and sedimentary formations allow easier access to productive aquifers. Shallower wells in this region typically use rotary drilling methods and can often be completed more quickly and at lower cost than deeper bedrock wells.`;
  }
}

function costEstimate(avgDepth) {
  const low = Math.round(avgDepth * 45);
  const high = Math.round(avgDepth * 75);
  return { low, high };
}

function decadeChart(wellsByDecade) {
  if (!wellsByDecade || Object.keys(wellsByDecade).length === 0) return '';
  const sorted = Object.entries(wellsByDecade).sort((a, b) => a[0].localeCompare(b[0]));
  const maxCount = Math.max(...sorted.map(([, c]) => c));
  const rows = sorted.map(([decade, count]) => {
    const pct = Math.round((count / maxCount) * 100);
    return `                        <div style="display:flex;align-items:center;gap:12px;margin:6px 0">
                            <span style="min-width:60px;font-weight:600;color:#334155;font-size:0.9em">${decade}</span>
                            <div style="flex:1;display:flex;align-items:center;gap:8px">
                                <div style="height:22px;width:${pct}%;background:#4e9271;border-radius:4px;min-width:4px"></div>
                                <span style="color:#64748b;font-size:0.85em">${count}</span>
                            </div>
                        </div>`;
  }).join('\n');
  return `
                <h3 class="font-bold text-primary text-lg mt-6 mb-3">Wells Drilled by Decade</h3>
                <div class="bg-gray-50 rounded-lg p-4">
${rows}
                </div>`;
}

function useBreakdown(wellsByUse) {
  if (!wellsByUse || Object.keys(wellsByUse).length === 0) return '';
  const sorted = Object.entries(wellsByUse).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const total = sorted.reduce((s, [, c]) => s + c, 0);
  const rows = sorted.map(([use, count]) => {
    const pct = Math.round((count / total) * 100);
    return `                        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f0f0f0">
                            <span style="color:#334155;font-size:0.9em">${use}</span>
                            <span style="font-weight:600;color:#0c4a6e;font-size:0.9em">${count} (${pct}%)</span>
                        </div>`;
  }).join('\n');
  return `
                <h3 class="font-bold text-primary text-lg mt-6 mb-3">Wells by Use Type</h3>
                <div class="bg-gray-50 rounded-lg p-4">
${rows}
                </div>`;
}

function depthChart(data) {
  const avgPct = ((data.avgDepth - data.minDepth) / (data.maxDepth - data.minDepth) * 100).toFixed(1);
  return `
                <div class="bg-gray-50 rounded-lg p-5 my-4">
                    <div style="position:relative;height:55px;margin-bottom:8px">
                        <span style="position:absolute;left:0;font-weight:700;color:#4e9271;font-size:0.9em">${data.minDepth}ft<br><small style="font-weight:400;color:#64748b">Shallowest</small></span>
                        <span style="position:absolute;left:${avgPct}%;transform:translateX(-50%);text-align:center;font-weight:700;color:#0c4a6e;font-size:0.9em">${data.avgDepth}ft<br><small style="font-weight:400;color:#64748b">Average</small></span>
                        <span style="position:absolute;right:0;font-weight:700;color:#dc2626;font-size:0.9em">${data.maxDepth}ft<br><small style="font-weight:400;color:#64748b">Deepest</small></span>
                    </div>
                    <div style="position:relative;height:36px;background:#e2e8f0;border-radius:18px;overflow:hidden">
                        <div style="height:100%;width:100%;background:linear-gradient(90deg,#4e9271 0%,#3d7a5c 50%,#2d5a43 100%)"></div>
                        <div style="position:absolute;top:0;left:${avgPct}%;width:3px;height:100%;background:#fff;transform:translateX(-1.5px)"></div>
                    </div>
                </div>`;
}

function nearbyCities(city, county, allStats) {
  const sameCo = Object.entries(allStats)
    .filter(([c, d]) => d.county === county && c !== city && d.count >= 10)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 6);
  if (sameCo.length === 0) return '';
  const links = sameCo.map(([c, d]) =>
    `<li><a href="/blog/average-well-depth-${slug(c)}-ca.html" class="text-accent hover:text-green-700 font-medium hover:underline">${c} \u2014 ${d.avgDepth}ft avg (${d.count} wells)</a></li>`
  ).join('\n                        ');
  return `
            <div class="bg-gray-50 rounded-xl p-6 my-8 border border-gray-200">
                <h3 class="font-bold text-primary text-lg mb-3">\uD83D\uDCCD Nearby Cities \u2014 Well Depth Data</h3>
                <ul class="space-y-2">
                    ${links}
                </ul>
            </div>`;
}

function generatePage(city, data, allStats) {
  const s = slug(city);
  const cost = costEstimate(data.avgDepth);
  const yieldStr = data.avgYield ? data.avgYield.toFixed(1) : 'N/A';

  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>Average Well Depth in ${city}, CA | SCWS</title>
    <meta name="description" content="Average well depth in ${city}, California is ${data.avgDepth} feet based on ${data.count} wells on record. ${data.minDepth}-${data.maxDepth} ft range. ${data.county} County well data.">
    <link rel="canonical" href="https://scwellservice.com/blog/average-well-depth-${s}-ca.html">
    <link rel="stylesheet" href="../css/styles.css">

    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "How deep are wells in ${city}, CA?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "The average well depth in ${city}, California is ${data.avgDepth} feet, based on ${data.count} wells on record. Well depths range from ${data.minDepth} to ${data.maxDepth} feet depending on geology and location."
                }
            },
            {
                "@type": "Question",
                "name": "How much does it cost to drill a well in ${city}, CA?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Well drilling costs in ${city} typically range from $${cost.low.toLocaleString()}-$${cost.high.toLocaleString()} based on the ${data.avgDepth}-foot average depth. Call Southern California Well Service at (760) 440-8520 for a free estimate."
                }
            }
        ]
    }
    </script>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://scwellservice.com/"},
            {"@type": "ListItem", "position": 2, "name": "Resources", "item": "https://scwellservice.com/blog/"},
            {"@type": "ListItem", "position": 3, "name": "Well Depth in ${city}", "item": "https://scwellservice.com/blog/average-well-depth-${s}-ca.html"}
        ]
    }
    </script>

    <script src="/js/ga4-filter.js"></script>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-5LL1YRWT5T"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-5LL1YRWT5T');</script>
    <meta property="og:title" content="Average Well Depth in ${city}, CA">
    <meta property="og:description" content="${data.avgDepth} feet average depth, ${data.count} wells on record in ${data.county} County.">
    <meta property="og:type" content="article">
    <meta property="og:image" content="https://scwellservice.com/images/og-default.jpg">
    <meta name="twitter:card" content="summary_large_image">
</head>
<body class="pb-20 lg:pb-0 bg-white">
    <header class="bg-primary text-white sticky top-0 z-50 shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-2">
                <a href="/" class="shrink-0">
                    <img loading="lazy" src="/images/logo-text-only-3x.png" alt="Southern California Well Service" class="h-10 lg:h-12 w-auto">
                </a>
                <nav class="hidden lg:flex space-x-4 items-center">
                    <a href="/services/" class="text-white hover:text-accent transition whitespace-nowrap">Services</a>
                    <a href="/blog/" class="text-white hover:text-accent transition whitespace-nowrap">Resources</a>
                    <a href="/faq.html" class="text-white hover:text-accent transition whitespace-nowrap">FAQ</a>
                    <a href="/contact/" class="text-white hover:text-accent transition whitespace-nowrap">Contact</a>
                    <a href="/cost-calculator.html" class="text-white font-semibold hover:text-accent transition whitespace-nowrap">Free Estimate</a>
                    <a href="/pages/about.html" class="text-white hover:text-accent transition whitespace-nowrap">About</a>
                </nav>
                <div class="flex items-center gap-3">
                    <button id="mobile-menu-btn" class="lg:hidden p-2 hover:bg-white/10 rounded-lg transition" aria-label="Toggle menu">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                        </svg>
                    </button>
                    <a href="tel:7604408520" class="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 lg:px-6 rounded-lg transition whitespace-nowrap text-sm lg:text-base">
                        (760) 440-8520
                    </a>
                </div>
            </div>
        </div>
        <div id="mobile-menu" class="hidden lg:hidden bg-primary/95 border-t border-white/10">
            <nav class="max-w-7xl mx-auto px-4 py-4 flex flex-col space-y-3">
                <a href="/services/" class="hover:text-accent transition py-2">Services</a>
                <a href="/blog/" class="hover:text-accent transition py-2">Resources</a>
                <a href="/faq.html" class="hover:text-accent transition py-2">FAQ</a>
                <a href="/contact/" class="hover:text-accent transition py-2">Contact</a>
                <a href="/cost-calculator.html" class="text-white font-semibold hover:text-accent transition py-2">Free Estimate</a>
                <a href="/pages/about.html" class="hover:text-accent transition py-2">About</a>
            </nav>
        </div>
    </header>
    <script>
        document.getElementById('mobile-menu-btn').addEventListener('click', function() {
            document.getElementById('mobile-menu').classList.toggle('hidden');
        });
    </script>

    <main>
        <section class="bg-gray-100 border-b border-gray-200 py-10 px-4">
            <div class="max-w-4xl mx-auto">
                <nav class="text-sm text-gray-500 mb-3" aria-label="Breadcrumb">
                    <a href="/" class="hover:text-primary">Home</a> &rsaquo;
                    <a href="/blog/" class="hover:text-primary">Resources</a> &rsaquo;
                    <span class="text-gray-700">Well Depth in ${city}</span>
                </nav>
                <h1 class="text-3xl sm:text-4xl font-bold text-primary mb-2">Average Well Depth in ${city}, California</h1>
                <p class="text-gray-600 text-lg">Based on ${data.count} wells on record | ${data.county} County, CA</p>
            </div>
        </section>

        <article class="max-w-4xl mx-auto px-4 sm:px-6 py-8">

            <div class="bg-gray-50 rounded-xl p-6 my-8 border border-gray-200">
                <h3 class="font-bold text-primary text-lg mb-4">Well Statistics for ${city}</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px">
                    <div style="text-align:center">
                        <div class="text-primary" style="font-size:2em;font-weight:700">${data.avgDepth}ft</div>
                        <div style="color:#64748b;font-size:0.85em">Average Depth</div>
                    </div>
                    <div style="text-align:center">
                        <div class="text-primary" style="font-size:2em;font-weight:700">${data.count.toLocaleString()}</div>
                        <div style="color:#64748b;font-size:0.85em">Wells on Record</div>
                    </div>
                    <div style="text-align:center">
                        <div class="text-primary" style="font-size:2em;font-weight:700">${data.minDepth}-${data.maxDepth}ft</div>
                        <div style="color:#64748b;font-size:0.85em">Depth Range</div>
                    </div>
                    <div style="text-align:center">
                        <div class="text-primary" style="font-size:2em;font-weight:700">${yieldStr}</div>
                        <div style="color:#64748b;font-size:0.85em">Avg Yield (GPM)</div>
                    </div>
                </div>
            </div>

            <div class="bg-primary text-white rounded-xl p-6 my-8">
                <h3 class="font-bold text-lg mb-2">Need a Well Drilled in ${city}?</h3>
                <p style="color:#cbd5e1;font-size:0.9em;margin-bottom:16px">Expert well drilling, pump installation, and repair service in ${data.county} County.</p>
                <a href="tel:7604408520" style="display:block;background:#dc2626;color:#fff;font-weight:700;padding:12px 16px;border-radius:8px;text-align:center;text-decoration:none;margin-bottom:8px">\uD83D\uDCDE (760) 440-8520</a>
                <a href="/contact/" style="display:block;background:#4e9271;color:#fff;font-weight:700;padding:12px 16px;border-radius:8px;text-align:center;text-decoration:none;font-size:0.9em">Get Free Estimate \u2192</a>
            </div>

            <h2>Well Depth Distribution in ${city}</h2>
            <p>Based on ${data.count.toLocaleString()} wells drilled in ${city}, California, the average depth is <strong>${data.avgDepth} feet</strong>. The median depth is ${data.medianDepth} feet, which represents the typical well depth in the area.</p>
            ${depthChart(data)}
            <ul class="my-4" style="list-style:disc;padding-left:20px">
                <li><strong>Shallowest well:</strong> ${data.minDepth} feet</li>
                <li><strong>Deepest well:</strong> ${data.maxDepth} feet</li>
                <li><strong>Average depth:</strong> ${data.avgDepth} feet</li>
                <li><strong>Median depth:</strong> ${data.medianDepth} feet</li>
            </ul>

            <h2>Geology and Groundwater in ${city}</h2>
            <p>${geologySummary(city, data)}</p>
            <p style="margin-top:12px">The average static water level (depth to water when the pump is off) in ${city} wells is approximately ${data.avgStaticLevel} feet below ground surface.</p>

            <h2>Drilling Trends &amp; Well Use</h2>
            ${decadeChart(data.wellsByDecade)}
            ${useBreakdown(data.wellsByUse)}

            <h2>Estimated Drilling Cost in ${city}</h2>
            <p>Based on the average well depth of ${data.avgDepth} feet, drilling a new well in ${city} typically costs between <strong>$${cost.low.toLocaleString()} and $${cost.high.toLocaleString()}</strong>. This includes drilling, casing, pump installation, and basic connections. Actual costs vary based on geology, access, and permit requirements.</p>
            <p style="margin-top:12px"><a href="/app/well-depth.html" class="text-accent hover:text-green-700 font-medium">\uD83D\uDD0D Try our free Well Depth Lookup Tool</a> to check well records near your specific address.</p>

            ${nearbyCities(city, data.county, allStats)}

            <div class="bg-gray-50 rounded-xl p-6 my-8 border border-gray-200">
                <h3 class="font-bold text-primary text-lg mb-3">\uD83D\uDCDA Related Resources</h3>
                <ul class="space-y-2">
                    <li><a href="/blog/well-depth-explained.html" class="text-accent hover:text-green-700 font-medium hover:underline">Well Depth Explained \u2192</a></li>
                    <li><a href="/blog/drilling-cost-per-foot-san-diego.html" class="text-accent hover:text-green-700 font-medium hover:underline">Drilling Cost Per Foot \u2192</a></li>
                    <li><a href="/blog/factors-affecting-well-depth.html" class="text-accent hover:text-green-700 font-medium hover:underline">Factors Affecting Well Depth \u2192</a></li>
                    <li><a href="/blog/well-yield-test-explained.html" class="text-accent hover:text-green-700 font-medium hover:underline">Well Yield Testing \u2192</a></li>
                </ul>
            </div>

            <div class="bg-primary text-white rounded-xl p-6 my-8 text-center">
                <h3 class="font-bold text-xl mb-2">Get Expert Advice for Your ${city} Property</h3>
                <p class="text-white/80 mb-4">Southern California Well Service has drilled hundreds of wells across ${data.county} County. We know the local geology and can give you an accurate depth and cost estimate.</p>
                <a href="tel:7604408520" style="display:inline-block;background:#dc2626;color:#fff;font-weight:700;padding:14px 32px;border-radius:8px;text-decoration:none;font-size:1.1em">Call (760) 440-8520</a>
                <p class="text-white/60 text-sm mt-3">Licensed C-57 Contractor | San Diego, Riverside &amp; San Bernardino Counties</p>
            </div>
        </article>
    </main>

    <footer class="bg-gray-900 text-gray-400 text-center py-8 text-sm">
        <p>&copy; 2026 Southern California Well Service. Licensed C-57 Contractor.</p>
        <p class="mt-1">1077 Main St, Ramona, CA 92065 | <a href="tel:7604408520" class="text-white hover:text-accent">(760) 440-8520</a></p>
    </footer>

<style>main article h2{font-size:1.5em;font-weight:700;color:#0c4a6e;margin:2em 0 0.75em;padding-bottom:0.3em;border-bottom:2px solid #e5e7eb}main article p{line-height:1.7;color:#334155;margin-bottom:1em}main article ul{color:#334155;line-height:1.7}</style>
<style>#sticky-cta{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:2px solid #e5e7eb;padding:12px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px;z-index:50;box-shadow:0 -4px 12px rgba(0,0,0,0.1)}#sticky-cta a{flex:1;font-weight:700;padding:12px 16px;border-radius:8px;text-align:center;color:#fff;font-size:14px;text-decoration:none}#sticky-cta .cta-call{background:#dc2626}#sticky-cta .cta-call:hover{background:#b91c1c}#sticky-cta .cta-text{background:#2563eb}#sticky-cta .cta-text:hover{background:#1d4ed8}#sticky-cta .cta-est{background:#4e9271}#sticky-cta .cta-est:hover{background:#3d7a5c}@media(min-width:1024px){#sticky-cta{display:none}}</style>
<div id="sticky-cta">
    <a href="tel:7604408520" class="cta-call">\uD83D\uDCDE Call Now</a>
    <a href="sms:6192590410" class="cta-text">\uD83D\uDCAC Text Us</a>
    <a href="/contact/" class="cta-est">Free Estimate</a>
</div>
</body>
</html>`;
}

// Generate all pages
let count = 0;
const blogDir = path.join(__dirname, '..', 'blog');
for (const [city, data] of Object.entries(stats)) {
  const s = slug(city);
  const html = generatePage(city, data, stats);
  fs.writeFileSync(path.join(blogDir, `average-well-depth-${s}-ca.html`), html);
  count++;
}
console.log(`Regenerated ${count} city pages`);
