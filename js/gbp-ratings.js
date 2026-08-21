/**
 * Live Google Business Profile ratings for the homepage Why SCWS item.
 *
 * Fetches public JSON from the jobs app (GitHub Pages cannot hold GBP secrets).
 * Success body (from scws-jobs src/lib/gbp.ts GbpRatingsPayload):
 *   { ramona: { rating, count, url? }, anza: { rating, count, url? }, updated }
 * Failure body: { error: "gbp_unconfigured" | "gbp_unavailable" }
 *
 * Never invent or hardcode a combined star count. Never reuse the Ramona
 * review URL for Anza. On any fetch/parse failure, show "Google reviews"
 * plus the two shop links already in the homepage mount.
 */
(function (root) {
  'use strict';

  var API_URL = 'https://scws-jobs.vercel.app/api/gbp-ratings';
  var FETCH_MS = 6000;

  var RAMONA_REVIEWS = 'https://g.page/r/CU9X_NG3TvP2EBM/review';
  // No Anza g.page exists in this repo. Use the contact.html Maps place page.
  var ANZA_LISTING = 'https://www.google.com/maps/place/57174+CA-371,+Anza,+CA+92539';

  var SHOPS = {
    ramona: { label: 'Ramona', fallbackUrl: RAMONA_REVIEWS },
    anza: { label: 'Anza', fallbackUrl: ANZA_LISTING }
  };

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

  function shopUrl(key, data) {
    if (data && isHttpUrl(data.url)) return data.url.trim();
    return SHOPS[key].fallbackUrl;
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

  function shopLine(key, data) {
    var meta = SHOPS[key];
    var url = escapeAttr(shopUrl(key, data));
    if (hasLive(data)) {
      return (
        '<a href="' + url + '" target="_blank" rel="noopener">' +
          '<strong>' + meta.label + '</strong> ' +
          formatRating(data.rating) + ' (' + formatCount(data.count) + ')' +
        '</a>'
      );
    }
    return (
      '<a href="' + url + '" target="_blank" rel="noopener">' + meta.label + '</a>'
    );
  }

  function headingText(payload) {
    if (!payload || typeof payload !== 'object' || payload.error) {
      return 'Google reviews';
    }
    var parts = [];
    if (hasLive(payload.ramona)) {
      parts.push(
        'Ramona ' + formatRating(payload.ramona.rating) +
          ' (' + formatCount(payload.ramona.count) + ')'
      );
    }
    if (hasLive(payload.anza)) {
      parts.push(
        'Anza ' + formatRating(payload.anza.rating) +
          ' (' + formatCount(payload.anza.count) + ')'
      );
    }
    return parts.length ? parts.join(' · ') : 'Google reviews';
  }

  function shopsHtml(payload) {
    if (!payload || typeof payload !== 'object' || payload.error) {
      return fallbackShopsHtml();
    }
    return (
      '<p class="text-gray-600">' + shopLine('ramona', payload.ramona) + '</p>' +
      '<p class="text-gray-600">' + shopLine('anza', payload.anza) + '</p>'
    );
  }

  function fallbackShopsHtml() {
    return (
      '<p class="text-gray-600">' +
        '<a href="' + RAMONA_REVIEWS + '" target="_blank" rel="noopener">Ramona</a>' +
        ' · ' +
        '<a href="' + ANZA_LISTING + '" target="_blank" rel="noopener">Anza</a>' +
      '</p>'
    );
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

  function headingNode(mount) {
    return (
      mount.querySelector('[data-gbp-heading]') ||
      mount.querySelector('h3')
    );
  }

  function shopsNode(mount) {
    return (
      mount.querySelector('[data-gbp-shops]') ||
      mount.querySelector('.gbp-ratings-shops')
    );
  }

  function renderMount(mount, payload) {
    var heading = headingNode(mount);
    var shops = shopsNode(mount);
    if (heading) heading.textContent = headingText(payload);
    if (shops) {
      shops.innerHTML = shopsHtml(payload);
      return;
    }
    mount.innerHTML =
      '<h3 class="font-bold text-primary text-lg">' + headingText(payload) + '</h3>' +
      shopsHtml(payload);
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
        if (!hasLive(data.ramona) && !hasLive(data.anza)) {
          throw new Error('no shop ratings');
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
    shopsHtml: shopsHtml,
    fallbackShopsHtml: fallbackShopsHtml,
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
