/**
 * GA4 Bot Filter + Consent Mode honor
 * Prevents GA4 from tracking obvious bot/scraper traffic
 * Load BEFORE the GA4 snippet
 *
 * If the visitor already accepted/rejected cookies on a page with the
 * banner, honor that decision here so city/other pages stay consistent.
 */
(function() {
  window.dataLayer = window.dataLayer || [];
  if (typeof window.gtag !== 'function') {
    window.gtag = function () { window.dataLayer.push(arguments); };
  }
  try {
    var storedConsent = localStorage.getItem('cookieConsent');
    if (storedConsent === 'accepted' || storedConsent === 'rejected') {
      var granted = storedConsent === 'accepted';
      var state = granted ? 'granted' : 'denied';
      window.gtag('consent', 'default', {
        analytics_storage: state,
        ad_storage: state,
        ad_user_data: state,
        ad_personalization: state
      });
      if (!granted) {
        window['ga-disable-G-5LL1YRWT5T'] = true;
      }
    }
  } catch (e) {}

  var dominated = false;

  // 1. Check for headless browser indicators
  if (navigator.webdriver) dominated = true;
  if (!window.chrome && /Chrome/.test(navigator.userAgent)) dominated = true;
  if (navigator.languages && navigator.languages.length === 0) dominated = true;
  
  // 2. Check for phantom/selenium indicators
  if (window._phantom || window.__nightmare || window.callPhantom) dominated = true;
  if (document.__selenium_unwrapped || document.__webdriver_evaluate || document.__driver_evaluate) dominated = true;
  
  // 3. Check screen dimensions (headless often has 0x0 or tiny screens)
  if (screen.width === 0 || screen.height === 0) dominated = true;
  
  // 4. Check for common bot user agents
  var ua = navigator.userAgent.toLowerCase();
  var botPatterns = ['bot', 'crawl', 'spider', 'scrape', 'headless', 'phantom', 'selenium', 'puppeteer', 'lighthouse'];
  for (var i = 0; i < botPatterns.length; i++) {
    if (ua.indexOf(botPatterns[i]) !== -1) { dominated = true; break; }
  }

  if (dominated) {
    // Override gtag to no-op
    window.gtag = function() {};
    window.dataLayer = { push: function() {} };
    console.log('[GA4-Filter] Bot detected, tracking disabled');
  }
})();
