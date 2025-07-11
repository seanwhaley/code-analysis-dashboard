/**
 * Modal Components for File, Class, and Function Details
 * Handles detailed view modals with rich AST data
 */

class ModalManager {
    constructor() {
        this.activeModals = new Set();
    }

    // Enhanced file details modal with full AST data
    async showFileDetails(fileId) {
        try {
            // Get detailed file content from API
            const detailResponse = await fetch(`/api/file/${fileId}/detailed`);
            const detailResult = await detailResponse.json();
            
            if (!detailResult.success) {
                window.dashboard.showError('Failed to load file details');
                return;
            }
            
            const fileData = detailResult.data;
            const file = window.dashboard.data.files.find(f => f.id === fileId) || fileData;
            
            // Get related classes and functions for this file
            const [classesResponse, functionsResponse] = await Promise.all([
                fetch(`/api/classes?file_id=${fileId}&limit=100`),
                fetch(`/api/functions?file_id=${fileId}&limit=100`)
            ]);
            
            const classesData = await classesResponse.json();
            const functionsData = await functionsResponse.json();
            
            const modalHtml = this.createFileModal(file, fileData, classesData.data || [], functionsData.data || []);
            this.showModal(modalHtml);
            
        } catch (error) {
            console.error('Error loading file details:', error);
            window.dashboard.showError('Failed to load detailed file information');
        }
    }

    // Create file modal HTML with nested organization
    createFileModal(file, fileData, classes = [], functions = []) {
        return `
            <div class="modal-overlay" onclick="modalManager.closeModal(this)">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h2>📄 ${file.name}</h2>
                        <button class="modal-close" onclick="modalManager.closeModal(this.closest('.modal-overlay'))">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${this.createLocationSection(file)}
                        ${this.createFileStatsSection(file, fileData)}
                        ${this.createComplexityBreakdownSection(file)}
                        ${this.createNestedCodeStructureSection(fileData)}
                        ${this.createImportsSection(fileData)}
                        ${this.createDomainSection(file)}
                    </div>
                </div>
            </div>
        `;
    }

    // Enhanced class details modal
    async showClassDetails(classId) {
        try {
            // Find class in current data or fetch if needed
            let cls = window.dashboard.data.classes.find(c => c.id === classId);
            
            if (!cls) {
                const response = await fetch(`/api/classes?limit=5000`);
                const result = await response.json();
                if (result.success) {
                    cls = result.data.find(c => c.id === classId);
                }
            }
            
            if (!cls) {
                window.dashboard.showError('Class not found');
                return;
            }
            
            // Get functions that belong to this class
            const functionsResponse = await fetch(`/api/functions?class_id=${classId}&limit=1000`);
            const functionsResult = await functionsResponse.json();
            const classFunctions = functionsResult.success ? functionsResult.data : [];
            
            const modalHtml = this.createClassModal(cls, classFunctions);
            this.showModal(modalHtml);
            
        } catch (error) {
            console.error('Error loading class details:', error);
            window.dashboard.showError('Failed to load detailed class information');
        }
    }

    // Create class modal HTML with detailed information
    createClassModal(cls, classFunctions) {
        return `
            <div class="modal-overlay" onclick="modalManager.closeModal(this)">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h2>🏗️ ${cls.name}</h2>
                        <button class="modal-close" onclick="modalManager.closeModal(this.closest('.modal-overlay'))">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${this.createLocationSection(cls)}
                        ${this.createClassOverviewSection(cls, classFunctions)}
                        ${this.createInheritanceSection(cls)}
                        ${this.createClassContentSection(classFunctions)}
                        ${this.createClassDocstringSection(cls)}
                        ${this.createDecoratorsSection(cls)}
                    </div>
                </div>
            </div>
        `;
    }

    // Enhanced function details modal
    async showFunctionDetails(functionId) {
        try {
            // Find function in current data or fetch if needed
            let func = window.dashboard.data.functions.find(f => f.id === functionId);
            
            if (!func) {
                const response = await fetch(`/api/functions?limit=5000`);
                const result = await response.json();
                if (result.success) {
                    func = result.data.find(f => f.id === functionId);
                }
            }
            
            if (!func) {
                window.dashboard.showError('Function not found');
                return;
            }
            
            const modalHtml = this.createFunctionModal(func);
            this.showModal(modalHtml);
            
        } catch (error) {
            console.error('Error loading function details:', error);
            window.dashboard.showError('Failed to load detailed function information');
        }
    }

    // Create function modal HTML
    createFunctionModal(func) {
        return `
            <div class="modal-overlay" onclick="modalManager.closeModal(this)">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h2>⚙️ ${func.name}</h2>
                        <button class="modal-close" onclick="modalManager.closeModal(this.closest('.modal-overlay'))">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${this.createLocationSection(func)}
                        ${this.createFunctionDetailsSection(func)}
                        ${this.createParametersSection(func)}
                        ${this.createReturnTypeSection(func)}
                        ${this.createDecoratorsSection(func)}
                        ${this.createDocstringSection(func)}
                    </div>
                </div>
            </div>
        `;
    }

    // Helper method sections
    createLocationSection(item) {
        return `
            <div class="detail-section">
                <h3>📍 Location</h3>
                <p><code>${item.path || item.file_path}</code>${item.line_number ? ` (Line ${item.line_number})` : ''}</p>
            </div>
        `;
    }

    createFileStatsSection(file, fileData) {
        return `
            <div class="detail-section">
                <h3>📊 Statistics</h3>
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="stat-label">Lines of Code</div>
                        <div class="stat-value">${file.lines || fileData.lines || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Classes</div>
                        <div class="stat-value">${fileData.classes?.length || file.classes || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Functions</div>
                        <div class="stat-value">${fileData.functions?.length || file.functions || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Complexity</div>
                        <div class="stat-value">${file.complexity || fileData.complexity || 0}</div>
                    </div>
                </div>
            </div>
        `;
    }

    createClassesSection(fileData) {
        if (!fileData.classes || fileData.classes.length === 0) return '';
        
        return `
            <div class="detail-section">
                <h3>🏗️ Classes (${fileData.classes.length})</h3>
                <div style="max-height: 200px; overflow-y: auto;">
                    ${fileData.classes.map(cls => `
                        <div class="list-item" onclick="modalManager.showClassDetails(${cls.id})" style="margin-bottom: 8px; cursor: pointer;">
                            <div class="list-item-title">${cls.name}</div>
                            <div class="list-item-meta">Line ${cls.line_number || 'Unknown'} • ${cls.class_type || 'class'}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    createFunctionsSection(fileData) {
        if (!fileData.functions || fileData.functions.length === 0) return '';
        
        return `
            <div class="detail-section">
                <h3>⚙️ Functions (${fileData.functions.length})</h3>
                <div style="max-height: 200px; overflow-y: auto;">
                    ${fileData.functions.map(func => `
                        <div class="list-item" onclick="modalManager.showFunctionDetails(${func.id})" style="margin-bottom: 8px; cursor: pointer;">
                            <div class="list-item-title">${func.name}</div>
                            <div class="list-item-meta">Line ${func.line_number || 'Unknown'} • ${func.function_type || 'function'} • ${func.parameters_count || 0} params</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    createImportsSection(fileData) {
        if (!fileData.imports || fileData.imports.length === 0) return '';
        
        // Group imports by type
        const standardLibrary = fileData.imports.filter(imp => imp.is_standard_library);
        const thirdParty = fileData.imports.filter(imp => imp.is_third_party);
        const local = fileData.imports.filter(imp => !imp.is_standard_library && !imp.is_third_party);
        
        return `
            <div class="detail-section">
                <h3>📦 Imports (${fileData.imports.length})</h3>
                
                <!-- Import Statistics -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 15px;">
                    <div style="background: var(--dashboard-bg-tertiary); padding: 10px; border-radius: 4px; text-align: center; border-left: 3px solid #28a745;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${standardLibrary.length}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">📚 Standard</div>
                    </div>
                    <div style="background: var(--dashboard-bg-tertiary); padding: 10px; border-radius: 4px; text-align: center; border-left: 3px solid #ffc107;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${thirdParty.length}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">📦 3rd Party</div>
                    </div>
                    <div style="background: var(--dashboard-bg-tertiary); padding: 10px; border-radius: 4px; text-align: center; border-left: 3px solid #007bff;">
                        <div style="font-weight: 600; color: var(--dashboard-text-primary);">${local.length}</div>
                        <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">🏠 Local</div>
                    </div>
                </div>
                
                <!-- Import Details -->
                <div style="max-height: 200px; overflow-y: auto;">
                    ${this.renderImportGroup('📚 Standard Library', standardLibrary, '#28a745')}
                    ${this.renderImportGroup('📦 Third Party', thirdParty, '#ffc107')}
                    ${this.renderImportGroup('🏠 Local Modules', local, '#007bff')}
                </div>
            </div>
        `;
    }

    renderImportGroup(title, imports, color) {
        if (imports.length === 0) return '';
        
        return `
            <div style="margin-bottom: 15px;">
                <h4 style="color: ${color}; font-size: 0.9em; margin-bottom: 8px; border-bottom: 1px solid ${color}; padding-bottom: 4px;">
                    ${title} (${imports.length})
                </h4>
                ${imports.map(imp => {
                    const importedNames = Array.isArray(imp.imported_names) ? imp.imported_names : 
                                        (typeof imp.imported_names === 'string' ? JSON.parse(imp.imported_names || '[]') : []);
                    const displayNames = importedNames.length > 0 ? importedNames.join(', ') : imp.module_name;
                    
                    return `
                        <div style="background: var(--dashboard-bg-card); padding: 10px; margin: 6px 0; border-radius: 4px; border-left: 3px solid ${color};">
                            <div style="font-family: monospace; font-size: 0.9em; color: var(--dashboard-text-primary); margin-bottom: 4px;">
                                ${imp.import_type === 'from_import' ? `from <strong>${imp.module_name}</strong>` : ''} 
                                import <strong>${imp.import_type === 'import' ? imp.module_name : displayNames}</strong>
                                ${imp.alias ? ` as <strong>${imp.alias}</strong>` : ''}
                            </div>
                            <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">
                                Line ${imp.line_number || '?'} • 
                                ${imp.import_type === 'from_import' ? 'Selective import' : 'Module import'}
                                ${importedNames.length > 1 ? ` • ${importedNames.length} items` : ''}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    createDomainSection(item) {
        return `
            <div class="detail-section">
                <h3>🏷️ Domain</h3>
                <p>${item.domain}</p>
            </div>
        `;
    }

    createClassOverviewSection(cls, classFunctions) {
        // Categorize methods
        const methods = classFunctions.filter(f => f.function_type === 'method' || !f.function_type);
        const staticMethods = classFunctions.filter(f => f.is_static);
        const classMethods = classFunctions.filter(f => f.function_type === 'classmethod');
        const properties = classFunctions.filter(f => f.is_property);
        const asyncMethods = classFunctions.filter(f => f.is_async);
        const specialMethods = classFunctions.filter(f => f.name.startsWith('__') && f.name.endsWith('__'));
        
        return `
            <div class="detail-section">
                <h3>📊 Class Overview</h3>
                
                <!-- Basic Stats -->
                <div class="stats-row" style="margin-bottom: 15px;">
                    <div class="stat-item">
                        <div class="stat-label">Type</div>
                        <div class="stat-value">${cls.class_type || 'class'}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Total Methods</div>
                        <div class="stat-value">${classFunctions.length}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Line</div>
                        <div class="stat-value">${cls.line_number || 'Unknown'}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Complexity</div>
                        <div class="stat-value" style="color: ${this.getComplexityColor(cls.complexity)}">
                            ${cls.complexity || 'N/A'}
                        </div>
                    </div>
                </div>

                <!-- Method Type Breakdown -->
                <div style="background: var(--dashboard-bg-tertiary); padding: 15px; border-radius: 6px; border: 1px solid var(--dashboard-border-light);">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 10px;">Method Composition</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px;">
                        <div style="text-align: center; padding: 8px; background: var(--dashboard-bg-card); border-radius: 4px;">
                            <div style="font-size: 1.2em; font-weight: 600; color: #007bff;">${methods.length}</div>
                            <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">⚙️ Methods</div>
                        </div>
                        <div style="text-align: center; padding: 8px; background: var(--dashboard-bg-card); border-radius: 4px;">
                            <div style="font-size: 1.2em; font-weight: 600; color: #28a745;">${properties.length}</div>
                            <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">🏷️ Properties</div>
                        </div>
                        <div style="text-align: center; padding: 8px; background: var(--dashboard-bg-card); border-radius: 4px;">
                            <div style="font-size: 1.2em; font-weight: 600; color: #ffc107;">${staticMethods.length}</div>
                            <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">📌 Static</div>
                        </div>
                        <div style="text-align: center; padding: 8px; background: var(--dashboard-bg-card); border-radius: 4px;">
                            <div style="font-size: 1.2em; font-weight: 600; color: #dc3545;">${specialMethods.length}</div>
                            <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">🔧 Special</div>
                        </div>
                        <div style="text-align: center; padding: 8px; background: var(--dashboard-bg-card); border-radius: 4px;">
                            <div style="font-size: 1.2em; font-weight: 600; color: #6f42c1;">${asyncMethods.length}</div>
                            <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">🔄 Async</div>
                        </div>
                        <div style="text-align: center; padding: 8px; background: var(--dashboard-bg-card); border-radius: 4px;">
                            <div style="font-size: 1.2em; font-weight: 600; color: #17a2b8;">${classMethods.length}</div>
                            <div style="font-size: 0.8em; color: var(--dashboard-text-muted);">🏛️ Class</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    createClassContentSection(classFunctions) {
        if (classFunctions.length === 0) {
            return `
                <div class="detail-section">
                    <h3>📋 Class Contents</h3>
                    <p style="color: var(--dashboard-text-muted); font-style: italic;">No methods found for this class.</p>
                </div>
            `;
        }

        // Group methods by type
        const methodGroups = {
            'Special Methods': classFunctions.filter(f => f.name.startsWith('__') && f.name.endsWith('__')),
            'Properties': classFunctions.filter(f => f.is_property),
            'Class Methods': classFunctions.filter(f => f.function_type === 'classmethod'),
            'Static Methods': classFunctions.filter(f => f.is_static),
            'Instance Methods': classFunctions.filter(f => 
                !f.name.startsWith('__') && 
                !f.is_property && 
                f.function_type !== 'classmethod' && 
                !f.is_static
            )
        };

        return `
            <div class="detail-section">
                <h3>📋 Class Contents</h3>
                ${Object.entries(methodGroups).map(([groupName, methods]) => {
                    if (methods.length === 0) return '';
                    
                    const groupIcon = {
                        'Special Methods': '🔧',
                        'Properties': '🏷️',
                        'Class Methods': '🏛️',
                        'Static Methods': '📌',
                        'Instance Methods': '⚙️'
                    }[groupName] || '⚙️';
                    
                    return `
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: var(--dashboard-accent-primary); font-size: 1rem; margin-bottom: 10px; border-bottom: 1px solid var(--dashboard-border-light); padding-bottom: 5px;">
                                ${groupIcon} ${groupName} (${methods.length})
                            </h4>
                            <div style="display: grid; gap: 8px;">
                                ${methods.map(func => `
                                    <div class="list-item" onclick="modalManager.showFunctionDetails(${func.id})" style="cursor: pointer; padding: 10px; background: var(--dashboard-bg-card); border-radius: 4px; border-left: 3px solid var(--dashboard-accent-primary);">
                                        <div class="list-item-title" style="display: flex; justify-content: space-between; align-items: center;">
                                            <span>${func.name}(${func.parameters_count || 0} params)</span>
                                            <div style="display: flex; gap: 5px;">
                                                ${func.is_async ? '<span style="background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 3px; font-size: 0.7em;">async</span>' : ''}
                                                ${func.complexity ? `<span style="background: ${this.getComplexityColor(func.complexity)}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.7em;">C:${func.complexity}</span>` : ''}
                                            </div>
                                        </div>
                                        <div class="list-item-meta">
                                            Line ${func.line_number || '?'} • ${func.function_type || 'method'}
                                            ${func.docstring ? ' • Has documentation' : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    createInheritanceSection(cls) {
        let baseClasses = [];
        try {
            baseClasses = Array.isArray(cls.base_classes) ? cls.base_classes : 
                         (typeof cls.base_classes === 'string' ? JSON.parse(cls.base_classes || '[]') : []);
        } catch (e) {
            console.warn('Failed to parse base_classes:', cls.base_classes);
            baseClasses = [];
        }
        
        if (baseClasses.length === 0) return '';
        
        return `
            <div class="detail-section">
                <h3>🔗 Inheritance</h3>
                <div>
                    <strong>Inherits from:</strong> 
                    ${baseClasses.map(base => `<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; margin: 2px;">${base}</code>`).join(' ')}
                </div>
            </div>
        `;
    }

    createMethodsSection(classFunctions) {
        if (classFunctions.length === 0) return '';
        
        return `
            <div class="detail-section">
                <h3>⚙️ Methods (${classFunctions.length})</h3>
                <div style="max-height: 300px; overflow-y: auto;">
                    ${classFunctions.map(func => `
                        <div class="list-item" onclick="modalManager.showFunctionDetails(${func.id})" style="margin-bottom: 8px; cursor: pointer;">
                            <div class="list-item-title">${func.name}</div>
                            <div class="list-item-meta">
                                Line ${func.line_number || 'Unknown'} • 
                                ${func.function_type || 'method'} • 
                                ${func.parameters_count || 0} params
                                ${func.is_async ? ' • async' : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    createFunctionDetailsSection(func) {
        return `
            <div class="detail-section">
                <h3>📊 Function Overview</h3>
                
                <!-- Basic Stats -->
                <div class="stats-row" style="margin-bottom: 15px;">
                    <div class="stat-item">
                        <div class="stat-label">Type</div>
                        <div class="stat-value">${func.function_type || 'function'}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Parameters</div>
                        <div class="stat-value">${func.parameters_count || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Complexity</div>
                        <div class="stat-value" style="color: ${this.getComplexityColor(func.complexity)}">
                            ${func.complexity || 'N/A'}
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Line Count</div>
                        <div class="stat-value">${func.end_line_number && func.line_number ? func.end_line_number - func.line_number + 1 : 'N/A'}</div>
                    </div>
                </div>

                <!-- Function Characteristics -->
                <div style="background: var(--dashboard-bg-tertiary); padding: 15px; border-radius: 6px; border: 1px solid var(--dashboard-border-light);">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 10px;">Characteristics</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        ${func.is_async ? '<span style="background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">🔄 Async</span>' : ''}
                        ${func.is_static ? '<span style="background: #fff3e0; color: #f57c00; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">📌 Static</span>' : ''}
                        ${func.is_property ? '<span style="background: #e8f5e8; color: #2e7d32; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">🏷️ Property</span>' : ''}
                        ${func.function_type === 'classmethod' ? '<span style="background: #f3e5f5; color: #7b1fa2; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">🏛️ Class Method</span>' : ''}
                        ${func.class_id ? '<span style="background: #e1f5fe; color: #0277bd; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">🏗️ Method</span>' : '<span style="background: #fce4ec; color: #c2185b; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">⚙️ Function</span>'}
                        ${func.docstring ? '<span style="background: #e0f2f1; color: #00695c; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">📖 Documented</span>' : ''}
                        ${func.decorators && func.decorators.length > 0 ? '<span style="background: #fff8e1; color: #ef6c00; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">🎯 Decorated</span>' : ''}
                    </div>
                </div>

                <!-- Complexity Breakdown -->
                ${func.complexity ? `
                <div style="background: var(--dashboard-bg-secondary); padding: 15px; border-radius: 6px; margin-top: 15px; border: 1px solid var(--dashboard-border-light);">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 10px;">🎯 Complexity Analysis</h4>
                    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 15px; align-items: center;">
                        <div style="text-align: center;">
                            <div style="font-size: 2rem; font-weight: 700; color: ${this.getComplexityColor(func.complexity)};">${func.complexity}</div>
                            <div style="font-size: 0.9em; color: var(--dashboard-text-muted);">Cyclomatic Complexity</div>
                        </div>
                        <div>
                            <div style="color: var(--dashboard-text-secondary); font-size: 0.9em; line-height: 1.5;">
                                ${this.getComplexityExplanation(func.complexity)}
                            </div>
                            <div style="margin-top: 8px; padding: 8px; background: var(--dashboard-bg-card); border-radius: 4px; font-size: 0.8em;">
                                <strong>💡 Tip:</strong> ${this.getComplexityRecommendation(func.complexity)}
                            </div>
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    // Add complexity explanation helper
    getComplexityExplanation(complexity) {
        if (!complexity) return 'Complexity not calculated';
        if (complexity <= 10) return 'Simple function with straightforward logic flow. Easy to understand and test.';
        if (complexity <= 25) return 'Moderate complexity with some conditional logic. Generally acceptable.';
        if (complexity <= 50) return 'High complexity with multiple decision points. Consider refactoring.';
        return 'Very high complexity with many branching paths. Refactoring strongly recommended.';
    }

    getComplexityRecommendation(complexity) {
        if (!complexity) return 'Enable complexity analysis to get recommendations.';
        if (complexity <= 10) return 'Well-structured function. No action needed.';
        if (complexity <= 25) return 'Consider adding unit tests to cover all paths.';
        if (complexity <= 50) return 'Break down into smaller functions or simplify logic.';
        return 'Immediate refactoring needed. Split into multiple smaller functions.';
    }

    createParametersSection(func) {
        if (!func.parameters || func.parameters.length === 0) return '';
        
        return `
            <div class="detail-section">
                <h3>📝 Parameters</h3>
                <div style="max-height: 200px; overflow-y: auto;">
                    ${func.parameters.map(param => `
                        <div style="background: #f8f9fa; padding: 12px; margin: 8px 0; border-radius: 6px; border-left: 4px solid #007bff;">
                            <div style="font-weight: 600; color: #333;">${param.name}</div>
                            ${param.type ? `<div style="color: #666; font-size: 0.9em;">Type: <code>${param.type}</code></div>` : ''}
                            ${param.default_value ? `<div style="color: #666; font-size: 0.9em;">Default: <code>${param.default_value}</code></div>` : ''}
                            ${param.annotation ? `<div style="color: #666; font-size: 0.9em;">Annotation: <code>${param.annotation}</code></div>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    createReturnTypeSection(func) {
        const returnType = func.return_type || func.return_annotation;
        if (!returnType) return '';
        
        return `
            <div class="detail-section">
                <h3>🔄 Return Type</h3>
                <div style="background: #e8f5e8; padding: 12px; border-radius: 6px; border-left: 4px solid #28a745;">
                    <code style="font-size: 1.1em;">${returnType}</code>
                </div>
            </div>
        `;
    }

    createDecoratorsSection(item) {
        let decorators = [];
        try {
            decorators = Array.isArray(item.decorators) ? item.decorators : 
                        (typeof item.decorators === 'string' ? JSON.parse(item.decorators || '[]') : []);
        } catch (e) {
            console.warn('Failed to parse decorators:', item.decorators);
            decorators = [];
        }
        
        if (decorators.length === 0) return '';
        
        const decoratorColor = item.function_type ? '#fff3cd' : '#e3f2fd';
        
        return `
            <div class="detail-section">
                <h3>🎯 Decorators</h3>
                <div>
                    ${decorators.map(dec => `
                        <code style="background: ${decoratorColor}; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block;">@${dec}</code>
                    `).join('')}
                </div>
            </div>
        `;
    }

    createDocstringSection(func) {
        if (!func.docstring) return '';
        
        return `
            <div class="detail-section">
                <h3>📖 Documentation</h3>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #6c757d;">
                    <pre style="white-space: pre-wrap; margin: 0; font-size: 0.9em; line-height: 1.4;">${func.docstring}</pre>
                </div>
            </div>
        `;
    }

    // Create class methods section
    createClassMethodsSection(classFunctions) {
        if (!classFunctions || classFunctions.length === 0) {
            return `
                <div class="detail-section">
                    <h3>⚙️ Methods (0)</h3>
                    <p style="color: var(--dashboard-text-muted);">No methods found for this class.</p>
                </div>
            `;
        }

        return `
            <div class="detail-section">
                <h3>⚙️ Methods (${classFunctions.length})</h3>
                <div style="max-height: 300px; overflow-y: auto;">
                    ${classFunctions.map(method => `
                        <div class="list-item" onclick="modalManager.showFunctionDetails(${method.id})" style="margin-bottom: 8px; cursor: pointer;">
                            <div class="list-item-title">
                                ${method.name}(${this.formatParameters(method)})
                                ${method.is_async ? '<span style="background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-left: 8px;">async</span>' : ''}
                            </div>
                            <div class="list-item-meta">
                                Line ${method.line_number || 'Unknown'} • 
                                ${method.function_type || 'method'} • 
                                ${method.parameters_count || 0} parameters
                                ${method.is_property ? ' • property' : ''}
                                ${method.is_static ? ' • static' : ''}
                                ${method.is_classmethod ? ' • classmethod' : ''}
                            </div>
                            ${method.docstring ? `
                                <div style="font-size: 0.8em; color: var(--dashboard-text-muted); margin-top: 5px; max-height: 40px; overflow: hidden;">
                                    ${method.docstring.split('\n')[0].substring(0, 100)}${method.docstring.length > 100 ? '...' : ''}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Create class docstring section
    createClassDocstringSection(cls) {
        if (!cls.docstring) return '';
        
        return `
            <div class="detail-section">
                <h3>📖 Class Documentation</h3>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff;">
                    <pre style="white-space: pre-wrap; margin: 0; font-size: 0.9em; line-height: 1.4;">${cls.docstring}</pre>
                </div>
            </div>
        `;
    }

    // Create function details section
    createFunctionDetailsSection(func) {
        return `
            <div class="detail-section">
                <h3>📊 Function Details</h3>
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="stat-label">Type</div>
                        <div class="stat-value">${func.function_type || 'function'}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Parameters</div>
                        <div class="stat-value">${func.parameters_count || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Async</div>
                        <div class="stat-value">${func.is_async ? 'Yes' : 'No'}</div>
                    </div>
                    ${func.is_property ? `
                        <div class="stat-item">
                            <div class="stat-label">Property</div>
                            <div class="stat-value">Yes</div>
                        </div>
                    ` : ''}
                    ${func.is_static ? `
                        <div class="stat-item">
                            <div class="stat-label">Static</div>
                            <div class="stat-value">Yes</div>
                        </div>
                    ` : ''}
                    ${func.is_classmethod ? `
                        <div class="stat-item">
                            <div class="stat-label">Class Method</div>
                            <div class="stat-value">Yes</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // Create parameters section
    createParametersSection(func) {
        let parameters = [];
        try {
            parameters = Array.isArray(func.parameters) ? func.parameters : 
                        (typeof func.parameters === 'string' ? JSON.parse(func.parameters || '[]') : []);
        } catch (e) {
            console.warn('Failed to parse parameters:', func.parameters);
            parameters = [];
        }

        if (parameters.length === 0) {
            return `
                <div class="detail-section">
                    <h3>📝 Parameters (0)</h3>
                    <p style="color: var(--dashboard-text-muted);">This function takes no parameters.</p>
                </div>
            `;
        }

        return `
            <div class="detail-section">
                <h3>📝 Parameters (${parameters.length})</h3>
                <div style="background: var(--dashboard-bg-secondary); padding: 15px; border-radius: 6px;">
                    ${parameters.map((param, index) => `
                        <div style="margin-bottom: 8px; padding: 8px; background: var(--dashboard-bg-card); border-radius: 4px;">
                            <code style="color: #007bff; font-weight: 600;">${param.name || `param_${index + 1}`}</code>
                            ${param.type ? `<span style="color: var(--dashboard-text-muted); margin-left: 8px;">: ${param.type}</span>` : ''}
                            ${param.default_value ? `<span style="color: #28a745; margin-left: 8px;">= ${param.default_value}</span>` : ''}
                            ${param.annotation ? `<div style="font-size: 0.8em; color: var(--dashboard-text-muted); margin-top: 4px;">${param.annotation}</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Create return type section
    createReturnTypeSection(func) {
        if (!func.return_type && !func.return_annotation) return '';

        return `
            <div class="detail-section">
                <h3>↩️ Return Type</h3>
                <div style="background: var(--dashboard-bg-secondary); padding: 10px; border-radius: 6px;">
                    <code style="color: #28a745; font-weight: 600;">
                        ${func.return_type || func.return_annotation || 'Unknown'}
                    </code>
                </div>
            </div>
        `;
    }

    // Create complexity breakdown section
    createComplexityBreakdownSection(file) {
        const complexity = file.complexity || 0;
        
        return `
            <div class="detail-section">
                <h3>📊 Complexity Analysis</h3>
                <div style="background: var(--dashboard-bg-secondary); padding: 15px; border-radius: 6px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span style="font-weight: 600;">Cyclomatic Complexity Score:</span>
                        <span style="background: ${this.getComplexityColor(complexity)}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">
                            ${complexity}
                        </span>
                    </div>
                    <div style="font-size: 0.9em; color: var(--dashboard-text-muted); margin-bottom: 10px;">
                        <strong>What this measures:</strong> Cyclomatic complexity measures the number of linearly independent paths through a program's source code. It indicates how complex the control flow is.
                    </div>
                    <div style="font-size: 0.9em; color: var(--dashboard-text-muted);">
                        <strong>Score breakdown:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                            <li><strong>1-10:</strong> Simple, easy to test and maintain</li>
                            <li><strong>11-25:</strong> Moderate complexity, acceptable</li>
                            <li><strong>26-50:</strong> High complexity, consider refactoring</li>
                            <li><strong>50+:</strong> Very high complexity, refactoring recommended</li>
                        </ul>
                    </div>
                    ${this.getComplexityRecommendation(complexity)}
                </div>
            </div>
        `;
    }
    
    // Get complexity color
    getComplexityColor(complexity) {
        if (complexity <= 10) return '#28a745';
        if (complexity <= 25) return '#ffc107';
        if (complexity <= 50) return '#fd7e14';
        return '#dc3545';
    }
    
    // Get complexity recommendation
    getComplexityRecommendation(complexity) {
        if (complexity <= 10) {
            return '<div style="color: #28a745; font-size: 0.9em; margin-top: 10px;"><strong>✅ Good:</strong> This file has low complexity and should be easy to maintain.</div>';
        } else if (complexity <= 25) {
            return '<div style="color: #ffc107; font-size: 0.9em; margin-top: 10px;"><strong>⚠️ Moderate:</strong> Complexity is acceptable but monitor for increases.</div>';
        } else if (complexity <= 50) {
            return '<div style="color: #fd7e14; font-size: 0.9em; margin-top: 10px;"><strong>🔥 High:</strong> Consider breaking this file into smaller, more focused modules.</div>';
        } else {
            return '<div style="color: #dc3545; font-size: 0.9em; margin-top: 10px;"><strong>🚨 Very High:</strong> This file should be refactored immediately to improve maintainability.</div>';
        }
    }

    // Create nested code structure section
    createNestedCodeStructureSection(fileData) {
        if ((!fileData.classes || fileData.classes.length === 0) && 
            (!fileData.functions || fileData.functions.length === 0)) {
            return '<div class="detail-section"><h3>🏗️ Code Structure</h3><p>No classes or functions found in this file.</p></div>';
        }

        let html = `
            <div class="detail-section">
                <h3>🏗️ Code Structure</h3>
                <div style="font-family: monospace; background: var(--dashboard-bg-secondary); padding: 15px; border-radius: 6px;">
        `;

        // Group functions by class (if they belong to a class)
        const classFunctions = new Map();
        const fileLevelFunctions = [];

        if (fileData.functions) {
            fileData.functions.forEach(func => {
                if (func.class_id) {
                    if (!classFunctions.has(func.class_id)) {
                        classFunctions.set(func.class_id, []);
                    }
                    classFunctions.get(func.class_id).push(func);
                } else {
                    fileLevelFunctions.push(func);
                }
            });
        }

        // Render classes with their methods
        if (fileData.classes && fileData.classes.length > 0) {
            fileData.classes.forEach(cls => {
                const methods = classFunctions.get(cls.id) || [];
                html += `
                    <div style="margin-bottom: 15px; border-left: 3px solid #007bff; padding-left: 10px;">
                        <div style="cursor: pointer; color: #007bff; font-weight: 600; margin-bottom: 5px;" 
                             onclick="modalManager.showClassDetails(${cls.id})">
                            🏗️ class ${cls.name} ${cls.base_classes ? `(${cls.base_classes})` : ''}
                        </div>
                        <div style="margin-left: 20px; color: var(--dashboard-text-muted); font-size: 0.9em;">
                            Line ${cls.line_number || '?'} • ${cls.class_type || 'class'}
                        </div>
                        ${methods.length > 0 ? `
                            <div style="margin-left: 20px; margin-top: 8px;">
                                ${methods.map(method => `
                                    <div style="margin-bottom: 3px; cursor: pointer; color: #28a745;" 
                                         onclick="modalManager.showFunctionDetails(${method.id})">
                                        ⚙️ def ${method.name}(${this.formatParameters(method)})
                                        <span style="color: var(--dashboard-text-muted); font-size: 0.8em; margin-left: 10px;">
                                            Line ${method.line_number || '?'}
                                        </span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            });
        }

        // Render file-level functions
        if (fileLevelFunctions.length > 0) {
            html += `
                <div style="margin-bottom: 15px;">
                    <div style="color: var(--dashboard-text-secondary); font-weight: 600; margin-bottom: 8px;">
                        📄 File-level functions:
                    </div>
                    ${fileLevelFunctions.map(func => `
                        <div style="margin-bottom: 3px; margin-left: 10px; cursor: pointer; color: #28a745;" 
                             onclick="modalManager.showFunctionDetails(${func.id})">
                            ⚙️ def ${func.name}(${this.formatParameters(func)})
                            <span style="color: var(--dashboard-text-muted); font-size: 0.8em; margin-left: 10px;">
                                Line ${func.line_number || '?'}
                            </span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        html += `
                </div>
                <div style="margin-top: 10px; padding: 10px; background: var(--dashboard-bg-tertiary); border-radius: 4px; font-size: 0.9em; color: var(--dashboard-text-muted);">
                    <strong>💡 Legend:</strong>
                    🏗️ Classes (clickable) • ⚙️ Functions/Methods (clickable) • 📄 File-level items
                </div>
            </div>
        `;

        return html;
    }

    // Format function parameters
    formatParameters(func) {
        if (func.parameters_count === 0) return '';
        if (func.parameters_count === 1) return '...';
        return `${func.parameters_count} params`;
    }

    // Show system status modal
    async showSystemStatus() {
        try {
            const response = await fetch('/api/stats');
            const result = await response.json();
            
            if (!result.success) {
                window.dashboard.showError('Failed to load system status');
                return;
            }
            
            const stats = result.data;
            const modalHtml = `
                <div class="modal-overlay" onclick="modalManager.closeModal(this)">
                    <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 600px;">
                        <div class="modal-header">
                            <h2>🖥️ System Status</h2>
                            <button class="modal-close-btn" onclick="modalManager.closeModal(this.closest('.modal-overlay'))" 
                                    style="background: none; border: none; font-size: 1.5em; cursor: pointer; color: #666;">
                                ✕
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="detail-section">
                                <h3>📊 Database Statistics</h3>
                                <div class="stats-row">
                                    <div class="stat-item">
                                        <div class="stat-label">Total Files</div>
                                        <div class="stat-value">${stats.total_files || 0}</div>
                                    </div>
                                    <div class="stat-item">
                                        <div class="stat-label">Total Classes</div>
                                        <div class="stat-value">${stats.total_classes || 0}</div>
                                    </div>
                                    <div class="stat-item">
                                        <div class="stat-label">Total Functions</div>
                                        <div class="stat-value">${stats.total_functions || 0}</div>
                                    </div>
                                    <div class="stat-item">
                                        <div class="stat-label">Avg Complexity</div>
                                        <div class="stat-value">${stats.avg_complexity ? stats.avg_complexity.toFixed(1) : 'N/A'}</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <h3>🏷️ Domain Distribution</h3>
                                <div style="display: grid; gap: 8px;">
                                    ${Object.entries(stats.domain_distribution || {}).map(([domain, count]) => `
                                        <div style="display: flex; justify-content: space-between; padding: 8px; background: var(--dashboard-bg-tertiary); border-radius: 4px;">
                                            <span>${domain}</span>
                                            <span style="font-weight: bold;">${count}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <h3>⚡ Performance Metrics</h3>
                                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px;">
                                    <div style="margin-bottom: 8px;">
                                        <strong>High Complexity Files:</strong> ${stats.high_complexity_files || 0}
                                    </div>
                                    <div style="margin-bottom: 8px;">
                                        <strong>Total Domains:</strong> ${stats.total_domains || 0}
                                    </div>
                                    <div>
                                        <strong>Last Updated:</strong> ${new Date().toLocaleString()}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button class="usa-button usa-button--outline" onclick="modalManager.closeModal(this.closest('.modal-overlay'))">
                                Close
                            </button>
                            <button class="usa-button" onclick="window.location.reload()">
                                Refresh Dashboard
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            this.showModal(modalHtml);
            
        } catch (error) {
            console.error('Error loading system status:', error);
            window.dashboard.showError('Failed to load system status');
        }
    }

    // Show modal
    showModal(modalHtml) {
        // Close any existing modals first
        this.closeAllModals();
        
        // Create modal element
        const modalElement = document.createElement('div');
        modalElement.innerHTML = modalHtml;
        const modal = modalElement.firstElementChild;
        
        // Add modal to body
        document.body.appendChild(modal);
        this.activeModals.add(modal);
        
        // Add modal styles to ensure proper overlay behavior
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.zIndex = '9999';
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        
        // Add keyboard support for closing modal
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') {
                this.closeModal(modal);
                document.removeEventListener('keydown', handleKeyDown);
            }
        };
        document.addEventListener('keydown', handleKeyDown);
        
        // Store the event handler for cleanup
        modal._keydownHandler = handleKeyDown;
    }

    // Close modal
    closeModal(modalElement) {
        if (modalElement && modalElement.classList.contains('modal-overlay')) {
            // Remove keyboard event listener if it exists
            if (modalElement._keydownHandler) {
                document.removeEventListener('keydown', modalElement._keydownHandler);
            }
            this.activeModals.delete(modalElement);
            modalElement.remove();
        }
    }

    // Close all modals
    closeAllModals() {
        this.activeModals.forEach(modal => modal.remove());
        this.activeModals.clear();
    }
}

// Create global modal manager instance
window.modalManager = new ModalManager();

// Global functions for backwards compatibility
window.showFileDetails = (fileId) => window.modalManager.showFileDetails(fileId);
window.showClassDetails = (classId) => window.modalManager.showClassDetails(classId);
window.showFunctionDetails = (functionId) => window.modalManager.showFunctionDetails(functionId);
window.showSystemStatus = () => window.modalManager.showSystemStatus();
