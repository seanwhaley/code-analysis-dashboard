/**
 * Navigation Components
 * Handles section navigation and state management
 */

class NavigationManager {
    constructor() {
        this.currentSection = 'overview';
        this.sectionHistory = ['overview'];
        this.maxHistoryLength = 10;
    }

    // Show specific section
    showSection(sectionName) {
        // Validate section name
        const validSections = ['overview', 'files', 'classes', 'functions', 'services', 'relationships', 'dependencies', 'layers', 'complexity', 'domains'];
        if (!validSections.includes(sectionName)) {
            console.error(`Invalid section: ${sectionName}`);
            return;
        }

        // Update history
        if (this.currentSection !== sectionName) {
            this.sectionHistory.push(sectionName);
            if (this.sectionHistory.length > this.maxHistoryLength) {
                this.sectionHistory.shift();
            }
        }

        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Remove active from all nav items (USWDS classes)
        document.querySelectorAll('.usa-sidenav__link').forEach(item => {
            item.classList.remove('usa-current');
        });
        
        // Show selected section
        const targetSection = document.getElementById(sectionName);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // Activate nav item (USWDS classes)
        document.querySelectorAll('.usa-sidenav__link').forEach(item => {
            if (item.getAttribute('onclick') && item.getAttribute('onclick').includes(sectionName)) {
                item.classList.add('usa-current');
            }
        });
        
        // Update current section
        this.currentSection = sectionName;
        
        // Load section data if needed
        this.loadSectionIfNeeded(sectionName);
        
        // Update browser history (optional)
        if (history.pushState) {
            history.pushState({section: sectionName}, '', `#${sectionName}`);
        }
    }

    // Enhanced section data loading with dashboard integration
    async loadSectionIfNeeded(sectionName) {
        const sectionsRequiringData = ['files', 'classes', 'functions', 'services'];
        
        if (sectionsRequiringData.includes(sectionName)) {
            // Use dashboard methods if available for better UX
            if (window.dashboard && window.dashboard.isInitialized) {
                try {
                    switch(sectionName) {
                        case 'files':
                            await window.dashboard.loadFiles();
                            break;
                        case 'classes':
                            await window.dashboard.loadClasses();
                            break;
                        case 'functions':
                            await window.dashboard.loadFunctions();
                            break;
                        case 'services':
                            await window.dashboard.loadServices();
                            break;
                    }
                } catch (error) {
                    console.warn(`Failed to load ${sectionName} via dashboard:`, error);
                    // Fallback to dataLoader
                    if (window.dataLoader) {
                        window.dataLoader.loadSectionData(sectionName);
                    }
                }
            } else if (window.dataLoader) {
                window.dataLoader.loadSectionData(sectionName);
            }
        }
        
        // Load analyzer data for specific sections
        if (sectionName === 'complexity' && window.complexityAnalyzer) {
            try {
                await window.complexityAnalyzer.showComplexityOverview();
            } catch (error) {
                console.warn('Failed to load complexity analysis:', error);
            }
        }
        
        if (sectionName === 'domains' && window.domainAnalyzer) {
            try {
                await window.domainAnalyzer.showDomainOverview();
            } catch (error) {
                console.warn('Failed to load domain analysis:', error);
            }
        }
    }

    // Go back to previous section
    goBack() {
        if (this.sectionHistory.length > 1) {
            this.sectionHistory.pop(); // Remove current
            const previousSection = this.sectionHistory.pop(); // Get previous
            this.showSection(previousSection);
        }
    }

    // Get current section
    getCurrentSection() {
        return this.currentSection;
    }

    // Get section history
    getHistory() {
        return [...this.sectionHistory];
    }

    // Initialize navigation from URL hash
    initializeFromURL() {
        const hash = window.location.hash.substring(1);
        if (hash && this.isValidSection(hash)) {
            this.showSection(hash);
        } else {
            this.showSection('overview');
        }
    }

    // Check if section name is valid
    isValidSection(sectionName) {
        const validSections = ['overview', 'files', 'classes', 'functions', 'services', 'relationships', 'dependencies', 'layers', 'complexity', 'domains'];
        return validSections.includes(sectionName);
    }

    // Setup browser navigation handlers
    setupBrowserNavigation() {
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (event) => {
            if (event.state && event.state.section) {
                this.showSection(event.state.section);
            }
        });

        // Initialize from URL on load
        this.initializeFromURL();
    }

    // Add keyboard navigation
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (event) => {
            // Alt + Left Arrow: Go back
            if (event.altKey && event.key === 'ArrowLeft') {
                event.preventDefault();
                this.goBack();
            }

            // Number keys for quick section access
            if (event.ctrlKey || event.metaKey) {
                const sectionMap = {
                    '1': 'overview',
                    '2': 'files',
                    '3': 'classes',
                    '4': 'functions',
                    '5': 'relationships',
                    '6': 'dependencies',
                    '7': 'layers'
                };

                const section = sectionMap[event.key];
                if (section) {
                    event.preventDefault();
                    this.showSection(section);
                }
            }
        });
    }

    // Get section breadcrumbs
    getBreadcrumbs() {
        const sectionTitles = {
            'overview': '🏠 Overview',
            'files': '📁 Files',
            'classes': '🏗️ Classes',
            'functions': '⚙️ Functions',
            'relationships': '🌐 Relationships',
            'dependencies': '📦 Dependencies',
            'layers': '🏛️ Layers',
            'complexity': '🎯 Complexity',
            'domains': '🏷️ Domains'
        };

        return this.sectionHistory.map(section => ({
            name: section,
            title: sectionTitles[section] || section,
            isCurrent: section === this.currentSection
        }));
    }

    // Initialize navigation manager
    initialize() {
        this.setupBrowserNavigation();
        this.setupKeyboardNavigation();
        
        // Add navigation helper to header if it doesn't exist
        this.addNavigationHelper();
    }

    // Add navigation helper to the UI
    addNavigationHelper() {
        const header = document.querySelector('.header');
        if (header && !document.getElementById('navHelper')) {
            const navHelper = document.createElement('div');
            navHelper.id = 'navHelper';
            navHelper.style.cssText = `
                margin-top: 10px;
                font-size: 0.8rem;
                opacity: 0.7;
                text-align: center;
            `;
            navHelper.innerHTML = `
                <div>Shortcuts: Ctrl+1-7 for sections, Ctrl+K for search, Alt+← for back</div>
            `;
            header.appendChild(navHelper);
        }
    }

    // Update navigation state display
    updateNavigationState() {
        // Update any breadcrumb display
        const breadcrumbContainer = document.getElementById('breadcrumbs');
        if (breadcrumbContainer) {
            const breadcrumbs = this.getBreadcrumbs();
            breadcrumbContainer.innerHTML = breadcrumbs.map((crumb, index) => {
                const isLast = index === breadcrumbs.length - 1;
                return `
                    <span class="breadcrumb-item ${crumb.isCurrent ? 'current' : ''}" 
                          ${!isLast ? `onclick="navigationManager.showSection('${crumb.name}')"` : ''}>
                        ${crumb.title}
                    </span>
                    ${!isLast ? '<span class="breadcrumb-separator">›</span>' : ''}
                `;
            }).join('');
        }
    }
}

// Create global navigation manager instance
window.navigationManager = new NavigationManager();

// Global function for showing sections (backwards compatibility)
window.showSection = (sectionName) => window.navigationManager.showSection(sectionName);
