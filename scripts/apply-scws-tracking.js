#!/usr/bin/env node
/**
 * Surgical tracking bootstrap install.
 * Replaces standalone inline gtag config scripts with /js/scws-tracking.js
 * and adds cookie-consent.js after ga4-filter.js when missing.
 *
 * Does not reformat unrelated HTML.
 */
'use strict';

var fs = require('fs');
var path = require('path');

var ROOT = path.join(__dirname, '..');
var SKIP_DIRS = new Set(['node_modules', '.git', 'scripts', '_internal', 'ops']);

var MONEY_PAGES = [
  'index.html',
  'contact.html',
  'cost-calculator.html',
  'free-guide.html',
  'pump-repair.html',
  'emergency.html',
  'heritage-well-service.html',
  'faq.html',
  'water-treatment.html',
  'pages/about.html',
  'pages/faq.html',
  'pages/estimate.html',
  'pages/landing/emergency.html',
  'pages/landing/drilling.html',
  'pages/services/index.html',
  'pages/services/well-drilling.html',
  'pages/services/well-drilling-san-diego.html',
  'pages/services/water-testing.html',
  'pages/services/pump-repair.html',
  'pages/services/maintenance.html',
  'pages/services/emergency-well-service.html',
  'pages/services/diagnostics.html',
  'pages/services/controls.html',
  'services/index.html'
];

function walk(dir) {
  var files = [];
  fs.readdirSync(dir, { withFileTypes: true }).forEach(function (entry) {
    var full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!SKIP_DIRS.has(entry.name)) files = files.concat(walk(full));
    } else if (entry.name.endsWith('.html')) {
      files.push(full);
    }
  });
  return files;
}

function isConfigOnlyScript(body) {
  var stripped = body
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\/\/[^\n]*/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  if (!stripped) return false;
  if (/handleFormSubmit|submitLead|scwsTrackLeadFormSuccess|fetch\(/.test(stripped)) return false;
  if (!/dataLayer/.test(stripped) && !/gtag\(/.test(stripped)) return false;

  var withoutSetup = stripped
    .replace(/window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\];?/g, '')
    .replace(/dataLayer\s*=\s*(?:window\.)?dataLayer\s*\|\|\s*\[\];?/g, '')
    .replace(/function gtag\(\)\s*\{\s*dataLayer\.push\(arguments\);?\s*\}/g, '')
    .replace(/gtag\('js',\s*new Date\(\)\);?/g, '')
    .replace(/gtag\('config',\s*'G-5LL1YRWT5T'\);?/g, '')
    .replace(/gtag\('config',\s*'AW-490838730'\);?/g, '')
    .replace(/gtag\('config',\s*'AW-490838730\/aFiRCMDlofAbEMq1huoB',\s*\{\s*'?phone_conversion_number'?\s*:\s*'\(760\) 440-8520'\s*\}\);?/g, '')
    .replace(/function trackFormClick\(\)\s*\{\s*\}/g, '')
    .replace(/function trackPhoneClick\(\)\s*\{\s*if\s*\(window\.scwsCallTracking\)\s*return;\s*\}/g, '')
    .trim();

  return withoutSetup === '';
}

function indentOf(html, index) {
  var lineStart = html.lastIndexOf('\n', index - 1) + 1;
  var prefix = html.slice(lineStart, index);
  var match = prefix.match(/^(\s*)/);
  return match ? match[1] : '';
}

function replaceConfigScripts(html) {
  var changed = false;
  var result = '';
  var cursor = 0;
  var scriptRe = /<script(?![^>]*\bsrc=)([^>]*)>([\s\S]*?)<\/script>/g;
  var match;
  while ((match = scriptRe.exec(html))) {
    var full = match[0];
    var body = match[2];
    if (!isConfigOnlyScript(body)) continue;
    var indent = indentOf(html, match.index);
    var replacement = indent + '<script src="/js/scws-tracking.js"></script>';
    result += html.slice(cursor, match.index) + replacement;
    cursor = match.index + full.length;
    changed = true;
  }
  if (!changed) return { html: html, replaced: false };
  return { html: result + html.slice(cursor), replaced: true };
}

function addCookieConsent(html) {
  if (html.indexOf('cookie-consent.js') !== -1) return { html: html, added: false };
  if (html.indexOf('G-5LL1YRWT5T') === -1 && html.indexOf('gtag/js') === -1) {
    return { html: html, added: false };
  }
  var patterns = [
    /(<script src="\/js\/ga4-filter\.js"><\/script>)/,
    /(<script src='\/js\/ga4-filter\.js'><\/script>)/
  ];
  for (var i = 0; i < patterns.length; i++) {
    if (patterns[i].test(html)) {
      html = html.replace(patterns[i], '$1\n<script src="/js/cookie-consent.js"></script>');
      return { html: html, added: true };
    }
  }
  return { html: html, added: false };
}

function dropRedundantLeadEvents(html) {
  if (html.indexOf('scws-tracking.js') === -1) return { html: html, dropped: false };
  if (html.indexOf('lead-events.js') === -1) return { html: html, dropped: false };
  var next = html.replace(/\n?\s*<script src="\/js\/lead-events\.js"><\/script>/g, '');
  return { html: next, dropped: next !== html };
}

var stats = { replaced: 0, consent: 0, droppedLead: 0, skipped: 0 };
var moneySet = new Set(MONEY_PAGES.map(function (p) { return path.join(ROOT, p); }));

function processFile(file, forceReplace) {
  var html = fs.readFileSync(file, 'utf8');
  var original = html;
  var consent = addCookieConsent(html);
  html = consent.html;
  if (consent.added) stats.consent += 1;

  var shouldReplace = forceReplace || moneySet.has(file) || file.indexOf(path.join(ROOT, 'recent-work')) === 0;
  if (shouldReplace || isProbablyStandaloneConfigPage(html)) {
    var replaced = replaceConfigScripts(html);
    html = replaced.html;
    if (replaced.replaced) stats.replaced += 1;
    var dropped = dropRedundantLeadEvents(html);
    html = dropped.html;
    if (dropped.dropped) stats.droppedLead += 1;
  }

  if (html !== original) fs.writeFileSync(file, html);
  else stats.skipped += 1;
}

function isProbablyStandaloneConfigPage(html) {
  return /gtag\('config',\s*'G-5LL1YRWT5T'\)/.test(html) && html.indexOf('scws-tracking.js') === -1;
}

MONEY_PAGES.forEach(function (rel) {
  var file = path.join(ROOT, rel);
  if (fs.existsSync(file)) processFile(file, true);
});

walk(path.join(ROOT, 'recent-work')).forEach(function (file) {
  processFile(file, true);
});

walk(ROOT).forEach(function (file) {
  if (moneySet.has(file)) return;
  if (file.indexOf(path.join(ROOT, 'recent-work')) === 0) return;
  var html = fs.readFileSync(file, 'utf8');
  if (html.indexOf('G-5LL1YRWT5T') === -1 && html.indexOf('gtag/js') === -1) return;
  processFile(file, false);
});

console.log(
  'Done. Replaced config: ' + stats.replaced +
  ', added consent: ' + stats.consent +
  ', dropped extra lead-events: ' + stats.droppedLead +
  ', unchanged: ' + stats.skipped
);
