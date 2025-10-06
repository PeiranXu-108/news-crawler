/**
 * API client for communicating with the backend service
 */

class NewsCrawlerAPI {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.wsConnection = null;
        this.wsReconnectInterval = null;
    }

    // HTTP API Methods
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Health check
    async healthCheck() {
        return this.request('/health');
    }

    // Task Management
    async createTask(taskData) {
        return this.request('/tasks', {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
    }

    async getTasks(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/tasks?${queryString}` : '/tasks';
        return this.request(endpoint);
    }

    async getTask(taskId) {
        return this.request(`/tasks/${taskId}`);
    }

    async deleteTask(taskId) {
        return this.request(`/tasks/${taskId}`, {
            method: 'DELETE'
        });
    }

    async retryTask(taskId) {
        return this.request(`/tasks/${taskId}/retry`, {
            method: 'POST'
        });
    }

    // Article Management
    async getArticles(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/articles?${queryString}` : '/articles';
        return this.request(endpoint);
    }

    async getArticle(articleId) {
        return this.request(`/articles/${articleId}`);
    }

    async regenerateArticleSummary(articleId, strategy = null) {
        const body = strategy ? { strategy } : {};
        return this.request(`/articles/${articleId}/regenerate-summary`, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    // RSS Source Management
    async getRSSSources() {
        return this.request('/rss-sources');
    }

    async createRSSSource(sourceData) {
        return this.request('/rss-sources', {
            method: 'POST',
            body: JSON.stringify(sourceData)
        });
    }

    async updateRSSSource(sourceId, sourceData) {
        return this.request(`/rss-sources/${sourceId}`, {
            method: 'PUT',
            body: JSON.stringify(sourceData)
        });
    }

    async deleteRSSSource(sourceId) {
        return this.request(`/rss-sources/${sourceId}`, {
            method: 'DELETE'
        });
    }

    // Summary Service
    async getSummaryStats() {
        return this.request('/summary/stats');
    }

    async regenerateSummaries(articleIds, strategy = null) {
        const body = { article_ids: articleIds };
        if (strategy) {
            body.strategy = strategy;
        }
        return this.request('/summary/regenerate', {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    async setSummaryStrategy(strategy) {
        return this.request('/summary/strategy', {
            method: 'PUT',
            body: JSON.stringify({ strategy })
        });
    }

    // WebSocket Connection
    connectWebSocket() {
        if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
            return;
        }

        const wsUrl = this.baseURL.replace('http', 'ws') + '/ws';
        
        try {
            this.wsConnection = new WebSocket(wsUrl);
            
            this.wsConnection.onopen = () => {
                console.log('WebSocket connected');
                this.clearReconnectInterval();
            };

            this.wsConnection.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.wsConnection.onclose = () => {
                console.log('WebSocket disconnected');
                this.scheduleReconnect();
            };

            this.wsConnection.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        if (this.wsReconnectInterval) {
            return;
        }

        this.wsReconnectInterval = setInterval(() => {
            console.log('Attempting to reconnect WebSocket...');
            this.connectWebSocket();
        }, 5000);
    }

    clearReconnectInterval() {
        if (this.wsReconnectInterval) {
            clearInterval(this.wsReconnectInterval);
            this.wsReconnectInterval = null;
        }
    }

    handleWebSocketMessage(data) {
        // Emit custom events for different message types
        const event = new CustomEvent('websocket-message', {
            detail: data
        });
        document.dispatchEvent(event);

        // Handle specific message types
        switch (data.type) {
            case 'progress_update':
                this.handleProgressUpdate(data);
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    handleProgressUpdate(data) {
        // Emit progress update event
        const event = new CustomEvent('task-progress', {
            detail: data
        });
        document.dispatchEvent(event);
    }

    disconnectWebSocket() {
        this.clearReconnectInterval();
        
        if (this.wsConnection) {
            this.wsConnection.close();
            this.wsConnection = null;
        }
    }

    // Utility Methods
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    formatRelativeTime(dateString) {
        if (!dateString) return 'N/A';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return this.formatDate(dateString);
    }

    truncateText(text, maxLength = 150) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    highlightKeywords(text, keywords) {
        if (!text || !keywords) return text;
        
        const keywordList = keywords.toLowerCase().split(/\s+/);
        let highlightedText = text;
        
        keywordList.forEach(keyword => {
            if (keyword.length > 2) {
                const regex = new RegExp(`(${keyword})`, 'gi');
                highlightedText = highlightedText.replace(regex, '<mark>$1</mark>');
            }
        });
        
        return highlightedText;
    }
}

// Create global API instance
window.api = new NewsCrawlerAPI();
