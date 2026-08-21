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
    '<div id="gbp-ratings">' +
      '<h3 class="font-bold text-primary text-lg" data-gbp-heading>Google reviews</h3>' +
      '<div class="gbp-ratings-shops" data-gbp-shops>' +
        '<p class="text-gray-600">' +
          '<a href="https://www.google.com/maps/place/57174+CA-371,+Anza,+CA+92539" target="_blank" rel="noopener">Anza</a>' +
        '</p>' +
      '</div>' +
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

  var whyBlock = indexHtml.match(/id="gbp-ratings"[\s\S]*?<\/div>\s*<\/div>\s*<\/div>/);
  assert.ok(whyBlock, 'homepage Why SCWS mount missing');
  assert.match(indexHtml, /js\/gbp-ratings\.js\?v=/);
  assert.match(whyBlock[0], /Google reviews/);
  assert.doesNotMatch(indexHtml, /Read us on Google/);
  assert.doesNotMatch(indexHtml, /combined star count/);
  assert.doesNotMatch(whyBlock[0], /4\.9/);
  assert.doesNotMatch(whyBlock[0], /127/);
  assert.doesNotMatch(whyBlock[0], /4\.8/);
  assert.doesNotMatch(whyBlock[0], /4\.7/);
  assert.doesNotMatch(indexHtml, /reviewCount["']:\s*["']?127/);
  assert.doesNotMatch(whyBlock[0], /Ramona/);
  assert.doesNotMatch(whyBlock[0], /g\.page\/r\/CU9X_NG3TvP2EBM\/review/);
  assert.match(whyBlock[0], /57174\+CA-371/);
  assert.match(whyBlock[0], />Anza</);

  var liveWin = loadWidget(function () {
    return jsonResponse({
      ramona: { rating: 4.7, count: 61, url: 'https://example.com/ramona' },
      anza: { rating: 4.8, count: 94 },
      updated: '2026-08-21T00:00:00Z'
    });
  });
  await wait(20);
  var heading = liveWin.document.querySelector('[data-gbp-heading]').textContent;
  var shops = liveWin.document.querySelector('[data-gbp-shops]').innerHTML;
  assert.strictEqual(heading, 'Anza 4.8 (94)');
  assert.doesNotMatch(heading, /Ramona/);
  assert.match(shops, /<strong>Anza<\/strong> 4\.8 \(94\)/);
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
  var failShops = failWin.document.querySelector('[data-gbp-shops]').innerHTML;
  assert.strictEqual(failHeading, 'Google reviews');
  assert.doesNotMatch(failShops, /Ramona/);
  assert.match(failShops, /Anza/);
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
    'Google reviews'
  );
  var unconfiguredShops = unconfigured.document.querySelector('[data-gbp-shops]').innerHTML;
  assert.doesNotMatch(unconfiguredShops, /\(\d+\)/);
  assert.doesNotMatch(unconfiguredShops, /Ramona/);
  assert.match(unconfiguredShops, /Anza/);
  assert.match(unconfiguredShops, /57174\+CA-371/);

  var unavailable = loadWidget(function () {
    return jsonResponse({ error: 'gbp_unavailable' }, 502);
  });
  await wait(20);
  var unavailableShops = unavailable.document.querySelector('[data-gbp-shops]').innerHTML;
  assert.strictEqual(
    unavailable.document.querySelector('[data-gbp-heading]').textContent,
    'Google reviews'
  );
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
    'Google reviews'
  );
  assert.doesNotMatch(
    html404.document.querySelector('[data-gbp-shops]').innerHTML,
    /4\.7/
  );

  var missingAnza = loadWidget(function () {
    return jsonResponse({
      ramona: { rating: 4.7, count: 61, url: 'https://example.com/ramona' },
      anza: { rating: 'nope' },
      updated: '2026-08-21T00:00:00Z'
    });
  });
  await wait(20);
  var missingHeading = missingAnza.document.querySelector('[data-gbp-heading]').textContent;
  var missingShops = missingAnza.document.querySelector('[data-gbp-shops]').innerHTML;
  assert.strictEqual(missingHeading, 'Google reviews');
  assert.doesNotMatch(missingShops, /Ramona/);
  assert.match(missingShops, /Anza/);
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
  assert.match(partial, /Anza/);
  assert.doesNotMatch(partial, /4\.6/);
  assert.doesNotMatch(partial, /4\.9/);
  assert.strictEqual(api.headingText({
    ramona: { rating: 4.6, count: 10 },
    anza: { rating: 'nope' }
  }), 'Google reviews');

  var withAnzaUrl = api.shopsHtml({
    ramona: { rating: 4.6, count: 10 },
    anza: { rating: 4.8, count: 22, url: 'https://example.com/anza' },
    updated: '2026-08-21T00:00:00Z'
  });
  assert.match(withAnzaUrl, /https:\/\/example.com\/anza/);
  assert.doesNotMatch(withAnzaUrl, /CU9X_NG3TvP2EBM/);
  assert.doesNotMatch(withAnzaUrl, /Ramona/);
  assert.strictEqual(api.headingText({
    ramona: { rating: 4.6, count: 10 },
    anza: { rating: 4.8, count: 22, url: 'https://example.com/anza' }
  }), 'Anza 4.8 (22)');

  var fallback = api.fallbackShopsHtml();
  assert.doesNotMatch(fallback, /Ramona/);
  assert.match(fallback, /Anza/);
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
  assert.strictEqual(api.headingText({ error: 'gbp_unconfigured' }), 'Google reviews');
  assert.strictEqual(api.headingText(null), 'Google reviews');

  console.log('gbp-ratings tests passed');
}

run().catch(function (err) {
  console.error(err);
  process.exit(1);
});
