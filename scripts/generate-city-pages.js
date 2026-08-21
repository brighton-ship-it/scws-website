#!/usr/bin/env node

/**
 * Generate average well depth city pages for SCWS
 * Updated to match correct site template structure
 */

const fs = require('fs');
const path = require('path');

// Load city statistics
const cityStatsPath = path.join(__dirname, 'city-well-stats.json');
const cityStats = JSON.parse(fs.readFileSync(cityStatsPath, 'utf8'));

const cities = Object.keys(cityStats).sort();
console.log(`Generating pages for ${cities.length} cities...`);

// Helper: slugify city name
function slugify(str) {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// Helper: get geology context based on depth patterns
function getGeologyContext(avgDepth, medianDepth, minDepth, maxDepth, city, county) {
  let context = '';
  
  if (avgDepth > 400) {
    context = `${city} sits in an area with deep bedrock, typically requiring wells to penetrate granite or metamorphic formations. The average depth of ${avgDepth} feet reflects the need to drill through hard rock layers to reach productive aquifers. These deeper wells often require air rotary or DTH (down-the-hole) hammer drilling methods and tend to have lower yields but more stable water quality.`;
  } else if (avgDepth > 250) {
    context = `Wells in ${city} typically reach moderate depths to access fractured rock aquifers beneath alluvial deposits. At an average of ${avgDepth} feet, most wells here penetrate through soil and weathered rock before encountering water-bearing fractures in the underlying bedrock. This depth range is common in ${county} County's foothill and valley transition zones.`;
  } else if (avgDepth > 150) {
    context = `${city} wells tap into intermediate-depth aquifers, averaging ${avgDepth} feet. This depth is typical for areas with alluvial valleys or sedimentary basins where groundwater accumulates in sand and gravel layers. Wells at this depth generally provide reliable yields and benefit from some natural filtration through overlying soil layers.`;
  } else {
    context = `The relatively shallow average well depth of ${avgDepth} feet in ${city} indicates the presence of productive alluvial aquifers close to the surface. These shallow groundwater systems are typically recharged by local precipitation and surface water infiltration, though they may be more susceptible to seasonal fluctuations and surface contamination.`;
  }
  
  // Add range context if significant variation
  if (maxDepth && minDepth && (maxDepth - minDepth) > 400) {
    context += ` Well depths in the area vary significantly—from ${minDepth} to ${maxDepth} feet—reflecting diverse geological conditions across the region. Shallower wells often indicate alluvial areas, while deeper wells suggest locations over bedrock or in zones with lower water tables.`;
  }
  
  return context;
}

// Helper: generate decade chart HTML (using Tailwind + inline styles with muted green)
function generateDecadeChart(wellsByDecade) {
  const decades = Object.keys(wellsByDecade).sort();
  if (decades.length === 0) return '<p>Decade data not available for this area.</p>';
  
  const maxCount = Math.max(...Object.values(wellsByDecade));
  
  let html = '<div class="my-6">\n';
  decades.forEach(decade => {
    const count = wellsByDecade[decade];
    const percentage = (count / maxCount) * 100;
    html += `  <div class="flex items-center my-2 gap-3">
    <span class="min-w-[80px] font-semibold text-gray-700">${decade}</span>
    <div class="flex-1 flex items-center gap-2">
      <div style="width: ${percentage}%; height: 24px; background: #4e9271; border-radius: 4px;"></div>
      <span class="text-gray-500 text-sm whitespace-nowrap">${count} wells</span>
    </div>
  </div>\n`;
  });
  html += '</div>';
  
  return html;
}

// Helper: generate use type breakdown (using Tailwind)
function generateUseBreakdown(wellsByUse) {
  const uses = Object.entries(wellsByUse)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10); // Top 10
  
  if (uses.length === 0) return '<p>Use type data not available.</p>';
  
  let html = '<div class="my-6">\n';
  uses.forEach(([use, count]) => {
    html += `  <div class="flex items-center my-2 gap-3">
    <span class="font-semibold text-gray-700">${use}</span>
    <span class="ml-auto font-semibold text-gray-500">${count} wells</span>
  </div>\n`;
  });
  html += '</div>';
  
  return html;
}

// Helper: generate depth distribution chart (inline styles with muted green)
function generateDepthChart(minDepth, avgDepth, maxDepth) {
  if (!minDepth || !avgDepth || !maxDepth) {
    return '<p>Depth distribution data not available.</p>';
  }
  
  const range = maxDepth - minDepth;
  const avgPosition = ((avgDepth - minDepth) / range) * 100;
  
  return `<div style="margin: 24px 0; padding: 20px; background: #f8fafc; border-radius: 8px;">
  <div style="position: relative; height: 60px; margin-bottom: 12px;">
    <span style="position: absolute; left: 0; font-weight: bold; color: #4e9271;">${minDepth}ft<br><small>Shallowest</small></span>
    <span style="position: absolute; left: ${avgPosition}%; transform: translateX(-50%); font-weight: bold; color: #4e9271; text-align: center;">${avgDepth}ft<br><small>Average</small></span>
    <span style="position: absolute; right: 0; font-weight: bold; color: #4e9271;">${maxDepth}ft<br><small>Deepest</small></span>
  </div>
  <div style="position: relative; height: 40px; background: #e2e8f0; border-radius: 20px; overflow: hidden;">
    <div style="height: 100%; background: linear-gradient(90deg, #4e9271 0%, #5ca880 50%, #6ab88f 100%);"></div>
    <div style="position: absolute; top: 0; left: ${avgPosition}%; width: 4px; height: 100%; background: #dc2626; transform: translateX(-2px);"></div>
  </div>
</div>`;
}

// Helper: get nearby cities (same county, similar well count)
function getNearbyCities(city, county, count) {
  const nearby = Object.entries(cityStats)
    .filter(([c, stats]) => c !== city && stats.county === county)
    .map(([c, stats]) => ({ name: c, count: stats.count, diff: Math.abs(stats.count - count) }))
    .sort((a, b) => a.diff - b.diff)
    .slice(0, 5);
  
  return nearby.map(n => n.name);
}

// Generate page for each city
let pagesGenerated = 0;
const generatedPages = [];

cities.forEach(city => {
  const stats = cityStats[city];
  const slug = slugify(city);
  const filename = `average-well-depth-${slug}-ca.html`;
  const filepath = path.join(__dirname, '../blog', filename);
  
  const {
    county,
    count,
    avgDepth,
    minDepth,
    maxDepth,
    medianDepth,
    avgYield,
    medianYield,
    avgStaticLevel,
    wellsByDecade,
    wellsByUse
  } = stats;
  
  // Skip if missing critical data
  if (!avgDepth || count < 5) {
    console.log(`Skipping ${city} - insufficient data`);
    return;
  }
  
  const depthRange = maxDepth && minDepth ? `${minDepth}-${maxDepth}` : 'varies';
  const yieldText = avgYield ? `average yield of ${avgYield} GPM` : 'yield data varies';
  const geologyText = getGeologyContext(avgDepth, medianDepth, minDepth, maxDepth, city, county);
  const nearbyCities = getNearbyCities(city, county, count);
  
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>Average Well Depth in ${city}, CA | SCWS</title>
    <meta name="description" content="Average well depth in ${city}, California is ${avgDepth} feet based on ${count} wells on record. ${depthRange} ft typical range. ${county} County well drilling data.">
    <link rel="canonical" href="https://scwellservice.com/blog/${filename}">
    <link rel="stylesheet" href="../css/styles.css">
    
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Average Well Depth in ${city}, California",
        "description": "Average well depth data for ${city}, CA based on ${count} wells on record in ${county} County.",
        "author": {"@type": "Organization", "name": "Southern California Well Service"},
        "publisher": {"@type": "Organization", "name": "Southern California Well Service"},
        "datePublished": "2026-03-11",
        "dateModified": "2026-03-11"
    }
    </script>
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
                    "text": "The average well depth in ${city}, California is ${avgDepth} feet, based on ${count} wells on record. Well depths in the area range from ${depthRange} feet depending on geology and location. ${county} County wells typically require ${avgDepth > 300 ? 'deeper drilling into bedrock' : 'moderate drilling into alluvial aquifers'}."
                }
            },
            {
                "@type": "Question",
                "name": "How much does it cost to drill a well in ${city}, CA?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Well drilling costs in ${city} typically range from $${Math.round(avgDepth * 45)}-$${Math.round(avgDepth * 75)} for a complete installation, based on the ${avgDepth}-foot average depth. Cost factors include depth, geology, casing requirements, and pump size. Call Southern California Well Service at (760) 440-8520 for a free estimate specific to your property."
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
            {"@type": "ListItem", "position": 3, "name": "Average Well Depth in ${city}, CA", "item": "https://scwellservice.com/blog/${filename}"}
        ]
    }
    </script>
    
    <script src="/js/ga4-filter.js"></script>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-5LL1YRWT5T"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-5LL1YRWT5T');</script>
    <meta property="og:image" content="https://scwellservice.com/images/logo-text-only-3x.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@scwellservice">
</head>
<body class="pb-20 lg:pb-0 bg-white">
    <header class="site-header">
        <div class="header-content">
            <a href="/" class="logo">
                <img loading="lazy" src="/images/logo-text-only-3x.png" alt="SCWS Logo" width="50" height="50">
                <span>Southern California Well Service</span>
            </a>
            <nav class="main-nav">
                <a href="/">Home</a>
                <a href="/services/">Services</a>
                <a href="/blog/">Resources</a>
                <a href="/contact/">Contact</a>
                <a href="tel:7604408520" class="cta-phone">(760) 440-8520</a>
            </nav>
        </div>
    </header>

    <main class="blog-post">
        <article>
            <h1>Average Well Depth in ${city}, California</h1>
            
            <p class="meta">Based on ${count} wells on record | ${county} County, CA</p>

            <div class="bg-gray-50 rounded-xl p-6 my-8 border border-gray-200">
                <h3 class="font-bold text-primary text-lg mb-3">Well Statistics for ${city}</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="text-center">
                        <div class="text-3xl font-bold text-primary">${avgDepth}ft</div>
                        <div class="text-gray-600 text-sm mt-1">Average Depth</div>
                    </div>
                    <div class="text-center">
                        <div class="text-3xl font-bold text-primary">${count}</div>
                        <div class="text-gray-600 text-sm mt-1">Wells on Record</div>
                    </div>
                    <div class="text-center">
                        <div class="text-3xl font-bold text-primary">${depthRange}ft</div>
                        <div class="text-gray-600 text-sm mt-1">Depth Range</div>
                    </div>
                    ${avgYield ? `<div class="text-center">
                        <div class="text-3xl font-bold text-primary">${avgYield}</div>
                        <div class="text-gray-600 text-sm mt-1">Avg Yield (GPM)</div>
                    </div>` : ''}
                </div>
            </div>

            <div id="blog-cta" class="bg-primary text-white rounded-xl p-6 my-8">
                <h3 class="font-bold text-lg mb-2">Need a Well Drilled in ${city}?</h3>
                <p class="text-gray-300 text-sm mb-4">Expert well drilling, pump installation, and repair service in ${county} County.</p>
                <a href="tel:7604408520" class="block bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg text-center transition mb-2">📞 (760) 440-8520</a>
                <a href="/contact.html" class="block bg-accent hover:bg-green-600 text-white font-bold py-3 px-4 rounded-lg text-center transition text-sm">Get Free Estimate →</a>
            </div>

            <section>
                <h2>Well Depth Distribution in ${city}</h2>
                <p>Based on ${count} wells drilled in ${city}, California, the average depth is <strong>${avgDepth} feet</strong>. ${medianDepth ? `The median depth is ${medianDepth} feet, which represents the typical well depth in the area.` : ''}</p>
                
                ${generateDepthChart(minDepth, avgDepth, maxDepth)}
                
                <ul>
                    <li><strong>Shallowest well:</strong> ${minDepth} feet</li>
                    <li><strong>Deepest well:</strong> ${maxDepth} feet</li>
                    <li><strong>Average depth:</strong> ${avgDepth} feet</li>
                    ${medianDepth ? `<li><strong>Median depth:</strong> ${medianDepth} feet</li>` : ''}
                </ul>
            </section>

            <section>
                <h2>Geology and Groundwater in ${city}</h2>
                <p>${geologyText}</p>
                ${avgStaticLevel ? `<p>The average static water level (depth to water when the pump is off) in ${city} wells is approximately ${avgStaticLevel} feet below ground surface. This indicates the natural resting level of the water table in the area.</p>` : ''}
            </section>

            <section>
                <h2>Wells by Decade</h2>
                <p>This chart shows when wells were drilled in ${city}, based on well completion reports:</p>
                ${generateDecadeChart(wellsByDecade)}
                <p>Drilling activity patterns often reflect local development trends, water availability, and economic growth periods.</p>
            </section>

            <section>
                <h2>Well Use Types in ${city}</h2>
                <p>Wells in ${city} serve various purposes. Here's the breakdown:</p>
                ${generateUseBreakdown(wellsByUse)}
            </section>

            <section>
                <h2>What This Means for Your Property</h2>
                <p>If you're planning to drill a well in ${city}, you can expect:</p>
                <ul>
                    <li><strong>Depth:</strong> ${avgDepth > 300 ? 'A deeper well requiring rotary drilling methods' : 'A moderate-depth well accessible with standard rotary drilling'}</li>
                    <li><strong>Cost:</strong> Approximately $${Math.round(avgDepth * 45)}-$${Math.round(avgDepth * 75)} for complete installation (depth, pump, pressure tank, electrical)</li>
                    <li><strong>Drilling time:</strong> ${avgDepth > 400 ? '2-5 days depending on rock hardness' : '1-3 days for typical installations'}</li>
                    <li><strong>Yield:</strong> ${avgYield ? `Average ${avgYield} GPM (gallons per minute)` : 'Varies by location and geology'}</li>
                    ${avgStaticLevel ? `<li><strong>Water level:</strong> Expect water at approximately ${avgStaticLevel} feet depth</li>` : ''}
                </ul>
            </section>

            <section>
                <h2>Well Drilling in ${city}</h2>
                <p>Southern California Well Service has drilled hundreds of wells across ${county} County, including ${city}. We understand the local geology and can provide accurate estimates based on your property's location.</p>
                
                <h3>Our ${city} Well Services:</h3>
                <ul>
                    <li>New well drilling and installation</li>
                    <li>Well pump replacement and repair</li>
                    <li>Well inspection and testing</li>
                    <li>Water quality testing</li>
                    <li>Pressure tank installation</li>
                    <li>24/7 emergency service</li>
                </ul>

                <p><strong>Call <a href="tel:+17604408520">(760) 440-8520</a></strong> for a free site evaluation and accurate quote for your ${city} property.</p>
            </section>

            <section>
                <h2>Free Well Depth Lookup Tool</h2>
                <p>Want to know the exact depth of an existing well? Use our <a href="/app/well-depth.html"><strong>free Well Depth Lookup Tool</strong></a> to search California well completion reports by address or APN.</p>
            </section>

            ${nearbyCities.length > 0 ? `<section>
                <h2>Nearby Communities</h2>
                <p>Also serving well drilling and pump service in these nearby ${county} County areas:</p>
                <ul>
                    ${nearbyCities.map(c => `<li><a href="/blog/average-well-depth-${slugify(c)}-ca.html">${c} Well Depth Data</a></li>`).join('\n                    ')}
                </ul>
            </section>` : ''}

            <section>
                <h2>Frequently Asked Questions</h2>
                
                <h3>How deep are wells in ${city}, CA?</h3>
                <p>The average well depth in ${city}, California is ${avgDepth} feet, based on ${count} wells on record. Well depths range from ${depthRange} feet depending on your specific location and the depth to productive water-bearing formations.</p>

                <h3>How much does it cost to drill a well in ${city}?</h3>
                <p>Well drilling costs in ${city} typically range from $${Math.round(avgDepth * 45)}-$${Math.round(avgDepth * 75)} for a complete system, based on the ${avgDepth}-foot average depth. The final cost depends on actual depth required, rock hardness, pump size, and site accessibility. Call us at <a href="tel:+17604408520">(760) 440-8520</a> for a free on-site estimate.</p>

                <h3>How long does it take to drill a well in ${city}?</h3>
                <p>Most wells in ${city} take ${avgDepth > 400 ? '2-5 days' : '1-3 days'} to drill and complete, depending on depth and geology. ${avgDepth > 400 ? 'Harder rock formations may require additional time.' : 'Standard rotary drilling is typically efficient in the local geology.'}</p>

                <h3>Do I need a permit to drill a well in ${county} County?</h3>
                <p>Yes, ${county} County requires a well permit before drilling. We handle all permit applications as part of our service. Permits typically take 2-4 weeks to obtain.</p>
            </section>

            <div class="bg-primary text-white rounded-xl p-6 my-8">
                <h2 class="text-xl font-bold mb-2">Ready to Drill a Well in ${city}?</h2>
                <p class="text-gray-200 mb-4">Southern California Well Service was founded in 2020 and drills wells across ${county} County. We provide honest estimates, quality workmanship, and reliable service.</p>
                <a href="tel:7604408520" class="inline-block bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg text-center transition">📞 (760) 440-8520</a>
                <p class="text-gray-300 text-sm mt-4">Licensed C-57 Contractor | San Diego, Riverside & San Bernardino Counties</p>
            </div>

        </article>
    </main>

    <footer>
        <p>&copy; 2026 Southern California Well Service. Licensed C-57 Contractor.</p>
        <p>1077 Main Street, Unit B, Ramona, CA 92065 | <a href="tel:7604408520">(760) 440-8520</a></p>
    </footer>

<!-- Sticky Mobile CTA Bar -->
<style>#sticky-cta{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:2px solid #e5e7eb;padding:12px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px;z-index:50;box-shadow:0 -4px 12px rgba(0,0,0,0.1)}#sticky-cta a{flex:1;font-weight:700;padding:12px 16px;border-radius:8px;text-align:center;color:#fff;font-size:14px;text-decoration:none}#sticky-cta .cta-call{background:#dc2626}#sticky-cta .cta-call:hover{background:#b91c1c}#sticky-cta .cta-text{background:#2563eb}#sticky-cta .cta-text:hover{background:#1d4ed8}#sticky-cta .cta-est{background:#4e9271}#sticky-cta .cta-est:hover{background:#3d7a5c}@media(min-width:1024px){#sticky-cta{display:none}}</style>
<div id="sticky-cta">
    <a href="tel:7604408520" class="cta-call">📞 Call Now</a>
    <a href="sms:7602195877" class="cta-text">💬 Text Us</a>
    <a href="/contact.html" class="cta-est">Free Estimate</a>
</div>
</body>
</html>`;

  fs.writeFileSync(filepath, html, 'utf8');
  generatedPages.push({
    city,
    county,
    count,
    avgDepth,
    filename
  });
  pagesGenerated++;
  
  if (pagesGenerated % 50 === 0) {
    console.log(`  Generated ${pagesGenerated} pages...`);
  }
});

console.log(`\n✅ Generated ${pagesGenerated} city pages`);

// Save list for sitemap update
fs.writeFileSync(
  path.join(__dirname, 'generated-pages-list.json'),
  JSON.stringify(generatedPages, null, 2),
  'utf8'
);

console.log(`Saved page list to generated-pages-list.json`);
