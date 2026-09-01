/**
 * Tests for the internal leads scoreboard.
 * Run: node js/leads-scoreboard.test.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var assert = require('assert');
var { JSDOM } = require('jsdom');

var src = fs.readFileSync(path.join(__dirname, 'leads-scoreboard.js'), 'utf8');
var pageHtml = fs.readFileSync(path.join(__dirname, '..', 'ops', 'leads.html'), 'utf8');
var robots = fs.readFileSync(path.join(__dirname, '..', 'robots.txt'), 'utf8');
var indexHtml = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
var sitemapPages = fs.readFileSync(path.join(__dirname, '..', 'sitemap-pages.xml'), 'utf8');

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

function load() {
  var dom = new JSDOM('<!doctype html><html><body><div id="leads-scoreboard"></div></body></html>', {
    url: 'https://scwellservice.com/ops/leads.html',
    runScripts: 'outside-only'
  });
  var fetches = [];
  dom.window.fetch = function (url) {
    fetches.push(String(url));
    return Promise.reject(new Error('Failed to fetch'));
  };
  dom.window.eval(src);
  return { window: dom.window, fetches: fetches, api: dom.window.scwsLeadsScoreboard };
}

function jsonResponse(body, status) {
  var code = status == null ? 200 : status;
  return Promise.resolve({
    ok: code >= 200 && code < 300,
    status: code,
    json: function () { return Promise.resolve(body); }
  });
}

async function run() {
  await test('page is noindex internal and not linked from homepage or sitemap', function () {
    assert.match(pageHtml, /noindex,\s*nofollow,\s*noarchive/);
    assert.match(pageHtml, /googlebot/);
    assert.match(pageHtml, /Internal/);
    assert.doesNotMatch(pageHtml, /1966/);
    assert.doesNotMatch(pageHtml, /drilling since/i);
    assert.doesNotMatch(indexHtml, /ops\/leads/);
    assert.doesNotMatch(sitemapPages, /ops\/leads/);
    assert.match(robots, /Disallow:\s*\/ops\//);
    assert.match(pageHtml, /scwellservice\.com\/ops\/leads\.html/);
    assert.doesNotMatch(pageHtml, /gtag|G-5LL1YRWT5T|googletagmanager/);
    assert.doesNotMatch(pageHtml, /sticky-cta|lead-capture|chat-widget/);
  });

  await test('tracking numbers match scws-jobs Twilio map and keep GBP out of SEO', function () {
    var api = load().api;
    assert.strictEqual(api.TRACKING.organic_seo.e164, '+17604630493');
    assert.strictEqual(api.TRACKING.gbp_ramona.e164, '+17602791262');
    assert.strictEqual(api.TRACKING.gbp_anza.e164, '+17602791262');
    assert.strictEqual(api.TRACKING.google_ads.e164, '+17603312502');
    assert.strictEqual(api.TRACKING.direct.e164, '+17604937719');
    assert.strictEqual(api.TRACKING.organic_seo.callStatsKey, 'seo');
    assert.strictEqual(api.TRACKING.gbp_ramona.callStatsKey, 'gmb');
    assert.strictEqual(api.TRACKING.gbp_anza.callStatsKey, 'gmb');
    assert.strictEqual(api.TRACKING.organic_seo.channel, 'website_search_console');
    assert.strictEqual(api.TRACKING.gbp_ramona.channel, 'google_business_profile');
    assert.notStrictEqual(api.TRACKING.organic_seo.channel, api.TRACKING.gbp_ramona.channel);
    assert.strictEqual(api.CONVERSION, 'jobber_job_scheduled');
    assert.match(api.SCOREBOARD_PATH, /\/api\/scoreboard\/leads/);
  });

  await test('call stats put GMB in a combined pool and do not add it to organic', function () {
    var api = load().api;
    var period = api.emptyPeriod();
    api.applyCallStats(period, {
      total_calls: 12,
      period_days: 7,
      by_source: {
        seo: { total_calls: 4, completed_calls: 3 },
        google_ads: { total_calls: 5, completed_calls: 4 },
        gmb: { total_calls: 2, completed_calls: 2 },
        direct: { total_calls: 1, completed_calls: 1 }
      }
    }, 'live');
    assert.strictEqual(period.sources.organic_seo.calls.value, 4);
    assert.strictEqual(period.sources.organic_seo.calls.status, 'live');
    assert.strictEqual(period.sources.google_ads.calls.value, 5);
    assert.strictEqual(period.sources.direct.calls.value, 1);
    assert.strictEqual(period.sources.gbp_ramona.calls.value, null);
    assert.strictEqual(period.sources.gbp_ramona.calls.status, 'unsplit');
    assert.strictEqual(period.sources.gbp_anza.calls.status, 'unsplit');
    assert.strictEqual(period.gbpCombinedCalls.value, 2);
    assert.strictEqual(api.seoTotal(period, 'calls'), 4);
    assert.strictEqual(api.gbpRolledIntoSeo(period), false);
  });

  await test('reports/leads never promotes CRM job_scheduled as Jobber conversion', function () {
    var api = load().api;
    var period = api.emptyPeriod();
    api.applyReportsLeads(period, {
      stats_by_source: [
        { lead_source: 'organic_seo', total_leads: 3, jobs_scheduled: 9, quotes_accepted: 2, paid: 1 },
        { lead_source: 'google_ads', total_leads: 6, jobs_scheduled: 4 }
      ],
      recent_leads: [{ name: 'Jane Doe', phone: '7605550100' }]
    }, 'live');
    assert.strictEqual(period.sources.organic_seo.forms.value, 3);
    assert.strictEqual(period.sources.organic_seo.jobs.value, null);
    assert.strictEqual(period.sources.organic_seo.jobs.status, 'stub');
    assert.strictEqual(period.sources.google_ads.forms.value, 6);
    assert.strictEqual(period.sources.gbp_ramona.forms.value, null);
  });

  await test('scoreboard payload fills Jobber jobs and can split GBP listings', function () {
    var api = load().api;
    var period = api.emptyPeriod();
    api.applyScoreboard(period, {
      period_days: 7,
      conversion: 'jobber_job_scheduled',
      sources: {
        organic_seo: { calls: 2, texts: 1, forms: 3, jobs_scheduled: 1 },
        gbp_ramona: { calls: 4, texts: 0, forms: 0, jobs_scheduled: 2 },
        gbp_anza: { calls: 1, texts: 0, forms: 0, jobs_scheduled: 1 },
        google_ads: { calls: 5, texts: 0, forms: 2, jobs_scheduled: 2 },
        direct: { calls: 1, texts: 0, forms: 0, jobs_scheduled: 0 }
      }
    }, 'live');
    assert.strictEqual(period.sources.organic_seo.jobs.value, 1);
    assert.strictEqual(period.sources.gbp_ramona.jobs.value, 2);
    assert.strictEqual(period.sources.gbp_anza.jobs.value, 1);
    assert.strictEqual(period.sources.gbp_ramona.calls.value, 4);
    assert.notStrictEqual(period.sources.organic_seo.jobs.value, period.sources.gbp_ramona.jobs.value);
  });

  await test('stripPii drops names, phones, emails, and recent_leads', function () {
    var api = load().api;
    var clean = api.stripPii({
      stats_by_source: [{ lead_source: 'organic_seo', total_leads: 2 }],
      recent_leads: [{ name: 'Pat', email: 'pat@example.com', phone: '7605550199' }],
      customer_name: 'Pat',
      email: 'pat@example.com',
      caller_number: '+17605550199',
      totals: { jobs_scheduled: 1 }
    });
    assert.strictEqual(clean.recent_leads, undefined);
    assert.strictEqual(clean.customer_name, undefined);
    assert.strictEqual(clean.email, undefined);
    assert.strictEqual(clean.caller_number, undefined);
    assert.strictEqual(clean.stats_by_source[0].total_leads, 2);
    assert.strictEqual(clean.totals.jobs_scheduled, 1);
  });

  await test('HTTP statuses map to live / auth-gated / stub', function () {
    var api = load().api;
    assert.strictEqual(api.classifyHttp({ status: 200 }), 'live');
    assert.strictEqual(api.classifyHttp({ status: 401 }), 'auth_gated');
    assert.strictEqual(api.classifyHttp({ status: 403 }), 'auth_gated');
    assert.strictEqual(api.classifyHttp({ status: 404 }), 'stub');
    assert.strictEqual(api.classifyHttp({ status: 500 }), 'error');
    assert.strictEqual(api.classifyError(new Error('Failed to fetch')), 'not_public');
  });

  await test('render labels Jobber stub and does not print PII', function () {
    var loaded = load();
    var api = loaded.api;
    var p7 = api.emptyPeriod();
    p7.days = 7;
    p7.endpoints = { scoreboard: 'stub', calls_stats: 'auth_gated', reports_leads: 'not_public' };
    var p28 = api.emptyPeriod();
    p28.days = 28;
    p28.endpoints = p7.endpoints;
    var mount = loaded.window.document.getElementById('leads-scoreboard');
    api.render(mount, {
      asOf: '2026-09-01T00:00:00.000Z',
      conversion: 'jobber_job_scheduled',
      periods: { 7: p7, 28: p28 }
    });
    var html = mount.innerHTML;
    assert.match(html, /Jobber job scheduled/);
    assert.match(html, /Not quote approved/);
    assert.match(html, /Do not roll Maps\/GBP into SEO/);
    assert.match(html, /Jobber jobs scheduled by source/);
    assert.match(html, /api\/scoreboard\/leads/);
    assert.match(html, /no-PII/);
    assert.match(html, /GBP Ramona/);
    assert.match(html, /GBP Anza/);
    assert.match(html, /Organic site \(SEO\)/);
    assert.doesNotMatch(html, /Jane Doe|@example\.com|76055501/);
    assert.doesNotMatch(html, /1966/);
  });

  await test('loadBoard requests scoreboard, call stats, and reports for 7 and 28 days', function () {
    var loaded = load();
    return loaded.api.loadBoard().then(function (board) {
      assert.ok(board.periods[7]);
      assert.ok(board.periods[28]);
      var joined = loaded.fetches.join('\n');
      assert.match(joined, /\/api\/scoreboard\/leads\?days=7/);
      assert.match(joined, /\/api\/scoreboard\/leads\?days=28/);
      assert.match(joined, /\/api\/calls\/stats\?days=7/);
      assert.match(joined, /\/api\/calls\/stats\?days=28/);
      assert.match(joined, /\/api\/reports\/leads\?/);
      assert.strictEqual(board.periods[7].endpoints.scoreboard, 'not_public');
      assert.strictEqual(board.periods[7].sources.organic_seo.jobs.status, 'stub');
    });
  });

  await test('live scoreboard fetch wins Jobber counts without leaking PII fields from a dirty payload', function () {
    var dom = new JSDOM('<!doctype html><html><body><div id="leads-scoreboard"></div></body></html>', {
      url: 'https://scwellservice.com/ops/leads.html',
      runScripts: 'outside-only'
    });
    dom.window.fetch = function (url) {
      var href = String(url);
      if (href.indexOf('/api/scoreboard/leads') !== -1) {
        return jsonResponse({
          period_days: 7,
          sources: {
            organic_seo: { calls: 2, texts: 0, forms: 1, jobs_scheduled: 1, customer_name: 'NOPE' }
          },
          recent_leads: [{ name: 'NOPE' }]
        });
      }
      return jsonResponse({}, 401);
    };
    dom.window.eval(src);
    return dom.window.scwsLeadsScoreboard.loadBoard().then(function (board) {
      assert.strictEqual(board.periods[7].sources.organic_seo.jobs.value, 1);
      assert.strictEqual(board.periods[7].sources.organic_seo.jobs.status, 'live');
      var mount = dom.window.document.getElementById('leads-scoreboard');
      dom.window.scwsLeadsScoreboard.render(mount, board);
      assert.doesNotMatch(mount.innerHTML, /NOPE/);
    });
  });
}

run();
