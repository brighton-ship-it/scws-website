#!/usr/bin/env node
// Add mid-article CTA box to top blog posts
const fs = require('fs');
const path = require('path');

const blogDir = path.join(__dirname, '..', 'blog');

const ctaHtml = `
<div id="blog-cta" class="bg-primary text-white rounded-xl p-6 my-8">
    <h3 class="font-bold text-lg mb-2">Need Help With Your Well?</h3>
    <p class="text-gray-300 text-sm mb-4">Our experts are ready to help. Free estimates, same-day emergency service.</p>
    <a href="tel:7604408520" class="block bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg text-center transition mb-2">📞 (760) 440-8520</a>
    <a href="/contact.html" class="block bg-accent hover:bg-green-600 text-white font-bold py-3 px-4 rounded-lg text-center transition text-sm">Get Free Estimate →</a>
</div>`;

// Get top 50 blog posts by file size
const files = fs.readdirSync(blogDir)
  .filter(f => f.endsWith('.html'))
  .map(f => ({ name: f, size: fs.statSync(path.join(blogDir, f)).size }))
  .sort((a, b) => b.size - a.size)
  .slice(0, 50);

let modified = 0;

for (const file of files) {
  const filePath = path.join(blogDir, file.name);
  let html = fs.readFileSync(filePath, 'utf8');

  // Skip if already has CTA
  if (html.includes('id="blog-cta"')) continue;

  // Insert after TOC if it exists, otherwise after 3rd </p> in content
  const tocEnd = html.indexOf('</div>', html.indexOf('id="table-of-contents"'));
  if (html.includes('id="table-of-contents"') && tocEnd !== -1) {
    // Find the closing </div> of the TOC
    const insertAt = tocEnd + 6;
    html = html.slice(0, insertAt) + ctaHtml + html.slice(insertAt);
  } else {
    // Find the h1, then insert after the 3rd </p> after it
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
      }
    }
  }

  fs.writeFileSync(filePath, html);
  modified++;
  console.log(`✅ CTA added: ${file.name}`);
}

console.log(`\nDone: ${modified} files modified`);
