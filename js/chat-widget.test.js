/**
 * Singleton + API-path tests for the SCWS site-chat widget.
 * Run: node js/chat-widget.test.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var assert = require('assert');
var { JSDOM } = require('jsdom');

var widgetSrc = fs.readFileSync(path.join(__dirname, 'chat-widget.js'), 'utf8');

function loadWidget(documentReady) {
  var dom = new JSDOM('<!doctype html><html><body></body></html>', {
    url: 'https://scwellservice.com/',
    runScripts: 'outside-only'
  });
  var window = dom.window;
  // Delayed page injects run after DOM is ready, same as production.
  Object.defineProperty(window.document, 'readyState', {
    configurable: true,
    get: function () { return documentReady === false ? 'loading' : 'complete'; }
  });
  var fetches = [];
  window.fetch = function (url, opts) {
    fetches.push({ url: url, opts: opts });
    return Promise.resolve({
      json: function () { return Promise.resolve({ response: 'Hello from Sarah' }); }
    });
  };
  window.eval(widgetSrc);
  return { window: window, document: window.document, fetches: fetches, evalAgain: function () { window.eval(widgetSrc); } };
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
    return test('creates exactly one widget on first eval', function () {
      var page = loadWidget();
      assert.strictEqual(page.document.querySelectorAll('[id="scws-chat-widget"]').length, 1);
      assert.strictEqual(page.document.querySelectorAll('[id="scws-chat-button"]').length, 1);
    });
  })
  .then(function () {
    return test('second eval is a no-op singleton', function () {
      var page = loadWidget();
      page.evalAgain();
      page.evalAgain();
      assert.strictEqual(page.document.querySelectorAll('[id="scws-chat-widget"]').length, 1);
      assert.strictEqual(page.document.querySelectorAll('[id="scws-chat-button"]').length, 1);
    });
  })
  .then(function () {
    return test('does not create a second widget if one already exists', function () {
      var page = loadWidget();
      var stray = page.document.createElement('div');
      stray.id = 'scws-chat-widget';
      page.document.body.appendChild(stray);
      page.evalAgain();
      assert.strictEqual(page.document.querySelectorAll('[id="scws-chat-widget"]').length, 1);
    });
  })
  .then(function () {
    return test('click opens the existing chat panel', function () {
      var page = loadWidget();
      var button = page.document.getElementById('scws-chat-button');
      var panel = page.document.getElementById('scws-chat-window');
      assert.ok(button);
      assert.ok(panel);
      assert.ok(!panel.classList.contains('open'));
      button.dispatchEvent(new page.window.MouseEvent('click', { bubbles: true }));
      assert.ok(panel.classList.contains('open'));
    });
  })
  .then(function () {
    return test('send POSTs to the existing /api/chat URL', function () {
      var page = loadWidget();
      var input = page.document.getElementById('scws-chat-input');
      var sendBtn = page.document.getElementById('scws-chat-send');
      input.value = 'How much to replace a pump?';
      sendBtn.dispatchEvent(new page.window.MouseEvent('click', { bubbles: true }));
      return new Promise(function (resolve) { setTimeout(resolve, 20); }).then(function () {
        assert.strictEqual(page.fetches.length, 1);
        assert.strictEqual(page.fetches[0].url, 'https://scws-jobs.vercel.app/api/chat');
        assert.strictEqual(page.fetches[0].opts.method, 'POST');
        var body = JSON.parse(page.fetches[0].opts.body);
        assert.strictEqual(body.message, 'How much to replace a pump?');
      });
    });
  })
  .then(function () {
    return test('does not mention the dead scws-jobs widget embed URL', function () {
      assert.ok(!widgetSrc.includes('scws-jobs.vercel.app/chat-widget'));
      assert.ok(widgetSrc.includes('https://scws-jobs.vercel.app/api/chat'));
    });
  })
  .then(function () {
    console.log('\n' + passed + ' tests passed');
  })
  .catch(function (err) {
    console.error(err);
    process.exit(1);
  });
