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
 * Active experiment: exp_homepage_form (homepage #contact-form only)
 *   control: today's full form (name, phone, email, address, city,
 *            service, message, sms consent)
 *   variant: name + phone required; service defaults to Emergency
 *            Service; email, address, city, and message stay in the
 *            DOM but are hidden and not required. Empty address/city
 *            still use handleFormSubmit defaults.
 *
 * One experiment at a time. exp_emergency_cta is retired (no lift).
 * The emergency bar stays Call-only in HTML — this file does not
 * mutate it.
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

  // Longer fields hidden on the variant. Left in the DOM so CRM and
  // Formspree still receive them; handleFormSubmit supplies defaults
  // when address/city/email/message are empty.
  var VARIANT_HIDDEN_FIELDS = ['email', 'address', 'city', 'message'];

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

  function isHomepage() {
    var path = (window.location.pathname || '/').replace(/index\.html$/, '').replace(/\/$/, '');
    return path === '' || path === '/';
  }

  function hideLongField(form, name) {
    var field = form.querySelector('[name="' + name + '"]');
    if (!field) return;
    field.required = false;
    field.removeAttribute('required');
    var wrap = field.parentElement;
    if (!wrap || wrap === form) return;
    wrap.classList.add('hidden');
    wrap.setAttribute('hidden', '');
    wrap.setAttribute('aria-hidden', 'true');
  }

  function applyEmergencyFirst(form) {
    var service = form.querySelector('select[name="service"]');
    if (!service) return;
    var emergency = service.querySelector('option[value="emergency"]');
    if (!emergency) return;
    if (service.options[0] !== emergency) {
      service.insertBefore(emergency, service.options[0]);
    }
    service.value = 'emergency';
  }

  function applyFormVariant(form) {
    if (!form || form.getAttribute('data-scws-ab') === 'applied') return;
    form.setAttribute('data-scws-ab', 'applied');
    var variant = window.scwsAb && window.scwsAb.variant;
    form.setAttribute('data-scws-ab-var', variant || '');
    if (variant !== 'variant') return;

    for (var i = 0; i < VARIANT_HIDDEN_FIELDS.length; i++) {
      hideLongField(form, VARIANT_HIDDEN_FIELDS[i]);
    }
    applyEmergencyFirst(form);
  }

  function applyExperiment() {
    if (!isHomepage()) return;
    applyFormVariant(document.getElementById('contact-form'));
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
