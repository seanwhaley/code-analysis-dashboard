/**
 * Reality-Based UI Component
 * Shows users what actually works vs what's broken/incomplete
 * Implements progressive enhancement and graceful degradation
 */

class RealityBasedUI {
    constructor() {
        this.dataAvailability = {
            files: { available: true, quality: 'high', coverage: 100 },
            search: { available: true, quality: 'high', coverage: 100 },
            classes: { available: true, quality: 'good', coverage: 86.3 },
            functions: { available: true, quality: 'good', coverage: 70.2 },
            imports: { available: true, quality: 'medium', coverage: 60 },
            decorators: { available: false, quality: 'none', coverage: 0 },
            relationships: { available: false, quality: 'none', coverage: 0 },
            visualizations: { available: 'partial', quality: 'basic', coverage: 30 }
        };
        
        this.init();
    }
    
    init() {
        this.addDataQualityIndicators();
        this.implementProgressiveEnhancement();
        this.addHonestErrorMessages();
        this.createDataAvailabilityDashboard();
    }
    
    addDataQualityIndicators() {
        // Add quality indicators to each section
        const sections = document.querySelectorAll('[data-feature]');
        
        sections.forEach(section => {
            const feature = section.dataset.feature;
            const availability = this.dataAvailability[feature];
            
            if (availability) {
                const indicator = this.createQualityIndicator(availability);
                section.insertBefore(indicator, section.firstChild);
                
                // Disable or modify sections based on availability
                if (!availability.available || availability.available === false) {
                    this.disableSection(section, 'Feature not yet implemented');
                } else if (availability.available === 'partial') {
                    this.addPartialWarning(section, `Limited functionality - ${availability.coverage}% coverage`);
                } else if (availability.coverage < 80) {
                    this.addDataWarning(section, `Data coverage: ${availability.coverage}%`);
                }
            }
        });
    }
    
    createQualityIndicator(availability) {
        const indicator = document.createElement('div');
        indicator.className = 'data-quality-indicator';
        
        let statusClass, statusText, statusIcon;
        
        if (availability.available === true && availability.coverage >= 80) {
            statusClass = 'status-good';
            statusText = 'Fully Functional';
            statusIcon = '✅';
        } else if (availability.available === true && availability.coverage >= 50) {
            statusClass = 'status-partial';
            statusText = `Partial Data (${availability.coverage}%)`;
            statusIcon = '⚠️';
        } else if (availability.available === 'partial') {
            statusClass = 'status-limited';
            statusText = 'Limited Functionality';
            statusIcon = '🔶';
        } else {
            statusClass = 'status-unavailable';
            statusText = 'Not Available';
            statusIcon = '❌';
        }
        
        indicator.innerHTML = `
            <div class="quality-badge ${statusClass}">
                <span class="status-icon">${statusIcon}</span>
                <span class="status-text">${statusText}</span>
            </div>
        `;
        
        return indicator;
    }
    
    disableSection(section, reason) {
        section.classList.add('section-disabled');
        section.style.opacity = '0.5';
        section.style.pointerEvents = 'none';
        
        const overlay = document.createElement('div');
        overlay.className = 'disabled-overlay';
        overlay.innerHTML = `
            <div class="disabled-message">
                <i class="fas fa-construction"></i>
                <h4>Feature Under Development</h4>
                <p>${reason}</p>
            </div>
        `;
        
        section.style.position = 'relative';
        section.appendChild(overlay);
    }
    
    addPartialWarning(section, message) {
        const warning = document.createElement('div');
        warning.className = 'partial-warning usa-alert usa-alert--warning usa-alert--slim';
        warning.innerHTML = `
            <div class="usa-alert__body">
                <p class="usa-alert__text">
                    <strong>Limited Functionality:</strong> ${message}
                </p>
            </div>
        `;
        
        section.insertBefore(warning, section.children[1]);
    }
    
    addDataWarning(section, message) {
        const warning = document.createElement('div');
        warning.className = 'data-warning usa-alert usa-alert--info usa-alert--slim';
        warning.innerHTML = `
            <div class="usa-alert__body">
                <p class="usa-alert__text">
                    <i class="fas fa-info-circle"></i> ${message}
                </p>
            </div>
        `;
        
        section.insertBefore(warning, section.children[1]);
    }
    
    implementProgressiveEnhancement() {
        // Start with basic functionality and add features only when data is available
        
        // File listing - always works
        this.enableFileExplorer();
        
        // Search - works well
        this.enableAdvancedSearch();
        
        // Class/function views - work with caveats
        this.enableCodeStructureViews();
        
        // Disable broken visualizations
        this.disableBrokenVisualizations();
    }
    
    enableFileExplorer() {
        // File explorer is fully functional
        const fileSection = document.querySelector('[data-feature="files"]');
        if (fileSection) {
            fileSection.classList.add('feature-ready');
        }
    }
    
    enableAdvancedSearch() {
        // Search works well, enhance it
        const searchSection = document.querySelector('[data-feature="search"]');
        if (searchSection) {
            searchSection.classList.add('feature-ready');
            this.addSearchEnhancements();
        }
    }
    
    addSearchEnhancements() {
        // Add real-time search suggestions
        const searchInput = document.querySelector('#search-input');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.showSearchSuggestions(e.target.value);
            }, 300));
        }
    }
    
    enableCodeStructureViews() {
        // Enable class/function views with data quality warnings
        const structureSection = document.querySelector('[data-feature="classes"]');
        if (structureSection) {
            structureSection.classList.add('feature-ready');
        }
        
        const functionSection = document.querySelector('[data-feature="functions"]');
        if (functionSection) {
            functionSection.classList.add('feature-ready');
        }
    }
    
    disableBrokenVisualizations() {
        // Disable relationship diagrams that don't work
        const relationshipButtons = document.querySelectorAll('[data-visualization="relationships"]');
        relationshipButtons.forEach(button => {
            button.disabled = true;
            button.title = 'Relationship data not available - feature under development';
            button.classList.add('btn-disabled');
        });
        
        // Disable dependency flow that's broken
        const dependencyButtons = document.querySelectorAll('[data-visualization="dependencies"]');
        dependencyButtons.forEach(button => {
            button.disabled = true;
            button.title = 'Dependency analysis not available - feature under development';
            button.classList.add('btn-disabled');
        });
    }
    
    createDataAvailabilityDashboard() {
        // Create a small dashboard showing what's working
        const dashboard = document.createElement('div');
        dashboard.id = 'data-availability-dashboard';
        dashboard.className = 'availability-dashboard';
        
        dashboard.innerHTML = `
            <div class="dashboard-header">
                <h3><i class="fas fa-tachometer-alt"></i> System Status</h3>
                <button class="toggle-dashboard" onclick="this.parentElement.parentElement.classList.toggle('collapsed')">
                    <i class="fas fa-chevron-up"></i>
                </button>
            </div>
            <div class="dashboard-content">
                ${this.generateAvailabilityReport()}
            </div>
        `;
        
        // Add to page
        const mainContent = document.querySelector('main') || document.body;
        mainContent.insertBefore(dashboard, mainContent.firstChild);
    }
    
    generateAvailabilityReport() {
        let html = '<div class="availability-grid">';
        
        Object.entries(this.dataAvailability).forEach(([feature, data]) => {
            const statusClass = this.getStatusClass(data);
            const statusIcon = this.getStatusIcon(data);
            
            html += `
                <div class="availability-item ${statusClass}">
                    <div class="item-icon">${statusIcon}</div>
                    <div class="item-info">
                        <div class="item-name">${this.formatFeatureName(feature)}</div>
                        <div class="item-status">${this.getStatusText(data)}</div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    getStatusClass(data) {
        if (data.available === true && data.coverage >= 80) return 'status-good';
        if (data.available === true && data.coverage >= 50) return 'status-partial';
        if (data.available === 'partial') return 'status-limited';
        return 'status-unavailable';
    }
    
    getStatusIcon(data) {
        if (data.available === true && data.coverage >= 80) return '✅';
        if (data.available === true && data.coverage >= 50) return '⚠️';
        if (data.available === 'partial') return '🔶';
        return '❌';
    }
    
    getStatusText(data) {
        if (data.available === true && data.coverage >= 80) return 'Ready';
        if (data.available === true && data.coverage >= 50) return `${data.coverage}% Data`;
        if (data.available === 'partial') return 'Limited';
        return 'Unavailable';
    }
    
    formatFeatureName(feature) {
        return feature.charAt(0).toUpperCase() + feature.slice(1);
    }
    
    addHonestErrorMessages() {
        // Replace generic loading messages with honest status
        const loadingElements = document.querySelectorAll('.loading-placeholder');
        
        loadingElements.forEach(element => {
            const feature = element.dataset.feature;
            const availability = this.dataAvailability[feature];
            
            if (availability && !availability.available) {
                element.innerHTML = `
                    <div class="honest-message">
                        <i class="fas fa-info-circle"></i>
                        <h4>Feature Not Available</h4>
                        <p>This feature is currently under development. Check the system status above for updates.</p>
                    </div>
                `;
                element.classList.remove('loading-placeholder');
                element.classList.add('unavailable-feature');
            }
        });
    }
    
    showSearchSuggestions(query) {
        if (query.length < 2) return;
        
        // This would connect to the working search API
        fetch(`/api/search?q=${encodeURIComponent(query)}&limit=5`)
            .then(response => response.json())
            .then(data => {
                this.displaySearchSuggestions(data.files || []);
            })
            .catch(error => {
                console.log('Search suggestions unavailable:', error);
            });
    }
    
    displaySearchSuggestions(suggestions) {
        let suggestionsContainer = document.querySelector('#search-suggestions');
        
        if (!suggestionsContainer) {
            suggestionsContainer = document.createElement('div');
            suggestionsContainer.id = 'search-suggestions';
            suggestionsContainer.className = 'search-suggestions';
            
            const searchInput = document.querySelector('#search-input');
            if (searchInput) {
                searchInput.parentNode.appendChild(suggestionsContainer);
            }
        }
        
        if (suggestions.length === 0) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        suggestionsContainer.innerHTML = suggestions.map(file => `
            <div class="suggestion-item" onclick="window.dashboardCore.showFileDetails(${file.id})">
                <div class="suggestion-name">${file.name}</div>
                <div class="suggestion-path">${file.path}</div>
            </div>
        `).join('');
        
        suggestionsContainer.style.display = 'block';
    }
    
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.realityBasedUI = new RealityBasedUI();
});