#!/usr/bin/env python3
"""
Dependency Flow Visualization Component

This module provides a Sankey-like diagram to visualize dependency flows
between different domains within the codebase.
"""

from typing import Any, Dict, List, Optional, Tuple

import panel as pn
from bokeh.plotting import figure
from dashboard.dashboard_logging import get_logger
from param import Parameterized

logger = get_logger(__name__)


class DependencyFlowComponent(Parameterized):
    """Component for visualizing dependency flows and architectural layers."""

    def __init__(self, state: Any, **params: Any) -> None:
        """
        Initialize the DependencyFlowComponent.

        Args:
            state (Any): The application state object, containing db_querier.
            **params (Any): Keyword arguments for the parent class.
        """
        super().__init__(**params)
        self.state = state

    def create_sankey_diagram(self) -> pn.pane.Bokeh:
        """
        Create a Sankey-like diagram showing dependency flows between domains.

        Returns:
            pn.pane.Bokeh: Bokeh pane with the flow diagram, or HTML pane on error.
        """
        try:
            relationships = self.state.db_querier.get_all_relationships()
            files_list, _ = self.state.db_querier.get_all_files(limit=1000)
            files = {f.id: f for f in files_list}
            classes, _ = self.state.db_querier.get_all_classes()
            functions, _ = self.state.db_querier.get_all_functions()
            class_to_file: Dict[int, int] = {cls.id: cls.file_id for cls in classes}
            function_to_file: Dict[int, int] = {
                func.id: func.file_id for func in functions
            }

            domain_flows: Dict[Tuple[str, str], int] = {}
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
                ):
                    source_file = files.get(source_file_id)
                    target_file = files.get(target_file_id)
                    if source_file and target_file:
                        source_domain = getattr(source_file.domain, "value", "unknown")
                        target_domain = getattr(target_file.domain, "value", "unknown")
                        if source_domain != target_domain:
                            key = (source_domain, target_domain)
                            domain_flows[key] = domain_flows.get(key, 0) + 1

            p = figure(
                width=800,
                height=600,
                title="Domain Dependency Flows",
                tools="pan,wheel_zoom,reset,save",
            )

            domains: List[str] = list(
                set(
                    [d for d, _ in domain_flows.keys()]
                    + [d for _, d in domain_flows.keys()]
                )
            )
            domain_positions: Dict[str, int] = {
                domain: i for i, domain in enumerate(domains)
            }

            for (source, target), count in domain_flows.items():
                if count > 0:
                    source_pos = domain_positions[source]
                    target_pos = domain_positions[target]
                    p.line(
                        [source_pos, target_pos],
                        [0, 1],
                        line_width=max(1, count // 5),
                        line_alpha=0.6,
                        color="blue",
                    )

            p.text(
                x=list(range(len(domains))),
                y=[0] * len(domains),
                text=domains,
                text_align="center",
                text_baseline="middle",
            )
            p.text(
                x=list(range(len(domains))),
                y=[1] * len(domains),
                text=domains,
                text_align="center",
                text_baseline="middle",
            )

            p.grid.visible = False
            p.axis.visible = False

            return pn.pane.Bokeh(p)
        except Exception as e:
            logger.error(f"Error creating Sankey diagram: {e}")
            return pn.pane.HTML(f"<p>Error creating dependency flow diagram: {e}</p>")

    def view(self) -> pn.Column:
        """Return the dependency flow view."""
        return pn.Column(
            "## Dependency Flow Analysis",
            self.create_sankey_diagram(),
            sizing_mode="stretch_width",
        )
