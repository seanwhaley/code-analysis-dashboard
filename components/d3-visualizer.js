/**
 * D3.js Interactive Relationship Network for Code Analysis Dashboard
 * Usage: window.d3Visualizer.createRelationshipGraph(data, containerId)
 */
class D3Visualizer {
    async createRelationshipGraph(relationships, containerId) {
        // relationships: [{source, target, type}]
        const width = 900, height = 600;
        const nodes = {};
        relationships.forEach(r => {
            nodes[r.source] = {id: r.source};
            nodes[r.target] = {id: r.target};
        });
        const links = relationships.map(r => ({
            source: r.source,
            target: r.target,
            type: r.type || "rel"
        }));
        const svg = d3.select(`#${containerId}`)
            .html("")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const simulation = d3.forceSimulation(Object.values(nodes))
            .force("link", d3.forceLink(links).distance(120).id(d => d.id))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = svg.append("g")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("stroke-width", 2);

        const node = svg.append("g")
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5)
            .selectAll("circle")
            .data(Object.values(nodes))
            .enter().append("circle")
            .attr("r", 14)
            .attr("fill", "#1976d2")
            .call(drag(simulation));

        node.append("title").text(d => d.id);

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
        });

        function drag(sim) {
            function dragstarted(event, d) {
                if (!event.active) sim.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }
            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }
            function dragended(event, d) {
                if (!event.active) sim.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
            return d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }
    }
}
window.d3Visualizer = new D3Visualizer();