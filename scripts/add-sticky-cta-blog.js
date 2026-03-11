#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const blogDir = path.join(__dirname, '..', 'blog');

const stickyHtml = `
<!-- Sticky Mobile CTA Bar -->
<style>#sticky-cta{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:2px solid #e5e7eb;padding:12px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px;z-index:50;box-shadow:0 -4px 12px rgba(0,0,0,0.1)}#sticky-cta a{flex:1;font-weight:700;padding:12px 16px;border-radius:8px;text-align:center;color:#fff;font-size:14px;text-decoration:none}#sticky-cta .cta-call{background:#dc2626}#sticky-cta .cta-call:hover{background:#b91c1c}#sticky-cta .cta-est{background:#4e9271}#sticky-cta .cta-est:hover{background:#3d7a5c}@media(min-width:1024px){#sticky-cta{display:none}}</style>
<div id="sticky-cta">
    <a href="tel:7604408520" class="cta-call">📞 Call Now</a>
    <a href="/contact.html" class="cta-est">Free Estimate</a>
</div>`;

const files = fs.readdirSync(blogDir).filter(f => f.endsWith('.html') && f !== 'index.html');
let modified = 0, skipped = 0;

for (const file of files) {
  const fp = path.join(blogDir, file);
  let html = fs.readFileSync(fp, 'utf8');
  
  if (html.includes('id="sticky-cta"')) { skipped++; continue; }
  
  // Insert before </body>
  const bodyEnd = html.lastIndexOf('</body>');
  if (bodyEnd === -1) continue;
  
  html = html.slice(0, bodyEnd) + stickyHtml + '\n' + html.slice(bodyEnd);
  
  // Add bottom padding to body tag
  if (html.includes('<body class="')) {
    if (!html.includes('pb-20')) {
      html = html.replace('<body class="', '<body class="pb-20 lg:pb-0 ');
    }
  } else if (html.includes('<body>')) {
    html = html.replace('<body>', '<body style="padding-bottom:80px">');
  }
  
  fs.writeFileSync(fp, html);
  modified++;
  if (modified % 500 === 0) console.log('  ...' + modified);
}
console.log('Sticky CTA: ' + modified + ' added, ' + skipped + ' skipped');
