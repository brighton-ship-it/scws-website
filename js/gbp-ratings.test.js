/**
 * Unit tests for the homepage GBP ratings widget (Anza only).
 * Run: node js/gbp-ratings.test.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var assert = require('assert');
var { JSDOM } = require('jsdom');

var src = fs.readFileSync(path.join(__dirname, 'gbp-ratings.js'), 'utf8');
var indexHtml = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

function homepageMount() {
  return (
    '<div id="gbp-ratings" class="gbp-ratings-widget">' +
      '<a class="gbp-ratings-link" href="https://www.google.com/maps/place/57174+CA-371,+Anza,+CA+92539" target="_blank" rel="noopener">' +
        '<span class="gbp-stars" aria-hidden="true">★★★★★</span>' +
        '<span data-gbp-heading>Anza on Google</span>' +
      '</a>' +
    '</div>'
  );
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
  assert.doesNotMatch(src, /4\.8/);
  assert.doesNotMatch(src, /4\.7/);
  assert.doesNotMatch(src, /\b94\b/);
  assert.doesNotMatch(src, /\b61\b/);
  assert.match(src, /scws-jobs\.vercel\.app\/api\/gbp-ratings/);
  assert.match(src, /g\.page\/r\/CU9X_NG3TvP2EBM\/review/);
  assert.match(src, /57174\+CA-371/);
  assert.doesNotMatch(src, /we don.?t publish a combined star count/i);

  var heritageIdx = indexHtml.indexOf('heritage-banner');
  var gbpIdx = indexHtml.indexOf('id="gbp-ratings"');
  var whyIdx = indexHtml.indexOf('Why Southern California Well Service?');
  assert.ok(heritageIdx > -1 && gbpIdx > heritageIdx && gbpIdx < whyIdx, 'widget must sit under Heritage banner');
  assert.strictEqual(indexHtml.indexOf('id="gbp-ratings"', gbpIdx + 1), -1, 'only one gbp-ratings mount');
  assert.match(indexHtml, /js\/gbp-ratings\.js\?v=/);

  var widgetBlock = indexHtml.slice(gbpIdx, whyIdx);
  assert.match(widgetBlock, /★★★★★/);
  assert.match(widgetBlock, /Anza on Google/);
  assert.match(widgetBlock, /57174\+CA-371/);
  assert.doesNotMatch(widgetBlock, /4\.9/);
  assert.doesNotMatch(widgetBlock, /127/);
  assert.doesNotMatch(widgetBlock, /4\.8/);
  assert.doesNotMatch(widgetBlock, /4\.7/);
  assert.doesNotMatch(widgetBlock, /Ramona/);
  assert.doesNotMatch(widgetBlock, /g\.page\/r\/CU9X_NG3TvP2EBM\/review/);
  assert.doesNotMatch(indexHtml, /reviewCount["']:\s*["']?127/);
  assert.doesNotMatch(indexHtml, /Read us on Google/);
  assert.doesNotMatch(indexHtml, /combined star count/);

  var whyEnd = indexHtml.indexOf('<!-- Services Section -->');
  var whyBlock = indexHtml.slice(whyIdx, whyEnd > whyIdx ? whyEnd : indexHtml.length);
  assert.doesNotMatch(whyBlock, /id="gbp-ratings"/);
  assert.doesNotMatch(whyBlock, /data-gbp-heading/);
  assert.match(whyBlock, /<h3 class="font-bold text-primary text-lg">Google reviews<\/h3>/);
  assert.match(whyBlock, /Fast response, quality work, fair prices — that's what customers say\./);
  assert.match(whyBlock, /Read Anza reviews on Google/);
  assert.match(whyBlock, /57174\+CA-371/);
  assert.doesNotMatch(whyBlock, /g\.page\/r\/CU9X_NG3TvP2EBM\/review/);
  assert.doesNotMatch(whyBlock, /4\.9/);
  assert.doesNotMatch(whyBlock, /127/);

  var liveWin = loadWidget(function () {
    return jsonResponse({
      ramona: { rating: 4.7, count: 61, url: 'https://example.com/ramona' },
      anza: { rating: 4.8, count: 94 },
      updated: '2026-08-21T00:00:00Z'
    });
  });
  await wait(20);
  var heading = liveWin.document.querySelector('[data-gbp-heading]').textContent;
  var shops = mountHtml(liveWin);
  assert.strictEqual(heading, '4.8');
  assert.match(shops, /★★★★★/);
  assert.match(shops, /4\.8/);
  assert.match(shops, /\(94\)/);
  assert.match(shops, />Anza</);
  assert.doesNotMatch(heading, /Ramona/);
  assert.doesNotMatch(shops, /Ramona/);
  assert.doesNotMatch(shops, /https:\/\/example.com\/ramona/);
  assert.match(shops, /57174\+CA-371/);
  assert.doesNotMatch(shops, /4\.9/);
  assert.doesNotMatch(shops, /127/);
  assert.doesNotMatch(heading + shops, /155/);
  assert.doesNotMatch(heading + shops, /4\.7/);
  assert.doesNotMatch(heading + shops, /\b61\b/);

  var failWin = loadWidget(function () {
    return Promise.reject(new Error('network'));
  });
  await wait(20);
  var failHeading = failWin.document.querySelector('[data-gbp-heading]').textContent;
  var failShops = mountHtml(failWin);
  assert.strictEqual(failHeading, 'Anza on Google');
  assert.match(failShops, /★★★★★/);
  assert.match(failShops, /Anza on Google/);
  assert.doesNotMatch(failShops, /Ramona/);
  assert.doesNotMatch(failShops, /g\.page\/r\/CU9X_NG3TvP2EBM\/review/);
  assert.match(failShops, /57174\+CA-371/);
  assert.doesNotMatch(failShops, /4\.9/);
  assert.doesNotMatch(failShops, /127/);
  assert.doesNotMatch(failShops, /4\.7/);
  assert.doesNotMatch(failShops, /\(\d+\)/);

  var unconfigured = loadWidget(function () {
    return jsonResponse({ error: 'gbp_unconfigured' }, 503);
  });
  await wait(20);
  assert.strictEqual(
    unconfigured.document.querySelector('[data-gbp-heading]').textContent,
    'Anza on Google'
  );
  var unconfiguredShops = mountHtml(unconfigured);
  assert.match(unconfiguredShops, /★★★★★/);
  assert.doesNotMatch(unconfiguredShops, /\(\d+\)/);
  assert.doesNotMatch(unconfiguredShops, /Ramona/);
  assert.match(unconfiguredShops, /Anza on Google/);
  assert.match(unconfiguredShops, /57174\+CA-371/);

  var unavailable = loadWidget(function () {
    return jsonResponse({ error: 'gbp_unavailable' }, 502);
  });
  await wait(20);
  var unavailableShops = mountHtml(unavailable);
  assert.strictEqual(
    unavailable.document.querySelector('[data-gbp-heading]').textContent,
    'Anza on Google'
  );
  assert.match(unavailableShops, /★★★★★/);
  assert.doesNotMatch(unavailableShops, /g\.page\/r\/CU9X_NG3TvP2EBM\/review/);
  assert.match(unavailableShops, /57174\+CA-371/);
  assert.doesNotMatch(unavailableShops, /Ramona/);
  assert.doesNotMatch(unavailableShops, /\(\d+\)/);
  assert.doesNotMatch(unavailableShops, /4\.9/);
  assert.doesNotMatch(unavailableShops, /127/);

  var html404 = loadWidget(function () {
    return jsonResponse({ ramona: { rating: 4.7, count: 61 } }, 404);
  });
  await wait(20);
  assert.strictEqual(
    html404.document.querySelector('[data-gbp-heading]').textContent,
    'Anza on Google'
  );
  assert.doesNotMatch(mountHtml(html404), /4\.7/);

  var missingAnza = loadWidget(function () {
    return jsonResponse({
      ramona: { rating: 4.7, count: 61, url: 'https://example.com/ramona' },
      anza: { rating: 'nope' },
      updated: '2026-08-21T00:00:00Z'
    });
  });
  await wait(20);
  var missingHeading = missingAnza.document.querySelector('[data-gbp-heading]').textContent;
  var missingShops = mountHtml(missingAnza);
  assert.strictEqual(missingHeading, 'Anza on Google');
  assert.match(missingShops, /★★★★★/);
  assert.doesNotMatch(missingShops, /Ramona/);
  assert.match(missingShops, /Anza on Google/);
  assert.match(missingShops, /57174\+CA-371/);
  assert.doesNotMatch(missingShops, /4\.7/);
  assert.doesNotMatch(missingShops, /\(\d+\)/);

  var api = liveWin.scwsGbpRatings;
  assert.notStrictEqual(api.LINKS.ramonaReviews, api.LINKS.anzaListing);
  assert.doesNotMatch(api.LINKS.anzaListing, /CU9X_NG3TvP2EBM/);

  var partial = api.shopsHtml({
    ramona: { rating: 4.6, count: 10 },
    anza: { rating: 'nope' }
  });
  assert.doesNotMatch(partial, /Ramona/);
  assert.match(partial, /Anza on Google/);
  assert.match(partial, /★★★★★/);
  assert.doesNotMatch(partial, /4\.6/);
  assert.doesNotMatch(partial, /4\.9/);
  assert.strictEqual(api.headingText({
    ramona: { rating: 4.6, count: 10 },
    anza: { rating: 'nope' }
  }), 'Anza on Google');

  var withAnzaUrl = api.shopsHtml({
    ramona: { rating: 4.6, count: 10 },
    anza: { rating: 4.8, count: 22, url: 'https://example.com/anza' },
    updated: '2026-08-21T00:00:00Z'
  });
  assert.match(withAnzaUrl, /https:\/\/example.com\/anza/);
  assert.match(withAnzaUrl, /★★★★★/);
  assert.match(withAnzaUrl, /4\.8/);
  assert.match(withAnzaUrl, /\(22\)/);
  assert.match(withAnzaUrl, />Anza</);
  assert.doesNotMatch(withAnzaUrl, /CU9X_NG3TvP2EBM/);
  assert.doesNotMatch(withAnzaUrl, /Ramona/);
  assert.strictEqual(api.headingText({
    ramona: { rating: 4.6, count: 10 },
    anza: { rating: 4.8, count: 22, url: 'https://example.com/anza' }
  }), '4.8');

  var fallback = api.fallbackShopsHtml();
  assert.doesNotMatch(fallback, /Ramona/);
  assert.match(fallback, /Anza on Google/);
  assert.match(fallback, /★★★★★/);
  assert.doesNotMatch(fallback, /<\/p>\s*<p class="text-gray-600">/);
  assert.doesNotMatch(fallback, /4\.9/);
  assert.doesNotMatch(fallback, /127/);
  assert.doesNotMatch(fallback, /\(\d+\)/);
  assert.doesNotMatch(fallback, /CU9X_NG3TvP2EBM/);
  assert.match(fallback, /57174\+CA-371/);

  assert.strictEqual(api.hasLive({ rating: 4.6, count: 10 }), true);
  assert.strictEqual(api.hasLive({ rating: 4.6 }), false);
  assert.strictEqual(api.hasLive({ count: 10 }), false);
  assert.strictEqual(api.hasLive({ rating: 0, count: 0 }), true);
  assert.strictEqual(api.hasLive({ rating: 5, count: 0 }), true);
  assert.strictEqual(api.hasLive({ rating: -0.1, count: 1 }), false);
  assert.strictEqual(api.hasLive({ rating: 5.1, count: 1 }), false);
  assert.strictEqual(api.headingText({ error: 'gbp_unconfigured' }), 'Anza on Google');
  assert.strictEqual(api.headingText(null), 'Anza on Google');

  console.log('gbp-ratings tests passed');
}

run().catch(function (err) {
  console.error(err);
  process.exit(1);
});
