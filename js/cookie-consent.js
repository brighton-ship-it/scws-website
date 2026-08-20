/* Cookie Consent Banner for SCWS
 * Sits above the mobile sticky Call/Text/Estimate bar so the call CTA
 * stays fully visible and tappable.
 */

(function () {
  function stickyVisible() {
    var sticky = document.getElementById('sticky-cta');
    if (!sticky) return false;
    if (window.matchMedia && window.matchMedia('(min-width: 1024px)').matches) return false;
    var style = window.getComputedStyle(sticky);
    return style.display !== 'none' && style.visibility !== 'hidden';
  }

  function positionBanner(banner) {
    if (!banner || banner.style.display === 'none') return;
    var sticky = document.getElementById('sticky-cta');
    if (stickyVisible() && sticky) {
      sticky.style.zIndex = '1100';
      banner.style.bottom = sticky.offsetHeight + 'px';
    } else {
      banner.style.bottom = '0';
    }
  }

  function notify() {
    document.dispatchEvent(new CustomEvent('scws-overlays-changed'));
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (localStorage.getItem('cookieConsent')) return;

    var banner = document.createElement('div');
    banner.id = 'scws-cookie-banner';
    banner.style.cssText = 'position: fixed; left: 0; right: 0; background: rgba(0, 0, 0, 0.8); color: white; padding: 15px; text-align: center; z-index: 1000; font-family: Inter, sans-serif;';
    banner.innerHTML =
      '<p style="margin: 0 0 10px 0; font-size: 14px;">We use cookies to enhance your browsing experience and analyze site traffic. By clicking "Accept", you consent to the use of cookies as described in our <a href="/privacy-policy.html" style="color: #4e9271; text-decoration: underline;">Privacy Policy</a>.</p>' +
      '<button id="acceptCookies" type="button" style="background: #4e9271; color: white; border: none; padding: 8px 16px; margin: 0 5px; cursor: pointer; border-radius: 4px; font-weight: bold;">Accept</button>' +
      '<button id="rejectCookies" type="button" style="background: #dc2626; color: white; border: none; padding: 8px 16px; margin: 0 5px; cursor: pointer; border-radius: 4px; font-weight: bold;">Reject</button>';
    document.body.appendChild(banner);
    positionBanner(banner);
    notify();

    window.addEventListener('resize', function () { positionBanner(banner); notify(); });

    function dismiss(value) {
      localStorage.setItem('cookieConsent', value);
      banner.style.display = 'none';
      notify();
    }

    document.getElementById('acceptCookies').addEventListener('click', function () {
      dismiss('accepted');
    });

    document.getElementById('rejectCookies').addEventListener('click', function () {
      dismiss('rejected');
      window['ga-disable-G-5LL1YRWT5T'] = true;
    });
  });
})();
