#!/usr/bin/env python3
"""
Advanced Relationship and Dependency Analysis Component

This module provides comprehensive analysis of code relationships, dependencies,
circular dependencies, coupling metrics, and architectural insights.
"""


import asyncio
from collections import defaultdict
from typing import Dict, List, Union

import networkx as nx
import pandas as pd
import panel as pn
import param
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category20, Spectral11
from bokeh.plotting import figure
from bokeh.transform import linear_cmap
from dashboard.dashboard_logging import get_logger
from dashboard.models.dashboard_models import (
    CircularDependencyModel,
    CouplingMetricsModel,
)
from dashboard.services import TemplateService

logger = get_logger(__name__)


class RelationshipAnalysisComponent(param.Parameterized):
    """Component for analyzing code relationships and dependencies."""

    analysis_type = param.String(
        default="dependencies"
    )  # dependencies, coupling, circular
    scope_filter = param.String(default="all")  # all, domain, file
    relationship_types = param.List(default=["imports", "inherits", "calls"])

    def __init__(self, state, **params):
        super().__init__(**params)
        self.state = state
        self.dependency_graph: nx.DiGraph = nx.DiGraph()
        self.coupling_metrics: Dict[int, CouplingMetricsModel] = {}
        self.circular_dependencies: List[CircularDependencyModel] = []
        self.load_relationship_data()

    def load_relationship_data(self) -> None:
        """Load and process relationship data from database."""
        try:
            # Get all relationships and files
            relationships = self.state.db_querier.get_all_relationships()
            files, _ = self.state.db_querier.get_all_files(limit=1000)

            # Create file lookup
            file_lookup = {f.id: f for f in files}

            # Build dependency graph
            self.dependency_graph = nx.DiGraph()

            # Add nodes (files)
            for file in files:
                self.dependency_graph.add_node(
                    file.id,
                    name=file.name,
                    path=file.path,
                    domain=file.domain.value,
                    complexity=file.complexity,
                    lines_of_code=file.lines_of_code,
                )

            # Create file lookup for classes and functions
            classes, _ = self.state.db_querier.get_all_classes()
            functions, _ = self.state.db_querier.get_all_functions()

            # Create mappings from class/function IDs to file IDs
            class_to_file = {cls.id: cls.file_id for cls in classes}
            function_to_file = {func.id: func.file_id for func in functions}

            # Track file-to-file relationships to avoid duplicates
            file_relationships = set()

            # Add edges (derive file relationships from class/function relationships)
            for rel in relationships:
                source_file_id = None
                target_file_id = None

                # Determine source file
                if rel.source_type == "class":
                    source_file_id = class_to_file.get(rel.source_id)
                elif rel.source_type == "function":
                    source_file_id = function_to_file.get(rel.source_id)

                # Determine target file
                if rel.target_type == "class":
                    target_file_id = class_to_file.get(rel.target_id)
                elif rel.target_type == "function":
                    target_file_id = function_to_file.get(rel.target_id)

                # Add file-to-file edge if both files exist and are different
                if (
                    source_file_id
                    and target_file_id
                    and source_file_id != target_file_id
                    and source_file_id in file_lookup
                    and target_file_id in file_lookup
                    and (source_file_id, target_file_id) not in file_relationships
                ):

                    self.dependency_graph.add_edge(
                        source_file_id,
                        target_file_id,
                        relationship_type=rel.relationship_type.value,
                        source_entity=rel.source_name,
                        target_entity=rel.target_name,
                    )
                    file_relationships.add((source_file_id, target_file_id))

            # Calculate coupling metrics
            self.calculate_coupling_metrics()

            # Detect circular dependencies
            self.detect_circular_dependencies()

            logger.info(
                f"Loaded {self.dependency_graph.number_of_nodes()} nodes and {self.dependency_graph.number_of_edges()} relationships"
            )

        except Exception as e:
            logger.error(f"Error loading relationship data: {e}")
            self.dependency_graph = nx.DiGraph()

    def calculate_coupling_metrics(self):
        """Calculate various coupling metrics for the codebase."""
        if not self.dependency_graph:
            self.coupling_metrics = {}
            return

        # Calculate metrics for each file
        metrics: Dict[int, CouplingMetricsModel] = {}

        for node in self.dependency_graph.nodes():
            node_data = self.dependency_graph.nodes[node]

            # Afferent coupling (Ca) - incoming dependencies
            afferent_coupling = self.dependency_graph.in_degree(node)

            # Efferent coupling (Ce) - outgoing dependencies
            efferent_coupling = self.dependency_graph.out_degree(node)

            # Instability (I) = Ce / (Ca + Ce)
            total_coupling = afferent_coupling + efferent_coupling
            instability = (
                efferent_coupling / total_coupling if total_coupling > 0 else 0
            )

            # Abstractness (A) - simplified as ratio of abstract elements
            # For now, use a placeholder calculation
            abstractness = 0.5  # Would need more detailed analysis

            # Distance from main sequence (D) = |A + I - 1|
            distance_from_main = abs(abstractness + instability - 1)

            metrics[node] = CouplingMetricsModel(
                file_id=node,
                name=node_data["name"],
                path=node_data["path"],
                domain=node_data["domain"],
                afferent_coupling=afferent_coupling,
                efferent_coupling=efferent_coupling,
                instability=instability,
                abstractness=abstractness,
                distance_from_main=distance_from_main,
                total_coupling=total_coupling,
            )

        self.coupling_metrics = metrics

    def detect_circular_dependencies(self):
        """Detect circular dependencies in the codebase."""
        if not self.dependency_graph:
            self.circular_dependencies = []
            return

        try:
            # Find strongly connected components
            strongly_connected = list(
                nx.strongly_connected_components(self.dependency_graph)
            )

            # Filter out single-node components (not circular)
            circular_components = [comp for comp in strongly_connected if len(comp) > 1]

            self.circular_dependencies = []
            for component in circular_components:
                # Get the subgraph for this component
                subgraph = self.dependency_graph.subgraph(component)

                # Find a cycle in this component
                try:
                    cycle = nx.find_cycle(subgraph, orientation="original")

                    # Convert to file information
                    cycle_info = CircularDependencyModel(
                        nodes=list(component),
                        cycle_path=cycle,
                        file_names=[
                            self.dependency_graph.nodes[node]["name"]
                            for node in component
                        ],
                        file_paths=[
                            self.dependency_graph.nodes[node]["path"]
                            for node in component
                        ],
                        size=len(component),
                    )
                    self.circular_dependencies.append(cycle_info)

                except nx.NetworkXNoCycle:
                    # This shouldn't happen for strongly connected components with >1 node
                    pass

            logger.info(
                f"Found {len(self.circular_dependencies)} circular dependency groups"
            )

        except Exception as e:
            logger.error(f"Error detecting circular dependencies: {e}")
            self.circular_dependencies = []

    def create_dependency_matrix(self) -> Union[pn.pane.Bokeh, pn.pane.HTML]:
        """Create a dependency structure matrix (DSM)."""
        if not self.dependency_graph:
            return pn.pane.HTML("<p>No dependency data available</p>")

        # Get nodes and create adjacency matrix
        nodes = list(self.dependency_graph.nodes())
        node_names = [self.dependency_graph.nodes[node]["name"] for node in nodes]

        # Limit to reasonable size for visualization
        if len(nodes) > 50:
            # Take the most connected nodes
            degrees = dict(self.dependency_graph.degree())
            top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:50]
            nodes = [node for node, _ in top_nodes]
            node_names = [self.dependency_graph.nodes[node]["name"] for node in nodes]

        # Create adjacency matrix
        matrix_size = len(nodes)

        # Prepare data for heatmap
        x_coords = []
        y_coords = []
        colors = []

        for i, source in enumerate(nodes):
            for j, target in enumerate(nodes):
                x_coords.append(j)
                y_coords.append(matrix_size - 1 - i)  # Flip Y axis

                if self.dependency_graph.has_edge(source, target):
                    colors.append(1.0)  # Has dependency
                elif source == target:
                    colors.append(0.5)  # Diagonal
                else:
                    colors.append(0.0)  # No dependency

        # Create figure
        p = figure(
            width=800,
            height=800,
            title="Dependency Structure Matrix",
            x_range=node_names,
            y_range=list(reversed(node_names)),
            tools="hover,save",
            toolbar_location="above",
        )

        source = ColumnDataSource(
            data={
                "x": x_coords,
                "y": y_coords,
                "color": colors,
                "source_file": [
                    node_names[i % len(node_names)] for i in range(len(x_coords))
                ],
                "target_file": [
                    node_names[i // len(node_names)] for i in range(len(x_coords))
                ],
            }
        )

        # Add rectangles
        p.rect(
            "x",
            "y",
            width=0.9,
            height=0.9,
            source=source,
            fill_color=linear_cmap("color", ["white", "lightblue", "darkblue"], 0, 1),
            line_color="gray",
            line_width=0.5,
        )

        # Configure hover
        hover = p.select_one(HoverTool)
        hover.tooltips = [
            ("From", "@source_file"),
            ("To", "@target_file"),
            ("Has Dependency", "@color"),
        ]

        # Style
        p.xaxis.major_label_orientation = 45
        p.axis.major_label_text_font_size = "8pt"

        return pn.pane.Bokeh(p)

    def create_coupling_analysis(self) -> Union[pn.Column, pn.pane.HTML]:
        """Create coupling analysis dashboard."""
        if not self.coupling_metrics:
            return pn.pane.HTML("<p>No coupling metrics available</p>")

        df = pd.DataFrame([m.model_dump() for m in self.coupling_metrics.values()])

        # Create coupling scatter plot
        p = figure(
            width=800,
            height=600,
            title="Coupling Analysis: Instability vs Abstractness",
            x_axis_label="Instability (I)",
            y_axis_label="Abstractness (A)",
            tools="pan,wheel_zoom,box_zoom,reset,save,hover",
        )

        # Add main sequence line (ideal line from (0,1) to (1,0))
        p.line(
            [0, 1],
            [1, 0],
            line_color="red",
            line_dash="dashed",
            line_width=2,
            legend_label="Main Sequence",
        )

        # Color by domain
        domains = df["domain"].unique()
        if len(domains) == 1:
            colors = ["#1f77b4"]  # Single blue color for one domain
        elif len(domains) <= 20:
            colors = Category20[
                max(3, len(domains))
            ]  # Category20 requires at least 3 colors
        else:
            colors = Spectral11
        domain_colors = {
            domain: colors[i % len(colors)] for i, domain in enumerate(domains)
        }

        # Add scatter points
        for domain in domains:
            domain_data = df[df["domain"] == domain]

            source = ColumnDataSource(
                data={
                    "x": domain_data["instability"],
                    "y": domain_data["abstractness"],
                    "name": domain_data["name"],
                    "path": domain_data["path"],
                    "afferent": domain_data["afferent_coupling"],
                    "efferent": domain_data["efferent_coupling"],
                    "distance": domain_data["distance_from_main"],
                }
            )

            p.scatter(
                "x",
                "y",
                source=source,
                size=10,
                color=domain_colors[domain],
                alpha=0.7,
                legend_label=domain.title(),
            )

        # Configure hover
        hover = p.select_one(HoverTool)
        hover.tooltips = [
            ("File", "@name"),
            ("Path", "@path"),
            ("Instability", "@x{0.000}"),
            ("Abstractness", "@y{0.000}"),
            ("Afferent Coupling", "@afferent"),
            ("Efferent Coupling", "@efferent"),
            ("Distance from Main", "@distance{0.000}"),
        ]

        # Style
        p.legend.location = "top_right"
        p.legend.click_policy = "hide"

        # Prepare context for the template
        top_coupled = df.nlargest(10, "total_coupling")
        context = {
            "avg_instability": f"{df['instability'].mean():.3f}",
            "highly_coupled_files_count": len(df[df["total_coupling"] > 10]),
            "avg_distance_from_main": f"{df['distance_from_main'].mean():.3f}",
            "top_coupled": top_coupled.to_dict(orient="records"),
        }

        template_path = "d:/VS Code Projects/USASpendingv4/code-intelligence-dashboard/dashboard/components/templates/coupling_analysis_summary.html"

        # Use TemplateService instead of HTMLTemplateManager
        template_service = TemplateService()
        coupling_summary_html = template_service.render_template_sync(
            template_path, context
        )

        return pn.Column(
            pn.pane.Bokeh(p),
            pn.pane.HTML(coupling_summary_html),
            sizing_mode="stretch_width",
        )

    def create_circular_dependency_analysis(self) -> Union[pn.Column, pn.pane.HTML]:
        """Create circular dependency analysis and visualization."""
        # Prepare context for the template
        if not self.circular_dependencies:
            context = {"circular_dependencies": []}
        else:
            largest_cycle = max(self.circular_dependencies, key=lambda x: x.size)
            context = {
                "circular_dependencies": [
                    cycle.model_dump() for cycle in self.circular_dependencies
                ],
                "total_cycles": len(self.circular_dependencies),
                "total_files_involved": sum(
                    cycle.size for cycle in self.circular_dependencies
                ),
                "largest_cycle_size": largest_cycle.size,
            }

        template_path = "d:/VS Code Projects/USASpendingv4/code-intelligence-dashboard/dashboard/components/templates/circular_dependency_analysis.html"

        # Use TemplateService instead of HTMLTemplateManager
        template_service = TemplateService()
        analysis_html = template_service.render_template_sync(template_path, context)

        return pn.pane.HTML(analysis_html)

    def create_dependency_flow_diagram(self) -> Union[pn.pane.Bokeh, pn.pane.HTML]:
        """Create a flow diagram showing dependencies between domains."""
        if not self.dependency_graph:
            return pn.pane.HTML("<p>No dependency data available</p>")

        # Calculate domain-to-domain dependencies
        domain_deps = defaultdict(lambda: defaultdict(int))

        for source, target in self.dependency_graph.edges():
            source_domain = self.dependency_graph.nodes[source]["domain"]
            target_domain = self.dependency_graph.nodes[target]["domain"]

            if source_domain != target_domain:  # Only cross-domain dependencies
                domain_deps[source_domain][target_domain] += 1

        # Create a simplified chord diagram using Bokeh
        domains = list(
            set(
                list(domain_deps.keys())
                + [t for targets in domain_deps.values() for t in targets.keys()]
            )
        )

        if not domains:
            return pn.pane.HTML("<p>No cross-domain dependencies found</p>")

        # Create figure
        p = figure(
            width=800,
            height=600,
            title="Cross-Domain Dependency Flow",
            tools="hover,save",
            toolbar_location="above",
        )

        # Position domains in a circle
        import math

        n_domains = len(domains)
        angles = [2 * math.pi * i / n_domains for i in range(n_domains)]
        radius = 200

        domain_positions = {}
        for i, domain in enumerate(domains):
            x = radius * math.cos(angles[i])
            y = radius * math.sin(angles[i])
            domain_positions[domain] = (x, y)

        # Add domain nodes
        x_coords = [pos[0] for pos in domain_positions.values()]
        y_coords = [pos[1] for pos in domain_positions.values()]

        domain_source = ColumnDataSource(
            data={"x": x_coords, "y": y_coords, "domain": domains}
        )

        p.scatter("x", "y", source=domain_source, size=20, color="blue", alpha=0.7)
        p.text(
            "x",
            "y",
            text="domain",
            source=domain_source,
            text_align="center",
            text_baseline="middle",
        )

        # Add dependency arrows
        for source_domain, targets in domain_deps.items():
            for target_domain, count in targets.items():
                if count > 0:
                    source_pos = domain_positions[source_domain]
                    target_pos = domain_positions[target_domain]

                    # Draw arrow (simplified as line)
                    p.line(
                        [source_pos[0], target_pos[0]],
                        [source_pos[1], target_pos[1]],
                        line_width=max(1, count / 2),
                        line_alpha=0.6,
                        color="red",
                    )

        # Configure hover
        hover = p.select_one(HoverTool)
        hover.tooltips = [("Domain", "@domain")]

        return pn.pane.Bokeh(p)

    def view(self) -> pn.Tabs:
        """Return the complete relationship analysis view."""
        # Create different analysis tabs
        dependency_matrix_tab = self.create_dependency_matrix()
        coupling_tab = self.create_coupling_analysis()
        circular_tab = self.create_circular_dependency_analysis()
        flow_tab = self.create_dependency_flow_diagram()

        return pn.Tabs(
            ("📊 Dependency Matrix", dependency_matrix_tab),
            ("🔗 Coupling Analysis", coupling_tab),
            ("🔄 Circular Dependencies", circular_tab),
            ("🌊 Dependency Flow", flow_tab),
            dynamic=True,
            sizing_mode="stretch_width",
        )
