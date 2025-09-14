/**
 * TRAE.AI Chat Integration System
 * 
 * Modern chat UI with real-time messaging, AI integration,
 * and connection to all existing integrations.
 * 
 * Features:
 * - Real-time WebSocket messaging
 * - AI-powered responses
 * - Integration commands (/weather,/news,/images,/pets)
 * - Rich media support
 * - Modern responsive UI
 * - Chat history persistence
 */class TraeChat {
    constructor(options = {}) {
        this.userId = options.userId || `user_${Date.now()}`;
        this.roomId = options.roomId || 'general';
        this.wsUrl = options.wsUrl || `ws://localhost:8000/chat/ws/${this.userId}?room_id=${this.roomId}`;
        this.apiUrl = options.apiUrl || 'http://localhost:8000/chat';
        
        this.socket = null;
        this.isConnected = false;
        this.messageHistory = [];
        this.currentRoom = this.roomId;//Chat history management
        this.chatHistory = JSON.parse(localStorage.getItem('traeChat_history') || '[]');
        this.maxHistorySize = 1000;
        this.currentConversationId = null;
        this.conversations = [];
        this.userId = this.generateUserId();
        
        this.init();
    }
    
    generateUserId() {
        let userId = localStorage.getItem('traeChat_userId');
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
            localStorage.setItem('traeChat_userId', userId);
        }
        return userId;
    }

    async loadConversations() {
        try {
            const response = await fetch(`/api/chat/conversations/${this.userId}`);
            if (response.ok) {
                const data = await response.json();
                this.conversations = data.conversations || [];
                this.updateConversationsList();
            }
        } catch (error) {
            console.warn('Failed to load conversations:', error);
        }
    }

    async createNewConversation(title = null) {
        try {
            const response = await fetch(`/api/chat/conversations/${this.userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentConversationId = data.conversation_id;
                await this.loadConversations();
                return data.conversation_id;
            }
        } catch (error) {
            console.warn('Failed to create conversation:', error);
        }
        return null;
    }

    async loadConversationMessages(conversationId) {
        try {
            const response = await fetch(`/api/chat/conversations/${this.userId}/${conversationId}/messages`);
            if (response.ok) {
                const data = await response.json();
                this.clearMessages();
                data.messages.forEach(msg => {
                    this.displayMessage(msg.content, msg.sender === 'user' ? 'user' : 'assistant', false);
                });
                this.currentConversationId = conversationId;
            }
        } catch (error) {
            console.warn('Failed to load conversation messages:', error);
        }
    }

    updateConversationsList() {//This would update a conversations sidebar if implemented//For now, we'll just log the conversations
        console.log('Available conversations:', this.conversations);
    }
    
    async init() {
        this.createChatUI();
        this.setupEventListeners();
        this.connectWebSocket();//Load conversations and chat history
        await this.loadConversations();//Create a new conversation if none exists
        if (this.conversations.length === 0) {
            await this.createNewConversation();
        } else {//Load the most recent conversation
            this.currentConversationId = this.conversations[0].id;
        }
        
        this.loadChatHistory();
    }
    
    createChatUI() {//Create main chat container
        const chatContainer = document.createElement('div');
        chatContainer.id = 'trae-chat-container';
        chatContainer.innerHTML = `
            <div class="chat-header">
                <div class="chat-title">
                    <h3>TRAE.AI Chat</h3>
                    <span class="connection-status" id="connection-status">Connecting...</span>
                </div>
                <div class="chat-controls">
                    <button id="toggle-chat" class="btn-toggle">−</button>
                    <button id="clear-chat" class="btn-clear">Clear</button>
                </div>
            </div>
            
            <div class="chat-body">
                <div class="chat-messages" id="chat-messages"></div>
                
                <div class="chat-input-container">
                    <div class="input-wrapper">
                        <input type="text" id="chat-input" placeholder="Type a message... (try/ai,/weather,/news,/images,/pets)" autocomplete="off">
                        <button id="send-button" class="btn-send">Send</button>
                    </div>
                    
                    <div class="chat-commands">
                        <button class="cmd-btn" data-cmd="/ai ">🤖 AI</button>
                        <button class="cmd-btn" data-cmd="/weather ">🌤️ Weather</button>
                        <button class="cmd-btn" data-cmd="/news ">📰 News</button>
                        <button class="cmd-btn" data-cmd="/images ">🖼️ Images</button>
                        <button class="cmd-btn" data-cmd="/pets ">🐕 Pets</button>
                    </div>
                </div>
            </div>
        `;//Add CSS styles
        this.addChatStyles();//Append to body
        document.body.appendChild(chatContainer);
    }
    
    addChatStyles() {
        const styles = `
            <style id="trae-chat-styles">
                #trae-chat-container {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    width: 400px;
                    height: 600px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 15px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    display: flex;
                    flex-direction: column;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    z-index: 10000;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.2);
                }
                
                .chat-header {
                    padding: 15px 20px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 15px 15px 0 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    backdrop-filter: blur(10px);
                }
                
                .chat-title h3 {
                    margin: 0;
                    color: white;
                    font-size: 18px;
                    font-weight: 600;
                }
                
                .connection-status {
                    font-size: 12px;
                    color: rgba(255,255,255,0.8);
                    margin-top: 2px;
                }
                
                .connection-status.connected {
                    color: #4ade80;
                }
                
                .connection-status.disconnected {
                    color: #f87171;
                }
                
                .chat-controls {
                    display: flex;
                    gap: 8px;
                }
                
                .btn-toggle, .btn-clear {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    width: 32px;
                    height: 32px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 16px;
                    transition: all 0.2s;
                }
                
                .btn-toggle:hover, .btn-clear:hover {
                    background: rgba(255,255,255,0.3);
                    transform: scale(1.05);
                }
                
                .chat-body {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    background: rgba(255,255,255,0.95);
                    margin: 0 10px 10px 10px;
                    border-radius: 10px;
                    overflow: hidden;
                }
                
                .chat-messages {
                    flex: 1;
                    padding: 15px;
                    overflow-y: auto;
                    scroll-behavior: smooth;
                }
                
                .chat-messages::-webkit-scrollbar {
                    width: 6px;
                }
                
                .chat-messages::-webkit-scrollbar-track {
                    background: #f1f1f1;
                    border-radius: 3px;
                }
                
                .chat-messages::-webkit-scrollbar-thumb {
                    background: #c1c1c1;
                    border-radius: 3px;
                }
                
                .message {
                    margin-bottom: 15px;
                    animation: fadeInUp 0.3s ease;
                }
                
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                .message.user {
                    text-align: right;
                }
                
                .message.ai {
                    text-align: left;
                }
                
                .message.system {
                    text-align: center;
                }
                
                .message-content {
                    display: inline-block;
                    max-width: 80%;
                    padding: 12px 16px;
                    border-radius: 18px;
                    font-size: 14px;
                    line-height: 1.4;
                    word-wrap: break-word;
                }
                
                .message.user .message-content {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                
                .message.ai .message-content {
                    background: #f3f4f6;
                    color: #374151;
                    border: 1px solid #e5e7eb;
                }
                
                .message.system .message-content {
                    background: #fef3c7;
                    color: #92400e;
                    font-style: italic;
                    font-size: 12px;
                }
                
                .message-time {
                    font-size: 11px;
                    color: #9ca3af;
                    margin-top: 4px;
                }
                
                .integration-data {
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 15px;
                    margin: 10px 0;
                }
                
                .integration-data h4 {
                    margin: 0 0 10px 0;
                    color: #1e293b;
                    font-size: 14px;
                    font-weight: 600;
                }
                
                .weather-data {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                    font-size: 13px;
                }
                
                .news-article {
                    border-bottom: 1px solid #e2e8f0;
                    padding-bottom: 10px;
                    margin-bottom: 10px;
                }
                
                .news-article:last-child {
                    border-bottom: none;
                    margin-bottom: 0;
                }
                
                .news-title {
                    font-weight: 600;
                    color: #1e293b;
                    font-size: 13px;
                    margin-bottom: 4px;
                }
                
                .news-description {
                    font-size: 12px;
                    color: #64748b;
                    margin-bottom: 4px;
                }
                
                .news-source {
                    font-size: 11px;
                    color: #94a3b8;
                }
                
                .image-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                    gap: 8px;
                }
                
                .image-item img {
                    width: 100%;
                    height: 80px;
                    object-fit: cover;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: transform 0.2s;
                }
                
                .image-item img:hover {
                    transform: scale(1.05);
                }
                
                .pet-item {
                    display: flex;
                    gap: 10px;
                    padding: 8px;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    margin-bottom: 8px;
                }
                
                .pet-photo {
                    width: 60px;
                    height: 60px;
                    border-radius: 8px;
                    object-fit: cover;
                }
                
                .pet-info {
                    flex: 1;
                }
                
                .pet-name {
                    font-weight: 600;
                    color: #1e293b;
                    font-size: 13px;
                }
                
                .pet-details {
                    font-size: 12px;
                    color: #64748b;
                }
                
                .chat-input-container {
                    padding: 15px;
                    border-top: 1px solid #e5e7eb;
                    background: white;
                }
                
                .input-wrapper {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 10px;
                }
                
                #chat-input {
                    flex: 1;
                    padding: 12px 16px;
                    border: 1px solid #d1d5db;
                    border-radius: 25px;
                    font-size: 14px;
                    outline: none;
                    transition: border-color 0.2s;
                }
                
                #chat-input:focus {
                    border-color: #667eea;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                }
                
                .btn-send {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 600;
                    transition: all 0.2s;
                }
                
                .btn-send:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                }
                
                .btn-send:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                    transform: none;
                }
                
                .chat-commands {
                    display: flex;
                    gap: 6px;
                    flex-wrap: wrap;
                }
                
                .cmd-btn {
                    background: #f3f4f6;
                    border: 1px solid #e5e7eb;
                    color: #374151;
                    padding: 6px 10px;
                    border-radius: 15px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: all 0.2s;
                }
                
                .cmd-btn:hover {
                    background: #e5e7eb;
                    transform: translateY(-1px);
                }
                
                .typing-indicator {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 16px;
                    color: #6b7280;
                    font-size: 13px;
                    font-style: italic;
                }
                
                .typing-dots {
                    display: flex;
                    gap: 3px;
                }
                
                .typing-dot {
                    width: 6px;
                    height: 6px;
                    background: #9ca3af;
                    border-radius: 50%;
                    animation: typingDot 1.4s infinite;
                }
                
                .typing-dot:nth-child(2) {
                    animation-delay: 0.2s;
                }
                
                .typing-dot:nth-child(3) {
                    animation-delay: 0.4s;
                }
                
                @keyframes typingDot {
                    0%, 60%, 100% {
                        transform: translateY(0);
                        opacity: 0.4;
                    }
                    30% {
                        transform: translateY(-10px);
                        opacity: 1;
                    }
                }
                
                .chat-minimized {
                    height: 60px !important;
                }
                
                .chat-minimized .chat-body {
                    display: none;
                }
                
                .error-message {
                    background: #fef2f2;
                    color: #dc2626;
                    padding: 10px;
                    border-radius: 8px;
                    margin: 10px 0;
                    font-size: 13px;
                    border: 1px solid #fecaca;
                }
                
                @media (max-width: 480px) {
                    #trae-chat-container {
                        width: calc(100vw - 20px);
                        height: calc(100vh - 40px);
                        bottom: 10px;
                        right: 10px;
                        left: 10px;
                    }
                }
            </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', styles);
    }
    
    setupEventListeners() {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');
        const toggleButton = document.getElementById('toggle-chat');
        const clearButton = document.getElementById('clear-chat');
        const commandButtons = document.querySelectorAll('.cmd-btn');//Send message on Enter or button click
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        sendButton.addEventListener('click', () => this.sendMessage());//Toggle chat minimize/maximize
        toggleButton.addEventListener('click', () => {
            const container = document.getElementById('trae-chat-container');
            container.classList.toggle('chat-minimized');
            toggleButton.textContent = container.classList.contains('chat-minimized') ? '+' : '−';
        });//Clear chat
        clearButton.addEventListener('click', () => {
            if (confirm('Clear all chat messages?')) {
                this.clearChat();
            }
        });//Command buttons
        commandButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const cmd = btn.dataset.cmd;
                chatInput.value = cmd;
                chatInput.focus();
            });
        });
    }
    
    connectWebSocket() {
        try {//Update WebSocket URL to include user ID
            this.wsUrl = this.wsUrl.includes('?') 
                ? this.wsUrl + `&user_id=${this.userId}`
                : this.wsUrl + `?user_id=${this.userId}`;
            
            this.socket = new WebSocket(this.wsUrl);
            
            this.socket.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus('Connected', 'connected');
                console.log('Chat WebSocket connected');
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleIncomingMessage(data);
            };
            
            this.socket.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus('Disconnected', 'disconnected');
                console.log('Chat WebSocket disconnected');//Attempt to reconnect after 3 seconds
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.connectWebSocket();
                    }
                }, 3000);
            };
            
            this.socket.onerror = (error) => {
                console.error('Chat WebSocket error:', error);
                this.updateConnectionStatus('Error', 'disconnected');
            };
            
        } catch (error) {
            console.error('Failed to connect to chat WebSocket:', error);
            this.updateConnectionStatus('Failed to connect', 'disconnected');
        }
    }
    
    clearMessages() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        this.chatHistory = [];
        this.messageHistory = [];
    }
    
    updateConnectionStatus(text, className) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = text;
            statusElement.className = `connection-status ${className}`;
        }
    }
    
    sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || !this.isConnected) return;//Add user message to UI immediately
        this.addMessage({
            type: 'message',
            user_id: this.userId,
            content: message,
            message_type: 'text',
            timestamp: new Date().toISOString()
        }, true);//Send via WebSocket
        this.socket.send(JSON.stringify({
            content: message,
            type: 'text',
            metadata: {}
        }));//Clear input
        input.value = '';//Show typing indicator for AI/integration commands
        if (message.startsWith('/ai ') || message.startsWith('/weather ') || 
            message.startsWith('/news ') || message.startsWith('/images ') || 
            message.startsWith('/pets ')) {
            this.showTypingIndicator();
        }
    }
    
    handleIncomingMessage(data) {
        this.hideTypingIndicator();
        
        if (data.type === 'message') {//Regular chat message from another user
            if (data.user_id !== this.userId) {
                this.addMessage(data);
            }
        } else if (data.type === 'system') {//System message
            this.addSystemMessage(data.content, data.timestamp);
        } else if (data.type === 'ai_response') {//AI response
            this.addAIMessage(data.content, data.timestamp);
        } else if (data.type === 'integration_data') {//Integration data (weather, news, images, pets)
            this.addIntegrationMessage(data);
        }
    }
    
    addMessage(data, isOwnMessage = false) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isOwnMessage ? 'user' : 'other'}`;
        
        const time = new Date(data.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="message-content">${this.escapeHtml(data.content)}</div>
            <div class="message-time">${time}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addSystemMessage(content, timestamp) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        
        const time = new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="message-content">${this.escapeHtml(content)}</div>
            <div class="message-time">${time}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addAIMessage(content, timestamp) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai';
        
        const time = new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="message-content">🤖 ${this.escapeHtml(content)}</div>
            <div class="message-time">${time}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addIntegrationMessage(data) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        
        const time = new Date(data.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        let content = '';
        
        if (data.integration_type === 'weather' && data.data.location) {
            content = `
                <div class="integration-data">
                    <h4>🌤️ Weather in ${data.data.location}</h4>
                    <div class="weather-data">
                        <div><strong>Temperature:</strong> ${data.data.temperature}°C</div>
                        <div><strong>Condition:</strong> ${data.data.description}</div>
                        <div><strong>Humidity:</strong> ${data.data.humidity}%</div>
                        <div><strong>Wind:</strong> ${data.data.wind_speed} m/s</div>
                    </div>
                </div>
            `;
        } else if (data.integration_type === 'news' && data.data.articles) {
            content = `
                <div class="integration-data">
                    <h4>📰 Latest News</h4>
                    ${data.data.articles.map(article => `
                        <div class="news-article">
                            <div class="news-title">${this.escapeHtml(article.title)}</div>
                            <div class="news-description">${this.escapeHtml(article.description || '')}</div>
                            <div class="news-source">${this.escapeHtml(article.source)} • <a href="${article.url}" target="_blank">Read more</a></div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (data.integration_type === 'images' && data.data.images) {
            content = `
                <div class="integration-data">
                    <h4>🖼️ Images</h4>
                    <div class="image-grid">
                        ${data.data.images.map(image => `
                            <div class="image-item">
                                <img src="${image.url}" alt="${this.escapeHtml(image.description || '')}" 
                                     onclick="window.open('${image.url}', '_blank')">
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        } else if (data.integration_type === 'pets' && data.data.pets) {
            content = `
                <div class="integration-data">
                    <h4>🐕 Available Pets</h4>
                    ${data.data.pets.map(pet => `
                        <div class="pet-item">
                            ${pet.photos && pet.photos[0] ? `<img src="${pet.photos[0].small}" alt="${pet.name}" class="pet-photo">` : ''}
                            <div class="pet-info">
                                <div class="pet-name">${this.escapeHtml(pet.name || 'Unknown')}</div>
                                <div class="pet-details">
                                    ${pet.breeds && pet.breeds.primary ? `${pet.breeds.primary} • ` : ''}
                                    ${pet.age || 'Unknown age'} • ${pet.gender || 'Unknown gender'}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (data.data.error) {
            content = `<div class="error-message">❌ ${this.escapeHtml(data.data.error)}</div>`;
        }
        
        messageDiv.innerHTML = `
            ${content}
            <div class="message-time">${time}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        const existingIndicator = document.querySelector('.typing-indicator');
        
        if (existingIndicator) return;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <span>AI is thinking</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const indicator = document.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    async loadChatHistory() {
        try {
            const response = await fetch(`${this.apiUrl}/rooms/${this.roomId}/history?limit=50`);
            if (response.ok) {
                const data = await response.json();
                data.messages.forEach(message => {
                    this.addMessage({
                        type: 'message',
                        user_id: message.user_id,
                        content: message.content,
                        message_type: message.message_type,
                        timestamp: message.timestamp
                    }, message.user_id === this.userId);
                });
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }
    
    clearChat() {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = '';//Also clear on server
        fetch(`${this.apiUrl}/rooms/${this.roomId}/history`, {
            method: 'DELETE'
        }).catch(error => {
            console.error('Failed to clear chat history on server:', error);
        });
    }
    
    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }//Public methods
    destroy() {
        if (this.socket) {
            this.socket.close();
        }
        
        const container = document.getElementById('trae-chat-container');
        const styles = document.getElementById('trae-chat-styles');
        
        if (container) container.remove();
        if (styles) styles.remove();
    }
    
    sendCustomMessage(message, type = 'text') {
        if (this.isConnected && this.socket) {
            this.socket.send(JSON.stringify({
                content: message,
                type: type,
                metadata: {}
            }));
        }
    }
    
    changeRoom(roomId) {
        this.roomId = roomId;
        this.currentRoom = roomId;//Reconnect to new room
        if (this.socket) {
            this.socket.close();
        }
        
        this.wsUrl = this.wsUrl.replace(/room_id=[^&]*/, `room_id=${roomId}`);
        this.connectWebSocket();//Clear current messages and load new room history
        document.getElementById('chat-messages').innerHTML = '';
        this.loadChatHistory();
    }
}//Auto-initialize chat when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.traeChat = new TraeChat();
    });
} else {
    window.traeChat = new TraeChat();
}//Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TraeChat;
}