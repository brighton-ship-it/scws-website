/**
 * UTM Parameter Tracking for SCWS Lead Forms
 * Auto-captures UTM params and determines lead source
 */
(function() {
    // Get UTM params from URL
    const urlParams = new URLSearchParams(window.location.search);
    const utmFields = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'];
    
    // Store UTM params in sessionStorage for multi-page visits
    if (urlParams.toString()) {
        const utmData = {};
        utmFields.forEach(function(field) {
            const value = urlParams.get(field);
            if (value) utmData[field] = value;
        });
        if (Object.keys(utmData).length > 0) {
            sessionStorage.setItem('scws_utm', JSON.stringify(utmData));
        }
    }
    
    // Function to populate form fields
    function populateUtmFields() {
        // Get current URL params or stored params
        let params = {};
        if (urlParams.toString()) {
            utmFields.forEach(function(field) {
                const value = urlParams.get(field);
                if (value) params[field] = value;
            });
        } else {
            const stored = sessionStorage.getItem('scws_utm');
            if (stored) {
                params = JSON.parse(stored);
            }
        }
        
        // Populate hidden fields
        utmFields.forEach(function(field) {
            const input = document.getElementById(field);
            if (input && params[field]) {
                input.value = params[field];
            }
        });
        
        // Capture landing page and referrer
        const landingPage = document.getElementById('landing_page');
        if (landingPage) landingPage.value = window.location.href;
        
        const referrer = document.getElementById('referrer');
        if (referrer) referrer.value = document.referrer || 'direct';
        
        // Auto-detect lead source
        const leadSource = document.getElementById('lead_source');
        const source = params.utm_source || urlParams.get('utm_source');
        const medium = params.utm_medium || urlParams.get('utm_medium');
        
        if (leadSource) {
            if (source === 'google' && medium === 'cpc') {
                leadSource.value = 'google_ads';
            } else if (source === 'google' || source === 'bing') {
                leadSource.value = 'paid_search';
            } else if (source === 'facebook' || source === 'instagram') {
                leadSource.value = 'social_ads';
            } else if (source) {
                leadSource.value = source;
            } else if (document.referrer.includes('google.com')) {
                leadSource.value = 'organic_seo';
            } else if (document.referrer.includes('yelp.com')) {
                leadSource.value = 'yelp';
            } else if (document.referrer) {
                leadSource.value = 'referral';
            } else {
                leadSource.value = 'direct';
            }
        }
    }
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', populateUtmFields);
    } else {
        populateUtmFields();
    }
})();
