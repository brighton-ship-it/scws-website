/**
 * Combined Google ratings for the homepage hero kicker and shared mounts.
 *
 * Fetches public JSON from the jobs app (GitHub Pages cannot hold GBP secrets).
 * Success body (from scws-jobs src/lib/gbp.ts GbpRatingsPayload):
 *   { ramona: { rating, count, url? }, anza: { rating, count, url? }, updated }
 * Failure body: { error: "gbp_unconfigured" | "gbp_unavailable" }
 *
 * Visible copy is the combined Ramona + Anza figure, not a single shop:
 *   ★★★★★  4.8  from 170+ Google reviews  across our Ramona and Anza shops
 * The link stays the Anza GBP listing already used on the homepage.
 * Never reuse the Ramona review URL for that href.
 *
 * Verified from the Google Business Profile API on 2026-10-02:
 *   Anza 4.8 (108), Ramona 4.7 (62), combined 170 reviews, weighted 4.76 → 4.8.
 * The API is often unconfigured, so that snapshot is what visitors see.
 * A live payload is used only when both shops are present and the total
 * is at least 170, so a stale Anza-only count cannot overwrite it.
 */
(function (root) {
  'use strict';

  var API_URL = 'https://scws-jobs.vercel.app/api/gbp-ratings';
  var FETCH_MS = 6000;

  // Documented so it is never reused as the Anza href.
  var RAMONA_REVIEWS = 'https://g.page/r/CU9X_NG3TvP2EBM/review';
  // Anza Google Business Profile (g.page). This is the listing, not a
  // write-a-review dump — do not append /review. Do not replace this with the
  // street-address Maps pin (57174 CA-371) or the Ramona g.page above.
  var ANZA_LISTING = 'https://g.page/r/Cajtn6jSo-ONEBM';

  // GBP API pull, 2026-10-02. Weighted average 4.76 displays as 4.8.
  var SHOPS = {
    asOf: '2026-10-02',
    anza: { rating: 4.8, count: 108 },
    ramona: { rating: 4.7, count: 62 }
  };
  var COMBINED_SNAPSHOT = { rating: 4.8, countLabel: '170+', asOf: '2026-10-02' };

  var SHOP_LABEL = 'across our Ramona and Anza shops';
  var STAR_ROW = '<span class="gbp-stars" aria-hidden="true">★★★★★</span>';

  function hasLive(data) {
    return !!(
      data &&
      typeof data.rating === 'number' &&
      isFinite(data.rating) &&
      data.rating >= 0 &&
      data.rating <= 5 &&
      typeof data.count === 'number' &&
      isFinite(data.count) &&
      data.count >= 0
    );
  }

  function formatRating(n) {
    return (Math.round(n * 10) / 10).toFixed(1);
  }

  function combinedLive(payload) {
    if (!payload || typeof payload !== 'object' || payload.error) return null;
    if (!hasLive(payload.anza) || !hasLive(payload.ramona)) return null;
    var count = payload.anza.count + payload.ramona.count;
    if (!(count >= 170)) return null;
    var weighted =
      (payload.anza.rating * payload.anza.count +
        payload.ramona.rating * payload.ramona.count) /
      count;
    return {
      rating: weighted,
      countLabel: String(Math.round(count)) + '+'
    };
  }

  function headingText(payload) {
    var data = combinedLive(payload) || COMBINED_SNAPSHOT;
    return formatRating(data.rating);
  }

  function ratedWidgetHtml(data) {
    var rating = formatRating(data.rating);
    var countLabel = data.countLabel || COMBINED_SNAPSHOT.countLabel;
    return (
      '<a class="gbp-ratings-link" href="' + ANZA_LISTING + '" target="_blank" rel="noopener">' +
        STAR_ROW +
        '<span class="gbp-ratings-score" data-gbp-heading>' + rating + '</span>' +
        '<span class="gbp-ratings-count">from ' + countLabel + ' Google reviews</span>' +
        '<span class="gbp-ratings-label" data-gbp-shops>' + SHOP_LABEL + '</span>' +
      '</a>'
    );
  }

  function fallbackWidgetHtml() {
    return ratedWidgetHtml(COMBINED_SNAPSHOT);
  }

  function widgetHtml(payload) {
    var data = combinedLive(payload);
    return data ? ratedWidgetHtml(data) : fallbackWidgetHtml();
  }

  function shopsHtml(payload) {
    return widgetHtml(payload);
  }

  function fallbackShopsHtml() {
    return fallbackWidgetHtml();
  }

  function mountNodes() {
    var nodes = [];
    var byId = root.document.getElementById('gbp-ratings');
    if (byId) nodes.push(byId);
    var extra = root.document.querySelectorAll('[data-gbp-ratings]');
    for (var i = 0; i < extra.length; i++) {
      if (extra[i] !== byId) nodes.push(extra[i]);
    }
    return nodes;
  }

  function renderMount(mount, payload) {
    mount.innerHTML = widgetHtml(payload);
  }

  function renderAll(payload) {
    var nodes = mountNodes();
    for (var i = 0; i < nodes.length; i++) {
      renderMount(nodes[i], payload);
    }
  }

  function fetchRatings() {
    if (typeof root.fetch !== 'function') {
      return Promise.reject(new Error('no fetch'));
    }
    var ctrl = typeof root.AbortController === 'function' ? new root.AbortController() : null;
    var timer = root.setTimeout(function () {
      if (ctrl) ctrl.abort();
    }, FETCH_MS);
    return root
      .fetch(API_URL, {
        method: 'GET',
        credentials: 'omit',
        cache: 'no-store',
        signal: ctrl ? ctrl.signal : undefined,
        headers: { Accept: 'application/json' }
      })
      .then(function (res) {
        if (!res || !res.ok) throw new Error('bad status');
        return res.json();
      })
      .then(function (data) {
        if (!combinedLive(data)) throw new Error('no combined ratings');
        return data;
      })
      .finally(function () {
        root.clearTimeout(timer);
      });
  }

  function init() {
    if (!mountNodes().length) return Promise.resolve();
    renderAll(null);
    return fetchRatings()
      .then(function (data) {
        renderAll(data);
      })
      .catch(function () {
        renderAll(null);
      });
  }

  root.scwsGbpRatings = {
    API_URL: API_URL,
    COMBINED_SNAPSHOT: COMBINED_SNAPSHOT,
    SHOPS: SHOPS,
    LINKS: {
      ramonaReviews: RAMONA_REVIEWS,
      anzaListing: ANZA_LISTING
    },
    hasLive: hasLive,
    headingText: headingText,
    widgetHtml: widgetHtml,
    shopsHtml: shopsHtml,
    fallbackShopsHtml: fallbackShopsHtml,
    fallbackWidgetHtml: fallbackWidgetHtml,
    init: init
  };

  if (root.document) {
    if (root.document.readyState === 'loading') {
      root.document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }
})(typeof window !== 'undefined' ? window : globalThis);
