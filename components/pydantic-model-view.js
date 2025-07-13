/**
 * Pydantic Model Visualization Component
 * 
 * This module provides functionality to render and display Pydantic models
 * with their fields, inheritance relationships, validators, and configurations
 * in an interactive and user-friendly format.
 * 
 * @author Code Intelligence Dashboard
 * @version 1.0.0
 */

class PydanticModelView {
    constructor() {
        this.containerId = 'pydanticModelList';
        this.modelFilter = null;
        this.sortBy = 'name';
        this.sortOrder = 'asc';
    }

    /**
     * Render a list of Pydantic models with comprehensive details
     * @param {Array} classes - Array of class objects from the API
     * @param {Object} options - Rendering options
     */
    renderPydanticModels(classes, options = {}) {
        if (!classes || !Array.isArray(classes)) {
            this.renderError('Invalid classes data provided');
            return;
        }

        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container element #${this.containerId} not found`);
            return;
        }

        try {
            // Filter and process Pydantic models
            const pydanticModels = this.filterPydanticModels(classes);
            
            if (pydanticModels.length === 0) {
                this.renderEmptyState();
                return;
            }

            // Sort models
            const sortedModels = this.sortModels(pydanticModels);

            // Generate HTML
            const html = this.generateModelListHtml(sortedModels, options);
            container.innerHTML = html;

            // Add interactive functionality
            this.attachEventListeners();

            console.log(`Rendered ${pydanticModels.length} Pydantic models`);

        } catch (error) {
            console.error('Error rendering Pydantic models:', error);
            this.renderError(error.message);
        }
    }

    /**
     * Filter classes to only include Pydantic models
     * @param {Array} classes - All classes
     * @returns {Array} Filtered Pydantic models
     */
    filterPydanticModels(classes) {
        return classes.filter(cls => 
            cls.class_type === 'pydantic_model' || 
            cls.is_pydantic_model ||
            (cls.base_classes && cls.base_classes.includes('BaseModel'))
        );
    }

    /**
     * Sort models based on current sort criteria
     * @param {Array} models - Pydantic models to sort
     * @returns {Array} Sorted models
     */
    sortModels(models) {
        return models.sort((a, b) => {
            let aVal = a[this.sortBy] || '';
            let bVal = b[this.sortBy] || '';
            
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (this.sortOrder === 'asc') {
                return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
            } else {
                return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
            }
        });
    }

    /**
     * Generate HTML for the model list
     * @param {Array} models - Sorted Pydantic models
     * @param {Object} options - Rendering options
     * @returns {string} Generated HTML
     */
    generateModelListHtml(models, options) {
        const showLineNumbers = options.showLineNumbers !== false;
        const showValidators = options.showValidators !== false;
        const showConfig = options.showConfig !== false;

        let html = `
            <div class="pydantic-models-header">
                <h2>🧬 Pydantic Models (${models.length})</h2>
                <div class="model-controls">
                    <select id="model-sort" class="form-control">
                        <option value="name">Sort by Name</option>
                        <option value="file_path">Sort by File</option>
                        <option value="line_number">Sort by Line Number</option>
                    </select>
                    <button id="sort-order" class="btn btn-sm">${this.sortOrder === 'asc' ? '↑' : '↓'}</button>
                </div>
            </div>
            <div class="pydantic-models-list">
        `;

        models.forEach((model, index) => {
            html += this.generateModelHtml(model, index, { showLineNumbers, showValidators, showConfig });
        });

        html += '</div>';
        return html;
    }

    /**
     * Generate HTML for a single Pydantic model
     * @param {Object} model - Model data
     * @param {number} index - Model index
     * @param {Object} options - Display options
     * @returns {string} Model HTML
     */
    generateModelHtml(model, index, options) {
        const baseClasses = this.formatBaseClasses(model.base_classes || []);
        const fields = this.formatFields(model.fields || []);
        const validators = this.formatValidators(model.validators || []);
        const config = this.formatConfig(model.config);

        return `
            <div class="pydantic-model" data-model-id="${model.id || index}">
                <div class="model-header">
                    <h3 class="model-name">${this.escapeHtml(model.name)}</h3>
                    <div class="model-badges">
                        <span class="badge badge-primary">Pydantic</span>
                        ${model.is_abstract ? '<span class="badge badge-warning">Abstract</span>' : ''}
                    </div>
                </div>
                
                <div class="model-metadata">
                    <p><strong>📁 File:</strong> 
                        <code>${this.escapeHtml(model.file_path)}</code>
                        ${options.showLineNumbers && model.line_number ? ` @ Line ${model.line_number}` : ''}
                    </p>
                    ${baseClasses ? `<p><strong>🏗️ Inheritance:</strong> ${baseClasses}</p>` : ''}
                    ${model.docstring ? `<p><strong>📖 Description:</strong> ${this.escapeHtml(model.docstring)}</p>` : ''}
                </div>

                ${fields ? `
                    <div class="model-fields">
                        <h4>🏷️ Fields</h4>
                        ${fields}
                    </div>
                ` : ''}

                ${options.showValidators && validators ? `
                    <div class="model-validators">
                        <h4>✅ Validators</h4>
                        ${validators}
                    </div>
                ` : ''}

                ${options.showConfig && config ? `
                    <div class="model-config">
                        <h4>⚙️ Configuration</h4>
                        ${config}
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Format base classes list
     * @param {Array} baseClasses - Array of base class names
     * @returns {string} Formatted HTML
     */
    formatBaseClasses(baseClasses) {
        if (!baseClasses || baseClasses.length === 0) return '';
        
        return baseClasses
            .map(cls => `<code class="base-class">${this.escapeHtml(cls)}</code>`)
            .join(' → ');
    }

    /**
     * Format model fields
     * @param {Array} fields - Array of field objects
     * @returns {string} Formatted HTML
     */
    formatFields(fields) {
        if (!fields || fields.length === 0) return '<p class="no-fields">No fields defined</p>';

        const fieldHtml = fields.map(field => {
            const type = field.type || 'unknown';
            const defaultVal = field.default ? ` = ${field.default}` : '';
            const required = field.required ? '<span class="field-required">*</span>' : '';
            const description = field.description ? `<small>${this.escapeHtml(field.description)}</small>` : '';
            
            return `
                <li class="field-item">
                    <code class="field-name">${this.escapeHtml(field.name)}${required}</code>: 
                    <code class="field-type">${this.escapeHtml(type)}</code>
                    <code class="field-default">${this.escapeHtml(defaultVal)}</code>
                    ${description ? `<br>${description}` : ''}
                </li>
            `;
        }).join('');

        return `<ul class="fields-list">${fieldHtml}</ul>`;
    }

    /**
     * Format validators
     * @param {Array} validators - Array of validator strings
     * @returns {string} Formatted HTML
     */
    formatValidators(validators) {
        if (!validators || validators.length === 0) return '<p class="no-validators">No validators defined</p>';

        const validatorHtml = validators
            .map(validator => `<li><code>${this.escapeHtml(validator)}</code></li>`)
            .join('');

        return `<ul class="validators-list">${validatorHtml}</ul>`;
    }

    /**
     * Format configuration
     * @param {string|Object} config - Configuration data
     * @returns {string} Formatted HTML
     */
    formatConfig(config) {
        if (!config) return '';

        const configStr = typeof config === 'object' ? JSON.stringify(config, null, 2) : config;
        return `<pre class="config-code"><code>${this.escapeHtml(configStr)}</code></pre>`;
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Render error state
     * @param {string} message - Error message
     */
    renderError(message) {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <h3>❌ Error</h3>
                    <p>Failed to render Pydantic models: ${this.escapeHtml(message)}</p>
                </div>
            `;
        }
    }

    /**
     * Render empty state
     */
    renderEmptyState() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>📝 No Pydantic Models Found</h3>
                    <p>No Pydantic models were found in the analyzed codebase.</p>
                </div>
            `;
        }
    }

    /**
     * Attach event listeners for interactive functionality
     */
    attachEventListeners() {
        const sortSelect = document.getElementById('model-sort');
        const sortOrderBtn = document.getElementById('sort-order');

        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortBy = e.target.value;
                // Re-render would be called here with current data
            });
        }

        if (sortOrderBtn) {
            sortOrderBtn.addEventListener('click', () => {
                this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
                // Re-render would be called here with current data
            });
        }
    }
}

// Legacy function for backward compatibility
function renderPydanticModels(classes, options) {
    const viewer = new PydanticModelView();
    viewer.renderPydanticModels(classes, options);
}

// Initialize global instance
window.pydanticModelView = new PydanticModelView();