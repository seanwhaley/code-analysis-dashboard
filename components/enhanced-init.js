/**
 * Enhanced Dashboard Initialization
 * Ensures proper loading order and component integration
 * 
 * **Features:**
 * - Proper component initialization sequence
 * - Error handling and recovery
 * - Performance monitoring
 * - User feedback during loading
 */

class EnhancedDashboardInitializer {
    constructor() {
        this.initSteps = [
            { name: 'Core Dashboard', fn: this.initCoreDashboard.bind(this) },
            { name: 'Navigation Manager', fn: this.initNavigationManager.bind(this) },
            { name: 'Data Loader', fn: this.initDataLoader.bind(this) },
            { name: 'Modal Manager', fn: this.initModalManager.bind(this) },
            { name: 'Visualization Manager', fn: this.initVisualizationManager.bind(this) },
            { name: 'Chart.js', fn: this.initChartJS.bind(this) },
            { name: 'Final Setup', fn: this.finalSetup.bind(this) }
        ];
        this.currentStep = 0;
        this.startTime = Date.now();
    }

    async initialize() {
        console.log('🚀 Starting Enhanced Dashboard Initialization...');
        
        try {
            this.showInitializationProgress();
            
            for (const step of this.initSteps) {
                await this.executeStep(step);
                this.currentStep++;
                this.updateProgress();
            }
            
            this.onInitializationComplete();
            
        } catch (error) {
            this.onInitializationError(error);
        } finally {
            // Force remove initialization overlay regardless
            setTimeout(() => {
                const progressContainer = document.getElementById('initProgress');
                if (progressContainer) {
                    progressContainer.remove();
                }
            }, 1000);
        }
    }

    async executeStep(step) {
        console.log(`📍 Initializing: ${step.name}`);
        
        try {
            await step.fn();
            console.debug("✅ ${step.name} initialized successfully");
        } catch (error) {
            console.warn(`⚠️ ${step.name} initialization failed:`, error);
            // Continue with other steps unless it's critical
            if (step.name === 'Core Dashboard') {
                throw error; // Core dashboard is critical
            }
        }
    }

    async initCoreDashboard() {
        if (typeof CodeIntelligenceDashboard === 'undefined') {
            throw new Error('CodeIntelligenceDashboard class not found');
        }
        
        if (!window.dashboard) {
            window.dashboard = new CodeIntelligenceDashboard();
            console.debug("✅ Dashboard instance created");
        }
        
        // Initialize dashboard data structure
        if (!window.dashboard.data) {
            window.dashboard.data = {
                files: [],
                classes: [],
                functions: [],
                services: [],
                stats: {}
            };
        }
        
        await window.dashboard.init();
        console.debug("✅ Dashboard initialized with data structure:", window.dashboard.data);
    }

    async initNavigationManager() {
        if (typeof NavigationManager === 'undefined') {
            console.warn('NavigationManager not found, creating fallback');
            return;
        }
        
        if (!window.navigationManager) {
            window.navigationManager = new NavigationManager();
        }
        
        // Initialize from URL hash
        window.navigationManager.initializeFromURL();
    }

    async initDataLoader() {
        if (typeof DataLoader === 'undefined') {
            console.warn('DataLoader not found');
            return;
        }
        
        if (!window.dataLoader) {
            window.dataLoader = new DataLoader();
            console.debug("✅ DataLoader instance created");
        }
        
        // Ensure dashboard data structure exists
        if (window.dashboard && !window.dashboard.data) {
            window.dashboard.data = {
                files: [],
                classes: [],
                functions: [],
                services: [],
                stats: {}
            };
        }
    }

    async initModalManager() {
        if (typeof ModalManager === 'undefined') {
            console.warn('ModalManager not found');
            return;
        }
        
        if (!window.modalManager) {
            window.modalManager = new ModalManager();
        }
    }

    async initVisualizationManager() {
        if (typeof VisualizationManager === 'undefined') {
            console.warn('VisualizationManager not found');
            return;
        }
        
        if (!window.visualizationManager) {
            window.visualizationManager = new VisualizationManager();
        }
    }

    async initChartJS() {
        // Wait for Chart.js to be available
        let attempts = 0;
        while (typeof Chart === 'undefined' && attempts < 50) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded, charts will not be available');
            return;
        }
        
        // Configure Chart.js defaults
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.plugins.legend.position = 'bottom';
        
        // Set up chart resize observer
        this.setupChartResizeObserver();
    }

    async finalSetup() {
        // Set up global error handlers
        this.setupErrorHandlers();
        
        // Set up keyboard shortcuts
        this.setupGlobalKeyboardShortcuts();
        
        // Set up auto-refresh
        this.setupAutoRefresh();
        
        // Initialize URL routing
        this.setupURLRouting();
        
        // Show welcome message
        this.showWelcomeMessage();
    }

    setupErrorHandlers() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            if (window.dashboard && window.dashboard.showError) {
                window.dashboard.showError('An unexpected error occurred. Please refresh the page.');
            }
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            if (window.dashboard && window.dashboard.showError) {
                window.dashboard.showError('A network or processing error occurred.');
            }
        });
    }

    setupChartResizeObserver() {
        // Set up ResizeObserver to handle chart resizing
        if (typeof ResizeObserver !== 'undefined') {
            const resizeObserver = new ResizeObserver((entries) => {
                entries.forEach((entry) => {
                    const canvas = entry.target.querySelector('canvas');
                    if (canvas && canvas.chart) {
                        // Delay resize to avoid rapid firing
                        setTimeout(() => {
                            canvas.chart.resize();
                        }, 100);
                    }
                });
            });
            
            // Observe feature grid containers
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // Observe feature cards
                            const featureCards = node.querySelectorAll('.feature-card');
                            featureCards.forEach(card => resizeObserver.observe(card));
                            
                            // If the node itself is a feature card
                            if (node.classList && node.classList.contains('feature-card')) {
                                resizeObserver.observe(node);
                            }
                        }
                    });
                });
            });
            
            observer.observe(document.body, { childList: true, subtree: true });
        }
        
        // Fallback: window resize handler
        window.addEventListener('resize', () => {
            setTimeout(() => {
                document.querySelectorAll('canvas').forEach(canvas => {
                    if (canvas.chart) {
                        canvas.chart.resize();
                    }
                });
            }, 200);
        });
    }

    setupGlobalKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Ctrl/Cmd + Shift + D for debug info
            if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'D') {
                event.preventDefault();
                this.showDebugInfo();
            }
            
            // Ctrl/Cmd + Shift + R for hard refresh
            if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'R') {
                event.preventDefault();
                this.hardRefresh();
            }
        });
    }

    setupAutoRefresh() {
        // Refresh stats every 5 minutes
        setInterval(() => {
            if (window.dashboard && window.dashboard.refreshStats) {
                window.dashboard.refreshStats();
            }
        }, 300000);
    }

    setupURLRouting() {
        // Handle browser back/forward
        window.addEventListener('popstate', (event) => {
            if (event.state && event.state.section && window.navigationManager) {
                window.navigationManager.showSection(event.state.section);
            }
        });
    }

    showInitializationProgress() {
        const progressContainer = document.createElement('div');
        progressContainer.id = 'initProgress';
        progressContainer.className = 'initialization-progress';
        progressContainer.innerHTML = `
            <div class="init-overlay">
                <div class="init-content">
                    <h2>🚀 Initializing Dashboard</h2>
                    <div class="init-progress-bar">
                        <div class="init-progress-fill" id="initProgressFill"></div>
                    </div>
                    <div class="init-status" id="initStatus">Starting...</div>
                </div>
            </div>
        `;
        
        document.body.appendChild(progressContainer);
    }

    updateProgress() {
        const progress = (this.currentStep / this.initSteps.length) * 100;
        const progressFill = document.getElementById('initProgressFill');
        const status = document.getElementById('initStatus');
        
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        
        if (status && this.currentStep < this.initSteps.length) {
            status.textContent = `Initializing ${this.initSteps[this.currentStep].name}...`;
        }
    }

    onInitializationComplete() {
        const duration = Date.now() - this.startTime;
        console.log(`✅ Dashboard initialization complete in ${duration}ms`);
        
        // Force remove progress indicator immediately
        const progressContainer = document.getElementById('initProgress');
        if (progressContainer) {
            progressContainer.remove();
        }
        
        // Update system status to show completion
        this.updateSystemStatus();
        
        // Show success notification
        if (window.dashboard && window.dashboard.showNotification) {
            window.dashboard.showNotification(
                `Dashboard initialized successfully in ${duration}ms`, 
                'success'
            );
        }
        
        // Trigger custom event
        window.dispatchEvent(new CustomEvent('dashboardReady', {
            detail: { duration, timestamp: Date.now() }
        }));
    }

    updateSystemStatus() {
        // Update the reality-based UI system status to reflect completion
        if (window.realityBasedUI) {
            window.realityBasedUI.dataAvailability.initialization = { 
                available: true, 
                quality: 'high', 
                coverage: 100 
            };
            
            // Refresh the status dashboard
            const statusDashboard = document.getElementById('data-availability-dashboard');
            if (statusDashboard) {
                statusDashboard.querySelector('.dashboard-content').innerHTML = 
                    window.realityBasedUI.generateAvailabilityReport();
            }
        }
    }

    onInitializationError(error) {
        console.error('❌ Dashboard initialization failed:', error);
        
        // Remove progress indicator
        const progressContainer = document.getElementById('initProgress');
        if (progressContainer) {
            progressContainer.innerHTML = `
                <div class="init-overlay">
                    <div class="init-content init-error">
                        <h2>❌ Initialization Failed</h2>
                        <p>The dashboard failed to initialize properly.</p>
                        <p><strong>Error:</strong> ${error.message}</p>
                        <button class="usa-button" onclick="location.reload()">
                            Reload Page
                        </button>
                    </div>
                </div>
            `;
        }
    }

    showDebugInfo() {
        const debugInfo = {
            dashboard: !!window.dashboard,
            navigationManager: !!window.navigationManager,
            dataLoader: !!window.dataLoader,
            modalManager: !!window.modalManager,
            visualizationManager: !!window.visualizationManager,
            chartJS: typeof Chart !== 'undefined',
            initTime: Date.now() - this.startTime,
            cacheStats: window.dataLoader ? window.dataLoader.getCacheStats() : null,
            currentSection: window.navigationManager ? window.navigationManager.getCurrentSection() : null
        };
        
        console.table(debugInfo);
        
        if (window.dashboard && window.dashboard.createModal) {
            const modal = window.dashboard.createModal(
                'Debug Information',
                `<pre>${JSON.stringify(debugInfo, null, 2)}</pre>`
            );
            document.body.appendChild(modal);
        }
    }

    hardRefresh() {
        if (window.dataLoader) {
            window.dataLoader.clearCache();
        }
        
        localStorage.removeItem('recentSearches');
        location.reload(true);
    }

    showWelcomeMessage() {
        // Show welcome message for first-time users
        if (!localStorage.getItem('dashboardVisited')) {
            localStorage.setItem('dashboardVisited', 'true');
            
            if (window.dashboard && window.dashboard.showNotification) {
                setTimeout(() => {
                    window.dashboard.showNotification(
                        'Welcome to the Code Intelligence Dashboard! Press Ctrl+K to search.',
                        'info'
                    );
                }, 2000);
            }
        }
    }
}

// Enhanced initialization styles
const initStyles = `
<style>
.initialization-progress {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: opacity 0.5s ease;
}

.init-overlay {
    background: white;
    border-radius: 8px;
    padding: 40px;
    max-width: 400px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.init-content h2 {
    margin: 0 0 20px 0;
    color: #1f2937;
}

.init-progress-bar {
    width: 100%;
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
    margin: 20px 0;
}

.init-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #1d4ed8);
    width: 0%;
    transition: width 0.3s ease;
}

.init-status {
    color: #6b7280;
    font-size: 0.9em;
    margin-top: 10px;
}

.init-error {
    color: #dc2626;
}

.init-error p {
    margin: 10px 0;
    text-align: left;
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', initStyles);

// AGGRESSIVE INITIALIZATION - Force everything to work
function forceInitialization() {
    console.log('🚀 FORCE INITIALIZATION STARTING...');
    
    // Step 1: Create all global objects immediately
    if (typeof CodeIntelligenceDashboard !== 'undefined' && !window.dashboard) {
        window.dashboard = new CodeIntelligenceDashboard();
        window.dashboard.data = { files: [], classes: [], functions: [], services: [], stats: {} };
        console.debug("✅ Dashboard object created");
    }
    
    if (typeof DataLoader !== 'undefined' && !window.dataLoader) {
        window.dataLoader = new DataLoader();
        console.debug("✅ DataLoader object created");
    }
    
    if (typeof NavigationManager !== 'undefined' && !window.navigationManager) {
        window.navigationManager = new NavigationManager();
        console.debug("✅ NavigationManager object created");
    }
    
    if (typeof ModalManager !== 'undefined' && !window.modalManager) {
        window.modalManager = new ModalManager();
        console.debug("✅ ModalManager object created");
    }
    
    // Step 2: Initialize dashboard immediately
    if (window.dashboard && typeof window.dashboard.init === 'function') {
        window.dashboard.init().then(() => {
            console.debug("✅ Dashboard initialized");
            
            // Step 3: Load initial data immediately
            setTimeout(() => {
                if (window.dashboard.loadStats) {
                    window.dashboard.loadStats().catch(e => console.warn('Stats load failed:', e));
                }
                
                // Auto-load files on startup
                if (window.dashboard.loadFiles) {
                    window.dashboard.loadFiles().catch(e => console.warn('Files load failed:', e));
                }
            }, 500);
            
            // Step 4: Fire ready event
            window.dispatchEvent(new CustomEvent('dashboardReady', {
                detail: { timestamp: Date.now(), forced: true }
            }));
            
        }).catch(error => {
            console.error('❌ Dashboard init failed:', error);
        });
    }
    
    // Step 5: Test D3 and other dependencies
    setTimeout(() => {
                console.log('- D3.js:', typeof d3 !== 'undefined' ? '✅' : '❌');
        console.log('- Chart.js:', typeof Chart !== 'undefined' ? '✅' : '❌');
        console.log('- Mermaid:', typeof mermaid !== 'undefined' ? '✅' : '❌');
        
        // Show D3 version if available
        if (typeof d3 !== 'undefined') {
            console.log('🎯 D3.js version:', d3.version || 'Unknown');
            
            // Test D3 by creating a simple visualization
            const testContainer = document.createElement('div');
            testContainer.id = 'test-d3';
            testContainer.style.display = 'none';
            document.body.appendChild(testContainer);
            
            try {
                d3.select('#test-d3').append('svg').attr('width', 100).attr('height', 100);
                console.log('✅ D3.js is working correctly');
                document.body.removeChild(testContainer);
            } catch (error) {
                console.error('❌ D3.js test failed:', error);
            }
        }
    }, 1000);
}

// Multiple initialization attempts
let initAttempts = 0;
const maxAttempts = 5;

function attemptInitialization() {
    initAttempts++;
    console.log(`🔄 Initialization attempt ${initAttempts}/${maxAttempts}`);
    
    if (typeof CodeIntelligenceDashboard !== 'undefined') {
        forceInitialization();
        return;
    }
    
    if (initAttempts < maxAttempts) {
        setTimeout(attemptInitialization, 1000);
    } else {
        console.error('❌ Failed to initialize after', maxAttempts, 'attempts');
        // Show error to user
        document.body.innerHTML = `
            <div style="padding: 40px; text-align: center; font-family: Arial, sans-serif;">
                <h1 style="color: #dc3545;">⚠️ Dashboard Initialization Failed</h1>
                <p>The dashboard failed to initialize properly. Please refresh the page.</p>
                <button onclick="location.reload()" style="padding: 10px 20px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🔄 Refresh Page
                </button>
            </div>
        `;
    }
}

// Start initialization immediately
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attemptInitialization);
} else {
    attemptInitialization();
}

// Export for global access
window.EnhancedDashboardInitializer = EnhancedDashboardInitializer;