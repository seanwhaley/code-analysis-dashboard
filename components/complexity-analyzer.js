/**
 * Complexity Analysis Component
 * Handles complexity analysis and visualization
 */

class ComplexityAnalyzer {
    constructor() {
        this.cache = new Map();
        this.complexityData = null;
    }

    // Show complexity overview
    async showComplexityOverview() {
        try {
            await this.loadComplexityData();
            
            if (!this.complexityData || this.complexityData.length === 0) {
                this.showNoDataMessage();
                return;
            }

            const stats = this.calculateComplexityStats();
            const distribution = this.getComplexityDistribution();
            
            let html = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="color: var(--dashboard-text-primary); margin: 0;">📊 Complexity Analysis</h3>
                    <button class="usa-button usa-button--outline usa-button--inverse" onclick="complexityAnalyzer.showComplexityGuide()" style="font-size: 0.9em;">
                        ❓ What is Complexity?
                    </button>
                </div>
                
                <!-- Complexity Purpose Explanation -->
                <div style="background: var(--dashboard-bg-secondary); padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 4px solid var(--dashboard-accent-primary);">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 10px;">🎯 Why Complexity Analysis Matters</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; font-size: 0.95em;">
                        <div>
                            <strong style="color: var(--dashboard-accent-primary);">🔍 Code Quality:</strong>
                            <span style="color: var(--dashboard-text-secondary);">Identifies functions that are hard to understand and maintain</span>
                        </div>
                        <div>
                            <strong style="color: var(--dashboard-accent-primary);">🧪 Testing:</strong>
                            <span style="color: var(--dashboard-text-secondary);">Higher complexity = more test cases needed</span>
                        </div>
                        <div>
                            <strong style="color: var(--dashboard-accent-primary);">🐛 Bug Risk:</strong>
                            <span style="color: var(--dashboard-text-secondary);">Complex code is more prone to bugs and errors</span>
                        </div>
                        <div>
                            <strong style="color: var(--dashboard-accent-primary);">⚡ Performance:</strong>
                            <span style="color: var(--dashboard-text-secondary);">Helps prioritize refactoring efforts</span>
                        </div>
                    </div>
                </div>
                
                <!-- Complexity Statistics -->
                <div class="grid-row grid-gap stats-grid" style="margin-bottom: 30px;">
                    <div class="tablet:grid-col-3">
                        <div class="usa-summary-box stat-card">
                            <div class="usa-summary-box__body">
                                <h2 class="usa-summary-box__heading stat-number">${stats.total}</h2>
                                <div class="usa-summary-box__text stat-label">Total Files</div>
                            </div>
                        </div>
                    </div>
                    <div class="tablet:grid-col-3">
                        <div class="usa-summary-box stat-card">
                            <div class="usa-summary-box__body">
                                <h2 class="usa-summary-box__heading stat-number">${stats.average.toFixed(1)}</h2>
                                <div class="usa-summary-box__text stat-label">Average Complexity</div>
                            </div>
                        </div>
                    </div>
                    <div class="tablet:grid-col-3">
                        <div class="usa-summary-box stat-card">
                            <div class="usa-summary-box__body">
                                <h2 class="usa-summary-box__heading stat-number">${stats.highest}</h2>
                                <div class="usa-summary-box__text stat-label">Highest Complexity</div>
                            </div>
                        </div>
                    </div>
                    <div class="tablet:grid-col-3">
                        <div class="usa-summary-box stat-card">
                            <div class="usa-summary-box__body">
                                <h2 class="usa-summary-box__heading stat-number">${stats.highComplexityCount}</h2>
                                <div class="usa-summary-box__text stat-label">High Complexity (>25)</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Complexity Explanation -->
                <div style="background: var(--dashboard-bg-secondary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light); margin-bottom: 20px;">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">📊 What is Cyclomatic Complexity?</h4>
                    <div style="color: var(--dashboard-text-secondary); line-height: 1.6;">
                        <p style="margin-bottom: 10px;">
                            <strong>Cyclomatic complexity</strong> measures the number of linearly independent paths through a program's source code. 
                            It counts decision points like if statements, loops, and switch cases.
                        </p>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 15px;">
                            <div style="background: var(--dashboard-bg-card); padding: 10px; border-radius: 4px; border-left: 3px solid #28a745;">
                                <strong style="color: #28a745;">1-10: Simple</strong><br>
                                <small>Easy to test and maintain</small>
                            </div>
                            <div style="background: var(--dashboard-bg-card); padding: 10px; border-radius: 4px; border-left: 3px solid #ffc107;">
                                <strong style="color: #ffc107;">11-25: Moderate</strong><br>
                                <small>Acceptable complexity</small>
                            </div>
                            <div style="background: var(--dashboard-bg-card); padding: 10px; border-radius: 4px; border-left: 3px solid #fd7e14;">
                                <strong style="color: #fd7e14;">26-50: High</strong><br>
                                <small>Consider refactoring</small>
                            </div>
                            <div style="background: var(--dashboard-bg-card); padding: 10px; border-radius: 4px; border-left: 3px solid #dc3545;">
                                <strong style="color: #dc3545;">50+: Very High</strong><br>
                                <small>Refactoring recommended</small>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Complexity Distribution -->
                <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light); margin-bottom: 20px;">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">Complexity Distribution</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: space-around;">
                        ${Object.entries(distribution).map(([range, data]) => `
                            <div style="background: var(--dashboard-bg-card); padding: 20px; border-radius: 6px; text-align: center; min-width: 150px; flex: 1; max-width: 200px; border-left: 4px solid ${data.color};">
                                <div style="color: ${data.color}; font-size: 2rem; font-weight: 700; margin-bottom: 8px;">${data.count}</div>
                                <div style="color: var(--dashboard-text-primary); font-size: 1rem; font-weight: 600; margin-bottom: 4px;">${range}</div>
                                <div style="color: var(--dashboard-text-muted); font-size: 0.9rem;">${((data.count / stats.total) * 100).toFixed(1)}% of files</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- Top Complex Files -->
                <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light);">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">Most Complex Files</h4>
                    <div style="max-height: 300px; overflow-y: auto;">
                        ${this.complexityData
                            .sort((a, b) => (b.complexity || 0) - (a.complexity || 0))
                            .slice(0, 10)
                            .map(file => `
                                <div class="list-item" onclick="modalManager.showFileDetails(${file.id})" style="margin-bottom: 10px; cursor: pointer;">
                                    <div class="list-item-title">${file.name}</div>
                                    <div class="list-item-meta">${file.path}</div>
                                    <div class="list-item-stats">
                                        <span class="list-item-stat" style="background: ${this.getComplexityColor(file.complexity)}; color: white;">
                                            📊 Complexity: ${file.complexity || 0}
                                        </span>
                                        <span class="list-item-stat">📏 Lines: ${file.lines || 0}</span>
                                        <span class="list-item-stat">🏷️ ${file.domain || 'Unknown'}</span>
                                    </div>
                                </div>
                            `).join('')}
                    </div>
                </div>
            `;
            
            document.getElementById('complexityContent').innerHTML = html;
            
        } catch (error) {
            console.error('Error showing complexity overview:', error);
            this.showErrorMessage('Failed to load complexity overview');
        }
    }

    // Show high complexity files
    async showHighComplexityFiles() {
        try {
            await this.loadComplexityData();
            
            const highComplexityFiles = this.complexityData
                .filter(file => (file.complexity || 0) > 25)
                .sort((a, b) => (b.complexity || 0) - (a.complexity || 0));
            
            let html = `
                <h3 style="margin-bottom: 20px; color: var(--dashboard-text-primary);">🔥 High Complexity Files (>25)</h3>
            `;
            
            if (highComplexityFiles.length === 0) {
                html += `
                    <div style="background: var(--dashboard-bg-tertiary); padding: 30px; border-radius: 8px; text-align: center; color: var(--dashboard-text-muted);">
                        <p style="font-size: 1.2rem; margin-bottom: 10px;">🎉 Great news!</p>
                        <p>No files with high complexity (>25) found in your codebase.</p>
                        <p style="font-size: 0.9rem; margin-top: 15px;">This indicates good code maintainability.</p>
                    </div>
                `;
            } else {
                html += `
                    <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light); margin-bottom: 20px;">
                        <p style="color: var(--dashboard-text-secondary); margin-bottom: 15px;">
                            Found <strong>${highComplexityFiles.length}</strong> files with high complexity. 
                            Consider refactoring these files to improve maintainability.
                        </p>
                        <div style="max-height: 500px; overflow-y: auto;">
                            ${highComplexityFiles.map(file => `
                                <div class="list-item" onclick="modalManager.showFileDetails(${file.id})" style="margin-bottom: 10px; cursor: pointer; border-left: 4px solid ${this.getComplexityColor(file.complexity)};">
                                    <div class="list-item-title">${file.name}</div>
                                    <div class="list-item-meta">${file.path}</div>
                                    <div class="list-item-stats">
                                        <span class="list-item-stat" style="background: ${this.getComplexityColor(file.complexity)}; color: white;">
                                            📊 Complexity: ${file.complexity || 0}
                                        </span>
                                        <span class="list-item-stat">📏 Lines: ${file.lines || 0}</span>
                                        <span class="list-item-stat">🏗️ Classes: ${file.classes || 0}</span>
                                        <span class="list-item-stat">⚙️ Functions: ${file.functions || 0}</span>
                                        <span class="list-item-stat">🏷️ ${file.domain || 'Unknown'}</span>
                                    </div>
                                    <div style="margin-top: 10px; padding: 10px; background: var(--dashboard-bg-secondary); border-radius: 4px; font-size: 0.9em; color: var(--dashboard-text-muted);">
                                        <strong>Refactoring suggestions:</strong>
                                        ${this.getRefactoringSuggestions(file.complexity)}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            document.getElementById('complexityContent').innerHTML = html;
            
        } catch (error) {
            console.error('Error showing high complexity files:', error);
            this.showErrorMessage('Failed to load high complexity files');
        }
    }

    // Show complexity trends
    async showComplexityTrends() {
        try {
            await this.loadComplexityData();
            
            const domainComplexity = this.getComplexityByDomain();
            const sizeComplexityCorrelation = this.getSizeComplexityCorrelation();
            
            let html = `
                <h3 style="margin-bottom: 20px; color: var(--dashboard-text-primary);">📈 Complexity Trends</h3>
                
                <!-- Complexity by Domain -->
                <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light); margin-bottom: 20px;">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">Complexity by Domain</h4>
                    <div style="display: grid; gap: 10px;">
                        ${Object.entries(domainComplexity)
                            .sort(([,a], [,b]) => b.avgComplexity - a.avgComplexity)
                            .map(([domain, data]) => `
                                <div style="background: var(--dashboard-bg-card); padding: 15px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="color: var(--dashboard-text-primary); font-weight: 600;">${domain}</div>
                                        <div style="color: var(--dashboard-text-muted); font-size: 0.9em;">${data.fileCount} files</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="color: ${this.getComplexityColor(data.avgComplexity)}; font-size: 1.2rem; font-weight: 600;">
                                            ${data.avgComplexity.toFixed(1)}
                                        </div>
                                        <div style="color: var(--dashboard-text-muted); font-size: 0.8em;">avg complexity</div>
                                    </div>
                                </div>
                            `).join('')}
                    </div>
                </div>
                
                <!-- Size vs Complexity Correlation -->
                <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; border: 1px solid var(--dashboard-border-light);">
                    <h4 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">Size vs Complexity Analysis</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                        ${sizeComplexityCorrelation.map(range => `
                            <div style="background: var(--dashboard-bg-card); padding: 15px; border-radius: 6px; text-align: center;">
                                <div style="color: var(--dashboard-text-primary); font-weight: 600; margin-bottom: 5px;">
                                    ${range.sizeRange}
                                </div>
                                <div style="color: var(--dashboard-text-muted); font-size: 0.9em; margin-bottom: 10px;">
                                    ${range.fileCount} files
                                </div>
                                <div style="color: ${this.getComplexityColor(range.avgComplexity)}; font-size: 1.1rem; font-weight: 600;">
                                    ${range.avgComplexity.toFixed(1)} avg complexity
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div style="margin-top: 15px; padding: 15px; background: var(--dashboard-bg-secondary); border-radius: 6px; color: var(--dashboard-text-secondary); font-size: 0.9em;">
                        <strong>Insight:</strong> ${this.getCorrelationInsight(sizeComplexityCorrelation)}
                    </div>
                </div>
            `;
            
            document.getElementById('complexityContent').innerHTML = html;
            
        } catch (error) {
            console.error('Error showing complexity trends:', error);
            this.showErrorMessage('Failed to load complexity trends');
        }
    }

    // Load complexity data
    async loadComplexityData() {
        if (this.complexityData) return;
        
        try {
            console.log('🔍 Loading complexity data...');
            const response = await fetch('/api/files?limit=5000');
            const result = await response.json();
            
            console.log('📊 Complexity API response:', result);
            
            if (result.success && result.data) {
                this.complexityData = result.data;
                console.log(`✅ Loaded ${this.complexityData.length} files for complexity analysis`);
            } else {
                console.error('❌ API response failed:', result);
                throw new Error('Failed to load files data: ' + (result.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('❌ Error loading complexity data:', error);
            throw error;
        }
    }

    // Calculate complexity statistics
    calculateComplexityStats() {
        const complexities = this.complexityData.map(file => file.complexity || 0);
        
        return {
            total: this.complexityData.length,
            average: complexities.reduce((sum, c) => sum + c, 0) / complexities.length,
            highest: Math.max(...complexities),
            lowest: Math.min(...complexities),
            highComplexityCount: complexities.filter(c => c > 25).length
        };
    }

    // Get complexity distribution
    getComplexityDistribution() {
        const distribution = {
            'Low (0-10)': { count: 0, color: '#28a745' },
            'Medium (11-25)': { count: 0, color: '#ffc107' },
            'High (26-50)': { count: 0, color: '#fd7e14' },
            'Very High (50+)': { count: 0, color: '#dc3545' }
        };
        
        this.complexityData.forEach(file => {
            const complexity = file.complexity || 0;
            if (complexity <= 10) distribution['Low (0-10)'].count++;
            else if (complexity <= 25) distribution['Medium (11-25)'].count++;
            else if (complexity <= 50) distribution['High (26-50)'].count++;
            else distribution['Very High (50+)'].count++;
        });
        
        return distribution;
    }

    // Get complexity by domain
    getComplexityByDomain() {
        const domainData = {};
        
        this.complexityData.forEach(file => {
            const domain = file.domain || 'Unknown';
            if (!domainData[domain]) {
                domainData[domain] = { totalComplexity: 0, fileCount: 0 };
            }
            domainData[domain].totalComplexity += file.complexity || 0;
            domainData[domain].fileCount++;
        });
        
        Object.keys(domainData).forEach(domain => {
            domainData[domain].avgComplexity = domainData[domain].totalComplexity / domainData[domain].fileCount;
        });
        
        return domainData;
    }

    // Get size vs complexity correlation
    getSizeComplexityCorrelation() {
        const ranges = [
            { min: 0, max: 50, sizeRange: 'Small (0-50 lines)' },
            { min: 51, max: 200, sizeRange: 'Medium (51-200 lines)' },
            { min: 201, max: 500, sizeRange: 'Large (201-500 lines)' },
            { min: 501, max: Infinity, sizeRange: 'Very Large (500+ lines)' }
        ];
        
        return ranges.map(range => {
            const filesInRange = this.complexityData.filter(file => {
                const lines = file.lines || 0;
                return lines >= range.min && lines <= range.max;
            });
            
            const avgComplexity = filesInRange.length > 0 
                ? filesInRange.reduce((sum, file) => sum + (file.complexity || 0), 0) / filesInRange.length
                : 0;
            
            return {
                ...range,
                fileCount: filesInRange.length,
                avgComplexity
            };
        });
    }

    // Get complexity color
    getComplexityColor(complexity) {
        if (complexity <= 10) return '#28a745';
        if (complexity <= 25) return '#ffc107';
        if (complexity <= 50) return '#fd7e14';
        return '#dc3545';
    }

    // Get refactoring suggestions
    getRefactoringSuggestions(complexity) {
        if (complexity > 50) {
            return 'Consider breaking this file into smaller modules, extract classes or functions, and simplify complex logic.';
        } else if (complexity > 25) {
            return 'Look for opportunities to extract functions, reduce nesting, and simplify conditional logic.';
        }
        return 'File complexity is acceptable.';
    }

    // Get correlation insight
    getCorrelationInsight(correlation) {
        const largeFiles = correlation.find(r => r.sizeRange.includes('Large'));
        const smallFiles = correlation.find(r => r.sizeRange.includes('Small'));
        
        if (largeFiles && smallFiles) {
            const ratio = largeFiles.avgComplexity / smallFiles.avgComplexity;
            if (ratio > 2) {
                return 'Larger files tend to have significantly higher complexity. Consider breaking down large files.';
            } else if (ratio < 1.5) {
                return 'File size and complexity are well-balanced across your codebase.';
            }
        }
        return 'Analyze individual files to identify complexity patterns.';
    }

    // Show no data message
    showNoDataMessage() {
        document.getElementById('complexityContent').innerHTML = `
            <div style="background: var(--dashboard-bg-tertiary); padding: 30px; border-radius: 8px; text-align: center; color: var(--dashboard-text-muted);">
                <p style="font-size: 1.2rem; margin-bottom: 10px;">📊 No Data Available</p>
                <p>No complexity data found. This could mean:</p>
                <ul style="text-align: left; display: inline-block; margin-top: 15px;">
                    <li>No files have been analyzed yet</li>
                    <li>Complexity metrics are not available</li>
                    <li>Data needs to be refreshed</li>
                </ul>
            </div>
        `;
    }

    // Show error message
    showErrorMessage(message) {
        document.getElementById('complexityContent').innerHTML = `
            <div style="background: var(--dashboard-bg-tertiary); padding: 20px; border-radius: 8px; text-align: center; color: var(--dashboard-accent-error);">
                <p>❌ ${message}</p>
                <button class="usa-button usa-button--outline" onclick="complexityAnalyzer.showComplexityOverview()" style="margin-top: 15px;">
                    Try Again
                </button>
            </div>
        `;
    }

    // Show complexity guide modal
    showComplexityGuide() {
        const modalHtml = `
            <div class="modal-overlay" onclick="modalManager.closeModal(this)">
                <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 700px;">
                    <div class="modal-header">
                        <h2>📚 Cyclomatic Complexity Guide</h2>
                        <button class="modal-close" onclick="modalManager.closeModal(this.closest('.modal-overlay'))">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div style="margin-bottom: 20px;">
                            <h3 style="color: var(--dashboard-accent-primary);">🔍 What is Cyclomatic Complexity?</h3>
                            <p style="line-height: 1.6; color: var(--dashboard-text-secondary);">
                                Cyclomatic complexity is a software metric that measures the number of linearly independent paths 
                                through a program's source code. It was developed by Thomas J. McCabe in 1976.
                            </p>
                        </div>

                        <div style="margin-bottom: 20px;">
                            <h3 style="color: var(--dashboard-accent-primary);">📊 Complexity Levels</h3>
                            <div style="display: grid; gap: 10px;">
                                <div style="display: flex; align-items: center; padding: 10px; background: var(--dashboard-bg-tertiary); border-radius: 4px; border-left: 4px solid #28a745;">
                                    <span style="font-weight: 600; color: #28a745; margin-right: 10px;">1-10:</span>
                                    <span>Simple - Easy to understand and test</span>
                                </div>
                                <div style="display: flex; align-items: center; padding: 10px; background: var(--dashboard-bg-tertiary); border-radius: 4px; border-left: 4px solid #ffc107;">
                                    <span style="font-weight: 600; color: #ffc107; margin-right: 10px;">11-25:</span>
                                    <span>Moderate - Acceptable complexity, may need attention</span>
                                </div>
                                <div style="display: flex; align-items: center; padding: 10px; background: var(--dashboard-bg-tertiary); border-radius: 4px; border-left: 4px solid #fd7e14;">
                                    <span style="font-weight: 600; color: #fd7e14; margin-right: 10px;">26-50:</span>
                                    <span>High - Consider refactoring for better maintainability</span>
                                </div>
                                <div style="display: flex; align-items: center; padding: 10px; background: var(--dashboard-bg-tertiary); border-radius: 4px; border-left: 4px solid #dc3545;">
                                    <span style="font-weight: 600; color: #dc3545; margin-right: 10px;">50+:</span>
                                    <span>Very High - Immediate refactoring recommended</span>
                                </div>
                            </div>
                        </div>

                        <div style="margin-bottom: 20px;">
                            <h3 style="color: var(--dashboard-accent-primary);">🎯 How to Use This Information</h3>
                            <ul style="line-height: 1.8; color: var(--dashboard-text-secondary);">
                                <li><strong>Prioritize Refactoring:</strong> Focus on functions with complexity > 25</li>
                                <li><strong>Testing Strategy:</strong> High complexity functions need more comprehensive tests</li>
                                <li><strong>Code Reviews:</strong> Pay extra attention to complex functions during reviews</li>
                                <li><strong>Documentation:</strong> Complex functions should have detailed documentation</li>
                                <li><strong>Team Training:</strong> Use complexity metrics to identify learning opportunities</li>
                            </ul>
                        </div>

                        <div style="background: var(--dashboard-bg-secondary); padding: 15px; border-radius: 6px; border-left: 4px solid var(--dashboard-accent-secondary);">
                            <h4 style="color: var(--dashboard-accent-secondary); margin-bottom: 10px;">💡 Pro Tips</h4>
                            <ul style="margin: 0; line-height: 1.6; color: var(--dashboard-text-secondary);">
                                <li>Break down complex functions into smaller, focused functions</li>
                                <li>Use early returns to reduce nesting levels</li>
                                <li>Consider using design patterns to simplify complex logic</li>
                                <li>Regular complexity monitoring helps maintain code quality</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        modalManager.showModal(modalHtml);
    }
}

// Create global complexity analyzer instance
window.complexityAnalyzer = new ComplexityAnalyzer();