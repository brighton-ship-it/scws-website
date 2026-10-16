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
    '<div aria-hidden="true"><input type="text" id="website_url" name="website_url" tabindex="-1" autocomplete="off"></div>' +
    '<div><label for="name">Name *</label><input type="text" id="name" name="name" required></div>' +
    '<div><label for="phone">Phone *</label><input type="tel" id="phone" name="phone" required></div>' +
    '<div><label for="email">Email</label><input type="email" id="email" name="email"></div>' +
    '<div><label for="address">Property Address *</label><input type="text" id="address" name="address" required></div>' +
    '<div><label for="city">City *</label><input type="text" id="city" name="city" required></div>' +
    '<div><label for="service">Service Needed</label>' +
      '<select id="service" name="service">' +
        '<option value="">Select a service...</option>' +
        '<option value="pump-repair">Pump Repair</option>' +
        '<option value="well-drilling">Well Drilling</option>' +
        '<option value="maintenance">Well Maintenance</option>' +
        '<option value="diagnostics">Diagnostics / Inspection</option>' +
        '<option value="emergency">Emergency Service</option>' +
        '<option value="other">Other</option>' +
      '</select>' +
    '</div>' +
    '<div><label for="message">Message</label><textarea id="message" name="message" rows="3"></textarea></div>' +
    '<div class="flex"><input type="checkbox" id="sms_consent" name="sms_consent" value="yes"><label for="sms_consent">I agree to receive appointment reminders by text.</label></div>' +
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

function fieldWrap(form, name) {
  return form.querySelector('[name="' + name + '"]').parentElement;
}

function isFieldHidden(form, name) {
  var wrap = fieldWrap(form, name);
  return wrap.classList.contains('hidden') && wrap.hasAttribute('hidden');
}

var passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
  console.log('ok - ' + name);
}

test('harness names a single homepage-form experiment', function () {
  var code = abSrc.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '');
  assert.strictEqual((code.match(/var EXP_ID = /g) || []).length, 1);
  assert.match(code, /var EXP_ID = 'exp_homepage_form'/);
  assert.doesNotMatch(code, /exp_emergency_cta/);
  assert.doesNotMatch(code, /findEmergencyBars|function applyVariant|function isEmergencyBar|TEXT_SMS|TEXT_DISPLAY/);
});

test('exposes window.scwsAb and persists a 30-day cookie', function () {
  var page = loadPage({ variant: 'control' });
  assert.strictEqual(page.window.scwsAb.id, 'exp_homepage_form');
  assert.strictEqual(page.window.scwsAb.variant, 'control');
  assert.match(page.document.cookie, /scws_ab=exp_homepage_form\.control/);
  assert.match(abSrc, /var COOKIE_DAYS = 30/);
});

test('reuses the cookie assignment on later visits', function () {
  var page = loadPage({
    url: 'https://scwellservice.com/',
    cookie: 'scws_ab=exp_homepage_form.variant; Path=/'
  });
  assert.strictEqual(page.window.scwsAb.variant, 'variant');
});

test('retired exp_emergency_cta cookies are not reused', function () {
  var page = loadPage({
    variant: 'control',
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

test('no-ops GA calls when gtag is missing and still applies the form variant', function () {
  var page = loadPage({ variant: 'variant', gtag: false });
  assert.strictEqual(page.window.scwsAb.variant, 'variant');
  assert.strictEqual(typeof page.window.gtag, 'undefined');
  var form = page.document.getElementById('contact-form');
  assert.strictEqual(form.querySelector('[name="service"]').value, 'emergency');
  assert.ok(isFieldHidden(form, 'email'));
});

test('control leaves the full homepage form unchanged', function () {
  var page = loadPage({ variant: 'control' });
  var form = page.document.getElementById('contact-form');
  ['email', 'address', 'city', 'message', 'name', 'phone', 'sms_consent'].forEach(function (name) {
    assert.ok(!isFieldHidden(form, name), name + ' should stay visible');
  });
  assert.strictEqual(form.querySelector('[name="name"]').required, true);
  assert.strictEqual(form.querySelector('[name="phone"]').required, true);
  assert.strictEqual(form.querySelector('[name="address"]').required, true);
  assert.strictEqual(form.querySelector('[name="city"]').required, true);
  assert.strictEqual(form.querySelector('[name="email"]').required, false);
  var service = form.querySelector('[name="service"]');
  assert.strictEqual(service.options[0].value, '');
  assert.strictEqual(service.options[0].textContent, 'Select a service...');
  assert.strictEqual(service.value, '');
  assert.strictEqual(form.querySelector('[name="address"]').value, '');
  assert.strictEqual(form.querySelector('[name="city"]').value, '');
  assert.strictEqual(form.getAttribute('data-scws-ab-var'), 'control');
});

test('variant shortens the form to name, phone, and emergency-first service', function () {
  var page = loadPage({ variant: 'variant' });
  var form = page.document.getElementById('contact-form');
  ['email', 'address', 'city', 'message'].forEach(function (name) {
    var field = form.querySelector('[name="' + name + '"]');
    assert.ok(field, name + ' stays in the DOM');
    assert.strictEqual(field.required, false, name + ' is not required');
    assert.strictEqual(field.value, '');
    assert.ok(isFieldHidden(form, name), name + ' is hidden');
    assert.strictEqual(fieldWrap(form, name).getAttribute('aria-hidden'), 'true');
  });
  assert.ok(!isFieldHidden(form, 'name'));
  assert.ok(!isFieldHidden(form, 'phone'));
  assert.ok(!isFieldHidden(form, 'sms_consent'));
  assert.strictEqual(form.querySelector('[name="name"]').required, true);
  assert.strictEqual(form.querySelector('[name="phone"]').required, true);
  var service = form.querySelector('select[name="service"]');
  assert.ok(service);
  assert.ok(!isFieldHidden(form, 'service'));
  assert.strictEqual(service.options[0].value, 'emergency');
  assert.strictEqual(service.options[0].textContent, 'Emergency Service');
  assert.strictEqual(service.value, 'emergency');
  assert.strictEqual(service.options.length, 7);
  assert.strictEqual(form.getAttribute('data-scws-ab'), 'applied');
  assert.strictEqual(form.getAttribute('data-scws-ab-var'), 'variant');
  assert.ok(form.querySelector('[name="website_url"]'));
  assert.ok(form.querySelector('[name="gclid"]'));
  page.window.eval(abSrc);
  page.document.dispatchEvent(new page.window.Event('DOMContentLoaded', { bubbles: true }));
  assert.strictEqual(form.querySelectorAll('[name="email"]').length, 1);
  assert.strictEqual(service.options[0].value, 'emergency');
});

test('does not shorten the form off the homepage', function () {
  var page = loadPage({
    url: 'https://scwellservice.com/contact.html?scws_ab=variant'
  });
  var form = page.document.getElementById('contact-form');
  assert.strictEqual(page.window.scwsAb.id, 'exp_homepage_form');
  assert.strictEqual(page.window.scwsAb.variant, 'variant');
  assert.strictEqual(form.querySelector('[name="address"]').required, true);
  assert.ok(!isFieldHidden(form, 'email'));
  assert.ok(!isFieldHidden(form, 'message'));
  assert.strictEqual(form.querySelector('[name="service"]').value, '');
  assert.strictEqual(form.querySelector('[name="service"]').options[0].value, '');
  assert.strictEqual(form.getAttribute('data-scws-ab'), null);
});

test('does not mutate the emergency bar, sticky bar, or header phone', function () {
  var page = loadPage({ variant: 'variant' });
  var bar = page.document.getElementById('scws-emergency-cta');
  var call = bar.querySelector('a[href^="tel:"]');
  assert.strictEqual(bar.querySelectorAll('a[href^="tel:"]').length, 1);
  assert.strictEqual(bar.querySelectorAll('a[href^="sms:"]').length, 0);
  assert.strictEqual(call.getAttribute('href'), 'tel:7604408520');
  assert.match(call.textContent, /Call Now/);
  assert.strictEqual(bar.getAttribute('data-scws-ab'), null);
  var sticky = page.document.getElementById('sticky-cta');
  assert.strictEqual(sticky.querySelectorAll('a').length, 3);
  assert.match(sticky.querySelector('.cta-call').textContent, /Call Now/);
  assert.strictEqual(sticky.querySelector('.cta-text').getAttribute('href'), 'sms:7602195877');
  var headerPhone = page.document.querySelector('header a[href^="tel:"]');
  assert.strictEqual(headerPhone.getAttribute('href'), 'tel:+17604408520');
  assert.strictEqual(headerPhone.textContent, '(760) 440-8520');
});

test('homepage HTML keeps the Call-only emergency bar and full form', function () {
  var html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  assert.match(html, /\/js\/ab\.js\?v=20260928a/);
  assert.doesNotMatch(html, /exp_emergency_cta/);
  assert.match(html, /formData\.get\('address'\) \|\| 'Not provided'/);
  assert.match(html, /formData\.get\('city'\) \|\| 'San Diego County'/);
  var barStart = html.indexOf('id="scws-emergency-cta"');
  var bar = html.slice(barStart, html.indexOf('</div>', html.indexOf('</div>', barStart) + 1));
  assert.match(bar, /tel:7604408520/);
  assert.match(bar, /Call Now/);
  assert.doesNotMatch(bar, /sms:/);
  var formStart = html.indexOf('id="contact-form"');
  var form = html.slice(formStart, html.indexOf('id="form-success"'));
  assert.match(form, /name="email"/);
  assert.match(form, /name="address"[^>]*required|name="address" required/);
  assert.match(form, /name="city"[^>]*required|name="city" required/);
  assert.match(form, /name="message"/);
  assert.match(form, /name="sms_consent"/);
  assert.match(form, /value="emergency"/);
  assert.doesNotMatch(form, /data-scws-ab/);
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
  assert.ok(!findEvent(page.events, 'click_to_call'));
  assert.ok(!findEvent(page.events, 'contact_page'));
  assert.ok(!findEvent(page.events, 'seo_call_conversion'));
});

console.log('\n' + passed + ' tests passed');
