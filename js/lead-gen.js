/**
 * SCWS Lead Generation Components
 * - Sticky phone header bar
 * - Exit intent popup
 */

(function() {
    'use strict';

    // Configuration
    const PHONE_NUMBER = '(760) 440-8520';
    const PHONE_LINK = 'tel:7604408520';
    const BRAND_COLOR = '#1f3b4d';
    const ACCENT_COLOR = '#4e9271';

    // ========================================
    // 1. STICKY PHONE HEADER
    // ========================================
    function createStickyHeader() {
        // Check if already exists
        if (document.getElementById('scws-sticky-phone-header')) return;

        const header = document.createElement('div');
        header.id = 'scws-sticky-phone-header';
        header.innerHTML = `
            <div class="scws-sticky-inner">
                <span class="scws-sticky-text">
                    <span class="scws-phone-icon">📞</span>
                    <span class="scws-help-text">Need Well Help?</span>
                </span>
                <a href="${PHONE_LINK}" class="scws-sticky-phone" onclick="typeof trackPhoneClick === 'function' && trackPhoneClick()">
                    Call (760) 440-8520
                </a>
            </div>
        `;

        // Insert at the very top of the body
        document.body.insertBefore(header, document.body.firstChild);

        // Add offset to body so content isn't hidden
        document.body.style.paddingTop = '44px';
    }

    // ========================================
    // 2. EXIT INTENT POPUP
    // ========================================
    const EXIT_POPUP_KEY = 'scws_exit_popup_shown';

    function hasSeenExitPopup() {
        return sessionStorage.getItem(EXIT_POPUP_KEY) === 'true';
    }

    function markExitPopupSeen() {
        sessionStorage.setItem(EXIT_POPUP_KEY, 'true');
    }

    function createExitPopup() {
        // Check if already exists or already shown
        if (document.getElementById('scws-exit-popup') || hasSeenExitPopup()) return;

        const popup = document.createElement('div');
        popup.id = 'scws-exit-popup';
        popup.className = 'scws-exit-popup-overlay';
        popup.innerHTML = `
            <div class="scws-exit-popup-content">
                <button class="scws-exit-popup-close" onclick="closeExitPopup()">&times;</button>
                <div class="scws-exit-popup-header">
                    <span class="scws-exit-icon">💧</span>
                    <h2>Before You Go — Get a FREE Quote!</h2>
                </div>
                <p class="scws-exit-popup-subtext">No obligation. Fast response from local well experts.</p>
                
                <form id="scws-exit-form" class="scws-exit-form" action="https://formspree.io/f/xrbzpngj" method="POST">
                    <input type="hidden" name="_subject" value="Exit Popup Lead - SCWS Website">
                    <input type="hidden" name="source" value="exit_intent_popup">
                    
                    <div class="scws-form-group">
                        <input type="text" name="name" placeholder="Your Name" required class="scws-input">
                    </div>
                    <div class="scws-form-group">
                        <input type="tel" name="phone" placeholder="Phone Number" required class="scws-input">
                    </div>
                    <div class="scws-form-group">
                        <textarea name="message" placeholder="Brief description of your well issue..." rows="3" class="scws-input scws-textarea"></textarea>
                    </div>
                    
                    <button type="submit" class="scws-exit-submit">
                        Get My Free Quote →
                    </button>
                </form>
                
                <p class="scws-exit-phone-alt">
                    Or call now: <a href="${PHONE_LINK}">${PHONE_NUMBER}</a>
                </p>
            </div>
        `;

        document.body.appendChild(popup);

        // Handle form submission
        const form = document.getElementById('scws-exit-form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            const submitBtn = form.querySelector('button[type="submit"]');
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Sending...';

            // Track conversion if available
            if (typeof gtag === 'function') {
                gtag('event', 'generate_lead', {
                    'event_category': 'engagement',
                    'event_label': 'exit_popup_form',
                    'value': 100
                });
            }

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: { 'Accept': 'application/json' }
            })
            .then(response => {
                if (response.ok) {
                    popup.querySelector('.scws-exit-popup-content').innerHTML = `
                        <div class="scws-exit-success">
                            <span class="scws-success-icon">✓</span>
                            <h2>Thank You!</h2>
                            <p>We'll contact you shortly with your free quote.</p>
                            <p class="scws-exit-phone-alt">
                                Need immediate help? Call <a href="${PHONE_LINK}">${PHONE_NUMBER}</a>
                            </p>
                            <button onclick="closeExitPopup()" class="scws-exit-submit" style="margin-top: 20px;">Close</button>
                        </div>
                    `;
                } else {
                    throw new Error('Form submission failed');
                }
            })
            .catch(error => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Get My Free Quote →';
                alert('There was an issue. Please call us at ' + PHONE_NUMBER);
            });
        });
    }

    // Show popup on exit intent
    function showExitPopup() {
        if (hasSeenExitPopup()) return;
        
        const popup = document.getElementById('scws-exit-popup');
        if (popup) {
            popup.classList.add('scws-exit-popup-visible');
            markExitPopupSeen();
        }
    }

    // Close popup
    window.closeExitPopup = function() {
        const popup = document.getElementById('scws-exit-popup');
        if (popup) {
            popup.classList.remove('scws-exit-popup-visible');
        }
    };

    // Exit intent detection
    function setupExitIntent() {
        let exitIntentTriggered = false;

        document.addEventListener('mouseout', function(e) {
            // Only trigger on desktop
            if (window.innerWidth < 768) return;
            if (exitIntentTriggered) return;
            
            // Check if mouse is leaving toward the top of the page
            if (e.clientY < 10 && e.relatedTarget == null) {
                exitIntentTriggered = true;
                showExitPopup();
            }
        });

        // Close on overlay click
        document.addEventListener('click', function(e) {
            if (e.target.id === 'scws-exit-popup') {
                closeExitPopup();
            }
        });

        // Close on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeExitPopup();
            }
        });
    }

    // ========================================
    // INJECT STYLES
    // ========================================
    function injectStyles() {
        const styles = document.createElement('style');
        styles.textContent = `
            /* Sticky Phone Header */
            #scws-sticky-phone-header {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 9999;
                background: ${BRAND_COLOR};
                color: white;
                padding: 10px 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }

            .scws-sticky-inner {
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
                flex-wrap: wrap;
            }

            .scws-sticky-text {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }

            .scws-phone-icon {
                font-size: 16px;
            }

            .scws-help-text {
                font-weight: 500;
            }

            .scws-sticky-phone {
                background: ${ACCENT_COLOR};
                color: white;
                padding: 6px 16px;
                border-radius: 50px;
                font-weight: 700;
                font-size: 15px;
                text-decoration: none;
                transition: all 0.2s ease;
            }

            .scws-sticky-phone:hover {
                background: #3d7a5c;
                transform: scale(1.05);
            }

            @media (max-width: 480px) {
                .scws-help-text {
                    display: none;
                }
                .scws-sticky-phone {
                    font-size: 14px;
                    padding: 8px 20px;
                }
            }

            /* Exit Intent Popup */
            .scws-exit-popup-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.7);
                z-index: 99999;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
            }

            .scws-exit-popup-overlay.scws-exit-popup-visible {
                opacity: 1;
                visibility: visible;
            }

            .scws-exit-popup-content {
                background: white;
                border-radius: 16px;
                padding: 32px;
                max-width: 440px;
                width: 100%;
                position: relative;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                animation: scws-popup-slide 0.3s ease;
            }

            @keyframes scws-popup-slide {
                from {
                    transform: translateY(-20px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }

            .scws-exit-popup-close {
                position: absolute;
                top: 12px;
                right: 16px;
                background: none;
                border: none;
                font-size: 28px;
                cursor: pointer;
                color: #666;
                line-height: 1;
                padding: 4px;
                transition: color 0.2s;
            }

            .scws-exit-popup-close:hover {
                color: #333;
            }

            .scws-exit-popup-header {
                text-align: center;
                margin-bottom: 8px;
            }

            .scws-exit-icon {
                font-size: 48px;
                display: block;
                margin-bottom: 8px;
            }

            .scws-exit-popup-header h2 {
                color: ${BRAND_COLOR};
                font-size: 24px;
                margin: 0;
                font-weight: 700;
            }

            .scws-exit-popup-subtext {
                text-align: center;
                color: #666;
                margin: 8px 0 20px;
                font-size: 14px;
            }

            .scws-exit-form {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .scws-form-group {
                width: 100%;
            }

            .scws-input {
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.2s;
                box-sizing: border-box;
                font-family: inherit;
            }

            .scws-input:focus {
                outline: none;
                border-color: ${ACCENT_COLOR};
            }

            .scws-textarea {
                resize: vertical;
                min-height: 80px;
            }

            .scws-exit-submit {
                background: ${ACCENT_COLOR};
                color: white;
                border: none;
                padding: 14px 24px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.2s ease;
                width: 100%;
            }

            .scws-exit-submit:hover {
                background: #3d7a5c;
                transform: translateY(-1px);
            }

            .scws-exit-submit:disabled {
                background: #999;
                cursor: not-allowed;
                transform: none;
            }

            .scws-exit-phone-alt {
                text-align: center;
                margin-top: 16px;
                color: #666;
                font-size: 14px;
            }

            .scws-exit-phone-alt a {
                color: ${ACCENT_COLOR};
                font-weight: 700;
                text-decoration: none;
            }

            .scws-exit-phone-alt a:hover {
                text-decoration: underline;
            }

            .scws-exit-success {
                text-align: center;
                padding: 20px 0;
            }

            .scws-success-icon {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 60px;
                height: 60px;
                background: ${ACCENT_COLOR};
                color: white;
                border-radius: 50%;
                font-size: 32px;
                margin-bottom: 16px;
            }

            .scws-exit-success h2 {
                color: ${BRAND_COLOR};
                margin: 0 0 8px;
            }

            .scws-exit-success p {
                color: #666;
                margin: 0;
            }

            @media (max-width: 480px) {
                .scws-exit-popup-content {
                    padding: 24px 20px;
                }
                .scws-exit-popup-header h2 {
                    font-size: 20px;
                }
                .scws-exit-icon {
                    font-size: 40px;
                }
            }
        `;
        document.head.appendChild(styles);
    }

    // ========================================
    // INITIALIZE
    // ========================================
    function init() {
        injectStyles();
        createStickyHeader();
        createExitPopup();
        setupExitIntent();
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
