#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const blogDir = path.join(__dirname, '..', 'blog');

// Expanded topic clusters
const clusters = {
  'pump-repair': {
    keywords: ['pump repair', 'pump replacement', 'pump fail', 'pump not working', 'no water', 'pump cost', 'pump installation', 'submersible', 'jet pump', 'pump noise', 'pump cycling', 'pressure switch'],
    links: [
      { href: '/blog/well-pump-installation-cost.html', text: 'Well Pump Installation Cost Guide' },
      { href: '/blog/signs-well-pump-failing.html', text: '7 Signs Your Well Pump Is Failing' },
      { href: '/blog/no-water-from-well.html', text: 'No Water? Troubleshooting Guide' },
      { href: '/blog/jet-pump-vs-submersible-pump.html', text: 'Jet Pump vs Submersible Pump' },
      { href: '/blog/well-pump-lifespan-expectancy.html', text: 'How Long Do Well Pumps Last?' },
    ]
  },
  'drilling': {
    keywords: ['well drilling', 'drill a well', 'drilling cost', 'new well', 'how deep', 'permit', 'casing', 'borehole', 'drilling rig', 'cost per foot'],
    links: [
      { href: '/blog/well-drilling-cost-san-diego.html', text: 'Well Drilling Costs in San Diego' },
      { href: '/blog/how-wells-work.html', text: 'How Wells Work: Complete Guide' },
      { href: '/blog/new-construction-well-drilling.html', text: 'Well Drilling for New Construction' },
      { href: '/blog/can-you-drill-well-anywhere.html', text: 'Can You Drill a Well Anywhere?' },
      { href: '/blog/drilling-cost-per-foot-san-diego.html', text: 'Drilling Cost Per Foot' },
    ]
  },
  'water-quality': {
    keywords: ['water quality', 'water test', 'hard water', 'iron', 'bacteria', 'contamina', 'treatment', 'filter', 'softener', 'sulfur', 'smell', 'taste', 'coliform', 'nitrate', 'arsenic', 'lead', 'tds', 'ph'],
    links: [
      { href: '/blog/hard-water-solutions.html', text: 'Hard Water Solutions for Well Owners' },
      { href: '/blog/water-quality-testing-san-diego.html', text: 'Water Quality Testing Guide' },
      { href: '/blog/well-water-taste-problems.html', text: 'Well Water Taste Problems & Fixes' },
      { href: '/blog/coliform-bacteria-test-well-water.html', text: 'Coliform Bacteria Testing' },
      { href: '/blog/uv-vs-chlorine-well-water-treatment.html', text: 'UV vs Chlorine Treatment' },
    ]
  },
  'maintenance': {
    keywords: ['maintenance', 'inspection', 'pressure tank', 'annual', 'prevent', 'check', 'service', 'tune', 'flow rate', 'well cap'],
    links: [
      { href: '/blog/spring-well-maintenance-checklist.html', text: 'Well Maintenance Checklist' },
      { href: '/blog/preventive-maintenance-extends-well-life.html', text: 'Preventive Maintenance Guide' },
      { href: '/blog/pressure-tank-sizing-guide.html', text: 'Pressure Tank Sizing Guide' },
      { href: '/blog/well-pump-lifespan-expectancy.html', text: 'Well Pump Lifespan Guide' },
      { href: '/blog/well-maintenance-log-keeping.html', text: 'Keeping a Well Maintenance Log' },
    ]
  },
  'cost': {
    keywords: ['cost', 'price', 'how much', 'budget', 'estimate', 'expensive', 'afford', 'financing', 'quote', 'labor'],
    links: [
      { href: '/blog/well-pump-installation-cost.html', text: 'Pump Installation Cost Guide' },
      { href: '/blog/well-drilling-cost-san-diego.html', text: 'Well Drilling Cost in San Diego' },
      { href: '/blog/drilling-cost-per-foot-san-diego.html', text: 'Cost Per Foot Breakdown' },
      { href: '/blog/well-pump-replacement-labor-cost.html', text: 'Pump Replacement Labor Costs' },
      { href: '/blog/well-water-vs-city-water-cost.html', text: 'Well Water vs City Water Cost' },
    ]
  },
  'emergency': {
    keywords: ['emergency', 'no water', 'urgent', '24/7', 'same day', 'broken', 'leak', 'flood', 'burst', 'power outage'],
    links: [
      { href: '/blog/no-water-from-well.html', text: 'No Water? What To Do Now' },
      { href: '/blog/well-pump-not-working.html', text: 'Well Pump Not Working Guide' },
      { href: '/blog/breaker-trips-when-pump-starts.html', text: 'Breaker Trips When Pump Starts' },
      { href: '/blog/air-lock-well-pump-fix.html', text: 'Air Lock in Well Pump Fix' },
      { href: '/blog/backup-generator-for-well-pump.html', text: 'Backup Generator for Well Pumps' },
    ]
  },
  'location': {
    keywords: ['san diego', 'riverside', 'san bernardino', 'ramona', 'valley center', 'escondido', 'temecula', 'murrieta', 'fallbrook', 'julian', 'alpine', 'anza', 'hemet', 'aguanga'],
    links: [
      { href: '/blog/well-drilling-cost-san-diego.html', text: 'Well Drilling in San Diego County' },
      { href: '/blog/how-wells-work.html', text: 'How Water Wells Work' },
      { href: '/blog/signs-well-pump-failing.html', text: 'Signs Your Pump Is Failing' },
      { href: '/blog/spring-well-maintenance-checklist.html', text: 'Annual Maintenance Checklist' },
      { href: '/blog/well-pump-installation-cost.html', text: 'Pump Installation Pricing' },
    ]
  }
};

const files = fs.readdirSync(blogDir).filter(f => f.endsWith('.html') && f !== 'index.html');
let modified = 0, skipped = 0;

for (const file of files) {
  const fp = path.join(blogDir, file);
  let html = fs.readFileSync(fp, 'utf8');
  
  if (html.includes('id="related-articles-cta"')) { skipped++; continue; }
  
  const lowerHtml = html.toLowerCase();
  const thisPath = '/blog/' + file;
  
  // Score each cluster
  let bestCluster = null;
  let bestScore = 0;
  for (const [name, cluster] of Object.entries(clusters)) {
    let score = 0;
    for (const kw of cluster.keywords) {
      const regex = new RegExp(kw, 'gi');
      const matches = lowerHtml.match(regex);
      if (matches) score += Math.min(matches.length, 3); // cap at 3 per keyword
    }
    if (score > bestScore) { bestScore = score; bestCluster = cluster; }
  }
  
  if (!bestCluster || bestScore < 2) {
    // Fallback: use general links for any page
    bestCluster = clusters['location'];
  }
  
  const related = bestCluster.links.filter(l => l.href !== thisPath).slice(0, 3);
  if (related.length < 2) continue;
  
  const relatedHtml = '\n<div id="related-articles-cta" class="bg-gray-50 rounded-xl p-6 my-8 border border-gray-200">\n    <h3 class="font-bold text-primary text-lg mb-3">📚 Related Articles</h3>\n    <ul class="space-y-2">\n' +
    related.map(r => '        <li><a href="' + r.href + '" class="text-accent hover:text-green-700 font-medium hover:underline">' + r.text + ' →</a></li>').join('\n') +
    '\n    </ul>\n</div>';
  
  // Insert before </article>, or before last footer, or before </main>, or before </body>
  let insertBefore = html.lastIndexOf('</article>');
  if (insertBefore < 0) insertBefore = html.lastIndexOf('<footer');
  if (insertBefore < 0) insertBefore = html.lastIndexOf('</main>');
  if (insertBefore < 0) insertBefore = html.lastIndexOf('<!-- Sticky Mobile CTA');
  if (insertBefore < 0) insertBefore = html.lastIndexOf('</body>');
  
  if (insertBefore > 0) {
    html = html.slice(0, insertBefore) + relatedHtml + '\n' + html.slice(insertBefore);
    fs.writeFileSync(fp, html);
    modified++;
    if (modified % 1000 === 0) console.log('  ...' + modified);
  }
}

console.log('Related links: ' + modified + ' added, ' + skipped + ' already had them');
