#!/usr/bin/env python3
"""
Template Management Service

This service provides centralized template loading and rendering for the dashboard.
It follows best practices by separating HTML/CSS from Python code and providing
a clean interface for template management.
"""

from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional

from ..dashboard_logging import get_logger

logger = get_logger(__name__)


class TemplateManager:
    """
    Centralized template management for the dashboard.

    This class provides methods to load HTML templates from files and render them
    with data, following the separation of concerns principle.
    """

    def __init__(self, template_dir: Optional[Path] = None) -> None:
        """
        Initialize the template manager.

        Args:
            template_dir: Optional custom template directory path
        """
        if template_dir is None:
            # Default to current templates directory (this file is already in templates/)
            template_dir = Path(__file__).parent

        self.template_dir = Path(template_dir)
        self._template_cache: Dict[str, Template] = {}

        # Verify template directory exists
        if not self.template_dir.exists():
            logger.warning(f"Template directory does not exist: {self.template_dir}")

    def load_template(self, template_name: str) -> Template:
        """
        Load a template from file with caching.

        Args:
            template_name: Name of the template file (without .html extension)

        Returns:
            Template object ready for rendering

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        template_path = self.template_dir / f"{template_name}.html"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()

            template = Template(content)
            self._template_cache[template_name] = template

            logger.debug(f"Loaded template: {template_name}")
            return template

        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            raise

    def render_template(self, template_name: str, **kwargs: Any) -> str:
        """
        Render a template with the provided data.

        Args:
            template_name: Name of the template to render
            **kwargs: Template variables to substitute

        Returns:
            Rendered HTML string
        """
        try:
            template = self.load_template(template_name)
            return template.safe_substitute(**kwargs)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            # Return a basic error message instead of crashing
            return f"<p>Error loading template: {template_name}</p>"

    def render_component(self, component_name: str, **kwargs: Any) -> str:
        """
        Render a component template from the components subdirectory.

        Args:
            component_name: Name of the component template
            **kwargs: Template variables to substitute

        Returns:
            Rendered HTML string
        """
        component_path = f"components/{component_name}"
        return self.render_template(component_path, **kwargs)

    def render_stats_card(self, value: int, label: str, color: str = "blue") -> str:
        """
        Render a statistics card with the provided data.

        Args:
            value: Numeric value to display
            label: Label for the statistic
            color: Color theme (blue, green, yellow, red)

        Returns:
            Rendered HTML for the stats card
        """
        # Format the value with commas for better readability
        formatted_value = (
            f"{value:,}" if isinstance(value, (int, float)) else str(value)
        )

        return self.render_component(
            "stats_card", value=formatted_value, label=label, color=color
        )

    def render_search_results_section(
        self, section_title: str, items: List[Dict[str, Any]]
    ) -> str:
        """
        Render a search results section with items.

        Args:
            section_title: Title for the section (e.g., "Files")
            items: List of result items with name, path, details keys

        Returns:
            Rendered HTML for the search results section
        """
        # Render individual items
        rendered_items = []
        for item in items[:10]:  # Limit to 10 items
            item_html = self.render_component(
                "search_result_item",
                name=item.get("name", "Unknown"),
                path=item.get("path", ""),
                details=item.get("details", ""),
            )
            rendered_items.append(item_html)

        items_html = "\n".join(rendered_items)

        return self.render_component(
            "search_results_section",
            section_title=section_title,
            count=len(items),
            items=items_html,
        )

    def get_css_path(self) -> Path:
        """
        Get the path to the CSS file.

        Returns:
            Path to the dashboard CSS file
        """
        return self.template_dir / "dashboard.css"

    def get_css_content(self) -> str:
        """
        Get the CSS content as a string.

        Returns:
            CSS content for embedding in HTML
        """
        css_path = self.get_css_path()
        if css_path.exists():
            try:
                with open(css_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error loading CSS: {e}")
                return ""
        return ""

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._template_cache.clear()
        logger.debug("Template cache cleared")


# Global template manager instance
template_manager = TemplateManager()


# Convenience functions for common operations
def render_header() -> str:
    """Render the dashboard header."""
    return template_manager.render_template("header")


def render_footer() -> str:
    """Render the dashboard footer."""
    return template_manager.render_template("footer")


def render_error_page(error: str, db_path: str) -> str:
    """Render the error page with error details."""
    return template_manager.render_template("error_page", error=error, db_path=db_path)


def render_stats_card(value: int, label: str, color: str = "blue") -> str:
    """Render a statistics card."""
    return template_manager.render_stats_card(value, label, color)


def render_search_results_section(
    section_title: str, items: List[Dict[str, Any]]
) -> str:
    """Render a search results section."""
    return template_manager.render_search_results_section(section_title, items)
