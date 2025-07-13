#!/usr/bin/env python3
"""
Class Diagram and UML Visualization Component

This module provides interactive class diagrams, inheritance hierarchies,
and UML-style visualizations for code structure analysis.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import networkx as nx
import pandas as pd
import panel as pn
import param
from bokeh.layouts import column, row
from bokeh.models import (
    Arrow,
    ColumnDataSource,
    HoverTool,
    Line,
    Rect,
    TapTool,
    Text,
    VeeHead,
)
from bokeh.palettes import Category20, Set3
from bokeh.plotting import figure
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


from dashboard.models.dashboard_models import ClassNodeModel


class ClassDiagramComponent(param.Parameterized):
    """Interactive class diagram component with inheritance visualization."""

    selected_file_id = param.Integer(default=None, allow_None=True)
    show_methods = param.Boolean(default=True)
    show_attributes = param.Boolean(default=True)
    show_inheritance = param.Boolean(default=True)
    diagram_type = param.String(default="inheritance")  # inheritance, composition, full

    def __init__(self, state: Any, **params: Any) -> None:
        super().__init__(**params)
        self.state = state
        self.classes_data = []
        self.inheritance_graph = None
        self.load_class_data()

    def load_class_data(self) -> None:
        """Load class data from database."""
        try:
            # Get all classes with their relationships
            classes, _ = self.state.db_querier.get_all_classes()
            functions, _ = self.state.db_querier.get_all_functions()

            # Group functions by class
            class_methods: Dict[int, List[Any]] = {}
            for func in functions:
                if func.class_id:
                    if func.class_id not in class_methods:
                        class_methods[func.class_id] = []
                    class_methods[func.class_id].append(func)

            # Process classes
            self.classes_data: List[ClassNodeModel] = []
            for cls in classes:
                methods = class_methods.get(cls.id, [])
                node = ClassNodeModel(
                    id=cls.id,
                    name=cls.name,
                    file_id=cls.file_id,
                    file_path=cls.file_path,
                    base_classes=cls.base_classes or [],
                    is_pydantic_model=cls.is_pydantic_model,
                    methods=methods,
                    method_count=len(methods),
                    complexity=sum(getattr(m, "complexity", 0) for m in methods),
                    is_abstract=any(
                        "abc" in str(base).lower() for base in (cls.base_classes or [])
                    ),
                    docstring=getattr(cls, "docstring", "") or "",
                )
                self.classes_data.append(node)

            # Build inheritance graph
            self.build_inheritance_graph()

            logger.info(f"Loaded {len(self.classes_data)} classes")

        except Exception as e:
            logger.error(f"Error loading class data: {e}")
            self.classes_data = []

    def build_inheritance_graph(self) -> None:
        """Build NetworkX graph for inheritance relationships."""
        self.inheritance_graph = nx.DiGraph()

        # Add nodes for all classes
        for node in self.classes_data:
            self.inheritance_graph.add_node(node.name, **node.model_dump())

        # Add edges for inheritance relationships
        for node in self.classes_data:
            for base_class in node.base_classes:
                if base_class in [c.name for c in self.classes_data]:
                    self.inheritance_graph.add_edge(base_class, node.name)

    def create_inheritance_diagram(self) -> Union[pn.pane.Bokeh, pn.pane.HTML]:
        """Create inheritance hierarchy diagram."""
        if not self.inheritance_graph:
            return pn.pane.HTML("<p>No inheritance data available</p>")

        try:
            # Calculate hierarchical layout
            pos = nx.nx_agraph.graphviz_layout(self.inheritance_graph, prog="dot")
        except:
            # Fallback to spring layout if graphviz not available
            pos = nx.spring_layout(self.inheritance_graph, k=3, iterations=50)

        # Scale positions
        scale_factor = 100
        pos = {
            node: (x * scale_factor, y * scale_factor) for node, (x, y) in pos.items()
        }

        # Create figure
        p = figure(
            width=1000,
            height=700,
            title="Class Inheritance Hierarchy",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="above",
        )

        # Prepare node data
        node_data = {
            "x": [],
            "y": [],
            "name": [],
            "width": [],
            "height": [],
            "color": [],
            "file_path": [],
            "method_count": [],
            "is_pydantic_model": [],
            "is_abstract": [],
            "complexity": [],
        }

        colors = {
            "pydantic": "#FF6B6B",
            "abstract": "#4ECDC4",
            "regular": "#45B7D1",
            "interface": "#96CEB4",
        }

        for node in self.classes_data:
            # Position
            try:
                x, y = pos.get(node.name, (0.0, 0.0))
            except Exception:
                x, y = 0.0, 0.0
            node.x = x
            node.y = y

            # Color
            if node.is_pydantic_model:
                node.color = colors["pydantic"]
            elif node.is_abstract:
                node.color = colors["abstract"]
            else:
                node.color = colors["regular"]

            # Size
            node.width = max(80, len(node.name) * 8)
            node.height = max(40, 20 + node.method_count * 3)

            # Collect for ColumnDataSource
            node_data["x"].append(node.x)
            node_data["y"].append(node.y)
            node_data["name"].append(node.name)
            node_data["width"].append(node.width)
            node_data["height"].append(node.height)
            node_data["color"].append(node.color)
            node_data["file_path"].append(node.file_path)
            node_data["method_count"].append(node.method_count)
            node_data["is_pydantic_model"].append(node.is_pydantic_model)
            node_data["is_abstract"].append(node.is_abstract)
            node_data["complexity"].append(node.complexity)

        node_source = ColumnDataSource(data=node_data)

        # Add class boxes
        boxes = p.rect(
            x="x",
            y="y",
            width="width",
            height="height",
            source=node_source,
            fill_color="color",
            fill_alpha=0.7,
            line_color="black",
            line_width=2,
        )

        # Add class names
        p.text(
            x="x",
            y="y",
            text="name",
            source=node_source,
            text_align="center",
            text_baseline="middle",
            text_font_size="10pt",
            text_font_style="bold",
        )

        # Add inheritance arrows
        edge_data = {"x0": [], "y0": [], "x1": [], "y1": []}

        for parent, child in self.inheritance_graph.edges():
            parent_pos = pos.get(parent, (0, 0))
            child_pos = pos.get(child, (0, 0))

            edge_data["x0"].append(parent_pos[0])
            edge_data["y0"].append(parent_pos[1])
            edge_data["x1"].append(child_pos[0])
            edge_data["y1"].append(child_pos[1])

        if edge_data["x0"]:  # Only add arrows if there are edges
            edge_source = ColumnDataSource(data=edge_data)

            # Add inheritance lines
            p.segment(
                "x0",
                "y0",
                "x1",
                "y1",
                source=edge_source,
                line_color="gray",
                line_width=2,
            )

            # Add arrowheads
            p.add_layout(
                Arrow(
                    end=VeeHead(size=10, fill_color="gray"),
                    x_start="x0",
                    y_start="y0",
                    x_end="x1",
                    y_end="y1",
                    source=edge_source,
                )
            )

        # Add hover tool
        hover = HoverTool(
            tooltips=[
                ("Class", "@name"),
                ("File", "@file_path"),
                ("Methods", "@method_count"),
                ("Complexity", "@complexity"),
                ("Pydantic Model", "@is_pydantic_model"),
                ("Abstract", "@is_abstract"),
            ],
            renderers=[boxes],
        )
        p.add_tools(hover)

        # Style the plot
        p.title.text_font_size = "16pt"
        p.title.align = "center"
        p.grid.visible = False

        return pn.pane.Bokeh(p)

    def create_class_detail_view(
        self, class_name: str
    ) -> Union[pn.Column, pn.pane.HTML]:
        """Create detailed view for a specific class."""
        # Find the class
        class_info: Optional[ClassNodeModel] = None
        for node in self.classes_data:
            if node.name == class_name:
                class_info = node
                break

        if not class_info:
            return pn.pane.HTML(f"<p>Class '{class_name}' not found</p>")

        # Create detailed class diagram
        detail_html = f"""
        <div style="border: 2px solid #333; border-radius: 8px; padding: 20px; margin: 10px; background: white;">
            <div style="background: #f0f0f0; padding: 10px; margin: -20px -20px 15px -20px; border-radius: 6px 6px 0 0;">
                <h3 style="margin: 0; text-align: center;">{class_info.name}</h3>
                <p style="margin: 5px 0 0 0; text-align: center; font-size: 12px; color: #666;">
                    {class_info.file_path}
                </p>
            </div>
            
            <div style="margin-bottom: 15px;">
                <h4>Class Information</h4>
                <ul>
                    <li><strong>Pydantic Model:</strong> {'Yes' if class_info.is_pydantic_model else 'No'}</li>
                    <li><strong>Abstract:</strong> {'Yes' if class_info.is_abstract else 'No'}</li>
                    <li><strong>Base Classes:</strong> {', '.join(class_info.base_classes) if class_info.base_classes else 'None'}</li>
                    <li><strong>Method Count:</strong> {class_info.method_count}</li>
                    <li><strong>Total Complexity:</strong> {class_info.complexity}</li>
                </ul>
            </div>
            
            {f'<div style="margin-bottom: 15px;"><h4>Documentation</h4><p>{class_info.docstring}</p></div>' if class_info.docstring else ''}
            
            <div>
                <h4>Methods</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Method</th>
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Parameters</th>
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Complexity</th>
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Type</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for method in class_info.methods:
            method_type = "Async" if getattr(method, "is_async", False) else "Sync"
            method_name = getattr(method, "name", "Unknown")
            if method_name.startswith("__") and method_name.endswith("__"):
                method_type += " (Magic)"
            elif method_name.startswith("_"):
                method_type += " (Private)"

            detail_html += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;">{method_name}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{getattr(method, 'parameter_count', 0)}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{getattr(method, 'complexity', 0)}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{method_type}</td>
                        </tr>
            """

        detail_html += """
                    </tbody>
                </table>
            </div>
        </div>
        """

        return pn.pane.HTML(detail_html)

    def create_class_browser(self) -> pn.Column:
        """Create a browser for selecting and viewing classes."""
        # Create class selection widget
        class_options = [
            (f"{node.name} ({node.file_path})", node.name) for node in self.classes_data
        ]

        class_select = pn.widgets.Select(
            name="Select Class", options=class_options, width=400
        )

        # Create detail view pane
        detail_pane = pn.pane.HTML("<p>Select a class to view details</p>")

        def update_detail_view(event: Any) -> None:
            if event.new:
                result = self.create_class_detail_view(str(event.new))
                if hasattr(result, "object"):
                    detail_pane.object = result.object
                else:
                    detail_pane.object = str(result)

        class_select.param.watch(update_detail_view, "value")

        return pn.Column(
            "## Class Browser", class_select, detail_pane, sizing_mode="stretch_width"
        )

    def create_pydantic_model_analysis(self) -> Union[pn.Column, pn.pane.HTML]:
        """Create analysis specific to Pydantic models."""
        pydantic_models = [node for node in self.classes_data if node.is_pydantic_model]

        if not pydantic_models:
            return pn.pane.HTML("<p>No Pydantic models found in the codebase</p>")

        # Create summary statistics
        total_models = len(pydantic_models)
        avg_methods = (
            sum(node.method_count for node in pydantic_models) / total_models
            if total_models > 0
            else 0
        )

        # Group by file
        models_by_file: Dict[str, List[ClassNodeModel]] = {}
        for model in pydantic_models:
            file_path = model.file_path
            if file_path not in models_by_file:
                models_by_file[file_path] = []
            models_by_file[file_path].append(model)

        # Create HTML summary
        summary_html = f"""
        <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 10px 0;">
            <h3>Pydantic Model Analysis</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div>
                    <h4 style="color: #0066cc;">Total Models</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 0;">{total_models}</p>
                </div>
                <div>
                    <h4 style="color: #0066cc;">Average Methods</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 0;">{avg_methods:.1f}</p>
                </div>
                <div>
                    <h4 style="color: #0066cc;">Files with Models</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 0;">{len(models_by_file)}</p>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <h4>Models by File</h4>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">File</th>
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Models</th>
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Total Methods</th>
                    </tr>
                </thead>
                <tbody>
        """

        for file_path, models in models_by_file.items():
            model_names = [model.name for model in models]
            total_methods = sum(model.method_count for model in models)

            summary_html += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 12px;">{file_path}</td>
                        <td style="border: 1px solid #ddd; padding: 12px;">{', '.join(model_names)}</td>
                        <td style="border: 1px solid #ddd; padding: 12px;">{total_methods}</td>
                    </tr>
            """

        summary_html += """
                </tbody>
            </table>
        </div>
        """

        return pn.pane.HTML(summary_html)

    def create_controls(self) -> pn.Column:
        """Create control widgets for the class diagram."""
        # Diagram type selector
        diagram_type_select = pn.widgets.Select(
            name="Diagram Type",
            value=self.diagram_type,
            options=["inheritance", "composition", "full"],
            width=200,
        )

        # Display options
        show_methods_checkbox = pn.widgets.Checkbox(
            name="Show Methods", value=self.show_methods, width=150
        )

        show_attributes_checkbox = pn.widgets.Checkbox(
            name="Show Attributes", value=self.show_attributes, width=150
        )

        show_inheritance_checkbox = pn.widgets.Checkbox(
            name="Show Inheritance", value=self.show_inheritance, width=150
        )

        # Update button
        update_button = pn.widgets.Button(
            name="Update Diagram", button_type="primary", width=150
        )

        def update_diagram(event: Any) -> None:
            self.diagram_type = str(diagram_type_select.value)
            self.show_methods = bool(show_methods_checkbox.value)
            self.show_attributes = bool(show_attributes_checkbox.value)
            self.show_inheritance = bool(show_inheritance_checkbox.value)
            # Trigger diagram update

        update_button.on_click(update_diagram)

        return pn.Column(
            "## Diagram Controls",
            diagram_type_select,
            show_methods_checkbox,
            show_attributes_checkbox,
            show_inheritance_checkbox,
            update_button,
            width=250,
        )

    def view(self) -> pn.Tabs:
        """Return the complete class diagram view."""
        # Create tabs for different views
        inheritance_tab = pn.Row(
            self.create_controls(),
            self.create_inheritance_diagram(),
            sizing_mode="stretch_width",
        )

        browser_tab = self.create_class_browser()
        pydantic_tab = self.create_pydantic_model_analysis()

        return pn.Tabs(
            ("🏗️ Inheritance Hierarchy", inheritance_tab),
            ("📋 Class Browser", browser_tab),
            ("🔧 Pydantic Models", pydantic_tab),
            dynamic=True,
            sizing_mode="stretch_width",
        )
