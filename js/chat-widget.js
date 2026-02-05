/**
 * SCWS Chat Widget v2
 * Live chat interface for Southern California Well Service
 * Ready for Clawdbot API integration
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        businessName: 'Southern California Well Service',
        phone: '(760) 440-8520',
        phoneClean: '7604408520',
        greeting: "Hi! 👋 How can we help with your well today?",
        quickReplies: [
            { text: "🚨 Emergency - No Water!", action: "emergency" },
            { text: "💰 Get a Quote", action: "quote" },
            { text: "❓ Ask a Question", action: "question" },
            { text: "🔧 Schedule Service", action: "service" }
        ],
        // Clawdbot API endpoint (configure when ready)
        apiEndpoint: null, // e.g., 'https://your-domain.com/api/chat'
        // Store leads locally
        storeLocally: true
    };

    // Auto-responses based on keywords
    const RESPONSES = {
        emergency: {
            keywords: ['emergency', 'no water', 'urgent', 'asap', 'broken', 'flood'],
            response: null, // Will show emergency box instead
            isEmergency: true
        },
        drilling: {
            keywords: ['drill', 'new well', 'drilling', 'dig', 'install well'],
            response: `Great question about drilling! 🛠️ Well costs depend on depth, geology, and location. Most wells in our area run 200-600ft.\n\nWant a free site evaluation? Fill out the quote form and we'll get back to you within 24 hours!`,
            showQuoteForm: true
        },
        pump: {
            keywords: ['pump', 'repair', 'not working', 'pressure', 'motor', 'submersible'],
            response: `Pump issues are our specialty! Common problems include motor failure, pressure switch issues, or dropping water levels.\n\nWe can usually diagnose and fix same-day. Would you like to schedule a service call?`,
            showServiceForm: true
        },
        cost: {
            keywords: ['cost', 'price', 'how much', 'quote', 'estimate', 'pricing'],
            response: `We offer free estimates! 💰\n\n• Pump repairs: $200-$1,500+\n• New wells: $15K-$40K+ (depth dependent)\n• Service calls: Starting at $150\n\nWant an accurate quote for your situation?`,
            showQuoteForm: true
        },
        maintenance: {
            keywords: ['maintenance', 'checkup', 'inspection', 'annual', 'service plan'],
            response: `Smart thinking! Regular maintenance extends well life and catches issues early. We recommend annual inspections.\n\nWant to schedule a maintenance visit?`,
            showServiceForm: true
        },
        testing: {
            keywords: ['water test', 'quality', 'safe', 'contamination', 'bacteria', 'testing'],
            response: `We offer comprehensive water testing for bacteria, minerals, and contaminants. Results typically in 3-5 days.\n\nThis is especially important for new wells or if you notice changes in taste/smell. Want to schedule a test?`,
            showServiceForm: true
        },
        hours: {
            keywords: ['hours', 'open', 'available', 'when', 'schedule'],
            response: `We're available Mon-Fri 7AM-5PM for regular service, but we offer 24/7 emergency response! 🕐\n\nFor emergencies, call us directly at ${CONFIG.phone}`,
        },
        area: {
            keywords: ['where', 'area', 'location', 'service area', 'come to', 'serve'],
            response: `We serve San Diego, Riverside, and San Bernardino Counties! 📍\n\nIncluding: Ramona, Valley Center, Temecula, Anza, Hemet, Escondido, Fallbrook, and surrounding areas.\n\nWhere are you located?`
        }
    };

    // State
    let state = {
        isOpen: false,
        messages: [],
        currentView: 'chat', // 'chat', 'quote', 'question', 'service'
        lead: null
    };

    // Utility: Generate unique ID
    function generateId() {
        return 'lead_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Utility: Store lead locally
    function storeLead(lead) {
        if (!CONFIG.storeLocally) return;
        
        try {
            const leads = JSON.parse(localStorage.getItem('scws_chat_leads') || '[]');
            leads.push({
                ...lead,
                id: generateId(),
                timestamp: new Date().toISOString(),
                page: window.location.pathname,
                userAgent: navigator.userAgent
            });
            localStorage.setItem('scws_chat_leads', JSON.stringify(leads));
            console.log('Lead stored:', lead);
        } catch (e) {
            console.error('Failed to store lead:', e);
        }
    }

    // Utility: Send to API (when configured)
    async function sendToAPI(data) {
        if (!CONFIG.apiEndpoint) {
            console.log('API not configured. Lead data:', data);
            return { success: true, offline: true };
        }

        try {
            const response = await fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (e) {
            console.error('API error:', e);
            return { success: false, error: e.message };
        }
    }

    // Create widget HTML
    function createWidget() {
        // Load CSS
        const cssLink = document.createElement('link');
        cssLink.rel = 'stylesheet';
        cssLink.href = '/css/chat-widget.css';
        document.head.appendChild(cssLink);

        const widget = document.createElement('div');
        widget.id = 'scws-chat-widget';
        widget.innerHTML = `
            <div id="scws-chat-window">
                <div id="scws-chat-header">
                    <img src="/images/logo.png" alt="SCWS" onerror="this.style.display='none'">
                    <div id="scws-chat-header-info">
                        <h3>SCWS Chat</h3>
                        <p>We typically reply in minutes</p>
                    </div>
                    <button id="scws-chat-close" aria-label="Close chat">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 6L6 18M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                
                <div id="scws-chat-messages"></div>
                
                <div id="scws-quick-replies"></div>
                
                <div id="scws-chat-input-area">
                    <input type="text" id="scws-chat-input" placeholder="Type your message..." autocomplete="off">
                    <button id="scws-chat-send" aria-label="Send message">
                        <svg viewBox="0 0 24 24">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
                
                <div id="scws-chat-cta">
                    <a href="tel:${CONFIG.phoneClean}" onclick="if(typeof gtag==='function')gtag('event','click_to_call',{event_category:'chat_widget'});">
                        📞 Call Now: ${CONFIG.phone}
                    </a>
                </div>
            </div>
            
            <button id="scws-chat-button" aria-label="Open chat">
                <svg viewBox="0 0 24 24">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                </svg>
                <span class="badge" style="display:none;">1</span>
            </button>
        `;
        document.body.appendChild(widget);
        return widget;
    }

    // Add message to chat
    function addMessage(text, type = 'bot', options = {}) {
        const messages = document.getElementById('scws-chat-messages');
        const msg = document.createElement('div');
        msg.className = `scws-message ${type}`;
        
        if (options.html) {
            msg.innerHTML = text;
        } else {
            msg.textContent = text;
        }
        
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
        
        state.messages.push({ text, type, timestamp: new Date() });
    }

    // Show typing indicator
    function showTyping() {
        const messages = document.getElementById('scws-chat-messages');
        const typing = document.createElement('div');
        typing.className = 'scws-typing';
        typing.id = 'scws-typing';
        typing.innerHTML = '<span></span><span></span><span></span>';
        messages.appendChild(typing);
        messages.scrollTop = messages.scrollHeight;
    }

    // Hide typing indicator
    function hideTyping() {
        const typing = document.getElementById('scws-typing');
        if (typing) typing.remove();
    }

    // Show quick replies
    function showQuickReplies(replies) {
        const container = document.getElementById('scws-quick-replies');
        container.innerHTML = '';
        
        replies.forEach(reply => {
            const btn = document.createElement('button');
            btn.className = 'scws-quick-reply';
            btn.textContent = typeof reply === 'string' ? reply : reply.text;
            btn.onclick = () => {
                if (typeof reply === 'string') {
                    handleUserMessage(reply);
                } else {
                    handleAction(reply.action);
                }
            };
            container.appendChild(btn);
        });
    }

    // Handle specific actions
    function handleAction(action) {
        const container = document.getElementById('scws-quick-replies');
        container.innerHTML = '';

        switch (action) {
            case 'emergency':
                showEmergencyBox();
                break;
            case 'quote':
                addMessage("Get a Quote", 'user');
                setTimeout(() => showQuoteForm(), 300);
                break;
            case 'question':
                addMessage("Ask a Question", 'user');
                setTimeout(() => showQuestionForm(), 300);
                break;
            case 'service':
                addMessage("Schedule Service", 'user');
                setTimeout(() => showServiceForm(), 300);
                break;
        }
    }

    // Show emergency box
    function showEmergencyBox() {
        addMessage("Emergency - No Water!", 'user');
        
        setTimeout(() => {
            const messages = document.getElementById('scws-chat-messages');
            const box = document.createElement('div');
            box.className = 'scws-emergency-box';
            box.innerHTML = `
                <h4>🚨 Emergency Service Available</h4>
                <a href="tel:${CONFIG.phoneClean}" class="phone" onclick="if(typeof gtag==='function')gtag('event','emergency_call',{event_category:'chat_widget'});">
                    ${CONFIG.phone}
                </a>
                <p>Call now for same-day emergency response!<br>We're available 24/7 for emergencies.</p>
            `;
            messages.appendChild(box);
            messages.scrollTop = messages.scrollHeight;
            
            // Track emergency action
            if (typeof gtag === 'function') {
                gtag('event', 'chat_emergency', { event_category: 'chat_widget' });
            }
        }, 300);
    }

    // Show quote form
    function showQuoteForm() {
        addMessage("I'd be happy to help you get a quote! Please fill out this quick form:", 'bot');
        
        setTimeout(() => {
            const messages = document.getElementById('scws-chat-messages');
            const form = document.createElement('div');
            form.className = 'scws-form';
            form.innerHTML = `
                <h4>📋 Quick Quote Request</h4>
                <div class="scws-form-group">
                    <label>Your Name *</label>
                    <input type="text" id="scws-quote-name" placeholder="John Smith" required>
                </div>
                <div class="scws-form-group">
                    <label>Phone Number *</label>
                    <input type="tel" id="scws-quote-phone" placeholder="(760) 555-1234" required>
                </div>
                <div class="scws-form-group">
                    <label>City/Area</label>
                    <input type="text" id="scws-quote-city" placeholder="Ramona, Valley Center, etc.">
                </div>
                <div class="scws-form-group">
                    <label>Service Needed</label>
                    <select id="scws-quote-service">
                        <option value="">Select a service...</option>
                        <option value="well-drilling">New Well Drilling</option>
                        <option value="pump-repair">Pump Repair/Replacement</option>
                        <option value="maintenance">Well Maintenance</option>
                        <option value="water-testing">Water Testing</option>
                        <option value="inspection">Well Inspection</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                <div class="scws-form-group">
                    <label>Tell us more (optional)</label>
                    <textarea id="scws-quote-message" placeholder="Describe your situation..."></textarea>
                </div>
                <button class="scws-form-submit" onclick="window.scwsSubmitQuote()">
                    Get My Free Quote →
                </button>
            `;
            messages.appendChild(form);
            messages.scrollTop = messages.scrollHeight;
            
            // Focus first field
            document.getElementById('scws-quote-name').focus();
        }, 500);
    }

    // Submit quote form
    window.scwsSubmitQuote = async function() {
        const name = document.getElementById('scws-quote-name').value.trim();
        const phone = document.getElementById('scws-quote-phone').value.trim();
        const city = document.getElementById('scws-quote-city').value.trim();
        const service = document.getElementById('scws-quote-service').value;
        const message = document.getElementById('scws-quote-message').value.trim();

        if (!name || !phone) {
            alert('Please enter your name and phone number.');
            return;
        }

        const lead = {
            type: 'quote',
            name,
            phone,
            city,
            service,
            message,
            source: 'chat_widget'
        };

        storeLead(lead);
        await sendToAPI(lead);

        // Show success
        const messages = document.getElementById('scws-chat-messages');
        const success = document.createElement('div');
        success.className = 'scws-success';
        success.innerHTML = `
            <h4>✅ Quote Request Received!</h4>
            <p>Thanks ${name.split(' ')[0]}! We'll call you at ${phone} within 24 hours (usually much sooner).</p>
        `;
        messages.appendChild(success);
        messages.scrollTop = messages.scrollHeight;

        // Remove form
        document.querySelector('.scws-form').remove();

        // Track conversion
        if (typeof gtag === 'function') {
            gtag('event', 'generate_lead', {
                event_category: 'chat_widget',
                event_label: 'quote_request',
                value: 100
            });
        }

        setTimeout(() => {
            addMessage("Is there anything else I can help you with?", 'bot');
            showQuickReplies([
                { text: "📞 Call Now", action: "emergency" },
                { text: "❓ Another Question", action: "question" }
            ]);
        }, 1500);
    };

    // Show question form
    function showQuestionForm() {
        addMessage("Sure! What would you like to know? Type your question below, or fill out this form to have someone call you back:", 'bot');
        
        setTimeout(() => {
            const messages = document.getElementById('scws-chat-messages');
            const form = document.createElement('div');
            form.className = 'scws-form';
            form.innerHTML = `
                <h4>❓ Ask Us Anything</h4>
                <div class="scws-form-group">
                    <label>Your Question *</label>
                    <textarea id="scws-question-text" placeholder="What would you like to know about wells, pumps, or our services?" required></textarea>
                </div>
                <div class="scws-form-group">
                    <label>Your Name (for callback)</label>
                    <input type="text" id="scws-question-name" placeholder="John Smith">
                </div>
                <div class="scws-form-group">
                    <label>Phone (for callback)</label>
                    <input type="tel" id="scws-question-phone" placeholder="(760) 555-1234">
                </div>
                <button class="scws-form-submit" onclick="window.scwsSubmitQuestion()">
                    Send Question →
                </button>
            `;
            messages.appendChild(form);
            messages.scrollTop = messages.scrollHeight;
            document.getElementById('scws-question-text').focus();
        }, 500);
    }

    // Submit question
    window.scwsSubmitQuestion = async function() {
        const question = document.getElementById('scws-question-text').value.trim();
        const name = document.getElementById('scws-question-name').value.trim();
        const phone = document.getElementById('scws-question-phone').value.trim();

        if (!question) {
            alert('Please enter your question.');
            return;
        }

        const lead = {
            type: 'question',
            question,
            name: name || 'Anonymous',
            phone: phone || 'Not provided',
            source: 'chat_widget'
        };

        storeLead(lead);
        await sendToAPI(lead);

        // Remove form
        document.querySelector('.scws-form').remove();

        // Show success
        addMessage(`Question: "${question}"`, 'user');
        
        setTimeout(() => {
            const messages = document.getElementById('scws-chat-messages');
            const success = document.createElement('div');
            success.className = 'scws-success';
            success.innerHTML = `
                <h4>✅ Question Received!</h4>
                <p>${name ? `Thanks ${name.split(' ')[0]}! ` : ''}We'll get back to you ${phone ? 'via phone' : 'soon'}!</p>
            `;
            messages.appendChild(success);
            messages.scrollTop = messages.scrollHeight;

            // Track
            if (typeof gtag === 'function') {
                gtag('event', 'chat_question', { event_category: 'chat_widget' });
            }
        }, 300);

        setTimeout(() => {
            showQuickReplies([
                { text: "💰 Get a Quote", action: "quote" },
                { text: "📞 Call Now", action: "emergency" }
            ]);
        }, 1500);
    };

    // Show service scheduling form
    function showServiceForm() {
        addMessage("Let's get you scheduled! Fill out this form and we'll call to confirm:", 'bot');
        
        setTimeout(() => {
            const messages = document.getElementById('scws-chat-messages');
            const form = document.createElement('div');
            form.className = 'scws-form';
            form.innerHTML = `
                <h4>🔧 Schedule Service</h4>
                <div class="scws-form-group">
                    <label>Your Name *</label>
                    <input type="text" id="scws-service-name" placeholder="John Smith" required>
                </div>
                <div class="scws-form-group">
                    <label>Phone Number *</label>
                    <input type="tel" id="scws-service-phone" placeholder="(760) 555-1234" required>
                </div>
                <div class="scws-form-group">
                    <label>Address/City *</label>
                    <input type="text" id="scws-service-address" placeholder="123 Main St, Ramona">
                </div>
                <div class="scws-form-group">
                    <label>What's the issue?</label>
                    <textarea id="scws-service-issue" placeholder="Describe what's happening with your well or pump..."></textarea>
                </div>
                <button class="scws-form-submit" onclick="window.scwsSubmitService()">
                    Request Service →
                </button>
            `;
            messages.appendChild(form);
            messages.scrollTop = messages.scrollHeight;
            document.getElementById('scws-service-name').focus();
        }, 500);
    }

    // Submit service request
    window.scwsSubmitService = async function() {
        const name = document.getElementById('scws-service-name').value.trim();
        const phone = document.getElementById('scws-service-phone').value.trim();
        const address = document.getElementById('scws-service-address').value.trim();
        const issue = document.getElementById('scws-service-issue').value.trim();

        if (!name || !phone || !address) {
            alert('Please fill in all required fields.');
            return;
        }

        const lead = {
            type: 'service_request',
            name,
            phone,
            address,
            issue,
            source: 'chat_widget'
        };

        storeLead(lead);
        await sendToAPI(lead);

        // Remove form
        document.querySelector('.scws-form').remove();

        // Show success
        const messages = document.getElementById('scws-chat-messages');
        const success = document.createElement('div');
        success.className = 'scws-success';
        success.innerHTML = `
            <h4>✅ Service Request Submitted!</h4>
            <p>Thanks ${name.split(' ')[0]}! We'll call ${phone} shortly to confirm your appointment.</p>
        `;
        messages.appendChild(success);
        messages.scrollTop = messages.scrollHeight;

        // Track
        if (typeof gtag === 'function') {
            gtag('event', 'generate_lead', {
                event_category: 'chat_widget',
                event_label: 'service_request',
                value: 150
            });
        }

        setTimeout(() => {
            addMessage("Is there anything else you need?", 'bot');
            showQuickReplies([
                { text: "❓ Another Question", action: "question" },
                { text: "📞 Call Now", action: "emergency" }
            ]);
        }, 1500);
    };

    // Find best response for message
    function findResponse(message) {
        const lower = message.toLowerCase();
        
        for (const [key, data] of Object.entries(RESPONSES)) {
            if (data.keywords.some(kw => lower.includes(kw))) {
                return data;
            }
        }
        
        return null;
    }

    // Handle user message
    function handleUserMessage(text) {
        addMessage(text, 'user');
        
        // Hide quick replies
        document.getElementById('scws-quick-replies').innerHTML = '';
        
        // Show typing
        showTyping();
        
        setTimeout(() => {
            hideTyping();
            
            const match = findResponse(text);
            
            if (match) {
                if (match.isEmergency) {
                    showEmergencyBox();
                } else {
                    addMessage(match.response);
                    
                    if (match.showQuoteForm) {
                        setTimeout(() => {
                            showQuickReplies([
                                { text: "Yes, get a quote!", action: "quote" },
                                { text: "No thanks", action: "question" }
                            ]);
                        }, 500);
                    } else if (match.showServiceForm) {
                        setTimeout(() => {
                            showQuickReplies([
                                { text: "Yes, schedule service", action: "service" },
                                { text: "Just browsing", action: "question" }
                            ]);
                        }, 500);
                    } else {
                        setTimeout(() => {
                            showQuickReplies([
                                { text: "💰 Get a Quote", action: "quote" },
                                { text: "📞 Call Us", action: "emergency" }
                            ]);
                        }, 500);
                    }
                }
            } else {
                // Default response
                addMessage(`Thanks for reaching out! For the best assistance, I'd recommend:\n\n• 📞 Call us: ${CONFIG.phone}\n• 📝 Fill out a quick form\n\nOr type another question and I'll do my best to help!`);
                
                setTimeout(() => {
                    showQuickReplies([
                        { text: "💰 Get a Quote", action: "quote" },
                        { text: "🔧 Schedule Service", action: "service" },
                        { text: "📞 Call Now", action: "emergency" }
                    ]);
                }, 500);
            }
            
            // Store message for later API integration
            storeLead({
                type: 'chat_message',
                message: text,
                source: 'chat_widget'
            });
            
        }, 800 + Math.random() * 400);
    }

    // Initialize widget
    function init() {
        createWidget();
        
        const chatButton = document.getElementById('scws-chat-button');
        const chatWindow = document.getElementById('scws-chat-window');
        const chatClose = document.getElementById('scws-chat-close');
        const chatInput = document.getElementById('scws-chat-input');
        const chatSend = document.getElementById('scws-chat-send');
        
        // Toggle chat
        chatButton.onclick = () => {
            state.isOpen = !state.isOpen;
            chatWindow.classList.toggle('open', state.isOpen);
            
            if (state.isOpen) {
                // Show greeting on first open
                const messages = document.getElementById('scws-chat-messages');
                if (messages.children.length === 0) {
                    addMessage(CONFIG.greeting);
                    setTimeout(() => {
                        showQuickReplies(CONFIG.quickReplies);
                    }, 300);
                }
                chatInput.focus();
                
                // Track open
                if (typeof gtag === 'function') {
                    gtag('event', 'chat_open', { event_category: 'chat_widget' });
                }
            }
        };
        
        chatClose.onclick = () => {
            state.isOpen = false;
            chatWindow.classList.remove('open');
        };
        
        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && state.isOpen) {
                state.isOpen = false;
                chatWindow.classList.remove('open');
            }
        });
        
        // Send message
        const sendMessage = () => {
            const text = chatInput.value.trim();
            if (text) {
                handleUserMessage(text);
                chatInput.value = '';
            }
        };
        
        chatSend.onclick = sendMessage;
        chatInput.onkeypress = (e) => {
            if (e.key === 'Enter') sendMessage();
        };
        
        // Auto-open after delay on certain pages (optional)
        // Uncomment to enable:
        // setTimeout(() => {
        //     if (!state.isOpen && !sessionStorage.getItem('scws_chat_shown')) {
        //         chatButton.click();
        //         sessionStorage.setItem('scws_chat_shown', '1');
        //     }
        // }, 30000);
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose for external access
    window.SCWSChat = {
        open: () => document.getElementById('scws-chat-button').click(),
        close: () => {
            state.isOpen = false;
            document.getElementById('scws-chat-window').classList.remove('open');
        },
        getLeads: () => JSON.parse(localStorage.getItem('scws_chat_leads') || '[]')
    };
})();
