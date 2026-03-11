#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const blogDir = path.join(__dirname, '..', 'blog');

const ctaHtml = '\n<div id="blog-cta" class="bg-primary text-white rounded-xl p-6 my-8">\n    <h3 class="font-bold text-lg mb-2">Need Help With Your Well?</h3>\n    <p class="text-gray-300 text-sm mb-4">Our experts are ready to help. Free estimates, same-day emergency service.</p>\n    <a href="tel:7604408520" class="block bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg text-center transition mb-2">📞 (760) 440-8520</a>\n    <a href="/contact.html" class="block bg-accent hover:bg-green-600 text-white font-bold py-3 px-4 rounded-lg text-center transition text-sm">Get Free Estimate →</a>\n</div>';

const files = fs.readdirSync(blogDir)
  .filter(f => f.endsWith('.html') && f !== 'index.html');

let modified = 0, skipped = 0;

for (const file of files) {
  const filePath = path.join(blogDir, file);
  let html = fs.readFileSync(filePath, 'utf8');

  // Skip if already has our CTA (exact id match)
  if (html.includes('id="blog-cta"')) { skipped++; continue; }
  // Skip if has existing CTA boxes (class-based)
  if (html.includes('blog-cta-section') || html.includes('blog-cta-box')) { skipped++; continue; }

  // Insert after TOC if exists
  if (html.includes('id="table-of-contents"')) {
    const tocStart = html.indexOf('<div id="table-of-contents"');
    // Find the matching closing </div>
    const ulEnd = html.indexOf('</ul>', tocStart);
    const tocEnd = html.indexOf('</div>', ulEnd) + 6;
    if (tocEnd > 6) {
      html = html.slice(0, tocEnd) + ctaHtml + html.slice(tocEnd);
      fs.writeFileSync(filePath, html);
      modified++;
      if (modified % 500 === 0) console.log('  ...' + modified + ' files');
      continue;
    }
  }

  // Otherwise after 3rd </p> after h1
  const h1Match = html.match(/<h1[^>]*>/i);
  if (h1Match) {
    let searchFrom = h1Match.index;
    let pCount = 0;
    let insertAt = -1;
    while (pCount < 3) {
      const nextP = html.indexOf('</p>', searchFrom);
      if (nextP === -1) break;
      pCount++;
      searchFrom = nextP + 4;
      insertAt = searchFrom;
    }
    if (insertAt > 0) {
      html = html.slice(0, insertAt) + ctaHtml + html.slice(insertAt);
      fs.writeFileSync(filePath, html);
      modified++;
      if (modified % 500 === 0) console.log('  ...' + modified + ' files');
    }
  }
}

console.log('CTA: ' + modified + ' added, ' + skipped + ' skipped');
