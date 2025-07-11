/**
 * Data Loading Components
 * Handles section-specific data loading for files, classes, and functions
 */

class DataLoader {
    constructor() {
        this.cache = new Map();
        this.loadingStates = new Set();
    }

    // Load data for specific sections
    async loadSectionData(sectionName) {
        try {
            console.log(`🔄 Loading section data for: ${sectionName}`);
            switch(sectionName) {
                case 'files':
                    await this.loadFiles();
                    break;
                case 'classes':
                    await this.loadClasses();
                    break;
                case 'functions':
                    await this.loadFunctions();
                    break;
                case 'services':
                    await this.loadServices();
                    break;
                default:
                    console.log(`❓ No specific loader for section: ${sectionName}`);
            }
            console.debug("✅ Successfully loaded section: ${sectionName}");
        } catch (error) {
            console.error(`❌ Failed to load ${sectionName}:`, error);
            window.dashboard.showError(`Failed to load ${sectionName}: ${error.message}`);
        }
    }

    // Load files data with caching
    async loadFiles() {
        console.log('🔄 Loading files...');
        
        if (this.loadingStates.has('files')) {
            console.log('⏳ Files already loading, skipping...');
            return;
        }

        this.loadingStates.add('files');
        this.showLoadingState('filesList');

        try {
            // Ensure dashboard data structure exists
            if (!window.dashboard) {
                throw new Error('Dashboard not initialized');
            }
            if (!window.dashboard.data) {
                window.dashboard.data = { files: [], classes: [], functions: [], services: [], stats: {} };
            }

            // Check cache first (shorter cache time for debugging)
            if (this.cache.has('files') && this.cache.get('files').timestamp > Date.now() - 10000) {
                console.log('📦 Using cached files data');
                window.dashboard.data.files = this.cache.get('files').data;
                this.renderFilesList();
                return;
            }

            console.log('🌐 Fetching files from API...');
            const response = await fetch('/api/files?limit=5000');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('📊 API Response:', result);
            
            if (result.success && result.data) {
                window.dashboard.data.files = result.data;
                console.log(`✅ Loaded ${result.data.length} files`);
                
                // Cache the data
                this.cache.set('files', {
                    data: result.data,
                    timestamp: Date.now()
                });
                
                this.renderFilesList();
                
                // Show success notification
                if (window.dashboard.showNotification) {
                    window.dashboard.showNotification(`Loaded ${result.data.length} files successfully`, 'success');
                }
            } else {
                throw new Error(result.message || 'Invalid API response');
            }
        } catch (error) {
            console.error('❌ Failed to load files:', error);
            this.showError('filesList', `Failed to load files: ${error.message}`);
            
            // Show error notification
            if (window.dashboard && window.dashboard.showError) {
                window.dashboard.showError(`Failed to load files: ${error.message}`);
            }
        } finally {
            this.loadingStates.delete('files');
        }
    }

    // Load classes data with caching
    async loadClasses() {
        console.log('🔄 Loading classes...');
        
        if (this.loadingStates.has('classes')) {
            console.log('⏳ Classes already loading, skipping...');
            return;
        }

        this.loadingStates.add('classes');
        this.showLoadingState('classesList');

        try {
            // Ensure dashboard data structure exists
            if (!window.dashboard) {
                throw new Error('Dashboard not initialized');
            }
            if (!window.dashboard.data) {
                window.dashboard.data = { files: [], classes: [], functions: [], services: [], stats: {} };
            }

            // Check cache first
            if (this.cache.has('classes') && this.cache.get('classes').timestamp > Date.now() - 10000) {
                console.log('📦 Using cached classes data');
                window.dashboard.data.classes = this.cache.get('classes').data;
                this.renderClassesList();
                return;
            }

            console.log('🌐 Fetching classes from API...');
            const response = await fetch('/api/classes?limit=5000');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('📊 API Response:', result);
            
            if (result.success && result.data) {
                window.dashboard.data.classes = result.data;
                console.log(`✅ Loaded ${result.data.length} classes`);
                
                // Cache the data
                this.cache.set('classes', {
                    data: result.data,
                    timestamp: Date.now()
                });
                
                this.renderClassesList();
                
                // Show success notification
                if (window.dashboard.showNotification) {
                    window.dashboard.showNotification(`Loaded ${result.data.length} classes successfully`, 'success');
                }
            } else {
                throw new Error(result.message || 'Invalid API response');
            }
        } catch (error) {
            console.error('❌ Failed to load classes:', error);
            this.showError('classesList', `Failed to load classes: ${error.message}`);
            
            // Show error notification
            if (window.dashboard && window.dashboard.showError) {
                window.dashboard.showError(`Failed to load classes: ${error.message}`);
            }
        } finally {
            this.loadingStates.delete('classes');
        }
    }

    // Load functions data with caching
    async loadFunctions() {
        if (this.loadingStates.has('functions')) {
            return;
        }

        this.loadingStates.add('functions');
        this.showLoadingState('functionsList');

        try {
            // Check cache first
            if (this.cache.has('functions') && this.cache.get('functions').timestamp > Date.now() - 30000) {
                window.dashboard.data.functions = this.cache.get('functions').data;
                this.renderFunctionsList();
                return;
            }

            const response = await fetch('/api/functions?limit=5000');
            const result = await response.json();
            
            if (result.success) {
                window.dashboard.data.functions = result.data;
                
                // Cache the data
                this.cache.set('functions', {
                    data: result.data,
                    timestamp: Date.now()
                });
                
                this.renderFunctionsList();
            } else {
                this.showError('functionsList', 'Failed to load functions');
            }
        } catch (error) {
            console.error('Failed to load functions:', error);
            this.showError('functionsList', 'Failed to load functions');
        } finally {
            this.loadingStates.delete('functions');
        }
    }

    // Load services data (service classes)
    async loadServices() {
        if (this.loadingStates.has('services')) {
            return;
        }

        this.loadingStates.add('services');
        this.showLoadingState('servicesList');

        try {
            // Check cache first
            if (this.cache.has('services') && this.cache.get('services').timestamp > Date.now() - 30000) {
                window.dashboard.data.services = this.cache.get('services').data;
                this.renderServicesList();
                return;
            }

            // Load service classes using dedicated services endpoint
            const response = await fetch('/api/services?limit=5000');
            const result = await response.json();
            
            if (result.success) {
                window.dashboard.data.services = result.data;
                
                // Cache the data
                this.cache.set('services', {
                    data: result.data,
                    timestamp: Date.now()
                });
                
                this.renderServicesList();
            } else {
                this.showError('servicesList', 'Failed to load services');
            }
        } catch (error) {
            console.error('Failed to load services:', error);
            this.showError('servicesList', 'Failed to load services');
        } finally {
            this.loadingStates.delete('services');
        }
    }

    // Render files list
    renderFilesList() {
        console.log('🔄 Rendering files list...');
        
        const container = document.getElementById('filesList');
        
        if (!container) {
            console.error('❌ Files container not found (filesList)');
            // Try to create the container if it doesn't exist
            const mainContent = document.getElementById('mainContent') || document.querySelector('main');
            if (mainContent) {
                const newContainer = document.createElement('div');
                newContainer.id = 'filesList';
                newContainer.className = 'list-container';
                mainContent.appendChild(newContainer);
                console.log('✅ Created missing filesList container');
                return this.renderFilesList(); // Retry
            }
            return;
        }
        
        // Clear loading state
        container.classList.remove('loading');
        
        const files = (window.dashboard && window.dashboard.data && window.dashboard.data.files) || [];
        console.log(`📁 Rendering ${files.length} files`);
        
        if (files.length === 0) {
            container.innerHTML = `
                <div class="placeholder-text" style="text-align: center; padding: 40px; color: #666;">
                    <h3>📁 No Files Loaded</h3>
                    <p>Click the "📋 All Files" button above to load file data.</p>
                    <button class="usa-button" onclick="window.dashboard && window.dashboard.loadFiles()">
                        📋 Load Files Now
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = files.map(file => `
            <div class="list-item file-item" 
                 data-id="${file.id}" 
                 data-domain="${file.domain || ''}" 
                 data-complexity="${file.complexity || 0}" 
                 data-file-type="${this.getFileType(file.name).toLowerCase()}" 
                 onclick="window.modalManager && window.modalManager.showFileDetails(${file.id})" 
                 style="cursor: pointer; margin-bottom: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 6px; background: white;">
                <div class="list-item-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div class="list-item-title" style="font-weight: bold; font-size: 1.1em;">
                        ${this.getFileTypeIcon(file.name)} ${file.name}
                    </div>
                    <div class="file-type-badge">
                        <span class="usa-tag ${this.getFileTypeClass(file.name)}">
                            ${this.getFileType(file.name)}
                        </span>
                    </div>
                </div>
                <div class="list-item-meta" style="color: #666; font-size: 0.9em; margin-bottom: 8px;">
                    ${file.path || 'Unknown path'}
                </div>
                <div class="list-item-stats" style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <span class="list-item-stat" style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">📍 Lines: ${file.lines || 0}</span>
                    <span class="list-item-stat" style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">🏷️ ${file.domain || 'Unknown'}</span>
                    <span class="list-item-stat" style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">🏗️ Classes: ${file.classes || 0}</span>
                    <span class="list-item-stat" style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">⚙️ Functions: ${file.functions || 0}</span>
                    <span class="list-item-stat complexity-score" style="background: ${this.getComplexityColor(file.complexity || 0)}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">📊 Complexity: ${file.complexity || 0}</span>
                </div>
            </div>
        `).join('');
        
        console.log('✅ Files list rendered successfully');
    }
    
    getComplexityColor(complexity) {
        if (complexity <= 10) return '#28a745';
        if (complexity <= 25) return '#ffc107';
        if (complexity <= 50) return '#fd7e14';
        return '#dc3545';
    }
    
    getFileType(filename) {
        if (!filename) return 'Unknown';
        const ext = filename.split('.').pop().toLowerCase();
        const typeMap = {
            'py': 'Python',
            'js': 'JavaScript', 
            'json': 'JSON',
            'yaml': 'YAML',
            'yml': 'YAML',
            'md': 'Markdown',
            'txt': 'Text'
        };
        return typeMap[ext] || ext.toUpperCase();
    }
    
    getFileTypeIcon(filename) {
        if (!filename) return '📄';
        const ext = filename.split('.').pop().toLowerCase();
        const iconMap = {
            'py': '🐍',
            'js': '📜',
            'json': '📋',
            'yaml': '⚙️',
            'yml': '⚙️',
            'md': '📝',
            'txt': '📄',
            'html': '🌐',
            'css': '🎨',
            'sql': '🗃️'
        };
        return iconMap[ext] || '📄';
    }
    
    getFileTypeClass(filename) {
        if (!filename) return '';
        const ext = filename.split('.').pop().toLowerCase();
        const classMap = {
            'py': 'usa-tag--accent-cool',
            'js': 'usa-tag--accent-warm',
            'json': 'usa-tag--accent-cool',
            'yaml': 'usa-tag--accent-warm',
            'yml': 'usa-tag--accent-warm'
        };
        return classMap[ext] || '';
    }
    
    getComplexityClass(complexity) {
        if (complexity <= 10) return 'complexity-low';
        if (complexity <= 50) return 'complexity-medium';
        return 'complexity-high';
    }

    // Render classes list with enhanced type indicators
    renderClassesList() {
        console.log('🔄 Rendering classes list...');
        
        const container = document.getElementById('classesList');
        
        if (!container) {
            console.error('❌ Classes container not found (classesList)');
            // Try to create the container if it doesn't exist
            const mainContent = document.getElementById('mainContent') || document.querySelector('main');
            if (mainContent) {
                const newContainer = document.createElement('div');
                newContainer.id = 'classesList';
                newContainer.className = 'list-container';
                mainContent.appendChild(newContainer);
                console.log('✅ Created missing classesList container');
                return this.renderClassesList(); // Retry
            }
            return;
        }
        
        // Clear loading state
        container.classList.remove('loading');
        
        const classes = (window.dashboard && window.dashboard.data && window.dashboard.data.classes) || [];
        console.log(`🏗️ Rendering ${classes.length} classes`);
        
        if (classes.length === 0) {
            container.innerHTML = `
                <div class="placeholder-text" style="text-align: center; padding: 40px; color: #666;">
                    <h3>🏗️ No Classes Loaded</h3>
                    <p>Click the "📋 All Classes" button above to load class data.</p>
                    <button class="usa-button" onclick="window.dashboard && window.dashboard.loadClasses()">
                        🏗️ Load Classes Now
                    </button>
                </div>
            `;
            return;
        }
        
        // Update class type statistics
        this.updateClassTypeStats(classes);
        
        container.innerHTML = classes.map(cls => `
            <div class="list-item class-item" 
                 onclick="window.modalManager && window.modalManager.showClassDetails(${cls.id})" 
                 data-id="${cls.id}" 
                 data-class-type="${cls.class_type || 'class'}" 
                 data-domain="${cls.domain || ''}" 
                 data-methods="${cls.methods_count || 0}"
                 style="cursor: pointer; margin-bottom: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 6px; background: white;">
                <div class="list-item-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div class="list-item-title" style="font-weight: bold; font-size: 1.1em;">
                        ${this.getClassTypeIcon(cls.class_type)} ${cls.name}
                    </div>
                    <div class="class-type-badge">
                        <span class="usa-tag ${this.getClassTypeClass(cls.class_type)}">
                            ${this.getClassTypeLabel(cls.class_type)}
                        </span>
                    </div>
                </div>
                <div class="list-item-meta" style="color: #666; font-size: 0.9em; margin-bottom: 8px;">
                    ${cls.file_path || 'Unknown file'}
                </div>
                <div class="list-item-stats" style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <span class="list-item-stat" style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">📍 Line: ${cls.line_number || 'Unknown'}</span>
                    <span class="list-item-stat" style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">🏷️ ${cls.domain || 'Unknown'}</span>
                    <span class="list-item-stat" style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">⚙️ Methods: ${cls.methods_count || 0}</span>
                    ${cls.base_classes ? `<span class="list-item-stat" style="background: #e3f2fd; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">🔗 Extends: ${cls.base_classes}</span>` : ''}
                    <span class="list-item-stat" style="background: ${this.getComplexityColor(cls.complexity_score || 0)}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">📊 Complexity: ${cls.complexity_score || 0}</span>
                </div>
            </div>
        `).join('');
        
        console.log('✅ Classes list rendered successfully');
    }
    
    getClassTypeIcon(classType) {
        const iconMap = {
            'pydantic': '🏷️',
            'abstract': '🔧', 
            'enum': '🎯',
            'dataclass': '📋',
            'exception': '⚠️',
            'class': '📦'
        };
        return iconMap[classType] || '📦';
    }
    
    getClassTypeLabel(classType) {
        const labelMap = {
            'pydantic': 'Pydantic Model',
            'abstract': 'Abstract Class',
            'enum': 'Enum',
            'dataclass': 'Dataclass', 
            'exception': 'Exception',
            'class': 'Class'
        };
        return labelMap[classType] || 'Class';
    }
    
    getClassTypeClass(classType) {
        const classMap = {
            'pydantic': 'usa-tag--accent-cool',
            'abstract': 'usa-tag--accent-warm',
            'enum': 'usa-tag--accent-cool',
            'dataclass': 'usa-tag--big',
            'exception': 'usa-tag--accent-warm',
            'class': ''
        };
        return classMap[classType] || '';
    }
    
    updateClassTypeStats(classes) {
        const stats = {
            pydantic: 0,
            abstract: 0,
            enum: 0,
            dataclass: 0
        };
        
        classes.forEach(cls => {
            const type = cls.class_type;
            if (type === 'pydantic' || (cls.file_path && (cls.file_path.includes('models') || cls.file_path.includes('dtos')))) {
                stats.pydantic++;
            } else if (type === 'abstract') {
                stats.abstract++;
            } else if (type === 'enum') {
                stats.enum++;
            } else if (type === 'dataclass') {
                stats.dataclass++;
            }
        });
        
        // Update the stats in the UI
        document.getElementById('pydanticCount').textContent = stats.pydantic;
        document.getElementById('abstractCount').textContent = stats.abstract;
        document.getElementById('enumCount').textContent = stats.enum;
        document.getElementById('dataclassCount').textContent = stats.dataclass;
    }

    // Render functions list
    renderFunctionsList() {
        const container = document.getElementById('functionsList');
        
        // Clear loading state
        container.classList.remove('loading');
        
        if (!window.dashboard.data.functions || window.dashboard.data.functions.length === 0) {
            container.innerHTML = '<div class="placeholder-text">No functions found</div>';
            return;
        }
        
        container.innerHTML = window.dashboard.data.functions.map(func => `
            <div class="list-item function-item" onclick="modalManager.showFunctionDetails(${func.id})" data-id="${func.id}" data-is-async="${func.is_async == 1}" data-function-type="${func.function_type || 'function'}" data-params="${func.parameters_count || 0}">
                <div class="list-item-header">
                    <div class="list-item-title">
                        ${func.is_async == 1 ? '⚡' : '⚙️'} ${func.name}
                    </div>
                    <div class="function-type-badge">
                        <span class="usa-tag ${func.is_async == 1 ? 'usa-tag--accent-warm' : ''}">
                            ${func.is_async == 1 ? 'Async' : 'Sync'}
                        </span>
                    </div>
                </div>
                <div class="list-item-meta">${func.file_path || 'Unknown file'}</div>
                <div class="list-item-stats">
                    <span class="list-item-stat">📝 Type: ${func.function_type || 'function'}</span>
                    <span class="list-item-stat">📍 Line: ${func.line_number || 'Unknown'}</span>
                    <span class="list-item-stat param-count">📊 Params: ${func.parameters_count || 0}</span>
                    ${func.class_id ? '<span class="list-item-stat">🏗️ Method</span>' : '<span class="list-item-stat">🔧 Function</span>'}
                </div>
            </div>
        `).join('');
    }

    // Render services list
    renderServicesList() {
        const container = document.getElementById('servicesList');
        
        // Clear loading state
        container.classList.remove('loading');
        
        if (!window.dashboard.data.services || window.dashboard.data.services.length === 0) {
            container.innerHTML = '<div class="placeholder-text">No services found</div>';
            return;
        }
        
        // Update service type statistics
        this.updateServiceTypeStats(window.dashboard.data.services);
        
        container.innerHTML = window.dashboard.data.services.map(service => `
            <div class="list-item service-item" onclick="modalManager.showClassDetails(${service.id})" data-service-type="${this.getServiceType(service.name)}">
                <div class="list-item-header">
                    <div class="list-item-title">
                        ${this.getServiceTypeIcon(service.name)} ${service.name}
                    </div>
                    <div class="service-type-badge">
                        <span class="usa-tag ${this.getServiceTypeClass(service.name)}">
                            ${this.getServiceType(service.name)}
                        </span>
                    </div>
                </div>
                <div class="list-item-meta">${service.file_path || 'Unknown file'}</div>
                <div class="list-item-stats">
                    <span class="list-item-stat">📍 Line: ${service.line_number || 'Unknown'}</span>
                    <span class="list-item-stat">🏷️ ${service.domain || 'Unknown'}</span>
                    <span class="list-item-stat">📊 Methods: ${service.methods_count || 0}</span>
                    <span class="list-item-stat">🔧 Complexity: ${service.complexity_score || 0}</span>
                </div>
            </div>
        `).join('');
    }
    
    getServiceType(serviceName) {
        if (serviceName.includes('Service')) return 'Service';
        if (serviceName.includes('Interface')) return 'Interface';
        if (serviceName.includes('Validator')) return 'Validator';
        if (serviceName.includes('Factory')) return 'Factory';
        if (serviceName.includes('Manager')) return 'Manager';
        if (serviceName.includes('Handler')) return 'Handler';
        if (serviceName.includes('Provider')) return 'Provider';
        return 'Service';
    }
    
    getServiceTypeIcon(serviceName) {
        const type = this.getServiceType(serviceName);
        const iconMap = {
            'Service': '⚙️',
            'Interface': '🔌',
            'Validator': '✅',
            'Factory': '🏭',
            'Manager': '👔',
            'Handler': '🎯',
            'Provider': '📦'
        };
        return iconMap[type] || '⚙️';
    }
    
    getServiceTypeClass(serviceName) {
        const type = this.getServiceType(serviceName);
        const classMap = {
            'Service': 'usa-tag--accent-cool',
            'Interface': 'usa-tag--accent-warm',
            'Validator': 'usa-tag--big',
            'Factory': 'usa-tag--accent-cool',
            'Manager': '',
            'Handler': 'usa-tag--accent-warm',
            'Provider': 'usa-tag--big'
        };
        return classMap[type] || '';
    }
    
    updateServiceTypeStats(services) {
        const stats = {
            service: 0,
            interface: 0,
            validator: 0,
            factory: 0
        };
        
        services.forEach(service => {
            const type = this.getServiceType(service.name).toLowerCase();
            if (type === 'service') stats.service++;
            else if (type === 'interface') stats.interface++;
            else if (type === 'validator') stats.validator++;
            else if (type === 'factory') stats.factory++;
        });
        
        // Update the stats in the UI
        const serviceCountEl = document.getElementById('serviceCount');
        const interfaceCountEl = document.getElementById('interfaceCount');
        const validatorCountEl = document.getElementById('validatorCount');
        const factoryCountEl = document.getElementById('factoryCount');
        
        if (serviceCountEl) serviceCountEl.textContent = stats.service;
        if (interfaceCountEl) interfaceCountEl.textContent = stats.interface;
        if (validatorCountEl) validatorCountEl.textContent = stats.validator;
        if (factoryCountEl) factoryCountEl.textContent = stats.factory;
    }

    // Show loading state
    showLoadingState(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    Loading data...
                </div>
            `;
        }
    }

    // Show error state
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="placeholder-text">
                    ❌ ${message}
                    <br><br>
                    <button class="button" onclick="dataLoader.loadSectionData('${containerId.replace('List', '')}')">
                        Try Again
                    </button>
                </div>
            `;
        }
    }

    // Clear cache
    clearCache() {
        this.cache.clear();
    }

    // Get cache statistics
    getCacheStats() {
        const stats = {};
        this.cache.forEach((value, key) => {
            stats[key] = {
                items: value.data.length,
                age: Date.now() - value.timestamp,
                size: JSON.stringify(value.data).length
            };
        });
        return stats;
    }
}

// Create global data loader instance
window.dataLoader = new DataLoader();

// Global function for loading section data
window.loadSectionData = (sectionName) => window.dataLoader.loadSectionData(sectionName);

// Global functions for filtering
window.showClassesByType = function(classType) {
    // Update button states
    document.querySelectorAll('[id^="classFilter-"]').forEach(btn => {
        btn.classList.remove('usa-button');
        btn.classList.add('usa-button', 'usa-button--outline');
    });
    document.getElementById(`classFilter-${classType}`).classList.remove('usa-button--outline');
    document.getElementById(`classFilter-${classType}`).classList.add('usa-button');
    
    // Filter classes
    const allClasses = document.querySelectorAll('.class-item');
    allClasses.forEach(item => {
        if (classType === 'all') {
            item.style.display = 'block';
        } else {
            const itemType = item.getAttribute('data-class-type');
            item.style.display = (itemType === classType) ? 'block' : 'none';
        }
    });
};

window.filterFiles = function() {
    const typeFilter = document.getElementById('fileTypeFilter').value;
    const domainFilter = document.getElementById('domainFilter').value;
    const complexityFilter = document.getElementById('complexityFilter').value;
    
    // Re-render files with filters applied
    if (window.dashboard.data.files) {
        let filteredFiles = window.dashboard.data.files;
        
        if (typeFilter) {
            filteredFiles = filteredFiles.filter(file => {
                const fileType = window.dataLoader.getFileType(file.name).toLowerCase();
                return fileType.includes(typeFilter.toLowerCase());
            });
        }
        
        if (domainFilter) {
            filteredFiles = filteredFiles.filter(file => 
                (file.domain || '').toLowerCase().includes(domainFilter.toLowerCase())
            );
        }
        
        if (complexityFilter) {
            filteredFiles = filteredFiles.filter(file => {
                const complexity = file.complexity_score || 0;
                switch(complexityFilter) {
                    case 'low': return complexity <= 10;
                    case 'medium': return complexity > 10 && complexity <= 50;
                    case 'high': return complexity > 50;
                    default: return true;
                }
            });
        }
        
        // Temporarily store filtered data and re-render
        const originalFiles = window.dashboard.data.files;
        window.dashboard.data.files = filteredFiles;
        window.dataLoader.renderFilesList();
        window.dashboard.data.files = originalFiles; // Restore original data
    }
};

window.showServicesByType = function(serviceType) {
    // Update button states
    document.querySelectorAll('[id^="serviceFilter-"]').forEach(btn => {
        btn.classList.remove('usa-button');
        btn.classList.add('usa-button', 'usa-button--outline');
    });
    document.getElementById(`serviceFilter-${serviceType}`).classList.remove('usa-button--outline');
    document.getElementById(`serviceFilter-${serviceType}`).classList.add('usa-button');
    
    // Filter services
    const allServices = document.querySelectorAll('.service-item');
    allServices.forEach(item => {
        if (serviceType === 'all') {
            item.style.display = 'block';
        } else {
            const itemType = item.getAttribute('data-service-type').toLowerCase();
            item.style.display = (itemType === serviceType) ? 'block' : 'none';
        }
    });
};
