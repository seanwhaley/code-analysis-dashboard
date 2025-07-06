/**
 * D3.js Visualization Manager
 * Alternative to Mermaid for complex, interactive visualizations
 */
class D3Visualizer {
    constructor() {
        this.d3Loaded = false;
        this.currentVisualization = null;
    }

    // Initialize D3.js library
    async initializeD3() {
        if (this.d3Loaded) return true;

        try {
            // Load D3.js from CDN
            const script = document.createElement('script');
            script.src = 'https://d3js.org/d3.v7.min.js';
            script.onload = () => {
                this.d3Loaded = true;
                console.log('✅ D3.js loaded successfully');
            };
            script.onerror = () => {
                console.error('❌ Failed to load D3.js');
            };
            document.head.appendChild(script);

            // Wait for D3 to load
            return new Promise((resolve) => {
                const checkD3 = () => {
                    if (typeof d3 !== 'undefined') {
                        this.d3Loaded = true;
                        resolve(true);
                    } else {
                        setTimeout(checkD3, 100);
                    }
                };
                checkD3();
            });
        } catch (error) {
            console.error('❌ Error initializing D3:', error);
            return false;
        }
    }

    // Create interactive dependency network
    async createDependencyNetwork(dependencies, containerId) {
        if (!await this.initializeD3()) {
            this.showFallbackMessage(containerId, 'Failed to load D3.js visualization library');
            return;
        }

        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`❌ Container ${containerId} not found`);
            return;
        }

        // Clear previous visualization
        container.innerHTML = '';

        // Set up dimensions
        const width = container.clientWidth || 800;
        const height = 600;
        const margin = { top: 20, right: 20, bottom: 20, left: 20 };

        // Create SVG
        const svg = d3.select(`#${containerId}`)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .style('background', 'var(--dashboard-bg-tertiary)')
            .style('border-radius', '8px');

        // Create nodes and links from dependencies data
        const nodes = [];
        const links = [];
        const nodeMap = new Map();

        // Process dependencies into nodes and links
        dependencies.forEach(dep => {
            // Add source node
            if (!nodeMap.has(dep.source)) {
                nodeMap.set(dep.source, {
                    id: dep.source,
                    name: dep.source,
                    type: 'file',
                    group: this.getNodeGroup(dep.source)
                });
                nodes.push(nodeMap.get(dep.source));
            }

            // Add target node
            if (!nodeMap.has(dep.target)) {
                nodeMap.set(dep.target, {
                    id: dep.target,
                    name: dep.target,
                    type: 'module',
                    group: this.getNodeGroup(dep.target)
                });
                nodes.push(nodeMap.get(dep.target));
            }

            // Add link
            links.push({
                source: dep.source,
                target: dep.target,
                type: dep.type || 'import'
            });
        });

        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30));

        // Create links
        const link = svg.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', 2)
            .attr('marker-end', 'url(#arrowhead)');

        // Add arrow markers
        svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 25)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#999');

        // Create nodes
        const node = svg.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(nodes)
            .enter().append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', this.dragstarted.bind(this, simulation))
                .on('drag', this.dragged)
                .on('end', this.dragended.bind(this, simulation)));

        // Add circles to nodes
        node.append('circle')
            .attr('r', 20)
            .attr('fill', d => this.getNodeColor(d.group))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);

        // Add labels to nodes
        node.append('text')
            .text(d => d.name.length > 15 ? d.name.substring(0, 12) + '...' : d.name)
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .attr('font-size', '10px')
            .attr('fill', '#333');

        // Add tooltips
        node.append('title')
            .text(d => `${d.name}\nType: ${d.type}\nGroup: ${d.group}`);

        // Update positions on simulation tick
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('transform', d => `translate(${d.x},${d.y})`);
        });

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                svg.selectAll('g.nodes, g.links')
                    .attr('transform', event.transform);
            });

        svg.call(zoom);

        // Add controls
        this.addVisualizationControls(containerId, simulation, svg);

        console.log('✅ D3 dependency network created successfully');
    }

    // Create interactive class hierarchy tree
    async createClassHierarchyTree(classData, containerId) {
        if (!await this.initializeD3()) {
            this.showFallbackMessage(containerId, 'Failed to load D3.js visualization library');
            return;
        }

        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';

        const width = container.clientWidth || 800;
        const height = 600;

        const svg = d3.select(`#${containerId}`)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .style('background', 'var(--dashboard-bg-tertiary)')
            .style('border-radius', '8px');

        // Transform flat class data into hierarchy
        const hierarchy = this.buildClassHierarchy(classData);
        
        const root = d3.hierarchy(hierarchy);
        const treeLayout = d3.tree().size([height - 100, width - 100]);
        
        treeLayout(root);

        // Create links
        svg.selectAll('.link')
            .data(root.links())
            .enter().append('path')
            .attr('class', 'link')
            .attr('d', d3.linkHorizontal()
                .x(d => d.y + 50)
                .y(d => d.x + 50))
            .attr('fill', 'none')
            .attr('stroke', '#999')
            .attr('stroke-width', 2);

        // Create nodes
        const nodes = svg.selectAll('.node')
            .data(root.descendants())
            .enter().append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.y + 50},${d.x + 50})`);

        nodes.append('circle')
            .attr('r', 15)
            .attr('fill', d => d.children ? '#007bff' : '#28a745')
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);

        nodes.append('text')
            .attr('dx', 20)
            .attr('dy', '.35em')
            .text(d => d.data.name)
            .attr('font-size', '12px')
            .attr('fill', '#333');

        // Add click handlers
        nodes.on('click', (event, d) => {
            if (d.data.id) {
                window.modalManager.showClassDetails(d.data.id);
            }
        });

        console.log('✅ D3 class hierarchy tree created successfully');
    }

    // Helper methods
    getNodeGroup(nodeName) {
        if (nodeName.includes('src/')) return 'source';
        if (nodeName.includes('test')) return 'test';
        if (nodeName.includes('.py')) return 'python';
        return 'other';
    }

    getNodeColor(group) {
        const colors = {
            'source': '#007bff',
            'test': '#28a745',
            'python': '#ffc107',
            'other': '#6c757d'
        };
        return colors[group] || '#6c757d';
    }

    buildClassHierarchy(classData) {
        // Build a tree structure from flat class data
        const classMap = new Map();
        const roots = [];

        // First pass: create all nodes
        classData.forEach(cls => {
            classMap.set(cls.name, {
                name: cls.name,
                id: cls.id,
                children: [],
                data: cls
            });
        });

        // Second pass: build hierarchy
        classData.forEach(cls => {
            const node = classMap.get(cls.name);
            let hasParent = false;

            if (cls.base_classes) {
                let baseClasses = [];
                try {
                    baseClasses = Array.isArray(cls.base_classes) ? 
                        cls.base_classes : JSON.parse(cls.base_classes || '[]');
                } catch (e) {
                    baseClasses = [];
                }

                baseClasses.forEach(baseName => {
                    const parent = classMap.get(baseName);
                    if (parent) {
                        parent.children.push(node);
                        hasParent = true;
                    }
                });
            }

            if (!hasParent) {
                roots.push(node);
            }
        });

        // Return a single root with all trees as children
        return {
            name: 'Classes',
            children: roots
        };
    }

    // Drag handlers for force simulation
    dragstarted(simulation, event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragended(simulation, event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    // Add visualization controls
    addVisualizationControls(containerId, simulation, svg) {
        const container = document.getElementById(containerId);
        const controls = document.createElement('div');
        controls.style.cssText = 'margin-top: 10px; text-align: center;';
        
        controls.innerHTML = `
            <button class="usa-button usa-button--outline" onclick="d3Visualizer.resetZoom('${containerId}')">
                Reset View
            </button>
            <button class="usa-button usa-button--outline" onclick="d3Visualizer.pauseSimulation()">
                Pause Animation
            </button>
            <button class="usa-button usa-button--outline" onclick="d3Visualizer.resumeSimulation()">
                Resume Animation
            </button>
        `;
        
        container.appendChild(controls);
        
        // Store references for control functions
        this.currentSimulation = simulation;
        this.currentSvg = svg;
    }

    // Control functions
    resetZoom(containerId) {
        if (this.currentSvg) {
            this.currentSvg.transition().duration(750).call(
                d3.zoom().transform,
                d3.zoomIdentity
            );
        }
    }

    pauseSimulation() {
        if (this.currentSimulation) {
            this.currentSimulation.stop();
        }
    }

    resumeSimulation() {
        if (this.currentSimulation) {
            this.currentSimulation.restart();
        }
    }

    // Fallback message for when D3 fails to load
    showFallbackMessage(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div style="background: var(--dashboard-bg-tertiary); padding: 30px; border-radius: 8px; text-align: center; color: var(--dashboard-text-muted);">
                    <h3 style="color: var(--dashboard-text-primary); margin-bottom: 15px;">⚠️ Visualization Unavailable</h3>
                    <p>${message}</p>
                    <p style="font-size: 0.9em; margin-top: 15px;">Falling back to alternative visualization...</p>
                    <button class="usa-button usa-button--outline" onclick="location.reload()" style="margin-top: 15px;">
                        Refresh Page
                    </button>
                </div>
            `;
        }
    }
}

// Create global instance
window.d3Visualizer = new D3Visualizer();