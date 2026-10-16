/**
 * Unit tests for the GA4 A/B harness and SMS click tracking.
 * Run: node js/ab.test.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var assert = require('assert');
var { JSDOM } = require('jsdom');

var abSrc = fs.readFileSync(path.join(__dirname, 'ab.js'), 'utf8');
var callSrc = fs.readFileSync(path.join(__dirname, 'call-tracking.js'), 'utf8');
var trackingSrc = fs.readFileSync(path.join(__dirname, 'scws-tracking.js'), 'utf8');

var HOMEPAGE_BAR =
  '<div id="scws-emergency-cta" class="bg-gradient-to-r from-red-600 to-red-700 text-white py-2.5">' +
    '<div class="max-w-7xl mx-auto px-4 text-center flex items-center justify-center gap-2 flex-wrap">' +
      '<span class="font-bold tracking-wide">🚨 No Water?</span>' +
      '<span class="hidden sm:inline">Same-day emergency service available.</span>' +
      '<a href="tel:7604408520" class="bg-white text-red-600 font-bold px-4 py-1 rounded-full text-sm">Call Now →</a>' +
    '</div>' +
  '</div>';

var STICKY =
  '<div id="sticky-cta">' +
    '<a href="tel:+17604408520" class="cta-call">📞 Call Now</a>' +
    '<a href="sms:7602195877" class="cta-text">💬 Text Us</a>' +
    '<a href="#contact" class="cta-est">Free Estimate</a>' +
  '</div>';

var HEADER =
  '<header class="bg-primary text-white sticky top-0 z-50">' +
    '<a href="tel:+17604408520" class="site-phone-cta">(760) 440-8520</a>' +
  '</header>';

var HOMEPAGE_FORM =
  '<form id="contact-form">' +
    '<input type="hidden" name="utm_source" id="utm_source">' +
    '<input type="hidden" name="gclid" id="gclid">' +
    '<input type="hidden" name="ga_client_id" id="ga_client_id">' +
    '<input type="hidden" name="ga_session_id" id="ga_session_id">' +
    '<div aria-hidden="true"><label for="website_url">Website</label>' +
      '<input type="text" id="website_url" name="website_url" tabindex="-1" autocomplete="off"></div>' +
    '<div class="space-y-4">' +
      '<div><label for="name">Name *</label><input type="text" id="name" name="name" required></div>' +
      '<div><label for="phone">Phone *</label><input type="tel" id="phone" name="phone" required></div>' +
      '<div><label for="email">Email</label><input type="email" id="email" name="email"></div>' +
      '<div><label for="address">Property Address *</label><input type="text" id="address" name="address" required></div>' +
      '<div><label for="city">City *</label><input type="text" id="city" name="city" required></div>' +
      '<div><label for="service">Service Needed</label>' +
        '<select id="service" name="service">' +
          '<option value="">Select a service...</option>' +
          '<option value="pump-repair">Pump Repair</option>' +
          '<option value="emergency">Emergency Service</option>' +
          '<option value="other">Other</option>' +
        '</select></div>' +
      '<div><label for="message">Message</label><textarea id="message" name="message"></textarea></div>' +
      '<div class="sms-row"><input type="checkbox" id="sms_consent" name="sms_consent" value="yes">' +
        '<label for="sms_consent">SMS consent</label></div>' +
      '<button type="submit" id="submit-btn">Get Estimate →</button>' +
    '</div>' +
  '</form>';

function loadPage(opts) {
  opts = opts || {};
  var html = '<!doctype html><html><body>' +
    HOMEPAGE_BAR + HEADER + STICKY + HOMEPAGE_FORM +
    '</body></html>';
  var dom = new JSDOM(html, {
    url: opts.url || 'https://scwellservice.com/?scws_ab=' + (opts.variant || 'control'),
    runScripts: 'outside-only'
  });
  var window = dom.window;
  window.dataLayer = [];
  if (opts.gtag !== false) {
    window.gtag = function () { window.dataLayer.push(Array.prototype.slice.call(arguments)); };
  }
  if (opts.utm) {
    window.sessionStorage.setItem('scws_utm', JSON.stringify(opts.utm));
  }
  if (opts.cookie) {
    window.document.cookie = opts.cookie;
  }
  window.eval(abSrc);
  window.eval(callSrc);
  window.document.dispatchEvent(new window.Event('DOMContentLoaded', { bubbles: true }));
  return { window: window, document: window.document, events: window.dataLayer };
}

function eventNames(events) {
  return events.filter(function (e) { return e[0] === 'event'; }).map(function (e) { return e[1]; });
}

function findEvent(events, name) {
  return events.find(function (e) { return e[0] === 'event' && e[1] === name; });
}

function fieldWrap(document, id) {
  return document.getElementById(id).parentNode;
}

var passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
  console.log('ok - ' + name);
}

test('homepage retires the emergency CTA experiment and cache-busts ab.js', function () {
  var html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  assert.match(html, /\/js\/ab\.js\?v=20260921a/);
  assert.doesNotMatch(html, /exp_emergency_cta/);
  assert.doesNotMatch(abSrc, /EXP_ID = 'exp_emergency_cta'|function findEmergencyBars|function isEmergencyBar/);
  assert.match(abSrc, /EXP_ID = 'exp_homepage_form'/);
  assert.match(abSrc, /COOKIE_DAYS = 30/);
  var barAt = html.indexOf('id="scws-emergency-cta"');
  var bar = html.slice(html.lastIndexOf('<!--', barAt), html.indexOf('<!-- Header', barAt));
  assert.doesNotMatch(bar, /sms:/);
  assert.match(bar, /tel:7604408520/);
  assert.match(bar, /Call Now/);
  assert.match(html, /id="address" name="address" required/);
  assert.match(html, /id="city" name="city" required/);
  assert.match(html, /name="sms_consent"/);
  assert.match(html, /name="website_url"/);
  assert.match(html, /'emergency': 'no_water'/);
  assert.match(html, /phone_conversion_number|scws-tracking\.js/);
});

test('exposes window.scwsAb and persists a 30-day cookie', function () {
  var page = loadPage({ variant: 'control' });
  assert.strictEqual(page.window.scwsAb.id, 'exp_homepage_form');
  assert.strictEqual(page.window.scwsAb.variant, 'control');
  assert.match(page.document.cookie, /scws_ab=exp_homepage_form\.control/);
});

test('reuses the cookie assignment on later visits', function () {
  var page = loadPage({
    url: 'https://scwellservice.com/',
    cookie: 'scws_ab=exp_homepage_form.variant; Path=/'
  });
  assert.strictEqual(page.window.scwsAb.id, 'exp_homepage_form');
  assert.strictEqual(page.window.scwsAb.variant, 'variant');
});

test('drops a retired experiment cookie instead of keeping that arm', function () {
  var page = loadPage({
    url: 'https://scwellservice.com/?scws_ab=control',
    cookie: 'scws_ab=exp_emergency_cta.variant; Path=/'
  });
  assert.strictEqual(page.window.scwsAb.id, 'exp_homepage_form');
  assert.strictEqual(page.window.scwsAb.variant, 'control');
  assert.match(page.document.cookie, /scws_ab=exp_homepage_form\.control/);
});

test('sets GA4 user properties and fires experiment_view once per session', function () {
  var page = loadPage({ variant: 'variant' });
  var setCall = page.events.find(function (e) { return e[0] === 'set' && e[1] === 'user_properties'; });
  assert.ok(setCall);
  assert.strictEqual(setCall[2].exp_id, 'exp_homepage_form');
  assert.strictEqual(setCall[2].exp_var, 'variant');
  assert.strictEqual(eventNames(page.events).filter(function (n) { return n === 'experiment_view'; }).length, 1);
  page.window.eval(abSrc);
  assert.strictEqual(eventNames(page.events).filter(function (n) { return n === 'experiment_view'; }).length, 1);
});

test('no-ops GA calls when gtag is missing', function () {
  var page = loadPage({ variant: 'variant', gtag: false });
  assert.strictEqual(page.window.scwsAb.variant, 'variant');
  assert.strictEqual(typeof page.window.gtag, 'undefined');
  assert.strictEqual(eventNames(page.events).length, 0);
});

test('tags experiment_view and later events when gtag appears after startup', function () {
  var page = loadPage({ variant: 'control', gtag: false });
  assert.strictEqual(eventNames(page.events).filter(function (n) { return n === 'experiment_view'; }).length, 0);
  page.window.gtag = function () { page.window.dataLayer.push(Array.prototype.slice.call(arguments)); };
  page.window.dispatchEvent(new page.window.Event('load'));
  assert.strictEqual(eventNames(page.events).filter(function (n) { return n === 'experiment_view'; }).length, 1);
  page.window.gtag('event', 'generate_lead', { event_category: 'engagement' });
  assert.strictEqual(findEvent(page.events, 'generate_lead')[2].exp_id, 'exp_homepage_form');
  assert.strictEqual(findEvent(page.events, 'generate_lead')[2].exp_var, 'control');
});

test('re-wraps gtag if a later script replaces it', function () {
  var page = loadPage({ variant: 'variant' });
  page.window.gtag = function () { page.window.dataLayer.push(Array.prototype.slice.call(arguments)); };
  page.window.dispatchEvent(new page.window.Event('load'));
  page.window.gtag('event', 'generate_lead', {});
  page.window.gtag('event', 'page_view', {});
  var leads = page.events.filter(function (e) { return e[0] === 'event' && e[1] === 'generate_lead'; });
  assert.strictEqual(leads[leads.length - 1][2].exp_id, 'exp_homepage_form');
  assert.strictEqual(leads[leads.length - 1][2].exp_var, 'variant');
  var views = page.events.filter(function (e) { return e[0] === 'event' && e[1] === 'page_view'; });
  assert.strictEqual(views[views.length - 1][2].exp_id, undefined);
});

test('both arms leave the emergency bar as Call only', function () {
  ['control', 'variant'].forEach(function (variant) {
    var page = loadPage({ variant: variant });
    var bar = page.document.getElementById('scws-emergency-cta');
    assert.strictEqual(bar.querySelectorAll('a[href^="tel:"]').length, 1);
    assert.strictEqual(bar.querySelectorAll('a[href^="sms:"]').length, 0);
    assert.strictEqual(bar.querySelector('a[href^="tel:"]').getAttribute('href'), 'tel:7604408520');
    assert.match(bar.textContent, /Call Now/);
    assert.strictEqual(bar.getAttribute('data-scws-ab'), null);
  });
});

test('control leaves the full homepage form untouched', function () {
  var page = loadPage({ variant: 'control' });
  var doc = page.document;
  assert.strictEqual(doc.getElementById('scws-emergency-first'), null);
  assert.strictEqual(doc.getElementById('address').required, true);
  assert.strictEqual(doc.getElementById('city').required, true);
  assert.strictEqual(doc.getElementById('name').required, true);
  assert.strictEqual(doc.getElementById('phone').required, true);
  assert.strictEqual(fieldWrap(doc, 'address').style.display, '');
  assert.strictEqual(fieldWrap(doc, 'email').style.display, '');
  assert.strictEqual(fieldWrap(doc, 'message').style.display, '');
  assert.strictEqual(doc.getElementById('service').value, '');
  assert.match(doc.querySelector('label[for="service"]').textContent, /Service Needed/);
  assert.strictEqual(doc.getElementById('contact-form').getAttribute('data-scws-ab-form'), null);
});

test('variant shortens the homepage form to name, phone, and emergency', function () {
  var page = loadPage({ variant: 'variant' });
  var doc = page.document;
  var form = doc.getElementById('contact-form');
  var box = doc.getElementById('scws-emergency-first');
  var service = doc.getElementById('service');
  assert.ok(box);
  assert.strictEqual(box.checked, true);
  assert.strictEqual(box.getAttribute('name'), null);
  assert.strictEqual(service.value, 'emergency');
  assert.strictEqual(form.getAttribute('data-scws-ab-var'), 'variant');
  assert.strictEqual(doc.getElementById('name').required, true);
  assert.strictEqual(doc.getElementById('phone').required, true);
  ['email', 'address', 'city', 'message'].forEach(function (id) {
    var field = doc.getElementById(id);
    assert.strictEqual(field.required, false);
    assert.strictEqual(field.hasAttribute('required'), false);
    assert.strictEqual(fieldWrap(doc, id).style.display, 'none');
    assert.strictEqual(fieldWrap(doc, id).getAttribute('data-scws-ab-collapsed'), '1');
  });
  assert.strictEqual(fieldWrap(doc, 'sms_consent').style.display, '');
  assert.ok(doc.getElementById('website_url'));
  assert.ok(doc.getElementById('gclid'));
  assert.ok(doc.getElementById('ga_client_id'));
  assert.ok(doc.querySelector('[name="utm_source"]'));
  var data = new page.window.FormData(form);
  assert.strictEqual(data.get('service'), 'emergency');
  assert.strictEqual(data.get('name'), '');
  assert.strictEqual(data.get('address'), '');
  assert.strictEqual(data.get('website_url'), '');
  assert.strictEqual(data.get('scws-emergency-first'), null);
  page.window.eval(abSrc);
  page.document.dispatchEvent(new page.window.Event('DOMContentLoaded', { bubbles: true }));
  assert.strictEqual(doc.querySelectorAll('#scws-emergency-first').length, 1);
});

test('emergency checkbox stays synced with the service value', function () {
  var page = loadPage({ variant: 'variant' });
  var doc = page.document;
  var box = doc.getElementById('scws-emergency-first');
  var service = doc.getElementById('service');
  var form = doc.getElementById('contact-form');
  service.value = 'pump-repair';
  service.dispatchEvent(new page.window.Event('change', { bubbles: true }));
  assert.strictEqual(box.checked, false);
  box.checked = true;
  box.dispatchEvent(new page.window.Event('change', { bubbles: true }));
  assert.strictEqual(service.value, 'emergency');
  box.checked = false;
  box.dispatchEvent(new page.window.Event('change', { bubbles: true }));
  assert.strictEqual(service.value, '');
  service.value = 'pump-repair';
  box.checked = true;
  form.dispatchEvent(new page.window.Event('submit', { bubbles: true, cancelable: true }));
  assert.strictEqual(service.value, 'emergency');
});

test('does not shorten the form off the homepage', function () {
  var page = loadPage({
    url: 'https://scwellservice.com/contact.html?scws_ab=variant'
  });
  var doc = page.document;
  assert.strictEqual(page.window.scwsAb.variant, 'variant');
  assert.strictEqual(doc.getElementById('scws-emergency-first'), null);
  assert.strictEqual(doc.getElementById('address').required, true);
  assert.strictEqual(fieldWrap(doc, 'city').style.display, '');
  assert.strictEqual(doc.getElementById('service').value, '');
  var bar = doc.getElementById('scws-emergency-cta');
  assert.strictEqual(bar.querySelectorAll('a[href^="sms:"]').length, 0);
  assert.match(bar.textContent, /Call Now/);
});

test('applies the short form when the homepage path is /index.html', function () {
  var page = loadPage({ url: 'https://scwellservice.com/index.html?scws_ab=variant' });
  assert.strictEqual(page.document.getElementById('scws-emergency-first').checked, true);
  assert.strictEqual(page.document.getElementById('service').value, 'emergency');
  assert.strictEqual(fieldWrap(page.document, 'address').style.display, 'none');
});

test('does not change the sticky bar or header phone', function () {
  var page = loadPage({ variant: 'variant' });
  var sticky = page.document.getElementById('sticky-cta');
  assert.strictEqual(sticky.querySelectorAll('a').length, 3);
  assert.match(sticky.querySelector('.cta-call').textContent, /Call Now/);
  assert.match(sticky.querySelector('.cta-text').textContent, /Text Us/);
  var headerPhone = page.document.querySelector('header a[href^="tel:"]');
  assert.strictEqual(headerPhone.textContent, '(760) 440-8520');
  assert.strictEqual(headerPhone.getAttribute('href'), 'tel:+17604408520');
});

test('enriches generate_lead / call_click / text_click with exp_id and exp_var', function () {
  var page = loadPage({ variant: 'control' });
  page.window.gtag('event', 'generate_lead', { event_category: 'engagement' });
  page.window.gtag('event', 'call_click', { event_category: 'engagement' });
  page.window.gtag('event', 'text_click', { event_category: 'engagement' });
  page.window.gtag('event', 'ads_conversion_submit_lead_form', { event_category: 'lead' });
  page.window.gtag('event', 'page_view', {});
  var lead = findEvent(page.events, 'generate_lead');
  assert.strictEqual(lead[2].exp_id, 'exp_homepage_form');
  assert.strictEqual(lead[2].exp_var, 'control');
  assert.strictEqual(findEvent(page.events, 'call_click')[2].exp_id, 'exp_homepage_form');
  assert.strictEqual(findEvent(page.events, 'text_click')[2].exp_id, 'exp_homepage_form');
  assert.strictEqual(findEvent(page.events, 'ads_conversion_submit_lead_form')[2].exp_id, 'exp_homepage_form');
  assert.strictEqual(findEvent(page.events, 'page_view')[2].exp_id, undefined);
});

test('homepage form success path includes exp_id and exp_var', function () {
  var page = loadPage({ variant: 'variant' });
  page.window.eval(trackingSrc);
  page.window.scwsTrackLeadFormSuccess({
    event_category: 'engagement',
    value: 150
  }, { phone: '7605550100' });
  var lead = findEvent(page.events, 'generate_lead');
  var ads = findEvent(page.events, 'ads_conversion_submit_lead_form');
  assert.strictEqual(lead[2].exp_id, 'exp_homepage_form');
  assert.strictEqual(lead[2].exp_var, 'variant');
  assert.strictEqual(lead[2].value, 150);
  assert.strictEqual(ads[2].exp_id, 'exp_homepage_form');
  assert.strictEqual(ads[2].exp_var, 'variant');
  var conv = findEvent(page.events, 'conversion');
  assert.ok(conv);
  assert.strictEqual(conv[2].send_to, 'AW-490838730/nFeMCN_cyegcEMq1huoB');
  page.events.forEach(function (evt) {
    assert.ok(!evt[2] || evt[2].send_to !== 'AW-490838730/aFiRCMDlofAbEMq1huoB');
  });
});

test('SMS clicks fire text_click only and never the Ads phone conversion', function () {
  var page = loadPage({
    variant: 'variant',
    utm: { utm_source: 'google', utm_medium: 'cpc' }
  });
  page.events.length = 0;
  page.document.querySelector('#sticky-cta a[href^="sms:"]').dispatchEvent(
    new page.window.MouseEvent('click', { bubbles: true })
  );
  var names = eventNames(page.events);
  assert.deepStrictEqual(names, ['text_click']);
  assert.strictEqual(findEvent(page.events, 'text_click')[2].traffic_source, 'google_ads');
  assert.strictEqual(findEvent(page.events, 'text_click')[2].page_path, '/');
  assert.strictEqual(findEvent(page.events, 'text_click')[2].exp_id, 'exp_homepage_form');
  assert.strictEqual(findEvent(page.events, 'text_click')[2].exp_var, 'variant');
  assert.ok(!findEvent(page.events, 'click_to_text'));
  assert.ok(!findEvent(page.events, 'conversion'));
});

test('voice clicks fire one call_click plus the Ads phone conversion', function () {
  var page = loadPage({
    variant: 'control',
    utm: { utm_source: 'google', utm_medium: 'cpc' }
  });
  page.events.length = 0;
  page.document.querySelector('#scws-emergency-cta a[href^="tel:"]').dispatchEvent(
    new page.window.MouseEvent('click', { bubbles: true })
  );
  var names = eventNames(page.events);
  assert.deepStrictEqual(names, ['call_click', 'conversion']);
  var conv = findEvent(page.events, 'conversion');
  assert.strictEqual(conv[2].send_to, 'AW-490838730/aFiRCMDlofAbEMq1huoB');
  assert.strictEqual(findEvent(page.events, 'call_click')[2].exp_id, 'exp_homepage_form');
  assert.strictEqual(findEvent(page.events, 'call_click')[2].exp_var, 'control');
  assert.ok(!findEvent(page.events, 'click_to_call'));
  assert.ok(!findEvent(page.events, 'contact_page'));
  assert.ok(!findEvent(page.events, 'seo_call_conversion'));
});

console.log('\n' + passed + ' tests passed');
