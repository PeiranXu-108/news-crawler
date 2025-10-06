/**
 * Main application logic for the News Crawler desktop app
 */

class NewsCrawlerApp {
    constructor() {
        this.currentSection = 'dashboard';
        this.currentTask = null;
        this.currentArticle = null;
        this.tasks = [];
        this.articles = [];
        this.sources = [];
        this.filters = {
            status: '',
            source: '',
            task: '',
            search: ''
        };

        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupWebSocket();
        await this.loadInitialData();
        this.showSection('dashboard');
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                this.showSection(section);
            });
        });

        // Header buttons
        document.getElementById('newTaskBtn').addEventListener('click', () => this.showNewTaskModal());
        document.getElementById('newTaskBtn2').addEventListener('click', () => this.showNewTaskModal());
        document.getElementById('settingsBtn').addEventListener('click', () => this.showSettingsModal());

        // Section refresh buttons
        document.getElementById('refreshDashboard').addEventListener('click', () => this.loadDashboard());
        document.getElementById('refreshTasks').addEventListener('click', () => this.loadTasks());
        document.getElementById('refreshArticles').addEventListener('click', () => this.loadArticles());
        document.getElementById('refreshSources').addEventListener('click', () => this.loadSources());

        // Modal events
        this.setupModalEvents();

        // Form submissions
        document.getElementById('newTaskForm').addEventListener('submit', (e) => this.handleNewTask(e));
        document.getElementById('addSourceForm').addEventListener('submit', (e) => this.handleAddSource(e));

        // Filter events
        document.getElementById('statusFilter').addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.loadTasks();
        });

        document.getElementById('searchArticles').addEventListener('input', (e) => {
            this.filters.search = e.target.value;
            this.loadArticles();
        });

        document.getElementById('sourceFilter').addEventListener('change', (e) => {
            this.filters.source = e.target.value;
            this.loadArticles();
        });

        document.getElementById('taskFilter').addEventListener('change', (e) => {
            this.filters.task = e.target.value;
            this.loadArticles();
        });

        // Export functionality
        document.getElementById('exportArticles').addEventListener('click', () => this.exportArticles());

        // Settings
        document.getElementById('saveSettings').addEventListener('click', () => this.saveSettings());

        // WebSocket events
        document.addEventListener('task-progress', (e) => this.handleTaskProgress(e.detail));
        document.addEventListener('websocket-message', (e) => this.handleWebSocketMessage(e.detail));
    }

    setupModalEvents() {
        // Modal close events
        document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                this.hideModal(modal.id);
            });
        });

        // Click outside modal to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal.id);
                }
            });
        });

        // Regenerate summary
        document.getElementById('regenerateSummary').addEventListener('click', () => {
            if (this.currentArticle) {
                this.regenerateArticleSummary(this.currentArticle.id);
            }
        });
    }

    setupWebSocket() {
        try {
            api.connectWebSocket();
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    }

    async loadInitialData() {
        this.showLoading();
        try {
            await Promise.all([
                this.loadDashboard(),
                this.loadSources()
            ]);
        } catch (error) {
            this.showToast('Failed to load initial data', 'error');
            console.error('Error loading initial data:', error);
        } finally {
            this.hideLoading();
        }
    }

    showSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Show section
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');

        this.currentSection = sectionName;

        // Load section data
        switch (sectionName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'tasks':
                this.loadTasks();
                break;
            case 'articles':
                this.loadArticles();
                break;
            case 'sources':
                this.loadSources();
                break;
        }
    }

    async loadDashboard() {
        try {
            const [tasks, articles, sources] = await Promise.all([
                api.getTasks(),
                api.getArticles({ limit: 1000 }),
                api.getRSSSources()
            ]);

            this.tasks = tasks;
            this.articles = articles;
            this.sources = sources;

            // Update stats
            document.getElementById('totalTasks').textContent = tasks.length;
            document.getElementById('totalArticles').textContent = articles.length;
            document.getElementById('runningTasks').textContent = tasks.filter(t => t.status === 'running').length;
            document.getElementById('activeSources').textContent = sources.filter(s => s.is_active).length;

            // Update recent tasks
            this.updateRecentTasks(tasks.slice(0, 5));

        } catch (error) {
            this.showToast('Failed to load dashboard', 'error');
            console.error('Error loading dashboard:', error);
        }
    }

    async loadTasks() {
        try {
            const params = {};
            if (this.filters.status) {
                params.status = this.filters.status;
            }

            const tasks = await api.getTasks(params);
            this.tasks = tasks;
            this.updateTasksList(tasks);

        } catch (error) {
            this.showToast('Failed to load tasks', 'error');
            console.error('Error loading tasks:', error);
        }
    }

    async loadArticles() {
        try {
            const params = {};
            if (this.filters.source) {
                params.source = this.filters.source;
            }
            if (this.filters.task) {
                params.task_id = this.filters.task;
            }

            const articles = await api.getArticles(params);
            this.articles = articles;

            // Filter by search term
            let filteredArticles = articles;
            if (this.filters.search) {
                const searchTerm = this.filters.search.toLowerCase();
                filteredArticles = articles.filter(article => 
                    article.title.toLowerCase().includes(searchTerm) ||
                    article.summary?.toLowerCase().includes(searchTerm) ||
                    article.source.toLowerCase().includes(searchTerm)
                );
            }

            this.updateArticlesList(filteredArticles);
            this.updateArticleFilters(articles);

        } catch (error) {
            this.showToast('Failed to load articles', 'error');
            console.error('Error loading articles:', error);
        }
    }

    async loadSources() {
        try {
            const sources = await api.getRSSSources();
            this.sources = sources;
            this.updateSourcesList(sources);

        } catch (error) {
            this.showToast('Failed to load sources', 'error');
            console.error('Error loading sources:', error);
        }
    }

    updateRecentTasks(tasks) {
        const container = document.getElementById('recentTasksList');
        container.innerHTML = '';

        if (tasks.length === 0) {
            container.innerHTML = '<p class="text-center">No recent tasks</p>';
            return;
        }

        tasks.forEach(task => {
            const taskElement = this.createTaskElement(task);
            container.appendChild(taskElement);
        });
    }

    updateTasksList(tasks) {
        const container = document.getElementById('tasksList');
        container.innerHTML = '';

        if (tasks.length === 0) {
            container.innerHTML = '<p class="text-center">No tasks found</p>';
            return;
        }

        tasks.forEach(task => {
            const taskElement = this.createTaskElement(task);
            container.appendChild(taskElement);
        });
    }

    createTaskElement(task) {
        const div = document.createElement('div');
        div.className = 'task-item';
        
        const progressBar = task.status === 'running' ? 
            `<div class="progress-bar">
                <div class="progress-fill" style="width: ${task.progress}%"></div>
            </div>` : '';

        div.innerHTML = `
            <div class="task-info">
                <h4>${task.query}</h4>
                <div class="task-meta">
                    <span>Created: ${api.formatRelativeTime(task.created_at)}</span>
                    <span>Limit: ${task.limit}</span>
                    <span>Articles: ${task.processed_articles}/${task.total_articles}</span>
                </div>
                ${progressBar}
            </div>
            <div class="task-actions">
                <span class="task-status ${task.status}">${task.status}</span>
                ${task.status === 'failed' ? 
                    `<button class="btn btn-outline" onclick="app.retryTask(${task.id})">
                        <i class="fas fa-redo"></i>
                    </button>` : ''
                }
                <button class="btn btn-danger" onclick="app.deleteTask(${task.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;

        return div;
    }

    updateArticlesList(articles) {
        const container = document.getElementById('articlesList');
        container.innerHTML = '';

        if (articles.length === 0) {
            container.innerHTML = '<p class="text-center">No articles found</p>';
            return;
        }

        articles.forEach(article => {
            const articleElement = this.createArticleElement(article);
            container.appendChild(articleElement);
        });
    }

    createArticleElement(article) {
        const div = document.createElement('div');
        div.className = 'article-item';
        div.onclick = () => this.showArticleDetail(article);

        const tags = article.tags ? article.tags.map(tag => `<span class="tag">${tag}</span>`).join('') : '';

        div.innerHTML = `
            <div class="article-header">
                <div class="article-title">${article.title}</div>
                <div class="article-meta">
                    <span class="article-source">${article.source}</span>
                    <span class="article-date">${api.formatRelativeTime(article.published)}</span>
                </div>
            </div>
            <div class="article-summary">${api.truncateText(article.summary || 'No summary available')}</div>
            <div class="article-tags">${tags}</div>
        `;

        return div;
    }

    updateSourcesList(sources) {
        const container = document.getElementById('sourcesList');
        container.innerHTML = '';

        if (sources.length === 0) {
            container.innerHTML = '<p class="text-center">No sources found</p>';
            return;
        }

        sources.forEach(source => {
            const sourceElement = this.createSourceElement(source);
            container.appendChild(sourceElement);
        });
    }

    createSourceElement(source) {
        const div = document.createElement('div');
        div.className = 'source-item';

        div.innerHTML = `
            <div class="source-info">
                <h4>${source.name}</h4>
                <div class="source-url">${source.url_template}</div>
                <div class="task-meta">
                    <span>Priority: ${source.priority}</span>
                    <span>Query Support: ${source.supports_query ? 'Yes' : 'No'}</span>
                    <span>Status: ${source.is_active ? 'Active' : 'Inactive'}</span>
                </div>
            </div>
            <div class="source-actions">
                <button class="btn btn-outline" onclick="app.editSource(${source.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger" onclick="app.deleteSource(${source.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;

        return div;
    }

    updateArticleFilters(articles) {
        // Update source filter
        const sourceFilter = document.getElementById('sourceFilter');
        const sources = [...new Set(articles.map(a => a.source))].sort();
        
        sourceFilter.innerHTML = '<option value="">All Sources</option>';
        sources.forEach(source => {
            const option = document.createElement('option');
            option.value = source;
            option.textContent = source;
            sourceFilter.appendChild(option);
        });

        // Update task filter
        const taskFilter = document.getElementById('taskFilter');
        const tasks = [...new Set(articles.map(a => a.task_id))].sort();
        
        taskFilter.innerHTML = '<option value="">All Tasks</option>';
        tasks.forEach(taskId => {
            const task = this.tasks.find(t => t.id === taskId);
            if (task) {
                const option = document.createElement('option');
                option.value = taskId;
                option.textContent = `${task.query} (${taskId})`;
                taskFilter.appendChild(option);
            }
        });
    }

    // Modal Management
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    }

    showNewTaskModal() {
        // Reset form
        document.getElementById('newTaskForm').reset();
        document.getElementById('taskLimit').value = '50';
        this.showModal('newTaskModal');
    }

    showSettingsModal() {
        this.showModal('settingsModal');
    }

    showArticleDetail(article) {
        this.currentArticle = article;
        
        document.getElementById('articleTitle').textContent = article.title;
        document.getElementById('articleSource').textContent = article.source;
        document.getElementById('articleDate').textContent = api.formatDate(article.published);
        document.getElementById('articleUrl').href = article.url;
        document.getElementById('articleSummary').innerHTML = article.summary || 'No summary available';
        document.getElementById('articleContent').innerHTML = article.text || 'No content available';
        
        this.showModal('articleModal');
    }

    // Form Handlers
    async handleNewTask(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const taskData = {
            query: formData.get('taskQuery'),
            since: formData.get('taskSince') || null,
            limit: parseInt(formData.get('taskLimit')) || 50,
            custom_feeds: formData.get('customFeeds') ? 
                formData.get('customFeeds').split('\n').filter(url => url.trim()) : null
        };

        try {
            this.showLoading();
            await api.createTask(taskData);
            this.hideModal('newTaskModal');
            this.showToast('Task created successfully', 'success');
            this.loadTasks();
            this.loadDashboard();
        } catch (error) {
            this.showToast(`Failed to create task: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleAddSource(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const sourceData = {
            name: formData.get('sourceName'),
            url_template: formData.get('sourceUrl'),
            supports_query: formData.get('supportsQuery') === 'on',
            priority: parseInt(formData.get('sourcePriority')) || 0
        };

        try {
            this.showLoading();
            await api.createRSSSource(sourceData);
            this.hideModal('addSourceModal');
            this.showToast('Source added successfully', 'success');
            this.loadSources();
        } catch (error) {
            this.showToast(`Failed to add source: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Task Actions
    async retryTask(taskId) {
        try {
            this.showLoading();
            await api.retryTask(taskId);
            this.showToast('Task retry initiated', 'success');
            this.loadTasks();
        } catch (error) {
            this.showToast(`Failed to retry task: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task and all its articles?')) {
            return;
        }

        try {
            this.showLoading();
            await api.deleteTask(taskId);
            this.showToast('Task deleted successfully', 'success');
            this.loadTasks();
            this.loadDashboard();
        } catch (error) {
            this.showToast(`Failed to delete task: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async deleteSource(sourceId) {
        if (!confirm('Are you sure you want to delete this RSS source?')) {
            return;
        }

        try {
            this.showLoading();
            await api.deleteRSSSource(sourceId);
            this.showToast('Source deleted successfully', 'success');
            this.loadSources();
        } catch (error) {
            this.showToast(`Failed to delete source: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async regenerateArticleSummary(articleId) {
        try {
            this.showLoading();
            await api.regenerateArticleSummary(articleId);
            this.showToast('Summary regenerated successfully', 'success');
            this.loadArticles();
            
            // Update current article if it's the same one
            if (this.currentArticle && this.currentArticle.id === articleId) {
                const updatedArticle = await api.getArticle(articleId);
                this.currentArticle = updatedArticle;
                document.getElementById('articleSummary').innerHTML = updatedArticle.summary || 'No summary available';
            }
        } catch (error) {
            this.showToast(`Failed to regenerate summary: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Export functionality
    async exportArticles() {
        try {
            const articles = await api.getArticles();
            const dataStr = JSON.stringify(articles, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = `news-articles-${new Date().toISOString().split('T')[0]}.json`;
            link.click();
            
            this.showToast('Articles exported successfully', 'success');
        } catch (error) {
            this.showToast(`Failed to export articles: ${error.message}`, 'error');
        }
    }

    // Settings
    async saveSettings() {
        try {
            const strategy = document.getElementById('summaryStrategy').value;
            const apiUrl = document.getElementById('apiBaseUrl').value;
            
            if (strategy) {
                await api.setSummaryStrategy(strategy);
            }
            
            if (apiUrl && apiUrl !== api.baseURL) {
                api.baseURL = apiUrl;
                api.disconnectWebSocket();
                api.connectWebSocket();
            }
            
            this.hideModal('settingsModal');
            this.showToast('Settings saved successfully', 'success');
        } catch (error) {
            this.showToast(`Failed to save settings: ${error.message}`, 'error');
        }
    }

    // WebSocket Event Handlers
    handleTaskProgress(data) {
        console.log('Task progress update:', data);
        
        // Update task in current list
        const taskIndex = this.tasks.findIndex(t => t.id === data.task_id);
        if (taskIndex !== -1) {
            this.tasks[taskIndex].progress = data.progress;
            this.tasks[taskIndex].status = data.status;
            
            // Refresh current view if showing tasks
            if (this.currentSection === 'tasks') {
                this.loadTasks();
            } else if (this.currentSection === 'dashboard') {
                this.loadDashboard();
            }
        }
    }

    handleWebSocketMessage(data) {
        console.log('WebSocket message:', data);
    }

    // Utility Methods
    showLoading() {
        document.getElementById('loadingOverlay').classList.add('active');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.remove('active');
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'exclamation-circle' :
                    type === 'warning' ? 'exclamation-triangle' : 'info-circle';
        
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NewsCrawlerApp();
});
