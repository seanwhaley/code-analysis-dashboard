#!/usr/bin/env python3
"""
Dashboard Template Service

This service provides template rendering specifically for dashboard views,
building on the template manager with dashboard-specific functionality.
"""

from typing import Any, Dict, List, Union

from dashboard.templates.template_manager import template_manager

from ..dashboard_logging import get_logger

logger = get_logger(__name__)


class DashboardTemplateService:
    """Service for rendering dashboard-specific templates."""

    def __init__(self) -> None:
        self.template_manager = template_manager

    def render_no_data_message(self, message: str = "No data available") -> str:
        """Render a standardized no data message using USWDS alert."""
        return f"""
        <div class="usa-alert usa-alert--info" role="alert">
            <div class="usa-alert__body">
                <p class="usa-alert__text">{message}</p>
            </div>
        </div>
        """

    def render_status_message(self, message: str, status_type: str = "info") -> str:
        """
        Render a status message with appropriate USWDS alert styling.

        Args:
            message: The message to display
            status_type: Type of status (info, success, error, warning)
        """
        return f"""
        <div class="usa-alert usa-alert--{status_type}" role="alert">
            <div class="usa-alert__body">
                <p class="usa-alert__text">{message}</p>
            </div>
        </div>
        """

    def render_stats_cards_row(self, stats: Any) -> str:
        """
        Render a row of statistics cards.

        Args:
            stats: System statistics object with attributes
        """
        if not stats:
            return self.render_no_data_message("No statistics available")

        cards_html = []

        # Files card
        if hasattr(stats, "total_files"):
            cards_html.append(
                self.template_manager.render_stats_card(
                    value=getattr(stats, "total_files", 0),
                    label="Total Files",
                    color="blue",
                )
            )

        # Classes card
        if hasattr(stats, "total_classes"):
            cards_html.append(
                self.template_manager.render_stats_card(
                    value=getattr(stats, "total_classes", 0),
                    label="Total Classes",
                    color="green",
                )
            )

        # Functions card
        if hasattr(stats, "total_functions"):
            cards_html.append(
                self.template_manager.render_stats_card(
                    value=getattr(stats, "total_functions", 0),
                    label="Total Functions",
                    color="yellow",
                )
            )

        # Lines of code card
        if hasattr(stats, "total_lines"):
            cards_html.append(
                self.template_manager.render_stats_card(
                    value=getattr(stats, "total_lines", 0),
                    label="Lines of Code",
                    color="red",
                )
            )

        return '<div class="dashboard-stats-grid">' + "".join(cards_html) + "</div>"

    def render_search_results(self, results: Dict[str, Any], search_term: str) -> str:
        """
        Render complete search results.

        Args:
            results: Search results dictionary
            search_term: The search term used
        """
        if not isinstance(results, dict):
            return self.render_no_data_message(f"No results found for '{search_term}'")

        total_results = sum(
            len(v) if isinstance(v, list) else 0 for v in results.values()
        )

        if total_results == 0:
            return self.render_no_data_message(f"No results found for '{search_term}'")

        sections_html = []

        # Files section
        if "files" in results and isinstance(results["files"], list):
            sections_html.append(
                self.template_manager.render_search_results_section(
                    "Files", results["files"]
                )
            )

        # Classes section
        if "classes" in results and isinstance(results["classes"], list):
            sections_html.append(
                self.template_manager.render_search_results_section(
                    "Classes", results["classes"]
                )
            )

        # Functions section
        if "functions" in results and isinstance(results["functions"], list):
            sections_html.append(
                self.template_manager.render_search_results_section(
                    "Functions", results["functions"]
                )
            )

        header = f'<h3>Search Results for "{search_term}" ({total_results} total)</h3>'
        return (
            header + '<div class="search-results">' + "".join(sections_html) + "</div>"
        )

    def render_analysis_status(self, status: str, message: str) -> str:
        """
        Render analysis status with appropriate styling.

        Args:
            status: Status type (started, completed, error)
            message: Status message
        """
        status_map = {"started": "info", "completed": "success", "error": "error"}

        status_type = status_map.get(status, "info")
        return self.render_status_message(message, status_type)


# Global instance
dashboard_template_service = DashboardTemplateService()
