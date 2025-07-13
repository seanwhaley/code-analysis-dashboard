"""
Dashboard services package.

This package contains all service classes for the dashboard submodule,
providing clean separation between business logic and presentation layers.

**Last Updated:** 2025-01-27 15:30:00
"""

from .base_service import BaseService, timing_decorator
from .statistics_service import StatisticsService
from .template_service import TemplateService

__all__ = ["BaseService", "timing_decorator", "StatisticsService", "TemplateService"]
