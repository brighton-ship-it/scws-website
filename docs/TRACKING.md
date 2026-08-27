# SCWS tracking dictionary

First-party measurement for scwellservice.com. No GTM. One bootstrap:

`cookie-consent.js` → `ga4-filter.js` (or the reverse; both before gtag) → `gtag.js` → **`js/scws-tracking.js`**.

| Property | ID |
| --- | --- |
| GA4 | `G-5LL1YRWT5T` |
| Google Ads | `AW-490838730` |
| Ads phone / call conversion | `AW-490838730/aFiRCMDlofAbEMq1huoB` |
| Ads form conversion | **none yet** — `AW_FORM_SEND_TO` is `null` until a real `AW-490838730/<label>` is created in Google Ads |

Phone forwarding number: `(760) 440-8520`. The bootstrap configures `phone_conversion_number` once so Ads can replace the **voice** `tel:` node. Do not send form leads to the phone label.

Consent Mode v2 uses the existing cookie banner (`analytics_storage`, `ad_storage`, `ad_user_data`, `ad_personalization`). Default stays granted unless the visitor already rejected; no new consent UX.

## Events

| Event | When it fires | Key event | Ads | Notes |
| --- | --- | --- | --- | --- |
| `call_click` | Visitor taps a `tel:` link (`js/call-tracking.js`) | Yes | Phone conversion only when `traffic_source === 'google_ads'` | One GA4 event per tap. Organic is a parameter, not a second event. |
| `text_click` | Visitor taps an `sms:` link (`js/call-tracking.js`) | No | No | Never send the phone Ads label on SMS. |
| `generate_lead` | CRM (or booking API) returns success after a real form / exit-intent submit | Yes | No Ads `send_to` today | Honeypot skip. Failure / non-200 does not fire. |
| `ads_conversion_submit_lead_form` | Same success path as `generate_lead` | Yes | No Ads `send_to` until `AW_FORM_SEND_TO` is a real label | Same payload as `generate_lead`. Never the phone label. |
| `experiment_view` | Homepage A/B harness (`js/ab.js`) once per session | No | No | Also sets `exp_id` / `exp_var` user properties. |
| `estimate_click` | Estimate / contact CTA (`scwsTrackEstimateClick` or homepage helper) | No | No | Click is not a lead. |

Form success also sets enhanced conversions `user_data` (`email`, `phone_number`) when those fields were collected. gtag hashes them. Do not log PII to the console.

Retired / never reintroduce: `click_to_call`, `seo_call_conversion`, `contact_page`, invented Ads suffixes such as `contact_form_submit`, `form_submit`, `phone_click`.

## Next layer (not this PR)

Booked-job / offline conversion upload from the CRM is the next measurement layer. Website tags stop at successful form submit and qualified call clicks.
