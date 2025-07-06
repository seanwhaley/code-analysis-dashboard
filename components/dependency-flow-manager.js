/**
 * Dependency Flow Manager
 * Shows import/export relationships for a selected file, class, or function
 */
class DependencyFlowManager {
    constructor() {
        this.currentItem = null;
        this.currentType = null; // 'file', 'class', 'function'
    }

    // Show dependency flow for a file
    async showFileFlow(fileId) {
        try {
            console.log('🔍 Loading file dependency flow for:', fileId);
            
            // Get file details
            const fileResponse = await fetch(`/api/file/${fileId}/detailed`);
            const fileResult = await fileResponse.json();
            
            if (!fileResult.success) {
                this.showFlowError('Failed to load file details');
                return;
            }
            
            const file = fileResult.data;
            this.currentItem = file;
            this.currentType = 'file';
            
            // Get all files to find what imports this file
            const allFilesResponse = await fetch('/api/files?limit=1000');
            const allFilesResult = await allFilesResponse.json();
            
            const allFiles = allFilesResult.success ? allFilesResult.data : [];
            
            // Find files that import this file
            const importingFiles = await this.findFilesImporting(file, allFiles);
            
            this.renderDependencyFlow(file, file.imports || [], importingFiles, 'file');
            
        } catch (error) {
            console.error('❌ Error loading file flow:', error);
            this.showFlowError('Failed to load file dependency flow: ' + error.message);
        }
    }

    // Show dependency flow for a class
    async showClassFlow(classId) {
        try {
            console.log('🔍 Loading class dependency flow for:', classId);
            
            // Get class details
            const classResponse = await fetch(`/api/classes?limit=5000`);
            const classResult = await classResponse.json();
            
            if (!classResult.success) {
                this.showFlowError('Failed to load class details');
                return;
            }
            
            const cls = classResult.data.find(c => c.id === classId);
            if (!cls) {
                this.showFlowError('Class not found');
                return;
            }
            
            this.currentItem = cls;
            this.currentType = 'class';
            
            // Get class methods
            const methodsResponse = await fetch(`/api/functions?class_id=${classId}&limit=1000`);
            const methodsResult = await methodsResponse.json();
            const methods = methodsResult.success ? methodsResult.data : [];
            
            // Find what this class imports (from its file)
            const fileResponse = await fetch(`/api/file/${cls.file_id}/detailed`);
            const fileResult = await fileResponse.json();
            const fileImports = fileResult.success && fileResult.data.imports ? fileResult.data.imports : [];
            
            // Find what imports this class
            const importingItems = await this.findItemsImportingClass(cls);
            
            this.renderDependencyFlow(cls, fileImports, importingItems, 'class', methods);
            
        } catch (error) {
            console.error('❌ Error loading class flow:', error);
            this.showFlowError('Failed to load class dependency flow: ' + error.message);
        }
    }

    // Show dependency flow for a function
    async showFunctionFlow(functionId) {
        try {
            console.log('🔍 Loading function dependency flow for:', functionId);
            
            // Get function details
            const functionResponse = await fetch(`/api/functions?limit=5000`);
            const functionResult = await functionResponse.json();
            
            if (!functionResult.success) {
                this.showFlowError('Failed to load function details');
                return;
            }
            
            const func = functionResult.data.find(f => f.id === functionId);
            if (!func) {
                this.showFlowError('Function not found');
                return;
            }
            
            this.currentItem = func;
            this.currentType = 'function';
            
            // Get function's file imports
            const fileResponse = await fetch(`/api/file/${func.file_id}/detailed`);
            const fileResult = await fileResponse.json();
            const fileImports = fileResult.success && fileResult.data.imports ? fileResult.data.imports : [];
            
            // Find what calls this function (simplified - would need call graph analysis)
            const callingItems = await this.findItemsCallingFunction(func);
            
            this.renderDependencyFlow(func, fileImports, callingItems, 'function');
            
        } catch (error) {
            console.error('❌ Error loading function flow:', error);
            this.showFlowError('Failed to load function dependency flow: ' + error.message);
        }
    }

    // Render the three-column dependency flow view
    renderDependencyFlow(item, imports, dependents, type, methods = []) {
        const container = document.getElementById('dependencyList');
        if (!container) {
            console.error('❌ Dependency container not found');
            return;
        }

        const itemIcon = type === 'file' ? '📄' : type === 'class' ? '🏗️' : '⚙️';
        const itemName = item.name || item.path || 'Unknown';

        container.innerHTML = `
            <div style="background: var(--dashboard-bg-secondary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light);">
                <h3 style="color: var(--dashboard-text-primary); margin-bottom: 20px; text-align: center;">
                    ${itemIcon} Dependency Flow: ${itemName}
                </h3>
                
                <!-- Three Column Layout -->
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; min-height: 400px;">
                    
                    <!-- Left Column: What this item imports -->
                    <div style="background: var(--dashboard-bg-tertiary); padding: 15px; border-radius: 6px; border: 1px solid var(--dashboard-border-light);">
                        <h4 style="color: var(--dashboard-accent-primary); margin-bottom: 15px; text-align: center; border-bottom: 2px solid var(--dashboard-accent-primary); padding-bottom: 8px;">
                            📥 Imports (${imports.length})
                        </h4>
                        <div style="max-height: 350px; overflow-y: auto;">
                            ${this.renderImportsList(imports)}
                        </div>
                    </div>
                    
                    <!-- Center Column: The item itself -->
                    <div style="background: var(--dashboard-bg-card); padding: 15px; border-radius: 6px; border: 2px solid var(--dashboard-accent-primary); position: relative;">
                        <h4 style="color: var(--dashboard-accent-primary); margin-bottom: 15px; text-align: center; border-bottom: 2px solid var(--dashboard-accent-primary); padding-bottom: 8px;">
                            ${itemIcon} ${type.charAt(0).toUpperCase() + type.slice(1)} Details
                        </h4>
                        <div style="max-height: 350px; overflow-y: auto;">
                            ${this.renderItemDetails(item, type, methods)}
                        </div>
                        
                        <!-- Center indicator -->
                        <div style="position: absolute; top: 50%; left: -10px; width: 20px; height: 20px; background: var(--dashboard-accent-primary); border-radius: 50%; transform: translateY(-50%); display: flex; align-items: center; justify-content: center; color: white; font-size: 0.8em;">
                            ${itemIcon}
                        </div>
                        <div style="position: absolute; top: 50%; right: -10px; width: 20px; height: 20px; background: var(--dashboard-accent-primary); border-radius: 50%; transform: translateY(-50%); display: flex; align-items: center; justify-content: center; color: white; font-size: 0.8em;">
                            ${itemIcon}
                        </div>
                    </div>
                    
                    <!-- Right Column: What imports/uses this item -->
                    <div style="background: var(--dashboard-bg-tertiary); padding: 15px; border-radius: 6px; border: 1px solid var(--dashboard-border-light);">
                        <h4 style="color: var(--dashboard-accent-secondary); margin-bottom: 15px; text-align: center; border-bottom: 2px solid var(--dashboard-accent-secondary); padding-bottom: 8px;">
                            📤 Used By (${dependents.length})
                        </h4>
                        <div style="max-height: 350px; overflow-y: auto;">
                            ${this.renderDependentsList(dependents, type)}
                        </div>
                    </div>
                </div>
                
                <!-- Flow Arrows -->
                <div style="position: relative; margin-top: -200px; pointer-events: none; z-index: 1;">
                    <svg width="100%" height="200" style="position: absolute; top: 0; left: 0;">
                        <!-- Left to Center Arrow -->
                        <defs>
                            <marker id="arrowhead1" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                                <polygon points="0 0, 10 3.5, 0 7" fill="var(--dashboard-accent-primary)" />
                            </marker>
                        </defs>
                        <line x1="33%" y1="50%" x2="45%" y2="50%" stroke="var(--dashboard-accent-primary)" stroke-width="2" marker-end="url(#arrowhead1)" />
                        
                        <!-- Center to Right Arrow -->
                        <line x1="55%" y1="50%" x2="67%" y2="50%" stroke="var(--dashboard-accent-secondary)" stroke-width="2" marker-end="url(#arrowhead1)" />
                    </svg>
                </div>
                
                <!-- Legend -->
                <div style="margin-top: 20px; padding: 15px; background: var(--dashboard-bg-card); border-radius: 6px; border: 1px solid var(--dashboard-border-light);">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 10px;">📖 Flow Legend</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; font-size: 0.9em;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="color: var(--dashboard-accent-primary);">📥</span>
                            <span>Dependencies this ${type} requires</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="color: var(--dashboard-accent-primary);">${itemIcon}</span>
                            <span>The selected ${type} and its internal structure</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="color: var(--dashboard-accent-secondary);">📤</span>
                            <span>Other items that depend on this ${type}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Render imports list
    renderImportsList(imports) {
        if (imports.length === 0) {
            return `
                <div style="text-align: center; color: var(--dashboard-text-muted); font-style: italic; padding: 20px;">
                    No imports found
                </div>
            `;
        }

        return imports.map(imp => {
            const importType = imp.is_standard_library ? '📚' : imp.is_third_party ? '📦' : '🏠';
            const importColor = imp.is_standard_library ? '#28a745' : imp.is_third_party ? '#ffc107' : '#007bff';
            
            return `
                <div style="background: var(--dashboard-bg-card); padding: 10px; margin: 8px 0; border-radius: 4px; border-left: 3px solid ${importColor};">
                    <div style="font-family: monospace; font-size: 0.9em; color: var(--dashboard-text-primary); margin-bottom: 4px;">
                        <strong>${imp.module_name || imp.name}</strong>
                    </div>
                    <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">
                        ${importType} ${imp.is_standard_library ? 'Standard' : imp.is_third_party ? 'Third Party' : 'Local'} • 
                        Line ${imp.line_number || '?'}
                    </div>
                </div>
            `;
        }).join('');
    }

    // Render item details in center column
    renderItemDetails(item, type, methods = []) {
        if (type === 'file') {
            return `
                <div style="text-align: center; margin-bottom: 15px;">
                    <h5 style="color: var(--dashboard-text-primary); margin-bottom: 8px;">${item.name}</h5>
                    <div style="color: var(--dashboard-text-muted); font-size: 0.9em;">${item.path}</div>
                </div>
                
                <div style="display: grid; gap: 10px;">
                    <div style="background: var(--dashboard-bg-tertiary); padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${item.classes ? item.classes.length : 0}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">Classes</div>
                    </div>
                    <div style="background: var(--dashboard-bg-tertiary); padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${item.functions ? item.functions.length : 0}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">Functions</div>
                    </div>
                    <div style="background: var(--dashboard-bg-tertiary); padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${item.imports ? item.imports.length : 0}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">Imports</div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
                    <button class="usa-button usa-button--outline" onclick="modalManager.showFileDetails(${item.id})">
                        View Details
                    </button>
                    <button class="usa-button usa-button--accent-cool" onclick="modalManager.closeModal(); dependencyFlowManager.showFileFlow(${item.id})">
                        🌊 Flow View
                    </button>
                </div>
            `;
        } else if (type === 'class') {
            return `
                <div style="text-align: center; margin-bottom: 15px;">
                    <h5 style="color: var(--dashboard-text-primary); margin-bottom: 8px;">${item.name}</h5>
                    <div style="color: var(--dashboard-text-muted); font-size: 0.9em;">Line ${item.line_number || '?'}</div>
                </div>
                
                <div style="display: grid; gap: 10px;">
                    <div style="background: var(--dashboard-bg-tertiary); padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${methods.length}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">Methods</div>
                    </div>
                    <div style="background: var(--dashboard-bg-tertiary); padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${methods.filter(m => m.is_async).length}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">Async</div>
                    </div>
                    <div style="background: var(--dashboard-bg-tertiary); padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${methods.filter(m => m.is_property).length}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">Properties</div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
                    <button class="usa-button usa-button--outline" onclick="modalManager.showClassDetails(${item.id})">
                        View Details
                    </button>
                    <button class="usa-button usa-button--accent-cool" onclick="modalManager.closeModal(); dependencyFlowManager.showClassFlow(${item.id})">
                        🌊 Flow View
                    </button>
                </div>
            `;
        } else { // function
            return `
                <div style="text-align: center; margin-bottom: 15px;">
                    <h5 style="color: var(--dashboard-text-primary); margin-bottom: 8px;">${item.name}</h5>
                    <div style="color: var(--dashboard-text-muted); font-size: 0.9em;">Line ${item.line_number || '?'}</div>
                </div>
                
                <div style="display: grid; gap: 10px;">
                    <div style="background: var(--dashboard-bg-tertiary); padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${item.parameters_count || 0}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">Parameters</div>
                    </div>
                    <div style="background: var(--dashboard-bg-tertiary); padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${item.complexity || 'N/A'}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">Complexity</div>
                    </div>
                    <div style="background: var(--dashboard-bg-tertiary); padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${item.is_async ? 'Yes' : 'No'}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">Async</div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
                    <button class="usa-button usa-button--outline" onclick="modalManager.showFunctionDetails(${item.id})">
                        View Details
                    </button>
                    <button class="usa-button usa-button--accent-cool" onclick="modalManager.closeModal(); dependencyFlowManager.showFunctionFlow(${item.id})">
                        🌊 Flow View
                    </button>
                </div>
            `;
        }
    }

    // Render dependents list
    renderDependentsList(dependents, type) {
        if (dependents.length === 0) {
            return `
                <div style="text-align: center; color: var(--dashboard-text-muted); font-style: italic; padding: 20px;">
                    No dependents found
                </div>
            `;
        }

        return dependents.map(dep => {
            const depIcon = dep.type === 'file' ? '📄' : dep.type === 'class' ? '🏗️' : '⚙️';
            
            return `
                <div style="background: var(--dashboard-bg-card); padding: 10px; margin: 8px 0; border-radius: 4px; border-left: 3px solid var(--dashboard-accent-secondary); cursor: pointer;" 
                     onclick="dependencyFlowManager.show${dep.type.charAt(0).toUpperCase() + dep.type.slice(1)}Flow(${dep.id})">
                    <div style="font-weight: 600; color: var(--dashboard-text-primary); margin-bottom: 4px;">
                        ${depIcon} ${dep.name}
                    </div>
                    <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">
                        ${dep.type.charAt(0).toUpperCase() + dep.type.slice(1)} • 
                        ${dep.usage || 'Used'}
                    </div>
                </div>
            `;
        }).join('');
    }

    // Helper methods to find dependencies (simplified implementations)
    async findFilesImporting(file, allFiles) {
        // This would need more sophisticated analysis
        // For now, return empty array
        return [];
    }

    async findItemsImportingClass(cls) {
        // This would need call graph analysis
        // For now, return empty array
        return [];
    }

    async findItemsCallingFunction(func) {
        // This would need call graph analysis
        // For now, return empty array
        return [];
    }

    // Show sample flow with first available file
    async showSampleFlow() {
        try {
            console.log('🌊 Loading sample dependency flow...');
            
            // Get first file
            const response = await fetch('/api/files?limit=1');
            const result = await response.json();
            
            if (result.success && result.data && result.data.length > 0) {
                const firstFile = result.data[0];
                await this.showFileFlow(firstFile.id);
            } else {
                this.showFlowError('No files available for dependency flow analysis');
            }
        } catch (error) {
            console.error('❌ Error loading sample flow:', error);
            this.showFlowError('Failed to load sample dependency flow');
        }
    }

    // Show error message
    showFlowError(message) {
        const container = document.getElementById('dependencyList');
        if (container) {
            container.innerHTML = `
                <div style="background: var(--dashboard-bg-tertiary); padding: 30px; border-radius: 8px; text-align: center; color: var(--dashboard-text-muted);">
                    <h3 style="color: var(--dashboard-accent-error); margin-bottom: 15px;">❌ Error</h3>
                    <p>${message}</p>
                    <button class="usa-button usa-button--outline" onclick="location.reload()" style="margin-top: 15px;">
                        Refresh Page
                    </button>
                </div>
            `;
        }
    }
}

// Create global instance
window.dependencyFlowManager = new DependencyFlowManager();