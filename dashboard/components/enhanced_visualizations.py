#!/usr/bin/env python3
"""
Enhanced Visualization Components
Modern, polished visualizations using Altair and Plotly with USWDS styling.
"""

import logging
from typing import Any, Dict, List, Optional, Union

import altair as alt
import pandas as pd
import panel as pn
import param
import plotly.express as px
import plotly.graph_objects as go
from dashboard.dashboard_logging import get_logger
from plotly.subplots import make_subplots

logger = get_logger(__name__)

# USWDS Color Palette
USWDS_COLORS = {
    "primary": "#005ea2",
    "primary_dark": "#1a4480",
    "primary_light": "#73b3e7",
    "secondary": "#fa9441",
    "success": "#00a91c",
    "warning": "#ffbe2e",
    "error": "#d63031",
    "info": "#2491eb",
    "base": "#1b1b1b",
    "base_light": "#71767a",
    "white": "#ffffff",
    "gray_5": "#f0f0f0",
    "gray_10": "#e6e6e6",
    "gray_20": "#c9c9c9",
    "gray_30": "#adadad",
    "gray_50": "#757575",
    "gray_70": "#454545",
    "gray_90": "#1b1b1b",
}

# Government-appropriate color schemes
DOMAIN_COLORS = [
    USWDS_COLORS["primary"],
    USWDS_COLORS["secondary"],
    USWDS_COLORS["success"],
    USWDS_COLORS["warning"],
    USWDS_COLORS["info"],
    USWDS_COLORS["error"],
    USWDS_COLORS["primary_light"],
    USWDS_COLORS["base_light"],
]


class EnhancedVisualizationComponent(param.Parameterized):
    """
    Enhanced visualization component with modern styling and interactions.
    """

    def __init__(self, state: Any, **params: Any) -> None:
        """Initialize the enhanced visualization component."""
        super().__init__(**params)
        self.state = state
        self._setup_altair_theme()
        self._setup_plotly_theme()

    def _setup_altair_theme(self) -> None:
        """Configure Altair with USWDS theme."""
        alt.data_transformers.enable("json")

        # Custom USWDS theme for Altair
        uswds_theme = {
            "config": {
                "view": {
                    "continuousWidth": 400,
                    "continuousHeight": 300,
                    "stroke": "transparent",
                },
                "axis": {
                    "domainColor": USWDS_COLORS["gray_30"],
                    "gridColor": USWDS_COLORS["gray_10"],
                    "tickColor": USWDS_COLORS["gray_30"],
                    "labelColor": USWDS_COLORS["base"],
                    "titleColor": USWDS_COLORS["base"],
                    "labelFont": "Source Sans Pro",
                    "titleFont": "Source Sans Pro",
                    "labelFontSize": 12,
                    "titleFontSize": 14,
                    "titleFontWeight": "bold",
                },
                "legend": {
                    "labelColor": USWDS_COLORS["base"],
                    "titleColor": USWDS_COLORS["base"],
                    "labelFont": "Source Sans Pro",
                    "titleFont": "Source Sans Pro",
                    "labelFontSize": 11,
                    "titleFontSize": 12,
                },
                "title": {
                    "color": USWDS_COLORS["base"],
                    "font": "Merriweather",
                    "fontSize": 16,
                    "fontWeight": "bold",
                    "anchor": "start",
                },
                "range": {"category": DOMAIN_COLORS, "ordinal": DOMAIN_COLORS},
            }
        }

        alt.themes.register("uswds", lambda: uswds_theme)
        alt.themes.enable("uswds")

    def _setup_plotly_theme(self) -> None:
        """Configure Plotly with USWDS theme."""
        self.plotly_template = {
            "layout": {
                "font": {
                    "family": "Source Sans Pro, sans-serif",
                    "size": 12,
                    "color": USWDS_COLORS["base"],
                },
                "title": {
                    "font": {
                        "family": "Merriweather, serif",
                        "size": 16,
                        "color": USWDS_COLORS["base"],
                    },
                    "x": 0.02,
                    "xanchor": "left",
                },
                "paper_bgcolor": USWDS_COLORS["white"],
                "plot_bgcolor": USWDS_COLORS["white"],
                "colorway": DOMAIN_COLORS,
                "xaxis": {
                    "gridcolor": USWDS_COLORS["gray_10"],
                    "linecolor": USWDS_COLORS["gray_30"],
                    "tickcolor": USWDS_COLORS["gray_30"],
                    "title": {"font": {"size": 14, "color": USWDS_COLORS["base"]}},
                },
                "yaxis": {
                    "gridcolor": USWDS_COLORS["gray_10"],
                    "linecolor": USWDS_COLORS["gray_30"],
                    "tickcolor": USWDS_COLORS["gray_30"],
                    "title": {"font": {"size": 14, "color": USWDS_COLORS["base"]}},
                },
            }
        }

    def create_domain_distribution_chart(self) -> Union[pn.pane.HTML, pn.pane.Plotly]:
        """Create modern domain distribution chart with Altair."""
        try:
            if not self.state.system_stats or not getattr(
                self.state.system_stats, "domains", None
            ):
                return self._create_no_data_message("No domain data available")

            domains = self.state.system_stats.domains

            # Prepare data
            data = []
            for d in domains:
                domain_name = (
                    getattr(d.domain, "value", str(d.domain)).replace("_", " ").title()
                )
                file_count = getattr(d, "files_count", 0)
                data.append(
                    {
                        "domain": domain_name,
                        "file_count": file_count,
                        "percentage": 0,  # Will calculate below
                    }
                )

            df = pd.DataFrame(data)
            total_files = df["file_count"].sum()
            df["percentage"] = (df["file_count"] / total_files * 100).round(1)

            # Create Altair chart
            chart = (
                alt.Chart(df)
                .mark_bar(
                    cornerRadiusTopLeft=3,
                    cornerRadiusTopRight=3,
                    stroke=USWDS_COLORS["white"],
                    strokeWidth=1,
                )
                .encode(
                    x=alt.X(
                        "domain:N",
                        sort="-y",
                        title="Domain",
                        axis=alt.Axis(labelAngle=-45),
                    ),
                    y=alt.Y("file_count:Q", title="Number of Files"),
                    color=alt.Color(
                        "domain:N", scale=alt.Scale(range=DOMAIN_COLORS), legend=None
                    ),
                    tooltip=[
                        alt.Tooltip("domain:N", title="Domain"),
                        alt.Tooltip("file_count:Q", title="Files"),
                        alt.Tooltip("percentage:Q", title="Percentage", format=".1f"),
                    ],
                )
                .properties(
                    width=500,
                    height=350,
                    title=alt.TitleParams(
                        text="Files by Domain",
                        subtitle="Distribution of code files across architectural domains",
                    ),
                )
                .resolve_scale(color="independent")
            )

            # Add value labels on bars
            text = (
                alt.Chart(df)
                .mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-5,
                    fontSize=11,
                    fontWeight="bold",
                    color=USWDS_COLORS["base"],
                )
                .encode(
                    x=alt.X("domain:N", sort="-y"),
                    y=alt.Y("file_count:Q"),
                    text=alt.Text("file_count:Q"),
                )
            )

            final_chart = (chart + text).resolve_scale(color="independent")

            return pn.pane.Vega(final_chart, sizing_mode="stretch_width")

        except Exception as e:
            logger.error(f"Error creating domain distribution chart: {e}")
            return self._create_error_message(f"Error creating domain chart: {e}")

    def create_complexity_distribution_chart(
        self,
    ) -> Union[pn.pane.HTML, pn.pane.Plotly]:
        """Create modern complexity distribution chart with Plotly."""
        try:
            if not self.state.system_stats or not getattr(
                self.state.system_stats, "complexity_distribution", None
            ):
                return self._create_no_data_message("No complexity data available")

            complexity_dist = self.state.system_stats.complexity_distribution

            # Prepare data
            data = []
            for item in complexity_dist:
                complexity_level = (
                    getattr(item.complexity, "value", str(item.complexity))
                    .replace("_", " ")
                    .title()
                )
                file_count = getattr(item, "files_count", 0)
                data.append({"complexity": complexity_level, "file_count": file_count})

            df = pd.DataFrame(data)
            total_files = df["file_count"].sum()
            df["percentage"] = (df["file_count"] / total_files * 100).round(1)

            # Define complexity colors (green to red gradient)
            complexity_colors = {
                "Low": USWDS_COLORS["success"],
                "Medium": USWDS_COLORS["warning"],
                "High": USWDS_COLORS["secondary"],
                "Very High": USWDS_COLORS["error"],
            }

            df["color"] = df["complexity"].map(complexity_colors)

            # Create Plotly donut chart
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=df["complexity"],
                        values=df["file_count"],
                        hole=0.4,
                        marker=dict(
                            colors=df["color"],
                            line=dict(color=USWDS_COLORS["white"], width=2),
                        ),
                        textinfo="label+percent",
                        textposition="outside",
                        textfont=dict(size=12),
                        hovertemplate="<b>%{label}</b><br>"
                        + "Files: %{value}<br>"
                        + "Percentage: %{percent}<br>"
                        + "<extra></extra>",
                    )
                ]
            )

            fig.update_layout(
                template=self.plotly_template,
                title={
                    "text": "Code Complexity Distribution<br><sub>Breakdown of files by complexity level</sub>",
                    "x": 0.02,
                    "xanchor": "left",
                },
                showlegend=True,
                legend=dict(
                    orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02
                ),
                width=600,
                height=400,
                margin=dict(l=20, r=120, t=80, b=20),
            )

            # Add center text
            fig.add_annotation(
                text=f"<b>{total_files}</b><br>Total Files",
                x=0.5,
                y=0.5,
                font_size=16,
                showarrow=False,
            )

            return pn.pane.Plotly(fig, sizing_mode="stretch_width")

        except Exception as e:
            logger.error(f"Error creating complexity distribution chart: {e}")
            return self._create_error_message(f"Error creating complexity chart: {e}")

    def create_network_graph(
        self, graph_data: Dict[str, Any]
    ) -> Union[pn.pane.HTML, pn.pane.Plotly]:
        """Create interactive network graph with Plotly."""
        try:
            if not graph_data or "nodes" not in graph_data or "edges" not in graph_data:
                return self._create_no_data_message("No network data available")

            nodes = graph_data["nodes"]
            edges = graph_data["edges"]

            if not nodes:
                return self._create_no_data_message("No nodes to display")

            # Create network layout (simple circular for demo)
            import math

            n_nodes = len(nodes)
            node_positions = {}

            for i, node in enumerate(nodes):
                angle = 2 * math.pi * i / n_nodes
                x = math.cos(angle)
                y = math.sin(angle)
                node_positions[node["id"]] = (x, y)

            # Prepare edge traces
            edge_x = []
            edge_y = []

            for edge in edges:
                if (
                    edge["source"] in node_positions
                    and edge["target"] in node_positions
                ):
                    x0, y0 = node_positions[edge["source"]]
                    x1, y1 = node_positions[edge["target"]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])

            # Create edge trace
            edge_trace = go.Scatter(
                x=edge_x,
                y=edge_y,
                line=dict(width=1, color=USWDS_COLORS["gray_30"]),
                hoverinfo="none",
                mode="lines",
                name="Dependencies",
            )

            # Prepare node traces
            node_x = []
            node_y = []
            node_text = []
            node_colors = []
            node_sizes = []

            for node in nodes:
                if node["id"] in node_positions:
                    x, y = node_positions[node["id"]]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(node.get("label", node["id"]))

                    # Color by domain
                    domain = node.get("domain", "unknown")
                    domain_index = hash(domain) % len(DOMAIN_COLORS)
                    node_colors.append(DOMAIN_COLORS[domain_index])

                    # Size by degree
                    degree = node.get("degree", 1)
                    node_sizes.append(max(10, min(30, degree * 3)))

            # Create node trace
            node_trace = go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers+text",
                hoverinfo="text",
                text=node_text,
                textposition="middle center",
                textfont=dict(size=10, color=USWDS_COLORS["white"]),
                marker=dict(
                    size=node_sizes,
                    color=node_colors,
                    line=dict(width=2, color=USWDS_COLORS["white"]),
                ),
                hovertext=[
                    f"<b>{node.get('label', node['id'])}</b><br>"
                    f"Domain: {node.get('domain', 'Unknown')}<br>"
                    f"Connections: {node.get('degree', 0)}"
                    for node in nodes
                    if node["id"] in node_positions
                ],
                name="Components",
            )

            # Create figure
            fig = go.Figure(data=[edge_trace, node_trace])

            fig.update_layout(
                template=self.plotly_template,
                title={
                    "text": "Component Dependency Network<br><sub>Interactive visualization of code relationships</sub>",
                    "x": 0.02,
                    "xanchor": "left",
                },
                showlegend=False,
                hovermode="closest",
                margin=dict(b=20, l=5, r=5, t=80),
                annotations=[
                    dict(
                        text="Click and drag to explore • Hover for details",
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
                width=700,
                height=500,
            )

            return pn.pane.Plotly(fig, sizing_mode="stretch_width")

        except Exception as e:
            logger.error(f"Error creating network graph: {e}")
            return self._create_error_message(f"Error creating network graph: {e}")

    def create_complexity_heatmap(
        self, complexity_data: List[Dict[str, Any]]
    ) -> Union[pn.pane.HTML, pn.pane.Plotly]:
        """Create complexity heatmap with Plotly."""
        try:
            if not complexity_data:
                return self._create_no_data_message("No complexity data available")

            df = pd.DataFrame(complexity_data)

            # Create pivot table for heatmap
            if (
                "domain" in df.columns
                and "complexity_level" in df.columns
                and "count" in df.columns
            ):
                pivot_df = df.pivot(
                    index="complexity_level", columns="domain", values="count"
                ).fillna(0)
            else:
                return self._create_no_data_message("Invalid complexity data format")

            # Create heatmap
            fig = go.Figure(
                data=go.Heatmap(
                    z=pivot_df.values,
                    x=pivot_df.columns,
                    y=pivot_df.index,
                    colorscale=[
                        [0, USWDS_COLORS["gray_5"]],
                        [0.25, USWDS_COLORS["success"]],
                        [0.5, USWDS_COLORS["warning"]],
                        [0.75, USWDS_COLORS["secondary"]],
                        [1, USWDS_COLORS["error"]],
                    ],
                    hovertemplate="<b>%{y}</b> complexity<br>"
                    + "Domain: <b>%{x}</b><br>"
                    + "Files: <b>%{z}</b><br>"
                    + "<extra></extra>",
                    colorbar=dict(title="Number of Files", titleside="right"),
                )
            )

            fig.update_layout(
                template=self.plotly_template,
                title={
                    "text": "Complexity Distribution by Domain<br><sub>Heatmap showing complexity patterns across domains</sub>",
                    "x": 0.02,
                    "xanchor": "left",
                },
                xaxis_title="Domain",
                yaxis_title="Complexity Level",
                width=600,
                height=400,
            )

            return pn.pane.Plotly(fig, sizing_mode="stretch_width")

        except Exception as e:
            logger.error(f"Error creating complexity heatmap: {e}")
            return self._create_error_message(f"Error creating complexity heatmap: {e}")

    def create_sankey_diagram(
        self, flow_data: Dict[str, Any]
    ) -> Union[pn.pane.HTML, pn.pane.Plotly]:
        """Create Sankey diagram for dependency flows."""
        try:
            if not flow_data or "nodes" not in flow_data or "links" not in flow_data:
                return self._create_no_data_message("No flow data available")

            nodes = flow_data["nodes"]
            links = flow_data["links"]

            # Create Sankey diagram
            fig = go.Figure(
                data=[
                    go.Sankey(
                        node=dict(
                            pad=15,
                            thickness=20,
                            line=dict(color=USWDS_COLORS["gray_30"], width=0.5),
                            label=[node["label"] for node in nodes],
                            color=[
                                DOMAIN_COLORS[i % len(DOMAIN_COLORS)]
                                for i in range(len(nodes))
                            ],
                        ),
                        link=dict(
                            source=links["source"],
                            target=links["target"],
                            value=links["value"],
                            color=[USWDS_COLORS["gray_20"]] * len(links["source"]),
                        ),
                    )
                ]
            )

            fig.update_layout(
                template=self.plotly_template,
                title={
                    "text": "Dependency Flow Diagram<br><sub>Sankey visualization of component dependencies</sub>",
                    "x": 0.02,
                    "xanchor": "left",
                },
                font_size=12,
                width=800,
                height=500,
            )

            return pn.pane.Plotly(fig, sizing_mode="stretch_width")

        except Exception as e:
            logger.error(f"Error creating Sankey diagram: {e}")
            return self._create_error_message(f"Error creating Sankey diagram: {e}")

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

    def create_polished_card_container(
        self,
        title: str,
        content: Any,
        subtitle: Optional[str] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
    ) -> pn.pane.HTML:
        """Create a polished card container with proper USWDS styling."""

        subtitle_html = (
            f'<p class="usa-card__subtitle">{subtitle}</p>' if subtitle else ""
        )

        actions_html = ""
        if actions:
            action_buttons = []
            for action in actions:
                button_class = action.get("class", "usa-button usa-button--outline")
                button_text = action.get("text", "Action")
                button_onclick = action.get("onclick", "")
                action_buttons.append(
                    f'<button class="{button_class}" onclick="{button_onclick}">{button_text}</button>'
                )
            actions_html = (
                f'<div class="usa-card__actions">{" ".join(action_buttons)}</div>'
            )

        card_html = f"""
        <div class="usa-card usa-card--header-first" style="margin: 1rem 0;">
            <div class="usa-card__container">
                <div class="usa-card__header">
                    <h3 class="usa-card__heading">{title}</h3>
                    {subtitle_html}
                </div>
                <div class="usa-card__body">
                    <div class="visualization-container">
                        {content if isinstance(content, str) else '<!-- Content will be inserted here -->'}
                    </div>
                </div>
                {actions_html}
            </div>
        </div>
        """

        return pn.pane.HTML(card_html, sizing_mode="stretch_width")
