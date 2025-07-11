/**
 * Enhanced Core Dashboard Functionality
 * Handles data loading, navigation, state management, and user interactions
 * 
 * **Enhanced Features:**
 * - Proper method binding to UI controls
 * - Advanced filtering and search capabilities
 * - Real-time data updates with caching
 * - Enhanced error handling and user feedback
 * - Performance optimizations
 */

class CodeIntelligenceDashboard {
    constructor() {
        this.data = {
            files: [],
            classes: [],
            functions: [],
            services: [],
            stats: {}
        };
        this.currentSection = 'overview';
        this.filters = {
            files: { type: '', domain: '', complexity: '' },
            classes: { type: 'all' },
            functions: { type: 'all', async: false },
            services: { type: 'all' }
        };
        this.isInitialized = false;
        this.loadingStates = new Set();
    }

    // Enhanced initialization with better error handling
    async init() {
        if (this.isInitialized) {
            console.debug("✅ Dashboard already initialized");
            return;
        }

        console.log('🚀 Initializing Enhanced Code Intelligence Dashboard...');

        try {
            // Initialize in proper order
            this.initializeEventListeners();
            await this.loadStats();
            await this.loadCharts();
            await this.loadLayerCounts();
            
            // Load initial section data
            await this.loadInitialData();
            
            this.isInitialized = true;
            console.debug("✅ Enhanced Dashboard initialized successfully");
            
            // Show success notification
            this.showNotification('Dashboard initialized successfully!', 'success');
        } catch (error) {
            console.error('❌ Failed to initialize dashboard:', error);
            this.showError('Failed to initialize dashboard: ' + error.message);
        }
    }

    // Enhanced event listeners with proper ID handling
    initializeEventListeners() {
        // Fix search input ID mismatch
        const searchInput = document.getElementById('search-input'); // Fixed ID
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
            searchInput.addEventListener('focus', () => this.showSearchSuggestions());
            searchInput.addEventListener('blur', () => this.hideSearchSuggestions());
        }

        // Enhanced keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboard.bind(this));
        
        // Add refresh functionality
        this.setupRefreshHandlers();
        
        // Add section change listeners
        this.setupSectionChangeListeners();
    }

    // Load initial data for better UX
    async loadInitialData() {
        try {
            // Pre-load files data for faster navigation
            if (window.dataLoader) {
                await window.dataLoader.loadFiles();
            }
        } catch (error) {
            console.warn('Failed to load initial data:', error);
        }
    }

    // === FIXED METHOD BINDINGS FOR UI CONTROLS ===

    // Files section methods
    async loadFiles() {
        return this.executeWithLoading('files', async () => {
            if (window.dataLoader) {
                await window.dataLoader.loadFiles();
                this.showNotification('Files loaded successfully', 'success');
            }
        });
    }

    async loadHighComplexityFiles() {
        return this.executeWithLoading('files', async () => {
            await this.loadFiles();
            this.applyComplexityFilter('high');
            this.showNotification('High complexity files filtered', 'info');
        });
    }

    async loadFilesByDomain() {
        return this.executeWithLoading('files', async () => {
            await this.loadFiles();
            this.showDomainFilterDialog();
        });
    }

    // Classes section methods
    async loadClasses() {
        return this.executeWithLoading('classes', async () => {
            if (window.dataLoader) {
                await window.dataLoader.loadClasses();
                this.showNotification('Classes loaded successfully', 'success');
            }
        });
    }

    async loadServiceClasses() {
        return this.executeWithLoading('classes', async () => {
            await this.loadClasses();
            this.applyClassTypeFilter('service');
            this.showNotification('Service classes filtered', 'info');
        });
    }

    // Functions section methods
    async loadFunctions() {
        return this.executeWithLoading('functions', async () => {
            if (window.dataLoader) {
                await window.dataLoader.loadFunctions();
                this.showNotification('Functions loaded successfully', 'success');
            }
        });
    }

    async loadAsyncFunctions() {
        return this.executeWithLoading('functions', async () => {
            await this.loadFunctions();
            this.applyAsyncFilter(true);
            this.showNotification('Async functions filtered', 'info');
        });
    }

    // Services section methods
    async loadServices() {
        return this.executeWithLoading('services', async () => {
            if (window.dataLoader) {
                await window.dataLoader.loadServices();
                this.showNotification('Services loaded successfully', 'success');
            }
        });
    }

    async loadServicesByDomain() {
        return this.executeWithLoading('services', async () => {
            await this.loadServices();
            this.showDomainFilterDialog('services');
        });
    }

    // === ENHANCED FILTERING METHODS ===

    applyComplexityFilter(level) {
        const container = document.getElementById('filesList');
        if (!container) return;

        const items = container.querySelectorAll('.file-item');
        items.forEach(item => {
            const complexityText = item.querySelector('.complexity-score')?.textContent || '0';
            const complexity = parseInt(complexityText);
            
            let show = false;
            switch(level) {
                case 'low': show = complexity <= 10; break;
                case 'medium': show = complexity > 10 && complexity <= 25; break;
                case 'high': show = complexity > 25; break;
                case 'all': show = true; break;
            }
            
            item.style.display = show ? 'block' : 'none';
        });

        this.updateFilterButtons('complexity', level);
    }

    applyClassTypeFilter(type) {
        const container = document.getElementById('classesList');
        if (!container) return;

        const items = container.querySelectorAll('.class-item');
        items.forEach(item => {
            const classType = item.getAttribute('data-class-type') || '';
            const show = type === 'all' || classType.toLowerCase().includes(type.toLowerCase());
            item.style.display = show ? 'block' : 'none';
        });

        this.updateFilterButtons('class-type', type);
    }

    applyAsyncFilter(asyncOnly) {
        const container = document.getElementById('functionsList');
        if (!container) return;

        const items = container.querySelectorAll('.function-item');
        items.forEach(item => {
            const isAsync = item.getAttribute('data-is-async') === 'true';
            const show = !asyncOnly || isAsync;
            item.style.display = show ? 'block' : 'none';
        });

        this.updateFilterButtons('function-type', asyncOnly ? 'async' : 'all');
    }

    applyParameterFilter(level) {
        const container = document.getElementById('functionsList');
        if (!container) return;

        const items = container.querySelectorAll('.function-item');
        items.forEach(item => {
            const paramCountText = item.querySelector('.param-count')?.textContent || '0';
            const paramCount = parseInt(paramCountText);
            
            let show = false;
            switch(level) {
                case 'low': show = paramCount <= 2; break;
                case 'medium': show = paramCount > 2 && paramCount <= 5; break;
                case 'high': show = paramCount > 5; break;
                case 'all': show = true; break;
            }
            
            item.style.display = show ? 'block' : 'none';
        });

        this.updateFilterButtons('function-params', level);
    }

    updateFilterButtons(filterType, activeValue) {
        const buttons = document.querySelectorAll(`[data-filter-type="${filterType}"]`);
        buttons.forEach(btn => {
            const btnValue = btn.getAttribute('data-filter-value');
            if (btnValue === activeValue) {
                btn.classList.remove('usa-button--outline');
                btn.classList.add('usa-button');
            } else {
                btn.classList.add('usa-button--outline');
                btn.classList.remove('usa-button');
            }
        });
    }

    // === ENHANCED UTILITY METHODS ===

    async executeWithLoading(section, operation) {
        if (this.loadingStates.has(section)) {
            console.log(`⏳ ${section} already loading, skipping...`);
            return;
        }

        this.loadingStates.add(section);
        this.showLoadingIndicator(section);

        try {
            await operation();
        } catch (error) {
            console.error(`❌ Failed to execute ${section} operation:`, error);
            this.showError(`Failed to load ${section}: ${error.message}`);
        } finally {
            this.loadingStates.delete(section);
            this.hideLoadingIndicator(section);
        }
    }

    showLoadingIndicator(section) {
        const button = document.querySelector(`[onclick*="${section}"]`);
        if (button) {
            button.disabled = true;
            button.innerHTML = button.innerHTML.replace(/^[^>]*>/, '⏳ ');
        }
    }

    hideLoadingIndicator(section) {
        const button = document.querySelector(`[onclick*="${section}"]`);
        if (button) {
            button.disabled = false;
            button.innerHTML = button.innerHTML.replace('⏳ ', '');
        }
    }

    showDomainFilterDialog(section = 'files') {
        const domains = this.getAvailableDomains(section);
        const modal = this.createModal('Domain Filter', this.createDomainFilterContent(domains, section));
        document.body.appendChild(modal);
    }

    getAvailableDomains(section) {
        const data = this.data[section] || [];
        const domains = [...new Set(data.map(item => item.domain).filter(Boolean))];
        return domains.sort();
    }

    createDomainFilterContent(domains, section) {
        return `
            <div class="domain-filter-content">
                <p>Select domains to filter:</p>
                <div class="domain-checkboxes">
                    ${domains.map(domain => `
                        <label class="usa-checkbox">
                            <input class="usa-checkbox__input" type="checkbox" value="${domain}" checked>
                            <span class="usa-checkbox__label">${domain}</span>
                        </label>
                    `).join('')}
                </div>
                <div class="modal-actions">
                    <button class="usa-button" onclick="this.applyDomainFilter('${section}')">Apply Filter</button>
                    <button class="usa-button usa-button--outline" onclick="this.closeModal()">Cancel</button>
                </div>
            </div>
        `;
    }

    setupRefreshHandlers() {
        // Add refresh button functionality
        const refreshBtn = document.getElementById('refreshData');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshAllData());
        }

        // Auto-refresh every 5 minutes
        setInterval(() => {
            if (this.isInitialized) {
                this.refreshStats();
            }
        }, 300000);
    }

    setupSectionChangeListeners() {
        // Listen for section changes and load data accordingly
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const target = mutation.target;
                    if (target.classList.contains('content-section') && target.classList.contains('active')) {
                        this.onSectionActivated(target.id);
                    }
                }
            });
        });

        document.querySelectorAll('.content-section').forEach(section => {
            observer.observe(section, { attributes: true });
        });
    }

    async onSectionActivated(sectionId) {
        console.log(`📍 Section activated: ${sectionId}`);
        
        // Auto-load data when section becomes active
        switch(sectionId) {
            case 'files':
                if (!this.data.files.length) await this.loadFiles();
                break;
            case 'classes':
                if (!this.data.classes.length) await this.loadClasses();
                break;
            case 'functions':
                if (!this.data.functions.length) await this.loadFunctions();
                break;
            case 'services':
                if (!this.data.services.length) await this.loadServices();
                break;
        }
    }

    async refreshAllData() {
        this.showNotification('Refreshing all data...', 'info');
        
        try {
            // Clear caches
            if (window.dataLoader) {
                window.dataLoader.clearCache();
            }
            
            // Reload current section data
            const activeSection = document.querySelector('.content-section.active');
            if (activeSection) {
                await this.onSectionActivated(activeSection.id);
            }
            
            // Refresh stats
            await this.loadStats();
            
            this.showNotification('Data refreshed successfully!', 'success');
        } catch (error) {
            this.showError('Failed to refresh data: ' + error.message);
        }
    }

    async refreshStats() {
        try {
            await this.loadStats();
        } catch (error) {
            console.warn('Failed to refresh stats:', error);
        }
    }

    // Enhanced system statistics loading
    async loadStats() {
        try {
            console.log('📊 Loading enhanced system statistics...');
            const response = await fetch('/api/stats');
            const result = await response.json();

            console.log('📈 Stats API response:', result);

            if (result.success) {
                this.data.stats = result.data;
                this.updateStatsDisplay();
                await this.loadAdditionalCounts();
            } else {
                console.error('❌ Stats API failed:', result);
                this.showError('Failed to load statistics: ' + (result.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('❌ Failed to load stats:', error);
            this.showError('Failed to load statistics: ' + error.message);
        }
    }

    // Load additional counts for classes and functions
    async loadAdditionalCounts() {
        try {
            // Get classes count
            const classesResponse = await fetch('/api/classes?limit=1');
            const classesData = await classesResponse.json();
            if (classesData.success && classesData.pagination) {
                this.data.stats.total_classes = classesData.pagination.total;
            }
            
            // Get functions count  
            const functionsResponse = await fetch('/api/functions?limit=1');
            const functionsData = await functionsResponse.json();
            if (functionsData.success && functionsData.pagination) {
                this.data.stats.total_functions = functionsData.pagination.total;
            }
            
            this.updateStatsDisplay();
        } catch (error) {
            console.error('Failed to load additional counts:', error);
        }
    }

    // Update stats display
    updateStatsDisplay() {
        const stats = this.data.stats;
        
        const elements = {
            'totalFiles': stats.total_files || '-',
            'totalClasses': stats.total_classes || '-',
            'totalFunctions': stats.total_functions || '-',
            'avgComplexity': stats.avg_complexity ? stats.avg_complexity.toFixed(1) : '-'
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    // Load and render charts
    async loadCharts() {
        try {
            const filesResponse = await fetch('/api/files?limit=1000');
            const filesData = await filesResponse.json();
            
            if (filesData.success) {
                this.renderComplexityChart(filesData.data);
                this.renderDomainChart(filesData.data);
            }
        } catch (error) {
            console.error('Failed to load chart data:', error);
        }
    }

    // Render complexity distribution chart
    renderComplexityChart(files) {
        const ctx = document.getElementById('complexityChart');
        if (!ctx) return;
        
        const chartContext = ctx.getContext('2d');
        
        // Group files by complexity ranges
        const ranges = {
            'Low (0-10)': 0,
            'Medium (11-25)': 0,
            'High (26-50)': 0,
            'Very High (50+)': 0
        };
        
        files.forEach(file => {
            const complexity = file.complexity || 0;
            if (complexity <= 10) ranges['Low (0-10)']++;
            else if (complexity <= 25) ranges['Medium (11-25)']++;
            else if (complexity <= 50) ranges['High (26-50)']++;
            else ranges['Very High (50+)']++;
        });
        
        new Chart(chartContext, {
            type: 'doughnut',
            data: {
                labels: Object.keys(ranges),
                datasets: [{
                    data: Object.values(ranges),
                    backgroundColor: [
                        '#28a745',
                        '#ffc107', 
                        '#fd7e14',
                        '#dc3545'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Render domain distribution chart
    renderDomainChart(files) {
        const ctx = document.getElementById('domainChart');
        if (!ctx) return;
        
        const chartContext = ctx.getContext('2d');
        
        // Count files by domain
        const domainCounts = {};
        files.forEach(file => {
            const domain = file.domain || 'unknown';
            domainCounts[domain] = (domainCounts[domain] || 0) + 1;
        });
        
        // Get top 10 domains
        const sortedDomains = Object.entries(domainCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10);
        
        new Chart(chartContext, {
            type: 'bar',
            data: {
                labels: sortedDomains.map(([domain]) => domain.split('.').pop() || domain),
                datasets: [{
                    label: 'Files',
                    data: sortedDomains.map(([,count]) => count),
                    backgroundColor: '#667eea'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Load layer counts for architectural overview
    async loadLayerCounts() {
        try {
            const response = await fetch('/api/files?limit=5000');
            const result = await response.json();
            
            if (result.success) {
                window.updateLayerCounts(result.data);
            }
        } catch (error) {
            console.error('Failed to load layer counts:', error);
        }
    }

    // === ENHANCED SEARCH FUNCTIONALITY ===

    async handleSearch(event) {
        const query = event.target.value.trim();
        
        if (query.length < 2) {
            this.hideSearchResults();
            return;
        }

        try {
            this.showSearchLoading();
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=50`);
            const result = await response.json();
            
            if (result.success) {
                this.displaySearchResults(result.data, query);
            } else {
                this.showSearchError('Search failed');
            }
        } catch (error) {
            console.error('Search failed:', error);
            this.showSearchError('Search failed: ' + error.message);
        }
    }

    displaySearchResults(results, query) {
        const container = this.getOrCreateSearchResultsContainer();
        
        if (results.length === 0) {
            container.innerHTML = `
                <div class="search-no-results">
                    <p>No results found for "${query}"</p>
                    <small>Try different keywords or check spelling</small>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="search-results-header">
                    <h4>Search Results (${results.length})</h4>
                    <button class="close-search" onclick="dashboard.hideSearchResults()">×</button>
                </div>
                <div class="search-results-list">
                    ${results.map(result => this.createSearchResultItem(result)).join('')}
                </div>
            `;
        }
        
        container.style.display = 'block';
    }

    createSearchResultItem(result) {
        const typeIcon = this.getTypeIcon(result.type);
        const typeClass = `search-result-${result.type}`;
        
        return `
            <div class="search-result-item ${typeClass}" onclick="dashboard.navigateToResult('${result.type}', ${result.id})">
                <div class="search-result-icon">${typeIcon}</div>
                <div class="search-result-content">
                    <div class="search-result-name">${result.name}</div>
                    <div class="search-result-meta">
                        <span class="search-result-type">${result.type}</span>
                        ${result.file_path ? `<span class="search-result-path">${result.file_path}</span>` : ''}
                        ${result.domain ? `<span class="search-result-domain">${result.domain}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    getTypeIcon(type) {
        const icons = {
            'file': '📁',
            'class': '🏗️',
            'function': '⚙️',
            'service': '🔧'
        };
        return icons[type] || '📄';
    }

    getOrCreateSearchResultsContainer() {
        let container = document.getElementById('searchResults');
        if (!container) {
            container = document.createElement('div');
            container.id = 'searchResults';
            container.className = 'search-results-container';
            
            const searchContainer = document.querySelector('.search-container');
            if (searchContainer) {
                searchContainer.appendChild(container);
            } else {
                document.body.appendChild(container);
            }
        }
        return container;
    }

    showSearchLoading() {
        const container = this.getOrCreateSearchResultsContainer();
        container.innerHTML = `
            <div class="search-loading">
                <div class="usa-spinner usa-spinner--small"></div>
                <span>Searching...</span>
            </div>
        `;
        container.style.display = 'block';
    }

    showSearchError(message) {
        const container = this.getOrCreateSearchResultsContainer();
        container.innerHTML = `
            <div class="search-error">
                <p>❌ ${message}</p>
            </div>
        `;
        container.style.display = 'block';
    }

    hideSearchResults() {
        const container = document.getElementById('searchResults');
        if (container) {
            container.style.display = 'none';
        }
    }

    showSearchSuggestions() {
        // Show recent searches or popular items
        const suggestions = this.getSearchSuggestions();
        if (suggestions.length > 0) {
            this.displaySearchResults(suggestions, '');
        }
    }

    getSearchSuggestions() {
        // Return popular or recent items as suggestions
        const recentSearches = JSON.parse(localStorage.getItem('recentSearches') || '[]');
        return recentSearches.slice(0, 5);
    }

    navigateToResult(type, id) {
        // Navigate to the appropriate section and highlight the result
        const sectionMap = {
            'file': 'files',
            'class': 'classes',
            'function': 'functions',
            'service': 'services'
        };
        
        const section = sectionMap[type];
        if (section && window.navigationManager) {
            window.navigationManager.showSection(section);
            
            // Highlight the specific item after a short delay
            setTimeout(() => {
                this.highlightItem(type, id);
            }, 500);
        }
        
        this.hideSearchResults();
        
        // Save to recent searches
        this.saveRecentSearch({ type, id, name: 'Search Result' });
    }

    highlightItem(type, id) {
        const selector = `.${type}-item[data-id="${id}"]`;
        const item = document.querySelector(selector);
        if (item) {
            item.scrollIntoView({ behavior: 'smooth', block: 'center' });
            item.classList.add('highlighted');
            setTimeout(() => item.classList.remove('highlighted'), 3000);
        }
    }

    saveRecentSearch(searchItem) {
        const recentSearches = JSON.parse(localStorage.getItem('recentSearches') || '[]');
        recentSearches.unshift(searchItem);
        recentSearches.splice(10); // Keep only last 10
        localStorage.setItem('recentSearches', JSON.stringify(recentSearches));
    }

    // === ENHANCED KEYBOARD SHORTCUTS ===

    handleKeyboard(event) {
        // Ctrl/Cmd + K for search focus (FIXED ID)
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const searchInput = document.getElementById('search-input'); // Fixed ID
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }

        // Escape to close modals and search results
        if (event.key === 'Escape') {
            this.hideSearchResults();
            const modals = document.querySelectorAll('.modal-overlay');
            modals.forEach(modal => modal.remove());
        }

        // Ctrl/Cmd + R for refresh
        if ((event.ctrlKey || event.metaKey) && event.key === 'r' && event.shiftKey) {
            event.preventDefault();
            this.refreshAllData();
        }

        // Arrow keys for search result navigation
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            this.navigateSearchResults(event.key === 'ArrowDown' ? 1 : -1);
        }

        // Enter to select search result
        if (event.key === 'Enter' && document.activeElement.id === 'search-input') {
            this.selectActiveSearchResult();
        }
    }

    navigateSearchResults(direction) {
        const results = document.querySelectorAll('.search-result-item');
        if (results.length === 0) return;

        const current = document.querySelector('.search-result-item.active');
        let index = current ? Array.from(results).indexOf(current) : -1;
        
        if (current) current.classList.remove('active');
        
        index += direction;
        if (index < 0) index = results.length - 1;
        if (index >= results.length) index = 0;
        
        results[index].classList.add('active');
        results[index].scrollIntoView({ block: 'nearest' });
    }

    selectActiveSearchResult() {
        const active = document.querySelector('.search-result-item.active');
        if (active) {
            active.click();
        }
    }

    // === ENHANCED NOTIFICATION SYSTEM ===

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icon = this.getNotificationIcon(type);
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${icon}</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add to notification container or create one
        let container = document.getElementById('notificationContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notificationContainer';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after delay
        const delay = type === 'error' ? 8000 : 4000;
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, delay);
        
        // Animate in
        setTimeout(() => notification.classList.add('show'), 100);
    }

    getNotificationIcon(type) {
        const icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        return icons[type] || 'ℹ️';
    }

    // === ENHANCED MODAL SYSTEM ===

    createModal(title, content, options = {}) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-dialog ${options.size || ''}">
                <div class="modal-header">
                    <h3 class="modal-title">${title}</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
            </div>
        `;
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        return modal;
    }

    closeModal() {
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.remove();
        }
    }

    applyDomainFilter(section) {
        const checkboxes = document.querySelectorAll('.domain-checkboxes input[type="checkbox"]');
        const selectedDomains = Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        
        const container = document.getElementById(`${section}List`);
        if (!container) return;
        
        const items = container.querySelectorAll(`.${section.slice(0, -1)}-item`);
        items.forEach(item => {
            const domain = item.getAttribute('data-domain') || '';
            const show = selectedDomains.length === 0 || selectedDomains.includes(domain);
            item.style.display = show ? 'block' : 'none';
        });
        
        this.closeModal();
        this.showNotification(`Domain filter applied (${selectedDomains.length} domains selected)`, 'success');
    }

    // Utility: Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Create global dashboard instance
window.dashboard = new CodeIntelligenceDashboard();
