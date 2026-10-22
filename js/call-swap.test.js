// Run: node js/call-swap.test.js
const fs = require('fs');
const assert = require('assert');
const { JSDOM } = require('jsdom');
const src = fs.readFileSync(__dirname + '/call-tracking.js', 'utf8');
const html = '<body><a id="a" href="tel:7604408520">(760) 440-8520</a><a id="b" href="tel:+17604408520">Call 760-440-8520</a><a id="s" href="sms:7602195877">Text (760) 219-5877</a><script type="application/ld+json">{"telephone":"+1-760-440-8520"}</script></body>';
function load(url) {
  const dom = new JSDOM(html, { url, runScripts: 'outside-only' });
  dom.window.eval(src);
  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  return dom;
}
let d = load('https://scwellservice.com/x.html?gclid=test');
const doc = d.window.document;
assert.strictEqual(doc.getElementById('a').getAttribute('href'), 'tel:+17603312502');
assert.strictEqual(doc.getElementById('b').getAttribute('href'), 'tel:+17603312502');
assert.strictEqual(doc.getElementById('a').textContent, '(760) 331-2502');
assert.strictEqual(doc.getElementById('b').textContent, 'Call (760) 331-2502');
assert.strictEqual(doc.getElementById('s').getAttribute('href'), 'sms:7602195877');
assert.ok(doc.querySelector('script').textContent.includes('440-8520'));
assert.ok(doc.documentElement.classList.contains('scws-phones-ready'));
d = load('https://scwellservice.com/x.html');
assert.strictEqual(d.window.document.getElementById('a').getAttribute('href'), 'tel:7604408520');
assert.strictEqual(d.window.document.getElementById('a').textContent, '(760) 440-8520');
assert.ok(d.window.document.documentElement.classList.contains('scws-phones-ready'));
d = load('https://scwellservice.com/x.html?utm_source=google&utm_medium=cpc');
assert.strictEqual(d.window.document.getElementById('a').getAttribute('href'), 'tel:+17603312502');
console.log('call-swap tests passed');

// ---- Source-based numbers (SEO / GBP / Yelp / Apple / direct) ----
function loadRef(url, referrer, store) {
  const dom = new JSDOM(html, Object.assign({ url, runScripts: 'outside-only' }, referrer ? { referrer } : {}));
  if (store) for (const [k, v] of Object.entries(store)) dom.window.localStorage.setItem(k, v);
  dom.window.eval(src);
  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  return dom;
}
const num = (dm) => dm.window.document.getElementById('a').getAttribute('href');
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html', 'https://www.google.com/')), 'tel:+17604630493');
assert.strictEqual(loadRef('https://scwellservice.com/x.html', 'https://www.bing.com/').window.document.getElementById('a').textContent, '(760) 463-0493');
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html?utm_source=gbp&utm_medium=organic', '')), 'tel:+17602791262');
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html', 'https://www.google.com/maps/place/x')), 'tel:+17602791262');
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html', 'https://www.yelp.com/biz/scws')), 'tel:7604408520');
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html', 'https://maps.apple.com/place')), 'tel:7604408520');
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html', '')), 'tel:7604408520');
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html', 'https://nextdoor.com/')), 'tel:7604408520');
// Ads click wins over organic referrer
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html?gclid=1', 'https://www.google.com/')), 'tel:+17603312502');
// First touch persists across internal navigation
let dm = loadRef('https://scwellservice.com/a.html', 'https://www.google.com/');
const saved = dm.window.localStorage.getItem('scws_src');
dm = loadRef('https://scwellservice.com/b.html', 'https://scwellservice.com/a.html', { scws_src: saved });
assert.strictEqual(num(dm), 'tel:+17604630493');
// Stored SEO then a later ad click -> ads
dm = loadRef('https://scwellservice.com/b.html?gclid=z', 'https://www.google.com/', { scws_src: saved });
assert.strictEqual(num(dm), 'tel:+17603312502');
// Stored direct then a Yelp visit -> yelp; legacy ads flag still honored
dm = loadRef('https://scwellservice.com/b.html', 'https://www.yelp.com/', { scws_src: JSON.stringify({ source: 'direct', ts: Date.now(), referrer: 'direct', landing: 'x' }) });
assert.strictEqual(dm.window.scwsCallSwap.visitorSource().source, 'yelp');
dm = loadRef('https://scwellservice.com/b.html', '', { scws_ads_visitor: String(Date.now()) });
assert.strictEqual(num(dm), 'tel:+17603312502');
// Form enrichment
dm = loadRef('https://scwellservice.com/contact.html', 'https://maps.apple.com/place');
const body = JSON.parse(dm.window.scwsCallSwap.enrichBody(JSON.stringify({ customer_name: 'x', lead_source: '' })));
assert.strictEqual(body.site_source, 'apple_maps');
assert.strictEqual(body.first_referrer, 'https://maps.apple.com/place');
assert.ok(body.first_landing_page.startsWith('https://scwellservice.com/contact.html'));
assert.strictEqual(dm.window.scwsCallSwap.enrichBody('a=b'), 'a=b');
console.log('source swap tests passed');

// ---- Per-campaign Google Ads numbers ----
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html?gclid=1&utm_source=google&utm_medium=cpc&utm_campaign=weekend-emergency', '')), 'tel:+17608256285');
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html?gclid=1&utm_campaign=drilling&utm_id=23533402261', '')), 'tel:+17608250520');
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html?gclid=1&utm_id=23533402261', '')), 'tel:+17608250520');
assert.strictEqual(num(loadRef('https://scwellservice.com/x.html?gclid=1&utm_campaign=pump-search-1&utm_id=19603168204', '')), 'tel:+17603312502');
let dc = loadRef('https://scwellservice.com/x.html?gclid=1&utm_campaign=drilling', '');
const stored = { scws_src: dc.window.localStorage.getItem('scws_src'), scws_ads_visitor: dc.window.localStorage.getItem('scws_ads_visitor') };
assert.strictEqual(num(loadRef('https://scwellservice.com/y.html', 'https://scwellservice.com/x.html', stored)), 'tel:+17608250520');
assert.strictEqual(num(loadRef('https://scwellservice.com/y.html?gclid=2', '', stored)), 'tel:+17608250520');
assert.strictEqual(dc.window.scwsCallSwap.attributionFields().ads_campaign, 'drilling');
console.log('per-campaign ads tests passed');

// ---- Click source: gclid / gbraid / wbraid and a stored Ads visitor ----
const PHONE_SEND_TO = 'AW-490838730/aFiRCMDlofAbEMq1huoB';
function clickTrack(dm, selector) {
  const events = [];
  dm.window.gtag = function () { events.push(Array.prototype.slice.call(arguments)); };
  dm.window.document.querySelector(selector).dispatchEvent(new dm.window.MouseEvent('click', { bubbles: true }));
  return events;
}
function named(events, name) {
  return events.find((e) => e[0] === 'event' && e[1] === name);
}
function assertAdsCall(dm, label) {
  const events = clickTrack(dm, '#a');
  const call = named(events, 'call_click');
  const conv = named(events, 'conversion');
  assert.ok(call, label + ' call_click');
  assert.strictEqual(call[2].traffic_source, 'google_ads', label);
  assert.strictEqual(call[2].is_organic, false, label);
  assert.ok(conv, label + ' conversion');
  assert.strictEqual(conv[2].send_to, PHONE_SEND_TO, label);
  assert.strictEqual(num(dm), 'tel:+17603312502', label);
}
for (const key of ['gclid', 'gbraid', 'wbraid']) {
  assertAdsCall(loadRef('https://scwellservice.com/blog/x.html?' + key + '=only', ''), key + '-only');
}
let sessionAds = loadRef('https://scwellservice.com/blog/x.html', '');
sessionAds.window.sessionStorage.setItem('scws_utm', JSON.stringify({ gbraid: 'stored-click' }));
let sessionEvents = clickTrack(sessionAds, '#a');
assert.strictEqual(named(sessionEvents, 'call_click')[2].traffic_source, 'google_ads');
assert.strictEqual(named(sessionEvents, 'conversion')[2].send_to, PHONE_SEND_TO);
const adsRec = JSON.stringify({ source: 'google_ads', ts: Date.now(), referrer: 'https://www.google.com/', landing: 'https://scwellservice.com/?gclid=prior' });
assertAdsCall(loadRef('https://scwellservice.com/blog/x.html', '', { scws_src: adsRec }), 'returning-ads');
let legacy = loadRef('https://scwellservice.com/blog/x.html', '', { scws_ads_visitor: String(Date.now()) });
assertAdsCall(legacy, 'legacy-ads-flag');
let adsBeatsUtm = loadRef('https://scwellservice.com/blog/x.html', '', { scws_src: adsRec });
adsBeatsUtm.window.sessionStorage.setItem('scws_utm', JSON.stringify({ utm_source: 'newsletter', utm_medium: 'email' }));
assertAdsCall(adsBeatsUtm, 'stored-ads-beats-utm');
let cpcOnly = loadRef('https://scwellservice.com/x.html', '');
cpcOnly.window.sessionStorage.setItem('scws_utm', JSON.stringify({ utm_source: 'google', utm_medium: 'cpc' }));
assert.strictEqual(named(clickTrack(cpcOnly, '#a'), 'call_click')[2].traffic_source, 'google_ads');
let organic = loadRef('https://scwellservice.com/x.html', 'https://www.google.com/search?q=well+pump');
let organicEvents = clickTrack(organic, '#a');
assert.strictEqual(named(organicEvents, 'call_click')[2].traffic_source, 'google/organic');
assert.strictEqual(named(organicEvents, 'call_click')[2].is_organic, true);
assert.strictEqual(named(organicEvents, 'conversion'), undefined);
assert.strictEqual(num(organic), 'tel:+17604630493');
let direct = loadRef('https://scwellservice.com/x.html', '');
let directEvents = clickTrack(direct, '#a');
assert.strictEqual(named(directEvents, 'call_click')[2].traffic_source, 'direct');
assert.strictEqual(named(directEvents, 'conversion'), undefined);
assert.strictEqual(num(direct), 'tel:7604408520');
let sms = loadRef('https://scwellservice.com/x.html?gclid=only', '');
let smsEvents = clickTrack(sms, '#s');
assert.strictEqual(named(smsEvents, 'text_click')[2].traffic_source, 'google_ads');
assert.strictEqual(named(smsEvents, 'conversion'), undefined);
assert.strictEqual(named(smsEvents, 'call_click'), undefined);
console.log('click source tests passed');
