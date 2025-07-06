/**
 * Core Dashboard Functionality
 * Handles basic data loading, navigation, and state management
 */

class CodeIntelligenceDashboard {
    constructor() {
        this.data = {
            files: [],
            classes: [],
            functions: [],
            stats: {}
        };
        this.currentSection = 'overview';
    }

    // Initialize dashboard
    async init() {
        console.log('🚀 Initializing Code Intelligence Dashboard...');
        
        try {
            await this.loadStats();
            await this.loadCharts();
            await this.loadLayerCounts();
            
            this.initializeEventListeners();
            console.log('✅ Dashboard initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize dashboard:', error);
            this.showError('Failed to initialize dashboard: ' + error.message);
        }
    }

    // Initialize event listeners
    initializeEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboard.bind(this));
    }

    // Load system statistics
    async loadStats() {
        try {
            console.log('📊 Loading system statistics...');
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

    // Handle search input
    async handleSearch(event) {
        const query = event.target.value.trim();
        
        if (query.length < 2) {
            return;
        }

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=20`);
            const result = await response.json();
            
            if (result.success) {
                this.displaySearchResults(result.data);
            }
        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    // Display search results
    displaySearchResults(results) {
        // TODO: Implement search results display
        console.log('Search results:', results);
    }

    // Handle keyboard shortcuts
    handleKeyboard(event) {
        // Ctrl/Cmd + K for search focus
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape to close modals
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll('.modal-overlay');
            modals.forEach(modal => modal.remove());
        }
    }

    // Show error message
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        document.body.insertBefore(errorDiv, document.body.firstChild);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
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
