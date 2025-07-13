"""
Template service for the dashboard submodule.

This module provides template loading, rendering, and management functionality
for HTML templates used throughout the dashboard.

**Last Updated:** 2025-01-27 15:30:00
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from jinja2 import Environment, FileSystemLoader, Template

from ..dashboard_logging import get_logger
from .base_service import BaseService, timing_decorator


class TemplateService(BaseService):
    """
    Service for managing and rendering HTML templates.

    Provides methods for:
    - Loading and caching templates
    - Rendering templates with context
    - Template validation and error handling
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the template service.

        Args:
            template_dir: Optional directory path for templates
        """
        super().__init__("TemplateService")
        self.template_dir = template_dir or Path(__file__).parent.parent / "templates"
        self.env: Optional[Environment] = None
        self._template_cache: Dict[str, Template] = {}

    async def _initialize_impl(self) -> None:
        """Initialize the template service with Jinja2 environment."""
        self.logger.debug(
            f"Initializing template environment with directory: {self.template_dir}"
        )

        try:
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True,
                enable_async=True,
                cache_size=100,  # Cache compiled templates
            )

            # Add common template functions/filters if needed
            self.env.globals["len"] = len
            self.env.globals["enumerate"] = enumerate

            self.logger.info(f"Template environment initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize template environment: {str(e)}")
            raise

    @timing_decorator
    async def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """
        Asynchronously loads and renders a Jinja2 template.

        Args:
            template_path: The path to the HTML template file
            context: A dictionary of context variables for rendering

        Returns:
            The rendered HTML string

        Raises:
            FileNotFoundError: If template file cannot be found
            Exception: If template rendering fails
        """
        self.logger.debug(
            f"Rendering template: {template_path}",
            extra={
                "template_path": template_path,
                "context_keys": list(context.keys()),
            },
        )

        if not self.env:
            await self.initialize()

        try:
            path = Path(template_path)

            # Check if this is an absolute path or relative to template_dir
            if path.is_absolute():
                # Load template from absolute path
                async with aiofiles.open(
                    template_path, mode="r", encoding="utf-8"
                ) as f:
                    template_str = await f.read()
                template = Template(template_str, enable_async=True)
                rendered = await template.render_async(context)
            else:
                # Load template using Jinja2 environment
                template = self.env.get_template(template_path)
                rendered = await template.render_async(context)

            self.logger.debug(
                f"Template rendered successfully: {template_path}",
                extra={
                    "template_path": template_path,
                    "rendered_length": len(rendered),
                },
            )

            return rendered

        except FileNotFoundError as e:
            error_msg = f"Template file not found: {template_path}"
            self.logger.error(
                error_msg,
                extra={
                    "template_path": template_path,
                    "template_dir": str(self.template_dir),
                },
            )
            return f"<div class='error'><h3>Error loading template {template_path}</h3><p>{error_msg}</p></div>"

        except Exception as e:
            error_msg = f"Error rendering template: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "template_path": template_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return f"<div class='error'><h3>Error loading template {template_path}</h3><p>{error_msg}</p></div>"

    def render_template_sync(self, template_path: str, context: Dict[str, Any]) -> str:
        """
        Synchronously loads and renders a Jinja2 template.

        Args:
            template_path: The path to the HTML template file
            context: A dictionary of context variables for rendering

        Returns:
            The rendered HTML string
        """
        try:
            from pathlib import Path

            from jinja2 import Environment, FileSystemLoader, Template

            path = Path(template_path)

            if path.is_absolute():
                # Load template from absolute path
                template_content = path.read_text(encoding="utf-8")
                template = Template(template_content)
                return template.render(**context)
            else:
                # Use environment loader for relative paths
                if not hasattr(self, "_sync_env") or self._sync_env is None:
                    self._sync_env = Environment(
                        loader=FileSystemLoader(str(self.template_dir)),
                        autoescape=True,
                    )
                    self._sync_env.globals["len"] = len
                    self._sync_env.globals["enumerate"] = enumerate

                template = self._sync_env.get_template(template_path)
                return template.render(**context)

        except Exception as e:
            error_msg = f"Error rendering template: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "template_path": template_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return f"<div class='error'><h3>Error loading template {template_path}</h3><p>{error_msg}</p></div>"

    @timing_decorator
    async def render_template_string(
        self, template_string: str, context: Dict[str, Any]
    ) -> str:
        """
        Render a template from a string instead of a file.

        Args:
            template_string: The template content as a string
            context: A dictionary of context variables for rendering

        Returns:
            The rendered HTML string
        """
        self.logger.debug(
            "Rendering template from string",
            extra={
                "template_length": len(template_string),
                "context_keys": list(context.keys()),
            },
        )

        try:
            template = Template(template_string, enable_async=True)
            rendered = await template.render_async(context)

            self.logger.debug(
                "Template string rendered successfully",
                extra={"rendered_length": len(rendered)},
            )

            return rendered

        except Exception as e:
            error_msg = f"Error rendering template string: {str(e)}"
            self.logger.error(
                error_msg, extra={"error": str(e), "error_type": type(e).__name__}
            )
            return f"<div class='error'><h3>Template Error</h3><p>{error_msg}</p></div>"

    @timing_decorator
    async def validate_template(self, template_path: str) -> Dict[str, Any]:
        """
        Validate that a template exists and can be loaded.

        Args:
            template_path: Path to the template file

        Returns:
            Dictionary containing validation results
        """
        self.logger.debug(f"Validating template: {template_path}")

        try:
            path = Path(template_path)

            if path.is_absolute():
                exists = path.exists()
                readable = path.is_file() if exists else False
            else:
                # Check if template exists in template directory
                full_path = self.template_dir / template_path
                exists = full_path.exists()
                readable = full_path.is_file() if exists else False

            if exists and readable:
                # Try to load the template
                if not self.env:
                    await self.initialize()

                if path.is_absolute():
                    async with aiofiles.open(
                        template_path, mode="r", encoding="utf-8"
                    ) as f:
                        content = await f.read()
                    template = Template(content)
                else:
                    template = self.env.get_template(template_path)

                result = {
                    "valid": True,
                    "exists": True,
                    "readable": True,
                    "template_path": template_path,
                    "message": "Template is valid",
                }
            else:
                result = {
                    "valid": False,
                    "exists": exists,
                    "readable": readable,
                    "template_path": template_path,
                    "message": f"Template not found or not readable: {template_path}",
                }

            self.logger.debug(
                f"Template validation complete: {template_path}", extra=result
            )

            return result

        except Exception as e:
            result = {
                "valid": False,
                "exists": False,
                "readable": False,
                "template_path": template_path,
                "message": f"Template validation error: {str(e)}",
                "error": str(e),
            }

            self.logger.error(
                f"Template validation failed: {template_path}", extra=result
            )

            return result

    @timing_decorator
    async def list_templates(self) -> List[str]:
        """
        List all available templates in the template directory.

        Returns:
            List of template file paths relative to template directory
        """
        self.logger.debug(f"Listing templates in: {self.template_dir}")

        try:
            templates = []

            if self.template_dir.exists():
                for template_file in self.template_dir.rglob("*.html"):
                    relative_path = template_file.relative_to(self.template_dir)
                    templates.append(str(relative_path))

                templates.sort()

            self.logger.debug(
                f"Found {len(templates)} templates",
                extra={
                    "template_count": len(templates),
                    "templates": templates[:10],
                },  # Log first 10
            )

            return templates

        except Exception as e:
            self.logger.error(
                f"Error listing templates: {str(e)}",
                extra={"template_dir": str(self.template_dir)},
            )
            return []

    async def clear_cache(self) -> None:
        """Clear the template cache."""
        self.logger.debug("Clearing template cache")
        self._template_cache.clear()

        if self.env:
            self.env.cache.clear()

        self.logger.info("Template cache cleared")
