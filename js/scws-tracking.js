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
 *   - sets enhanced-conversions user_data (email, phone_number) when provided
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

  function setEnhancedUserData(user) {
    if (!user || typeof user !== 'object') return;
    if (typeof root.gtag !== 'function') return;
    var email = trimValue(user.email);
    var phone = trimValue(user.phone_number || user.phone);
    if (!email && !phone) return;
    var userData = {};
    if (email) userData.email = email;
    if (phone) userData.phone_number = phone;
    root.gtag('set', 'user_data', userData);
  }

  function isPhoneSendTo(value) {
    if (!value) return false;
    var text = String(value);
    return text.indexOf(AW_PHONE_SEND_TO) !== -1 || text.indexOf('aFiRCMDlofAbEMq1huoB') !== -1;
  }

  function trackLeadFormSuccess(params, user) {
    ensureGtag();
    if (typeof root.gtag !== 'function') return;

    setEnhancedUserData(user);

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
    root.gtag('config', AW_PHONE_SEND_TO, {
      phone_conversion_number: PHONE_CONVERSION_NUMBER
    });
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
