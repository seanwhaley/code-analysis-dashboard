/**
 * D3.js Interactive Relationship Network for Code Analysis Dashboard
 * 
 * This module provides interactive network visualization capabilities using D3.js
 * for displaying code relationships and dependencies in the dashboard.
 * 
 * Usage: window.d3Visualizer.createRelationshipGraph(data, containerId)
 * 
 * @author Code Intelligence Dashboard
 * @version 1.0.0
 */

class D3Visualizer {
    constructor() {
        this.defaultConfig = {
            width: 900,
            height: 600,
            nodeRadius: 14,
            linkDistance: 120,
            chargeStrength: -300,
            strokeWidth: 2,
            colors: {
                node: '#1976d2',
                nodeStroke: '#fff',
                link: '#999',
                linkOpacity: 0.6
            }
        };
    }

    /**
     * Create an interactive relationship graph using D3.js force simulation
     * 
     * @param {Array} relationships - Array of relationship objects with source, target, type
     * @param {string} containerId - ID of the container element for the visualization
     * @param {Object} config - Optional configuration overrides
     * @returns {Promise<void>}
     */
    async createRelationshipGraph(relationships, containerId, config = {}) {
        if (!relationships || !Array.isArray(relationships)) {
            console.error('Invalid relationships data provided');
            return;
        }

        if (!document.getElementById(containerId)) {
            console.error(`Container element #${containerId} not found`);
            return;
        }

        // Merge configuration
        const settings = { ...this.defaultConfig, ...config };
        const { width, height, nodeRadius, linkDistance, chargeStrength, colors } = settings;

        try {
            // Build nodes and links from relationships
            const nodes = new Map();
            const links = [];

            relationships.forEach(rel => {
                // Ensure nodes exist
                if (!nodes.has(rel.source)) {
                    nodes.set(rel.source, { 
                        id: rel.source, 
                        name: rel.source,
                        type: rel.source_type || 'unknown'
                    });
                }
                if (!nodes.has(rel.target)) {
                    nodes.set(rel.target, { 
                        id: rel.target, 
                        name: rel.target,
                        type: rel.target_type || 'unknown'
                    });
                }

                // Add link
                links.push({
                    source: rel.source,
                    target: rel.target,
                    type: rel.relationship_type || rel.type || 'rel',
                    weight: rel.weight || 1
                });
            });

            const nodeArray = Array.from(nodes.values());

            // Create SVG container
            const container = d3.select(`#${containerId}`);
            container.selectAll('*').remove(); // Clear existing content

            const svg = container
                .append('svg')
                .attr('width', width)
                .attr('height', height)
                .attr('viewBox', `0 0 ${width} ${height}`)
                .style('max-width', '100%')
                .style('height', 'auto');

            // Create force simulation
            const simulation = d3.forceSimulation(nodeArray)
                .force('link', d3.forceLink(links)
                    .distance(linkDistance)
                    .id(d => d.id)
                )
                .force('charge', d3.forceManyBody().strength(chargeStrength))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(nodeRadius + 2));

            // Add zoom and pan behavior
            const g = svg.append('g');
            svg.call(d3.zoom()
                .scaleExtent([0.1, 4])
                .on('zoom', (event) => {
                    g.attr('transform', event.transform);
                })
            );

            // Create arrow markers for directed graphs
            svg.append('defs').selectAll('marker')
                .data(['end'])
                .enter().append('marker')
                .attr('id', 'arrowhead')
                .attr('viewBox', '0 -5 10 10')
                .attr('refX', nodeRadius + 8)
                .attr('refY', 0)
                .attr('markerWidth', 6)
                .attr('markerHeight', 6)
                .attr('orient', 'auto')
                .append('path')
                .attr('d', 'M0,-5L10,0L0,5')
                .attr('fill', colors.link);

            // Create links
            const link = g.append('g')
                .attr('class', 'links')
                .selectAll('line')
                .data(links)
                .enter().append('line')
                .attr('stroke', colors.link)
                .attr('stroke-opacity', colors.linkOpacity)
                .attr('stroke-width', d => Math.sqrt(d.weight || 1) * settings.strokeWidth)
                .attr('marker-end', 'url(#arrowhead)');

            // Add link labels
            const linkLabels = g.append('g')
                .attr('class', 'link-labels')
                .selectAll('text')
                .data(links)
                .enter().append('text')
                .attr('font-size', '10px')
                .attr('font-family', 'Arial, sans-serif')
                .attr('fill', '#666')
                .attr('text-anchor', 'middle')
                .text(d => d.type);

            // Create nodes
            const node = g.append('g')
                .attr('class', 'nodes')
                .selectAll('circle')
                .data(nodeArray)
                .enter().append('circle')
                .attr('r', nodeRadius)
                .attr('fill', this.getNodeColor)
                .attr('stroke', colors.nodeStroke)
                .attr('stroke-width', 1.5)
                .call(this.createDragBehavior(simulation));

            // Add node labels
            const labels = g.append('g')
                .attr('class', 'labels')
                .selectAll('text')
                .data(nodeArray)
                .enter().append('text')
                .attr('font-size', '12px')
                .attr('font-family', 'Arial, sans-serif')
                .attr('text-anchor', 'middle')
                .attr('dy', nodeRadius + 15)
                .text(d => d.name.length > 15 ? d.name.substring(0, 12) + '...' : d.name);

            // Add tooltips
            node.append('title').text(d => `${d.name}\nType: ${d.type}`);

            // Update positions on simulation tick
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);

                linkLabels
                    .attr('x', d => (d.source.x + d.target.x) / 2)
                    .attr('y', d => (d.source.y + d.target.y) / 2);

                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);

                labels
                    .attr('x', d => d.x)
                    .attr('y', d => d.y);
            });

            console.log(`Created network graph with ${nodeArray.length} nodes and ${links.length} links`);

        } catch (error) {
            console.error('Error creating relationship graph:', error);
            const container = d3.select(`#${containerId}`);
            container.html(`<div class="error">Error creating visualization: ${error.message}</div>`);
        }
    }

    /**
     * Get node color based on type
     * @param {Object} d - Node data
     * @returns {string} Color for the node
     */
    getNodeColor(d) {
        const colorMap = {
            'file': '#1976d2',
            'class': '#388e3c',
            'function': '#f57c00',
            'module': '#7b1fa2',
            'unknown': '#757575'
        };
        return colorMap[d.type] || colorMap.unknown;
    }

    /**
     * Create drag behavior for nodes
     * @param {Object} simulation - D3 force simulation
     * @returns {Object} D3 drag behavior
     */
    createDragBehavior(simulation) {
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }

    /**
     * Clear the visualization
     * @param {string} containerId - Container element ID
     */
    clear(containerId) {
        const container = d3.select(`#${containerId}`);
        container.selectAll('*').remove();
    }
}

// Initialize global instance
window.d3Visualizer = new D3Visualizer();