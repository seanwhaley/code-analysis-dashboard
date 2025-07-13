/**
 * Visualization Manager for Code Intelligence Dashboard
 * 
 * This module provides comprehensive visualization management capabilities
 * including Mermaid diagrams, D3.js network graphs, and interactive charts
 * for code analysis and relationship visualization.
 * 
 * @author Code Intelligence Dashboard
 * @version 1.0.0
 */

class VisualizationManager {
    constructor() {
        this.activeVisualization = null;
        this.cache = new Map();
        this.defaultConfig = {
            mermaid: {
                theme: 'default',
                themeVariables: {
                    primaryColor: '#1976d2',
                    primaryTextColor: '#fff',
                    primaryBorderColor: '#0d47a1',
                    lineColor: '#757575'
                }
            },
            network: {
                width: 800,
                height: 600,
                nodeRadius: 12,
                linkDistance: 100
            }
        };
    }

    /**
     * Initialize visualization manager with configuration
     * @param {Object} config - Configuration options
     */
    async initialize(config = {}) {
        this.config = { ...this.defaultConfig, ...config };
        
        // Initialize Mermaid if available
        if (typeof mermaid !== 'undefined') {
            mermaid.initialize({
                startOnLoad: false,
                theme: this.config.mermaid.theme,
                themeVariables: this.config.mermaid.themeVariables
            });
        }

        console.log('Visualization Manager initialized');
    }

    /**
     * Show Pydantic model inheritance and composition graph
     * @param {Object} options - Visualization options
     */
    async showPydanticModelGraph(options = {}) {
        try {
            const cacheKey = 'pydantic-models';
            let pydanticModels;

            // Check cache first
            if (this.cache.has(cacheKey) && !options.forceRefresh) {
                pydanticModels = this.cache.get(cacheKey);
            } else {
                // Fetch data from API
                const response = await fetch('/api/classes?limit=5000');
                if (!response.ok) {
                    throw new Error(`API request failed: ${response.status}`);
                }
                
                const result = await response.json();
                pydanticModels = result.data.filter(cls => 
                    cls.class_type === 'pydantic_model' || 
                    cls.is_pydantic_model ||
                    (cls.base_classes && cls.base_classes.includes('BaseModel'))
                );
                
                // Cache the result
                this.cache.set(cacheKey, pydanticModels);
            }

            if (pydanticModels.length === 0) {
                this.showEmptyState('No Pydantic models found in the codebase');
                return;
            }

            // Generate Mermaid diagram
            const mermaidCode = this.generatePydanticModelMermaid(pydanticModels, options);
            
            // Render the diagram
            await this.renderMermaidDiagram(
                mermaidCode, 
                'Pydantic Model Inheritance & Composition',
                options.containerId || 'visualization-container'
            );

            console.log(`Generated Pydantic model graph with ${pydanticModels.length} models`);

        } catch (error) {
            console.error('Error generating Pydantic model graph:', error);
            this.showError(`Failed to generate Pydantic model graph: ${error.message}`);
        }
    }

    /**
     * Generate Mermaid diagram code for Pydantic models
     * @param {Array} models - Array of Pydantic model data
     * @param {Object} options - Generation options
     * @returns {string} Mermaid diagram code
     */
    generatePydanticModelMermaid(models, options = {}) {
        const showFields = options.showFields !== false;
        const showValidators = options.showValidators === true;
        const direction = options.direction || 'TD';

        let mermaidCode = `graph ${direction}\n`;
        
        // Add CSS styling
        mermaidCode += `
            classDef pydanticModel fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
            classDef baseModel fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
            classDef formModel fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
        \n`;

        // Create nodes for each model
        models.forEach(model => {
            const modelId = this.sanitizeId(model.name);
            let nodeContent = model.name;

            if (showFields && model.fields && model.fields.length > 0) {
                const fieldList = model.fields.slice(0, 5).map(f => `${f.name}: ${f.type || 'Any'}`);
                if (model.fields.length > 5) {
                    fieldList.push('...');
                }
                nodeContent += `|${fieldList.join('|')}`;
            }

            // Determine node style based on model type
            let nodeClass = 'pydanticModel';
            if (model.name.includes('Form')) {
                nodeClass = 'formModel';
            } else if (model.base_classes && model.base_classes.includes('BaseModel')) {
                nodeClass = 'baseModel';
            }

            mermaidCode += `    ${modelId}["${nodeContent}"]:::${nodeClass}\n`;
        });

        // Add inheritance relationships
        models.forEach(model => {
            const modelId = this.sanitizeId(model.name);
            
            if (model.base_classes && model.base_classes.length > 0) {
                model.base_classes.forEach(baseClass => {
                    const baseId = this.sanitizeId(baseClass);
                    // Only add if the base class is also in our model list
                    const baseExists = models.some(m => m.name === baseClass);
                    if (baseExists) {
                        mermaidCode += `    ${baseId} --> ${modelId}\n`;
                    } else {
                        // Add external base class
                        mermaidCode += `    ${baseId}["${baseClass}"]:::baseModel\n`;
                        mermaidCode += `    ${baseId} --> ${modelId}\n`;
                    }
                });
            }
        });

        // Add composition relationships if available
        // This would require additional relationship data from the API
        
        return mermaidCode;
    }

    /**
     * Render a Mermaid diagram
     * @param {string} code - Mermaid diagram code
     * @param {string} title - Diagram title
     * @param {string} containerId - Container element ID
     */
    async renderMermaidDiagram(code, title, containerId = 'visualization-container') {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container element #${containerId} not found`);
            return;
        }

        try {
            // Clear previous content
            container.innerHTML = `
                <div class="visualization-header">
                    <h3>${title}</h3>
                    <div class="visualization-controls">
                        <button class="btn btn-sm" onclick="window.visualizationManager.downloadSvg('${containerId}')">
                            📥 Download SVG
                        </button>
                        <button class="btn btn-sm" onclick="window.visualizationManager.zoomReset('${containerId}')">
                            🔍 Reset Zoom
                        </button>
                    </div>
                </div>
                <div id="${containerId}-content" class="mermaid-container">
                    ${code}
                </div>
            `;

            // Render with Mermaid
            if (typeof mermaid !== 'undefined') {
                await mermaid.init(undefined, `#${containerId}-content`);
                this.activeVisualization = { type: 'mermaid', containerId, title };
            } else {
                container.innerHTML = `
                    <div class="error-state">
                        <h4>Mermaid Not Available</h4>
                        <p>Mermaid library is required for diagram rendering.</p>
                        <pre>${code}</pre>
                    </div>
                `;
            }

        } catch (error) {
            console.error('Error rendering Mermaid diagram:', error);
            this.showError(`Failed to render diagram: ${error.message}`);
        }
    }

    /**
     * Show network visualization using D3.js
     * @param {Array} relationships - Relationship data
     * @param {string} containerId - Container element ID
     * @param {Object} options - Visualization options
     */
    async showNetworkGraph(relationships, containerId = 'visualization-container', options = {}) {
        if (typeof window.d3Visualizer === 'undefined') {
            this.showError('D3 Visualizer not available');
            return;
        }

        try {
            const config = { ...this.config.network, ...options };
            await window.d3Visualizer.createRelationshipGraph(relationships, containerId, config);
            this.activeVisualization = { type: 'network', containerId, relationships };
        } catch (error) {
            console.error('Error creating network graph:', error);
            this.showError(`Failed to create network graph: ${error.message}`);
        }
    }

    /**
     * Sanitize string for use as Mermaid node ID
     * @param {string} str - String to sanitize
     * @returns {string} Sanitized string
     */
    sanitizeId(str) {
        return str.replace(/[^a-zA-Z0-9_]/g, '_');
    }

    /**
     * Show error state
     * @param {string} message - Error message
     */
    showError(message) {
        const container = document.getElementById('visualization-container');
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <h4>❌ Visualization Error</h4>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    /**
     * Show empty state
     * @param {string} message - Empty state message
     */
    showEmptyState(message) {
        const container = document.getElementById('visualization-container');
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <h4>📊 No Data</h4>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    /**
     * Download current visualization as SVG
     * @param {string} containerId - Container element ID
     */
    downloadSvg(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const svg = container.querySelector('svg');
        if (!svg) return;

        const serializer = new XMLSerializer();
        const svgString = serializer.serializeToString(svg);
        const blob = new Blob([svgString], { type: 'image/svg+xml' });
        
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${this.activeVisualization?.title || 'diagram'}.svg`;
        link.click();
        
        URL.revokeObjectURL(url);
    }

    /**
     * Reset zoom for current visualization
     * @param {string} containerId - Container element ID
     */
    zoomReset(containerId) {
        // Implementation would depend on the visualization type
        console.log(`Reset zoom for ${containerId}`);
    }

    /**
     * Clear cache
     */
    clearCache() {
        this.cache.clear();
        console.log('Visualization cache cleared');
    }
}

// Initialize global instance
window.visualizationManager = new VisualizationManager();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.visualizationManager.initialize();
});