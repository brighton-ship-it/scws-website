/**
 * SCWS Lead Capture Tools
 * 1. Sticky Mobile Phone Bar
 * 2. Exit-Intent Popup
 */

(function() {
  'use strict';

  const PHONE = '(760) 440-8520';
  const PHONE_LINK = 'tel:7604408520';
  const API_URL = 'https://scws-jobs.vercel.app/api/leads/create';

  // ============================================
  // 1. STICKY MOBILE PHONE BAR
  // ============================================
  function createStickyPhoneBar() {
    // Only show on mobile (check both width and user agent)
    const isMobile = window.innerWidth <= 768 || /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    if (!isMobile) return;
    
    // Don't create if already exists
    if (document.getElementById('scws-sticky-phone')) return;

    const bar = document.createElement('div');
    bar.id = 'scws-sticky-phone';
    bar.innerHTML = `
      <style>
        #scws-sticky-phone {
          position: fixed;
          bottom: 0;
          left: 0;
          right: 0;
          background: linear-gradient(135deg, #166534 0%, #15803d 100%);
          padding: 12px 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          z-index: 99998;
          box-shadow: 0 -4px 12px rgba(0,0,0,0.15);
        }
        #scws-sticky-phone a {
          color: white;
          text-decoration: none;
          font-weight: 600;
          font-size: 18px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        #scws-sticky-phone svg {
          width: 24px;
          height: 24px;
          fill: white;
          animation: phone-ring 1s ease-in-out infinite;
        }
        @keyframes phone-ring {
          0%, 100% { transform: rotate(0deg); }
          10%, 30% { transform: rotate(-10deg); }
          20%, 40% { transform: rotate(10deg); }
          50% { transform: rotate(0deg); }
        }
        #scws-sticky-phone .subtext {
          font-size: 12px;
          opacity: 0.9;
          font-weight: 400;
        }
        /* Adjust chat widget position when bar is present */
        #scws-chat-widget {
          bottom: 70px !important;
        }
      </style>
      <a href="${PHONE_LINK}">
        <svg viewBox="0 0 24 24"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
        <span>
          Tap to Call ${PHONE}
          <span class="subtext">Free Estimates • 24/7 Emergency</span>
        </span>
      </a>
    `;
    document.body.appendChild(bar);
    
    // Add body padding so content isn't hidden
    document.body.style.paddingBottom = '60px';
  }

  // ============================================
  // 2. EXIT-INTENT POPUP
  // ============================================
  function createExitIntentPopup() {
    // Check if already shown this session
    if (sessionStorage.getItem('scws-exit-shown')) return;

    const popup = document.createElement('div');
    popup.id = 'scws-exit-popup';
    popup.innerHTML = `
      <style>
        #scws-exit-popup {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.6);
          z-index: 999999;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }
        #scws-exit-popup.show {
          display: flex;
        }
        #scws-exit-popup .popup-content {
          background: white;
          border-radius: 16px;
          max-width: 420px;
          width: 100%;
          overflow: hidden;
          box-shadow: 0 20px 60px rgba(0,0,0,0.3);
          animation: popup-slide 0.3s ease-out;
        }
        @keyframes popup-slide {
          from { transform: translateY(-20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        #scws-exit-popup .popup-header {
          background: linear-gradient(135deg, #166534 0%, #15803d 100%);
          color: white;
          padding: 24px;
          text-align: center;
        }
        #scws-exit-popup .popup-header h2 {
          margin: 0 0 8px;
          font-size: 24px;
        }
        #scws-exit-popup .popup-header p {
          margin: 0;
          opacity: 0.9;
          font-size: 14px;
        }
        #scws-exit-popup .popup-body {
          padding: 24px;
        }
        #scws-exit-popup .popup-body p {
          margin: 0 0 16px;
          color: #374151;
          font-size: 15px;
          line-height: 1.5;
        }
        #scws-exit-popup input {
          width: 100%;
          padding: 14px 16px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          font-size: 16px;
          margin-bottom: 12px;
          box-sizing: border-box;
        }
        #scws-exit-popup input:focus {
          outline: none;
          border-color: #166534;
        }
        #scws-exit-popup .submit-btn {
          width: 100%;
          padding: 14px;
          background: #166534;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s;
        }
        #scws-exit-popup .submit-btn:hover {
          background: #15803d;
        }
        #scws-exit-popup .submit-btn:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }
        #scws-exit-popup .close-btn {
          position: absolute;
          top: 12px;
          right: 12px;
          background: rgba(255,255,255,0.2);
          border: none;
          color: white;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          cursor: pointer;
          font-size: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        #scws-exit-popup .close-btn:hover {
          background: rgba(255,255,255,0.3);
        }
        #scws-exit-popup .skip-link {
          display: block;
          text-align: center;
          margin-top: 12px;
          color: #6b7280;
          font-size: 14px;
          cursor: pointer;
        }
        #scws-exit-popup .skip-link:hover {
          color: #374151;
        }
        #scws-exit-popup .success-message {
          text-align: center;
          padding: 20px;
        }
        #scws-exit-popup .success-message svg {
          width: 60px;
          height: 60px;
          fill: #166534;
          margin-bottom: 16px;
        }
        #scws-exit-popup .success-message h3 {
          margin: 0 0 8px;
          color: #166534;
        }
        #scws-exit-popup .popup-header {
          position: relative;
        }
      </style>
      <div class="popup-content">
        <div class="popup-header">
          <button class="close-btn" onclick="closeExitPopup()">×</button>
          <h2>Wait! Before You Go...</h2>
          <p>Get a FREE callback from our well experts</p>
        </div>
        <div class="popup-body">
          <div id="exit-form">
            <p>Have a question about your well? Leave your number and we'll call you back within 5 minutes during business hours.</p>
            <input type="text" id="exit-name" placeholder="Your Name" required>
            <input type="tel" id="exit-phone" placeholder="Phone Number" required>
            <input type="text" id="exit-address" placeholder="Service Address (optional)">
            <input type="text" id="exit-website" name="website_url" autocomplete="off" tabindex="-1" aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0;">
            <p id="exit-error" style="display:none;color:#b91c1c;font-size:14px;margin:0 0 12px;"></p>
            <button class="submit-btn" onclick="submitExitForm()">Request Callback →</button>
            <span class="skip-link" onclick="closeExitPopup()">No thanks, I'll call later</span>
          </div>
          <div id="exit-success" class="success-message" style="display:none;">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
            <h3>We'll Call You Soon!</h3>
            <p>Expect a call within 5 minutes during business hours (Mon-Fri 7am-5pm). For emergencies, call us directly.</p>
            <a href="${PHONE_LINK}" style="display:inline-block;margin-top:16px;padding:12px 24px;background:#166534;color:white;text-decoration:none;border-radius:8px;font-weight:600;">Call Now: ${PHONE}</a>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(popup);

    // Exit intent detection (desktop only)
    let triggered = false;
    document.addEventListener('mouseout', function(e) {
      if (triggered) return;
      if (e.clientY < 10 && e.relatedTarget === null) {
        triggered = true;
        showExitPopup();
      }
    });

    // Also trigger after 45 seconds on page (mobile fallback)
    setTimeout(function() {
      if (!triggered && !sessionStorage.getItem('scws-exit-shown')) {
        // Only on mobile where exit intent doesn't work
        if (window.innerWidth <= 768) {
          triggered = true;
          showExitPopup();
        }
      }
    }, 45000);
  }

  window.showExitPopup = function() {
    const popup = document.getElementById('scws-exit-popup');
    if (popup) {
      popup.classList.add('show');
      sessionStorage.setItem('scws-exit-shown', 'true');
    }
  };

  window.closeExitPopup = function() {
    const popup = document.getElementById('scws-exit-popup');
    if (popup) {
      popup.classList.remove('show');
    }
  };

  window.submitExitForm = function() {
    const name = document.getElementById('exit-name').value.trim();
    const phone = document.getElementById('exit-phone').value.trim();
    const address = document.getElementById('exit-address').value.trim();
    const honeypot = (document.getElementById('exit-website') || {}).value || '';
    const errorEl = document.getElementById('exit-error');

    if (honeypot) {
      return;
    }

    if (!name || !phone) {
      alert('Please enter your name and phone number.');
      return;
    }

    const btn = document.querySelector('#scws-exit-popup .submit-btn');
    btn.disabled = true;
    btn.textContent = 'Submitting...';
    if (errorEl) {
      errorEl.style.display = 'none';
      errorEl.textContent = '';
    }

    // Send to API
    fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_name: name,
        phone: phone,
        address: address,
        city: '',
        service_type: 'Callback Request',
        notes: 'Exit-intent popup callback request',
        lead_source: 'website_form',
        lead_source_detail: 'exit-intent-popup'
      })
    })
    .then(response => {
      if (!response.ok) throw new Error('Lead request failed');
      return response.json().catch(function () { return {}; });
    })
    .then(function () {
      document.getElementById('exit-form').style.display = 'none';
      document.getElementById('exit-success').style.display = 'block';
    })
    .catch(function (error) {
      console.error('Error:', error);
      btn.disabled = false;
      btn.textContent = 'Request Callback →';
      if (errorEl) {
        errorEl.textContent = 'We could not send that request. Please call (760) 440-8520 or try again.';
        errorEl.style.display = 'block';
      }
    });
  };

  // Initialize when DOM is ready
  // NOTE: Sticky phone bar disabled - site already has enough phone CTAs
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      // createStickyPhoneBar(); // Disabled - too cluttered
      createExitIntentPopup();
    });
  } else {
    // createStickyPhoneBar(); // Disabled - too cluttered
    createExitIntentPopup();
  }
})();
