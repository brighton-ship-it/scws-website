/**
 * SCWS Chat Widget
 * Simple chat interface for Southern California Well Service
 */

(function() {
    // Configuration
    const CONFIG = {
        businessName: 'Southern California Well Service',
        phone: '(760) 440-8520',
        greeting: "Hi! 👋 I'm here to help with your water well questions. How can I assist you today?",
        quickReplies: [
            "I need pump repair",
            "Get a drilling quote", 
            "Emergency - no water!",
            "Schedule maintenance"
        ],
        offlineMessage: "We typically respond within a few hours during business hours (Mon-Fri 7AM-5PM). For emergencies, call us directly!"
    };

    // Auto-responses based on keywords
    const RESPONSES = {
        emergency: {
            keywords: ['emergency', 'no water', 'urgent', 'asap', 'broken'],
            response: `🚨 For emergencies, please call us directly at ${CONFIG.phone} - we offer same-day emergency service! Someone will be there fast.`
        },
        drilling: {
            keywords: ['drill', 'new well', 'drilling', 'dig'],
            response: `Great question! Well drilling costs depend on depth, geology, and access. In San Diego backcountry, most wells are 200-400ft using air drilling. Want me to connect you with our team for a free site evaluation?`
        },
        pump: {
            keywords: ['pump', 'repair', 'not working', 'pressure', 'motor'],
            response: `Pump issues are our specialty! Common problems include motor failure, pressure switch issues, or dropping water levels. We can diagnose and often fix same-day. Would you like to schedule a service call?`
        },
        cost: {
            keywords: ['cost', 'price', 'how much', 'quote', 'estimate'],
            response: `We offer free estimates! Costs vary by job - pump repairs typically $200-1500, new wells $15K-40K+ depending on depth. Want to describe your situation and we'll give you a ballpark?`
        },
        maintenance: {
            keywords: ['maintenance', 'service', 'checkup', 'inspection'],
            response: `Smart thinking! Regular maintenance extends well life and catches issues early. We recommend annual inspections. Want to schedule one?`
        },
        testing: {
            keywords: ['water test', 'quality', 'safe', 'contamination', 'bacteria'],
            response: `We offer comprehensive water testing for bacteria, minerals, and contaminants. Results typically in 3-5 days. This is especially important for new wells or if you notice changes in taste/smell.`
        },
        hours: {
            keywords: ['hours', 'open', 'available', 'when'],
            response: `We're available Mon-Fri 7AM-5PM for regular service, but we offer 24/7 emergency response. Just call ${CONFIG.phone}!`
        },
        area: {
            keywords: ['where', 'area', 'location', 'service area', 'come to'],
            response: `We serve San Diego, Riverside, and San Bernardino Counties - including Ramona, Valley Center, Temecula, Anza, Hemet, and surrounding areas. Where are you located?`
        }
    };

    // Styles
    const STYLES = `
        #scws-chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            font-family: 'Inter', -apple-system, sans-serif;
        }
        
        #scws-chat-button {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #4e9271 0%, #3d7a5d 100%);
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(78, 146, 113, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        #scws-chat-button:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(78, 146, 113, 0.6);
        }
        
        #scws-chat-button svg {
            width: 28px;
            height: 28px;
            fill: white;
        }
        
        #scws-chat-window {
            display: none;
            position: absolute;
            bottom: 70px;
            right: 0;
            width: 360px;
            max-width: calc(100vw - 40px);
            height: 500px;
            max-height: calc(100vh - 100px);
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            flex-direction: column;
            overflow: hidden;
        }
        
        #scws-chat-window.open {
            display: flex;
        }
        
        #scws-chat-header {
            background: linear-gradient(135deg, #1f3b4d 0%, #2a4d63 100%);
            color: white;
            padding: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        #scws-chat-header img {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: white;
            padding: 4px;
        }
        
        #scws-chat-header-info h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
        }
        
        #scws-chat-header-info p {
            margin: 2px 0 0;
            font-size: 12px;
            opacity: 0.8;
        }
        
        #scws-chat-close {
            margin-left: auto;
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 4px;
            opacity: 0.8;
        }
        
        #scws-chat-close:hover {
            opacity: 1;
        }
        
        #scws-chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .scws-message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .scws-message.bot {
            background: #f1f5f9;
            color: #1f3b4d;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }
        
        .scws-message.user {
            background: #4e9271;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        
        #scws-quick-replies {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 0 16px 12px;
        }
        
        .scws-quick-reply {
            background: #e8f5ee;
            color: #4e9271;
            border: 1px solid #4e9271;
            padding: 8px 14px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .scws-quick-reply:hover {
            background: #4e9271;
            color: white;
        }
        
        #scws-chat-input-area {
            display: flex;
            gap: 8px;
            padding: 12px 16px;
            border-top: 1px solid #e5e7eb;
            background: #f9fafb;
        }
        
        #scws-chat-input {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid #d1d5db;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        
        #scws-chat-input:focus {
            border-color: #4e9271;
        }
        
        #scws-chat-send {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #4e9271;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        
        #scws-chat-send:hover {
            background: #3d7a5d;
        }
        
        #scws-chat-send svg {
            width: 18px;
            height: 18px;
            fill: white;
        }
        
        #scws-chat-cta {
            padding: 12px 16px;
            background: #fef3c7;
            border-top: 1px solid #fcd34d;
            text-align: center;
        }
        
        #scws-chat-cta a {
            color: #1f3b4d;
            font-weight: 600;
            text-decoration: none;
            font-size: 14px;
        }
        
        #scws-chat-cta a:hover {
            text-decoration: underline;
        }
        
        @media (max-width: 480px) {
            #scws-chat-window {
                width: calc(100vw - 20px);
                right: -10px;
                bottom: 70px;
                height: calc(100vh - 100px);
                border-radius: 16px 16px 0 0;
            }
        }
    `;

    // Create widget HTML
    function createWidget() {
        const widget = document.createElement('div');
        widget.id = 'scws-chat-widget';
        widget.innerHTML = `
            <style>${STYLES}</style>
            
            <div id="scws-chat-window">
                <div id="scws-chat-header">
                    <img src="/images/logo.png" alt="SCWS">
                    <div id="scws-chat-header-info">
                        <h3>SCWS Support</h3>
                        <p>Typically replies within minutes</p>
                    </div>
                    <button id="scws-chat-close">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 6L6 18M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                
                <div id="scws-chat-messages"></div>
                
                <div id="scws-quick-replies"></div>
                
                <div id="scws-chat-input-area">
                    <input type="text" id="scws-chat-input" placeholder="Type your message...">
                    <button id="scws-chat-send">
                        <svg viewBox="0 0 24 24">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
                
                <div id="scws-chat-cta">
                    <a href="tel:7604408520">📞 Call Now: ${CONFIG.phone}</a>
                </div>
            </div>
            
            <button id="scws-chat-button">
                <svg viewBox="0 0 24 24">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                </svg>
            </button>
        `;
        document.body.appendChild(widget);
        return widget;
    }

    // Add message to chat
    function addMessage(text, isUser = false) {
        const messages = document.getElementById('scws-chat-messages');
        const msg = document.createElement('div');
        msg.className = `scws-message ${isUser ? 'user' : 'bot'}`;
        msg.textContent = text;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    }

    // Show quick replies
    function showQuickReplies(replies) {
        const container = document.getElementById('scws-quick-replies');
        container.innerHTML = '';
        replies.forEach(text => {
            const btn = document.createElement('button');
            btn.className = 'scws-quick-reply';
            btn.textContent = text;
            btn.onclick = () => handleUserMessage(text);
            container.appendChild(btn);
        });
    }

    // Find best response
    function findResponse(message) {
        const lower = message.toLowerCase();
        
        for (const [key, data] of Object.entries(RESPONSES)) {
            if (data.keywords.some(kw => lower.includes(kw))) {
                return data.response;
            }
        }
        
        // Default response
        return `Thanks for reaching out! For the best assistance, please call us at ${CONFIG.phone} or fill out our contact form. We typically respond within a few hours during business hours.`;
    }

    // Handle user message
    function handleUserMessage(text) {
        addMessage(text, true);
        
        // Hide quick replies after first message
        document.getElementById('scws-quick-replies').innerHTML = '';
        
        // Simulate typing delay
        setTimeout(() => {
            const response = findResponse(text);
            addMessage(response);
            
            // Show follow-up options
            setTimeout(() => {
                showQuickReplies([
                    "Talk to someone",
                    "Get a quote",
                    "Learn more"
                ]);
            }, 500);
        }, 800);
    }

    // Initialize
    function init() {
        const widget = createWidget();
        
        const chatButton = document.getElementById('scws-chat-button');
        const chatWindow = document.getElementById('scws-chat-window');
        const chatClose = document.getElementById('scws-chat-close');
        const chatInput = document.getElementById('scws-chat-input');
        const chatSend = document.getElementById('scws-chat-send');
        
        // Toggle chat
        chatButton.onclick = () => {
            chatWindow.classList.toggle('open');
            if (chatWindow.classList.contains('open')) {
                // Show greeting on first open
                const messages = document.getElementById('scws-chat-messages');
                if (messages.children.length === 0) {
                    addMessage(CONFIG.greeting);
                    showQuickReplies(CONFIG.quickReplies);
                }
                chatInput.focus();
            }
        };
        
        chatClose.onclick = () => {
            chatWindow.classList.remove('open');
        };
        
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
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
