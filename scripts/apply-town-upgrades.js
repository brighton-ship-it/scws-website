#!/usr/bin/env node
/**
 * Additive town-page upgrades. Does not rewrite titles, canonicals,
 * existing JSON-LD, or existing sitemap <url> lines.
 *
 *   node scripts/apply-town-upgrades.js css
 *   node scripts/apply-town-upgrades.js extras
 *   node scripts/apply-town-upgrades.js hubs
 *   node scripts/apply-town-upgrades.js reviews
 *   node scripts/apply-town-upgrades.js book
 *   node scripts/apply-town-upgrades.js towns
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const MODE = process.argv[2] || 'all';

const RATING = '4.8';
const REVIEW_COUNT = '175';
const REVIEW_COUNT_LABEL = '175';
const RAMONA_GBP = 'https://g.page/r/CU9X_NG3TvP2EBM/review';
const ANZA_GBP = 'https://g.page/r/Cajtn6jSo-ONEBM';
const PHONE_DISPLAY = '(760) 440-8520';
const PHONE_TEL = 'tel:+17604408520';
const TEXT_DISPLAY = '(760) 823-7963';
const TEXT_SMS = 'sms:+17608237963';

const CALCULATOR_RANGES = [
  ['Well pump repair', '$300–$1,200'],
  ['Well pump replacement', '$1,500–$4,500'],
  ['New well drilling', '$15,000–$50,000+'],
  ['Water quality service', '$200–$800'],
  ['Pressure system service', '$250–$1,000'],
  ['Diagnostic service', '$150–$500']
];

function read(rel) {
  return fs.readFileSync(path.join(ROOT, rel), 'utf8');
}
function write(rel, text) {
  fs.writeFileSync(path.join(ROOT, rel), text);
}
function exists(rel) {
  return fs.existsSync(path.join(ROOT, rel));
}
function slug(s) {
  return String(s || '')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
function looksLikePii(text) {
  const t = String(text || '');
  if (/\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b/.test(t)) return true;
  if (/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(t)) return true;
  if (/\b\d{2,5}\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Court|Ct|Way)\b/i.test(t)) return true;
  return false;
}
function walkHtml(dir, out) {
  if (!fs.existsSync(dir)) return out;
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    const st = fs.statSync(full);
    if (st.isDirectory()) walkHtml(full, out);
    else if (name.endsWith('.html')) out.push(full);
  }
  return out;
}
function ensureCss(html) {
  if (html.includes('/css/city-pages.css')) return html;
  if (!html.includes('</head>')) return html;
  return html.replace('</head>', '<link rel="stylesheet" href="/css/city-pages.css"/>\n</head>');
}
function ensureBookScript(html) {
  if (html.includes('/js/book-online.js')) return html;
  if (!html.includes('</body>')) return html;
  return html.replace('</body>', '<script src="/js/book-online.js" defer></script>\n</body>');
}
function townNameFrom(html, dirSlug) {
  const m = html.match(/<h1[^>]*>\s*(?:Well Services in|Well Pump Repair in|Well Drilling in)\s+([^<,]+)/i);
  if (m) return m[1].replace(/&amp;/g, '&').trim();
  return dirSlug.split('-').map(function (w) { return w.charAt(0).toUpperCase() + w.slice(1); }).join(' ');
}
const SKIP_INDEX = { agricultural: 1, commercial: 1, hoa: 1, residential: 1, vineyard: 1, 'san-diego': 1 };
function isTownIndex(html, dirSlug) {
  if (SKIP_INDEX[dirSlug]) return false;
  if (/http-equiv="refresh"/i.test(html)) return false;
  return /<h1[\s>]/i.test(html);
}

function loadProjects() {
  const projects = JSON.parse(read('recent-work/projects.json')).projects;
  const by = {};
  for (const p of projects) {
    const s = slug(p.location);
    if (!s) continue;
    if (!by[s]) by[s] = [];
    by[s].push(p);
  }
  for (const s of Object.keys(by)) {
    by[s].sort(function (a, b) {
      return String(b.date || '').localeCompare(String(a.date || '')) || String(b.id || '').localeCompare(String(a.id || ''));
    });
  }
  return by;
}
function loadReviews() {
  const raw = JSON.parse(read('scripts/reviews-by-city.json'));
  const by = {};
  for (const city of Object.keys(raw)) {
    const list = (raw[city] || []).filter(function (r) {
      return r && r.text && !looksLikePii(r.text) && !looksLikePii(r.name);
    });
    list.sort(function (a, b) { return String(b.date || '').localeCompare(String(a.date || '')); });
    by[slug(city)] = { city: city, reviews: list };
  }
  return by;
}

function loadKeptPhotoKeys() {
  const kept = {};
  try {
    const decisions = JSON.parse(read('ops/photo-audit/decisions.json'));
    const photos = decisions.photos || {};
    Object.keys(photos).forEach(function (key) {
      if (String((photos[key] || {}).decision || '').toLowerCase() === 'keep') kept[key.toLowerCase()] = 1;
    });
  } catch (e) {}
  return kept;
}
function loadPaperworkNames() {
  const names = {};
  try {
    read('recent-work/paperwork-photos.txt').split(/\n/).forEach(function (line) {
      const name = line.replace(/#.*/, '').trim();
      if (name) names[name] = 1;
    });
  } catch (e) {}
  return names;
}
function keptPhoto(job, kept, paperwork) {
  const photos = job.photos || [];
  for (let i = 0; i < photos.length; i++) {
    const photo = photos[i];
    const file = photo && photo.file;
    if (!file || photo.excluded || paperwork[file]) continue;
    const match = String(file).match(/^(job\d+)_(\d+)\./i);
    const key = match ? (match[1].toLowerCase() + ':' + match[2]) : '';
    if (!key || !kept[key]) continue;
    if (!exists('images/recent-work/' + file)) continue;
    return photo;
  }
  return null;
}
function jobCards(jobs, limit) {
  const kept = loadKeptPhotoKeys();
  const paperwork = loadPaperworkNames();
  const cards = [];
  for (const job of jobs.slice(0, limit)) {
    if (!job.slug || !exists('recent-work/' + job.slug + '.html')) continue;
    const photo = keptPhoto(job, kept, paperwork);
    const file = photo && photo.file;
    const img = file
      ? '<img src="/images/recent-work/' + esc(file) + '" alt="' + esc(photo.alt || job.title) + '" width="800" height="450" loading="lazy">'
      : '';
    cards.push(
      '<a class="recent-work-card" href="/recent-work/' + esc(job.slug) + '.html">\n' +
      img + '\n<div class="rw-body">\n<h3>' + esc(job.title) + '</h3>\n<p>' + esc(job.location) + '</p>\n</div>\n</a>'
    );
  }
  return cards.join('\n');
}

function replaceGrid(html, cardsHtml) {
  const open = '<div class="recent-work-grid">';
  const start = html.indexOf(open);
  if (start < 0 || !cardsHtml) return html;
  let i = start + open.length;
  let depth = 1;
  while (i < html.length && depth > 0) {
    const nextOpen = html.indexOf('<div', i);
    const nextClose = html.indexOf('</div>', i);
    if (nextClose < 0) return html;
    if (nextOpen !== -1 && nextOpen < nextClose) {
      depth++;
      i = nextOpen + 4;
    } else {
      depth--;
      if (depth === 0) {
        const end = nextClose + '</div>'.length;
        return html.slice(0, start) + open + '\n' + cardsHtml + '\n</div>' + html.slice(end);
      }
      i = nextClose + 6;
    }
  }
  return html;
}

function ratingSchema(extraReviews) {
  const node = {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    '@id': 'https://scwellservice.com/#reviews',
    name: 'Southern California Well Service',
    telephone: '+1-760-440-8520',
    url: 'https://scwellservice.com/',
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: RATING,
      reviewCount: REVIEW_COUNT,
      bestRating: '5',
      worstRating: '1'
    }
  };
  if (extraReviews && extraReviews.length) {
    node.review = extraReviews.map(function (r) {
      const item = {
        '@type': 'Review',
        author: { '@type': 'Person', name: r.name },
        reviewBody: r.text
      };
      if (r.date && /^\d{4}-\d{2}-\d{2}$/.test(r.date)) item.datePublished = r.date;
      if (r.city) item.name = 'Google review, ' + r.city;
      return item;
    });
  }
  return JSON.stringify(node, null, 2).replace(/</g, '\\u003c');
}

function upsertSchema(html) {
  return html.replace(
    /<!-- AggregateRating from js\/gbp-ratings\.js[\s\S]*?<script type="application\/ld\+json" id="town-aggregate-rating">[\s\S]*?<\/script>\n?/,
    ''
  );
}

function reviewCards(list, town) {
  return list.map(function (r) {
    return (
      '<article class="review-card">\n' +
      '<div class="reviewer">' + esc(r.name) + '</div>\n' +
      '<div class="review-meta">' + esc(r.city || town) + (r.date ? ' · ' + esc(r.date) : '') + '</div>\n' +
      '<p class="review-text">' + esc(r.text) + '</p>\n' +
      '</article>'
    );
  }).join('\n');
}

function extrasHtml(town, jobs, reviews, includeJobs) {
  const local = (reviews || []).slice(0, 3).map(function (r) {
    return { name: r.name, text: r.text, date: r.date, city: town };
  });
  const area = 'recent-work/areas/' + slug(town) + '.html';
  const areaHref = exists(area) ? '/recent-work/areas/' + slug(town) + '.html' : '/recent-work/';
  let jobsBlock = '';
  if (includeJobs) {
    const cards = jobCards(jobs, 6);
    jobsBlock =
      '<section class="recent-jobs-cards" id="recent-jobs">\n' +
      '<h2>Recent jobs in ' + esc(town) + '</h2>\n' +
      '<p class="rw-lede">' + (cards ? 'Latest photographed jobs in ' + esc(town) + '.' : 'No photographed job in ' + esc(town) + ' yet.') + '</p>\n' +
      (cards ? '<div class="recent-work-grid">\n' + cards + '\n</div>\n' : '') +
      '<p class="rw-all"><a href="' + areaHref + '">Recent work in ' + esc(town) + '</a> · <a href="/recent-work/">All recent work</a></p>\n' +
      '</section>\n';
  }
  const quotes = local.length
    ? '<div class="reviews-list">\n' + reviewCards(local, town) + '\n</div>\n'
    : '<p>Review text for ' + esc(town) + ' is not in the site archive. The company rating below is the combined Google figure for the Ramona and Anza shops.</p>\n';
  return (
    '<!-- TOWN_PAGE_EXTRAS_START -->\n' +
    '<section class="town-extras" id="town-extras">\n' +
    '<div class="town-rating">\n' +
    '<p class="town-stars" aria-hidden="true">★★★★★</p>\n' +
    '<p>About <strong>' + RATING + '</strong> from ' + REVIEW_COUNT_LABEL + ' Google reviews across our Ramona and Anza shops. Ramona is 4.7 from 62. Anza is 4.8 from 113.</p>\n' +
    '<p><a href="/reviews/">Read our Google reviews</a></p>\n' +
    '<p><a href="' + RAMONA_GBP + '" target="_blank" rel="noopener">Ramona Google reviews</a> · <a href="' + ANZA_GBP + '" target="_blank" rel="noopener">Anza Google reviews</a></p>\n' +
    '</div>\n' +
    '<div class="town-reviews">\n' +
    '<h2>Reviews</h2>\n' +
    quotes +
    '<p><a href="/reviews/">All reviews</a></p>\n' +
    '</div>\n' +
    jobsBlock +
    '</section>\n' +
    '<!-- TOWN_PAGE_EXTRAS_END -->\n'
  );
}

function upsertExtras(html, block) {
  if (html.includes('<!-- TOWN_PAGE_EXTRAS_START -->')) {
    return html.replace(/<!-- TOWN_PAGE_EXTRAS_START -->[\s\S]*?<!-- TOWN_PAGE_EXTRAS_END -->\n?/, block);
  }
  const hero = html.search(/<section class="hero"/);
  if (hero < 0) return html;
  const close = html.indexOf('</section>', hero);
  if (close < 0) return html;
  const at = close + '</section>'.length;
  return html.slice(0, at) + '\n' + block + html.slice(at);
}

function ensureHubLink(html, townSlug, town) {
  const href = '/recent-work/areas/' + townSlug + '.html';
  if (!exists('recent-work/areas/' + townSlug + '.html')) return html;
  const needle = '<p class="rw-all"><a href="/recent-work/">See all recent work →</a></p>';
  if (!html.includes(needle)) return html;
  return html.replace(
    needle,
    '<p class="rw-all"><a href="' + href + '">Recent work in ' + esc(town) + '</a> · <a href="/recent-work/">See all recent work →</a></p>'
  );
}

function applyCss() {
  const files = walkHtml(path.join(ROOT, 'services'), []);
  let n = 0;
  for (const full of files) {
    let html = fs.readFileSync(full, 'utf8');
    if (!html.includes('city-landing') && !html.includes('service-page') && !isTownIndex(html)) continue;
    const next = ensureCss(html);
    if (next !== html) {
      fs.writeFileSync(full, next);
      n++;
    }
  }
  console.log('css linked', n);
}

function applyExtras() {
  const byJob = loadProjects();
  const byReview = loadReviews();
  const dir = path.join(ROOT, 'services');
  let n = 0;
  for (const name of fs.readdirSync(dir)) {
    const index = path.join(dir, name, 'index.html');
    if (!fs.existsSync(index)) continue;
    let html = fs.readFileSync(index, 'utf8');
    if (!isTownIndex(html, name)) continue;
    const town = townNameFrom(html, name);
    const jobs = byJob[name] || [];
    const reviews = (byReview[name] && byReview[name].reviews) || [];
    const outside = html.replace(/<!-- TOWN_PAGE_EXTRAS_START -->[\s\S]*?<!-- TOWN_PAGE_EXTRAS_END -->/, '');
    const hasOutsideGrid = outside.includes('class="recent-work-grid"');
    html = ensureCss(html);
    html = upsertSchema(html, reviews.slice(0, 3).map(function (r) {
      return { name: r.name, text: r.text, date: r.date, city: town };
    }));
    html = upsertExtras(html, extrasHtml(town, jobs, reviews, !hasOutsideGrid));
    if (hasOutsideGrid) {
      const cards = jobCards(jobs, 6);
      if (cards) html = replaceGrid(html, cards);
      html = ensureHubLink(html, name, town);
      html = html.replace(
        /(<section class="recent-jobs-cards"[^>]*>\s*<h2>)[^<]*(<\/h2>)/,
        '$1Recent jobs in ' + esc(town) + '$2'
      );
    }
    fs.writeFileSync(index, html);
    n++;
  }
  console.log('extras on town indexes', n);
}

function hubBlock(which) {
  const shops = {
    ramona: {
      title: 'Ramona shop',
      address: '1077 Main St, Unit B, Ramona, CA 92065',
      map: '1077 Main St, Unit B, Ramona, CA 92065',
      note: 'This is the Ramona shop. The Anza shop is at 57174 CA-371, Anza, CA 92539.'
    },
    anza: {
      title: 'Anza shop',
      address: '57174 CA-371, Anza, CA 92539',
      map: '57174 CA-371, Anza, CA 92539',
      note: 'This is the Anza shop. The Ramona shop is at 1077 Main St, Unit B, Ramona, CA 92065.'
    }
  };
  const ranges = CALCULATOR_RANGES.map(function (row) {
    return '<li><strong>' + row[0] + ':</strong> ' + row[1] + '</li>';
  }).join('\n');
  const cost =
    '<section class="hub-costs" id="published-cost-ranges">\n' +
    '<h2>Typical cost ranges</h2>\n' +
    '<p>These ranges are the ones already published on the <a href="/cost-calculator.html">cost calculator</a>. They are sitewide ballparks, not a quote for this town.</p>\n' +
    '<ul>\n' + ranges + '\n</ul>\n' +
    '<p><a href="/cost-calculator.html">Open the cost calculator</a> or call <a href="' + PHONE_TEL + '">' + PHONE_DISPLAY + '</a>.</p>\n' +
    '</section>\n';
  const placeholders =
    '<!-- WARRANTY: placeholder. Do not publish warranty terms until they are provided. -->\n' +
    '<!-- OFFER: placeholder. Do not publish an offer banner until the offer terms are provided. -->\n';
  let shop;
  if (which === 'murrieta') {
    shop =
      '<section class="hub-shop-card" id="murrieta-shop">\n' +
      '<h2>Murrieta shop <span class="hub-coming-soon">Coming soon</span></h2>\n' +
      '<p>A Murrieta shop is coming soon. There is no Murrieta street address yet.</p>\n' +
      '<p>Murrieta jobs are covered from the Anza shop at 57174 CA-371, Anza, CA 92539. Voice <a href="' + PHONE_TEL + '">' + PHONE_DISPLAY + '</a>. Text <a href="' + TEXT_SMS + '">' + TEXT_DISPLAY + '</a>.</p>\n' +
      '<div class="hub-map">\n' +
      '<iframe title="Map of the Anza shop, which covers Murrieta until a Murrieta shop opens" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://maps.google.com/maps?q=57174%20CA-371%2C%20Anza%2C%20CA%2092539&amp;z=15&amp;output=embed"></iframe>\n' +
      '</div>\n' +
      '<p><a href="/services/anza/">Anza shop page</a> · <a href="/services/murrieta/well-pump-repair.html">Pump repair in Murrieta</a> · <a href="/services/murrieta/well-drilling.html">Well drilling in Murrieta</a> · <a href="/services/murrieta/water-treatment.html">Water treatment in Murrieta</a></p>\n' +
      '</section>\n';
  } else {
    const s = shops[which];
    shop =
      '<section class="hub-shop-card" id="' + which + '-shop-visit">\n' +
      '<h2>' + s.title + '</h2>\n' +
      '<p>' + s.address + '</p>\n' +
      '<p>Voice <a href="' + PHONE_TEL + '">' + PHONE_DISPLAY + '</a>. Text <a href="' + TEXT_SMS + '">' + TEXT_DISPLAY + '</a>. Mon–Sun 7:00 AM–5:00 PM. Emergency 24/7.</p>\n' +
      '<p>' + s.note + '</p>\n' +
      '<div class="hub-map">\n' +
      '<iframe title="Map of the ' + s.title + '" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://maps.google.com/maps?q=' + encodeURIComponent(s.map) + '&amp;z=15&amp;output=embed"></iframe>\n' +
      '</div>\n' +
      '</section>\n';
  }
  const faqTown = which === 'ramona' ? 'Ramona' : which === 'anza' ? 'Anza' : 'Murrieta';
  const faq =
    '<section class="hub-faq" id="hub-faq">\n' +
    '<h2>Questions about the ' + faqTown + ' shop</h2>\n' +
    '<details open><summary>Which phone number is the voice line?</summary><p>Call <a href="' + PHONE_TEL + '">' + PHONE_DISPLAY + '</a>. Text <a href="' + TEXT_SMS + '">' + TEXT_DISPLAY + '</a> is text-only. CSLB #1086994 (C-57).</p></details>\n' +
    '<details><summary>Where do the published price ranges come from?</summary><p>The ranges in the cost section are copied from the cost calculator already on this site. Pump-replacement figures already on the Ramona and Anza pages, where present, are invoice ranges and stay on those pages.</p></details>\n' +
    '<details><summary>How do I book?</summary><p><a href="/contact.html">Book online</a> opens the estimate form. Call <a href="' + PHONE_TEL + '">' + PHONE_DISPLAY + '</a> if you would rather talk to the shop.</p></details>\n' +
    '</section>\n';
  return '<!-- HUB_DEPTH_START -->\n<section class="hub-depth" id="hub-depth">\n' + shop + cost + faq + placeholders + '</section>\n<!-- HUB_DEPTH_END -->\n';
}

function applyHubs() {
  for (const which of ['ramona', 'anza', 'murrieta']) {
    const rel = 'services/' + which + '/index.html';
    let html = read(rel);
    const block = hubBlock(which);
    if (html.includes('<!-- HUB_DEPTH_START -->')) {
      html = html.replace(/<!-- HUB_DEPTH_START -->[\s\S]*?<!-- HUB_DEPTH_END -->\n?/, block);
    } else if (html.includes('<!-- TOWN_PAGE_EXTRAS_END -->')) {
      html = html.replace('<!-- TOWN_PAGE_EXTRAS_END -->', '<!-- TOWN_PAGE_EXTRAS_END -->\n' + block);
    } else {
      html = html.replace('</main>', block + '</main>');
    }
    html = ensureCss(html);
    write(rel, html);
    console.log('hub', which);
  }
}

function curatedFromPages() {
  const html = read('pages/reviews.html');
  const out = [];
  const re = /<div class="reviewer">([^<]*)<\/div>\s*<div class="review-meta">([^<]*)<\/div>\s*<p class="review-text">([\s\S]*?)<\/p>/g;
  let m;
  while ((m = re.exec(html))) {
    const text = m[3].replace(/<[^>]+>/g, '').replace(/[“”]/g, '"').replace(/&amp;/g, '&').replace(/&#39;/g, "'").trim();
    const name = m[1].trim();
    if (!text || looksLikePii(text)) continue;
    out.push({ name: name, city: m[2].trim(), text: text, date: '' });
  }
  return out;
}

function allPublicReviews() {
  const by = loadReviews();
  const list = [];
  for (const key of Object.keys(by)) {
    for (const r of by[key].reviews) {
      list.push({ name: r.name, city: by[key].city, text: r.text, date: r.date || '' });
    }
  }
  const seen = {};
  for (const r of list) seen[r.text.slice(0, 80).toLowerCase()] = true;
  for (const r of curatedFromPages()) {
    const key = r.text.slice(0, 80).toLowerCase();
    const dup = Object.keys(seen).some(function (k) { return k.indexOf(key.slice(0, 40)) !== -1 || key.indexOf(k.slice(0, 40)) !== -1; });
    if (!dup) list.push(r);
  }
  return list;
}

function reviewsPage(list) {
  const cards = reviewCards(list, '');
  const schema = ratingSchema(list.map(function (r) {
    return { name: r.name, text: r.text, date: r.date, city: r.city };
  }));
  return '<!DOCTYPE html>\n<html lang="en">\n<head>\n' +
    '<script src="/js/ga4-filter.js"></script>\n' +
    '<script src="/js/cookie-consent.js"></script>\n' +
    '<script async src="https://www.googletagmanager.com/gtag/js?id=G-5LL1YRWT5T"></script>\n' +
    '<script src="/js/scws-tracking.js"></script>\n' +
    '<script src="/js/call-tracking.js"></script>\n' +
    '<meta charset="utf-8"/>\n' +
    '<meta name="viewport" content="width=device-width, initial-scale=1.0"/>\n' +
    '<title>Customer Reviews | Southern California Well Service</title>\n' +
    '<meta name="description" content="Southern California Well Service is about 4.8 from 175 Google reviews. Ramona is 4.7 from 62. Anza is 4.8 from 113. Call (760) 440-8520."/>\n' +
    '<link rel="canonical" href="https://scwellservice.com/reviews/"/>\n' +
    '<meta property="og:title" content="Customer Reviews | Southern California Well Service"/>\n' +
    '<meta property="og:description" content="About 4.8 from 175 Google reviews. Ramona 4.7 from 62. Anza 4.8 from 113."/>\n' +
    '<meta property="og:image" content="https://www.scwellservice.com/images/logo-text-only-3x.png"/>\n' +
    '<link rel="stylesheet" href="/css/shop-chrome.css"/>\n' +
    '<link rel="stylesheet" href="/css/city-pages.css"/>\n' +
    '<!-- Combined Google rating: Ramona 4.7/62 and Anza 4.8/113, 175 reviews, about 4.8. -->\n' +
    '<script type="application/ld+json" id="town-aggregate-rating">\n' + schema + '\n</script>\n' +
    '</head>\n<body class="shop-page">\n' +
    '<div id="scws-emergency-cta"><span>🚨 No Water?</span> <a href="' + PHONE_TEL + '">Call Now →</a></div>\n' +
    '<header class="shop-header"><div class="shop-header-inner">\n' +
    '<a href="/"><img width="840" height="150" class="site-logo-img" src="/images/logo-text-only-3x.png" alt="Southern California Well Service"></a>\n' +
    '<nav class="shop-desktop-nav"><a href="/">Home</a><a href="/recent-work/">Recent Work</a><a href="/reviews/">Reviews</a><a href="/contact.html">Contact</a><a href="/pages/about.html">About</a></nav>\n' +
    '<div style="display:flex;align-items:center;gap:8px;">\n' +
    '<button type="button" id="mobile-menu-btn" class="shop-menu-btn" aria-label="Open menu">☰</button>\n' +
    '<a class="site-phone-cta" href="' + PHONE_TEL + '" style="background:#dc2626;color:#fff;border-radius:8px;padding:0.5rem 0.85rem;text-decoration:none;font-weight:700;">' + PHONE_DISPLAY + '</a>\n' +
    '</div></div>\n' +
    '<div id="mobile-menu" class="shop-mobile-nav" hidden style="padding:0.75rem 1rem;">\n' +
    '<a href="/">Home</a><a href="/recent-work/">Recent Work</a><a href="/reviews/">Reviews</a><a href="/contact.html">Contact</a><a href="/pages/about.html">About</a>\n' +
    '</div></header>\n' +
    '<script>document.getElementById("mobile-menu-btn").addEventListener("click",function(){var m=document.getElementById("mobile-menu");m.hidden=!m.hidden;});</script>\n' +
    '<main class="city-landing">\n' +
    '<section class="hero">\n<h1>Customer Reviews</h1>\n' +
    '<p>About <strong>' + RATING + '</strong> from ' + REVIEW_COUNT_LABEL + ' Google reviews across our Ramona and Anza shops. Ramona is 4.7 from 62. Anza is 4.8 from 113.</p>\n' +
    '<a class="cta-button" href="' + PHONE_TEL + '">Call ' + PHONE_DISPLAY + '</a>\n' +
    '<a id="scws-book-online" class="scws-book-online" href="/contact.html">Book online</a>\n' +
    '</section>\n' +
    '<section class="town-extras">\n' +
    '<div class="town-rating">\n' +
    '<p class="town-stars" aria-hidden="true">★★★★★</p>\n' +
    '<p>Ramona is 4.7 from 62 Google reviews. Anza is 4.8 from 113. Together that is 175 reviews, about 4.8.</p>\n' +
    '<p><a href="' + RAMONA_GBP + '" target="_blank" rel="noopener">Ramona Google reviews</a> · <a href="' + ANZA_GBP + '" target="_blank" rel="noopener">Anza Google reviews</a></p>\n' +
    '<p>Voice <a href="' + PHONE_TEL + '">' + PHONE_DISPLAY + '</a> · Text <a href="' + TEXT_SMS + '">' + TEXT_DISPLAY + '</a></p>\n' +
    '</div>\n' +
    '<h2>What customers have written</h2>\n' +
    '<div class="reviews-list">\n' + cards + '\n</div>\n' +
    '<div class="town-reviews">\n' +
    '<h2>Shops</h2>\n' +
    '<p><strong>Ramona:</strong> 1077 Main St, Unit B, Ramona, CA 92065</p>\n' +
    '<p><strong>Anza:</strong> 57174 CA-371, Anza, CA 92539</p>\n' +
    '<p>CSLB #1086994 (C-57).</p>\n' +
    '</div>\n</section>\n</main>\n' +
    '<footer class="shop-footer-nap" style="background:#0f172a;color:#94a3b8;padding:2rem 1rem;">\n' +
    '<p>Voice <a href="' + PHONE_TEL + '">' + PHONE_DISPLAY + '</a> · Text <a href="' + TEXT_SMS + '">' + TEXT_DISPLAY + '</a></p>\n' +
    '<p>1077 Main St, Unit B, Ramona, CA 92065 · 57174 CA-371, Anza, CA 92539</p>\n' +
    '<p><a href="/">Home</a> · <a href="/pages/service-area.html">Service areas</a> · <a href="/contact.html">Contact</a></p>\n' +
    '</footer>\n' +
    '<div id="sticky-cta"><a class="cta-call" href="' + PHONE_TEL + '">Call</a><a class="cta-text" href="' + TEXT_SMS + '">Text</a><a class="cta-est" href="/contact.html">Estimate</a></div>\n' +
    '<script src="/js/gbp-ratings.js?v=7" defer></script>\n' +
    '</body>\n</html>\n';
}

function applyReviewsPage() {
  const list = allPublicReviews();
  fs.mkdirSync(path.join(ROOT, 'reviews'), { recursive: true });
  write('reviews/index.html', reviewsPage(list));
  console.log('reviews page', list.length);

  let home = read('index.html');
  if (!home.includes('href="/reviews/"') && !home.includes("href='/reviews/'")) {
    home = home.replace(
      '<a href="faq.html" class="text-white hover:text-accent transition whitespace-nowrap">FAQ</a>',
      '<a href="faq.html" class="text-white hover:text-accent transition whitespace-nowrap">FAQ</a>\n                    <a href="/reviews/" class="text-white hover:text-accent transition whitespace-nowrap">Reviews</a>'
    );
    home = home.replace(
      '<a href="faq.html" class="hover:text-accent transition py-2">FAQ</a>',
      '<a href="faq.html" class="hover:text-accent transition py-2">FAQ</a>\n                <a href="/reviews/" class="hover:text-accent transition py-2">Reviews</a>'
    );
    home = home.replace(
      '<li><a href="#contact" class="hover:text-white">Get Estimate →</a></li>',
      '<li><a href="#contact" class="hover:text-white">Get Estimate →</a></li>\n                        <li><a href="/reviews/" class="hover:text-white">Reviews</a></li>'
    );
    write('index.html', home);
  }
  let sm = read('sitemap-pages.xml');
  const loc = 'https://scwellservice.com/reviews/';
  if (!sm.includes(loc)) {
    sm = sm.replace('</urlset>', '  <url><loc>' + loc + '</loc><lastmod>2026-10-21</lastmod><priority>0.6</priority></url>\n</urlset>');
    write('sitemap-pages.xml', sm);
    console.log('sitemap pages grew');
  }
}

function applyBook() {
  const files = []
    .concat(walkHtml(path.join(ROOT, 'services'), []))
    .concat(walkHtml(path.join(ROOT, 'pages', 'services'), []));
  let n = 0;
  for (const full of files) {
    let html = fs.readFileSync(full, 'utf8');
    const next = ensureBookScript(ensureCss(html.includes('city-landing') || html.includes('service-page') || isTownIndex(html) ? html : html));
    const withBook = ensureBookScript(html);
    if (withBook !== html) {
      fs.writeFileSync(full, withBook);
      n++;
    }
  }
  console.log('book script linked', n);
}

const NEW_TOWNS = [
  { slug: 'dulzura', name: 'Dulzura', county: 'San Diego County' },
  { slug: 'palomar-mountain', name: 'Palomar Mountain', county: 'San Diego County' },
  { slug: 'potrero', name: 'Potrero', county: 'San Diego County' },
  { slug: 'pala', name: 'Pala', county: 'San Diego County' },
  { slug: 'thousand-palms', name: 'Thousand Palms', county: 'Riverside County' },
  { slug: 'norco', name: 'Norco', county: 'Riverside County' },
  { slug: 'big-bear-city', name: 'Big Bear City', county: 'San Bernardino County' },
  { slug: 'ocotillo', name: 'Ocotillo', county: 'Imperial County' }
];

const LOCAL_LEADS = {
  pala: 'Pala sits in the Peninsular Ranges of northern San Diego County, where private wells draw from decomposed granite and fractured crystalline bedrock. Completion reports for 155 wells in Pala put the average depth at 390 feet and the median at 271 feet, from 20 feet to 2,774 feet.',
  dulzura: 'Dulzura\'s ground mixes granite, metavolcanic rock, decomposed granite, and ribbons of alluvium along creeks such as Dulzura Creek, so well depth varies widely. Completion reports for 101 wells put the average at 513 feet and the median at 470 feet, from 52 feet to 1,300 feet.',
  potrero: 'Potrero is north of the Tecate border crossing, in the fractured granitic bedrock of the Peninsular Ranges. Completion reports for 105 wells put the average depth at 511 feet and the median at 480 feet, with the deepest at 1,160 feet.',
  'palomar-mountain': 'Almost every home on Palomar Mountain depends on a private well drilled into granite. Completion reports for 119 wells there put the average depth at 386 feet and the median at 365 feet, with the deepest at 1,055 feet.',
  'thousand-palms': 'Thousand Palms is in the Coachella Valley of Riverside County, between Palm Desert and Indio. Groundwater here is stored in alluvial sand and gravel washed out of the surrounding mountains, not in the fractured granite of the mountain backcountry.',
  norco: 'Norco sits in the Santa Ana River valley in western Riverside County. Much of the valley floor is sand and gravel alluvium, and wells finished in that material draw water through the spaces between grains rather than through cracks in rock. Completion reports for 264 wells in Norco put the average depth at 87 feet and the median at 50 feet.',
  'big-bear-city': 'Big Bear City wells tap Bear Valley groundwater that lives largely in fractures in hard granite, fed by snowmelt and rain. Completion reports for 160 wells put both the average and the median at 200 feet, from 18 feet to 810 feet.',
  ocotillo: 'Ocotillo is in Imperial County, in the desert along Interstate 8 west of El Centro, between the Jacumba Mountains and the Yuha Desert. Wells here are finished in desert basin fill or in rock where the mountains meet the basin.'
};

function localTownLead(meta, jobs, span, mix) {
  const local = LOCAL_LEADS[meta.slug] || (meta.name + ' is in ' + meta.county + '.');
  return local + ' From ' + span + ' we finished ' + jobs.length + ' jobs (' + mix + '). Call ' + PHONE_DISPLAY + '. CSLB #1086994. Shops are in Ramona (1077 Main St, Unit B, Ramona, CA 92065) and Anza (57174 CA-371, Anza, CA 92539).';
}

function newTownPage(meta, jobs, reviews) {
  const cards = jobCards(jobs, 6);
  const titles = [];
  const seen = {};
  for (const job of jobs) {
    if (!seen[job.title]) { seen[job.title] = 0; titles.push(job.title); }
    seen[job.title]++;
  }
  const mix = titles.map(function (t) { return seen[t] + ' × ' + t; }).join('; ');
  const dates = jobs.map(function (j) { return j.date; }).filter(Boolean).sort();
  const span = dates.length ? dates[0] + ' through ' + dates[dates.length - 1] : 'the dates on the job cards';
  const rich = jobs.filter(function (j) {
    return j.summary && j.summary.length > 50 && !/^Well service completed/i.test(j.summary);
  }).slice(0, 3);
  const richHtml = rich.map(function (j) {
    return '<li><strong>' + esc(j.title) + '</strong> (' + esc(j.dateLabel || j.date) + '): ' + esc(j.summary) + '</li>';
  }).join('\n');
  const reviewBlock = reviews.length
    ? '<div class="reviews-list">\n' + reviewCards(reviews.slice(0, 3).map(function (r) { return { name: r.name, text: r.text, date: r.date, city: meta.name }; }), meta.name) + '\n</div>\n'
    : '<p>No ' + esc(meta.name) + ' review text is in the site archive. The rating above is the combined Ramona and Anza Google figure.</p>\n';
  const schemaReviews = reviews.slice(0, 3).map(function (r) {
    return { name: r.name, text: r.text, date: r.date, city: meta.name };
  });
  const serviceSchema = {
    '@context': 'https://schema.org',
    '@type': 'Service',
    name: 'Well service in ' + meta.name,
    serviceType: 'Water well service',
    url: 'https://scwellservice.com/services/' + meta.slug + '/',
    areaServed: { '@type': 'City', name: meta.name, containedInPlace: { '@type': 'State', name: 'California' } },
    provider: {
      '@type': 'LocalBusiness',
      name: 'Southern California Well Service',
      telephone: PHONE_DISPLAY,
      url: 'https://scwellservice.com/'
    }
  };
  return '<!DOCTYPE html>\n<html lang="en">\n<head>\n' +
    '<script src="/js/ga4-filter.js"></script>\n<script src="/js/cookie-consent.js"></script>\n' +
    '<script async src="https://www.googletagmanager.com/gtag/js?id=G-5LL1YRWT5T"></script>\n' +
    '<script src="/js/scws-tracking.js"></script>\n<script src="/js/call-tracking.js"></script>\n' +
    '<meta charset="utf-8"/>\n<meta name="viewport" content="width=device-width, initial-scale=1.0"/>\n' +
    '<title>' + esc(meta.name) + ' Well Service | Pump Repair &amp; Drilling | SCWS</title>\n' +
    '<meta name="description" content="' + esc(meta.name) + ', ' + esc(meta.county) + ': ' + jobs.length + ' photographed SCWS jobs from ' + esc(span) + '. Call (760) 440-8520. CSLB #1086994."/>\n' +
    '<link rel="canonical" href="https://scwellservice.com/services/' + meta.slug + '/"/>\n' +
    '<meta property="og:title" content="' + esc(meta.name) + ' Well Service | SCWS"/>\n' +
    '<meta property="og:description" content="' + jobs.length + ' photographed jobs in ' + esc(meta.name) + '. Call (760) 440-8520."/>\n' +
    '<meta property="og:image" content="https://www.scwellservice.com/images/logo-text-only-3x.png"/>\n' +
    '<link rel="stylesheet" href="/css/shop-chrome.css"/>\n<link rel="stylesheet" href="/css/city-pages.css"/>\n' +
    '<script type="application/ld+json">\n' + JSON.stringify(serviceSchema, null, 2).replace(/</g, '\\u003c') + '\n</script>\n' +
    '</head>\n<body class="shop-page" style="padding-bottom:80px">\n' +
    '<div class="bg-gradient-to-r from-red-600 to-red-700 text-white py-2.5" style="background:linear-gradient(90deg,#dc2626,#b91c1c);color:#fff;text-align:center;padding:0.6rem 1rem;">\n' +
    '<span style="font-weight:700;">🚨 No Water?</span> <a href="' + PHONE_TEL + '" style="color:#fff;font-weight:700;">Call Now →</a></div>\n' +
    '<header class="shop-header"><div class="shop-header-inner">\n' +
    '<a href="/"><img width="840" height="150" class="site-logo-img" src="/images/logo-text-only-3x.png" alt="Southern California Well Service"></a>\n' +
    '<nav class="shop-desktop-nav"><a href="/pages/services/well-drilling.html">Services</a><a href="/recent-work/">Recent Work</a><a href="/reviews/">Reviews</a><a href="/contact.html">Contact</a></nav>\n' +
    '<div style="display:flex;align-items:center;gap:8px;">\n' +
    '<button type="button" id="mobile-menu-btn" class="shop-menu-btn" aria-label="Open menu">☰</button>\n' +
    '<a class="site-phone-cta" href="' + PHONE_TEL + '" style="background:#dc2626;color:#fff;border-radius:8px;padding:0.5rem 0.85rem;text-decoration:none;font-weight:700;">' + PHONE_DISPLAY + '</a>\n' +
    '</div></div>\n<div id="mobile-menu" class="shop-mobile-nav" hidden style="padding:0.75rem 1rem;">\n' +
    '<a href="/pages/services/well-drilling.html">Services</a><a href="/recent-work/">Recent Work</a><a href="/reviews/">Reviews</a><a href="/contact.html">Contact</a>\n' +
    '</div></header>\n' +
    '<script>document.getElementById("mobile-menu-btn").addEventListener("click",function(){var m=document.getElementById("mobile-menu");m.hidden=!m.hidden;});</script>\n' +
    '<main class="city-landing">\n<section class="hero">\n' +
    '<h1>Well Services in ' + esc(meta.name) + ', CA</h1>\n' +
    '<p>' + jobs.length + ' photographed jobs in ' + esc(meta.name) + ', ' + esc(meta.county) + ', from ' + esc(span) + '.</p>\n' +
    '<a class="cta-button" href="' + PHONE_TEL + '">Call ' + PHONE_DISPLAY + '</a>\n' +
    '<a id="scws-book-online" class="scws-book-online" href="https://clienthub.getjobber.com/hubs/7c569177-85d0-4bac-9c7f-e2afe6652ee1/public/requests/1604593/new" target="_blank" rel="noopener">Book online</a>\n' +
    '</section>\n<section class="city-overview">\n' +
    '<h2>Well service in ' + esc(meta.name) + '</h2>\n' +
    '<p>' + esc(localTownLead(meta, jobs, span, mix)) + '</p>\n' +
    (richHtml ? '<h3>Job notes from the field</h3>\n<ul>\n' + richHtml + '\n</ul>\n' : '<p>The cards below are those visits.</p>\n') +
    '<h3>Services</h3>\n<ul class="service-links">\n' +
    '<li><a href="/pages/services/well-drilling.html">Well drilling</a></li>\n' +
    '<li><a href="/pages/services/pump-repair.html">Pump repair</a></li>\n' +
    '<li><a href="/pages/services/water-testing.html">Water testing</a></li>\n' +
    '<li><a href="/pages/services/emergency-well-service.html">Emergency service</a></li>\n' +
    '<li><a href="/pages/services/maintenance.html">Maintenance</a></li>\n' +
    '<li><a href="/recent-work/areas/' + meta.slug + '.html">All ' + esc(meta.name) + ' jobs</a></li>\n' +
    '<li><a href="/reviews/">Reviews</a></li>\n' +
    '</ul>\n</section>\n' +
    '<section class="recent-jobs-cards" id="recent-jobs">\n<h2>Recent jobs in ' + esc(meta.name) + '</h2>\n' +
    '<p class="rw-lede">Latest ' + Math.min(6, jobs.length) + ' of ' + jobs.length + ' photographed jobs.</p>\n' +
    '<div class="recent-work-grid">\n' + cards + '\n</div>\n' +
    '<p class="rw-all"><a href="/recent-work/areas/' + meta.slug + '.html">Recent work in ' + esc(meta.name) + '</a> · <a href="/recent-work/">All recent work</a></p>\n' +
    '</section>\n' +
    '<section class="town-extras">\n<div class="town-rating">\n' +
    '<p class="town-stars" aria-hidden="true">★★★★★</p>\n' +
    '<p>About <strong>' + RATING + '</strong> from ' + REVIEW_COUNT_LABEL + ' Google reviews across our Ramona and Anza shops. Ramona is 4.7 from 62. Anza is 4.8 from 113.</p>\n' +
    '<p><a href="/reviews/">Read our Google reviews</a></p>\n' +
    '</div>\n<div class="town-reviews"><h2>Reviews</h2>\n' + reviewBlock +
    '<p><a href="' + RAMONA_GBP + '" target="_blank" rel="noopener">Ramona Google reviews</a> · <a href="' + ANZA_GBP + '" target="_blank" rel="noopener">Anza Google reviews</a></p>\n' +
    '</div></section>\n' +
    '<div class="contact-cta"><h2>Call SCWS for ' + esc(meta.name) + '</h2>\n' +
    '<p class="phone-large"><a href="' + PHONE_TEL + '">' + PHONE_DISPLAY + '</a></p>\n' +
    '<p><a id="scws-book-online-cta" class="scws-book-online" href="https://clienthub.getjobber.com/hubs/7c569177-85d0-4bac-9c7f-e2afe6652ee1/public/requests/1604593/new" target="_blank" rel="noopener">Book online</a></p>\n' +
    '<p>Licensed C-57 · CSLB #1086994</p></div>\n' +
    '</main>\n' +
    '<footer class="shop-footer-nap" style="background:#0f172a;color:#94a3b8;padding:2rem 1rem;">\n' +
    '<p>Voice <a href="' + PHONE_TEL + '">' + PHONE_DISPLAY + '</a> · Text <a href="' + TEXT_SMS + '">' + TEXT_DISPLAY + '</a></p>\n' +
    '<p>1077 Main St, Unit B, Ramona, CA 92065 · 57174 CA-371, Anza, CA 92539</p>\n' +
    '<p><a href="/pages/service-area.html">Service areas</a> · <a href="/reviews/">Reviews</a></p>\n' +
    '</footer>\n' +
    '<div id="sticky-cta"><a class="cta-call" href="' + PHONE_TEL + '">Call</a><a class="cta-text" href="' + TEXT_SMS + '">Text</a><a class="cta-est" href="/contact.html">Estimate</a></div>\n' +
    '<script src="/js/book-online.js" defer></script>\n</body>\n</html>\n';
}

function applyTowns() {
  const byJob = loadProjects();
  const byReview = loadReviews();
  const created = [];
  for (const meta of NEW_TOWNS) {
    if (exists('services/' + meta.slug + '/index.html')) {
      console.log('skip existing', meta.slug);
      continue;
    }
    const jobs = (byJob[meta.slug] || []).filter(function (j) {
      return j.slug && exists('recent-work/' + j.slug + '.html');
    });
    if (jobs.length < 5) {
      console.log('skip thin', meta.slug, jobs.length);
      continue;
    }
    if (!exists('recent-work/areas/' + meta.slug + '.html')) {
      console.log('skip no area hub', meta.slug);
      continue;
    }
    const reviews = (byReview[meta.slug] && byReview[meta.slug].reviews) || [];
    fs.mkdirSync(path.join(ROOT, 'services', meta.slug), { recursive: true });
    write('services/' + meta.slug + '/index.html', newTownPage(meta, jobs, reviews));
    created.push(meta);
    console.log('created', meta.slug, jobs.length);
  }
  if (!created.length) return;
  let area = read('pages/service-area.html');
  const inserts = {
    dulzura: '<span class="city-tag"><a href="/services/santa-ysabel/">Santa Ysabel</a></span>',
    'palomar-mountain': null,
    potrero: '<span class="city-tag"><a href="/blog/well-service-potrero.html">Potrero</a></span>',
    pala: null,
    'thousand-palms': '<span class="city-tag"><a href="/services/perris/">Perris</a></span>',
    norco: null,
    'big-bear-city': '<span class="city-tag"><a href="/services/wrightwood/">Wrightwood</a></span>',
    ocotillo: null
  };
  function tag(meta) {
    return '<span class="city-tag"><a href="/services/' + meta.slug + '/">' + meta.name + '</a></span>';
  }
  for (const meta of created) {
    const href = '/services/' + meta.slug + '/';
    if (area.includes(href)) continue;
    if (meta.slug === 'potrero') {
      area = area.replace(inserts.potrero, inserts.potrero + '\n' + tag(meta));
    } else if (meta.county === 'San Diego County') {
      area = area.replace(inserts.dulzura, inserts.dulzura + '\n' + tag(meta));
    } else if (meta.county === 'Riverside County') {
      area = area.replace(inserts['thousand-palms'], inserts['thousand-palms'] + '\n' + tag(meta));
    } else if (meta.county === 'San Bernardino County') {
      area = area.replace(inserts['big-bear-city'], inserts['big-bear-city'] + '\n' + tag(meta));
    }
  }
  if (created.some(function (m) { return m.slug === 'ocotillo'; }) && !area.includes('/services/ocotillo/')) {
    area = area.replace(
      '<div class="not-listed">',
      '<div class="county">\n<h3>Imperial County</h3>\n<div class="city-list">\n<span class="city-tag"><a href="/services/ocotillo/">Ocotillo</a></span>\n</div>\n</div>\n<div class="not-listed">'
    );
  }
  write('pages/service-area.html', area);
  let sm = read('sitemap-services.xml');
  let added = 0;
  for (const meta of created) {
    const loc = 'https://scwellservice.com/services/' + meta.slug + '/';
    if (sm.includes(loc)) continue;
    sm = sm.replace('</urlset>', '  <url><loc>' + loc + '</loc><lastmod>2026-10-21</lastmod><priority>0.7</priority></url>\n</urlset>');
    added++;
  }
  write('sitemap-services.xml', sm);
  console.log('sitemap service urls added', added);
}

const modes = {
  css: applyCss,
  extras: applyExtras,
  hubs: applyHubs,
  reviews: applyReviewsPage,
  book: applyBook,
  towns: applyTowns
};

if (MODE === 'all') {
  applyCss();
  applyExtras();
  applyHubs();
  applyReviewsPage();
  applyBook();
  applyTowns();
} else if (!modes[MODE]) {
  console.error('unknown mode', MODE);
  process.exit(1);
} else {
  modes[MODE]();
}
