/**
 * Shared GA4 lead events after a successful CRM POST.
 *
 * Fires generate_lead and ads_conversion_submit_lead_form.
 * Attaches exp_id / exp_var when window.scwsAb exists (ab.js also
 * enriches these names via ENRICH_EVENTS when it is loaded).
 *
 * Ads form conversion still needs a real Google Ads label created in Ads.
 * Do not send form leads to AW-490838730/aFiRCMDlofAbEMq1huoB (phone/calls only).
 * Do not invent placeholder send_to values such as contact_form_submit.
 */
(function (root) {
  'use strict';

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

  function trackLeadFormSuccess(params) {
    if (typeof root.gtag !== 'function') return;
    var payload = assign({ event_category: 'engagement' }, params);
    var ab = abParams();
    if (payload.exp_id == null && ab.exp_id) payload.exp_id = ab.exp_id;
    if (payload.exp_var == null && ab.exp_var) payload.exp_var = ab.exp_var;
    root.gtag('event', 'generate_lead', payload);
    root.gtag('event', 'ads_conversion_submit_lead_form', payload);
  }

  root.scwsTrackLeadFormSuccess = trackLeadFormSuccess;
})(typeof window !== 'undefined' ? window : this);
