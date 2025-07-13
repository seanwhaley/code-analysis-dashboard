#!/usr/bin/env python3
"""
Network Graph Visualization Component

This module provides interactive network graph visualizations for code relationships,
dependencies, and architectural patterns using Bokeh and NetworkX.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

import networkx as nx
import panel as pn
import param
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, TapTool
from bokeh.plotting import figure
from dashboard.dashboard_logging import get_logger
from dashboard.models.dashboard_models import (
    DomainColorsModel,
    EdgeDataModel,
    EdgeFilterOptionsModel,
    EdgeModel,
    GraphStatisticsManager,
    HoverTooltipsModel,
    NodeDataModel,
    NodeModel,
    RelationshipTypeAlphaModel,
)

logger = get_logger(__name__)


class NetworkGraphComponent(param.Parameterized):
    """
    Interactive network graph component for code relationship visualization.

    All visualization parameters are config-driven via settings.
    """

    selected_nodes = param.List(default=[])
    graph_type = param.String(default="dependencies")
    layout_algorithm = param.String(default="spring")
    node_size_metric = param.String(default="degree")
    edge_filter = param.String(default="all")
    show_labels = param.Boolean(default=True)

    def __init__(self, state: Any, **params: Any) -> None:
        """
        Initialize the NetworkGraphComponent.
        Loads config-driven defaults from settings and sets up the graph.
        """
        super().__init__(**params)
        self.state = state
        self.settings = getattr(state, "settings", None)
        self.graph: nx.DiGraph = nx.DiGraph()
        self.pos: Dict[int, Tuple[float, float]] = {}
        self.figure: Optional[figure] = None
        self.node_source: Optional[ColumnDataSource] = None
        self.edge_source: Optional[ColumnDataSource] = None

        # Load config-driven defaults from settings if available
        if self.settings:
            net_cfg = getattr(self.settings, "network_graph", None)
            if net_cfg:
                self.layout_algorithm = net_cfg.default_layout
                self.node_size_metric = net_cfg.node_size_metric
                self.edge_filter = net_cfg.edge_filter
                self.show_labels = net_cfg.show_labels

        self.setup_graph()

    def setup_graph(self) -> None:
        """
        Initialize the network graph with data from database.
        All nodes and edges are created using Pydantic models.
        """
        try:
            relationships = self.state.db_querier.get_all_relationships()
            files = self.state.db_querier.get_all_files(limit=1000)[0]

            self.graph = nx.DiGraph()

            # Add nodes using NodeModel
            self.node_models: Dict[int, NodeModel] = {}
            for file in files:
                node = NodeModel(
                    id=file.id,
                    name=file.name,
                    path=file.path,
                    domain=file.domain.value,
                    complexity=file.complexity,
                    lines_of_code=file.lines_of_code,
                    classes_count=file.classes_count,
                    functions_count=file.functions_count,
                    file_type=file.file_type.value,
                )
                self.graph.add_node(node.id, **node.model_dump())
                self.node_models[node.id] = node

            # Create file lookup for classes and functions
            classes, _ = self.state.db_querier.get_all_classes()
            functions, _ = self.state.db_querier.get_all_functions()
            class_to_file = {cls.id: cls.file_id for cls in classes}
            function_to_file = {func.id: func.file_id for func in functions}

            file_relationships: Set[Tuple[int, int]] = set()
            self.edge_models: List[EdgeModel] = []
            # Add edges using EdgeModel
            for rel in relationships:
                source_file_id: Optional[int] = None
                target_file_id: Optional[int] = None
                if rel.source_type == "class":
                    source_file_id = class_to_file.get(rel.source_id)
                elif rel.source_type == "function":
                    source_file_id = function_to_file.get(rel.source_id)
                if rel.target_type == "class":
                    target_file_id = class_to_file.get(rel.target_id)
                elif rel.target_type == "function":
                    target_file_id = function_to_file.get(rel.target_id)
                if (
                    source_file_id is not None
                    and target_file_id is not None
                    and source_file_id != target_file_id
                    and (source_file_id, target_file_id) not in file_relationships
                ):
                    edge = EdgeModel(
                        source=source_file_id,
                        target=target_file_id,
                        relationship_type=rel.relationship_type.value,
                        alpha=0.5,
                    )
                    self.graph.add_edge(
                        edge.source,
                        edge.target,
                        relationship_type=edge.relationship_type,
                        alpha=edge.alpha,
                        weight=1,
                    )
                    self.edge_models.append(edge)
                    file_relationships.add((source_file_id, target_file_id))

            logger.info(
                f"Created graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges"
            )
        except Exception as e:
            logger.error(f"Error setting up graph: {e}")
            self.graph = nx.DiGraph()  # Empty graph as fallback

    def calculate_layout(
        self, algorithm: str = "spring"
    ) -> Dict[int, Tuple[float, float]]:
        """
        Calculate node positions using the specified layout algorithm.

        Args:
            algorithm (str): The layout algorithm to use ('spring', 'circular', 'hierarchical', 'force_atlas').

        Returns:
            Dict[int, Tuple[float, float]]: Mapping of node IDs to (x, y) positions.
        """
        if not self.graph or self.graph.number_of_nodes() == 0:
            return {}

        try:
            pos: Mapping[Any, Any] = {}
            if algorithm == "spring":
                pos = nx.spring_layout(self.graph, k=3, iterations=50)
            elif algorithm == "circular":
                pos = nx.circular_layout(self.graph)
            elif algorithm == "hierarchical":
                try:
                    import networkx.drawing.nx_agraph as nx_agraph

                    pos = nx_agraph.graphviz_layout(self.graph, prog="dot")
                except ImportError:
                    logger.warning(
                        "pygraphviz not installed, falling back to spring layout."
                    )
                    pos = nx.spring_layout(self.graph)
            elif algorithm == "force_atlas":
                pos = nx.spring_layout(self.graph, k=5, iterations=100)
            else:
                pos = nx.spring_layout(self.graph)

            scale_factor = 1000
            pos_dict: Dict[int, Tuple[float, float]] = {
                int(node): (float(x) * scale_factor, float(y) * scale_factor)
                for node, (x, y) in pos.items()
            }
            return pos_dict

        except Exception as e:
            logger.error(f"Error calculating layout: {e}")
            pos = nx.circular_layout(self.graph)
            return {int(node): (float(x), float(y)) for node, (x, y) in pos.items()}

    def create_node_data(self) -> ColumnDataSource:
        """Create Bokeh data source for nodes."""
        """
        Create Bokeh data source for nodes.

        Returns:
            ColumnDataSource: Bokeh data source containing node attributes.
        """
        if not self.graph:
            return ColumnDataSource(data={})

        self.pos = self.calculate_layout(str(self.layout_algorithm))

        degree_centrality: Dict[int, float] = nx.degree_centrality(self.graph)
        betweenness_centrality: Dict[int, float] = nx.betweenness_centrality(self.graph)
        closeness_centrality: Dict[int, float] = nx.closeness_centrality(self.graph)

        node_data = NodeDataModel()
        domain_colors_model = (
            getattr(self.settings.network_graph, "domain_colors_model", None)
            if self.settings
            and hasattr(self.settings.network_graph, "domain_colors_model")
            else DomainColorsModel()
        )
        domain_colors = domain_colors_model.as_dict()

        for node_id, node_model in self.node_models.items():
            node_data.id.append(node_model.id)
            node_data.x.append(self.pos.get(node_model.id, (0, 0))[0])
            node_data.y.append(self.pos.get(node_model.id, (0, 0))[1])
            node_data.name.append(node_model.name)
            node_data.path.append(node_model.path)
            node_data.domain.append(node_model.domain)
            node_data.complexity.append(node_model.complexity)
            node_data.lines_of_code.append(node_model.lines_of_code)
            node_data.classes_count.append(node_model.classes_count)
            node_data.functions_count.append(node_model.functions_count)
            node_data.file_type.append(node_model.file_type)

            degree: int = self.graph.degree(node_model.id)  # type: ignore
            node_data.degree.append(degree)
            node_data.degree_centrality.append(degree_centrality.get(node_model.id, 0))
            node_data.betweenness_centrality.append(
                betweenness_centrality.get(node_model.id, 0)
            )
            node_data.closeness_centrality.append(
                closeness_centrality.get(node_model.id, 0)
            )

            if self.node_size_metric == "degree":
                size: int = max(10, min(50, degree * 3))
            elif self.node_size_metric == "complexity":
                size = max(10, min(50, int(node_model.complexity) // 2))
            elif self.node_size_metric == "lines_of_code":
                size = max(10, min(50, node_model.lines_of_code // 20))
            else:
                size = 15

            node_data.size.append(size)
            node_data.color.append(domain_colors.get(node_model.domain, "#BDC3C7"))

        return ColumnDataSource(data=node_data.model_dump())

    def create_edge_data(self) -> ColumnDataSource:
        """Create Bokeh data source for edges."""
        """
        Create Bokeh data source for edges.

        Returns:
            ColumnDataSource: Bokeh data source containing edge attributes.
        """
        if not self.graph or not self.pos:
            return ColumnDataSource(data={})

        edge_data = EdgeDataModel()
        rel_alpha_model = (
            getattr(self.settings.network_graph, "relationship_type_alpha_model", None)
            if self.settings
            and hasattr(self.settings.network_graph, "relationship_type_alpha_model")
            else RelationshipTypeAlphaModel()
        )
        rel_colors = rel_alpha_model.as_dict()

        for edge_model in self.edge_models:
            if (
                self.edge_filter != "all"
                and edge_model.relationship_type != self.edge_filter
            ):
                continue
            source_pos: Tuple[float, float] = self.pos.get(edge_model.source, (0, 0))
            target_pos: Tuple[float, float] = self.pos.get(edge_model.target, (0, 0))
            edge_data.xs.append([source_pos[0], target_pos[0]])
            edge_data.ys.append([source_pos[1], target_pos[1]])
            edge_data.source.append(edge_model.source)
            edge_data.target.append(edge_model.target)
            edge_data.relationship_type.append(edge_model.relationship_type)
            edge_data.alpha.append(rel_colors.get(edge_model.relationship_type, 0.5))

        return ColumnDataSource(data=edge_data.model_dump())

    def create_figure(self) -> figure:
        """Create the main Bokeh figure for the network graph."""
        # Create figure
        p = figure(
            width=1200,
            height=800,
            title="Code Relationship Network Graph",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="above",
        )

        # Create data sources
        self.node_source = self.create_node_data()
        self.edge_source = self.create_edge_data()

        # Add edges
        edges = p.multi_line(
            "xs",
            "ys",
            source=self.edge_source,
            line_color="gray",
            line_alpha="alpha",
            line_width=1,
        )

        # Add nodes
        nodes = p.scatter(
            "x",
            "y",
            source=self.node_source,
            size="size",
            color="color",
            alpha=0.8,
            line_color="white",
            line_width=2,
        )

        # Add labels if enabled
        if self.show_labels:
            labels = LabelSet(
                x="x",
                y="y",
                text="name",
                source=self.node_source,
                text_font_size="8pt",
                text_color="black",
                text_align="center",
                text_baseline="middle",
            )
            p.add_layout(labels)

        # Add hover tool
        hovertips_model = (
            getattr(self.settings.network_graph, "hovertips_model", None)
            if self.settings and hasattr(self.settings.network_graph, "hovertips_model")
            else HoverTooltipsModel()
        )
        hover = HoverTool(
            tooltips=hovertips_model.tooltips,
            renderers=[nodes],
        )
        p.add_tools(hover)

        # Add tap tool for selection
        tap = TapTool(renderers=[nodes])
        p.add_tools(tap)

        # Style the plot
        p.title.text_font_size = "16pt"
        p.title.align = "center"
        p.grid.visible = False
        p.axis.visible = False

        return p

    def create_controls(self) -> pn.Column:
        """Create control widgets for the network graph."""
        # Layout algorithm selector
        layout_select = pn.widgets.Select(
            name="Layout Algorithm",
            value=self.layout_algorithm,
            options=["spring", "circular", "hierarchical", "force_atlas"],
            width=200,
        )

        # Node size metric selector
        size_metric_select = pn.widgets.Select(
            name="Node Size Metric",
            value=self.node_size_metric,
            options=["degree", "complexity", "lines_of_code", "uniform"],
            width=200,
        )

        # Edge filter selector
        edge_filter_options_model = EdgeFilterOptionsModel()
        if (
            self.settings
            and hasattr(self.settings, "network_graph")
            and hasattr(self.settings.network_graph, "edge_filter_options_model")
            and self.settings.network_graph.edge_filter_options_model is not None
        ):
            edge_filter_options_model = (
                self.settings.network_graph.edge_filter_options_model
            )
        edge_filter_select = pn.widgets.Select(
            name="Edge Filter",
            value=self.edge_filter,
            options=edge_filter_options_model.options,
            width=200,
        )

        # Show labels checkbox
        labels_checkbox = pn.widgets.Checkbox(
            name="Show Labels", value=self.show_labels, width=100
        )

        # Update button
        update_button = pn.widgets.Button(
            name="Update Graph", button_type="primary", width=150
        )

        # Bind callbacks
        def update_graph(event: param.parameterized.Event) -> None:
            self.layout_algorithm = layout_select.value
            self.node_size_metric = size_metric_select.value
            self.edge_filter = edge_filter_select.value
            self.show_labels = labels_checkbox.value

            # Recreate the figure
            if self.viewable_pane:
                self.viewable_pane.object = self.create_figure()

        update_button.on_click(update_graph)

        # Graph statistics
        stats_html = self.create_graph_statistics()

        return pn.Column(
            "## Network Graph Controls",
            pn.Row(layout_select, size_metric_select),
            pn.Row(edge_filter_select, labels_checkbox),
            update_button,
            "## Graph Statistics",
            stats_html,
            width=300,
        )

    def create_graph_statistics(self) -> pn.pane.HTML:
        """Create HTML panel with graph statistics using external template."""
        if not self.graph:
            return pn.pane.HTML("<p>No graph data available</p>")

        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()
        density = nx.density(self.graph)
        degrees = dict(self.graph.degree())
        top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        top_nodes_info = []
        for node_id, degree in top_nodes:
            node_attrs = self.graph.nodes.get(node_id, {})
            name = node_attrs.get("name", f"Node {node_id}")
            top_nodes_info.append(f"{name} ({degree})")

        # Determine template path from config if available
        template_path = None
        if self.settings and hasattr(self.settings, "network_graph"):
            template_path = getattr(
                self.settings.network_graph, "graph_statistics_template_path", None
            )
        # Fallback to default if not set
        if not template_path:
            template_path = "d:/VS Code Projects/USASpendingv4/code-intelligence-dashboard/dashboard/components/templates/graph_statistics.html"

        # Use manager to generate HTML string synchronously, then wrap in pane
        stats_html_str = GraphStatisticsManager.render_html_sync(
            num_nodes=num_nodes,
            num_edges=num_edges,
            density=density,
            top_nodes_info=top_nodes_info,
            template_path=template_path,
        )
        return pn.pane.HTML(stats_html_str)

    def view(self) -> pn.Row:
        """Return the complete network graph view."""
        # Create the figure
        self.figure = self.create_figure()

        # Create controls
        controls = self.create_controls()

        # Create the main view
        self.viewable_pane = pn.pane.Bokeh(self.figure, sizing_mode="stretch_both")

        return pn.Row(
            controls, self.viewable_pane, sizing_mode="stretch_width", height=850
        )
