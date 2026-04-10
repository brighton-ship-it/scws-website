#!/usr/bin/env node
/**
 * Inject call-tracking.js into all HTML pages that have GA4
 * Adds <script src="/js/call-tracking.js"></script> right after the closing </script> of the gtag config block
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SCRIPT_TAG = '<script src="/js/call-tracking.js"></script>';

function walk(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory() && !['node_modules', '.git', 'scripts', 'tools'].includes(entry.name)) {
      files.push(...walk(full));
    } else if (entry.name.endsWith('.html')) {
      files.push(full);
    }
  }
  return files;
}

let updated = 0, skipped = 0, already = 0;

for (const file of walk(ROOT)) {
  let html = fs.readFileSync(file, 'utf8');
  
  // Skip if already has call-tracking.js
  if (html.includes('call-tracking.js')) { already++; continue; }
  
  // Skip if no GA4
  if (!html.includes('G-5LL1YRWT5T')) { skipped++; continue; }
  
  // Insert after the GA4 config block closing </script>
  // Pattern: gtag('config', 'G-5LL1YRWT5T'); followed by </script>
  const pattern = /(gtag\('config',\s*'G-5LL1YRWT5T'\);?\s*<\/script>)/;
  if (pattern.test(html)) {
    html = html.replace(pattern, '$1\n    ' + SCRIPT_TAG);
    fs.writeFileSync(file, html);
    updated++;
  } else {
    // Fallback: insert before </head>
    if (html.includes('</head>')) {
      html = html.replace('</head>', '    ' + SCRIPT_TAG + '\n</head>');
      fs.writeFileSync(file, html);
      updated++;
    } else {
      skipped++;
    }
  }
}

console.log(`Done. Updated: ${updated}, Already had it: ${already}, Skipped (no GA4/head): ${skipped}`);
