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

function loadPage(opts) {
  opts = opts || {};
  var html = '<!doctype html><html><body>' +
    HOMEPAGE_BAR + HEADER + STICKY +
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

var passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
  console.log('ok - ' + name);
}

test('exposes window.scwsAb and persists a 30-day cookie', function () {
  var page = loadPage({ variant: 'control' });
  assert.strictEqual(page.window.scwsAb.id, 'exp_emergency_cta');
  assert.strictEqual(page.window.scwsAb.variant, 'control');
  assert.match(page.document.cookie, /scws_ab=exp_emergency_cta\.control/);
});

test('reuses the cookie assignment on later visits', function () {
  var page = loadPage({
    url: 'https://scwellservice.com/',
    cookie: 'scws_ab=exp_emergency_cta.variant; Path=/'
  });
  assert.strictEqual(page.window.scwsAb.variant, 'variant');
});

test('sets GA4 user properties and fires experiment_view once per session', function () {
  var page = loadPage({ variant: 'variant' });
  var setCall = page.events.find(function (e) { return e[0] === 'set' && e[1] === 'user_properties'; });
  assert.ok(setCall);
  assert.strictEqual(setCall[2].exp_id, 'exp_emergency_cta');
  assert.strictEqual(setCall[2].exp_var, 'variant');
  assert.strictEqual(eventNames(page.events).filter(function (n) { return n === 'experiment_view'; }).length, 1);
  page.window.eval(abSrc);
  assert.strictEqual(eventNames(page.events).filter(function (n) { return n === 'experiment_view'; }).length, 1);
});

test('no-ops GA calls when gtag is missing', function () {
  var page = loadPage({ variant: 'variant', gtag: false });
  assert.strictEqual(page.window.scwsAb.variant, 'variant');
  assert.strictEqual(typeof page.window.gtag, 'undefined');
  var bar = page.document.getElementById('scws-emergency-cta');
  assert.ok(bar.querySelector('a[href^="sms:"]'));
});

test('control leaves the emergency bar as Call only', function () {
  var page = loadPage({ variant: 'control' });
  var bar = page.document.getElementById('scws-emergency-cta');
  assert.strictEqual(bar.querySelectorAll('a[href^="tel:"]').length, 1);
  assert.strictEqual(bar.querySelectorAll('a[href^="sms:"]').length, 0);
  assert.match(bar.textContent, /Call Now/);
});

test('variant adds an equal Text button and keeps the voice tel: node', function () {
  var page = loadPage({ variant: 'variant' });
  var bar = page.document.getElementById('scws-emergency-cta');
  var call = bar.querySelector('a[href^="tel:"]');
  var text = bar.querySelector('a[href^="sms:"]');
  assert.ok(call);
  assert.ok(text);
  assert.strictEqual(call.getAttribute('href'), 'tel:7604408520');
  assert.strictEqual(text.getAttribute('href'), 'sms:7602195877');
  assert.match(call.textContent, /Call \(760\) 440-8520/);
  assert.match(text.textContent, /Text \(760\) 219-5877/);
});

test('does not apply the emergency-bar variant off the homepage', function () {
  var page = loadPage({
    url: 'https://scwellservice.com/contact.html?scws_ab=variant'
  });
  var bar = page.document.getElementById('scws-emergency-cta');
  assert.strictEqual(page.window.scwsAb.variant, 'variant');
  assert.strictEqual(bar.querySelectorAll('a[href^="sms:"]').length, 0);
  assert.match(bar.textContent, /Call Now/);
});

test('does not change the sticky bar or header phone', function () {
  var page = loadPage({ variant: 'variant' });
  var sticky = page.document.getElementById('sticky-cta');
  assert.strictEqual(sticky.querySelectorAll('a').length, 3);
  assert.match(sticky.querySelector('.cta-call').textContent, /Call Now/);
  assert.match(sticky.querySelector('.cta-text').textContent, /Text Us/);
  var headerPhone = page.document.querySelector('header a[href^="tel:"]');
  assert.strictEqual(headerPhone.textContent, '(760) 440-8520');
});

test('enriches generate_lead / call_click / text_click with exp_id and exp_var', function () {
  var page = loadPage({ variant: 'control' });
  page.window.gtag('event', 'generate_lead', { event_category: 'engagement' });
  page.window.gtag('event', 'call_click', { event_category: 'engagement' });
  page.window.gtag('event', 'text_click', { event_category: 'engagement' });
  page.window.gtag('event', 'ads_conversion_submit_lead_form', { event_category: 'lead' });
  page.window.gtag('event', 'page_view', {});
  var lead = findEvent(page.events, 'generate_lead');
  assert.strictEqual(lead[2].exp_id, 'exp_emergency_cta');
  assert.strictEqual(lead[2].exp_var, 'control');
  assert.strictEqual(findEvent(page.events, 'call_click')[2].exp_id, 'exp_emergency_cta');
  assert.strictEqual(findEvent(page.events, 'text_click')[2].exp_id, 'exp_emergency_cta');
  assert.strictEqual(findEvent(page.events, 'ads_conversion_submit_lead_form')[2].exp_id, 'exp_emergency_cta');
  assert.strictEqual(findEvent(page.events, 'page_view')[2].exp_id, undefined);
});

test('SMS clicks fire text_click only and never the Ads phone conversion', function () {
  var page = loadPage({
    variant: 'variant',
    utm: { utm_source: 'google', utm_medium: 'cpc' }
  });
  page.events.length = 0;
  page.document.querySelector('#scws-emergency-cta a[href^="sms:"]').dispatchEvent(
    new page.window.MouseEvent('click', { bubbles: true })
  );
  var names = eventNames(page.events);
  assert.deepStrictEqual(names, ['text_click']);
  assert.strictEqual(findEvent(page.events, 'text_click')[2].traffic_source, 'google_ads');
  assert.strictEqual(findEvent(page.events, 'text_click')[2].page_path, '/');
  assert.strictEqual(findEvent(page.events, 'text_click')[2].exp_id, 'exp_emergency_cta');
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
  assert.strictEqual(findEvent(page.events, 'call_click')[2].exp_id, 'exp_emergency_cta');
  assert.ok(!findEvent(page.events, 'click_to_call'));
  assert.ok(!findEvent(page.events, 'contact_page'));
  assert.ok(!findEvent(page.events, 'seo_call_conversion'));
});

console.log('\n' + passed + ' tests passed');
