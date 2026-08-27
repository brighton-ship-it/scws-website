/**
 * Shared GA4 lead events after a successful CRM POST.
 *
 * Prefer /js/scws-tracking.js as the page bootstrap. This file stays as a
 * compatibility helper for pages that still include it on its own.
 *
 * Fires generate_lead and ads_conversion_submit_lead_form.
 * Sets enhanced-conversions user_data when email / phone are provided.
 * Attaches exp_id / exp_var when window.scwsAb exists (ab.js also
 * enriches these names via ENRICH_EVENTS when it is loaded).
 *
 * Ads form conversion still needs a real Google Ads label created in Ads.
 * Do not send form leads to AW-490838730/aFiRCMDlofAbEMq1huoB (phone/calls only).
 * Do not invent placeholder Ads send_to suffixes.
 */
(function (root) {
  'use strict';

  // Real AW-490838730/<label> will be dropped in when created in Google Ads.
  var AW_FORM_SEND_TO = root.AW_FORM_SEND_TO != null ? root.AW_FORM_SEND_TO : null;
  var AW_PHONE_SEND_TO = 'AW-490838730/aFiRCMDlofAbEMq1huoB';

  function assign(target, source) {
    if (!source) return target;
    for (var key in source) {
      if (Object.prototype.hasOwnProperty.call(source, key)) {
        target[key] = source[key];
      }
    }
    return target;
  }

  function abParams() {
    var extra = {};
    var ab = root.scwsAb;
    if (!ab || typeof ab !== 'object') return extra;
    if (ab.id) extra.exp_id = ab.id;
    if (ab.variant) extra.exp_var = ab.variant;
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

  function trackLeadFormSuccess(params, user) {
    if (typeof root.gtag !== 'function') return;
    setEnhancedUserData(user);
    var payload = assign({ event_category: 'engagement' }, params);
    if (payload.send_to === AW_PHONE_SEND_TO) delete payload.send_to;
    var ab = abParams();
    if (payload.exp_id == null && ab.exp_id) payload.exp_id = ab.exp_id;
    if (payload.exp_var == null && ab.exp_var) payload.exp_var = ab.exp_var;
    root.gtag('event', 'generate_lead', payload);
    root.gtag('event', 'ads_conversion_submit_lead_form', payload);
    if (AW_FORM_SEND_TO) {
      var adsPayload = assign({}, payload);
      adsPayload.send_to = AW_FORM_SEND_TO;
      if (adsPayload.send_to !== AW_PHONE_SEND_TO) {
        root.gtag('event', 'conversion', adsPayload);
      }
    }
  }

  if (typeof root.scwsTrackLeadFormSuccess !== 'function') {
    root.scwsTrackLeadFormSuccess = trackLeadFormSuccess;
  }
  if (root.AW_FORM_SEND_TO === undefined) {
    root.AW_FORM_SEND_TO = AW_FORM_SEND_TO;
  }
})(typeof window !== 'undefined' ? window : this);
