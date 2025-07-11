/**
 * Visualization Components
 * Handles relationship graphs and architectural diagrams
 */

class VisualizationManager {
    constructor() {
        this.mermaidInitialized = false;
        this.chartInstances = new Map();
    }

    // Initialize Mermaid
    initializeMermaid() {
        if (typeof mermaid !== 'undefined' && !this.mermaidInitialized) {
            mermaid.initialize({ 
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose'
            });
            this.mermaidInitialized = true;
        }
    }

    // Sprint 3: Relationship visualization functions
    async showClassInheritanceGraph(useD3 = false) {
        try {
            console.log('🔍 Loading class inheritance graph...');
            const response = await fetch('/api/classes?limit=5000');
            const result = await response.json();
            
            console.log('📊 Classes API response:', result);
            
            if (!result.success) {
                console.error('❌ Classes API failed:', result);
                this.showRelationshipError('Failed to load classes for inheritance graph');
                return;
            }
            
            const classes = result.data || [];
            console.log(`🏗️ Processing ${classes.length} classes for inheritance graph`);
            
            if (classes.length === 0) {
                this.showNoClassesMessage();
                return;
            }
            
            // Build inheritance graph
            let mermaidCode = 'graph TD\n';
            const processedClasses = new Set();
            let hasInheritance = false;
            
            classes.forEach(cls => {
                if (!processedClasses.has(cls.name)) {
                    processedClasses.add(cls.name);
                    
                    // Clean class name for mermaid (remove special characters)
                    const cleanClassName = cls.name.replace(/[^a-zA-Z0-9_]/g, '_');
                    
                    // Add the class
                    mermaidCode += `    ${cleanClassName}["${cls.name}"]\n`;
                    
                    // Parse and add inheritance relationships if they exist
                    let baseClasses = [];
                    try {
                        if (cls.base_classes) {
                            if (Array.isArray(cls.base_classes)) {
                                baseClasses = cls.base_classes;
                            } else if (typeof cls.base_classes === 'string' && cls.base_classes.trim()) {
                                baseClasses = JSON.parse(cls.base_classes);
                            }
                        }
                    } catch (e) {
                        console.warn('Failed to parse base_classes for', cls.name, ':', cls.base_classes);
                    }
                    
                    if (baseClasses && baseClasses.length > 0) {
                        hasInheritance = true;
                        baseClasses.forEach(baseClass => {
                            const cleanBaseClass = baseClass.replace(/[^a-zA-Z0-9_]/g, '_');
                            mermaidCode += `    ${cleanBaseClass}["${baseClass}"] --> ${cleanClassName}\n`;
                        });
                    }
                    
                    // Style by class type
                    if (cls.class_type === 'dataclass') {
                        mermaidCode += `    class ${cleanClassName} dataclass\n`;
                    } else if (cls.class_type === 'enum') {
                        mermaidCode += `    class ${cleanClassName} enum\n`;
                    }
                }
            });
            
            // Add styles
            mermaidCode += `
    classDef dataclass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef enum fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px
            `;
            
            console.log('🎨 Generated mermaid code:', mermaidCode);
            
            if (!hasInheritance) {
                this.showNoInheritanceMessage(classes.length);
            } else if (useD3 && window.d3Visualizer) {
                // Use D3 for interactive visualization
                console.log('🎨 Using D3 for class inheritance visualization');
                try {
                    await window.d3Visualizer.createClassHierarchyTree(classes, 'relationshipDiagram');
                } catch (d3Error) {
                    console.error('❌ D3 visualization failed:', d3Error);
                    console.log('🔄 Falling back to Mermaid...');
                    this.renderMermaidDiagram(mermaidCode, 'Class Inheritance Graph');
                }
            } else {
                // Fallback to Mermaid
                console.log('🎨 Using Mermaid for class inheritance visualization');
                this.renderMermaidDiagram(mermaidCode, 'Class Inheritance Graph');
            }
        } catch (error) {
            console.error('❌ Error creating inheritance graph:', error);
            this.showRelationshipError('Failed to create inheritance graph: ' + error.message);
        }
    }
    
    async showImportDependencies(useD3 = false) {
        try {
            console.log('🔍 Loading import dependencies...');
            const response = await fetch('/api/files?limit=100');
            const result = await response.json();
            
            console.log('📊 Files API response for dependencies:', result);
            
            if (!result.success) {
                console.error('❌ Files API failed:', result);
                this.showRelationshipError('Failed to load files for dependency graph');
                return;
            }
            
            const files = result.data || [];
            console.log(`📁 Processing ${files.length} files for import dependencies`);
            
            if (files.length === 0) {
                this.showNoFilesMessage();
                return;
            }
            
            // Get detailed imports for each file
            let mermaidCode = 'graph LR\n';
            const processedConnections = new Set();
            let hasConnections = false;
            
            for (const file of files.slice(0, 20)) { // Limit to first 20 files for readability
                try {
                    console.log(`🔍 Processing imports for: ${file.name}`);
                    const detailResponse = await fetch(`/api/file/${file.id}/detailed`);
                    const detailResult = await detailResponse.json();
                    
                    if (detailResult.success && detailResult.data && detailResult.data.imports) {
                        const fileName = file.name.replace(/\.py$/, '').replace(/[^a-zA-Z0-9]/g, '_');
                        console.log(`📦 Found ${detailResult.data.imports.length} imports in ${file.name}`);
                        
                        detailResult.data.imports.forEach(imp => {
                            // Only show internal dependencies (not external libraries)
                            const module = imp.module_name || imp.module || imp.name;
                            if (module && !this.isExternalLibrary(module) && module.length < 30) {
                                const cleanModule = module.replace(/[^a-zA-Z0-9_]/g, '_');
                                const connection = `${cleanModule} --> ${fileName}`;
                                if (!processedConnections.has(connection)) {
                                    processedConnections.add(connection);
                                    mermaidCode += `    ${cleanModule}["${module}"] --> ${fileName}["${file.name}"]\n`;
                                    hasConnections = true;
                                }
                            }
                        });
                    } else {
                        console.warn(`⚠️ No imports found for ${file.name}`);
                    }
                } catch (error) {
                    console.error(`❌ Error processing file ${file.name}:`, error);
                }
            }
            
            console.debug("✅ Processed dependencies, found connections: ${hasConnections}");
            
            if (!hasConnections) {
                this.showNoDependenciesMessage(files.length);
            } else if (useD3 && window.d3Visualizer) {
                // Use D3 for interactive network visualization
                console.log('🎨 Using D3 for dependency network visualization');
                try {
                    const dependencies = Array.from(processedConnections).map(conn => {
                        const [source, target] = conn.split(' --> ');
                        return { source, target, type: 'import' };
                    });
                    await window.d3Visualizer.createDependencyNetwork(dependencies, 'relationshipDiagram');
                } catch (d3Error) {
                    console.error('❌ D3 network visualization failed:', d3Error);
                    console.log('🔄 Falling back to Mermaid...');
                    this.renderMermaidDiagram(mermaidCode, 'Import Dependencies (Sample)');
                }
            } else {
                // Fallback to Mermaid
                console.log('🎨 Using Mermaid for dependency visualization');
                this.renderMermaidDiagram(mermaidCode, 'Import Dependencies (Sample)');
            }
        } catch (error) {
            console.error('❌ Error creating dependency graph:', error);
            this.showRelationshipError('Failed to create dependency graph: ' + error.message);
        }
    }
    
    async showFunctionCallGraph() {
        try {
            console.log('🔍 Loading function overview...');
            const response = await fetch('/api/functions?limit=100');
            const result = await response.json();
            
            console.log('📊 Functions API response:', result);
            
            if (!result.success) {
                console.error('❌ Functions API failed:', result);
                this.showRelationshipError('Failed to load functions for overview');
                return;
            }
            
            const functions = result.data || [];
            console.log(`⚙️ Processing ${functions.length} functions for overview`);
            
            if (functions.length === 0) {
                this.showNoFunctionsMessage();
                return;
            }
            
            // Create a function overview instead of call graph (which requires more complex analysis)
            this.showFunctionOverview(functions);
        } catch (error) {
            console.error('❌ Error creating function overview:', error);
            this.showRelationshipError('Failed to create function overview: ' + error.message);
        }
    }

    // Show function overview
    showFunctionOverview(functions) {
        const container = document.getElementById('relationshipDiagram');
        if (!container) return;

        // Group functions by type and file
        const functionsByType = {
            methods: functions.filter(f => f.class_id),
            functions: functions.filter(f => !f.class_id),
            async: functions.filter(f => f.is_async),
            properties: functions.filter(f => f.is_property),
            static: functions.filter(f => f.is_static)
        };

        const html = `
            <h3 style="margin-bottom: 20px; color: var(--dashboard-text-primary);">⚙️ Function Overview</h3>
            
            <!-- Function Statistics -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div style="background: var(--dashboard-bg-tertiary); padding: 15px; border-radius: 6px; text-align: center; border-left: 3px solid #7b1fa2;">
                    <div style="color: var(--dashboard-text-primary); font-size: 1.5rem; font-weight: 600;">${functions.length}</div>
                    <div style="color: var(--dashboard-text-muted); font-size: 0.9em;">Total Functions</div>
                </div>
                <div style="background: var(--dashboard-bg-tertiary); padding: 15px; border-radius: 6px; text-align: center; border-left: 3px solid #2e7d32;">
                    <div style="color: var(--dashboard-text-primary); font-size: 1.5rem; font-weight: 600;">${functionsByType.methods.length}</div>
                    <div style="color: var(--dashboard-text-muted); font-size: 0.9em;">Class Methods</div>
                </div>
                <div style="background: var(--dashboard-bg-tertiary); padding: 15px; border-radius: 6px; text-align: center; border-left: 3px solid #1976d2;">
                    <div style="color: var(--dashboard-text-primary); font-size: 1.5rem; font-weight: 600;">${functionsByType.async.length}</div>
                    <div style="color: var(--dashboard-text-muted); font-size: 0.9em;">Async Functions</div>
                </div>
                <div style="background: var(--dashboard-bg-tertiary); padding: 15px; border-radius: 6px; text-align: center; border-left: 3px solid #f57c00;">
                    <div style="color: var(--dashboard-text-primary); font-size: 1.5rem; font-weight: 600;">${functionsByType.properties.length}</div>
                    <div style="color: var(--dashboard-text-muted); font-size: 0.9em;">Properties</div>
                </div>
            </div>

            <!-- Function Types Breakdown -->
            <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light); margin-bottom: 20px;">
                <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">Function Types Distribution</h4>
                <div style="display: grid; gap: 10px;">
                    ${Object.entries(functionsByType).map(([type, funcs]) => {
                        if (funcs.length === 0) return '';
                        const percentage = ((funcs.length / functions.length) * 100).toFixed(1);
                        const color = this.getFunctionTypeColor(type);
                        return `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: var(--dashboard-bg-card); border-radius: 4px; border-left: 3px solid ${color};">
                                <span style="color: var(--dashboard-text-primary); font-weight: 600; text-transform: capitalize;">${type}</span>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="color: var(--dashboard-text-secondary);">${funcs.length} functions</span>
                                    <span style="background: ${color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;">${percentage}%</span>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>

            <!-- Sample Functions -->
            <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light);">
                <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">Sample Functions</h4>
                <div style="max-height: 300px; overflow-y: auto;">
                    ${functions.slice(0, 10).map(func => `
                        <div class="list-item" onclick="modalManager.showFunctionDetails(${func.id})" style="margin-bottom: 8px; cursor: pointer;">
                            <div class="list-item-title">
                                ${func.name}(${func.parameters_count || 0} params)
                                ${func.is_async ? '<span style="background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-left: 8px;">async</span>' : ''}
                                ${func.is_property ? '<span style="background: #fff3e0; color: #f57c00; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-left: 8px;">property</span>' : ''}
                            </div>
                            <div class="list-item-meta">
                                ${func.file_path || 'Unknown file'} • Line ${func.line_number || '?'} • ${func.function_type || 'function'}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Legend -->
            <div style="margin-top: 15px; padding: 10px; background: var(--dashboard-bg-card); border-radius: 4px; font-size: 0.9em; color: var(--dashboard-text-secondary);">
                <strong>💡 Legend:</strong>
                <span style="color: #7b1fa2;">●</span> Functions • 
                <span style="color: #2e7d32;">●</span> Methods • 
                <span style="color: #1976d2;">●</span> Async • 
                <span style="color: #f57c00;">●</span> Properties
            </div>
        `;

        container.innerHTML = html;
    }

    // Get function type color
    getFunctionTypeColor(type) {
        const colors = {
            methods: '#2e7d32',
            functions: '#7b1fa2',
            async: '#1976d2',
            properties: '#f57c00',
            static: '#795548'
        };
        return colors[type] || '#6c757d';
    }

    // Show no functions message
    showNoFunctionsMessage() {
        const container = document.getElementById('relationshipDiagram');
        if (container) {
            container.innerHTML = `
                <div style="background: var(--dashboard-bg-tertiary); padding: 30px; border-radius: 8px; text-align: center; color: var(--dashboard-text-muted);">
                    <h3 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">⚙️ No Functions Found</h3>
                    <p>No functions were found in the analyzed codebase.</p>
                    <p style="font-size: 0.9em; margin-top: 15px;">This could mean:</p>
                    <ul style="text-align: left; display: inline-block; margin-top: 10px;">
                        <li>The codebase doesn't contain function definitions</li>
                        <li>Functions haven't been analyzed yet</li>
                        <li>The analysis needs to be refreshed</li>
                    </ul>
                </div>
            `;
        }
    }
    
    renderMermaidDiagram(mermaidCode, title) {
        console.log('🎨 Rendering mermaid diagram:', title);
        const container = document.getElementById('relationshipDiagram');
        
        if (!container) {
            console.error('❌ Relationship diagram container not found');
            return;
        }
        
        console.log('📊 Mermaid code to render:', mermaidCode);
        
        // Clear previous diagram
        container.innerHTML = `
            <h3 style="margin-bottom: 15px; color: var(--dashboard-text-primary);">${title}</h3>
            <div id="mermaidDiagram" style="min-height: 300px; background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light);">
                <div class="mermaid" style="text-align: center;">
                    ${mermaidCode}
                </div>
            </div>
            <div style="margin-top: 10px; padding: 10px; background: var(--dashboard-bg-card); border-radius: 4px; font-size: 0.9em; color: var(--dashboard-text-secondary);">
                <strong>💡 Diagram Legend:</strong>
                Boxes represent code elements • Arrows show relationships • Colors indicate different types
            </div>
        `;
        
        // Re-initialize Mermaid for the new diagram
        this.initializeMermaid();
        if (typeof mermaid !== 'undefined') {
            try {
                console.log('🔄 Initializing mermaid diagram...');
                // Use a unique ID for each diagram
                const diagramId = 'mermaid-' + Date.now();
                const mermaidElement = container.querySelector('.mermaid');
                mermaidElement.id = diagramId;
                
                mermaid.init(undefined, `#${diagramId}`);
                console.log('✅ Mermaid diagram rendered successfully');
            } catch (error) {
                console.error('❌ Error rendering mermaid diagram:', error);
                container.querySelector('#mermaidDiagram').innerHTML = `
                    <div style="color: var(--dashboard-accent-error); text-align: center; padding: 20px;">
                        ❌ Failed to render diagram: ${error.message}
                        <br><br>
                        <details style="margin-top: 10px;">
                            <summary style="cursor: pointer; color: var(--dashboard-accent-primary);">View Mermaid Code</summary>
                            <pre style="background: var(--dashboard-bg-secondary); padding: 10px; border-radius: 4px; margin-top: 10px; text-align: left; font-size: 0.8em; overflow-x: auto;">${mermaidCode}</pre>
                        </details>
                        <button class="usa-button usa-button--outline" onclick="location.reload()" style="margin-top: 15px;">
                            Refresh Page
                        </button>
                    </div>
                `;
            }
        } else {
            console.warn('⚠️ Mermaid library not available');
            container.querySelector('#mermaidDiagram').innerHTML = `
                <div style="color: var(--dashboard-accent-warning); text-align: center; padding: 20px;">
                    ⚠️ Mermaid library not loaded
                    <br><br>
                    <button class="usa-button usa-button--outline" onclick="location.reload()" style="margin-top: 15px;">
                        Refresh Page
                    </button>
                </div>
            `;
        }
    }

    // Dependency analysis functions
    async showModuleDependencies() {
        try {
            const response = await fetch('/api/files?limit=100');
            const result = await response.json();
            
            if (!result.success) {
                window.dashboard.showError('Failed to load files for dependency analysis');
                return;
            }
            
            const files = result.data;
            const dependencies = new Map();
            
            // Analyze dependencies by domain
            files.forEach(file => {
                const domain = file.domain || 'unknown';
                if (!dependencies.has(domain)) {
                    dependencies.set(domain, {
                        files: [],
                        totalComplexity: 0,
                        avgComplexity: 0
                    });
                }
                
                const domainData = dependencies.get(domain);
                domainData.files.push(file);
                domainData.totalComplexity += file.complexity || 0;
                domainData.avgComplexity = domainData.totalComplexity / domainData.files.length;
            });
            
            let html = `
                <h3 style="margin-bottom: 15px; color: white;">📦 Module Dependencies by Domain</h3>
                <div style="display: grid; gap: 15px;">
            `;
            
            Array.from(dependencies.entries()).sort(([,a], [,b]) => b.files.length - a.files.length).forEach(([domain, data]) => {
                const complexityClass = data.avgComplexity > 50 ? 'high' : data.avgComplexity > 25 ? 'medium' : 'low';
                const complexityColor = complexityClass === 'high' ? '#dc3545' : complexityClass === 'medium' ? '#ffc107' : '#28a745';
                
                html += `
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; border-left: 4px solid ${complexityColor};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h4 style="color: white; margin: 0;">${domain}</h4>
                            <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; color: white; font-size: 0.8em;">${data.files.length} files</span>
                        </div>
                        <div style="color: rgba(255,255,255,0.8); font-size: 0.9em;">
                            Average Complexity: ${data.avgComplexity.toFixed(1)} 
                            <span style="color: ${complexityColor}; font-weight: 600;">(${complexityClass.toUpperCase()})</span>
                        </div>
                        <div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px;">
                            ${data.files.slice(0, 5).map(file => `
                                <span style="background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 3px; font-size: 0.7em; color: rgba(255,255,255,0.9);" onclick="modalManager.showFileDetails(${file.id})" title="${file.path}">${file.name}</span>
                            `).join('')}
                            ${data.files.length > 5 ? `<span style="color: rgba(255,255,255,0.7); font-size: 0.7em;">+${data.files.length - 5} more</span>` : ''}
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            
            document.getElementById('dependencyList').innerHTML = html;
        } catch (error) {
            console.error('Error analyzing module dependencies:', error);
            window.dashboard.showError('Failed to analyze module dependencies');
        }
    }
    
    async showExternalLibraries() {
        try {
            console.log('🔍 Loading external libraries analysis...');
            const response = await fetch('/api/files?limit=200');
            const result = await response.json();
            
            console.log('📊 Files API response:', result);
            
            if (!result.success) {
                console.error('❌ Files API failed:', result);
                this.showLibrariesError('Failed to load files for library analysis');
                return;
            }
            
            const files = result.data;
            console.log(`📁 Processing ${files.length} files for library analysis`);
            const libraries = new Map();
            
            // Collect external libraries from imports
            let processedFiles = 0;
            for (const file of files.slice(0, 50)) { // Sample first 50 files
                try {
                    console.log(`🔍 Processing file: ${file.name}`);
                    const detailResponse = await fetch(`/api/file/${file.id}/detailed`);
                    const detailResult = await detailResponse.json();
                    
                    console.log(`📄 Detail response for ${file.name}:`, detailResult);
                    
                    if (detailResult.success && detailResult.data && detailResult.data.imports) {
                        console.log(`📦 Found ${detailResult.data.imports.length} imports in ${file.name}`);
                        detailResult.data.imports.forEach(imp => {
                            // Identify external libraries (common patterns)
                            const module = imp.module_name || imp.module || imp.name;
                            if (module) {
                                // Check if it's a standard library or common third-party library
                                const commonLibraries = ['pandas', 'numpy', 'requests', 'fastapi', 'pydantic', 'sqlite3', 'json', 'os', 'sys', 'pathlib', 'typing', 'datetime', 'logging', 'asyncio', 'typer', 'langchain', 'neo4j', 'chart', 'mermaid', 'flask', 'django', 'pytest', 'click', 'sqlalchemy'];
                                const isExternal = module.includes('.') || commonLibraries.includes(module.split('.')[0]);
                                
                                if (isExternal) {
                                    const libName = module.split('.')[0];
                                    if (!libraries.has(libName)) {
                                        libraries.set(libName, {
                                            count: 0,
                                            files: new Set(),
                                            imports: [],
                                            isStandardLibrary: imp.is_standard_library || false,
                                            isThirdParty: imp.is_third_party || false
                                        });
                                    }
                                    
                                    const libData = libraries.get(libName);
                                    libData.count++;
                                    libData.files.add(file.name);
                                    libData.imports.push({
                                        file: file.name,
                                        import: imp.imported_names || imp.name || module,
                                        type: imp.import_type,
                                        module: module
                                    });
                                    
                                    console.log(`📚 Added library: ${libName} from ${file.name}`);
                                }
                            }
                        });
                        processedFiles++;
                    } else {
                        console.warn(`⚠️ No imports found for ${file.name}:`, detailResult);
                    }
                } catch (error) {
                    console.error(`❌ Error processing file ${file.name}:`, error);
                }
            }
            
            console.debug("✅ Processed ${processedFiles} files, found ${libraries.size} libraries");
            
            // If no libraries found from detailed analysis, try a fallback approach
            if (libraries.size === 0) {
                console.debug("🔄 No libraries found via detailed analysis, trying fallback...");
                this.addFallbackLibraries(libraries, files);
            }
            
            let html = `
                <h3 style="margin-bottom: 15px; color: var(--dashboard-text-primary);">📚 External Libraries Usage</h3>
            `;
            
            if (libraries.size === 0) {
                html += `
                    <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 6px; text-align: center; color: var(--dashboard-text-muted);">
                        <p>No external libraries detected in the analyzed files.</p>
                        <p style="font-size: 0.9em; margin-top: 10px;">This could mean:</p>
                        <ul style="text-align: left; display: inline-block; margin-top: 10px;">
                            <li>Files don't contain import statements</li>
                            <li>Only internal modules are being imported</li>
                            <li>Import data needs to be refreshed</li>
                        </ul>
                    </div>
                `;
            } else {
                html += '<div style="display: grid; gap: 12px;">';
                
                Array.from(libraries.entries()).sort(([,a], [,b]) => b.count - a.count).forEach(([libName, data]) => {
                    const usage = data.files.size;
                    const usageColor = usage > 10 ? '#dc3545' : usage > 5 ? '#ffc107' : '#28a745';
                    const libraryType = data.isStandardLibrary ? '📚 Standard Library' : 
                                       data.isThirdParty ? '📦 Third Party' : '🔍 Detected';
                    
                    html += `
                        <div style="background: var(--dashboard-bg-tertiary); padding: 12px; border-radius: 6px; border-left: 3px solid ${usageColor}; border: 1px solid var(--dashboard-border-light);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4 style="color: var(--dashboard-text-primary); margin: 0; flex: 1;">${libName}</h4>
                                <div style="text-align: right;">
                                    <span style="background: var(--dashboard-bg-secondary); padding: 2px 6px; border-radius: 3px; color: var(--dashboard-text-secondary); font-size: 0.7em; margin-left: 5px;">${libraryType}</span>
                                    <span style="background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 3px; color: var(--dashboard-text-primary); font-size: 0.7em; margin-left: 5px;">${data.count} imports</span>
                                    <span style="background: ${usageColor}; padding: 2px 6px; border-radius: 3px; color: white; font-size: 0.7em; margin-left: 5px;">${usage} files</span>
                                </div>
                            </div>
                            <div style="margin-top: 8px; color: var(--dashboard-text-muted); font-size: 0.8em;">
                                <strong>Used in:</strong> ${Array.from(data.files).slice(0, 3).join(', ')}${data.files.size > 3 ? ` and ${data.files.size - 3} more` : ''}
                            </div>
                            <div style="margin-top: 5px; color: var(--dashboard-text-muted); font-size: 0.75em;">
                                <strong>Sample imports:</strong> ${data.imports.slice(0, 2).map(imp => imp.import).join(', ')}${data.imports.length > 2 ? '...' : ''}
                            </div>
                        </div>
                    `;
                });
                
                html += '</div>';
            }
            
            // Check if container exists
            const container = document.getElementById('dependencyList');
            if (!container) {
                console.error('❌ dependencyList container not found!');
                return;
            }

            console.log('📦 Setting dependencyList innerHTML...');
            container.innerHTML = html;
            console.log('✅ External libraries rendered successfully');
        } catch (error) {
            console.error('❌ Error analyzing external libraries:', error);
            this.showLibrariesError('Failed to analyze external libraries: ' + error.message);
        }
    }

    // Debug method for external libraries
    async debugExternalLibraries() {
                try {
            // Test API endpoint
                        const response = await fetch('/api/files?limit=10');
            console.log('🔍 DEBUG: Response status:', response.status);
            
            const result = await response.json();
            console.log('🔍 DEBUG: Response data:', result);
            
            if (result.success && result.data && result.data.length > 0) {
                                const firstFile = result.data[0];
                console.log('🔍 DEBUG: First file:', firstFile);
                
                const detailResponse = await fetch(`/api/file/${firstFile.id}/detailed`);
                const detailResult = await detailResponse.json();
                console.log('🔍 DEBUG: Detailed file data:', detailResult);
                
                // Show debug info in the UI
                const container = document.getElementById('dependencyList');
                if (container) {
                    container.innerHTML = `
                        <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px;">
                            <h3>🔍 Debug Information</h3>
                            <div style="background: var(--dashboard-bg-card); padding: 15px; border-radius: 4px; margin: 10px 0; font-family: monospace; font-size: 0.9em;">
                                <strong>Files API Response:</strong><br>
                                Status: ${response.status}<br>
                                Success: ${result.success}<br>
                                Files Count: ${result.data ? result.data.length : 'N/A'}<br>
                                First File: ${firstFile ? firstFile.name : 'N/A'}
                            </div>
                            <div style="background: var(--dashboard-bg-card); padding: 15px; border-radius: 4px; margin: 10px 0; font-family: monospace; font-size: 0.9em;">
                                <strong>Detailed File Response:</strong><br>
                                Status: ${detailResponse.status}<br>
                                Success: ${detailResult.success}<br>
                                Has Imports: ${detailResult.data && detailResult.data.imports ? 'Yes' : 'No'}<br>
                                Imports Count: ${detailResult.data && detailResult.data.imports ? detailResult.data.imports.length : 'N/A'}
                            </div>
                            <button class="usa-button" onclick="visualizationManager.showExternalLibraries()">
                                Try External Libraries Again
                            </button>
                        </div>
                    `;
                }
            } else {
                console.error('🔍 DEBUG: No files found or API failed');
            }
            
        } catch (error) {
            console.error('🔍 DEBUG: Error during debug:', error);
        }
    }
    
    // Fallback method to add common libraries when detailed analysis fails
    addFallbackLibraries(libraries, files) {
        console.log('📚 Adding fallback libraries based on common patterns...');
        
        // Add some common libraries that are likely to be used
        const commonLibraries = [
            { name: 'os', type: 'standard', description: 'Operating system interface' },
            { name: 'sys', type: 'standard', description: 'System-specific parameters' },
            { name: 'json', type: 'standard', description: 'JSON encoder/decoder' },
            { name: 'pathlib', type: 'standard', description: 'Object-oriented filesystem paths' },
            { name: 'typing', type: 'standard', description: 'Type hints support' },
            { name: 'datetime', type: 'standard', description: 'Date and time handling' },
            { name: 'logging', type: 'standard', description: 'Logging facility' },
            { name: 'asyncio', type: 'standard', description: 'Asynchronous I/O' }
        ];
        
        commonLibraries.forEach(lib => {
            libraries.set(lib.name, {
                count: 1,
                files: new Set(['(estimated)']),
                imports: [{ file: '(estimated)', import: lib.name, type: 'import', module: lib.name }],
                isStandardLibrary: lib.type === 'standard',
                isThirdParty: lib.type === 'third-party',
                description: lib.description
            });
        });
        
        console.log(`📚 Added ${commonLibraries.length} fallback libraries`);
    }
    
    // Show libraries error
    showLibrariesError(message) {
        document.getElementById('dependencyList').innerHTML = `
            <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; text-align: center; color: var(--dashboard-accent-error);">
                <p>❌ ${message}</p>
                <button class="usa-button usa-button--outline" onclick="visualizationManager.showExternalLibraries()" style="margin-top: 15px;">
                    Try Again
                </button>
            </div>
        `;
    }

    // Show relationship error
    showRelationshipError(message) {
        const container = document.getElementById('relationshipDiagram');
        if (container) {
            container.innerHTML = `
                <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; text-align: center; color: var(--dashboard-accent-error);">
                    <p>❌ ${message}</p>
                    <button class="usa-button usa-button--outline" onclick="location.reload()" style="margin-top: 15px;">
                        Refresh Page
                    </button>
                </div>
            `;
        }
    }

    // Show no classes message
    showNoClassesMessage() {
        const container = document.getElementById('relationshipDiagram');
        if (container) {
            container.innerHTML = `
                <div style="background: var(--dashboard-bg-tertiary); padding: 30px; border-radius: 8px; text-align: center; color: var(--dashboard-text-muted);">
                    <h3 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">🏗️ No Classes Found</h3>
                    <p>No classes were found in the analyzed codebase.</p>
                    <p style="font-size: 0.9em; margin-top: 15px;">This could mean:</p>
                    <ul style="text-align: left; display: inline-block; margin-top: 10px;">
                        <li>The codebase doesn't contain class definitions</li>
                        <li>Classes haven't been analyzed yet</li>
                        <li>The analysis needs to be refreshed</li>
                    </ul>
                </div>
            `;
        }
    }

    // Show no inheritance message
    showNoInheritanceMessage(classCount) {
        const container = document.getElementById('relationshipDiagram');
        if (container) {
            container.innerHTML = `
                <div style="background: var(--dashboard-bg-tertiary); padding: 30px; border-radius: 8px; text-align: center; color: var(--dashboard-text-muted);">
                    <h3 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">🏗️ Class Overview</h3>
                    <p>Found <strong>${classCount}</strong> classes, but no inheritance relationships detected.</p>
                    <div style="margin-top: 20px; padding: 15px; background: var(--dashboard-bg-secondary); border-radius: 6px;">
                        <h4 style="color: var(--dashboard-text-primary); margin-bottom: 10px;">Classes in your codebase:</h4>
                        <div style="text-align: left; max-height: 200px; overflow-y: auto;">
                            ${window.dashboard.data.classes ? window.dashboard.data.classes.slice(0, 10).map(cls => `
                                <div style="margin: 5px 0; padding: 5px; background: var(--dashboard-bg-card); border-radius: 4px;">
                                    <strong>${cls.name}</strong> 
                                    <span style="color: var(--dashboard-text-muted); font-size: 0.9em;">
                                        (${cls.class_type || 'class'}) - ${cls.file_path || 'Unknown file'}
                                    </span>
                                </div>
                            `).join('') : '<p>No class data available</p>'}
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding: 10px; background: var(--dashboard-bg-card); border-radius: 4px; font-size: 0.9em; color: var(--dashboard-text-secondary);">
                        💡 <strong>Tip:</strong> Inheritance relationships will appear here when classes extend other classes using syntax like <code>class Child(Parent):</code>
                    </div>
                </div>
            `;
        }
    }

    // Check if module is external library
    isExternalLibrary(module) {
        const externalLibraries = [
            'os', 'sys', 'json', 'pathlib', 'typing', 'datetime', 'logging', 'asyncio',
            'pandas', 'numpy', 'requests', 'fastapi', 'pydantic', 'sqlite3', 'typer',
            'langchain', 'neo4j', 'chart', 'mermaid', 'flask', 'django', 'pytest'
        ];
        return externalLibraries.includes(module.split('.')[0]) || module.includes('.');
    }

    // Show no files message
    showNoFilesMessage() {
        const container = document.getElementById('relationshipDiagram');
        if (container) {
            container.innerHTML = `
                <div style="background: var(--dashboard-bg-tertiary); padding: 30px; border-radius: 8px; text-align: center; color: var(--dashboard-text-muted);">
                    <h3 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">📁 No Files Found</h3>
                    <p>No files were found for dependency analysis.</p>
                    <p style="font-size: 0.9em; margin-top: 15px;">Please ensure files have been analyzed and try again.</p>
                </div>
            `;
        }
    }

    // Show no dependencies message
    showNoDependenciesMessage(fileCount) {
        const container = document.getElementById('relationshipDiagram');
        if (container) {
            container.innerHTML = `
                <div style="background: var(--dashboard-bg-tertiary); padding: 30px; border-radius: 8px; text-align: center; color: var(--dashboard-text-muted);">
                    <h3 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">📦 Import Dependencies</h3>
                    <p>Analyzed <strong>${fileCount}</strong> files, but no internal dependencies found.</p>
                    <div style="margin-top: 20px; padding: 15px; background: var(--dashboard-bg-secondary); border-radius: 6px; text-align: left;">
                        <h4 style="color: var(--dashboard-text-primary); margin-bottom: 10px;">This could mean:</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Files only import external libraries</li>
                            <li>No import statements were detected</li>
                            <li>All imports are from standard library</li>
                            <li>Files are self-contained modules</li>
                        </ul>
                    </div>
                    <div style="margin-top: 15px; padding: 10px; background: var(--dashboard-bg-card); border-radius: 4px; font-size: 0.9em; color: var(--dashboard-text-secondary);">
                        💡 <strong>Tip:</strong> Internal dependencies appear when files import from other files in your project using relative or absolute imports.
                    </div>
                </div>
            `;
        }
    }

    // Clean up chart instances
    destroyChart(chartId) {
        if (this.chartInstances.has(chartId)) {
            this.chartInstances.get(chartId).destroy();
            this.chartInstances.delete(chartId);
        }
    }

    // Clean up all charts
    destroyAllCharts() {
        this.chartInstances.forEach(chart => chart.destroy());
        this.chartInstances.clear();
    }

    // Show code relationships overview
    async showCodeRelationships() {
        const container = document.getElementById('relationshipDiagram') || document.getElementById('mainContent');
        if (!container) {
            console.error('No container found for code relationships');
            return;
        }

        // Show loading state
        container.innerHTML = `
            <div class="loading">
                <div class="usa-spinner"></div>
                <span>Loading code relationships...</span>
            </div>
        `;

        try {
            // Get data for relationships
            const [filesResponse, classesResponse, functionsResponse] = await Promise.all([
                fetch('/api/files?limit=1000'),
                fetch('/api/classes?limit=1000'),
                fetch('/api/functions?limit=1000')
            ]);

            const [filesResult, classesResult, functionsResult] = await Promise.all([
                filesResponse.json(),
                classesResponse.json(),
                functionsResponse.json()
            ]);

            if (!filesResult.success || !classesResult.success || !functionsResult.success) {
                throw new Error('Failed to load relationship data');
            }

            const files = filesResult.data;
            const classes = classesResult.data;
            const functions = functionsResult.data;

            // Create relationships overview
            const relationshipsHTML = `
                <div class="relationships-overview">
                    <h2 style="margin-bottom: 20px;">🔗 Code Relationships Overview</h2>
                    
                    <div class="relationship-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px;">
                        <div class="stat-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 2em; color: #007bff;">${files.length}</div>
                            <div style="color: var(--dashboard-text-secondary);">Files</div>
                        </div>
                        <div class="stat-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 2em; color: #28a745;">${classes.length}</div>
                            <div style="color: var(--dashboard-text-secondary);">Classes</div>
                        </div>
                        <div class="stat-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 2em; color: #fd7e14;">${functions.length}</div>
                            <div style="color: var(--dashboard-text-secondary);">Functions</div>
                        </div>
                        <div class="stat-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 2em; color: #6f42c1;">${new Set(files.map(f => f.domain)).size}</div>
                            <div style="color: var(--dashboard-text-secondary);">Domains</div>
                        </div>
                    </div>

                    <div class="relationship-actions" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px;">
                        <div class="action-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; border-left: 4px solid #007bff;">
                            <h3 style="color: #007bff; margin-bottom: 10px;">🏗️ Class Inheritance</h3>
                            <p style="color: var(--dashboard-text-secondary); margin-bottom: 15px;">
                                Visualize class inheritance hierarchies and relationships between classes.
                            </p>
                            <button class="usa-button" onclick="visualizationManager.showClassInheritanceGraph(true)">
                                Show Class Hierarchy
                            </button>
                        </div>
                        
                        <div class="action-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
                            <h3 style="color: #28a745; margin-bottom: 10px;">📦 Import Dependencies</h3>
                            <p style="color: var(--dashboard-text-secondary); margin-bottom: 15px;">
                                Explore how files import and depend on each other across the codebase.
                            </p>
                            <button class="usa-button usa-button--outline" onclick="visualizationManager.showImportDependencies()">
                                Show Dependencies
                            </button>
                        </div>
                        
                        <div class="action-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; border-left: 4px solid #fd7e14;">
                            <h3 style="color: #fd7e14; margin-bottom: 10px;">⚙️ Function Calls</h3>
                            <p style="color: var(--dashboard-text-secondary); margin-bottom: 15px;">
                                Analyze function call patterns and method interactions.
                            </p>
                            <button class="usa-button usa-button--outline" onclick="visualizationManager.showFunctionCallGraph()">
                                Show Function Calls
                            </button>
                        </div>
                        
                        <div class="action-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; border-left: 4px solid #6f42c1;">
                            <h3 style="color: #6f42c1; margin-bottom: 10px;">🌐 Module Network</h3>
                            <p style="color: var(--dashboard-text-secondary); margin-bottom: 15px;">
                                View the overall module structure and cross-module dependencies.
                            </p>
                            <button class="usa-button usa-button--outline" onclick="visualizationManager.showModuleDependencies()">
                                Show Module Network
                            </button>
                        </div>
                    </div>

                    <div class="domain-breakdown" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px;">
                        <h3 style="margin-bottom: 15px;">🏷️ Domain Breakdown</h3>
                        <div style="display: grid; gap: 10px;">
                            ${Array.from(new Set(files.map(f => f.domain))).map(domain => {
                                const domainFiles = files.filter(f => f.domain === domain);
                                const domainClasses = classes.filter(c => c.domain === domain);
                                const domainFunctions = functions.filter(f => domainFiles.some(df => df.id === f.file_id));
                                
                                return `
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: var(--dashboard-bg-tertiary); border-radius: 4px;">
                                        <div>
                                            <strong style="color: var(--dashboard-text-primary);">${domain}</strong>
                                        </div>
                                        <div style="display: flex; gap: 15px; font-size: 0.9em; color: var(--dashboard-text-secondary);">
                                            <span>📄 ${domainFiles.length} files</span>
                                            <span>🏗️ ${domainClasses.length} classes</span>
                                            <span>⚙️ ${domainFunctions.length} functions</span>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                </div>
            `;

            container.innerHTML = relationshipsHTML;

        } catch (error) {
            console.error('Error showing code relationships:', error);
            container.innerHTML = `
                <div class="error-state">
                    <h4>❌ Failed to load code relationships</h4>
                    <p>${error.message}</p>
                    <button class="usa-button" onclick="visualizationManager.showCodeRelationships()">
                        Try Again
                    </button>
                </div>
            `;
        }
    }
}

// Create global visualization manager instance
window.visualizationManager = new VisualizationManager();

// Global functions for backwards compatibility
window.showClassInheritanceGraph = () => window.visualizationManager.showClassInheritanceGraph();
window.showImportDependencies = () => window.visualizationManager.showImportDependencies();
window.showFunctionCallGraph = () => window.visualizationManager.showFunctionCallGraph();
window.showModuleDependencies = () => window.visualizationManager.showModuleDependencies();
window.showExternalLibraries = () => window.visualizationManager.showExternalLibraries();
window.showCodeRelationships = () => window.visualizationManager.showCodeRelationships();
