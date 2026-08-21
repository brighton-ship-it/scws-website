/**
 * SCWS GA4 A/B test harness
 *
 * - 50/50 bucket into control | variant
 * - Persist 30 days in a first-party cookie
 * - Set GA4 user properties exp_id and exp_var
 * - Fire experiment_view once per session
 * - Expose window.scwsAb = { id, variant }
 * - No-op safely if gtag is missing (bot filter)
 *
 * Active experiment: exp_emergency_cta (homepage emergency bar only)
 *   control: red emergency top bar, Call only
 *   variant: same bar, equal Call + Text buttons
 */
(function () {
  'use strict';

  var EXP_ID = 'exp_emergency_cta';
  var COOKIE_NAME = 'scws_ab';
  var COOKIE_DAYS = 30;
  var VIEW_KEY = 'scws_ab_view';
  var ENRICH_EVENTS = {
    generate_lead: true,
    call_click: true,
    text_click: true,
    ads_conversion_submit_lead_form: true
  };

  var VOICE_DISPLAY = '(760) 440-8520';
  var VOICE_TEL = 'tel:7604408520';
  var TEXT_DISPLAY = '(760) 219-5877';
  var TEXT_SMS = 'sms:7602195877';

  function hasGtag() {
    return typeof window.gtag === 'function';
  }

  function readCookie(name) {
    var parts = ('; ' + document.cookie).split('; ' + name + '=');
    if (parts.length < 2) return '';
    return decodeURIComponent(parts.pop().split(';').shift() || '');
  }

  function writeCookie(name, value, days) {
    var maxAge = Math.round(days * 24 * 60 * 60);
    var cookie = name + '=' + encodeURIComponent(value) +
      '; Max-Age=' + maxAge +
      '; Path=/' +
      '; SameSite=Lax';
    if (location.protocol === 'https:') cookie += '; Secure';
    document.cookie = cookie;
  }

  function parseAssignment(raw) {
    if (!raw) return null;
    var sep = raw.indexOf('.');
    if (sep < 1) return null;
    var id = raw.slice(0, sep);
    var variant = raw.slice(sep + 1);
    if (id !== EXP_ID) return null;
    if (variant !== 'control' && variant !== 'variant') return null;
    return { id: id, variant: variant };
  }

  function forcedVariant() {
    try {
      var params = new URLSearchParams(window.location.search);
      var force = params.get('scws_ab');
      if (force === 'control' || force === 'variant') return force;
    } catch (e) {}
    return '';
  }

  function assignVariant() {
    var force = forcedVariant();
    if (force) return force;
    return Math.random() < 0.5 ? 'control' : 'variant';
  }

  function getAssignment() {
    var existing = parseAssignment(readCookie(COOKIE_NAME));
    var force = forcedVariant();
    if (existing && !force) return existing;
    var variant = force || (existing && existing.variant) || assignVariant();
    var assignment = { id: EXP_ID, variant: variant };
    writeCookie(COOKIE_NAME, EXP_ID + '.' + variant, COOKIE_DAYS);
    return assignment;
  }

  function decorateParams(params) {
    var next = params ? params : {};
    if (next.exp_id == null) next.exp_id = assignment.id;
    if (next.exp_var == null) next.exp_var = assignment.variant;
    return next;
  }

  function wrapGtag() {
    var original = window.gtag;
    window.gtag = function () {
      var args = Array.prototype.slice.call(arguments);
      try {
        if (args[0] === 'event' && ENRICH_EVENTS[args[1]]) {
          args[2] = decorateParams(args[2]);
        }
      } catch (e) {}
      if (typeof original === 'function') {
        return original.apply(this, args);
      }
    };
  }

  function setUserProperties() {
    if (!hasGtag()) return;
    try {
      window.gtag('set', 'user_properties', {
        exp_id: assignment.id,
        exp_var: assignment.variant
      });
    } catch (e) {}
  }

  function fireExperimentView() {
    if (!hasGtag()) return;
    var token = assignment.id + '.' + assignment.variant;
    try {
      if (sessionStorage.getItem(VIEW_KEY) === token) return;
      sessionStorage.setItem(VIEW_KEY, token);
    } catch (e) {}
    try {
      window.gtag('event', 'experiment_view', {
        exp_id: assignment.id,
        exp_var: assignment.variant
      });
    } catch (e) {}
  }

  function isEmergencyBar(el) {
    if (!el || !el.querySelector) return false;
    if (el.id === 'sticky-cta' || el.closest('#sticky-cta')) return false;
    if (el.closest('header')) return false;
    var text = el.textContent || '';
    if (text.indexOf('No Water?') === -1) return false;
    return !!el.querySelector('a[href^="tel:"]');
  }

  function findEmergencyBars() {
    var found = [];
    var marked = document.getElementById('scws-emergency-cta');
    if (marked && isEmergencyBar(marked)) found.push(marked);

    var nodes = document.querySelectorAll('.from-red-600, .bg-gradient-to-r');
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (found.indexOf(el) !== -1) continue;
      if (isEmergencyBar(el)) found.push(el);
    }
    return found;
  }

  function applyVariant(bar) {
    if (!bar || bar.getAttribute('data-scws-ab') === 'applied') return;
    bar.setAttribute('data-scws-ab', 'applied');
    bar.setAttribute('data-scws-ab-var', assignment.variant);
    if (assignment.variant !== 'variant') return;
    if (bar.querySelector('a[href^="sms:"]')) return;

    var callLink = bar.querySelector('a[href^="tel:"]');
    if (!callLink) return;

    // Keep the existing tel: node so Google Ads can still swap the voice number.
    if (!callLink.getAttribute('href')) callLink.setAttribute('href', VOICE_TEL);
    callLink.textContent = 'Call ' + VOICE_DISPLAY;
    callLink.style.minWidth = '11.5rem';
    callLink.style.textAlign = 'center';

    var textLink = callLink.cloneNode(false);
    textLink.setAttribute('href', TEXT_SMS);
    textLink.removeAttribute('onclick');
    textLink.textContent = 'Text ' + TEXT_DISPLAY;
    textLink.title = 'Text-only line: ' + TEXT_DISPLAY;
    textLink.style.minWidth = '11.5rem';
    textLink.style.textAlign = 'center';

    if (callLink.parentNode) {
      callLink.parentNode.insertBefore(textLink, callLink.nextSibling);
    }
  }

  function isHomepage() {
    var path = (window.location.pathname || '/').replace(/index\.html$/, '').replace(/\/$/, '');
    return path === '' || path === '/';
  }

  function applyExperiment() {
    if (!isHomepage()) return;
    var bars = findEmergencyBars();
    for (var i = 0; i < bars.length; i++) applyVariant(bars[i]);
  }

  var assignment = getAssignment();
  window.scwsAb = { id: assignment.id, variant: assignment.variant };

  if (hasGtag()) {
    wrapGtag();
    setUserProperties();
    fireExperimentView();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyExperiment);
  } else {
    applyExperiment();
  }
})();
