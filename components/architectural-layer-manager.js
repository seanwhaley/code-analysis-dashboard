/**
 * Architectural Layer Components
 * Handles TOGAF-style architectural layer analysis and navigation
 */

class ArchitecturalLayerManager {
    constructor() {
        this.layerDefinitions = {
            presentation: {
                icon: '🖥️',
                title: 'Presentation Layer',
                description: 'CLIs, Formatters, User Interfaces',
                patterns: ['presentation', 'cli', 'ui', 'interface', 'view', 'formatter'],
                color: {
                    bg: 'linear-gradient(135deg, #e1f5fe, #b3e5fc)',
                    title: '#01579b',
                    desc: '#0277bd',
                    count: '#0288d1'
                }
            },
            application: {
                icon: '⚙️',
                title: 'Application Layer',
                description: 'Services, Business Logic, Workflows',
                patterns: ['service', 'application', 'workflow', 'handler', 'controller'],
                color: {
                    bg: 'linear-gradient(135deg, #e8f5e8, #c8e6c9)',
                    title: '#1b5e20',
                    desc: '#2e7d32',
                    count: '#388e3c'
                }
            },
            domain: {
                icon: '🎯',
                title: 'Domain Layer',
                description: 'Models, Entities, Domain Logic',
                patterns: ['domain', 'model', 'entity', 'business', 'core'],
                color: {
                    bg: 'linear-gradient(135deg, #fff3e0, #ffe0b2)',
                    title: '#e65100',
                    desc: '#f57c00',
                    count: '#fb8c00'
                }
            },
            infrastructure: {
                icon: '🔧',
                title: 'Infrastructure Layer',
                description: 'Database, External Services, Config',
                patterns: ['infrastructure', 'database', 'config', 'external', 'adapter'],
                color: {
                    bg: 'linear-gradient(135deg, #f3e5f5, #e1bee7)',
                    title: '#4a148c',
                    desc: '#7b1fa2',
                    count: '#8e24aa'
                }
            },
            data: {
                icon: '📊',
                title: 'Data Layer',
                description: 'Repositories, Data Access, Storage',
                patterns: ['data', 'repository', 'dao', 'storage', 'persistence'],
                color: {
                    bg: 'linear-gradient(135deg, #fce4ec, #f8bbd9)',
                    title: '#880e4f',
                    desc: '#c2185b',
                    count: '#e91e63'
                }
            },
            shared: {
                icon: '🔗',
                title: 'Shared/Utils Layer',
                description: 'Common Utilities, Helpers, Constants',
                patterns: ['util', 'helper', 'common', 'shared', 'constant', 'base'],
                color: {
                    bg: 'linear-gradient(135deg, #f5f5f5, #e0e0e0)',
                    title: '#424242',
                    desc: '#616161',
                    count: '#757575'
                }
            }
        };
    }

    // Show architectural layer analysis
    async showArchitecturalLayer(layerType) {
        try {
            const response = await fetch('/api/files?limit=5000');
            const result = await response.json();
            
            if (!result.success) {
                window.dashboard.showError('Failed to load files for layer analysis');
                return;
            }
            
            const files = result.data;
            const layerFiles = this.filterFilesByLayer(files, layerType);
            
            const html = this.createLayerAnalysisHTML(layerType, layerFiles);
            
            document.getElementById('layerDetails').innerHTML = html;
            
            // Update layer counts
            this.updateLayerCounts(files);
            
        } catch (error) {
            console.error('Error analyzing architectural layer:', error);
            window.dashboard.showError('Failed to analyze architectural layer');
        }
    }

    // Filter files by architectural layer
    filterFilesByLayer(files, layerType) {
        const layerDef = this.layerDefinitions[layerType];
        if (!layerDef) return [];
        
        const patterns = layerDef.patterns;
        
        return files.filter(file => {
            const pathLower = file.path.toLowerCase();
            const domainLower = (file.domain || '').toLowerCase();
            
            return patterns.some(pattern => 
                pathLower.includes(pattern) || domainLower.includes(pattern)
            );
        });
    }

    // Create layer analysis HTML
    createLayerAnalysisHTML(layerType, layerFiles) {
        const layerDef = this.layerDefinitions[layerType];
        
        return `
            <h3 style="margin-bottom: 15px; color: white;">${layerDef.icon} ${layerDef.title}</h3>
            <div style="margin-bottom: 20px;">
                ${this.createLayerStatsHTML(layerFiles)}
            </div>
            
            <div style="margin-bottom: 15px;">
                <h4 style="color: white; margin-bottom: 10px;">📁 Components in this Layer</h4>
                ${this.createLayerComponentsHTML(layerFiles)}
            </div>
        `;
    }

    // Create layer statistics HTML
    createLayerStatsHTML(layerFiles) {
        const totalClasses = layerFiles.reduce((sum, f) => sum + (f.classes || 0), 0);
        const totalFunctions = layerFiles.reduce((sum, f) => sum + (f.functions || 0), 0);
        const avgComplexity = layerFiles.length > 0 
            ? (layerFiles.reduce((sum, f) => sum + (f.complexity || 0), 0) / layerFiles.length).toFixed(1)
            : '0';
        
        return `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 1.5em; color: white; font-weight: 600;">${layerFiles.length}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.9em;">Files</div>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 1.5em; color: white; font-weight: 600;">${totalClasses}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.9em;">Classes</div>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 1.5em; color: white; font-weight: 600;">${totalFunctions}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.9em;">Functions</div>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 1.5em; color: white; font-weight: 600;">${avgComplexity}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.9em;">Avg Complexity</div>
                </div>
            </div>
        `;
    }

    // Create layer components HTML
    createLayerComponentsHTML(layerFiles) {
        if (layerFiles.length === 0) {
            return '<div class="placeholder-text">No files found in this layer</div>';
        }
        
        return `
            <div style="display: grid; gap: 10px; max-height: 400px; overflow-y: auto;">
                ${layerFiles.map(file => {
                    const complexityClass = file.complexity > 50 ? 'high' : file.complexity > 25 ? 'medium' : 'low';
                    const complexityColor = complexityClass === 'high' ? '#dc3545' : complexityClass === 'medium' ? '#ffc107' : '#28a745';
                    
                    return `
                        <div onclick="modalManager.showFileDetails(${file.id})" style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; cursor: pointer; border-left: 3px solid ${complexityColor}; transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.1)'" onmouseout="this.style.background='rgba(255,255,255,0.05)'">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="flex: 1;">
                                    <div style="color: white; font-weight: 600; margin-bottom: 4px;">${file.name}</div>
                                    <div style="color: rgba(255,255,255,0.7); font-size: 0.8em;">${file.path}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="color: white; font-size: 0.8em;">
                                        <span style="margin: 0 5px;">🏗️ ${file.classes || 0}</span>
                                        <span style="margin: 0 5px;">⚙️ ${file.functions || 0}</span>
                                        <span style="margin: 0 5px; color: ${complexityColor};">📊 ${file.complexity || 0}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    // Update layer counts for all layers
    updateLayerCounts(files) {
        Object.keys(this.layerDefinitions).forEach(layerType => {
            const layerFiles = this.filterFilesByLayer(files, layerType);
            const totalComponents = layerFiles.reduce((sum, f) => sum + (f.classes || 0) + (f.functions || 0), 0);
            
            const countElement = document.getElementById(`${layerType}Count`);
            if (countElement) {
                countElement.textContent = `${layerFiles.length} files, ${totalComponents} components`;
            }
        });
    }

    // Create layer overview cards
    createLayerOverviewHTML() {
        return Object.entries(this.layerDefinitions).map(([layerType, layerDef]) => {
            return `
                <div onclick="architecturalLayerManager.showArchitecturalLayer('${layerType}')" 
                     class="layer-card layer-${layerType}"
                     style="background: ${layerDef.color.bg}; padding: 20px; border-radius: 8px; cursor: pointer; transition: transform 0.2s;"
                     onmouseover="this.style.transform='translateY(-2px)'"
                     onmouseout="this.style.transform='translateY(0)'">
                    <h3 style="color: ${layerDef.color.title}; margin-bottom: 8px;">${layerDef.icon} ${layerDef.title}</h3>
                    <p style="color: ${layerDef.color.desc}; font-size: 0.9em;">${layerDef.description}</p>
                    <div style="margin-top: 10px; font-size: 0.8em; color: ${layerDef.color.count};" id="${layerType}Count">Loading...</div>
                </div>
            `;
        }).join('');
    }

    // Generate layer architecture diagram
    generateArchitectureDiagram() {
        let mermaidCode = `graph TD
    subgraph "USASpending Architecture Layers"
        direction TB
        
        %% Presentation Layer
        P[🖥️ Presentation Layer<br/>CLIs, Formatters, UIs]
        
        %% Application Layer  
        A[⚙️ Application Layer<br/>Services, Business Logic]
        
        %% Domain Layer
        D[🎯 Domain Layer<br/>Models, Entities]
        
        %% Infrastructure Layer
        I[🔧 Infrastructure Layer<br/>Database, External Services]
        
        %% Data Layer
        DA[📊 Data Layer<br/>Repositories, Storage]
        
        %% Shared Layer
        S[🔗 Shared/Utils Layer<br/>Common Utilities]
        
        %% Dependencies
        P --> A
        A --> D
        A --> I
        D --> DA
        I --> DA
        
        %% Cross-cutting concerns
        S -.-> P
        S -.-> A
        S -.-> D
        S -.-> I
        S -.-> DA
    end
    
    %% Styling
    classDef presentation fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef application fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef domain fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef infrastructure fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef data fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef shared fill:#f5f5f5,stroke:#757575,stroke-width:2px
    
    class P presentation
    class A application
    class D domain
    class I infrastructure
    class DA data
    class S shared
        `;
        
        return mermaidCode;
    }

    // Show architecture overview diagram
    async showArchitectureOverview() {
        const container = document.getElementById('architectureDiagram');
        if (!container) return;
        
        // Show loading state
        container.innerHTML = `
            <div class="loading">
                <div class="usa-spinner"></div>
                <span>Loading architecture overview...</span>
            </div>
        `;
        
        try {
            // Get layer statistics
            const stats = await this.getLayerStatistics();
            if (!stats) {
                throw new Error('Failed to load layer statistics');
            }
            
            // Generate overview HTML
            const overviewHTML = this.generateArchitectureOverviewHTML(stats);
            container.innerHTML = overviewHTML;
            
            // Update layer cards
            this.updateLayerCards(stats);
            
        } catch (error) {
            console.error('Error showing architecture overview:', error);
            container.innerHTML = `
                <div class="error-state">
                    <h4>❌ Failed to load architecture overview</h4>
                    <p>${error.message}</p>
                    <button class="usa-button" onclick="architecturalLayerManager.showArchitectureOverview()">
                        Try Again
                    </button>
                </div>
            `;
        }
    }
    
    // Show layer diagram
    async showLayerDiagram() {
        const container = document.getElementById('architectureDiagram');
        if (!container) return;
        
        container.innerHTML = `
            <div class="loading">
                <div class="usa-spinner"></div>
                <span>Generating layer diagram...</span>
            </div>
        `;
        
        try {
            const mermaidCode = this.generateArchitectureDiagram();
            
            if (window.visualizationManager) {
                await window.visualizationManager.renderMermaidDiagram(mermaidCode, 'USASpending Architecture Layers');
            } else {
                throw new Error('Visualization manager not available');
            }
        } catch (error) {
            console.error('Error showing layer diagram:', error);
            container.innerHTML = `
                <div class="error-state">
                    <h4>❌ Failed to generate layer diagram</h4>
                    <p>${error.message}</p>
                    <button class="usa-button" onclick="architecturalLayerManager.showLayerDiagram()">
                        Try Again
                    </button>
                </div>
            `;
        }
    }
    
    // Show component map
    async showComponentMap() {
        const container = document.getElementById('architectureDiagram');
        if (!container) return;
        
        container.innerHTML = `
            <div class="loading">
                <div class="usa-spinner"></div>
                <span>Loading component map...</span>
            </div>
        `;
        
        try {
            // Get files data for component mapping
            const response = await fetch('/api/files?limit=1000');
            const result = await response.json();
            
            if (!result.success) {
                throw new Error('Failed to load files data');
            }
            
            const componentMapHTML = this.generateComponentMapHTML(result.data);
            container.innerHTML = componentMapHTML;
            
        } catch (error) {
            console.error('Error showing component map:', error);
            container.innerHTML = `
                <div class="error-state">
                    <h4>❌ Failed to load component map</h4>
                    <p>${error.message}</p>
                    <button class="usa-button" onclick="architecturalLayerManager.showComponentMap()">
                        Try Again
                    </button>
                </div>
            `;
        }
    }

    // Show specific architectural layer
    async showArchitecturalLayer(layerType) {
        try {
            // Get files data
            const response = await fetch('/api/files?limit=5000');
            const result = await response.json();
            
            if (!result.success) {
                throw new Error('Failed to load files data');
            }
            
            const files = result.data;
            const layerFiles = this.filterFilesByLayer(files, layerType);
            const layerDef = this.layerDefinitions[layerType];
            
            if (!layerDef) {
                throw new Error(`Unknown layer type: ${layerType}`);
            }
            
            // Create detailed layer view
            const layerHTML = `
                <div class="layer-detail-view" style="background: ${layerDef.color.bg}; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h2 style="color: ${layerDef.color.title}; margin-bottom: 10px;">
                        ${layerDef.icon} ${layerDef.title}
                    </h2>
                    <p style="color: ${layerDef.color.desc}; margin-bottom: 20px;">
                        ${layerDef.description}
                    </p>
                    
                    <div class="layer-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px;">
                        <div style="background: rgba(255,255,255,0.8); padding: 15px; border-radius: 6px; text-align: center;">
                            <div style="font-size: 1.5em; font-weight: bold; color: ${layerDef.color.title};">${layerFiles.length}</div>
                            <div style="color: ${layerDef.color.desc}; font-size: 0.9em;">Files</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.8); padding: 15px; border-radius: 6px; text-align: center;">
                            <div style="font-size: 1.5em; font-weight: bold; color: ${layerDef.color.title};">${layerFiles.reduce((sum, f) => sum + (f.classes || 0), 0)}</div>
                            <div style="color: ${layerDef.color.desc}; font-size: 0.9em;">Classes</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.8); padding: 15px; border-radius: 6px; text-align: center;">
                            <div style="font-size: 1.5em; font-weight: bold; color: ${layerDef.color.title};">${layerFiles.reduce((sum, f) => sum + (f.functions || 0), 0)}</div>
                            <div style="color: ${layerDef.color.desc}; font-size: 0.9em;">Functions</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.8); padding: 15px; border-radius: 6px; text-align: center;">
                            <div style="font-size: 1.5em; font-weight: bold; color: ${layerDef.color.title};">${layerFiles.length > 0 ? (layerFiles.reduce((sum, f) => sum + (f.complexity || 0), 0) / layerFiles.length).toFixed(1) : '0'}</div>
                            <div style="color: ${layerDef.color.desc}; font-size: 0.9em;">Avg Complexity</div>
                        </div>
                    </div>
                    
                    <div class="layer-files">
                        <h3 style="color: ${layerDef.color.title}; margin-bottom: 15px;">📁 Files in this Layer</h3>
                        <div style="display: grid; gap: 10px;">
                            ${layerFiles.map(file => `
                                <div class="list-item" onclick="modalManager.showFileDetails(${file.id})" 
                                     style="cursor: pointer; background: rgba(255,255,255,0.9); padding: 15px; border-radius: 6px; border-left: 4px solid ${layerDef.color.title};">
                                    <div class="list-item-title" style="color: ${layerDef.color.title}; font-weight: bold;">
                                        📄 ${file.name}
                                    </div>
                                    <div class="list-item-meta" style="color: ${layerDef.color.desc}; margin: 5px 0;">
                                        ${file.path}
                                    </div>
                                    <div class="list-item-stats" style="display: flex; gap: 15px; font-size: 0.9em;">
                                        <span style="color: ${layerDef.color.count};">Classes: ${file.classes || 0}</span>
                                        <span style="color: ${layerDef.color.count};">Functions: ${file.functions || 0}</span>
                                        <span style="color: ${layerDef.color.count};">Complexity: ${file.complexity || 0}</span>
                                        <span style="color: ${layerDef.color.count};">Lines: ${file.lines || 0}</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
            
            // Show in modal or dedicated container
            if (window.modalManager) {
                const modalHTML = `
                    <div class="modal-overlay" onclick="modalManager.closeModal(this)">
                        <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 900px; max-height: 80vh; overflow-y: auto;">
                            <div class="modal-header">
                                <h2>${layerDef.icon} ${layerDef.title} Analysis</h2>
                                <button class="modal-close-btn" onclick="modalManager.closeModal(this.closest('.modal-overlay'))" 
                                        style="background: none; border: none; font-size: 1.5em; cursor: pointer; color: #666;">
                                    ✕
                                </button>
                            </div>
                            <div class="modal-body">
                                ${layerHTML}
                            </div>
                        </div>
                    </div>
                `;
                window.modalManager.showModal(modalHTML);
            } else {
                // Fallback: show in main content area
                const container = document.getElementById('layerDetails') || document.getElementById('mainContent');
                if (container) {
                    container.innerHTML = layerHTML;
                }
            }
            
        } catch (error) {
            console.error('Error showing architectural layer:', error);
            if (window.dashboard && window.dashboard.showError) {
                window.dashboard.showError(`Failed to load ${layerType} layer: ${error.message}`);
            }
        }
    }

    // Get layer statistics
    async getLayerStatistics() {
        try {
            const response = await fetch('/api/files?limit=5000');
            const result = await response.json();
            
            if (!result.success) {
                return null;
            }
            
            const files = result.data;
            const stats = {};
            
            Object.keys(this.layerDefinitions).forEach(layerType => {
                const layerFiles = this.filterFilesByLayer(files, layerType);
                const totalComplexity = layerFiles.reduce((sum, f) => sum + (f.complexity || 0), 0);
                
                stats[layerType] = {
                    files: layerFiles.length,
                    classes: layerFiles.reduce((sum, f) => sum + (f.classes || 0), 0),
                    functions: layerFiles.reduce((sum, f) => sum + (f.functions || 0), 0),
                    totalComplexity: totalComplexity,
                    avgComplexity: layerFiles.length > 0 ? totalComplexity / layerFiles.length : 0
                };
            });
            
            return stats;
        } catch (error) {
            console.error('Error getting layer statistics:', error);
            return null;
        }
    }
}

// Create global architectural layer manager instance
window.architecturalLayerManager = new ArchitecturalLayerManager();

// Global functions for backwards compatibility
window.showArchitecturalLayer = (layerType) => window.architecturalLayerManager.showArchitecturalLayer(layerType);
window.updateLayerCounts = (files) => window.architecturalLayerManager.updateLayerCounts(files);
