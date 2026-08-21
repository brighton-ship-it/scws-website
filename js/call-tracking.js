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
        'page_title': document.title
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
