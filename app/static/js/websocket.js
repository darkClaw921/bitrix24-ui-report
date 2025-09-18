// WebSocket management for real-time chat

class WebSocketManager {
    constructor() {
        this.socket = null;
        this.conversationId = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageHandlers = new Map();
        
        this.statusElement = document.getElementById('connection-status');
        this.statusDot = this.statusElement?.querySelector('.status-dot');
    }
    
    connect(conversationId) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.disconnect();
        }
        
        this.conversationId = conversationId;
        this.updateStatus('connecting', 'Подключение...');
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${conversationId}`;
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateStatus('connected', 'Подключено');
                console.log('WebSocket connected to:', wsUrl);
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket message received:', data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.socket.onclose = (event) => {
                this.isConnected = false;
                this.updateStatus('disconnected', 'Отключено');
                console.log('WebSocket disconnected:', event.code, event.reason);
                
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('disconnected', 'Ошибка подключения');
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.updateStatus('disconnected', 'Ошибка подключения');
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'Manual disconnect');
            this.socket = null;
        }
        this.isConnected = false;
        this.updateStatus('disconnected', 'Отключено');
    }
    
    sendMessage(message, provider = 'openai', model = null, temperature = 0.7, maxTokens = 1000) {
        if (!this.isConnected || !this.socket) {
            throw new Error('WebSocket не подключен');
        }
        
        const messageData = {
            message,
            provider,
            model,
            temperature,
            max_tokens: maxTokens
        };
        
        this.socket.send(JSON.stringify(messageData));
    }
    
    handleMessage(data) {
        const handler = this.messageHandlers.get(data.type);
        if (handler) {
            handler(data);
        } else {
            console.warn('No handler for message type:', data.type);
        }
    }
    
    onMessage(type, handler) {
        this.messageHandlers.set(type, handler);
    }
    
    offMessage(type) {
        this.messageHandlers.delete(type);
    }
    
    updateStatus(status, text) {
        if (this.statusDot) {
            this.statusDot.className = `status-dot ${status}`;
        }
        if (this.statusElement) {
            const textElement = this.statusElement.querySelector('span:last-child');
            if (textElement) {
                textElement.textContent = text;
            }
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        this.updateStatus('connecting', `Переподключение через ${Math.ceil(delay / 1000)}с...`);
        
        setTimeout(() => {
            if (this.conversationId) {
                this.connect(this.conversationId);
            }
        }, delay);
    }
    
    isConnectedToConversation(conversationId) {
        return this.isConnected && this.conversationId === conversationId;
    }
}

// Global WebSocket manager instance
window.wsManager = new WebSocketManager();