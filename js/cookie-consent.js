/* Cookie Consent Banner for SCWS
 * One line, pinned to the bottom above #sticky-cta.
 * Never covers the homepage hero Call or the sticky Call/Text/Estimate.
 * On mobile, wait for the first scroll so the first-paint Call stays clear.
 *
 * Consent Mode: this file must load BEFORE gtag.js so the default
 * (granted, or denied if cookieConsent is already rejected) is set first.
 */

(function () {
  var STORAGE_KEY = 'cookieConsent';
  var GA_ID = 'G-5LL1YRWT5T';

  // Same rules as css/styles.css and css/shop-chrome.css, for pages that
  // load Tailwind from the CDN and neither stylesheet.
  function ensureHeaderCallCss() {
    if (document.getElementById('scws-header-call-css')) return;
    var style = document.createElement('style');
    style.id = 'scws-header-call-css';
    style.textContent =
      '@media (max-width:767px){' +
      'header > div,header .header-content,header .shop-header-inner{min-width:0}' +
      'header .flex.justify-between,header .flex.items-center,header .header-content{flex-wrap:nowrap !important;min-width:0;gap:.35rem}' +
      'header a.shrink-0,header a.shrink{flex-shrink:1 !important;min-width:0 !important}' +
      'header img[src*="logo"],header .site-logo-img{max-width:108px !important;width:auto !important;height:auto !important;max-height:2rem !important}' +
      'header a[href^="tel:"],header .site-phone-cta{flex:0 0 auto !important;display:inline-flex !important;align-items:center;justify-content:center;white-space:nowrap;min-height:44px;max-width:none !important;box-sizing:border-box;font-size:.75rem !important;line-height:1.15 !important;padding:.45rem .55rem !important}' +
      'header #mobile-menu-btn,header button[aria-label="Toggle menu"],header .shop-menu-btn{flex:0 0 auto;min-width:44px;min-height:44px;padding:10px;box-sizing:border-box}' +
      '}' +
      '@media (max-width:380px){header img[src*="logo"],header .site-logo-img{max-width:88px !important}}';
    (document.head || document.documentElement).appendChild(style);
  }
  ensureHeaderCallCss();

  function ensureTapTargetCss() {
    if (document.getElementById('scws-tap-css')) return;
    var style = document.createElement('style');
    style.id = 'scws-tap-css';
    style.textContent =
      '@media (max-width:767px){' +
      'footer a,.rw-all a,.homepage-trust-pills a,a[href$="recent-work/"],a[href*="google.com/maps"],.bg-gray-50.border-b a{min-height:44px;display:inline-flex;align-items:center;box-sizing:border-box}' +
      'details>summary{min-height:44px;display:flex;align-items:center}' +
      '.filter-btn,#town-filter,button[aria-label="Previous reviews"],button[aria-label="Next reviews"]{min-height:44px;min-width:44px;box-sizing:border-box}' +
      '#carousel-dots{gap:0}' +
      '#carousel-dots button{width:44px;height:44px;min-width:44px;min-height:44px;padding:0;background:transparent !important;position:relative;display:inline-flex;align-items:center;justify-content:center}' +
      '#carousel-dots button::after{content:"";width:12px;height:12px;border-radius:9999px;background:#d1d5db;display:block}' +
      '#carousel-dots button.bg-accent::after{background:#4e9271}' +
      'input[name="sms_consent"]{width:44px !important;height:44px !important;min-width:44px;min-height:44px}' +
      '}';
    (document.head || document.documentElement).appendChild(style);
  }
  ensureTapTargetCss();

  function getStoredConsent() {
    try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  }

  function ensureGtag() {
    window.dataLayer = window.dataLayer || [];
    if (typeof window.gtag !== 'function') {
      window.gtag = function () { window.dataLayer.push(arguments); };
    }
  }

  function consentParams(granted) {
    var state = granted ? 'granted' : 'denied';
    return {
      analytics_storage: state,
      ad_storage: state,
      ad_user_data: state,
      ad_personalization: state
    };
  }

  function applyDisableFlag(granted) {
    window['ga-disable-' + GA_ID] = !granted;
  }

  // Immediate: Consent Mode default before any gtag config / page_view
  ensureGtag();
  var stored = getStoredConsent();
  if (stored === 'rejected') {
    gtag('consent', 'default', consentParams(false));
    applyDisableFlag(false);
  } else {
    // First visit and already-accepted: keep tracking on (CA site, not GDPR opt-in).
    gtag('consent', 'default', consentParams(true));
    applyDisableFlag(true);
  }

  function updateConsent(value) {
    var granted = value === 'accepted';
    ensureGtag();
    gtag('consent', 'update', consentParams(granted));
    applyDisableFlag(granted);
  }

  function stickyVisible() {
    var sticky = document.getElementById('sticky-cta');
    if (!sticky) return false;
    if (window.matchMedia && window.matchMedia('(min-width: 1024px)').matches) return false;
    var style = window.getComputedStyle(sticky);
    return style.display !== 'none' && style.visibility !== 'hidden';
  }

  function isMobileViewport() {
    return !(window.matchMedia && window.matchMedia('(min-width: 1024px)').matches);
  }

  function positionBanner(banner) {
    if (!banner || banner.style.display === 'none') return;
    banner.style.top = 'auto';
    var sticky = document.getElementById('sticky-cta');
    if (stickyVisible() && sticky) {
      sticky.style.zIndex = '1100';
      banner.style.bottom = sticky.offsetHeight + 'px';
    } else {
      banner.style.bottom = '0';
    }
  }

  function notify() {
    document.dispatchEvent(new CustomEvent('scws-overlays-changed'));
  }

  function mountBanner() {
    if (document.getElementById('scws-cookie-banner')) return null;

    var banner = document.createElement('div');
    banner.id = 'scws-cookie-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Cookie consent');
    // Bottom from the first paint — never top. One row. Buttons ≥44px.
    banner.style.position = 'fixed';
    banner.style.left = '0';
    banner.style.right = '0';
    banner.style.top = 'auto';
    banner.style.bottom = '0';
    banner.style.background = 'rgba(15,23,42,0.96)';
    banner.style.color = '#fff';
    banner.style.padding = '6px 10px';
    banner.style.zIndex = '1000';
    banner.style.fontFamily = 'Inter,sans-serif';
    banner.style.display = 'flex';
    banner.style.alignItems = 'center';
    banner.style.justifyContent = 'space-between';
    banner.style.gap = '8px';
    banner.style.flexWrap = 'nowrap';
    banner.style.minHeight = '52px';
    banner.style.boxSizing = 'border-box';
    banner.innerHTML =
      '<p style="margin:0;font-size:13px;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1;min-width:0;">Cookies help us run the site. <a href="/privacy-policy.html" style="color:#86efac;text-decoration:underline;">Privacy</a></p>' +
      '<span style="display:flex;gap:8px;flex-shrink:0;">' +
      '<button id="acceptCookies" type="button">Accept</button>' +
      '<button id="rejectCookies" type="button">Reject</button>' +
      '</span>';
    function styleBtn(el, bg) {
      el.style.background = bg;
      el.style.color = '#fff';
      el.style.border = 'none';
      el.style.minHeight = '44px';
      el.style.minWidth = '88px';
      el.style.padding = '10px 16px';
      el.style.cursor = 'pointer';
      el.style.borderRadius = '8px';
      el.style.fontWeight = '700';
      el.style.fontSize = '16px';
    }
    styleBtn(banner.querySelector('#acceptCookies'), '#4e9271');
    styleBtn(banner.querySelector('#rejectCookies'), '#dc2626');
    document.body.appendChild(banner);
    positionBanner(banner);
    notify();

    window.addEventListener('resize', function () { positionBanner(banner); notify(); });

    function dismiss(value) {
      localStorage.setItem('cookieConsent', value);
      updateConsent(value);
      banner.style.display = 'none';
      notify();
    }

    document.getElementById('acceptCookies').addEventListener('click', function () {
      dismiss('accepted');
    });
    document.getElementById('rejectCookies').addEventListener('click', function () {
      dismiss('rejected');
    });
    return banner;
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (getStoredConsent()) return;

    if (isMobileViewport()) {
      var shown = false;
      function onFirstScroll() {
        if (shown || window.scrollY < 12) return;
        shown = true;
        window.removeEventListener('scroll', onFirstScroll);
        mountBanner();
      }
      window.addEventListener('scroll', onFirstScroll, { passive: true });
      return;
    }

    mountBanner();
  });
})();
