#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const blogDir = path.join(__dirname, '..', 'blog');

function slugify(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

const files = fs.readdirSync(blogDir)
  .filter(f => f.endsWith('.html') && f !== 'index.html');

let modified = 0, skipped = 0;

for (const file of files) {
  const filePath = path.join(blogDir, file);
  let html = fs.readFileSync(filePath, 'utf8');

  if (html.includes('id="table-of-contents"')) { skipped++; continue; }

  const h2Regex = /<h2[^>]*>(.*?)<\/h2>/gi;
  const h2s = [];
  const seenSlugs = new Set();
  let match;
  while ((match = h2Regex.exec(html)) !== null) {
    const text = match[1].replace(/<[^>]+>/g, '').trim();
    if (!text) continue;
    let slug = slugify(text);
    // Dedupe slugs
    if (seenSlugs.has(slug)) {
      let i = 2;
      while (seenSlugs.has(slug + '-' + i)) i++;
      slug = slug + '-' + i;
    }
    seenSlugs.add(slug);
    h2s.push({ text, slug, fullMatch: match[0], index: match.index });
  }

  if (h2s.length < 3) continue;

  // Dedupe: skip if multiple h2s have exact same text (like "Related Articles")
  const uniqueTexts = [...new Set(h2s.map(h => h.text))];
  const tocItems = [];
  const addedTexts = new Set();
  for (const h2 of h2s) {
    if (addedTexts.has(h2.text)) continue; // skip duplicate text entries in TOC
    addedTexts.add(h2.text);
    tocItems.push(h2);
  }

  if (tocItems.length < 3) continue;

  // Add ids to h2 tags
  for (const h2 of h2s) {
    if (!h2.fullMatch.includes('id=')) {
      const newH2 = h2.fullMatch.replace('<h2', '<h2 id="' + h2.slug + '"');
      html = html.replace(h2.fullMatch, newH2);
    }
  }

  const tocHtml = '\n<div id="table-of-contents" class="bg-gray-50 rounded-xl p-6 my-8 border border-gray-200">\n    <h3 class="font-bold text-primary text-lg mb-3">📋 In This Guide</h3>\n    <ul class="space-y-2">\n' +
    tocItems.map(h => '        <li><a href="#' + h.slug + '" class="text-accent hover:text-green-700 font-medium">' + h.text + '</a></li>').join('\n') +
    '\n    </ul>\n</div>';

  const h1Match = html.match(/<h1[^>]*>.*?<\/h1>/is);
  if (h1Match) {
    const afterH1 = h1Match.index + h1Match[0].length;
    const firstPEnd = html.indexOf('</p>', afterH1);
    if (firstPEnd !== -1) {
      const insertAt = firstPEnd + 4;
      html = html.slice(0, insertAt) + tocHtml + html.slice(insertAt);
      fs.writeFileSync(filePath, html);
      modified++;
      if (modified % 500 === 0) console.log('  ...' + modified + ' files');
    }
  }
}

console.log('TOC: ' + modified + ' added, ' + skipped + ' already had one');
