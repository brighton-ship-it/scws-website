/**
 * Tests for UTM + ad click ID persist (Jobber book_job matching).
 * Run: node js/utm-tracking.test.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var assert = require('assert');
var { JSDOM } = require('jsdom');

var utmSrc = fs.readFileSync(path.join(__dirname, 'utm-tracking.js'), 'utf8');

var CLICK_FIELDS = ['gclid', 'gbraid', 'wbraid', 'ga_client_id', 'ga_session_id'];
var FORM_PAGES = [
  path.join(__dirname, '..', 'index.html'),
  path.join(__dirname, '..', 'contact.html'),
  path.join(__dirname, '..', 'free-guide.html'),
  path.join(__dirname, '..', 'cost-calculator.html'),
  path.join(__dirname, '..', 'pump-repair.html'),
  path.join(__dirname, '..', 'pages', 'landing', 'emergency.html'),
  path.join(__dirname, '..', 'pages', 'landing', 'drilling.html')
];

function test(name, fn) {
  return Promise.resolve()
    .then(fn)
    .then(function () { console.log('ok - ' + name); })
    .catch(function (err) {
      console.error('not ok - ' + name);
      console.error(err && err.stack ? err.stack : err);
      process.exitCode = 1;
    });
}

function hiddenInputsHtml() {
  return CLICK_FIELDS.concat([
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'landing_page', 'referrer', 'lead_source'
  ]).map(function (id) {
    return '<input type="hidden" name="' + id + '" id="' + id + '">';
  }).join('');
}

function loadTracker(opts) {
  opts = opts || {};
  var dom = new JSDOM('<!doctype html><html><body>' + hiddenInputsHtml() + '</body></html>', {
    url: opts.url || 'https://scwellservice.com/',
    runScripts: 'outside-only'
  });
  var window = dom.window;
  var logs = [];
  ['log', 'info', 'debug', 'warn'].forEach(function (level) {
    window.console[level] = function () {
      logs.push({ level: level, args: Array.prototype.slice.call(arguments) });
    };
  });
  if (opts.cookie) {
    window.document.cookie = opts.cookie;
  }
  if (opts.cookies) {
    opts.cookies.forEach(function (c) { window.document.cookie = c; });
  }
  if (opts.stored) {
    window.sessionStorage.setItem('scws_utm', JSON.stringify(opts.stored));
  }
  window.eval(utmSrc);
  return { window: window, document: window.document, logs: logs };
}

function stored(page) {
  return JSON.parse(page.window.sessionStorage.getItem('scws_utm') || '{}');
}

test('parses gclid / gbraid / wbraid from the URL and stores them', function () {
  var page = loadTracker({
    url: 'https://scwellservice.com/?gclid=TeSt-Gclid_1&gbraid=GBRAID99&wbraid=WBRAID88&utm_source=google'
  });
  var data = stored(page);
  assert.strictEqual(data.gclid, 'TeSt-Gclid_1');
  assert.strictEqual(data.gbraid, 'GBRAID99');
  assert.strictEqual(data.wbraid, 'WBRAID88');
  assert.strictEqual(data.utm_source, 'google');
  assert.strictEqual(page.document.getElementById('gclid').value, 'TeSt-Gclid_1');
  assert.strictEqual(page.document.getElementById('gbraid').value, 'GBRAID99');
  assert.strictEqual(page.document.getElementById('wbraid').value, 'WBRAID88');
})
.then(function () {
  return test('gclid survives a second page without the query string', function () {
    var first = loadTracker({
      url: 'https://scwellservice.com/?gclid=CLICK123&gbraid=GB1&wbraid=WB1'
    });
    var snapshot = stored(first);
    assert.strictEqual(snapshot.gclid, 'CLICK123');

    var second = loadTracker({
      url: 'https://scwellservice.com/contact.html',
      stored: snapshot
    });
    assert.strictEqual(stored(second).gclid, 'CLICK123');
    assert.strictEqual(second.document.getElementById('gclid').value, 'CLICK123');
    assert.strictEqual(second.document.getElementById('gbraid').value, 'GB1');
    assert.strictEqual(second.document.getElementById('wbraid').value, 'WB1');
  });
})
.then(function () {
  return test('parseGaClientId uses the portion after the last two dotted prefixes', function () {
    var page = loadTracker({ url: 'https://scwellservice.com/' });
    var parse = page.window.scwsUtmTracking.parseGaClientId;
    assert.strictEqual(parse('GA1.1.1234567890.1699999999'), '1234567890.1699999999');
    assert.strictEqual(parse('GA1.2.111.222'), '111.222');
    assert.strictEqual(parse(''), '');
    assert.strictEqual(parse('GA1.1'), '');
  });
})
.then(function () {
  return test('ga_client_id comes from the _ga cookie', function () {
    var page = loadTracker({
      url: 'https://scwellservice.com/contact.html',
      cookie: '_ga=GA1.1.9876543210.1700000000'
    });
    assert.strictEqual(stored(page).ga_client_id, '9876543210.1700000000');
    assert.strictEqual(page.document.getElementById('ga_client_id').value, '9876543210.1700000000');
  });
})
.then(function () {
  return test('ga_session_id comes from _ga_5LL1YRWT5T', function () {
    var page = loadTracker({
      url: 'https://scwellservice.com/',
      cookies: [
        '_ga=GA1.1.111.222',
        '_ga_5LL1YRWT5T=GS2.1.s1712345678$o2$g1$t1712349999$j60$l0$h0'
      ]
    });
    var parse = page.window.scwsUtmTracking.parseGaSessionId;
    assert.strictEqual(parse('GS2.1.s1712345678$o2$g1$t1712349999$j60$l0$h0'), '1712345678');
    assert.strictEqual(parse('GS1.1.1712345678.2.1.1712349999.0.0.0'), '1712345678');
    assert.strictEqual(stored(page).ga_session_id, '1712345678');
    assert.strictEqual(page.document.getElementById('ga_session_id').value, '1712345678');
    assert.strictEqual(stored(page).ga_client_id, '111.222');
  });
})
.then(function () {
  return test('does not log PII or click ids', function () {
    var page = loadTracker({
      url: 'https://scwellservice.com/?gclid=SECRET_GCLID&gbraid=SECRET_GBRAID',
      cookie: '_ga=GA1.1.555.666'
    });
    page.logs.forEach(function (entry) {
      var blob = JSON.stringify(entry.args);
      assert.doesNotMatch(blob, /SECRET_GCLID|SECRET_GBRAID|555\.666|gclid|gbraid|wbraid|ga_client_id/);
    });
    assert.doesNotMatch(utmSrc, /console\.(log|info|debug)\([^)]*(gclid|gbraid|wbraid|ga_client_id)/);
  });
})
.then(function () {
  return test('lead forms have hidden click-id inputs next to UTMs', function () {
    FORM_PAGES.forEach(function (file) {
      var html = fs.readFileSync(file, 'utf8');
      CLICK_FIELDS.forEach(function (field) {
        assert.match(html, new RegExp('id="' + field + '"'), file + ' missing ' + field);
        assert.match(html, new RegExp('name="' + field + '"'), file + ' missing name ' + field);
      });
      assert.match(html, /utm-tracking\.js/, file);
    });
  });
})
.then(function () {
  return test('homepage and contact booking payloads include click ids when present', function () {
    function extractHandler(html) {
      var start = html.indexOf('function handleFormSubmit');
      return html.slice(start, html.indexOf('</script>', start));
    }

    function submitWithIds(file) {
      var html = fs.readFileSync(path.join(__dirname, '..', file), 'utf8');
      var formHtml =
        '<form id="contact-form">' +
          '<input name="name" value="Test User">' +
          '<input name="phone" value="7605550100">' +
          '<input name="email" value="test@example.com">' +
          '<input name="address" value="1 Main">' +
          '<input name="city" value="Ramona">' +
          '<input name="location" value="Ramona">' +
          '<input name="service" value="pump-repair">' +
          '<textarea name="message">test</textarea>' +
          '<input name="website_url" value="">' +
          '<input name="gclid" id="gclid" value="GCLID-FROM-FORM">' +
          '<input name="gbraid" id="gbraid" value="GBRAID-FROM-FORM">' +
          '<input name="wbraid" id="wbraid" value="WBRAID-FROM-FORM">' +
          '<input name="ga_client_id" id="ga_client_id" value="123.456">' +
          '<input name="ga_session_id" id="ga_session_id" value="1712345678">' +
          '<button id="submit-btn" type="submit">Go</button>' +
        '</form>' +
        '<div id="form-success" class="hidden"></div>';
      var dom = new JSDOM('<!doctype html><html><body>' + formHtml + '</body></html>', {
        url: 'https://scwellservice.com/' + file,
        runScripts: 'outside-only'
      });
      var window = dom.window;
      window.gtag = function () {};
      window.scwsTrackLeadFormSuccess = function () {};
      window.alert = function () {};
      window.console.error = function () {};
      var bodies = [];
      window.fetch = function (url, init) {
        if (/api\/booking/.test(String(url)) && init && init.body) {
          bodies.push(JSON.parse(init.body));
        }
        return Promise.resolve({ ok: true, json: function () { return Promise.resolve({}); } });
      };
      window.eval(extractHandler(html) + '\nwindow.handleFormSubmit = handleFormSubmit;');
      window.handleFormSubmit(new window.Event('submit', { bubbles: true, cancelable: true }));
      return bodies;
    }

    return Promise.resolve().then(function () { return Promise.resolve(); }).then(function () {
      ['index.html', 'contact.html'].forEach(function (file) {
        var bodies = submitWithIds(file);
        assert.ok(bodies.length, file + ' should POST to booking');
        var payload = bodies[0];
        assert.strictEqual(payload.gclid, 'GCLID-FROM-FORM', file);
        assert.strictEqual(payload.gbraid, 'GBRAID-FROM-FORM', file);
        assert.strictEqual(payload.wbraid, 'WBRAID-FROM-FORM', file);
        assert.strictEqual(payload.ga_client_id, '123.456', file);
      });
    });
  });
})
.then(function () {
  if (process.exitCode) process.exit(process.exitCode);
});
