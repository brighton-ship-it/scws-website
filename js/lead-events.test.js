/**
 * Tests for form / exit-intent lead conversion events.
 * Run: node js/lead-events.test.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var assert = require('assert');
var { JSDOM } = require('jsdom');

var leadEventsSrc = fs.readFileSync(path.join(__dirname, 'lead-events.js'), 'utf8');
var leadCaptureSrc = fs.readFileSync(path.join(__dirname, 'lead-capture.js'), 'utf8');

var FORM_PAGES = [
  path.join(__dirname, '..', 'index.html'),
  path.join(__dirname, '..', 'contact.html'),
  path.join(__dirname, '..', 'free-guide.html'),
  path.join(__dirname, '..', 'cost-calculator.html'),
  path.join(__dirname, '..', 'pump-repair.html'),
  path.join(__dirname, '..', 'pages', 'landing', 'emergency.html'),
  path.join(__dirname, '..', 'pages', 'landing', 'drilling.html')
];

function findEvent(events, name) {
  return events.find(function (e) { return e[0] === 'event' && e[1] === name; });
}

function eventNames(events) {
  return events.filter(function (e) { return e[0] === 'event'; }).map(function (e) { return e[1]; });
}

function extractHandlerBlock(html) {
  var start = html.search(/function handleFormSubmit|function submitLead|addEventListener\('submit'/);
  assert.ok(start > -1, 'expected a form success handler');
  return html.slice(start, html.indexOf('</script>', start));
}

function loadLeadEvents(opts) {
  opts = opts || {};
  var dom = new JSDOM('<!doctype html><html><body></body></html>', {
    url: 'https://scwellservice.com/',
    runScripts: 'outside-only'
  });
  var window = dom.window;
  window.dataLayer = [];
  window.gtag = function () {
    window.dataLayer.push(Array.prototype.slice.call(arguments));
  };
  if (opts.scwsAb) window.scwsAb = opts.scwsAb;
  window.eval(leadEventsSrc);
  return { window: window, events: window.dataLayer };
}

function loadExitCapture(opts) {
  opts = opts || {};
  var dom = new JSDOM('<!doctype html><html><body></body></html>', {
    url: 'https://scwellservice.com/faq.html',
    runScripts: 'outside-only'
  });
  var window = dom.window;
  window.dataLayer = [];
  window.gtag = function () {
    window.dataLayer.push(Array.prototype.slice.call(arguments));
  };
  if (opts.scwsAb) window.scwsAb = opts.scwsAb;
  if (opts.withLeadEvents !== false) window.eval(leadEventsSrc);
  var fetches = [];
  window.fetch = function (url, init) {
    fetches.push({ url: url, init: init });
    var ok = opts.ok !== false;
    return Promise.resolve({
      ok: ok,
      json: function () { return Promise.resolve({}); }
    });
  };
  window.alert = function () {};
  window.console.error = function () {};
  window.eval(leadCaptureSrc);
  window.document.dispatchEvent(new window.Event('DOMContentLoaded', { bubbles: true }));
  return { window: window, document: window.document, events: window.dataLayer, fetches: fetches };
}

var passed = 0;
function test(name, fn) {
  var result = fn();
  if (result && typeof result.then === 'function') {
    return result.then(function () {
      passed += 1;
      console.log('ok - ' + name);
    });
  }
  passed += 1;
  console.log('ok - ' + name);
}

Promise.resolve()
  .then(function () {
    return test('fires generate_lead and ads_conversion_submit_lead_form only', function () {
      var page = loadLeadEvents();
      page.window.scwsTrackLeadFormSuccess({ event_category: 'engagement', value: 150 });
      assert.deepStrictEqual(eventNames(page.events), [
        'generate_lead',
        'ads_conversion_submit_lead_form'
      ]);
      assert.strictEqual(findEvent(page.events, 'generate_lead')[2].value, 150);
      assert.ok(!findEvent(page.events, 'conversion'));
      page.events.forEach(function (evt) {
        assert.ok(!evt[2] || !evt[2].send_to, 'form success must not send_to an Ads label');
      });
    });
  })
  .then(function () {
    return test('attaches exp_id and exp_var when scwsAb exists', function () {
      var page = loadLeadEvents({
        scwsAb: { id: 'exp_emergency_cta', variant: 'variant' }
      });
      page.window.scwsTrackLeadFormSuccess({ event_category: 'engagement' });
      var lead = findEvent(page.events, 'generate_lead')[2];
      var ads = findEvent(page.events, 'ads_conversion_submit_lead_form')[2];
      assert.strictEqual(lead.exp_id, 'exp_emergency_cta');
      assert.strictEqual(lead.exp_var, 'variant');
      assert.strictEqual(ads.exp_id, 'exp_emergency_cta');
      assert.strictEqual(ads.exp_var, 'variant');
    });
  })
  .then(function () {
    return test('is a no-op when gtag is missing', function () {
      var dom = new JSDOM('<!doctype html><html><body></body></html>', {
        url: 'https://scwellservice.com/',
        runScripts: 'outside-only'
      });
      dom.window.eval(leadEventsSrc);
      assert.doesNotThrow(function () {
        dom.window.scwsTrackLeadFormSuccess({ event_category: 'engagement' });
      });
    });
  })
  .then(function () {
    return test('exit-intent fires the same events after CRM ok', function () {
      var page = loadExitCapture();
      page.document.getElementById('exit-name').value = 'Test User';
      page.document.getElementById('exit-phone').value = '7605550100';
      page.window.submitExitForm();
      return Promise.resolve().then(function () {
        return Promise.resolve();
      }).then(function () {
        assert.strictEqual(page.fetches.length, 1);
        assert.match(page.fetches[0].url, /api\/leads\/create/);
        assert.deepStrictEqual(eventNames(page.events), [
          'generate_lead',
          'ads_conversion_submit_lead_form'
        ]);
        assert.strictEqual(findEvent(page.events, 'generate_lead')[2].event_label, 'exit_intent');
        assert.ok(!findEvent(page.events, 'conversion'));
      });
    });
  })
  .then(function () {
    return test('exit-intent honeypot and failed POST do not fire lead events', function () {
      var honey = loadExitCapture();
      honey.document.getElementById('exit-name').value = 'Bot';
      honey.document.getElementById('exit-phone').value = '7605550100';
      honey.document.getElementById('exit-website').value = 'http://spam.test';
      honey.window.submitExitForm();
      assert.strictEqual(honey.fetches.length, 0);
      assert.deepStrictEqual(eventNames(honey.events), []);

      var fail = loadExitCapture({ ok: false });
      fail.document.getElementById('exit-name').value = 'Test User';
      fail.document.getElementById('exit-phone').value = '7605550100';
      fail.window.submitExitForm();
      return Promise.resolve().then(function () {
        return Promise.resolve();
      }).then(function () {
        assert.strictEqual(fail.fetches.length, 1);
        assert.deepStrictEqual(eventNames(fail.events), []);
      });
    });
  })
  .then(function () {
    return test('exit-intent still fires when lead-events.js is not loaded', function () {
      var page = loadExitCapture({ withLeadEvents: false });
      page.document.getElementById('exit-name').value = 'Test User';
      page.document.getElementById('exit-phone').value = '7605550100';
      page.window.submitExitForm();
      return Promise.resolve().then(function () {
        return Promise.resolve();
      }).then(function () {
        assert.deepStrictEqual(eventNames(page.events), [
          'generate_lead',
          'ads_conversion_submit_lead_form'
        ]);
      });
    });
  })
  .then(function () {
    return test('form pages call the shared helper and never send form leads to Ads labels', function () {
      FORM_PAGES.forEach(function (file) {
        var html = fs.readFileSync(file, 'utf8');
        var block = extractHandlerBlock(html);
        assert.match(html, /js\/lead-events\.js/, file);
        assert.match(block, /scwsTrackLeadFormSuccess/, file);
        assert.doesNotMatch(block, /aFiRCMDlofAbEMq1huoB/, file);
        assert.doesNotMatch(block, /contact_form_submit/, file);
        assert.doesNotMatch(block, /send_to/, file);
      });
    });
  })
  .then(function () {
    return test('homepage hero Get Estimate fires estimate_click, not generate_lead', function () {
      var html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
      assert.match(html, /function trackEstimateClick/);
      assert.match(html, /gtag\('event', 'estimate_click'/);
      assert.match(html, /href="#contact" onclick="trackEstimateClick\(\)"/);
      var fn = html.slice(html.indexOf('function trackEstimateClick'), html.indexOf('function handleFormSubmit'));
      assert.doesNotMatch(fn, /generate_lead/);
    });
  })
  .then(function () {
    return test('phone Ads label remains only for call tracking / forwarding config', function () {
      var callSrc = fs.readFileSync(path.join(__dirname, 'call-tracking.js'), 'utf8');
      assert.match(callSrc, /AW-490838730\/aFiRCMDlofAbEMq1huoB/);
      assert.match(callSrc, /source === 'google_ads'/);

      var indexHtml = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
      assert.match(indexHtml, /phone_conversion_number/);
      var handler = extractHandlerBlock(indexHtml);
      assert.doesNotMatch(handler, /aFiRCMDlofAbEMq1huoB/);

      var contactHtml = fs.readFileSync(path.join(__dirname, '..', 'contact.html'), 'utf8');
      assert.match(contactHtml, /phone_conversion_number/);
    });
  })
  .then(function () {
    return test('pump-repair drops fake Ads send_to suffixes', function () {
      var html = fs.readFileSync(path.join(__dirname, '..', 'pump-repair.html'), 'utf8');
      assert.doesNotMatch(html, /phone_click|hero_call_click|footer_call_click|footer_button_click|form_submit/);
      assert.match(html, /call-tracking\.js|lead-events\.js/);
      assert.match(html, /phone_conversion_number/);
    });
  })
  .then(function () {
    console.log('\n' + passed + ' tests passed');
  })
  .catch(function (err) {
    console.error(err);
    process.exit(1);
  });
