/**
 * Cookie banner: one line, above #sticky-cta, never covers hero Call.
 * Run: node js/cookie-consent.test.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var assert = require('assert');
var { JSDOM } = require('jsdom');

var src = fs.readFileSync(path.join(__dirname, 'cookie-consent.js'), 'utf8');

function loadPage(opts) {
  opts = opts || {};
  var html =
    '<!doctype html><html><body>' +
    '<section class="hero"><a href="tel:7604408520" id="hero-call">Call (760) 440-8520</a></section>' +
    '<div id="sticky-cta" style="height:64px;display:flex;"><a class="cta-call" href="tel:+17604408520">Call Now</a></div>' +
    '</body></html>';
  var dom = new JSDOM(html, {
    url: 'https://scwellservice.com/',
    runScripts: 'outside-only'
  });
  var window = dom.window;
  window.dataLayer = [];
  window.gtag = function () { window.dataLayer.push(Array.prototype.slice.call(arguments)); };
  window.localStorage.clear();
  var mobile = opts.mobile !== false;
  window.matchMedia = function (query) {
    var desktop = String(query).indexOf('min-width: 1024px') !== -1;
    return {
      matches: desktop ? !mobile : false,
      media: query,
      addEventListener: function () {},
      removeEventListener: function () {}
    };
  };
  Object.defineProperty(window, 'scrollY', { value: opts.scrollY || 0, writable: true, configurable: true });
  if (opts.consent) window.localStorage.setItem('cookieConsent', opts.consent);
  window.eval(src);
  window.document.dispatchEvent(new window.Event('DOMContentLoaded', { bubbles: true }));
  return { window: window, document: window.document };
}

function scrollAndShow(page, y) {
  Object.defineProperty(page.window, 'scrollY', { value: y, writable: true, configurable: true });
  page.window.dispatchEvent(new page.window.Event('scroll'));
}

var passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
  console.log('ok - ' + name);
}

test('desktop mounts one-line banner above the fold at bottom, not top', function () {
  var page = loadPage({ mobile: false });
  var banner = page.document.getElementById('scws-cookie-banner');
  assert.ok(banner, 'banner should mount on desktop');
  assert.strictEqual(banner.style.position, 'fixed');
  assert.strictEqual(banner.style.top, 'auto');
  assert.ok(banner.style.bottom === '0' || banner.style.bottom === '0px');
  assert.strictEqual(banner.style.flexWrap, 'nowrap');
  var p = banner.querySelector('p');
  assert.ok(p.textContent.indexOf('Cookies help us run the site') !== -1);
  assert.strictEqual(p.style.whiteSpace, 'nowrap');
});

test('Accept/Reject are at least 44px', function () {
  var page = loadPage({ mobile: false });
  var accept = page.document.getElementById('acceptCookies');
  var reject = page.document.getElementById('rejectCookies');
  assert.strictEqual(accept.style.minHeight, '44px');
  assert.strictEqual(reject.style.minHeight, '44px');
  assert.strictEqual(accept.style.minWidth, '88px');
  assert.strictEqual(reject.style.minWidth, '88px');
});

test('mobile waits for first scroll so hero Call is not covered', function () {
  var page = loadPage({ mobile: true, scrollY: 0 });
  assert.strictEqual(page.document.getElementById('scws-cookie-banner'), null);
  assert.ok(page.document.getElementById('hero-call'));
  scrollAndShow(page, 24);
  var banner = page.document.getElementById('scws-cookie-banner');
  assert.ok(banner, 'banner should appear after scroll');
  assert.strictEqual(banner.style.top, 'auto');
  var sticky = page.document.getElementById('sticky-cta');
  assert.ok(parseInt(banner.style.bottom, 10) >= sticky.offsetHeight || banner.style.bottom === sticky.offsetHeight + 'px');
});

test('does not add a second phone bar', function () {
  var page = loadPage({ mobile: false });
  assert.strictEqual(page.document.querySelectorAll('#sticky-cta').length, 1);
  assert.strictEqual(page.document.querySelectorAll('[id*="sticky-phone"]').length, 0);
});

test('already-consented visitors see no banner', function () {
  var page = loadPage({ mobile: false, consent: 'accepted' });
  assert.strictEqual(page.document.getElementById('scws-cookie-banner'), null);
});

console.log('\n' + passed + ' tests passed');
