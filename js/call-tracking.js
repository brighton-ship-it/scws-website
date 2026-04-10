/**
 * SCWS Click-to-Call Conversion Tracking
 * Tracks all tel: link clicks as GA4 events with source attribution
 * Works with single number (760) 440-8520 across all pages
 */
(function() {
  'use strict';

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

  // Attach click listeners to all tel: links
  function attachListeners() {
    var links = document.querySelectorAll('a[href^="tel:"]');
    for (var i = 0; i < links.length; i++) {
      links[i].addEventListener('click', handleCallClick);
    }
  }

  function handleCallClick(e) {
    var source = getTrafficSource();
    var page = getPagePath();
    var isOrganic = source.indexOf('organic') !== -1;
    
    // Fire GA4 event
    if (typeof gtag === 'function') {
      // Primary event — all call clicks
      gtag('event', 'call_click', {
        'event_category': 'engagement',
        'event_label': page,
        'traffic_source': source,
        'is_organic': isOrganic,
        'page_path': page,
        'page_title': document.title
      });

      // Organic-specific conversion event
      if (isOrganic) {
        gtag('event', 'seo_call_conversion', {
          'event_category': 'conversion',
          'event_label': page,
          'search_engine': source.split('/')[0],
          'landing_page': page
        });
      }

      // Google Ads conversion (if from paid)
      if (source === 'google_ads') {
        gtag('event', 'conversion', {
          'send_to': 'AW-490838730/aFiRCMDlofAbEMq1huoB'
        });
      }
    }

    // Log for debugging (remove in production if noisy)
    console.log('[SCWS Call Tracking]', source, page);
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachListeners);
  } else {
    attachListeners();
  }

  // Also catch dynamically added tel: links (e.g., chat widget, popups)
  var observer = new MutationObserver(function(mutations) {
    for (var i = 0; i < mutations.length; i++) {
      var added = mutations[i].addedNodes;
      for (var j = 0; j < added.length; j++) {
        if (added[j].querySelectorAll) {
          var newLinks = added[j].querySelectorAll('a[href^="tel:"]');
          for (var k = 0; k < newLinks.length; k++) {
            newLinks[k].addEventListener('click', handleCallClick);
          }
        }
      }
    }
  });
  observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
})();
