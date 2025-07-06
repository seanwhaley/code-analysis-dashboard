/**
 * Search Manager Component
 * Handles search functionality across files, classes, and functions
 */

class SearchManager {
    constructor() {
        this.searchInput = null;
        this.searchResults = null;
        this.currentQuery = '';
        this.searchTimeout = null;
        this.isSearching = false;
        this.searchHistory = [];
        this.maxHistoryLength = 10;
    }

    // Initialize search functionality
    init() {
        this.searchInput = document.getElementById('search-input');
        this.setupSearchInput();
        this.setupKeyboardShortcuts();
        this.createSearchResultsContainer();
        console.log('🔍 Search manager initialized');
    }

    // Setup search input event listeners
    setupSearchInput() {
        if (!this.searchInput) {
            console.error('Search input not found');
            return;
        }

        // Input event with debouncing
        this.searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            this.debounceSearch(query);
        });

        // Focus and blur events
        this.searchInput.addEventListener('focus', () => {
            this.showSearchResults();
        });

        // Enter key to perform search
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch(this.searchInput.value.trim());
            } else if (e.key === 'Escape') {
                this.hideSearchResults();
                this.searchInput.blur();
            }
        });
    }

    // Setup keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+K or Cmd+K to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.focusSearch();
            }
        });
    }

    // Create search results container
    createSearchResultsContainer() {
        // Remove existing container if it exists
        const existing = document.getElementById('search-results-container');
        if (existing) {
            existing.remove();
        }

        // Create new container
        const container = document.createElement('div');
        container.id = 'search-results-container';
        container.className = 'search-results-container';
        container.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-height: 400px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        `;

        // Insert after search container
        const searchContainer = document.querySelector('.search-container');
        if (searchContainer) {
            searchContainer.style.position = 'relative';
            searchContainer.appendChild(container);
        }

        this.searchResults = container;
    }

    // Debounced search
    debounceSearch(query) {
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        this.searchTimeout = setTimeout(() => {
            if (query.length >= 2) {
                this.performSearch(query);
            } else if (query.length === 0) {
                this.hideSearchResults();
            }
        }, 300);
    }

    // Perform search
    async performSearch(query) {
        if (!query || query.length < 2) {
            this.hideSearchResults();
            return;
        }

        this.currentQuery = query;
        this.isSearching = true;
        this.showLoadingState();

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=20`);
            const result = await response.json();

            if (result.success) {
                this.displaySearchResults(result.data, query);
                this.addToHistory(query);
            } else {
                this.showError('Search failed');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search error occurred');
        } finally {
            this.isSearching = false;
        }
    }

    // Display search results
    displaySearchResults(results, query) {
        if (!this.searchResults) return;

        if (results.length === 0) {
            this.searchResults.innerHTML = `
                <div class="search-no-results">
                    <p>No results found for "${query}"</p>
                    <small>Try different keywords or check spelling</small>
                </div>
            `;
        } else {
            const groupedResults = this.groupResultsByType(results);
            this.searchResults.innerHTML = this.renderGroupedResults(groupedResults, query);
        }

        this.showSearchResults();
    }

    // Group results by type
    groupResultsByType(results) {
        const grouped = {
            files: [],
            classes: [],
            functions: []
        };

        results.forEach(result => {
            if (grouped[result.type + 's']) {
                grouped[result.type + 's'].push(result);
            }
        });

        return grouped;
    }

    // Render grouped results
    renderGroupedResults(grouped, query) {
        let html = `<div class="search-results-header">
            <strong>Search Results for "${query}"</strong>
        </div>`;

        // Render each group
        Object.entries(grouped).forEach(([type, items]) => {
            if (items.length > 0) {
                html += `
                    <div class="search-group">
                        <div class="search-group-header">
                            ${this.getTypeIcon(type)} ${this.capitalizeFirst(type)} (${items.length})
                        </div>
                        <div class="search-group-items">
                            ${items.map(item => this.renderSearchItem(item)).join('')}
                        </div>
                    </div>
                `;
            }
        });

        return html;
    }

    // Render individual search item
    renderSearchItem(item) {
        const typeClass = `search-item-${item.type}`;
        return `
            <div class="search-item ${typeClass}" onclick="searchManager.selectSearchResult('${item.type}', ${item.id})">
                <div class="search-item-name">
                    ${this.getTypeIcon(item.type)} ${item.name}
                </div>
                <div class="search-item-path">
                    ${item.file_path || 'Unknown path'}
                </div>
                ${item.domain ? `<div class="search-item-domain">${item.domain}</div>` : ''}
            </div>
        `;
    }

    // Select search result
    selectSearchResult(type, id) {
        this.hideSearchResults();
        
        // Navigate to appropriate section and show details
        switch(type) {
            case 'file':
                window.navigationManager.showSection('files');
                setTimeout(() => {
                    if (window.modalManager) {
                        window.modalManager.showFileDetails(id);
                    }
                }, 500);
                break;
            case 'class':
                window.navigationManager.showSection('classes');
                setTimeout(() => {
                    if (window.modalManager) {
                        window.modalManager.showClassDetails(id);
                    }
                }, 500);
                break;
            case 'function':
                window.navigationManager.showSection('functions');
                setTimeout(() => {
                    if (window.modalManager) {
                        window.modalManager.showFunctionDetails(id);
                    }
                }, 500);
                break;
        }
    }

    // Show loading state
    showLoadingState() {
        if (!this.searchResults) return;
        
        this.searchResults.innerHTML = `
            <div class="search-loading">
                <div class="usa-spinner"></div>
                <span>Searching...</span>
            </div>
        `;
        this.showSearchResults();
    }

    // Show error state
    showError(message) {
        if (!this.searchResults) return;
        
        this.searchResults.innerHTML = `
            <div class="search-error">
                <p>❌ ${message}</p>
            </div>
        `;
        this.showSearchResults();
    }

    // Show search results container
    showSearchResults() {
        if (this.searchResults) {
            this.searchResults.style.display = 'block';
        }
    }

    // Hide search results container
    hideSearchResults() {
        if (this.searchResults) {
            this.searchResults.style.display = 'none';
        }
    }

    // Focus search input
    focusSearch() {
        if (this.searchInput) {
            this.searchInput.focus();
            this.searchInput.select();
        }
    }

    // Add to search history
    addToHistory(query) {
        if (!this.searchHistory.includes(query)) {
            this.searchHistory.unshift(query);
            if (this.searchHistory.length > this.maxHistoryLength) {
                this.searchHistory.pop();
            }
        }
    }

    // Get type icon
    getTypeIcon(type) {
        const icons = {
            files: '📁',
            file: '📁',
            classes: '🏗️',
            class: '🏗️',
            functions: '⚙️',
            function: '⚙️'
        };
        return icons[type] || '📄';
    }

    // Capitalize first letter
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    // Get current query
    getCurrentQuery() {
        return this.currentQuery;
    }

    // Get search history
    getSearchHistory() {
        return [...this.searchHistory];
    }
}

// Initialize search manager
window.searchManager = new SearchManager();