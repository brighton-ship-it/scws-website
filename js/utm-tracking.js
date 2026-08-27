/**
 * Attribution tracking for SCWS lead forms.
 * Captures UTMs + ad click IDs in sessionStorage and hidden fields
 * so a later Jobber-scheduled book_job conversion can match in the CRM.
 * Do not log PII or click IDs to the console.
 */
(function() {
    var STORAGE_KEY = 'scws_utm';
    var GA_MEASUREMENT = 'G-5LL1YRWT5T';
    var urlFields = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'gclid', 'gbraid', 'wbraid'
    ];
    var allFields = urlFields.concat(['ga_client_id', 'ga_session_id']);

    function getCookie(name) {
        var prefix = name + '=';
        var parts = (document.cookie || '').split(';');
        for (var i = 0; i < parts.length; i++) {
            var part = parts[i].replace(/^\s+/, '');
            if (part.indexOf(prefix) === 0) {
                return decodeURIComponent(part.slice(prefix.length));
            }
        }
        return '';
    }

    // _ga=GA1.1.XXXXXXXXXX.YYYYYYYYYY → client_id is after the first two dotted prefixes
    function parseGaClientId(raw) {
        if (!raw) return '';
        var parts = String(raw).split('.');
        if (parts.length < 4) return '';
        return parts.slice(2).join('.');
    }

    // G-5LL1YRWT5T → cookie _ga_5LL1YRWT5T
    // GS2.1.sSESSION$o1$g0$t…  or  GS1.1.SESSION.sessionCount…
    function parseGaSessionId(raw) {
        if (!raw) return '';
        var value = String(raw);
        var gs2 = value.match(/\.s(\d+)/);
        if (gs2) return gs2[1];
        var parts = value.split('.');
        if (parts.length >= 3 && /^\d+$/.test(parts[2])) return parts[2];
        return '';
    }

    function readStored() {
        try {
            var stored = sessionStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored) : {};
        } catch (e) {
            return {};
        }
    }

    function collectUrlFields(search) {
        var params = new URLSearchParams(search || window.location.search);
        var data = {};
        urlFields.forEach(function(field) {
            var value = params.get(field);
            if (value) data[field] = value;
        });
        return data;
    }

    function collectCookieFields() {
        var data = {};
        var clientId = parseGaClientId(getCookie('_ga'));
        if (clientId) data.ga_client_id = clientId;
        var sessionId = parseGaSessionId(getCookie('_ga_' + GA_MEASUREMENT.replace(/^G-/, '')));
        if (sessionId) data.ga_session_id = sessionId;
        return data;
    }

    function mergeParams() {
        var params = {};
        var stored = readStored();
        var fromUrl = collectUrlFields();
        var fromCookies = collectCookieFields();
        urlFields.concat(['ga_client_id', 'ga_session_id']).forEach(function(field) {
            if (stored[field]) params[field] = stored[field];
        });
        Object.keys(fromUrl).forEach(function(field) {
            params[field] = fromUrl[field];
        });
        Object.keys(fromCookies).forEach(function(field) {
            params[field] = fromCookies[field];
        });
        return params;
    }

    function persist(params) {
        if (Object.keys(params).length === 0) return;
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(params));
        } catch (e) {}
    }

    function populateFields(params) {
        allFields.forEach(function(field) {
            var input = document.getElementById(field);
            if (input && params[field]) {
                input.value = params[field];
            }
        });

        var landingPage = document.getElementById('landing_page');
        if (landingPage && !landingPage.value) landingPage.value = window.location.href;

        var referrer = document.getElementById('referrer');
        if (referrer && !referrer.value) referrer.value = document.referrer || 'direct';

        var leadSource = document.getElementById('lead_source');
        var source = params.utm_source;
        var medium = params.utm_medium;

        if (leadSource && !leadSource.value) {
            if (source === 'google' && medium === 'cpc') {
                leadSource.value = 'google_ads';
            } else if (source === 'google' || source === 'bing') {
                leadSource.value = 'paid_search';
            } else if (source === 'facebook' || source === 'instagram') {
                leadSource.value = 'social_ads';
            } else if (source) {
                leadSource.value = source;
            } else if (document.referrer.indexOf('google.com') !== -1) {
                leadSource.value = 'organic_seo';
            } else if (document.referrer.indexOf('yelp.com') !== -1) {
                leadSource.value = 'yelp';
            } else if (document.referrer) {
                leadSource.value = 'referral';
            } else {
                leadSource.value = 'direct';
            }
        }
    }

    function captureAttribution() {
        var params = mergeParams();
        persist(params);
        populateFields(params);
        return params;
    }

    // Test/debug helpers — values are never logged.
    window.scwsUtmTracking = {
        parseGaClientId: parseGaClientId,
        parseGaSessionId: parseGaSessionId,
        collectUrlFields: collectUrlFields,
        captureAttribution: captureAttribution,
        fields: allFields.slice()
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', captureAttribution);
    } else {
        captureAttribution();
    }
})();
