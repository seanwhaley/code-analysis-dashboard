#!/usr/bin/env python3
"""
Enhanced Network Graph Component
Modern network visualization using Plotly with improved interactivity and styling.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import panel as pn
import param
import plotly.graph_objects as go
from dashboard.components.enhanced_visualizations import (
    DOMAIN_COLORS,
    USWDS_COLORS,
    EnhancedVisualizationComponent,
)
from dashboard.dashboard_logging import get_logger
from plotly.subplots import make_subplots

logger = get_logger(__name__)


class EnhancedNetworkGraphComponent(param.Parameterized):
    """
    Enhanced network graph component with modern styling and interactions.
    """

    selected_nodes = param.List(default=[])
    graph_type = param.String(default="dependencies")
    layout_algorithm = param.String(default="spring")
    node_size_metric = param.String(default="degree")
    edge_filter = param.String(default="all")
    show_labels = param.Boolean(default=True)
    show_edge_weights = param.Boolean(default=False)

    def __init__(self, state: Any, **params: Any) -> None:
        """Initialize the enhanced network graph component."""
        super().__init__(**params)
        self.state = state
        self.graph = None
        self.pos = {}
        self.enhanced_viz = EnhancedVisualizationComponent(state)

    def create_network_visualization(self) -> pn.pane.HTML:
        """Create the main network visualization with controls."""
        try:
            # Create control panel
            controls = self._create_control_panel()

            # Create network graph
            network_graph = self._create_network_graph()

            # Create info panel
            info_panel = self._create_info_panel()

            # Layout with responsive design
            layout = pn.Column(
                pn.pane.HTML(
                    """
                <div class="usa-card usa-card--header-first">
                    <div class="usa-card__container">
                        <div class="usa-card__header">
                            <h2 class="usa-card__heading">🕸️ Network Analysis</h2>
                            <p class="usa-card__subtitle">Interactive visualization of code dependencies and relationships</p>
                        </div>
                    </div>
                </div>
                """,
                    sizing_mode="stretch_width",
                ),
                controls,
                pn.Row(
                    pn.Column(
                        network_graph, sizing_mode="stretch_width", width_policy="max"
                    ),
                    pn.Column(info_panel, sizing_mode="stretch_height", width=300),
                    sizing_mode="stretch_width",
                ),
                sizing_mode="stretch_width",
            )

            return layout

        except Exception as e:
            logger.error(f"Error creating network visualization: {e}")
            return self._create_error_message(
                f"Error creating network visualization: {e}"
            )

    def _create_control_panel(self) -> pn.pane.HTML:
        """Create interactive control panel."""
        controls_html = """
        <div class="usa-card" style="margin: 1rem 0;">
            <div class="usa-card__container">
                <div class="usa-card__header">
                    <h3 class="usa-card__heading">Visualization Controls</h3>
                </div>
                <div class="usa-card__body">
                    <div class="usa-form-group" style="display: flex; gap: 1rem; flex-wrap: wrap; align-items: center;">
                        <div>
                            <label class="usa-label" for="layout-select">Layout Algorithm:</label>
                            <select class="usa-select" id="layout-select" onchange="updateLayout(this.value)">
                                <option value="spring">Spring Layout</option>
                                <option value="circular">Circular Layout</option>
                                <option value="kamada_kawai">Kamada-Kawai Layout</option>
                                <option value="random">Random Layout</option>
                            </select>
                        </div>
                        <div>
                            <label class="usa-label" for="node-size-select">Node Size:</label>
                            <select class="usa-select" id="node-size-select" onchange="updateNodeSize(this.value)">
                                <option value="degree">By Degree</option>
                                <option value="complexity">By Complexity</option>
                                <option value="lines_of_code">By Lines of Code</option>
                                <option value="uniform">Uniform Size</option>
                            </select>
                        </div>
                        <div>
                            <label class="usa-label" for="edge-filter-select">Edge Filter:</label>
                            <select class="usa-select" id="edge-filter-select" onchange="updateEdgeFilter(this.value)">
                                <option value="all">All Edges</option>
                                <option value="strong">Strong Dependencies</option>
                                <option value="weak">Weak Dependencies</option>
                                <option value="circular">Circular Dependencies</option>
                            </select>
                        </div>
                        <div>
                            <label class="usa-checkbox">
                                <input class="usa-checkbox__input" type="checkbox" id="show-labels" onchange="toggleLabels(this.checked)" checked>
                                <span class="usa-checkbox__label">Show Labels</span>
                            </label>
                        </div>
                        <div>
                            <label class="usa-checkbox">
                                <input class="usa-checkbox__input" type="checkbox" id="show-weights" onchange="toggleWeights(this.checked)">
                                <span class="usa-checkbox__label">Show Edge Weights</span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        function updateLayout(value) {
            console.log('Layout changed to:', value);
            // This would trigger a callback to update the graph
        }
        
        function updateNodeSize(value) {
            console.log('Node size metric changed to:', value);
            // This would trigger a callback to update the graph
        }
        
        function updateEdgeFilter(value) {
            console.log('Edge filter changed to:', value);
            // This would trigger a callback to update the graph
        }
        
        function toggleLabels(checked) {
            console.log('Labels toggled:', checked);
            // This would trigger a callback to update the graph
        }
        
        function toggleWeights(checked) {
            console.log('Edge weights toggled:', checked);
            // This would trigger a callback to update the graph
        }
        </script>
        """

        return pn.pane.HTML(controls_html, sizing_mode="stretch_width")

    def _create_network_graph(self) -> pn.pane.Plotly:
        """Create the main network graph using Plotly."""
        try:
            # Get network data from state
            if not hasattr(self.state, "db_querier") or not self.state.db_querier:
                return self._create_no_data_message("Database not available")

            # Get relationships data
            relationships = self.state.db_querier.get_all_relationships()
            if not relationships:
                return self._create_no_data_message("No relationship data available")

            # Build NetworkX graph
            G = nx.DiGraph()

            # Add nodes and edges from relationships
            for rel in relationships[:100]:  # Limit for performance
                source = rel.get("source_file", "unknown")
                target = rel.get("target_file", "unknown")
                rel_type = rel.get("relationship_type", "dependency")

                # Add nodes with attributes
                if source not in G:
                    G.add_node(
                        source,
                        domain=rel.get("source_domain", "unknown"),
                        complexity=rel.get("source_complexity", 1),
                        lines_of_code=rel.get("source_lines", 0),
                    )

                if target not in G:
                    G.add_node(
                        target,
                        domain=rel.get("target_domain", "unknown"),
                        complexity=rel.get("target_complexity", 1),
                        lines_of_code=rel.get("target_lines", 0),
                    )

                # Add edge
                G.add_edge(source, target, type=rel_type, weight=1)

            if len(G.nodes()) == 0:
                return self._create_no_data_message("No nodes to display")

            # Calculate layout
            if self.layout_algorithm == "spring":
                pos = nx.spring_layout(G, k=1, iterations=50)
            elif self.layout_algorithm == "circular":
                pos = nx.circular_layout(G)
            elif self.layout_algorithm == "kamada_kawai":
                pos = nx.kamada_kawai_layout(G)
            else:
                pos = nx.random_layout(G)

            # Prepare edge traces
            edge_x = []
            edge_y = []
            edge_info = []

            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_info.append(f"{edge[0]} → {edge[1]}")

            # Create edge trace
            edge_trace = go.Scatter(
                x=edge_x,
                y=edge_y,
                line=dict(width=1, color=USWDS_COLORS["gray_30"]),
                hoverinfo="none",
                mode="lines",
                name="Dependencies",
                showlegend=False,
            )

            # Prepare node traces
            node_x = []
            node_y = []
            node_text = []
            node_colors = []
            node_sizes = []
            node_hover_text = []

            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)

                # Node label
                node_name = node.split("/")[-1] if "/" in node else node
                node_text.append(node_name if self.show_labels else "")

                # Node color by domain
                domain = G.nodes[node].get("domain", "unknown")
                domain_index = hash(domain) % len(DOMAIN_COLORS)
                node_colors.append(DOMAIN_COLORS[domain_index])

                # Node size by metric
                if self.node_size_metric == "degree":
                    size = max(15, min(40, G.degree(node) * 5))
                elif self.node_size_metric == "complexity":
                    complexity = G.nodes[node].get("complexity", 1)
                    size = max(15, min(40, complexity * 8))
                elif self.node_size_metric == "lines_of_code":
                    lines = G.nodes[node].get("lines_of_code", 0)
                    size = max(15, min(40, lines / 10))
                else:
                    size = 20

                node_sizes.append(size)

                # Hover text
                hover_text = f"""
                <b>{node_name}</b><br>
                Domain: {domain}<br>
                Complexity: {G.nodes[node].get('complexity', 'N/A')}<br>
                Lines of Code: {G.nodes[node].get('lines_of_code', 'N/A')}<br>
                Connections: {G.degree(node)}
                """
                node_hover_text.append(hover_text)

            # Create node trace
            node_trace = go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers+text" if self.show_labels else "markers",
                hoverinfo="text",
                text=node_text,
                textposition="middle center",
                textfont=dict(size=10, color=USWDS_COLORS["white"]),
                marker=dict(
                    size=node_sizes,
                    color=node_colors,
                    line=dict(width=2, color=USWDS_COLORS["white"]),
                    opacity=0.8,
                ),
                hovertext=node_hover_text,
                name="Components",
                showlegend=False,
            )

            # Create figure
            fig = go.Figure(data=[edge_trace, node_trace])

            fig.update_layout(
                title={
                    "text": f"Network Graph ({len(G.nodes())} nodes, {len(G.edges())} edges)",
                    "x": 0.02,
                    "xanchor": "left",
                    "font": {"size": 16, "color": USWDS_COLORS["base"]},
                },
                showlegend=False,
                hovermode="closest",
                margin=dict(b=20, l=5, r=5, t=60),
                annotations=[
                    dict(
                        text="Click and drag to explore • Hover for details • Use controls above to customize",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.005,
                        y=-0.002,
                        xanchor="left",
                        yanchor="bottom",
                        font=dict(color=USWDS_COLORS["base_light"], size=10),
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor=USWDS_COLORS["white"],
                paper_bgcolor=USWDS_COLORS["white"],
                height=600,
            )

            return pn.pane.Plotly(fig, sizing_mode="stretch_width")

        except Exception as e:
            logger.error(f"Error creating network graph: {e}")
            return self._create_error_message(f"Error creating network graph: {e}")

    def _create_info_panel(self) -> pn.pane.HTML:
        """Create information panel with network statistics."""
        info_html = """
        <div class="usa-card">
            <div class="usa-card__container">
                <div class="usa-card__header">
                    <h3 class="usa-card__heading">Network Statistics</h3>
                </div>
                <div class="usa-card__body">
                    <div class="network-stats">
                        <div class="stat-item">
                            <span class="stat-label">Nodes:</span>
                            <span class="stat-value" id="node-count">-</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Edges:</span>
                            <span class="stat-value" id="edge-count">-</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Density:</span>
                            <span class="stat-value" id="density">-</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Avg Degree:</span>
                            <span class="stat-value" id="avg-degree">-</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Components:</span>
                            <span class="stat-value" id="components">-</span>
                        </div>
                    </div>
                    
                    <hr style="margin: 1rem 0;">
                    
                    <h4>Selected Node</h4>
                    <div id="selected-node-info">
                        <p style="color: #71767a; font-style: italic;">Click on a node to see details</p>
                    </div>
                    
                    <hr style="margin: 1rem 0;">
                    
                    <h4>Legend</h4>
                    <div class="legend">
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #005ea2;"></div>
                            <span>Services</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #fa9441;"></div>
                            <span>Models</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #00a91c;"></div>
                            <span>Views</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #ffbe2e;"></div>
                            <span>Utils</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
        .network-stats .stat-item {
            display: flex;
            justify-content: space-between;
            margin: 0.5rem 0;
            padding: 0.25rem 0;
            border-bottom: 1px solid #e6e6e6;
        }
        
        .stat-label {
            font-weight: bold;
            color: #1b1b1b;
        }
        
        .stat-value {
            color: #005ea2;
            font-weight: bold;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin: 0.5rem 0;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 0.5rem;
            border: 2px solid white;
            box-shadow: 0 0 0 1px #c9c9c9;
        }
        </style>
        """

        return pn.pane.HTML(info_html, sizing_mode="stretch_width")

    def _create_no_data_message(self, message: str) -> pn.pane.HTML:
        """Create a styled no-data message."""
        html = f"""
        <div class="usa-alert usa-alert--info usa-alert--no-icon" style="margin: 20px 0;">
            <div class="usa-alert__body">
                <p class="usa-alert__text">
                    <strong>No Data Available:</strong> {message}
                </p>
            </div>
        </div>
        """
        return pn.pane.HTML(html, sizing_mode="stretch_width")

    def _create_error_message(self, message: str) -> pn.pane.HTML:
        """Create a styled error message."""
        html = f"""
        <div class="usa-alert usa-alert--error usa-alert--no-icon" style="margin: 20px 0;">
            <div class="usa-alert__body">
                <p class="usa-alert__text">
                    <strong>Visualization Error:</strong> {message}
                </p>
            </div>
        </div>
        """
        return pn.pane.HTML(html, sizing_mode="stretch_width")
