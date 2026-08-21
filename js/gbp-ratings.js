/**
 * Live Google Business Profile ratings for the homepage strip
 * under the Heritage / Ransom banner.
 *
 * Fetches public JSON from the jobs app (GitHub Pages cannot hold GBP secrets).
 * Success body (from scws-jobs src/lib/gbp.ts GbpRatingsPayload):
 *   { ramona: { rating, count, url? }, anza: { rating, count, url? }, updated }
 * Failure body: { error: "gbp_unconfigured" | "gbp_unavailable" }
 *
 * Homepage widget shows Anza only. Never invent or hardcode a star count.
 * Never reuse the Ramona review URL for Anza. On any fetch/parse failure
 * or missing Anza rating, show a star row plus "Anza on Google" linking
 * to the Anza Maps listing already in the homepage mount.
 */
(function (root) {
  'use strict';

  var API_URL = 'https://scws-jobs.vercel.app/api/gbp-ratings';
  var FETCH_MS = 6000;

  // Documented so it is never reused as the Anza href.
  var RAMONA_REVIEWS = 'https://g.page/r/CU9X_NG3TvP2EBM/review';
  // No Anza g.page exists in this repo. Use the contact.html Maps place page.
  var ANZA_LISTING = 'https://www.google.com/maps/place/57174+CA-371,+Anza,+CA+92539';

  var SHOP = { label: 'Anza', fallbackUrl: ANZA_LISTING };
  var STAR_ROW = '<span class="gbp-stars" aria-hidden="true">★★★★★</span>';

  function isHttpUrl(value) {
    return typeof value === 'string' && /^https?:\/\/\S+$/i.test(value.trim());
  }

  function escapeAttr(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function shopUrl(data) {
    if (data && isHttpUrl(data.url)) return data.url.trim();
    return SHOP.fallbackUrl;
  }

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

  function formatCount(n) {
    return String(Math.round(n));
  }

  function headingText(payload) {
    if (payload && typeof payload === 'object' && !payload.error && hasLive(payload.anza)) {
      return formatRating(payload.anza.rating);
    }
    return 'Anza on Google';
  }

  function fallbackWidgetHtml() {
    return (
      '<a class="gbp-ratings-link" href="' + ANZA_LISTING + '" target="_blank" rel="noopener">' +
        STAR_ROW +
        '<span data-gbp-heading>Anza on Google</span>' +
      '</a>'
    );
  }

  function widgetHtml(payload) {
    if (!payload || typeof payload !== 'object' || payload.error || !hasLive(payload.anza)) {
      return fallbackWidgetHtml();
    }
    var data = payload.anza;
    var url = escapeAttr(shopUrl(data));
    var rating = formatRating(data.rating);
    var count = formatCount(data.count);
    return (
      '<a class="gbp-ratings-link" href="' + url + '" target="_blank" rel="noopener">' +
        STAR_ROW +
        '<span class="gbp-ratings-score" data-gbp-heading>' + rating + '</span>' +
        '<span class="gbp-ratings-count">(' + count + ')</span>' +
        '<span class="gbp-ratings-label" data-gbp-shops>' + SHOP.label + '</span>' +
      '</a>'
    );
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
        if (!data || typeof data !== 'object' || data.error) {
          throw new Error('gbp error payload');
        }
        if (!hasLive(data.anza)) {
          throw new Error('no anza ratings');
        }
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
