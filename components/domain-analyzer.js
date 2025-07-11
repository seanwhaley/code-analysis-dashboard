/**
 * Domain Analysis Component
 * Handles domain analysis and cross-domain dependency visualization
 */

class DomainAnalyzer {
    constructor() {
        this.cache = new Map();
        this.domainData = null;
        this.filesData = null;
    }

    // Show domain overview
    async showDomainOverview() {
        try {
            await this.loadDomainData();
            
            if (!this.filesData || this.filesData.length === 0) {
                this.showNoDataMessage();
                return;
            }

            const domainStats = this.calculateDomainStats();
            const domainDistribution = this.getDomainDistribution();
            
            let html = `
                <h3 style="margin-bottom: 20px; color: var(--dashboard-text-primary);">📊 Domain Overview</h3>
                
                <!-- Domain Statistics -->
                <div class="grid-row grid-gap stats-grid" style="margin-bottom: 30px;">
                    <div class="tablet:grid-col-4">
                        <div class="usa-summary-box stat-card">
                            <div class="usa-summary-box__body">
                                <h2 class="usa-summary-box__heading stat-number">${domainStats.totalDomains}</h2>
                                <div class="usa-summary-box__text stat-label">Total Domains</div>
                            </div>
                        </div>
                    </div>
                    <div class="tablet:grid-col-4">
                        <div class="usa-summary-box stat-card">
                            <div class="usa-summary-box__body">
                                <h2 class="usa-summary-box__heading stat-number">${domainStats.avgFilesPerDomain.toFixed(1)}</h2>
                                <div class="usa-summary-box__text stat-label">Avg Files/Domain</div>
                            </div>
                        </div>
                    </div>
                    <div class="tablet:grid-col-4">
                        <div class="usa-summary-box stat-card">
                            <div class="usa-summary-box__body">
                                <h2 class="usa-summary-box__heading stat-number">${domainStats.largestDomain.name}</h2>
                                <div class="usa-summary-box__text stat-label">Largest Domain</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Domain Distribution -->
                <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light); margin-bottom: 20px;">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">Domain Distribution</h4>
                    <div style="display: grid; gap: 10px;">
                        ${Object.entries(domainDistribution)
                            .sort(([,a], [,b]) => b.fileCount - a.fileCount)
                            .map(([domain, data]) => `
                                <div style="background: var(--dashboard-bg-card); padding: 15px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid ${this.getDomainColor(domain)};">
                                    <div style="flex: 1;">
                                        <div style="color: var(--dashboard-text-primary); font-weight: 600; margin-bottom: 5px;">${domain}</div>
                                        <div style="color: var(--dashboard-text-muted); font-size: 0.9em;">
                                            Avg Complexity: ${data.avgComplexity.toFixed(1)} | 
                                            Avg Lines: ${data.avgLines.toFixed(0)}
                                        </div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="color: var(--dashboard-text-primary); font-size: 1.2rem; font-weight: 600;">
                                            ${data.fileCount}
                                        </div>
                                        <div style="color: var(--dashboard-text-muted); font-size: 0.8em;">
                                            ${((data.fileCount / this.filesData.length) * 100).toFixed(1)}%
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                    </div>
                </div>
                
                <!-- Domain Health Analysis -->
                <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light);">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">Domain Health Analysis</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                        ${this.getDomainHealthAnalysis(domainDistribution).map(analysis => `
                            <div style="background: var(--dashboard-bg-card); padding: 15px; border-radius: 6px; border-left: 3px solid ${analysis.color};">
                                <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 10px;">
                                    <h5 style="color: var(--dashboard-text-primary); margin: 0;">${analysis.title}</h5>
                                    <span style="background: ${analysis.color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;">
                                        ${analysis.status}
                                    </span>
                                </div>
                                <p style="color: var(--dashboard-text-secondary); font-size: 0.9em; margin: 0;">
                                    ${analysis.description}
                                </p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
            document.getElementById('domainContent').innerHTML = html;
            
        } catch (error) {
            console.error('Error showing domain overview:', error);
            this.showErrorMessage('Failed to load domain overview');
        }
    }

    // Show domain details
    async showDomainDetails() {
        try {
            await this.loadDomainData();
            
            const domainDistribution = this.getDomainDistribution();
            
            let html = `
                <h3 style="margin-bottom: 20px; color: var(--dashboard-text-primary);">🔍 Domain Details</h3>
            `;
            
            Object.entries(domainDistribution)
                .sort(([,a], [,b]) => b.fileCount - a.fileCount)
                .forEach(([domain, data]) => {
                    const domainFiles = this.filesData.filter(file => (file.domain || 'Unknown') === domain);
                    
                    html += `
                        <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light); margin-bottom: 20px; border-left: 4px solid ${this.getDomainColor(domain)};">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <h4 style="color: var(--dashboard-text-primary); margin: 0;">${domain}</h4>
                                <div style="display: flex; gap: 10px;">
                                    <span style="background: var(--dashboard-bg-secondary); padding: 4px 8px; border-radius: 4px; color: var(--dashboard-text-secondary); font-size: 0.8em;">
                                        ${data.fileCount} files
                                    </span>
                                    <span style="background: ${this.getComplexityColor(data.avgComplexity)}; padding: 4px 8px; border-radius: 4px; color: white; font-size: 0.8em;">
                                        ${data.avgComplexity.toFixed(1)} avg complexity
                                    </span>
                                </div>
                            </div>
                            
                            <!-- Domain Statistics -->
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 15px;">
                                <div style="text-align: center; background: var(--dashboard-bg-card); padding: 10px; border-radius: 4px;">
                                    <div style="color: var(--dashboard-text-primary); font-size: 1.1rem; font-weight: 600;">${data.totalLines}</div>
                                    <div style="color: var(--dashboard-text-muted); font-size: 0.8em;">Total Lines</div>
                                </div>
                                <div style="text-align: center; background: var(--dashboard-bg-card); padding: 10px; border-radius: 4px;">
                                    <div style="color: var(--dashboard-text-primary); font-size: 1.1rem; font-weight: 600;">${data.totalClasses}</div>
                                    <div style="color: var(--dashboard-text-muted); font-size: 0.8em;">Total Classes</div>
                                </div>
                                <div style="text-align: center; background: var(--dashboard-bg-card); padding: 10px; border-radius: 4px;">
                                    <div style="color: var(--dashboard-text-primary); font-size: 1.1rem; font-weight: 600;">${data.totalFunctions}</div>
                                    <div style="color: var(--dashboard-text-muted); font-size: 0.8em;">Total Functions</div>
                                </div>
                            </div>
                            
                            <!-- Top Files in Domain -->
                            <div>
                                <h5 style="color: var(--dashboard-text-primary); margin-bottom: 10px;">Top Files by Complexity</h5>
                                <div style="max-height: 200px; overflow-y: auto;">
                                    ${domainFiles
                                        .sort((a, b) => (b.complexity || 0) - (a.complexity || 0))
                                        .slice(0, 5)
                                        .map(file => `
                                            <div class="list-item" onclick="modalManager.showFileDetails(${file.id})" style="margin-bottom: 8px; cursor: pointer;">
                                                <div class="list-item-title">${file.name}</div>
                                                <div class="list-item-meta">${file.path}</div>
                                                <div class="list-item-stats">
                                                    <span class="list-item-stat" style="background: ${this.getComplexityColor(file.complexity)}; color: white;">
                                                        📊 ${file.complexity || 0}
                                                    </span>
                                                    <span class="list-item-stat">📏 ${file.lines || 0} lines</span>
                                                    <span class="list-item-stat">🏗️ ${file.classes || 0} classes</span>
                                                    <span class="list-item-stat">⚙️ ${file.functions || 0} functions</span>
                                                </div>
                                            </div>
                                        `).join('')}
                                </div>
                            </div>
                        </div>
                    `;
                });
            
            document.getElementById('domainContent').innerHTML = html;
            
        } catch (error) {
            console.error('Error showing domain details:', error);
            this.showErrorMessage('Failed to load domain details');
        }
    }

    // Show cross-domain dependencies
    async showCrossDomainDependencies() {
        try {
            await this.loadDomainData();
            
            // For now, show a simplified dependency analysis
            // In a real implementation, this would analyze import statements across domains
            const domainDistribution = this.getDomainDistribution();
            const dependencyMatrix = this.buildDependencyMatrix();
            
            let html = `
                <h3 style="margin-bottom: 20px; color: var(--dashboard-text-primary);">🔗 Cross-Domain Dependencies</h3>
                
                <!-- Dependency Overview -->
                <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light); margin-bottom: 20px;">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">Domain Interaction Analysis</h4>
                    <p style="color: var(--dashboard-text-secondary); margin-bottom: 15px;">
                        This analysis shows potential dependencies based on domain structure and file organization.
                        For detailed import analysis, check the Dependencies section.
                    </p>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                        ${Object.entries(domainDistribution).map(([domain, data]) => `
                            <div style="background: var(--dashboard-bg-card); padding: 15px; border-radius: 6px; border-left: 3px solid ${this.getDomainColor(domain)};">
                                <h5 style="color: var(--dashboard-text-primary); margin: 0 0 10px 0;">${domain}</h5>
                                <div style="color: var(--dashboard-text-muted); font-size: 0.9em;">
                                    <div>Files: ${data.fileCount}</div>
                                    <div>Avg Complexity: ${data.avgComplexity.toFixed(1)}</div>
                                    <div>Coupling Risk: ${this.getCouplingRisk(data)}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- Domain Architecture Recommendations -->
                <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light);">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">Architecture Recommendations</h4>
                    <div style="display: grid; gap: 15px;">
                        ${this.getArchitectureRecommendations(domainDistribution).map(rec => `
                            <div style="background: var(--dashboard-bg-card); padding: 15px; border-radius: 6px; border-left: 3px solid ${rec.color};">
                                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                    <span style="font-size: 1.2em; margin-right: 10px;">${rec.icon}</span>
                                    <h5 style="color: var(--dashboard-text-primary); margin: 0;">${rec.title}</h5>
                                </div>
                                <p style="color: var(--dashboard-text-secondary); font-size: 0.9em; margin: 0;">
                                    ${rec.description}
                                </p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
            document.getElementById('domainContent').innerHTML = html;
            
        } catch (error) {
            console.error('Error showing cross-domain dependencies:', error);
            this.showErrorMessage('Failed to load cross-domain dependencies');
        }
    }

    // Load domain data
    async loadDomainData() {
        if (this.filesData) return;
        
        try {
            console.log('🔍 Loading domain data...');
            const response = await fetch('/api/files?limit=5000');
            const result = await response.json();
            
            console.log('📊 Domain API response:', result);
            
            if (result.success && result.data) {
                this.filesData = result.data;
                console.log(`✅ Loaded ${this.filesData.length} files for domain analysis`);
            } else {
                console.error('❌ API response failed:', result);
                throw new Error('Failed to load files data: ' + (result.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('❌ Error loading domain data:', error);
            throw error;
        }
    }

    // Calculate domain statistics
    calculateDomainStats() {
        const domains = {};
        
        this.filesData.forEach(file => {
            const domain = file.domain || 'Unknown';
            if (!domains[domain]) {
                domains[domain] = 0;
            }
            domains[domain]++;
        });
        
        const domainCounts = Object.values(domains);
        const largestDomainEntry = Object.entries(domains).reduce((max, [domain, count]) => 
            count > max.count ? { name: domain, count } : max, { name: '', count: 0 });
        
        return {
            totalDomains: Object.keys(domains).length,
            avgFilesPerDomain: domainCounts.reduce((sum, count) => sum + count, 0) / domainCounts.length,
            largestDomain: largestDomainEntry
        };
    }

    // Get domain distribution
    getDomainDistribution() {
        const distribution = {};
        
        this.filesData.forEach(file => {
            const domain = file.domain || 'Unknown';
            if (!distribution[domain]) {
                distribution[domain] = {
                    fileCount: 0,
                    totalComplexity: 0,
                    totalLines: 0,
                    totalClasses: 0,
                    totalFunctions: 0
                };
            }
            
            const data = distribution[domain];
            data.fileCount++;
            data.totalComplexity += file.complexity || 0;
            data.totalLines += file.lines || 0;
            data.totalClasses += file.classes || 0;
            data.totalFunctions += file.functions || 0;
        });
        
        // Calculate averages
        Object.keys(distribution).forEach(domain => {
            const data = distribution[domain];
            data.avgComplexity = data.totalComplexity / data.fileCount;
            data.avgLines = data.totalLines / data.fileCount;
        });
        
        return distribution;
    }

    // Get domain health analysis
    getDomainHealthAnalysis(distribution) {
        const analyses = [];
        
        // Check for domain balance
        const domainCounts = Object.values(distribution).map(d => d.fileCount);
        const maxFiles = Math.max(...domainCounts);
        const minFiles = Math.min(...domainCounts);
        const ratio = maxFiles / minFiles;
        
        if (ratio > 5) {
            analyses.push({
                title: 'Domain Balance',
                status: 'Needs Attention',
                color: '#ffc107',
                description: 'Some domains are significantly larger than others. Consider splitting large domains or consolidating small ones.'
            });
        } else {
            analyses.push({
                title: 'Domain Balance',
                status: 'Good',
                color: '#28a745',
                description: 'Domains are relatively well-balanced in terms of file count.'
            });
        }
        
        // Check for complexity distribution
        const avgComplexities = Object.values(distribution).map(d => d.avgComplexity);
        const highComplexityDomains = avgComplexities.filter(c => c > 25).length;
        
        if (highComplexityDomains > 0) {
            analyses.push({
                title: 'Complexity Distribution',
                status: 'Monitor',
                color: '#fd7e14',
                description: `${highComplexityDomains} domain(s) have high average complexity. Focus refactoring efforts here.`
            });
        } else {
            analyses.push({
                title: 'Complexity Distribution',
                status: 'Excellent',
                color: '#28a745',
                description: 'All domains maintain reasonable complexity levels.'
            });
        }
        
        return analyses;
    }

    // Build dependency matrix (simplified)
    buildDependencyMatrix() {
        // This is a placeholder for actual dependency analysis
        // In a real implementation, this would analyze import statements
        return {};
    }

    // Get coupling risk
    getCouplingRisk(domainData) {
        if (domainData.avgComplexity > 30) return 'High';
        if (domainData.avgComplexity > 15) return 'Medium';
        return 'Low';
    }

    // Get architecture recommendations
    getArchitectureRecommendations(distribution) {
        const recommendations = [];
        
        // Check for large domains
        const largeDomains = Object.entries(distribution).filter(([, data]) => data.fileCount > 20);
        if (largeDomains.length > 0) {
            recommendations.push({
                icon: '📦',
                title: 'Consider Domain Splitting',
                color: '#17a2b8',
                description: `${largeDomains.length} domain(s) contain many files. Consider splitting them into sub-domains for better organization.`
            });
        }
        
        // Check for high complexity domains
        const highComplexityDomains = Object.entries(distribution).filter(([, data]) => data.avgComplexity > 25);
        if (highComplexityDomains.length > 0) {
            recommendations.push({
                icon: '🔧',
                title: 'Refactoring Priority',
                color: '#dc3545',
                description: `Focus refactoring efforts on ${highComplexityDomains.map(([name]) => name).join(', ')} domain(s) with high complexity.`
            });
        }
        
        // General architecture advice
        recommendations.push({
            icon: '🏗️',
            title: 'Maintain Clean Architecture',
            color: '#28a745',
            description: 'Keep domain boundaries clear and minimize cross-domain dependencies for better maintainability.'
        });
        
        return recommendations;
    }

    // Get domain color
    getDomainColor(domain) {
        const colors = [
            '#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1',
            '#fd7e14', '#20c997', '#6c757d', '#e83e8c', '#17a2b8'
        ];
        
        let hash = 0;
        for (let i = 0; i < domain.length; i++) {
            hash = domain.charCodeAt(i) + ((hash << 5) - hash);
        }
        
        return colors[Math.abs(hash) % colors.length];
    }

    // Get complexity color
    getComplexityColor(complexity) {
        if (complexity <= 10) return '#28a745';
        if (complexity <= 25) return '#ffc107';
        if (complexity <= 50) return '#fd7e14';
        return '#dc3545';
    }

    // Show no data message
    showNoDataMessage() {
        document.getElementById('domainContent').innerHTML = `
            <div style="background: var(--dashboard-bg-tertiary); padding: 30px; border-radius: 8px; text-align: center; color: var(--dashboard-text-muted);">
                <p style="font-size: 1.2rem; margin-bottom: 10px;">🏷️ No Domain Data Available</p>
                <p>No domain information found. This could mean:</p>
                <ul style="text-align: left; display: inline-block; margin-top: 15px;">
                    <li>Files don't have domain classifications</li>
                    <li>Domain analysis needs to be run</li>
                    <li>Data needs to be refreshed</li>
                </ul>
            </div>
        `;
    }

    // Show services by domain
    async showServicesByDomain() {
        try {
            const response = await fetch('/api/services?limit=1000');
            const result = await response.json();
            
            if (!result.success) {
                throw new Error('Failed to load services data');
            }
            
            const services = result.data;
            const servicesByDomain = {};
            
            // Group services by domain
            services.forEach(service => {
                if (!servicesByDomain[service.domain]) {
                    servicesByDomain[service.domain] = [];
                }
                servicesByDomain[service.domain].push(service);
            });
            
            const html = `
                <h3 style="margin-bottom: 20px; color: var(--dashboard-text-primary);">🔧 Services by Domain</h3>
                
                <div class="services-overview" style="margin-bottom: 30px;">
                    <div class="stats-row" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div class="stat-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 2em; color: #007bff;">${services.length}</div>
                            <div style="color: var(--dashboard-text-secondary);">Total Services</div>
                        </div>
                        <div class="stat-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 2em; color: #28a745;">${Object.keys(servicesByDomain).length}</div>
                            <div style="color: var(--dashboard-text-secondary);">Domains</div>
                        </div>
                        <div class="stat-card" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 2em; color: #fd7e14;">${services.reduce((sum, s) => sum + (s.methods_count || 0), 0)}</div>
                            <div style="color: var(--dashboard-text-secondary);">Total Methods</div>
                        </div>
                    </div>
                </div>
                
                <div class="domains-grid" style="display: grid; gap: 20px;">
                    ${Object.entries(servicesByDomain).map(([domain, domainServices]) => `
                        <div class="domain-section" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px; border-left: 4px solid ${this.getDomainColor(domain)};">
                            <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">
                                🏷️ ${domain} Domain (${domainServices.length} services)
                            </h4>
                            <div class="services-grid" style="display: grid; gap: 10px;">
                                ${domainServices.map(service => `
                                    <div class="service-item" onclick="modalManager.showClassDetails(${service.id})" 
                                         style="cursor: pointer; background: var(--dashboard-bg-tertiary); padding: 15px; border-radius: 6px; transition: background-color 0.2s;">
                                        <div class="service-title" style="font-weight: bold; color: var(--dashboard-text-primary); margin-bottom: 5px;">
                                            🔧 ${service.name}
                                        </div>
                                        <div class="service-meta" style="color: var(--dashboard-text-secondary); font-size: 0.9em; margin-bottom: 10px;">
                                            ${service.file_path} • Line ${service.line_number || '?'}
                                        </div>
                                        <div class="service-stats" style="display: flex; gap: 15px; font-size: 0.8em;">
                                            <span style="color: var(--dashboard-text-muted);">Methods: ${service.methods_count || 0}</span>
                                            <span style="color: var(--dashboard-text-muted);">Type: ${service.class_type || 'service'}</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
            const container = document.getElementById('domainContent') || document.getElementById('mainContent');
            if (container) {
                container.innerHTML = html;
            }
            
        } catch (error) {
            console.error('Error showing services by domain:', error);
            this.showErrorMessage(`Failed to load services by domain: ${error.message}`);
        }
    }

    // Show method composition analysis
    async showMethodComposition() {
        try {
            const [functionsResponse, classesResponse] = await Promise.all([
                fetch('/api/functions?limit=1000'),
                fetch('/api/classes?limit=1000')
            ]);
            
            const [functionsResult, classesResult] = await Promise.all([
                functionsResponse.json(),
                classesResponse.json()
            ]);
            
            if (!functionsResult.success || !classesResult.success) {
                throw new Error('Failed to load method composition data');
            }
            
            const functions = functionsResult.data;
            const classes = classesResult.data;
            
            // Analyze method composition
            const methodTypes = {};
            const classMethodCounts = {};
            const parameterDistribution = {};
            
            functions.forEach(func => {
                // Count by function type
                const type = func.function_type || 'function';
                methodTypes[type] = (methodTypes[type] || 0) + 1;
                
                // Count methods per class
                if (func.class_id) {
                    classMethodCounts[func.class_id] = (classMethodCounts[func.class_id] || 0) + 1;
                }
                
                // Parameter distribution
                const paramCount = func.parameters_count || 0;
                const paramRange = paramCount === 0 ? '0' : 
                                 paramCount <= 2 ? '1-2' :
                                 paramCount <= 5 ? '3-5' : '6+';
                parameterDistribution[paramRange] = (parameterDistribution[paramRange] || 0) + 1;
            });
            
            const html = `
                <h3 style="margin-bottom: 20px; color: var(--dashboard-text-primary);">⚙️ Method Composition Analysis</h3>
                
                <div class="composition-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    <div class="stat-section" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px;">
                        <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">📊 Method Types</h4>
                        <div style="display: grid; gap: 8px;">
                            ${Object.entries(methodTypes).map(([type, count]) => `
                                <div style="display: flex; justify-content: space-between; padding: 8px; background: var(--dashboard-bg-tertiary); border-radius: 4px;">
                                    <span style="color: var(--dashboard-text-secondary);">${type}</span>
                                    <span style="font-weight: bold; color: var(--dashboard-text-primary);">${count}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="stat-section" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px;">
                        <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">📈 Parameter Distribution</h4>
                        <div style="display: grid; gap: 8px;">
                            ${Object.entries(parameterDistribution).map(([range, count]) => `
                                <div style="display: flex; justify-content: space-between; padding: 8px; background: var(--dashboard-bg-tertiary); border-radius: 4px;">
                                    <span style="color: var(--dashboard-text-secondary);">${range} params</span>
                                    <span style="font-weight: bold; color: var(--dashboard-text-primary);">${count}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="stat-section" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px;">
                        <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">🏗️ Class Composition</h4>
                        <div style="color: var(--dashboard-text-secondary); margin-bottom: 10px;">
                            Classes with most methods:
                        </div>
                        <div style="display: grid; gap: 8px;">
                            ${Object.entries(classMethodCounts)
                                .sort(([,a], [,b]) => b - a)
                                .slice(0, 5)
                                .map(([classId, count]) => {
                                    const cls = classes.find(c => c.id == classId);
                                    return `
                                        <div style="display: flex; justify-content: space-between; padding: 8px; background: var(--dashboard-bg-tertiary); border-radius: 4px;">
                                            <span style="color: var(--dashboard-text-secondary); cursor: pointer;" onclick="modalManager.showClassDetails(${classId})">
                                                ${cls ? cls.name : `Class ${classId}`}
                                            </span>
                                            <span style="font-weight: bold; color: var(--dashboard-text-primary);">${count}</span>
                                        </div>
                                    `;
                                }).join('')}
                        </div>
                    </div>
                </div>
                
                <div class="method-details" style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 8px;">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">🔍 Method Analysis</h4>
                    <div style="display: grid; gap: 15px;">
                        <div style="display: flex; justify-content: space-between; padding: 15px; background: var(--dashboard-bg-tertiary); border-radius: 6px;">
                            <span style="color: var(--dashboard-text-secondary);">Total Functions/Methods</span>
                            <span style="font-weight: bold; color: var(--dashboard-text-primary);">${functions.length}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 15px; background: var(--dashboard-bg-tertiary); border-radius: 6px;">
                            <span style="color: var(--dashboard-text-secondary);">Async Functions</span>
                            <span style="font-weight: bold; color: var(--dashboard-text-primary);">${functions.filter(f => f.is_async).length}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 15px; background: var(--dashboard-bg-tertiary); border-radius: 6px;">
                            <span style="color: var(--dashboard-text-secondary);">Class Methods</span>
                            <span style="font-weight: bold; color: var(--dashboard-text-primary);">${functions.filter(f => f.class_id).length}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 15px; background: var(--dashboard-bg-tertiary); border-radius: 6px;">
                            <span style="color: var(--dashboard-text-secondary);">File-level Functions</span>
                            <span style="font-weight: bold; color: var(--dashboard-text-primary);">${functions.filter(f => !f.class_id).length}</span>
                        </div>
                    </div>
                </div>
            `;
            
            const container = document.getElementById('domainContent') || document.getElementById('mainContent');
            if (container) {
                container.innerHTML = html;
            }
            
        } catch (error) {
            console.error('Error showing method composition:', error);
            this.showErrorMessage(`Failed to load method composition: ${error.message}`);
        }
    }

    // Show error message
    showErrorMessage(message) {
        const container = document.getElementById('domainContent') || document.getElementById('mainContent');
        if (container) {
            container.innerHTML = `
                <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; text-align: center; color: var(--dashboard-accent-error);">
                    <p>❌ ${message}</p>
                    <button class="usa-button usa-button--outline" onclick="domainAnalyzer.showDomainOverview()" style="margin-top: 15px;">
                        Try Again
                    </button>
                </div>
            `;
        }
    }
}

// Create global domain analyzer instance
window.domainAnalyzer = new DomainAnalyzer();

// Global functions for backwards compatibility
window.showServicesByDomain = () => window.domainAnalyzer.showServicesByDomain();
window.showMethodComposition = () => window.domainAnalyzer.showMethodComposition();