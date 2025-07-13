#!/usr/bin/env python3
"""
SQL Template Manager

This service provides centralized SQL query template loading and rendering.
It follows best practices by separating SQL from Python code and providing
parameterized query management.
"""

import logging
from pathlib import Path
from string import Template
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SQLTemplateManager:
    """
    Centralized SQL template management.

    This class provides methods to load SQL templates from files and render them
    with parameters, following the separation of concerns principle.
    """

    def __init__(self, sql_template_dir: Optional[Path] = None) -> None:
        """
        Initialize the SQL template manager.

        Args:
            sql_template_dir: Optional custom SQL template directory path
        """
        if sql_template_dir is None:
            # Default to sql templates directory relative to this file
            sql_template_dir = Path(__file__).parent / "sql"

        self.sql_template_dir = Path(sql_template_dir)
        self._template_cache: Dict[str, Template] = {}

        # Verify template directory exists
        if not self.sql_template_dir.exists():
            logger.warning(
                f"SQL template directory does not exist: {self.sql_template_dir}"
            )

    def load_sql_template(self, template_name: str) -> Template:
        """
        Load a SQL template from file with caching.

        Args:
            template_name: Name of the SQL template file (without .sql extension)

        Returns:
            Template object ready for rendering

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        template_path = self.sql_template_dir / f"{template_name}.sql"

        if not template_path.exists():
            raise FileNotFoundError(f"SQL template not found: {template_path}")

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()

            template = Template(content)
            self._template_cache[template_name] = template

            logger.debug(f"Loaded SQL template: {template_name}")
            return template

        except Exception as e:
            logger.error(f"Error loading SQL template {template_name}: {e}")
            raise

    def render_sql_template(self, template_name: str, **kwargs: Any) -> str:
        """
        Render a SQL template with the provided parameters.

        Args:
            template_name: Name of the SQL template to render
            **kwargs: Template variables to substitute

        Returns:
            Rendered SQL string
        """
        try:
            template = self.load_sql_template(template_name)

            # Convert None values to SQL NULL and ensure all params are strings
            sql_params: Dict[str, str] = {}
            for key, value in kwargs.items():
                if value is None:
                    sql_params[key] = "NULL"
                elif isinstance(value, str):
                    # Escape single quotes in strings
                    sql_params[key] = value.replace("'", "''")
                else:
                    # Convert non-string values to string
                    sql_params[key] = str(value)

            return template.safe_substitute(**sql_params)

        except Exception as e:
            logger.error(f"Error rendering SQL template {template_name}: {e}")
            # Return a basic error comment instead of crashing
            return f"-- Error loading SQL template: {template_name}"

    def render_files_query(
        self,
        domain: Optional[str] = None,
        file_type: Optional[str] = None,
        complexity_level: Optional[str] = None,
        min_lines: Optional[int] = None,
        max_lines: Optional[int] = None,
        search_term: Optional[str] = None,
        limit: int = 1000,
    ) -> str:
        """
        Render the files query with filters.

        Args:
            domain: Domain filter
            file_type: File type filter
            complexity_level: Complexity level filter
            min_lines: Minimum lines filter
            max_lines: Maximum lines filter
            search_term: Search term filter
            limit: Result limit

        Returns:
            Rendered SQL query
        """
        return self.render_sql_template(
            "get_files_with_filters",
            domain=domain,
            file_type=file_type,
            complexity_level=complexity_level,
            min_lines=min_lines,
            max_lines=max_lines,
            search_term=search_term,
            limit=limit,
        )

    def render_global_search_query(self, search_term: str, limit: int = 50) -> str:
        """
        Render the global search query.

        Args:
            search_term: Term to search for
            limit: Result limit

        Returns:
            Rendered SQL query
        """
        return self.render_sql_template(
            "global_search", search_term=search_term, limit=limit
        )

    def clear_cache(self) -> None:
        """Clear the SQL template cache."""
        self._template_cache.clear()
        logger.debug("SQL template cache cleared")


# Global SQL template manager instance
sql_template_manager = SQLTemplateManager()


# Convenience functions for common operations
def render_files_query(**kwargs: Any) -> str:
    """Render the files query with filters."""
    return sql_template_manager.render_files_query(**kwargs)


def render_global_search_query(search_term: str, limit: int = 50) -> str:
    """Render the global search query."""
    return sql_template_manager.render_global_search_query(search_term, limit)
