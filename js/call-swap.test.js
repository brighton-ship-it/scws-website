// Run: node js/call-swap.test.js
const fs = require('fs');
const assert = require('assert');
const { JSDOM } = require('jsdom');
const src = fs.readFileSync(__dirname + '/call-tracking.js', 'utf8');
const html = '<body><a id="a" href="tel:7604408520">(760) 440-8520</a><a id="b" href="tel:+17604408520">Call 760-440-8520</a><a id="s" href="sms:7602195877">Text (760) 219-5877</a><script type="application/ld+json">{"telephone":"+1-760-440-8520"}</script></body>';
function load(url) {
  const dom = new JSDOM(html, { url, runScripts: 'outside-only' });
  dom.window.eval(src);
  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  return dom;
}
let d = load('https://scwellservice.com/x.html?gclid=test');
const doc = d.window.document;
assert.strictEqual(doc.getElementById('a').getAttribute('href'), 'tel:+17603312502');
assert.strictEqual(doc.getElementById('b').getAttribute('href'), 'tel:+17603312502');
assert.strictEqual(doc.getElementById('a').textContent, '(760) 331-2502');
assert.strictEqual(doc.getElementById('b').textContent, 'Call (760) 331-2502');
assert.strictEqual(doc.getElementById('s').getAttribute('href'), 'sms:7602195877');
assert.ok(doc.querySelector('script').textContent.includes('440-8520'));
d = load('https://scwellservice.com/x.html');
assert.strictEqual(d.window.document.getElementById('a').getAttribute('href'), 'tel:7604408520');
assert.strictEqual(d.window.document.getElementById('a').textContent, '(760) 440-8520');
d = load('https://scwellservice.com/x.html?utm_source=google&utm_medium=cpc');
assert.strictEqual(d.window.document.getElementById('a').getAttribute('href'), 'tel:+17603312502');
console.log('call-swap tests passed');
