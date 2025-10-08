/**
 * KGiSL Chatbot Widget JavaScript
 * Handles user interactions, API calls, and chat functionality
 */

class KGiSLChatbot {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000'; // Adjust for your API endpoint
        this.messages = [];
        this.sessionId = this.generateSessionId();
        this.isTyping = false;
        this.lastMessage = null;
        this.theme = localStorage.getItem('theme') || 'light';
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupTheme();
        this.setupAutoResize();
        this.checkApiConnection();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    setupEventListeners() {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');

        // Input event listeners
        chatInput.addEventListener('input', this.handleInputChange.bind(this));
        chatInput.addEventListener('keydown', this.handleKeyDown.bind(this));
        
        // Send button
        sendButton.addEventListener('click', this.sendMessage.bind(this));

        // Character count
        chatInput.addEventListener('input', this.updateCharCount.bind(this));
    }

    setupTheme() {
        document.body.classList.toggle('dark-theme', this.theme === 'dark');
        const themeIcon = document.querySelector('#theme-toggle i');
        if (themeIcon) {
            themeIcon.className = this.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    setupAutoResize() {
        const textarea = document.getElementById('chat-input');
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        });
    }

    async checkApiConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            if (!response.ok) {
                throw new Error('API not available');
            }
            console.log('API connection successful');
        } catch (error) {
            console.warn('API connection failed:', error);
            this.showConnectionWarning();
        }
    }

    showConnectionWarning() {
        const welcomeSection = document.getElementById('welcome-section');
        if (welcomeSection) {
            const warningDiv = document.createElement('div');
            warningDiv.className = 'connection-warning';
            warningDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <p>Unable to connect to the chatbot service. Some features may be limited.</p>
            `;
            welcomeSection.appendChild(warningDiv);
        }
    }

    handleInputChange(event) {
        const value = event.target.value.trim();
        const sendButton = document.getElementById('send-button');
        sendButton.disabled = !value || this.isTyping;
        
        // Hide welcome section when user starts typing
        if (value && this.messages.length === 0) {
            this.hideWelcomeSection();
        }
    }

    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }

    updateCharCount() {
        const input = document.getElementById('chat-input');
        const charCount = document.getElementById('char-count');
        const currentLength = input.value.length;
        charCount.textContent = currentLength;
        
        // Change color if approaching limit
        charCount.style.color = currentLength > 900 ? '#e74c3c' : 
                               currentLength > 800 ? '#f39c12' : '#6c757d';
    }

    hideWelcomeSection() {
        const welcomeSection = document.getElementById('welcome-section');
        if (welcomeSection) {
            welcomeSection.style.display = 'none';
        }
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || this.isTyping) return;

        // Store for retry functionality
        this.lastMessage = message;

        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        input.value = '';
        input.style.height = 'auto';
        this.updateCharCount();
        
        // Disable send button and show typing
        this.setTyping(true);
        
        try {
            // Call API
            const response = await this.callChatAPI(message);
            
            // Add bot response
            this.addMessage(response.response, 'bot', response.sources, response.confidence);
            
        } catch (error) {
            console.error('Chat error:', error);
            this.handleChatError(error);
        } finally {
            this.setTyping(false);
        }
    }

    sendQuickMessage(message) {
        const input = document.getElementById('chat-input');
        input.value = message;
        this.handleInputChange({ target: input });
        this.sendMessage();
    }

    async callChatAPI(message) {
        const response = await fetch(`${this.apiBaseUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: this.sessionId,
                user_id: 'web_user'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    addMessage(content, sender, sources = null, confidence = null) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const timestamp = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        let messageHTML = `
            <div class="message-content">
                <div class="message-text">${this.formatMessage(content)}</div>
                <div class="message-time">${timestamp}</div>
            </div>
        `;

        // Add sources and confidence for bot messages
        if (sender === 'bot' && (sources || confidence !== null)) {
            messageHTML += this.createMessageFooter(sources, confidence);
        }

        messageDiv.innerHTML = messageHTML;
        messagesContainer.appendChild(messageDiv);
        
        // Store message
        this.messages.push({
            content,
            sender,
            timestamp: new Date(),
            sources,
            confidence
        });

        // Scroll to bottom
        this.scrollToBottom();
    }

    createMessageFooter(sources, confidence) {
        let footerHTML = '<div class="message-footer">';
        
        // Confidence indicator
        if (confidence !== null) {
            const confidencePercent = Math.round(confidence * 100);
            const confidenceClass = confidence > 0.7 ? 'high' : confidence > 0.4 ? 'medium' : 'low';
            footerHTML += `
                <div class="confidence-indicator ${confidenceClass}">
                    <i class="fas fa-chart-bar"></i>
                    <span>Confidence: ${confidencePercent}%</span>
                </div>
            `;
        }

        // Sources
        if (sources && sources.length > 0) {
            footerHTML += '<div class="sources-section">';
            footerHTML += '<span class="sources-label"><i class="fas fa-link"></i> Sources:</span>';
            footerHTML += '<div class="sources-list">';
            
            sources.slice(0, 3).forEach((source, index) => {
                const similarity = Math.round((source.similarity || 0) * 100);
                footerHTML += `
                    <div class="source-item" title="${source.snippet || ''}">
                        <span class="source-title">${source.title || 'Unknown Source'}</span>
                        <span class="source-similarity">${similarity}%</span>
                    </div>
                `;
            });
            
            footerHTML += '</div></div>';
        }
        
        footerHTML += '</div>';
        return footerHTML;
    }

    formatMessage(message) {
        // Simple message formatting
        message = message.replace(/\n/g, '<br>');
        
        // Make URLs clickable
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        message = message.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        
        // Make email addresses clickable
        const emailRegex = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
        message = message.replace(emailRegex, '<a href="mailto:$1">$1</a>');
        
        return message;
    }

    setTyping(isTyping) {
        this.isTyping = isTyping;
        const typingIndicator = document.getElementById('typing-indicator');
        const sendButton = document.getElementById('send-button');
        const input = document.getElementById('chat-input');
        
        typingIndicator.style.display = isTyping ? 'block' : 'none';
        sendButton.disabled = isTyping || !input.value.trim();
        
        if (isTyping) {
            this.scrollToBottom();
        }
    }

    handleChatError(error) {
        let errorMessage = 'Sorry, I encountered an error while processing your request.';
        
        if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Unable to connect to the chat service. Please check your internet connection.';
        } else if (error.message.includes('HTTP 500')) {
            errorMessage = 'The chat service is experiencing issues. Please try again later.';
        }

        this.addMessage(errorMessage, 'bot');
        this.showErrorModal(errorMessage);
    }

    showErrorModal(message) {
        const modal = document.getElementById('error-modal');
        const messageElement = document.getElementById('error-message');
        messageElement.textContent = message;
        modal.style.display = 'flex';
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Global functions
    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = '';
            this.messages = [];
            
            // Show welcome section again
            const welcomeSection = document.getElementById('welcome-section');
            if (welcomeSection) {
                welcomeSection.style.display = 'block';
            }
        }
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        this.setupTheme();
    }

    closeModal() {
        document.getElementById('error-modal').style.display = 'none';
    }

    retryLastMessage() {
        this.closeModal();
        if (this.lastMessage) {
            const input = document.getElementById('chat-input');
            input.value = this.lastMessage;
            this.sendMessage();
        }
    }
}

// Global functions for HTML onclick events
let chatbot;

function sendQuickMessage(message) {
    chatbot.sendQuickMessage(message);
}

function clearChat() {
    chatbot.clearChat();
}

function toggleTheme() {
    chatbot.toggleTheme();
}

function closeModal() {
    chatbot.closeModal();
}

function retryLastMessage() {
    chatbot.retryLastMessage();
}

function sendMessage() {
    chatbot.sendMessage();
}

// Initialize chatbot when page loads
document.addEventListener('DOMContentLoaded', () => {
    chatbot = new KGiSLChatbot();
});