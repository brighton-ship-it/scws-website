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
    return test('send POSTs to the existing /api/chat URL with visible history', function () {
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
        assert.ok(body.visitorInfo && body.visitorInfo.pageUrl);
        assert.ok(Array.isArray(body.history));
        assert.deepStrictEqual(body.history, [{
          role: 'assistant',
          content: "Hi! 👋 I'm Sarah from Southern California Well Service. How can I help you today?"
        }]);
        assert.ok(!JSON.stringify(body).includes('writeareview'));
      });
    });
  })
  .then(function () {
    return test('later sends include prior turns and skip the typing indicator', function () {
      var page = loadWidget();
      var input = page.document.getElementById('scws-chat-input');
      var sendBtn = page.document.getElementById('scws-chat-send');
      input.value = 'Need a pump repair';
      sendBtn.dispatchEvent(new page.window.MouseEvent('click', { bubbles: true }));
      return new Promise(function (resolve) { setTimeout(resolve, 20); }).then(function () {
        input.value = 'In Ramona';
        sendBtn.dispatchEvent(new page.window.MouseEvent('click', { bubbles: true }));
        return new Promise(function (resolve) { setTimeout(resolve, 20); });
      }).then(function () {
        assert.strictEqual(page.fetches.length, 2);
        var body = JSON.parse(page.fetches[1].opts.body);
        assert.strictEqual(body.message, 'In Ramona');
        assert.deepStrictEqual(body.history, [
          { role: 'assistant', content: "Hi! 👋 I'm Sarah from Southern California Well Service. How can I help you today?" },
          { role: 'user', content: 'Need a pump repair' },
          { role: 'assistant', content: 'Hello from Sarah' }
        ]);
        assert.ok(body.history.every(function (row) { return row.content !== 'Typing...'; }));
      });
    });
  })
  .then(function () {
    return test('history is last 20 messages, oldest first', function () {
      var page = loadWidget();
      var box = page.document.getElementById('scws-chat-messages');
      box.innerHTML = '';
      for (var i = 0; i < 25; i++) {
        var el = page.document.createElement('div');
        el.className = i % 2 === 0 ? 'scws-message assistant' : 'scws-message user';
        el.textContent = 'msg-' + i;
        box.appendChild(el);
      }
      var typing = page.document.createElement('div');
      typing.className = 'scws-message assistant typing';
      typing.textContent = 'Typing...';
      box.appendChild(typing);
      var input = page.document.getElementById('scws-chat-input');
      var sendBtn = page.document.getElementById('scws-chat-send');
      input.value = 'newest';
      sendBtn.dispatchEvent(new page.window.MouseEvent('click', { bubbles: true }));
      return new Promise(function (resolve) { setTimeout(resolve, 20); }).then(function () {
        var body = JSON.parse(page.fetches[0].opts.body);
        assert.strictEqual(body.message, 'newest');
        assert.strictEqual(body.history.length, 20);
        assert.strictEqual(body.history[0].content, 'msg-5');
        assert.strictEqual(body.history[19].content, 'msg-24');
        assert.ok(body.history.every(function (row) { return row.content !== 'Typing...' && row.content !== 'newest'; }));
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
