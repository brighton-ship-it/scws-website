/**
 * Unit tests for the homepage GBP ratings widget (combined Ramona + Anza).
 * Run: node js/gbp-ratings.test.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var assert = require('assert');
var { JSDOM } = require('jsdom');

var src = fs.readFileSync(path.join(__dirname, 'gbp-ratings.js'), 'utf8');
var indexHtml = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

var ANZA_GBP = 'https://g.page/r/Cajtn6jSo-ONEBM';

function snapshotWidgetInner() {
  return (
    '<a class="gbp-ratings-link" href="' + ANZA_GBP + '" target="_blank" rel="noopener">' +
      '<span class="gbp-stars" aria-hidden="true">★★★★★</span>' +
      '<span class="gbp-ratings-score" data-gbp-heading>4.8</span>' +
      '<span class="gbp-ratings-count">from 170+ Google reviews</span>' +
      '<span class="gbp-ratings-label" data-gbp-shops>across our Ramona and Anza shops</span>' +
    '</a>'
  );
}

function homepageMount() {
  return '<div id="gbp-ratings" class="gbp-ratings-widget">' + snapshotWidgetInner() + '</div>';
}

function assertCombinedSnapshot(html, heading) {
  assert.strictEqual(heading, '4.8');
  assert.match(html, /★★★★★/);
  assert.match(html, /gbp-ratings-score[^>]*>4\.8</);
  assert.match(html, /from 170\+ Google reviews/);
  assert.match(html, /across our Ramona and Anza shops/);
  assert.match(html, /g\.page\/r\/Cajtn6jSo-ONEBM/);
  assert.doesNotMatch(html, /Cajtn6jSo-ONEBM\/review/);
  assert.doesNotMatch(html, /57174\+CA-371/);
  assert.doesNotMatch(html, /maps\/place/);
  assert.doesNotMatch(html, /\(94\)/);
  assert.doesNotMatch(html, /4\.9/);
  assert.doesNotMatch(html, /127/);
  assert.doesNotMatch(html, /g\.page\/r\/CU9X_NG3TvP2EBM/);
}

function loadWidget(fetchImpl) {
  var dom = new JSDOM('<!doctype html><html><body>' + homepageMount() + '</body></html>', {
    runScripts: 'outside-only',
    url: 'https://scwellservice.com/'
  });
  dom.window.fetch = fetchImpl;
  dom.window.eval(src);
  return dom.window;
}

function jsonResponse(body, status) {
  var code = status == null ? 200 : status;
  return Promise.resolve({
    ok: code >= 200 && code < 300,
    status: code,
    json: function () {
      return Promise.resolve(body);
    }
  });
}

function wait(ms) {
  return new Promise(function (resolve) {
    setTimeout(resolve, ms);
  });
}

function mountHtml(win) {
  return win.document.getElementById('gbp-ratings').innerHTML;
}

async function run() {
  assert.doesNotMatch(src, /4\.9/);
  assert.doesNotMatch(src, /127/);
  assert.doesNotMatch(src, /count:\s*94/);
  assert.match(src, /rating:\s*4\.8/);
  assert.match(src, /count:\s*108/);
  assert.match(src, /rating:\s*4\.7/);
  assert.match(src, /count:\s*62/);
  assert.match(src, /170\+/);
  assert.match(src, /2026-10-02/);
  assert.match(src, /scws-jobs\.vercel\.app\/api\/gbp-ratings/);
  assert.match(src, /g\.page\/r\/CU9X_NG3TvP2EBM\/review/);
  assert.match(src, /g\.page\/r\/Cajtn6jSo-ONEBM/);
  assert.doesNotMatch(src, /Cajtn6jSo-ONEBM\/review/);
  assert.doesNotMatch(src, /maps\/place\/57174\+CA-371/);
  assert.doesNotMatch(src, /we don.?t publish a combined star count/i);

  var heritageIdx = indexHtml.indexOf('heritage-banner');
  var gbpIdx = indexHtml.indexOf('id="gbp-ratings"');
  var h1Idx = indexHtml.indexOf("Southern California's Trusted Water Well Experts");
  var whyIdx = indexHtml.indexOf('Why Southern California Well Service?');
  assert.ok(gbpIdx > -1 && h1Idx > gbpIdx && gbpIdx < heritageIdx, 'widget must sit in the hero kicker above H1');
  assert.ok(heritageIdx > -1 && heritageIdx < whyIdx, 'Heritage banner stays above Why SCWS');
  assert.doesNotMatch(indexHtml, /gbp-ratings-banner/);
  assert.strictEqual(indexHtml.indexOf('id="gbp-ratings"', gbpIdx + 1), -1, 'only one gbp-ratings mount');
  assert.match(indexHtml, /js\/gbp-ratings\.js\?v=/);

  var widgetBlock = indexHtml.slice(gbpIdx, h1Idx);
  var trustIdx = indexHtml.indexOf('aria-label="Trust stats and badges"');
  assert.ok(trustIdx > heritageIdx && trustIdx < whyIdx, 'trust row sits under Heritage, above Why SCWS');
  var trustBlock = indexHtml.slice(trustIdx, whyIdx);
  assert.match(trustBlock, /60\+/);
  assert.match(trustBlock, /Years Family Heritage/);
  assert.match(trustBlock, /16,000\+/);
  assert.match(trustBlock, /Customers Served/);
  assert.match(trustBlock, /text-3xl font-bold text-primary">4\.8★</);
  assert.match(trustBlock, /170\+ Google reviews/);
  assert.match(trustBlock, /24\/7/);
  assert.match(trustBlock, /Emergency Service/);
  assert.match(trustBlock, /Licensed &amp; Insured/);
  assert.match(trustBlock, /Satisfaction Guaranteed/);
  assert.match(trustBlock, /Free Estimates/);
  assert.match(trustBlock, /Same-Day Service/);
  assert.match(trustBlock, /NGWA Member/);
  assert.doesNotMatch(trustBlock, />4\.9★</);
  assert.doesNotMatch(trustBlock, />127</);
  assert.doesNotMatch(trustBlock, /id="gbp-ratings"/);
  assert.doesNotMatch(trustBlock, /drilling since 1966/i);
  assert.doesNotMatch(trustBlock, /founded 1966/i);
  assert.doesNotMatch(trustBlock, /over 30 years/i);
  assertCombinedSnapshot(widgetBlock, '4.8');
  assert.doesNotMatch(indexHtml, /reviewCount["']:\s*["']?127/);
  assert.doesNotMatch(indexHtml, /Read us on Google/);
  assert.doesNotMatch(indexHtml, /do not publish a combined rating/i);
  assert.doesNotMatch(indexHtml, /\(94\)/);
  assert.match(indexHtml, /4\.8 ★ from 170\+ Google reviews across our Ramona and Anza shops\./);

  var whyEnd = indexHtml.indexOf('<!-- Services Section -->');
  var whyBlock = indexHtml.slice(whyIdx, whyEnd > whyIdx ? whyEnd : indexHtml.length);
  assert.doesNotMatch(whyBlock, /id="gbp-ratings"/);
  assert.doesNotMatch(whyBlock, /data-gbp-heading/);
  assert.match(whyBlock, /<h3 class="font-bold text-primary text-lg">Google reviews<\/h3>/);
  assert.match(whyBlock, /Fast response, quality work, fair prices — that's what customers say\./);
  assert.match(whyBlock, /Read reviews on Google/);
  assert.doesNotMatch(whyBlock, /Read Anza reviews on Google/);
  assert.match(whyBlock, /g\.page\/r\/Cajtn6jSo-ONEBM/);
  assert.doesNotMatch(whyBlock, /Cajtn6jSo-ONEBM\/review/);
  assert.doesNotMatch(whyBlock, /57174\+CA-371/);
  assert.doesNotMatch(whyBlock, /maps\/place/);
  assert.doesNotMatch(whyBlock, /g\.page\/r\/CU9X_NG3TvP2EBM/);
  assert.doesNotMatch(whyBlock, /4\.9/);
  assert.doesNotMatch(whyBlock, /127/);
  var whyLink = whyBlock.match(/<a href="https:\/\/g\.page\/r\/Cajtn6jSo-ONEBM"[^>]*>Read reviews on Google<\/a>/);
  assert.ok(whyLink, 'Why SCWS reviews link must use Anza GBP href and no shop name');
  assert.doesNotMatch(whyLink[0], /Anza/);
  assert.doesNotMatch(whyLink[0], /Ramona/);

  var liveWin = loadWidget(function () {
    return jsonResponse({
      ramona: { rating: 4.7, count: 62, url: 'https://example.com/ramona' },
      anza: { rating: 4.8, count: 108 },
      updated: '2026-10-02T15:00:00Z'
    });
  });
  await wait(20);
  var heading = liveWin.document.querySelector('[data-gbp-heading]').textContent;
  var shops = mountHtml(liveWin);
  assertCombinedSnapshot(shops, heading);
  assert.doesNotMatch(shops, /https:\/\/example.com\/ramona/);

  var failWin = loadWidget(function () {
    return Promise.reject(new Error('network'));
  });
  await wait(20);
  var failHeading = failWin.document.querySelector('[data-gbp-heading]').textContent;
  var failShops = mountHtml(failWin);
  assertCombinedSnapshot(failShops, failHeading);

  var unconfigured = loadWidget(function () {
    return jsonResponse({ error: 'gbp_unconfigured' }, 503);
  });
  await wait(20);
  assertCombinedSnapshot(
    mountHtml(unconfigured),
    unconfigured.document.querySelector('[data-gbp-heading]').textContent
  );

  var unavailable = loadWidget(function () {
    return jsonResponse({ error: 'gbp_unavailable' }, 502);
  });
  await wait(20);
  assertCombinedSnapshot(
    mountHtml(unavailable),
    unavailable.document.querySelector('[data-gbp-heading]').textContent
  );

  var html404 = loadWidget(function () {
    return jsonResponse({ ramona: { rating: 4.7, count: 62 } }, 404);
  });
  await wait(20);
  assertCombinedSnapshot(
    mountHtml(html404),
    html404.document.querySelector('[data-gbp-heading]').textContent
  );

  var staleAnzaOnly = loadWidget(function () {
    return jsonResponse({
      ramona: { rating: 4.7, count: 61, url: 'https://example.com/ramona' },
      anza: { rating: 4.8, count: 94 },
      updated: '2026-08-21T00:00:00Z'
    });
  });
  await wait(20);
  var staleShops = mountHtml(staleAnzaOnly);
  assertCombinedSnapshot(
    staleShops,
    staleAnzaOnly.document.querySelector('[data-gbp-heading]').textContent
  );
  assert.doesNotMatch(staleShops, /\(94\)/);
  assert.doesNotMatch(staleShops, /\b155\b/);
  assert.doesNotMatch(staleShops, /https:\/\/example.com\/ramona/);

  var api = liveWin.scwsGbpRatings;
  assert.notStrictEqual(api.LINKS.ramonaReviews, api.LINKS.anzaListing);
  assert.strictEqual(api.LINKS.anzaListing, ANZA_GBP);
  assert.doesNotMatch(api.LINKS.anzaListing, /CU9X_NG3TvP2EBM/);
  assert.doesNotMatch(api.LINKS.anzaListing, /\/review/);
  assert.doesNotMatch(api.LINKS.anzaListing, /57174/);
  assert.strictEqual(api.COMBINED_SNAPSHOT.rating, 4.8);
  assert.strictEqual(api.COMBINED_SNAPSHOT.countLabel, '170+');
  assert.strictEqual(api.COMBINED_SNAPSHOT.asOf, '2026-10-02');
  assert.strictEqual(api.SHOPS.anza.rating, 4.8);
  assert.strictEqual(api.SHOPS.anza.count, 108);
  assert.strictEqual(api.SHOPS.ramona.rating, 4.7);
  assert.strictEqual(api.SHOPS.ramona.count, 62);

  var partial = api.shopsHtml({
    ramona: { rating: 4.6, count: 10 },
    anza: { rating: 'nope' }
  });
  assertCombinedSnapshot(partial, api.headingText({
    ramona: { rating: 4.6, count: 10 },
    anza: { rating: 'nope' }
  }));
  assert.doesNotMatch(partial, /4\.6/);

  var newer = api.shopsHtml({
    ramona: { rating: 4.7, count: 70 },
    anza: { rating: 4.8, count: 120, url: 'https://example.com/anza' },
    updated: '2026-11-01T00:00:00Z'
  });
  assert.match(newer, /from 190\+ Google reviews/);
  assert.match(newer, /gbp-ratings-score[^>]*>4\.8</);
  assert.match(newer, /g\.page\/r\/Cajtn6jSo-ONEBM/);
  assert.doesNotMatch(newer, /https:\/\/example.com\/anza/);
  assert.doesNotMatch(newer, /\(94\)/);
  assert.strictEqual(api.headingText({
    ramona: { rating: 4.7, count: 70 },
    anza: { rating: 4.8, count: 120, url: 'https://example.com/anza' }
  }), '4.8');

  var fallback = api.fallbackShopsHtml();
  assertCombinedSnapshot(fallback, api.headingText(null));
  assert.doesNotMatch(fallback, /4\.9/);
  assert.doesNotMatch(fallback, /127/);

  assert.strictEqual(api.hasLive({ rating: 4.6, count: 10 }), true);
  assert.strictEqual(api.hasLive({ rating: 4.6 }), false);
  assert.strictEqual(api.hasLive({ count: 10 }), false);
  assert.strictEqual(api.hasLive({ rating: 0, count: 0 }), true);
  assert.strictEqual(api.hasLive({ rating: 5, count: 0 }), true);
  assert.strictEqual(api.hasLive({ rating: -0.1, count: 1 }), false);
  assert.strictEqual(api.hasLive({ rating: 5.1, count: 1 }), false);
  assert.strictEqual(api.headingText({ error: 'gbp_unconfigured' }), '4.8');
  assert.strictEqual(api.headingText(null), '4.8');

  console.log('gbp-ratings tests passed');
}

run().catch(function (err) {
  console.error(err);
  process.exit(1);
});
