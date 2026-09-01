/**
 * Internal LEADS scoreboard for scwellservice.com /ops/leads.html.
 *
 * Brighton scores SEO by Jobber jobs scheduled from organic — not blog
 * clicks, not Maps/GBP rolled into “SEO traffic.”
 *
 * This file only ever renders counts. It strips names, phones, emails,
 * addresses, and call SIDs if a CRM payload includes them.
 */
(function (root) {
  'use strict';

  var JOBS_ORIGIN = 'https://scws-jobs.vercel.app';

  // Preferred public, no-PII contract. Does not exist yet — labeled stub.
  var SCOREBOARD_PATH = '/api/scoreboard/leads';

  // Exists in scws-jobs. Session-auth. No CORS for this origin.
  var CALLS_STATS_PATH = '/api/calls/stats';

  // Exists in scws-jobs. Session-auth. Returns customer names — never render.
  var REPORTS_LEADS_PATH = '/api/reports/leads';

  var CONVERSION = 'jobber_job_scheduled';

  // Twilio Called-number map from scws-jobs src/app/api/calls/webhook/route.ts.
  // Confirmed live tagging. One GMB number covers both GBP listings.
  var TRACKING = {
    organic_seo: {
      id: 'organic_seo',
      label: 'Organic site (SEO)',
      phone: '(760) 463-0493',
      e164: '+17604630493',
      callStatsKey: 'seo',
      reportsKey: 'organic_seo',
      formLeadSources: ['organic_seo'],
      channel: 'website_search_console',
      note: 'Website organic (Search Console / scwellservice.com). Not Maps. Not GBP.'
    },
    gbp_ramona: {
      id: 'gbp_ramona',
      label: 'GBP Ramona',
      phone: '(760) 279-1262',
      e164: '+17602791262',
      callStatsKey: 'gmb',
      reportsKey: null,
      formLeadSources: [],
      channel: 'google_business_profile',
      note: 'Google Business Profile — Ramona listing. Separate from website SEO. Shares the GMB tracking number with Anza.'
    },
    gbp_anza: {
      id: 'gbp_anza',
      label: 'GBP Anza',
      phone: '(760) 279-1262',
      e164: '+17602791262',
      callStatsKey: 'gmb',
      reportsKey: null,
      formLeadSources: [],
      channel: 'google_business_profile',
      note: 'Google Business Profile — Anza listing. Separate from website SEO. Shares the GMB tracking number with Ramona.'
    },
    google_ads: {
      id: 'google_ads',
      label: 'Google Ads',
      phone: '(760) 331-2502',
      e164: '+17603312502',
      callStatsKey: 'google_ads',
      reportsKey: 'google_ads',
      formLeadSources: ['google_ads'],
      channel: 'paid',
      note: 'Paid search. Landing pages also POST source=google_ads on estimate forms.'
    },
    direct: {
      id: 'direct',
      label: 'Direct',
      phone: '(760) 493-7719',
      e164: '+17604937719',
      callStatsKey: 'direct',
      reportsKey: null,
      formLeadSources: ['direct'],
      channel: 'direct',
      note: 'Direct / typed-in. Forms may send lead_source=direct; booking.source is often website.'
    }
  };

  var SOURCE_ORDER = ['organic_seo', 'gbp_ramona', 'gbp_anza', 'google_ads', 'direct'];
  var PERIODS = [7, 28];
  var METRICS = ['calls', 'texts', 'forms', 'jobs'];

  var PII_KEY = /^(.*_)?(name|email|phone|address|caller|customer|from|to|sid|notes)(s|_number|_id|_name|_email|_phone|_address)?$/i;

  function emptyMetric(status) {
    return { value: null, status: status || 'stub' };
  }

  function emptySourceRow() {
    return {
      calls: emptyMetric('stub'),
      texts: emptyMetric('stub'),
      forms: emptyMetric('stub'),
      jobs: emptyMetric('stub')
    };
  }

  function emptyPeriod() {
    var sources = {};
    SOURCE_ORDER.forEach(function (id) {
      sources[id] = emptySourceRow();
    });
    return {
      days: 0,
      sources: sources,
      gbpCombinedCalls: emptyMetric('stub'),
      endpoints: {}
    };
  }

  function classifyHttp(res) {
    if (!res) return 'error';
    if (res.status === 401 || res.status === 403) return 'auth_gated';
    if (res.status === 404) return 'stub';
    if (res.status >= 200 && res.status < 300) return 'live';
    if (res.status >= 500) return 'error';
    return 'not_public';
  }

  function classifyError(err) {
    var msg = err && err.message ? String(err.message) : '';
    if (/401|403|unauthorized|forbidden/i.test(msg)) return 'auth_gated';
    if (/404|not found/i.test(msg)) return 'stub';
    if (/failed to fetch|networkerror|cors|load failed/i.test(msg)) return 'not_public';
    return 'error';
  }

  function isPlainObject(value) {
    return !!value && typeof value === 'object' && !Array.isArray(value);
  }

  function stripPii(value, key) {
    if (key && PII_KEY.test(key)) return undefined;
    if (Array.isArray(value)) {
      return value.map(function (item) {
        return stripPii(item, null);
      }).filter(function (item) {
        return item !== undefined;
      });
    }
    if (!isPlainObject(value)) return value;
    var out = {};
    Object.keys(value).forEach(function (k) {
      if (PII_KEY.test(k)) return;
      if (k === 'recent_leads' || k === 'calls' || k === 'customers') return;
      var next = stripPii(value[k], k);
      if (next !== undefined) out[k] = next;
    });
    return out;
  }

  function numOrNull(value) {
    if (value == null || value === '') return null;
    var n = Number(value);
    return isFinite(n) ? n : null;
  }

  function setMetric(row, key, value, status) {
    if (!row || !row[key]) return;
    if (value == null) {
      row[key] = emptyMetric(status || row[key].status);
      return;
    }
    row[key] = { value: value, status: status || 'live' };
  }

  /**
   * scws-jobs GET /api/calls/stats?days=N
   * { total_calls, period_days, by_source: { seo, google_ads, gmb, direct, unknown } }
   * GMB is one bucket — do not copy that count onto both Ramona and Anza.
   */
  function applyCallStats(period, payload, status) {
    period.endpoints.calls_stats = status;
    if (status !== 'live' || !payload || !payload.by_source) return period;
    var by = payload.by_source;
    SOURCE_ORDER.forEach(function (id) {
      var def = TRACKING[id];
      if (def.callStatsKey === 'gmb') {
        setMetric(period.sources[id], 'calls', null, 'unsplit');
        return;
      }
      var bucket = by[def.callStatsKey];
      if (!bucket) {
        setMetric(period.sources[id], 'calls', null, 'stub');
        return;
      }
      var total = numOrNull(bucket.total_calls);
      setMetric(period.sources[id], 'calls', total, 'live');
    });
    var gmb = by.gmb;
    if (gmb) {
      period.gbpCombinedCalls = {
        value: numOrNull(gmb.total_calls),
        status: 'live'
      };
    }
    return period;
  }

  /**
   * scws-jobs GET /api/reports/leads
   * stats_by_source[].jobs_scheduled is CRM stage, not Jobber-by-source.
   * Never treat that as Brighton’s conversion. Forms = total_leads only
   * for organic_seo / google_ads. Discard recent_leads (PII).
   */
  function applyReportsLeads(period, payload, status) {
    period.endpoints.reports_leads = status;
    if (status !== 'live' || !payload) return period;
    var rows = payload.stats_by_source;
    if (!Array.isArray(rows)) return period;
    var byKey = {};
    rows.forEach(function (row) {
      if (row && row.lead_source) byKey[row.lead_source] = row;
    });
    SOURCE_ORDER.forEach(function (id) {
      var def = TRACKING[id];
      if (!def.reportsKey || !byKey[def.reportsKey]) return;
      var row = byKey[def.reportsKey];
      setMetric(period.sources[id], 'forms', numOrNull(row.total_leads), 'live');
      setMetric(period.sources[id], 'jobs', null, 'stub');
    });
    return period;
  }

  /**
   * Needed public contract:
   * GET /api/scoreboard/leads?days=7|28
   * {
   *   period_days, as_of, conversion: "jobber_job_scheduled",
   *   sources: {
   *     organic_seo: { calls, texts, forms, jobs_scheduled },
   *     gbp_ramona:  { ... },
   *     gbp_anza:    { ... },
   *     google_ads:  { ... },
   *     direct:      { ... }
   *   }
   * }
   * Aggregates only. No names, phones, emails, addresses.
   */
  function applyScoreboard(period, payload, status) {
    period.endpoints.scoreboard = status;
    if (status !== 'live' || !payload || !isPlainObject(payload.sources)) return period;
    SOURCE_ORDER.forEach(function (id) {
      var src = payload.sources[id];
      if (!src) return;
      setMetric(period.sources[id], 'calls', numOrNull(src.calls), 'live');
      setMetric(period.sources[id], 'texts', numOrNull(src.texts), 'live');
      setMetric(period.sources[id], 'forms', numOrNull(src.forms), 'live');
      setMetric(period.sources[id], 'jobs', numOrNull(src.jobs_scheduled != null ? src.jobs_scheduled : src.jobs), 'live');
    });
    if (payload.gbp_combined_calls != null) {
      period.gbpCombinedCalls = {
        value: numOrNull(payload.gbp_combined_calls),
        status: 'live'
      };
    }
    return period;
  }

  function dateRangeIso(days, now) {
    var end = now ? new Date(now) : new Date();
    var start = new Date(end.getTime());
    start.setUTCDate(start.getUTCDate() - days);
    return {
      start_date: start.toISOString(),
      end_date: end.toISOString()
    };
  }

  function fetchJson(url) {
    if (typeof root.fetch !== 'function') {
      return Promise.reject(new Error('no fetch'));
    }
    return root
      .fetch(url, {
        method: 'GET',
        credentials: 'omit',
        cache: 'no-store',
        headers: { Accept: 'application/json' }
      })
      .then(function (res) {
        var status = classifyHttp(res);
        if (status !== 'live') {
          return { status: status, data: null };
        }
        return res.json().then(function (data) {
          return { status: 'live', data: stripPii(data) };
        });
      });
  }

  function fetchPeriod(days) {
    var period = emptyPeriod();
    period.days = days;
    var range = dateRangeIso(days);
    var scoreboardUrl = JOBS_ORIGIN + SCOREBOARD_PATH + '?days=' + days;
    var callsUrl = JOBS_ORIGIN + CALLS_STATS_PATH + '?days=' + days;
    var reportsUrl =
      JOBS_ORIGIN +
      REPORTS_LEADS_PATH +
      '?start_date=' +
      encodeURIComponent(range.start_date) +
      '&end_date=' +
      encodeURIComponent(range.end_date);

    function grab(url, apply) {
      return fetchJson(url)
        .then(function (result) {
          apply(period, result.data, result.status);
        })
        .catch(function (err) {
          apply(period, null, classifyError(err));
        });
    }

    return Promise.all([
      grab(scoreboardUrl, applyScoreboard),
      grab(callsUrl, applyCallStats),
      grab(reportsUrl, applyReportsLeads)
    ]).then(function () {
      return period;
    });
  }

  function seoTotal(period, metric) {
    var row = period && period.sources && period.sources.organic_seo;
    if (!row || !row[metric] || row[metric].value == null) return null;
    return row[metric].value;
  }

  function gbpRolledIntoSeo(period) {
    var seoCalls = seoTotal(period, 'calls');
    var gbp = period && period.gbpCombinedCalls && period.gbpCombinedCalls.value;
    if (seoCalls == null || gbp == null || gbp === 0) return false;
    return seoCalls === gbp;
  }

  function endpointNote(period) {
    var score = period.endpoints.scoreboard;
    var calls = period.endpoints.calls_stats;
    var reports = period.endpoints.reports_leads;
    return {
      scoreboard: score || 'stub',
      calls_stats: calls || 'stub',
      reports_leads: reports || 'stub'
    };
  }

  function loadBoard() {
    return Promise.all(PERIODS.map(fetchPeriod)).then(function (rows) {
      var periods = {};
      rows.forEach(function (row) {
        periods[row.days] = row;
      });
      return {
        asOf: new Date().toISOString(),
        conversion: CONVERSION,
        periods: periods
      };
    });
  }

  function statusLabel(status) {
    if (status === 'live') return 'Live';
    if (status === 'auth_gated') return 'Auth-gated';
    if (status === 'not_public') return 'Not browser-public';
    if (status === 'unsplit') return 'Unsplit GMB';
    if (status === 'error') return 'Error';
    return 'Stub';
  }

  function formatValue(metric) {
    if (!metric || metric.value == null) return '—';
    return String(metric.value);
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function metricCell(metric) {
    var status = (metric && metric.status) || 'stub';
    return (
      '<td class="metric metric-' +
      status +
      '"><span class="metric-value">' +
      escapeHtml(formatValue(metric)) +
      '</span><span class="metric-status">' +
      escapeHtml(statusLabel(status)) +
      '</span></td>'
    );
  }

  function sourceRowHtml(id, p7, p28) {
    var def = TRACKING[id];
    var a = p7.sources[id];
    var b = p28.sources[id];
    return (
      '<tr>' +
        '<th scope="row">' +
          '<div class="src-label">' + escapeHtml(def.label) + '</div>' +
          '<div class="src-phone">' + escapeHtml(def.phone) + '</div>' +
          '<div class="src-note">' + escapeHtml(def.note) + '</div>' +
        '</th>' +
        metricCell(a.calls) +
        metricCell(a.texts) +
        metricCell(a.forms) +
        metricCell(a.jobs) +
        metricCell(b.calls) +
        metricCell(b.texts) +
        metricCell(b.forms) +
        metricCell(b.jobs) +
      '</tr>'
    );
  }

  function render(mount, board) {
    if (!mount) return;
    var p7 = board.periods[7];
    var p28 = board.periods[28];
    var notes = endpointNote(p7);
    var gbp7 = p7.gbpCombinedCalls;
    var gbp28 = p28.gbpCombinedCalls;

    var rows = SOURCE_ORDER.map(function (id) {
      return sourceRowHtml(id, p7, p28);
    }).join('');

    mount.innerHTML =
      '<div class="board-meta">' +
        '<p><strong>Conversion Brighton chose:</strong> Jobber job scheduled. Not quote approved. Not invoice paid.</p>' +
        '<p><strong>Do not roll Maps/GBP into SEO traffic.</strong> Website organic and GBP are separate lead sources.</p>' +
        '<p class="as-of">As of ' + escapeHtml(board.asOf) + '</p>' +
      '</div>' +
      '<div class="gbp-pool">' +
        '<h2>GBP combined (not SEO)</h2>' +
        '<p>Twilio tags one GMB number — ' +
        escapeHtml(TRACKING.gbp_ramona.phone) +
        ' — for both listings. Ramona vs Anza split needs a listing-level tag in scws-jobs.</p>' +
        '<p>7-day GMB calls: <strong>' +
        escapeHtml(formatValue(gbp7)) +
        '</strong> <span class="metric-status">' +
        escapeHtml(statusLabel(gbp7.status)) +
        '</span> · 28-day GMB calls: <strong>' +
        escapeHtml(formatValue(gbp28)) +
        '</strong> <span class="metric-status">' +
        escapeHtml(statusLabel(gbp28.status)) +
        '</span></p>' +
      '</div>' +
      '<div class="table-wrap"><table>' +
        '<thead>' +
          '<tr>' +
            '<th rowspan="2">Source</th>' +
            '<th colspan="4">Last 7 days</th>' +
            '<th colspan="4">Last 28 days</th>' +
          '</tr>' +
          '<tr>' +
            '<th>Calls</th><th>Texts</th><th>Forms</th><th>Jobs scheduled</th>' +
            '<th>Calls</th><th>Texts</th><th>Forms</th><th>Jobs scheduled</th>' +
          '</tr>' +
        '</thead>' +
        '<tbody>' + rows + '</tbody>' +
      '</table></div>' +
      '<section class="legend">' +
        '<h2>Real vs stub</h2>' +
        '<ul>' +
          '<li><strong>Tracking numbers — real.</strong> scws-jobs Twilio map: SEO ' +
          escapeHtml(TRACKING.organic_seo.phone) +
          ', GMB ' +
          escapeHtml(TRACKING.gbp_ramona.phone) +
          ', Ads ' +
          escapeHtml(TRACKING.google_ads.phone) +
          ', Direct ' +
          escapeHtml(TRACKING.direct.phone) +
          '.</li>' +
          '<li><strong>Form tagging — real on this site.</strong> Estimate forms POST to scws-jobs <code>/api/booking</code> with <code>lead_source</code> (organic_seo / google_ads / direct). Booking <code>source</code> is often just <code>website</code>.</li>' +
          '<li><strong>Call counts — ' +
          escapeHtml(statusLabel(notes.calls_stats)) +
          '.</strong> <code>GET /api/calls/stats?days=N</code> exists in scws-jobs but is session-auth and not CORS-open to this origin.</li>' +
          '<li><strong>Form counts — ' +
          escapeHtml(statusLabel(notes.reports_leads)) +
          '.</strong> <code>GET /api/reports/leads</code> exists (auth). If it ever returns here, only aggregates are used. Customer names are dropped.</li>' +
          '<li><strong>Jobber jobs scheduled by source — stub.</strong> Needs public no-PII <code>GET ' +
          SCOREBOARD_PATH +
          '?days=7|28</code> on scws-jobs (status: ' +
          escapeHtml(statusLabel(notes.scoreboard)) +
          '). Until then this page does not invent Jobber numbers.</li>' +
          '<li><strong>Texts by source — stub.</strong> Public SMS is (760) 219-5877 and is not in the Twilio source-number map.</li>' +
        '</ul>' +
      '</section>';
  }

  function init() {
    var mount = root.document && root.document.getElementById('leads-scoreboard');
    if (!mount) return Promise.resolve(null);
    mount.textContent = 'Loading counts…';
    return loadBoard()
      .then(function (board) {
        render(mount, board);
        return board;
      })
      .catch(function () {
        mount.innerHTML =
          '<p class="load-error">Could not build the scoreboard. Tracking numbers below are still real; counts stay stub.</p>';
        return null;
      });
  }

  root.scwsLeadsScoreboard = {
    JOBS_ORIGIN: JOBS_ORIGIN,
    SCOREBOARD_PATH: SCOREBOARD_PATH,
    CALLS_STATS_PATH: CALLS_STATS_PATH,
    REPORTS_LEADS_PATH: REPORTS_LEADS_PATH,
    CONVERSION: CONVERSION,
    TRACKING: TRACKING,
    SOURCE_ORDER: SOURCE_ORDER,
    PERIODS: PERIODS,
    METRICS: METRICS,
    emptyPeriod: emptyPeriod,
    dateRangeIso: dateRangeIso,
    stripPii: stripPii,
    classifyHttp: classifyHttp,
    classifyError: classifyError,
    applyCallStats: applyCallStats,
    applyReportsLeads: applyReportsLeads,
    applyScoreboard: applyScoreboard,
    seoTotal: seoTotal,
    gbpRolledIntoSeo: gbpRolledIntoSeo,
    loadBoard: loadBoard,
    render: render,
    init: init
  };

  if (root.document) {
    if (root.document.readyState === 'loading') {
      root.document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }
})(typeof window !== 'undefined' ? window : this);
