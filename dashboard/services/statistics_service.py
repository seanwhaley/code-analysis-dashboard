"""
Statistics service for the dashboard submodule.

This module provides statistics calculation and rendering functionality
for graph metrics and system performance data.

**Last Updated:** 2025-01-27 15:30:00
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from jinja2 import Template

from ..dashboard_logging import get_logger
from .base_service import BaseService, timing_decorator


class StatisticsService(BaseService):
    """
    Service for calculating and rendering statistics for graphs and system metrics.

    Provides methods for:
    - Graph statistics calculation
    - HTML rendering of statistics
    - Performance metrics aggregation
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the statistics service.

        Args:
            template_dir: Optional directory path for templates
        """
        super().__init__("StatisticsService")
        self.template_dir = (
            template_dir or Path(__file__).parent.parent / "components" / "templates"
        )

    async def _initialize_impl(self) -> None:
        """Initialize the statistics service."""
        self.logger.debug("Statistics service initialization complete")

    @timing_decorator
    async def render_graph_statistics_html(
        self,
        num_nodes: int,
        num_edges: int,
        density: float,
        top_nodes_info: List[str],
        template_path: Optional[str] = None,
    ) -> str:
        """
        Render HTML for graph statistics using external template file.

        Args:
            num_nodes: Number of nodes in the graph
            num_edges: Number of edges in the graph
            density: Graph density value
            top_nodes_info: List of information about top nodes
            template_path: Optional path to custom template file

        Returns:
            Rendered HTML string for statistics display

        Raises:
            FileNotFoundError: If template file cannot be found
            Exception: If template rendering fails
        """
        self.logger.debug(
            "Rendering graph statistics HTML",
            extra={
                "num_nodes": num_nodes,
                "num_edges": num_edges,
                "density": density,
                "top_nodes_count": len(top_nodes_info),
            },
        )

        # Use default template path if not provided
        if template_path is None:
            template_path = str(self.template_dir / "graph_statistics.html")

        try:
            async with aiofiles.open(template_path, mode="r", encoding="utf-8") as f:
                template_str = await f.read()

            template = Template(template_str)
            html = template.render(
                num_nodes=num_nodes,
                num_edges=num_edges,
                density=f"{density:.4f}",
                top_nodes_info=top_nodes_info,
            )

            self.logger.debug(
                "Graph statistics HTML rendered successfully",
                extra={"template_path": template_path},
            )

            return html

        except FileNotFoundError as e:
            error_msg = f"Template file not found: {template_path}"
            self.logger.error(error_msg, extra={"template_path": template_path})
            return f"<div class='graph-stats'><h3>Error loading statistics</h3><p>{error_msg}</p></div>"

        except Exception as e:
            error_msg = f"Error rendering statistics template: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "template_path": template_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return f"<div class='graph-stats'><h3>Error loading statistics</h3><p>{error_msg}</p></div>"

    @timing_decorator
    async def calculate_graph_metrics(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive graph metrics.

        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries

        Returns:
            Dictionary containing calculated metrics
        """
        self.logger.debug(
            "Calculating graph metrics",
            extra={"node_count": len(nodes), "edge_count": len(edges)},
        )

        num_nodes = len(nodes)
        num_edges = len(edges)

        # Calculate density (edges / max_possible_edges)
        max_possible_edges = num_nodes * (num_nodes - 1) / 2
        density = num_edges / max_possible_edges if max_possible_edges > 0 else 0.0

        # Calculate node degrees
        node_degrees = {}
        for edge in edges:
            source = edge.get("source", edge.get("source_id"))
            target = edge.get("target", edge.get("target_id"))

            node_degrees[source] = node_degrees.get(source, 0) + 1
            node_degrees[target] = node_degrees.get(target, 0) + 1

        # Find top nodes by degree
        top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:5]

        metrics = {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "density": density,
            "avg_degree": (
                sum(node_degrees.values()) / len(node_degrees) if node_degrees else 0
            ),
            "max_degree": max(node_degrees.values()) if node_degrees else 0,
            "min_degree": min(node_degrees.values()) if node_degrees else 0,
            "top_nodes": top_nodes,
        }

        self.logger.debug(
            "Graph metrics calculated",
            extra={"metrics": {k: v for k, v in metrics.items() if k != "top_nodes"}},
        )

        return metrics

    @timing_decorator
    async def aggregate_system_statistics(
        self, files_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate system-wide statistics from file data.

        Args:
            files_data: List of file data dictionaries

        Returns:
            Dictionary containing aggregated system statistics
        """
        self.logger.debug(
            "Aggregating system statistics", extra={"files_count": len(files_data)}
        )

        total_files = len(files_data)
        total_lines = sum(file_data.get("lines_of_code", 0) for file_data in files_data)
        total_classes = sum(
            file_data.get("classes_count", 0) for file_data in files_data
        )
        total_functions = sum(
            file_data.get("functions_count", 0) for file_data in files_data
        )

        # Aggregate by domain
        domain_stats = {}
        complexity_stats = {}

        for file_data in files_data:
            domain = file_data.get("domain", "unknown")
            complexity = file_data.get("complexity", 0)

            if domain not in domain_stats:
                domain_stats[domain] = {
                    "files": 0,
                    "lines": 0,
                    "classes": 0,
                    "functions": 0,
                }

            domain_stats[domain]["files"] += 1
            domain_stats[domain]["lines"] += file_data.get("lines_of_code", 0)
            domain_stats[domain]["classes"] += file_data.get("classes_count", 0)
            domain_stats[domain]["functions"] += file_data.get("functions_count", 0)

            # Complexity buckets
            if complexity < 5:
                bucket = "low"
            elif complexity < 15:
                bucket = "medium"
            else:
                bucket = "high"

            complexity_stats[bucket] = complexity_stats.get(bucket, 0) + 1

        statistics = {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "avg_lines_per_file": total_lines / total_files if total_files > 0 else 0,
            "avg_classes_per_file": (
                total_classes / total_files if total_files > 0 else 0
            ),
            "avg_functions_per_file": (
                total_functions / total_files if total_files > 0 else 0
            ),
            "domain_stats": domain_stats,
            "complexity_distribution": complexity_stats,
        }

        self.logger.info(
            "System statistics aggregated",
            extra={
                "total_files": total_files,
                "total_lines": total_lines,
                "domains": list(domain_stats.keys()),
            },
        )

        return statistics
