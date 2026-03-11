#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const blogDir = path.join(__dirname, '..', 'blog');

// Define topic clusters for cross-linking
const clusters = {
  'pump-repair': {
    keywords: ['pump repair', 'pump replacement', 'pump fail', 'pump not working', 'no water', 'pump cost', 'pump installation'],
    links: [
      { href: '/blog/well-pump-installation-cost.html', text: 'Well Pump Installation Cost Guide' },
      { href: '/blog/signs-well-pump-failing.html', text: '7 Warning Signs Your Well Pump Is Failing' },
      { href: '/blog/no-water-from-well.html', text: 'No Water From Well? Troubleshooting Guide' },
      { href: '/blog/well-pump-not-working.html', text: 'Well Pump Not Working: What to Check' },
      { href: '/blog/jet-pump-vs-submersible-pump.html', text: 'Jet Pump vs Submersible: Which Is Better?' },
    ]
  },
  'drilling': {
    keywords: ['well drilling', 'drill a well', 'drilling cost', 'new well', 'how deep'],
    links: [
      { href: '/blog/well-drilling-cost-san-diego.html', text: 'Well Drilling Costs in San Diego' },
      { href: '/blog/how-wells-work.html', text: 'How Wells Work: Complete Guide' },
      { href: '/blog/new-construction-well-drilling.html', text: 'Well Drilling for New Construction' },
      { href: '/blog/can-you-drill-well-anywhere.html', text: 'Can You Drill a Well Anywhere?' },
      { href: '/blog/drilling-cost-per-foot-san-diego.html', text: 'Drilling Cost Per Foot in San Diego' },
    ]
  },
  'water-quality': {
    keywords: ['water quality', 'water test', 'hard water', 'iron', 'bacteria', 'contamina', 'treatment', 'filter', 'softener'],
    links: [
      { href: '/blog/hard-water-solutions.html', text: 'Hard Water Solutions for Well Owners' },
      { href: '/blog/water-quality-testing-san-diego.html', text: 'Water Quality Testing in San Diego' },
      { href: '/blog/well-water-taste-problems.html', text: 'Well Water Taste Problems & Fixes' },
      { href: '/blog/coliform-bacteria-test-well-water.html', text: 'Coliform Bacteria Testing Guide' },
      { href: '/blog/uv-vs-chlorine-well-water-treatment.html', text: 'UV vs Chlorine Treatment Comparison' },
    ]
  },
  'maintenance': {
    keywords: ['maintenance', 'inspection', 'pressure tank', 'annual', 'prevent'],
    links: [
      { href: '/blog/spring-well-maintenance-checklist.html', text: 'Spring Well Maintenance Checklist' },
      { href: '/blog/preventive-maintenance-extends-well-life.html', text: 'How Preventive Maintenance Extends Well Life' },
      { href: '/blog/pressure-tank-sizing-guide.html', text: 'Pressure Tank Sizing Guide' },
      { href: '/blog/well-maintenance-log-keeping.html', text: 'Well Maintenance Log Keeping' },
      { href: '/blog/well-pump-lifespan-expectancy.html', text: 'Well Pump Lifespan & When to Replace' },
    ]
  }
};

const files = fs.readdirSync(blogDir)
  .filter(f => f.endsWith('.html') && f !== 'index.html')
  .map(f => ({ name: f, size: fs.statSync(path.join(blogDir, f)).size }))
  .sort((a, b) => b.size - a.size)
  .slice(0, 200); // Top 200 posts

let modified = 0;

for (const file of files) {
  const fp = path.join(blogDir, file.name);
  let html = fs.readFileSync(fp, 'utf8');
  
  if (html.includes('id="related-articles-cta"')) continue;
  
  const lowerHtml = html.toLowerCase();
  const thisPath = '/blog/' + file.name;
  
  // Find matching cluster
  let bestCluster = null;
  let bestScore = 0;
  for (const [name, cluster] of Object.entries(clusters)) {
    let score = 0;
    for (const kw of cluster.keywords) {
      if (lowerHtml.includes(kw)) score++;
    }
    if (score > bestScore) { bestScore = score; bestCluster = cluster; }
  }
  
  if (!bestCluster || bestScore < 2) continue;
  
  // Pick 3 related links (not self)
  const related = bestCluster.links.filter(l => l.href !== thisPath).slice(0, 3);
  if (related.length < 2) continue;
  
  const relatedHtml = '\n<div id="related-articles-cta" class="bg-gray-50 rounded-xl p-6 my-8 border border-gray-200">\n    <h3 class="font-bold text-primary text-lg mb-3">📚 Related Articles</h3>\n    <ul class="space-y-2">\n' +
    related.map(r => '        <li><a href="' + r.href + '" class="text-accent hover:text-green-700 font-medium hover:underline">' + r.text + ' →</a></li>').join('\n') +
    '\n    </ul>\n</div>';
  
  // Insert before the last </article> or before footer
  const articleEnd = html.lastIndexOf('</article>');
  const footerStart = html.indexOf('<footer');
  const insertBefore = articleEnd > 0 ? articleEnd : (footerStart > 0 ? footerStart : -1);
  
  if (insertBefore > 0) {
    html = html.slice(0, insertBefore) + relatedHtml + '\n' + html.slice(insertBefore);
    fs.writeFileSync(fp, html);
    modified++;
  }
}

console.log('Related links: ' + modified + ' posts updated');
