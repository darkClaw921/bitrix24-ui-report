// Main chat interface functionality

class ChatInterface {
    constructor() {
        this.currentConversationId = null;
        this.isStreaming = false;
        this.streamingMessageId = null;
        this.conversations = [];
        this.providers = [];
        
        this.initializeElements();
        this.bindEvents();
        this.loadInitialData();
    }
    
    initializeElements() {
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.messagesContainer = document.getElementById('messages-container');
        this.conversationsContainer = document.getElementById('conversations-container');
        this.providerSelect = document.getElementById('provider-select');
        this.modelSelect = document.getElementById('model-select');
        this.streamModeCheckbox = document.getElementById('stream-mode');
        this.conversationTitle = document.getElementById('conversation-title');
        this.currentProviderSpan = document.getElementById('current-provider');
        this.newConversationBtn = document.getElementById('new-conversation-btn');
        this.clearChatBtn = document.getElementById('clear-chat-btn');
    }
    
    bindEvents() {
        // Message input events
        this.messageInput?.addEventListener('input', () => this.handleInputChange());
        this.messageInput?.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Send button
        this.sendBtn?.addEventListener('click', () => this.sendMessage());
        
        // Provider selection
        this.providerSelect?.addEventListener('change', () => this.handleProviderChange());
        
        // New conversation
        this.newConversationBtn?.addEventListener('click', () => this.createNewConversation());
        
        // Clear chat
        this.clearChatBtn?.addEventListener('click', () => this.clearCurrentChat());
        
        // Auto-resize textarea
        this.messageInput?.addEventListener('input', () => this.autoResizeTextarea());
        
        // WebSocket message handlers
        if (window.wsManager) {
            window.wsManager.onMessage('chunk', (data) => this.handleStreamChunk(data));
            window.wsManager.onMessage('message_complete', (data) => this.handleStreamComplete(data));
            window.wsManager.onMessage('error', (data) => this.handleStreamError(data));
            window.wsManager.onMessage('message_received', (data) => this.handleMessageReceived(data));
        }
    }
    
    async loadInitialData() {
        try {
            // Load providers
            await this.loadProviders();
            
            // Load conversations
            await this.loadConversations();
            
            // Create new conversation if none exists
            if (this.conversations.length === 0) {
                await this.createNewConversation();
            } else {
                // Load the most recent conversation
                this.selectConversation(this.conversations[0]);
            }
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Ошибка загрузки данных: ' + error.message);
        }
    }
    
    async loadProviders() {
        try {
            const response = await fetch('/api/providers');
            if (!response.ok) throw new Error('Failed to load providers');
            
            const providers = await response.json();
            this.providers = Object.keys(providers);
            
            // Update provider select
            if (this.providerSelect) {
                this.providerSelect.innerHTML = '';
                this.providers.forEach(provider => {
                    const option = document.createElement('option');
                    option.value = provider;
                    option.textContent = provider.charAt(0).toUpperCase() + provider.slice(1);
                    this.providerSelect.appendChild(option);
                });
            }
            
            // Load models for default provider
            if (this.providers.length > 0) {
                await this.loadModels(this.providers[0]);
            }
        } catch (error) {
            console.error('Error loading providers:', error);
        }
    }
    
    async loadModels(provider) {
        try {
            const response = await fetch(`/api/providers`);
            if (!response.ok) throw new Error('Failed to load provider info');
            
            const providers = await response.json();
            const providerInfo = providers[provider];
            
            if (this.modelSelect && providerInfo && providerInfo.supported_models) {
                this.modelSelect.innerHTML = '<option value=\"\">Модель по умолчанию</option>';
                providerInfo.supported_models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    this.modelSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading models:', error);
        }
    }
    
    async loadConversations() {
        try {
            const response = await fetch('/api/conversations');
            if (!response.ok) throw new Error('Failed to load conversations');
            
            const data = await response.json();
            this.conversations = data || [];
            this.renderConversations();
        } catch (error) {
            console.error('Error loading conversations:', error);
        }
    }
    
    renderConversations() {
        if (!this.conversationsContainer) return;
        
        this.conversationsContainer.innerHTML = '';
        
        if (this.conversations.length === 0) {
            this.conversationsContainer.innerHTML = `
                <div class=\"no-conversations\">
                    <p>Нет сохраненных диалогов</p>
                </div>
            `;
            return;
        }
        
        this.conversations.forEach(conversation => {
            const conversationElement = document.createElement('div');
            conversationElement.className = 'conversation-item';
            conversationElement.innerHTML = `
                <div class=\"conversation-title\">${this.escapeHtml(conversation.title)}</div>
                <div class=\"conversation-meta\">
                    <span>${conversation.message_count} сообщений</span>
                    <span>${this.formatDate(conversation.updated_at)}</span>
                </div>
            `;
            
            conversationElement.addEventListener('click', () => {
                this.selectConversation(conversation);
            });
            
            this.conversationsContainer.appendChild(conversationElement);
        });
    }
    
    async selectConversation(conversation) {
        try {
            // Update UI
            this.currentConversationId = conversation.id;
            this.updateConversationTitle(conversation.title);
            
            // Update active conversation in sidebar
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            
            const conversationElements = document.querySelectorAll('.conversation-item');
            const index = this.conversations.findIndex(c => c.id === conversation.id);
            if (index >= 0 && conversationElements[index]) {
                conversationElements[index].classList.add('active');
            }
            
            // Clear current messages and show loading
            if (this.messagesContainer) {
                this.messagesContainer.innerHTML = '<div class="loading-messages">Загрузка сообщений...</div>';
            }
            
            // Load messages
            await this.loadConversationMessages(conversation.id);
            
            // Connect WebSocket
            if (window.wsManager) {
                window.wsManager.connect(conversation.id);
            }
        } catch (error) {
            console.error('Error selecting conversation:', error);
            this.showError('Ошибка выбора диалога: ' + error.message);
        }
    }
    
    async loadConversationMessages(conversationId) {
        try {
            const response = await fetch(`/api/chat/conversations/${conversationId}/messages`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const messages = await response.json();
            this.renderMessages(messages);
        } catch (error) {
            console.error('Error loading messages:', error);
            this.showError('Ошибка загрузки сообщений: ' + error.message);
        }
    }
    
    renderMessages(messages) {
        if (!this.messagesContainer) return;
        
        this.messagesContainer.innerHTML = '';
        
        if (messages.length === 0) {
            this.showWelcomeMessage();
            return;
        }
        
        messages.forEach(message => {
            this.addMessageToUI(message, false);
        });
        
        this.scrollToBottom();
    }
    
    addMessageToUI(message, animate = true) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.role} ${animate ? 'fade-in' : ''}`;
        
        const isUser = message.role === 'user';
        const avatar = isUser ? 'У' : 'AI';
        
        messageElement.innerHTML = `
            <div class=\"message-avatar\">${avatar}</div>
            <div class=\"message-content\">
                <div class=\"message-bubble\">
                    <div class=\"message-text\">${this.formatMessageContent(message.content)}</div>
                </div>
                <div class=\"message-meta\">
                    <span>${this.formatTime(message.timestamp)}</span>
                    ${message.provider ? `<span>${message.provider}</span>` : ''}
                    ${message.model ? `<span>${message.model}</span>` : ''}
                </div>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageElement);
        
        // Render chart if exists
        if (message.chart_data) {
            this.addChartToMessage(messageElement, message.chart_data);
        }
        
        if (animate) {
            this.scrollToBottom();
        }
        
        return messageElement;
    }
    
    addChartToMessage(messageElement, chartData) {
        const chartContainer = document.createElement('div');
        const chartId = 'chart-' + Date.now() + Math.random().toString(36).substr(2, 9);
        chartContainer.id = chartId;
        
        const messageContent = messageElement.querySelector('.message-content');
        messageContent.appendChild(chartContainer);
        
        // Render chart
        if (window.chartManager) {
            window.chartManager.renderChart(chartData, chartId);
        }
    }
    
    formatMessageContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
            .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    showWelcomeMessage() {
        this.messagesContainer.innerHTML = `
            <div class=\"welcome-message\">
                <div class=\"welcome-icon\">
                    <i data-lucide=\"bot\"></i>
                </div>
                <h3>Добро пожаловать в AI Chat!</h3>
                <p>Начните диалог с искусственным интеллектом. Вы можете задавать вопросы, просить создать графики и диаграммы, или просто общаться.</p>
                <div class=\"welcome-features\">
                    <div class=\"feature\">
                        <i data-lucide=\"bar-chart-3\"></i>
                        <span>Автоматическое создание графиков</span>
                    </div>
                    <div class=\"feature\">
                        <i data-lucide=\"globe\"></i>
                        <span>Поддержка разных LLM провайдеров</span>
                    </div>
                    <div class=\"feature\">
                        <i data-lucide=\"save\"></i>
                        <span>Сохранение диалогов</span>
                    </div>
                </div>
            </div>
        `;
        
        // Initialize icons
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }
    
    async sendMessage() {
        const message = this.messageInput?.value.trim();
        if (!message || this.isStreaming) return;
        
        const provider = this.providerSelect?.value || 'openai';
        const model = this.modelSelect?.value || null;
        const streamMode = this.streamModeCheckbox?.checked || false;
        
        // Clear input
        this.messageInput.value = '';
        this.updateSendButton();
        this.autoResizeTextarea();
        
        // Hide welcome message if shown
        const welcomeMessage = this.messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        // Add user message to UI
        const userMessage = {
            content: message,
            role: 'user',
            timestamp: new Date().toISOString(),
            provider: null,
            model: null
        };
        this.addMessageToUI(userMessage);
        
        try {
            if (streamMode && window.wsManager && window.wsManager.isConnected) {
                await this.sendStreamingMessage(message, provider, model);
            } else {
                await this.sendRegularMessage(message, provider, model);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Ошибка отправки сообщения: ' + error.message);
        }
    }
    
    async sendStreamingMessage(message, provider, model) {
        this.isStreaming = true;
        this.updateSendButton();
        
        // Create placeholder for assistant message
        const assistantMessage = {
            content: '',
            role: 'assistant',
            timestamp: new Date().toISOString(),
            provider: provider,
            model: model
        };
        
        const messageElement = this.addMessageToUI(assistantMessage);
        const messageText = messageElement.querySelector('.message-text');
        this.streamingMessageId = messageElement;
        
        // Send via WebSocket
        window.wsManager.sendMessage(message, provider, model);
    }
    
    async sendRegularMessage(message, provider, model) {
        this.isStreaming = true;
        this.updateSendButton();
        
        try {
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message,
                    conversation_id: this.currentConversationId,
                    provider,
                    model,
                    stream: false
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.addMessageToUI(data.message);
                
                // Update conversation ID if new
                if (data.conversation_id !== this.currentConversationId) {
                    this.currentConversationId = data.conversation_id;
                    // Reload conversations to reflect new conversation
                    await this.loadConversations();
                    // Update the title if it's a new conversation
                    if (data.message && this.conversationTitle) {
                        this.updateConversationTitle('Новый диалог');
                    }
                }
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } finally {
            this.isStreaming = false;
            this.updateSendButton();
        }
    }
    
    handleStreamChunk(data) {
        if (!this.streamingMessageId) return;
        
        const messageText = this.streamingMessageId.querySelector('.message-text');
        if (messageText && data.content) {
            messageText.innerHTML += this.formatMessageContent(data.content);
            this.scrollToBottom();
        }
    }
    
    handleStreamComplete(data) {
        this.isStreaming = false;
        this.updateSendButton();
        this.streamingMessageId = null;
        
        // Update conversation ID if changed
        if (data.conversation_id !== this.currentConversationId) {
            this.currentConversationId = data.conversation_id;
            this.loadConversations();
        }
        
        // Add chart if present
        if (data.chart_data && this.streamingMessageId) {
            this.addChartToMessage(this.streamingMessageId, data.chart_data);
        }
    }
    
    handleStreamError(data) {
        this.isStreaming = false;
        this.updateSendButton();
        this.streamingMessageId = null;
        this.showError(data.message || 'Ошибка при получении ответа');
    }
    
    handleMessageReceived(data) {
        // Show typing indicator or acknowledgment
        console.log('Message received by server');
    }
    
    async createNewConversation() {
        try {
            const response = await fetch('/api/chat/conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: 'Новый диалог'
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }
            
            const conversation = await response.json();
            await this.loadConversations();
            this.selectConversation(conversation);
        } catch (error) {
            console.error('Error creating conversation:', error);
            this.showError('Ошибка создания диалога: ' + error.message);
        }
    }
    
    clearCurrentChat() {
        if (this.messagesContainer) {
            this.showWelcomeMessage();
        }
        
        // Clear charts
        if (window.chartManager) {
            window.chartManager.destroyAllCharts();
        }
    }
    
    handleInputChange() {
        this.updateSendButton();
    }
    
    handleKeyDown(e) {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            this.sendMessage();
        }
    }
    
    handleProviderChange() {
        const provider = this.providerSelect?.value;
        if (provider) {
            this.loadModels(provider);
            this.updateCurrentProvider(provider);
        }
    }
    
    updateSendButton() {
        const hasText = this.messageInput?.value.trim().length > 0;
        if (this.sendBtn) {
            this.sendBtn.disabled = !hasText || this.isStreaming;
        }
    }
    
    updateCurrentProvider(provider) {
        if (this.currentProviderSpan) {
            this.currentProviderSpan.textContent = provider.charAt(0).toUpperCase() + provider.slice(1);
        }
    }
    
    updateConversationTitle(title) {
        if (this.conversationTitle) {
            this.conversationTitle.textContent = title;
        }
    }
    
    autoResizeTextarea() {
        if (this.messageInput) {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
        }
    }
    
    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }
    
    showError(message) {
        // Simple error display - could be enhanced with toast notifications
        console.error(message);
        alert(message);
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) {
            return 'сегодня';
        } else if (diffDays === 2) {
            return 'вчера';
        } else if (diffDays <= 7) {
            return `${diffDays} дн. назад`;
        } else {
            return date.toLocaleDateString('ru-RU');
        }
    }
    
    formatTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global chat interface instance
let chatInterface;

// Initialize chat interface
function initializeChat() {
    chatInterface = new ChatInterface();
    window.chatInterface = chatInterface;
}

// Export for global access immediately
window.initializeChat = initializeChat;

// Auto-initialize when script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeChat);
} else {
    // DOM already loaded
    initializeChat();
}"