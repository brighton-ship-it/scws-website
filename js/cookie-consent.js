/* Cookie Consent Banner for SCWS */

document.addEventListener('DOMContentLoaded', function() {
    // Check if user has already consented
    if (!localStorage.getItem('cookieConsent')) {
        // Create consent banner
        var banner = document.createElement('div');
        banner.style.cssText = 'position: fixed; bottom: 0; left: 0; right: 0; background: rgba(0, 0, 0, 0.8); color: white; padding: 15px; text-align: center; z-index: 1000; font-family: Inter, sans-serif;';
        banner.innerHTML = `
            <p style="margin: 0 0 10px 0; font-size: 14px;">We use cookies to enhance your browsing experience and analyze site traffic. By clicking "Accept", you consent to the use of cookies as described in our <a href="/privacy-policy.html" style="color: #4e9271; text-decoration: underline;">Privacy Policy</a>.</p>
            <button id="acceptCookies" style="background: #4e9271; color: white; border: none; padding: 8px 16px; margin: 0 5px; cursor: pointer; border-radius: 4px; font-weight: bold;">Accept</button>
            <button id="rejectCookies" style="background: #dc2626; color: white; border: none; padding: 8px 16px; margin: 0 5px; cursor: pointer; border-radius: 4px; font-weight: bold;">Reject</button>
        `;
        document.body.appendChild(banner);

        // Event listeners for buttons
        document.getElementById('acceptCookies').addEventListener('click', function() {
            localStorage.setItem('cookieConsent', 'accepted');
            banner.style.display = 'none';
            // Enable tracking (GA4 scripts are already loaded, but this could trigger custom events if needed)
        });

        document.getElementById('rejectCookies').addEventListener('click', function() {
            localStorage.setItem('cookieConsent', 'rejected');
            banner.style.display = 'none';
            // Disable non-essential tracking if possible
            window['ga-disable-G-5LL1YRWT5T'] = true; // Attempt to disable GA4 tracking
        });
    }
});
