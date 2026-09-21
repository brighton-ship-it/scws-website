/**
 * SCWS GA4 A/B test harness
 *
 * - 50/50 bucket into control | variant
 * - Persist 30 days in a first-party cookie
 * - Set GA4 user properties exp_id and exp_var
 * - Fire experiment_view once per session
 * - Expose window.scwsAb = { id, variant }
 * - Decorate generate_lead, call_click, text_click, and
 *   ads_conversion_submit_lead_form with exp_id / exp_var
 * - No-op safely if gtag is missing (bot filter)
 *
 * Active experiment: exp_homepage_form (homepage #contact-form only)
 *   control: current full form (HTML, unchanged)
 *   variant: name, phone, and a no-water / emergency choice;
 *            address, city, email, and message stay in the DOM but
 *            are optional and hidden
 *
 * Retired: exp_emergency_cta. The homepage emergency bar stays Call-only.
 */
(function () {
  'use strict';

  var EXP_ID = 'exp_homepage_form';
  var COOKIE_NAME = 'scws_ab';
  var COOKIE_DAYS = 30;
  var VIEW_KEY = 'scws_ab_view';
  var ENRICH_EVENTS = {
    generate_lead: true,
    call_click: true,
    text_click: true,
    ads_conversion_submit_lead_form: true
  };
  var COLLAPSE_IDS = ['email', 'address', 'city', 'message'];

  var assignment;
  var gaBooted = false;

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
    var next = { id: EXP_ID, variant: variant };
    writeCookie(COOKIE_NAME, EXP_ID + '.' + variant, COOKIE_DAYS);
    return next;
  }

  function decorateParams(params) {
    var next = params ? params : {};
    var id = assignment.id;
    var variant = assignment.variant;
    if (window.scwsAb && typeof window.scwsAb === 'object') {
      if (window.scwsAb.id) id = window.scwsAb.id;
      if (window.scwsAb.variant) variant = window.scwsAb.variant;
    }
    if (next.exp_id == null) next.exp_id = id;
    if (next.exp_var == null) next.exp_var = variant;
    return next;
  }

  function ensureWrap() {
    if (!hasGtag()) return;
    if (!window.gtag.__scwsAbWrapped) {
      var original = window.gtag;
      var wrapped = function () {
        var args = Array.prototype.slice.call(arguments);
        try {
          if (args[0] === 'event' && ENRICH_EVENTS[args[1]]) {
            args[2] = decorateParams(args[2]);
          }
        } catch (e) {}
        return original.apply(this, args);
      };
      wrapped.__scwsAbWrapped = true;
      window.gtag = wrapped;
    }
    if (gaBooted) return;
    gaBooted = true;
    setUserProperties();
    fireExperimentView();
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

  function isHomepage() {
    var path = (window.location.pathname || '/').replace(/index\.html$/, '').replace(/\/$/, '');
    return path === '' || path === '/';
  }

  function collapseOptionalField(id) {
    var field = document.getElementById(id);
    if (!field) return;
    field.required = false;
    field.removeAttribute('required');
    var wrap = field.parentNode;
    if (!wrap || wrap.tagName === 'FORM') return;
    wrap.style.display = 'none';
    wrap.setAttribute('hidden', '');
    wrap.setAttribute('aria-hidden', 'true');
    wrap.setAttribute('data-scws-ab-collapsed', '1');
  }

  function applyHomepageForm() {
    if (assignment.variant !== 'variant') return;
    var form = document.getElementById('contact-form');
    if (!form || form.getAttribute('data-scws-ab-form') === 'applied') return;
    form.setAttribute('data-scws-ab-form', 'applied');
    form.setAttribute('data-scws-ab-var', 'variant');

    for (var i = 0; i < COLLAPSE_IDS.length; i++) collapseOptionalField(COLLAPSE_IDS[i]);

    var service = document.getElementById('service');
    if (service) service.value = 'emergency';

    var stack = form.querySelector('.space-y-4');
    if (!stack || document.getElementById('scws-emergency-first')) return;

    var box = document.createElement('div');
    box.id = 'scws-ab-emergency';
    box.style.cssText = 'background:#fef2f2;border:2px solid #dc2626;border-radius:0.75rem;padding:0.875rem 1rem;';
    box.innerHTML =
      '<label style="display:flex;align-items:flex-start;gap:0.75rem;cursor:pointer;">' +
        '<input type="checkbox" id="scws-emergency-first" checked ' +
          'style="margin-top:0.2rem;width:1.25rem;height:1.25rem;flex:0 0 auto;">' +
        '<span>' +
          '<span style="display:block;font-weight:700;color:#991b1b;">No water / emergency</span>' +
          '<span style="display:block;font-weight:500;color:#7f1d1d;font-size:0.875rem;margin-top:0.15rem;">' +
            'Checked sends this as emergency service (no water). Uncheck to choose a different service below.' +
          '</span>' +
        '</span>' +
      '</label>';
    stack.insertBefore(box, stack.firstChild);

    var checkbox = document.getElementById('scws-emergency-first');
    if (checkbox && service) {
      checkbox.addEventListener('change', function () {
        if (checkbox.checked) service.value = 'emergency';
        else if (service.value === 'emergency') service.value = '';
      });
      service.addEventListener('change', function () {
        checkbox.checked = service.value === 'emergency';
      });
      // Capture phase runs before the onsubmit handler reads FormData.
      form.addEventListener('submit', function () {
        if (checkbox.checked) service.value = 'emergency';
      }, true);
    }
  }

  function applyExperiment() {
    if (!isHomepage()) return;
    applyHomepageForm();
  }

  assignment = getAssignment();
  window.scwsAb = { id: assignment.id, variant: assignment.variant };

  ensureWrap();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      ensureWrap();
      applyExperiment();
    });
  } else {
    applyExperiment();
  }
  window.addEventListener('load', ensureWrap);
})();
