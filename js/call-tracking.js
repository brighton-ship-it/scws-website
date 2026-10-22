/**
 * SCWS Click-to-Call / Click-to-Text Conversion Tracking
 * Tracks tel: and sms: clicks as GA4 events with source attribution
 * Works with voice (760) 440-8520 and text (760) 219-5877
 * Ads phone conversion is voice-only — never sent on SMS clicks
 */
(function() {
  'use strict';

  // Lets inline trackPhoneClick / extra tel: listeners stand down
  window.scwsCallTracking = true;

  // Determine traffic source from referrer + UTM
  function getTrafficSource() {
    var utm = {};
    try { utm = JSON.parse(sessionStorage.getItem('scws_utm') || '{}'); } catch(e) {}

    // Click ids count even when utm_medium is absent (gclid-only landing, or a
    // later page in the same session). A returning Ads visitor keeps the Ads
    // number from localStorage after sessionStorage is gone, so the click
    // source has to follow that stored source too. Ads wins before a generic
    // utm_source, matching the number swap.
    if (utm.gclid || utm.gbraid || utm.wbraid) return 'google_ads';
    if (isAdsLanding(window.location.search || '')) return 'google_ads';
    try {
      var rec = visitorSource();
      if (rec && rec.source === 'google_ads') return 'google_ads';
    } catch (e) {}

    if (utm.utm_medium === 'cpc' || utm.utm_source === 'google' && utm.utm_medium === 'cpc') return 'google_ads';
    if (utm.utm_source) return utm.utm_source + '/' + (utm.utm_medium || 'none');
    
    var ref = document.referrer.toLowerCase();
    if (!ref) return 'direct';
    if (ref.indexOf('google.') !== -1) return 'google/organic';
    if (ref.indexOf('bing.') !== -1) return 'bing/organic';
    if (ref.indexOf('yahoo.') !== -1) return 'yahoo/organic';
    if (ref.indexOf('facebook.') !== -1 || ref.indexOf('fb.') !== -1) return 'facebook/social';
    if (ref.indexOf('yelp.') !== -1) return 'yelp/referral';
    if (ref.indexOf('nextdoor.') !== -1) return 'nextdoor/referral';
    return 'referral';
  }

  // Get clean page path
  function getPagePath() {
    return window.location.pathname.replace(/\.html$/, '').replace(/\/$/, '') || '/';
  }

  // Optional A/B params — only if another PR has set window.scwsAb
  function getAbParams() {
    var extra = {};
    var ab = window.scwsAb;
    if (!ab || typeof ab !== 'object') return extra;
    if (ab.expId || ab.experimentId || ab.id) {
      extra.exp_id = ab.expId || ab.experimentId || ab.id;
    }
    if (ab.variant || ab.expVar || ab.exp_var) {
      extra.exp_var = ab.variant || ab.expVar || ab.exp_var;
    }
    return extra;
  }

  function bindOnce(el, handler) {
    if (!el || el.getAttribute('data-scws-tracked') === '1') return;
    el.setAttribute('data-scws-tracked', '1');
    el.addEventListener('click', handler);
  }

  function attachListeners() {
    var calls = document.querySelectorAll('a[href^="tel:"]');
    for (var i = 0; i < calls.length; i++) {
      bindOnce(calls[i], handleCallClick);
    }
    var texts = document.querySelectorAll('a[href^="sms:"]');
    for (var j = 0; j < texts.length; j++) {
      bindOnce(texts[j], handleTextClick);
    }
  }

  function handleCallClick(e) {
    var source = getTrafficSource();
    var page = getPagePath();
    var isOrganic = source.indexOf('organic') !== -1;
    var extra = getAbParams();
    
    // Fire GA4 event
    if (typeof gtag === 'function') {
      // Primary event — all call clicks
      // One GA4 event per tap. Organic is a parameter, not a second event.
      gtag('event', 'call_click', Object.assign({
        'event_category': 'engagement',
        'event_label': page,
        'traffic_source': source,
        'is_organic': isOrganic,
        'page_path': page,
        'page_title': document.title,
        'call_number': (e && e.currentTarget && e.currentTarget.getAttribute('data-scws-swapped') === '1' && swapTarget) ? '+1' + swapTarget.digits : '+1' + MAIN_DIGITS
      }, extra));

      // Google Ads conversion (if from paid) — voice only
      if (source === 'google_ads') {
        gtag('event', 'conversion', {
          'send_to': 'AW-490838730/aFiRCMDlofAbEMq1huoB'
        });
      }
    }

    // Log for debugging (remove in production if noisy)
    console.log('[SCWS Call Tracking]', source, page);
  }

  function handleTextClick(e) {
    var source = getTrafficSource();
    var page = getPagePath();
    var isOrganic = source.indexOf('organic') !== -1;
    var extra = getAbParams();

    if (typeof gtag === 'function') {
      gtag('event', 'text_click', Object.assign({
        'event_category': 'engagement',
        'event_label': page,
        'traffic_source': source,
        'is_organic': isOrganic,
        'page_path': page,
        'page_title': document.title
      }, extra));
    }

    // Do not send the Google Ads phone conversion on text clicks
    console.log('[SCWS Text Tracking]', source, page);
  }


  // ---------------------------------------------------------------------
  // Source-based call-number swap (first-party DNI).
  // Each visitor gets ONE source (first touch, kept 30 days in localStorage;
  // a later Google Ads click always wins). Visible numbers follow the source:
  //   google_ads -> (760) 331-2502  "SCWS - GOOGLE_ADS" (Leads-Search-1 pump + any other / unknown campaign)
  //     drilling campaign (utm_campaign ~ drill, or utm_id/campaignid 23533402261) -> (760) 825-0520 "SCWS - GOOGLE_ADS_DRILLING"
  //     weekend campaign  (utm_campaign ~ weekend, or utm_id/campaignid 24368951997) -> (760) 825-6285 "SCWS - GOOGLE_ADS_WEEKEND"
  //   seo        -> (760) 463-0493  "SCWS - SEO" (organic search visitors)
  //   gbp        -> (760) 279-1262  "SCWS - GBP_RAMONA" (website visits from the Google profile / Maps)
  //   yelp, apple_maps, referral, direct -> main line (760) 440-8520 (no number yet / not a channel)
  // All tracking numbers forward to the main line (recorded) and are logged by scws-jobs.
  // ---------------------------------------------------------------------
  var MAIN_DIGITS = '7604408520';
  var ADS_DIGITS = '7603312502';
  var ADS_DISPLAY = '(760) 331-2502';
  var SOURCE_NUMBERS = {
    google_ads: { digits: ADS_DIGITS, display: ADS_DISPLAY },
    seo: { digits: '7604630493', display: '(760) 463-0493' },
    gbp: { digits: '7602791262', display: '(760) 279-1262' }
  };
  // Per-campaign Google Ads numbers (keyed by visitor.ads_campaign).
  var ADS_CAMPAIGN_NUMBERS = {
    drilling: { digits: '7608250520', display: '(760) 825-0520' },
    weekend: { digits: '7608256285', display: '(760) 825-6285' }
  };
  var ADS_CAMPAIGN_IDS = { '23533402261': 'drilling', '24368951997': 'weekend', '19603168204': 'pump' };
  // Which ads campaign a landing came from. '' = not identifiable (stays on 331-2502).
  function adsCampaignFrom(search) {
    var id = param(search, 'utm_id') || param(search, 'campaignid') || param(search, 'cid');
    if (ADS_CAMPAIGN_IDS[id]) return ADS_CAMPAIGN_IDS[id];
    var c = param(search, 'utm_campaign');
    if (/weekend/.test(c)) return 'weekend';
    if (/drill/.test(c)) return 'drilling';
    if (/pump|leads-search-1|search-1/.test(c)) return 'pump';
    return '';
  }
  function adsNumberFor(rec) {
    return (rec && rec.ads_campaign && ADS_CAMPAIGN_NUMBERS[rec.ads_campaign]) || SOURCE_NUMBERS.google_ads;
  }
  var ADS_FLAG_KEY = 'scws_ads_visitor';
  var SRC_KEY = 'scws_src';
  var FLAG_TTL_MS = 30 * 24 * 60 * 60 * 1000;
  var MAIN_TEXT_RE = /\(?760\)?[\s.\-]*440[\s.\-]*8520/g;
  var MAIN_TEL_RE = /^tel:(?:\+?1)?[\s\-.()]*760[\s\-.()]*440[\s\-.()]*8520$/i;

  function isAdsLanding(search) {
    var q = search == null ? (window.location.search || '') : search;
    if (/[?&](gclid|gbraid|wbraid)=[^&]+/i.test(q)) return true;
    var m = /[?&]utm_medium=([^&]+)/i.exec(q);
    return !!(m && /^(cpc|ppc|paid)$/i.test(decodeURIComponent(m[1])));
  }

  function param(q, k) {
    var m = new RegExp('[?&]' + k + '=([^&]*)', 'i').exec(q || '');
    try { return m ? decodeURIComponent(m[1].replace(/\+/g, ' ')).toLowerCase() : ''; } catch (e) { return ''; }
  }

  // Same rules as scws-jobs src/lib/leads/lead-channel.ts. null = no new information (e.g. internal navigation).
  function classifyLanding(search, referrer) {
    if (isAdsLanding(search)) return 'google_ads';
    var src = param(search, 'utm_source'), med = param(search, 'utm_medium');
    if (src || med) {
      if (/^(gbp|gmb|google_business|googlebusiness|google_my_business|googlemybusiness|business_profile|maps)$/.test(src) || /^(gbp|gmb|maps|local)$/.test(med)) return 'gbp';
      if (/yelp/.test(src)) return 'yelp';
      if (/^(apple|apple_maps|applemaps|apple_business|maps\.apple\.com)$/.test(src)) return 'apple_maps';
      if (med === 'organic' || (/^(google|bing|yahoo|duckduckgo)$/.test(src) && !med)) return 'seo';
      return 'referral';
    }
    if (!referrer) return 'direct';
    var host = '', path = '';
    try { var u = new URL(referrer); host = u.hostname.toLowerCase(); path = u.pathname.toLowerCase(); } catch (e) { return 'referral'; }
    if (/(^|\.)scwellservice\.com$/.test(host)) return null;
    if (host === 'maps.apple.com' || /\.maps\.apple\.com$/.test(host)) return 'apple_maps';
    if (/(^|\.)yelp\.[a-z.]+$/.test(host)) return 'yelp';
    if (/^maps\.google\./.test(host) || (/(^|\.)google\.[a-z.]+$/.test(host) && path.indexOf('/maps') === 0) || host === 'business.google.com' || host === 'g.page') return 'gbp';
    if (/(^|\.)(google|bing|yahoo|duckduckgo|ecosia|search\.brave)\.[a-z.]+$/.test(host)) return 'seo';
    return 'referral';
  }

  function readJson(k) { try { return JSON.parse(window.localStorage.getItem(k) || 'null'); } catch (e) { return null; } }

  // First touch wins for 30 days, except: Google Ads always wins, and a real channel replaces a stored 'direct'.
  function visitorSource() {
    var now = Date.now();
    var fresh = classifyLanding(window.location.search || '', document.referrer || '');
    var stored = readJson(SRC_KEY);
    if (stored && !(now - stored.ts < FLAG_TTL_MS)) stored = null;
    try {
      var t = parseInt(window.localStorage.getItem(ADS_FLAG_KEY) || '', 10);
      if ((!fresh || fresh === 'direct') && t && now - t < FLAG_TTL_MS && (!stored || stored.source !== 'google_ads')) fresh = 'google_ads';
    } catch (e) {}
    var keep = stored && fresh !== 'google_ads' && !(stored.source === 'direct' && fresh && fresh !== 'direct');
    var rec = keep ? stored : (fresh ? { source: fresh, ts: now, referrer: (document.referrer || 'direct').slice(0, 300), landing: (window.location.origin + window.location.pathname + (window.location.search || '')).slice(0, 300) } : stored);
    if (rec && rec.source === 'google_ads' && fresh === 'google_ads' && !keep) {
      var camp = adsCampaignFrom(window.location.search || '');
      // A new ads landing without campaign info keeps the campaign from the stored ads visit.
      rec.ads_campaign = camp || (stored && stored.source === 'google_ads' && stored.ads_campaign) || '';
    }
    if (!rec) rec = { source: 'direct', ts: now, referrer: 'direct', landing: (window.location.origin + window.location.pathname).slice(0, 300) };
    try {
      window.localStorage.setItem(SRC_KEY, JSON.stringify(rec));
      if (rec.source === 'google_ads') window.localStorage.setItem(ADS_FLAG_KEY, String(rec.ts));
    } catch (e) {}
    return rec;
  }

  function isAdsVisitor() { return visitorSource().source === 'google_ads'; }

  function swapNumbers(root, target) {
    target = target || SOURCE_NUMBERS.google_ads;
    var changed = 0;
    var links = (root.querySelectorAll ? root.querySelectorAll('a[href^="tel:"]') : []);
    for (var i = 0; i < links.length; i++) {
      var href = links[i].getAttribute('href') || '';
      if (MAIN_TEL_RE.test(href)) {
        links[i].setAttribute('href', 'tel:+1' + target.digits);
        links[i].setAttribute('data-scws-swapped', '1');
        changed++;
      }
    }
    var doc = root.ownerDocument || root;
    var walker = doc.createTreeWalker(root, 4, null, false);
    var nodes = [], n;
    while ((n = walker.nextNode())) {
      var p = n.parentNode && n.parentNode.nodeName;
      if (p === 'SCRIPT' || p === 'STYLE' || p === 'NOSCRIPT' || p === 'TEXTAREA') continue;
      MAIN_TEXT_RE.lastIndex = 0;
      if (MAIN_TEXT_RE.test(n.nodeValue)) nodes.push(n);
    }
    for (var j = 0; j < nodes.length; j++) {
      nodes[j].nodeValue = nodes[j].nodeValue.replace(MAIN_TEXT_RE, target.display);
      changed++;
    }
    return changed;
  }

  var visitor = null;
  var swapTarget = null;
  var swapReported = false;
  var swapInited = false;

  // Tel links stay hidden (css #scws-phone-ready) until this runs, including
  // the no-swap path, so a visitor never sees or taps the wrong number.
  function revealPhones() {
    var root = document.documentElement;
    if (root && root.classList) root.classList.add('scws-phones-ready');
  }

  function runSwap() {
    if (!swapTarget || !document.body) return;
    var changed = swapNumbers(document.body, swapTarget);
    if (changed && !swapReported) {
      swapReported = true;
      try {
        if (typeof gtag === 'function') {
          gtag('event', 'call_number_swap', {
            'event_category': 'engagement',
            'swap_number': '+1' + swapTarget.digits,
            'page_path': getPagePath(),
            'traffic_source': visitor.source
          });
        }
      } catch (e) {}
    }
  }

  function initAdsSwap() {
    if (!document.body) return;
    if (swapInited) {
      revealPhones();
      return;
    }
    swapInited = true;
    try {
      visitor = visitorSource();
      swapTarget = visitor.source === 'google_ads' ? adsNumberFor(visitor) : (SOURCE_NUMBERS[visitor.source] || null);
      if (swapTarget) {
        runSwap();
        var mo = new MutationObserver(function () {
          mo.disconnect();
          runSwap();
          mo.observe(document.body, { childList: true, subtree: true });
        });
        mo.observe(document.body, { childList: true, subtree: true });
      }
    } finally {
      revealPhones();
    }
  }

  // Every lead form POST to scws-jobs carries the visitor's source + first-touch referrer / landing page.
  var LEAD_API_RE = /^https:\/\/scws-jobs\.vercel\.app\/api\/(booking|leads\/create)(\?|$)/;
  function attributionFields() {
    var v = visitor || visitorSource();
    var out = { site_source: v.source, first_referrer: v.referrer, first_landing_page: v.landing };
    if (v.source === 'google_ads' && v.ads_campaign) out.ads_campaign = v.ads_campaign;
    return out;
  }
  function enrichBody(body) {
    if (typeof body !== 'string') return body;
    try {
      var obj = JSON.parse(body);
      if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return body;
      var add = attributionFields();
      for (var k in add) if (obj[k] == null || obj[k] === '') obj[k] = add[k];
      if (!obj.landing_page) obj.landing_page = window.location.href;
      if (!obj.referrer) obj.referrer = document.referrer || 'direct';
      return JSON.stringify(obj);
    } catch (e) { return body; }
  }
  if (typeof window.fetch === 'function' && !window.fetch.__scwsLeadSource) {
    var origFetch = window.fetch;
    var wrapped = function (input, init) {
      try {
        var url = typeof input === 'string' ? input : (input && input.url) || '';
        if (LEAD_API_RE.test(url) && init && init.body) init = Object.assign({}, init, { body: enrichBody(init.body) });
      } catch (e) {}
      return origFetch.call(this, input, init);
    };
    wrapped.__scwsLeadSource = true;
    window.fetch = wrapped;
  }

  window.scwsCallSwap = { swapNumbers: swapNumbers, isAdsLanding: isAdsLanding, classifyLanding: classifyLanding, visitorSource: visitorSource, attributionFields: attributionFields, enrichBody: enrichBody, ADS_DIGITS: ADS_DIGITS, SOURCE_NUMBERS: SOURCE_NUMBERS, ADS_CAMPAIGN_NUMBERS: ADS_CAMPAIGN_NUMBERS, adsCampaignFrom: adsCampaignFrom, adsNumberFor: adsNumberFor };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAdsSwap);
  } else {
    initAdsSwap();
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachListeners);
  } else {
    attachListeners();
  }

  // Also catch dynamically added tel: / sms: links (e.g., chat widget, popups)
  var observer = new MutationObserver(function(mutations) {
    for (var i = 0; i < mutations.length; i++) {
      var added = mutations[i].addedNodes;
      for (var j = 0; j < added.length; j++) {
        var node = added[j];
        if (node.nodeType === 1 && node.matches && node.matches('a[href^="tel:"]')) {
          bindOnce(node, handleCallClick);
        }
        if (node.nodeType === 1 && node.matches && node.matches('a[href^="sms:"]')) {
          bindOnce(node, handleTextClick);
        }
        if (node.querySelectorAll) {
          var newCalls = node.querySelectorAll('a[href^="tel:"]');
          for (var k = 0; k < newCalls.length; k++) {
            bindOnce(newCalls[k], handleCallClick);
          }
          var newTexts = node.querySelectorAll('a[href^="sms:"]');
          for (var n = 0; n < newTexts.length; n++) {
            bindOnce(newTexts[n], handleTextClick);
          }
        }
      }
    }
  });
  observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
})();
