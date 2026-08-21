/* Cookie Consent Banner for SCWS
 * Sits above the mobile sticky Call/Text/Estimate bar so the call CTA
 * stays fully visible and tappable.
 *
 * Consent Mode: this file must load BEFORE gtag.js so the default
 * (granted, or denied if cookieConsent is already rejected) is set first.
 */

(function () {
  var STORAGE_KEY = 'cookieConsent';
  var GA_ID = 'G-5LL1YRWT5T';

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
    return {
      analytics_storage: granted ? 'granted' : 'denied',
      ad_storage: granted ? 'granted' : 'denied'
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

  function positionBanner(banner) {
    if (!banner || banner.style.display === 'none') return;
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

  document.addEventListener('DOMContentLoaded', function () {
    if (localStorage.getItem('cookieConsent')) return;

    var banner = document.createElement('div');
    banner.id = 'scws-cookie-banner';
    banner.style.cssText = 'position:fixed;left:0;right:0;background:rgba(15,23,42,0.96);color:#fff;padding:6px 10px;z-index:1000;font-family:Inter,sans-serif;display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:nowrap;min-height:52px;box-sizing:border-box;';
    banner.innerHTML =
      '<p style="margin:0;font-size:13px;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1;min-width:0;">Cookies help us run the site. <a href="/privacy-policy.html" style="color:#86efac;text-decoration:underline;">Privacy</a></p>' +
      '<span style="display:flex;gap:8px;flex-shrink:0;">' +
      '<button id="acceptCookies" type="button" style="background:#4e9271;color:#fff;border:none;min-height:44px;min-width:88px;padding:10px 16px;cursor:pointer;border-radius:8px;font-weight:700;font-size:16px;">Accept</button>' +
      '<button id="rejectCookies" type="button" style="background:#dc2626;color:#fff;border:none;min-height:44px;min-width:88px;padding:10px 16px;cursor:pointer;border-radius:8px;font-weight:700;font-size:16px;">Reject</button>' +
      '</span>';
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
  });
})();
