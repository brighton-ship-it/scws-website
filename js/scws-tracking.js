/**
 * SCWS first-party tracking bootstrap.
 *
 * Load after cookie-consent.js / ga4-filter.js (and the gtag.js snippet).
 * Idempotent: safe if this file is included twice.
 *
 * Configures G-5LL1YRWT5T and AW-490838730 once, plus Ads phone-swap
 * (forwarding-number replacement on the voice tel: node).
 *
 * Form leads: window.scwsTrackLeadFormSuccess(params, user)
 *   - normalizes email and US phone, SHA-256 hex-hashes them with crypto.subtle,
 *     and sets user_data {sha256_email_address, sha256_phone_number} before
 *     the conversion fires
 *   - falls back to plain normalized email / phone_number if hashing is unavailable
 *   - fires generate_lead + ads_conversion_submit_lead_form
 *   - attaches exp_id / exp_var from window.scwsAb
 *   - NEVER send_to the phone/call label
 *   - Ads form conversion send_to AW_FORM_SEND_TO when it is set
 *
 * While AW_FORM_SEND_TO is null/empty, do not fire a fake Ads conversion.
 */
(function (root) {
  'use strict';

  var GA_ID = 'G-5LL1YRWT5T';
  var AW_ID = 'AW-490838730';
  var AW_PHONE_SEND_TO = 'AW-490838730/aFiRCMDlofAbEMq1huoB';
  var PHONE_CONVERSION_NUMBER = '(760) 440-8520';

  // Website form lead. Do not invent placeholder send_to suffixes.
  var AW_FORM_SEND_TO = 'AW-490838730/nFeMCN_cyegcEMq1huoB';

  function assign(target, source) {
    if (!source) return target;
    for (var key in source) {
      if (Object.prototype.hasOwnProperty.call(source, key)) {
        target[key] = source[key];
      }
    }
    return target;
  }

  function ensureGtag() {
    root.dataLayer = root.dataLayer || [];
    if (typeof root.gtag !== 'function') {
      root.gtag = function () { root.dataLayer.push(arguments); };
    }
  }

  function abParams() {
    var extra = {};
    var ab = root.scwsAb;
    if (!ab || typeof ab !== 'object') return extra;
    if (ab.id || ab.expId || ab.experimentId) {
      extra.exp_id = ab.id || ab.expId || ab.experimentId;
    }
    if (ab.variant || ab.expVar || ab.exp_var) {
      extra.exp_var = ab.variant || ab.expVar || ab.exp_var;
    }
    return extra;
  }

  function trimValue(value) {
    if (value == null) return '';
    return String(value).replace(/^\s+|\s+$/g, '');
  }

  // Lowercase, trim, and drop dots in the local part for gmail.com / googlemail.com.
  function normalizeEmail(value) {
    var email = trimValue(value).toLowerCase();
    if (!email) return '';
    var at = email.indexOf('@');
    if (at === -1) return email;
    var local = email.slice(0, at);
    var domain = email.slice(at + 1);
    if (domain === 'gmail.com' || domain === 'googlemail.com') {
      local = local.replace(/\./g, '');
    }
    return local + '@' + domain;
  }

  // US numbers only: 10 digits, or 11 digits with a leading 1, as +1XXXXXXXXXX.
  function normalizeUsPhone(value) {
    var digits = trimValue(value).replace(/\D/g, '');
    if (!digits) return '';
    if (digits.length === 11 && digits.charAt(0) === '1') {
      digits = digits.slice(1);
    }
    if (digits.length !== 10) return '';
    return '+1' + digits;
  }

  function hashingAvailable() {
    try {
      return !!(
        root.crypto &&
        root.crypto.subtle &&
        typeof root.crypto.subtle.digest === 'function' &&
        typeof root.TextEncoder === 'function'
      );
    } catch (err) {
      return false;
    }
  }

  function sha256Hex(text) {
    var bytes = new root.TextEncoder().encode(text);
    return root.crypto.subtle.digest('SHA-256', bytes).then(function (buffer) {
      var view = new Uint8Array(buffer);
      var hex = '';
      for (var i = 0; i < view.length; i++) {
        var pair = view[i].toString(16);
        hex += pair.length < 2 ? '0' + pair : pair;
      }
      return hex;
    });
  }

  function plainUserData(email, phone) {
    var userData = {};
    if (email) userData.email = email;
    if (phone) userData.phone_number = phone;
    return userData;
  }

  // Resolves after user_data is set. Returns null when the set is synchronous
  // (no identifiers, or hashing is unavailable and the plain values were set).
  function setEnhancedUserData(user) {
    if (!user || typeof user !== 'object') return null;
    if (typeof root.gtag !== 'function') return null;
    var email = normalizeEmail(user.email);
    var phone = normalizeUsPhone(user.phone_number || user.phone);
    if (!email && !phone) return null;

    if (!hashingAvailable()) {
      root.gtag('set', 'user_data', plainUserData(email, phone));
      return null;
    }

    try {
      var jobs = [];
      if (email) {
        jobs.push(sha256Hex(email).then(function (hex) {
          return { key: 'sha256_email_address', value: hex };
        }));
      }
      if (phone) {
        jobs.push(sha256Hex(phone).then(function (hex) {
          return { key: 'sha256_phone_number', value: hex };
        }));
      }

      return Promise.all(jobs).then(function (parts) {
        var userData = {};
        for (var i = 0; i < parts.length; i++) {
          userData[parts[i].key] = parts[i].value;
        }
        root.gtag('set', 'user_data', userData);
      }).catch(function () {
        root.gtag('set', 'user_data', plainUserData(email, phone));
      });
    } catch (err) {
      root.gtag('set', 'user_data', plainUserData(email, phone));
      return null;
    }
  }

  function isPhoneSendTo(value) {
    if (!value) return false;
    var text = String(value);
    return text.indexOf(AW_PHONE_SEND_TO) !== -1 || text.indexOf('aFiRCMDlofAbEMq1huoB') !== -1;
  }

  function trackLeadFormSuccess(params, user) {
    ensureGtag();
    if (typeof root.gtag !== 'function') return;

    function fire() {
      var payload = assign({ event_category: 'engagement' }, params);
      if (isPhoneSendTo(payload.send_to)) delete payload.send_to;
      var ab = abParams();
      if (payload.exp_id == null && ab.exp_id) payload.exp_id = ab.exp_id;
      if (payload.exp_var == null && ab.exp_var) payload.exp_var = ab.exp_var;

      root.gtag('event', 'generate_lead', payload);
      root.gtag('event', 'ads_conversion_submit_lead_form', payload);

      if (AW_FORM_SEND_TO) {
        var adsPayload = assign({}, payload);
        adsPayload.send_to = AW_FORM_SEND_TO;
        if (!isPhoneSendTo(adsPayload.send_to)) {
          root.gtag('event', 'conversion', adsPayload);
        }
      }
    }

    var pending = setEnhancedUserData(user);
    if (pending && typeof pending.then === 'function') {
      return pending.then(fire);
    }
    fire();
  }

  function trackEstimateClick(params) {
    ensureGtag();
    if (typeof root.gtag !== 'function') return;
    var payload = assign({ event_category: 'engagement' }, params);
    var ab = abParams();
    if (payload.exp_id == null && ab.exp_id) payload.exp_id = ab.exp_id;
    if (payload.exp_var == null && ab.exp_var) payload.exp_var = ab.exp_var;
    root.gtag('event', 'estimate_click', payload);
  }

  function configureOnce() {
    if (root.__scwsTrackingConfigured) return;
    root.__scwsTrackingConfigured = true;
    ensureGtag();
    root.gtag('js', new Date());
    root.gtag('config', GA_ID);
    root.gtag('config', AW_ID);
    // Phone swap is handled first-party in call-tracking.js (Twilio ads number),
    // so Google's own number swap is not configured here (avoids two different numbers).
    root.gtag('config', AW_PHONE_SEND_TO);
  }

  function expose() {
    root.AW_FORM_SEND_TO = AW_FORM_SEND_TO;
    root.scwsTrackLeadFormSuccess = trackLeadFormSuccess;
    root.scwsTrackEstimateClick = trackEstimateClick;
    root.scwsTracking = {
      GA_ID: GA_ID,
      AW_ID: AW_ID,
      AW_PHONE_SEND_TO: AW_PHONE_SEND_TO,
      AW_FORM_SEND_TO: AW_FORM_SEND_TO,
      configure: configureOnce,
      trackLeadFormSuccess: trackLeadFormSuccess,
      trackEstimateClick: trackEstimateClick
    };
  }

  if (root.__scwsTrackingBooted) {
    expose();
    return;
  }
  root.__scwsTrackingBooted = true;
  expose();
  configureOnce();
})(typeof window !== 'undefined' ? window : this);
