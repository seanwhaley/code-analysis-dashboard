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
            console.log(`✅ Successfully loaded section: ${sectionName}`);
        } catch (error) {
            console.error(`❌ Failed to load ${sectionName}:`, error);
            window.dashboard.showError(`Failed to load ${sectionName}: ${error.message}`);
        }
    }

    // Load files data with caching
    async loadFiles() {
        if (this.loadingStates.has('files')) {
            return;
        }

        this.loadingStates.add('files');
        this.showLoadingState('filesList');

        try {
            // Check cache first
            if (this.cache.has('files') && this.cache.get('files').timestamp > Date.now() - 30000) {
                window.dashboard.data.files = this.cache.get('files').data;
                this.renderFilesList();
                return;
            }

            const response = await fetch('/api/files?limit=5000');
            const result = await response.json();
            
            if (result.success) {
                window.dashboard.data.files = result.data;
                
                // Cache the data
                this.cache.set('files', {
                    data: result.data,
                    timestamp: Date.now()
                });
                
                this.renderFilesList();
            } else {
                this.showError('filesList', 'Failed to load files');
            }
        } catch (error) {
            console.error('Failed to load files:', error);
            this.showError('filesList', 'Failed to load files');
        } finally {
            this.loadingStates.delete('files');
        }
    }

    // Load classes data with caching
    async loadClasses() {
        if (this.loadingStates.has('classes')) {
            return;
        }

        this.loadingStates.add('classes');
        this.showLoadingState('classesList');

        try {
            // Check cache first
            if (this.cache.has('classes') && this.cache.get('classes').timestamp > Date.now() - 30000) {
                window.dashboard.data.classes = this.cache.get('classes').data;
                this.renderClassesList();
                return;
            }

            const response = await fetch('/api/classes?limit=5000');
            const result = await response.json();
            
            if (result.success) {
                window.dashboard.data.classes = result.data;
                
                // Cache the data
                this.cache.set('classes', {
                    data: result.data,
                    timestamp: Date.now()
                });
                
                this.renderClassesList();
            } else {
                this.showError('classesList', 'Failed to load classes');
            }
        } catch (error) {
            console.error('Failed to load classes:', error);
            this.showError('classesList', 'Failed to load classes');
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
        const tableBody = document.getElementById('filesTableBody');
        
        if (!tableBody) {
            console.error('Files table body not found');
            return;
        }
        
        if (!window.dashboard.data.files || window.dashboard.data.files.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="placeholder-text">No files found</td></tr>';
            return;
        }
        
        tableBody.innerHTML = window.dashboard.data.files.map(file => `
            <tr onclick="modalManager.showFileDetails(${file.id})" style="cursor: pointer;">
                <td><strong>${file.name}</strong></td>
                <td><code>${file.path || 'Unknown'}</code></td>
                <td>
                    <span class="usa-tag ${this.getFileTypeClass(file.name)}">
                        ${this.getFileType(file.name)}
                    </span>
                </td>
                <td>
                    <span class="usa-tag usa-tag--big">
                        ${file.domain || 'Unknown'}
                    </span>
                </td>
                <td>
                    <span class="complexity-badge ${this.getComplexityClass(file.complexity || 0)}">
                        ${file.complexity || 0}
                    </span>
                </td>
                <td>
                    <button class="usa-button usa-button--unstyled" onclick="event.stopPropagation(); modalManager.showFileDetails(${file.id})">
                        View Details
                    </button>
                </td>
            </tr>
        `).join('');
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
        const container = document.getElementById('classesList');
        
        // Clear loading state
        container.classList.remove('loading');
        
        if (!window.dashboard.data.classes || window.dashboard.data.classes.length === 0) {
            container.innerHTML = '<div class="placeholder-text">No classes found</div>';
            return;
        }
        
        // Update class type statistics
        this.updateClassTypeStats(window.dashboard.data.classes);
        
        container.innerHTML = window.dashboard.data.classes.map(cls => `
            <div class="list-item class-item" onclick="modalManager.showClassDetails(${cls.id})" data-class-type="${cls.class_type || 'class'}">
                <div class="list-item-header">
                    <div class="list-item-title">
                        ${this.getClassTypeIcon(cls.class_type)} ${cls.name}
                    </div>
                    <div class="class-type-badge">
                        <span class="usa-tag ${this.getClassTypeClass(cls.class_type)}">
                            ${this.getClassTypeLabel(cls.class_type)}
                        </span>
                    </div>
                </div>
                <div class="list-item-meta">${cls.file_path || 'Unknown file'}</div>
                <div class="list-item-stats">
                    <span class="list-item-stat">📍 Line: ${cls.line_number || 'Unknown'}</span>
                    <span class="list-item-stat">🏷️ ${cls.domain || 'Unknown'}</span>
                    ${cls.base_classes ? `<span class="list-item-stat">🔗 Extends: ${cls.base_classes}</span>` : ''}
                    <span class="list-item-stat">📊 Complexity: ${cls.complexity_score || 0}</span>
                </div>
            </div>
        `).join('');
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
            <div class="list-item" onclick="modalManager.showFunctionDetails(${func.id})">
                <div class="list-item-title">${func.name}</div>
                <div class="list-item-meta">${func.file_path || 'Unknown file'}</div>
                <div class="list-item-stats">
                    <span class="list-item-stat">📝 Type: ${func.function_type || 'function'}</span>
                    <span class="list-item-stat">📍 Line: ${func.line_number || 'Unknown'}</span>
                    ${func.is_async == 1 ? '<span class="list-item-stat">🔄 Async</span>' : ''}
                    <span class="list-item-stat">📊 Params: ${func.parameters_count || 0}</span>
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
