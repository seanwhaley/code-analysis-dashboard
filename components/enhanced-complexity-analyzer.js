/**
 * Enhanced Complexity Analyzer Component
 * Analyzes and visualizes code complexity metrics with real data
 */

class EnhancedComplexityAnalyzer {
    constructor() {
        this.complexityChart = null;
        this.scatterChart = null;
        this.apiBase = '/api';
        this.init();
    }
    
    async init() {
        this.setupComplexityChart();
        this.createComplexityScatterPlot();
        this.addComplexityInsights();
        
        // Load real data from API
        await this.loadComplexityData();
    }
    
    async loadComplexityData() {
        try {
            // Show loading state
            this.showLoadingState();
            
            // Fetch files data with complexity information
            const response = await fetch(`${this.apiBase}/files?limit=1000`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            const files = data.data || [];
            
            if (files.length > 0) {
                this.updateComplexityData(files);
                this.hideLoadingState();
            } else {
                this.showNoDataState();
            }
            
        } catch (error) {
            console.error('Error loading complexity data:', error);
            this.showErrorState(error.message);
        }
    }
    
    showLoadingState() {
        const statsContainer = document.getElementById('complexity-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="loading-placeholder">
                    <div class="usa-spinner" aria-valuetext="Loading complexity data..."></div>
                    <p>Loading complexity analysis...</p>
                </div>
            `;
        }
    }
    
    hideLoadingState() {
        // Loading state will be replaced by actual data
    }
    
    showNoDataState() {
        const statsContainer = document.getElementById('complexity-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="usa-alert usa-alert--info">
                    <div class="usa-alert__body">
                        <h4 class="usa-alert__heading">No Data Available</h4>
                        <p class="usa-alert__text">No complexity data found. Please ensure the database is populated.</p>
                    </div>
                </div>
            `;
        }
    }
    
    showErrorState(errorMessage) {
        const statsContainer = document.getElementById('complexity-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="usa-alert usa-alert--error">
                    <div class="usa-alert__body">
                        <h4 class="usa-alert__heading">Error Loading Data</h4>
                        <p class="usa-alert__text">Failed to load complexity data: ${errorMessage}</p>
                        <button class="usa-button usa-button--outline" onclick="window.enhancedComplexityAnalyzer.loadComplexityData()">
                            Retry
                        </button>
                    </div>
                </div>
            `;
        }
    }
    
    setupComplexityChart() {
        const ctx = document.getElementById('complexityChart');
        if (!ctx) return;
        
        this.complexityChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Low (1-5)', 'Medium (6-10)', 'High (11-20)', 'Very High (21+)'],
                datasets: [{
                    label: 'Files by Complexity',
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#28a745',
                        '#ffc107',
                        '#fd7e14',
                        '#dc3545'
                    ],
                    borderColor: [
                        '#1e7e34',
                        '#e0a800',
                        '#e8590c',
                        '#c82333'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed.y / total) * 100).toFixed(1);
                                return `${context.parsed.y} files (${percentage}%)`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Files'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Complexity Range'
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        this.showComplexityDetails(index);
                    }
                }
            }
        });
    }
    
    createComplexityScatterPlot() {
        // Create a scatter plot showing file size vs complexity
        const scatterContainer = document.createElement('div');
        scatterContainer.innerHTML = `
            <div class="usa-card chart-container" style="margin-top: 1rem;">
                <div class="usa-card__container">
                    <div class="usa-card__header">
                        <h3 class="usa-card__heading">File Size vs Complexity</h3>
                        <p class="usa-card__text">Interactive scatter plot - click points for details</p>
                    </div>
                    <div class="usa-card__body">
                        <canvas id="complexityScatterChart" width="400" height="300"></canvas>
                    </div>
                </div>
            </div>
        `;
        
        const chartsContainer = document.querySelector('.charts-container');
        if (chartsContainer) {
            chartsContainer.appendChild(scatterContainer);
            
            const scatterCtx = document.getElementById('complexityScatterChart');
            this.scatterChart = new Chart(scatterCtx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Files',
                        data: [],
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: {
                            callbacks: {
                                title: function(context) {
                                    const point = context[0];
                                    return point.raw.name || 'File';
                                },
                                label: function(context) {
                                    return [
                                        `Lines: ${context.parsed.x}`,
                                        `Complexity: ${context.parsed.y}`,
                                        `Domain: ${context.raw.domain || 'Unknown'}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Lines of Code'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Complexity Score'
                            }
                        }
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const point = this.scatterChart.data.datasets[0].data[elements[0].index];
                            if (point.fileId) {
                                window.dashboardCore.showFileDetails(point.fileId);
                            }
                        }
                    }
                }
            });
        }
    }
    
    addComplexityInsights() {
        // Add a complexity insights panel
        const insightsContainer = document.createElement('div');
        insightsContainer.id = 'complexity-insights';
        insightsContainer.innerHTML = `
            <div class="usa-card" style="margin-top: 1rem;">
                <div class="usa-card__container">
                    <div class="usa-card__header">
                        <h3 class="usa-card__heading">📊 Complexity Insights</h3>
                    </div>
                    <div class="usa-card__body">
                        <div id="complexity-stats" class="complexity-stats">
                            <div class="loading-placeholder">Loading complexity analysis...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const chartsContainer = document.querySelector('.charts-container');
        if (chartsContainer) {
            chartsContainer.appendChild(insightsContainer);
        }
    }
    
    updateComplexityData(files) {
        if (!this.complexityChart || !files) return;
        
        const complexityBuckets = [0, 0, 0, 0]; // Low, Medium, High, Very High
        const scatterData = [];
        let totalComplexity = 0;
        let maxComplexity = 0;
        let minComplexity = Infinity;
        let highComplexityFiles = [];
        
        files.forEach(file => {
            const complexity = file.complexity || 0;
            const lines = file.lines || 0;
            
            totalComplexity += complexity;
            maxComplexity = Math.max(maxComplexity, complexity);
            minComplexity = Math.min(minComplexity, complexity);
            
            // Categorize complexity
            if (complexity <= 5) complexityBuckets[0]++;
            else if (complexity <= 10) complexityBuckets[1]++;
            else if (complexity <= 20) complexityBuckets[2]++;
            else {
                complexityBuckets[3]++;
                if (complexity > 15) {
                    highComplexityFiles.push(file);
                }
            }
            
            // Add to scatter plot data
            scatterData.push({
                x: lines,
                y: complexity,
                name: file.name,
                domain: file.domain,
                fileId: file.id
            });
        });
        
        // Update bar chart
        this.complexityChart.data.datasets[0].data = complexityBuckets;
        this.complexityChart.update();
        
        // Update scatter plot
        if (this.scatterChart) {
            this.scatterChart.data.datasets[0].data = scatterData;
            this.scatterChart.update();
        }
        
        // Update insights
        this.updateComplexityInsights(files, {
            total: files.length,
            average: totalComplexity / files.length,
            max: maxComplexity,
            min: minComplexity,
            highComplexityFiles: highComplexityFiles.slice(0, 5) // Top 5
        });
    }
    
    updateComplexityInsights(files, stats) {
        const statsContainer = document.getElementById('complexity-stats');
        if (!statsContainer) return;
        
        const domainComplexity = {};
        files.forEach(file => {
            const domain = file.domain || 'Unknown';
            if (!domainComplexity[domain]) {
                domainComplexity[domain] = { total: 0, count: 0, files: [] };
            }
            domainComplexity[domain].total += file.complexity || 0;
            domainComplexity[domain].count++;
            domainComplexity[domain].files.push(file);
        });
        
        const sortedDomains = Object.entries(domainComplexity)
            .map(([domain, data]) => ({
                domain,
                average: data.total / data.count,
                count: data.count,
                files: data.files
            }))
            .sort((a, b) => b.average - a.average);
        
        statsContainer.innerHTML = `
            <div class="grid-row grid-gap">
                <div class="tablet:grid-col-6">
                    <div class="stat-card">
                        <h4>📈 Overall Statistics</h4>
                        <ul class="usa-list usa-list--unstyled">
                            <li><strong>Total Files:</strong> ${stats.total}</li>
                            <li><strong>Average Complexity:</strong> ${stats.average.toFixed(1)}</li>
                            <li><strong>Complexity Range:</strong> ${stats.min} - ${stats.max}</li>
                            <li><strong>High Complexity Files:</strong> ${stats.highComplexityFiles.length}</li>
                        </ul>
                    </div>
                </div>
                <div class="tablet:grid-col-6">
                    <div class="stat-card">
                        <h4>🏗️ Domain Analysis</h4>
                        <div class="domain-complexity-list">
                            ${sortedDomains.slice(0, 5).map(domain => `
                                <div class="domain-item">
                                    <span class="domain-name">${domain.domain}</span>
                                    <span class="domain-avg">${domain.average.toFixed(1)} avg</span>
                                    <span class="domain-count">(${domain.count} files)</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
            
            ${stats.highComplexityFiles.length > 0 ? `
                <div class="high-complexity-section" style="margin-top: 1rem;">
                    <h4>⚠️ High Complexity Files (Needs Review)</h4>
                    <div class="high-complexity-list">
                        ${stats.highComplexityFiles.map(file => `
                            <div class="complexity-file-item" onclick="window.dashboardCore.showFileDetails(${file.id})">
                                <div class="file-info">
                                    <span class="file-name">${file.name}</span>
                                    <span class="file-path">${file.path}</span>
                                </div>
                                <div class="complexity-badge complexity-${this.getComplexityLevel(file.complexity)}">
                                    ${file.complexity}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
    }
    
    getComplexityLevel(complexity) {
        if (complexity <= 5) return 'low';
        if (complexity <= 10) return 'medium';
        if (complexity <= 20) return 'high';
        return 'very-high';
    }
    
    showComplexityDetails(bucketIndex) {
        const ranges = [
            { min: 1, max: 5, label: 'Low Complexity' },
            { min: 6, max: 10, label: 'Medium Complexity' },
            { min: 11, max: 20, label: 'High Complexity' },
            { min: 21, max: Infinity, label: 'Very High Complexity' }
        ];
        
        const range = ranges[bucketIndex];
        if (!range) return;
        
        // This would trigger a filtered view of files in this complexity range
        console.log(`Showing ${range.label} files (${range.min}-${range.max === Infinity ? '∞' : range.max})`);
        
        // Could integrate with the file list to filter by complexity
        if (window.dashboardCore && window.dashboardCore.filterFilesByComplexity) {
            window.dashboardCore.filterFilesByComplexity(range.min, range.max);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedComplexityAnalyzer = new EnhancedComplexityAnalyzer();
});