#!/usr/bin/env python3
"""
Dashboard Database Service Layer

Centralized database access patterns with consistent error handling,
logging, and type safety. Follows USASpending service patterns.

**Last Updated:** 2025-07-11 15:30:00
"""

from typing import Any, Dict, Optional

from dashboard.dashboard_logging import get_logger
from dashboard.models.dashboard_models import DatabaseQueryResult

logger = get_logger(__name__)


class DashboardDatabaseService:
    """
    Centralized database service for dashboard operations.

    Provides consistent database access patterns, error handling,
    and result formatting for all dashboard components.
    """

    def __init__(self, db_querier: Any) -> None:
        """Initialize with database querier instance."""
        self.db_querier = db_querier

    def safe_query_files(
        self,
        domain: Optional[Any] = None,
        file_type: Optional[Any] = None,
        complexity_level: Optional[Any] = None,
        min_lines: Optional[int] = None,
        max_lines: Optional[int] = None,
        search_term: Optional[str] = None,
        limit: int = 1000,
    ) -> DatabaseQueryResult:
        """
        Safe file query with consistent error handling.

        Args:
            domain: Domain filter (enum or None)
            file_type: File type filter (enum or None)
            complexity_level: Complexity level filter (enum or None)
            min_lines: Minimum lines filter
            max_lines: Maximum lines filter
            search_term: Search term filter
            limit: Query limit

        Returns:
            DatabaseQueryResult with typed data and error info
        """
        try:
            if hasattr(self.db_querier, "get_all_files"):
                result = self.db_querier.get_all_files(
                    domain=domain,
                    file_type=file_type,
                    complexity_level=complexity_level,
                    min_lines=min_lines,
                    max_lines=max_lines,
                    search_term=search_term,
                    limit=limit,
                )

                # Handle different return formats
                if isinstance(result, tuple):
                    data, total_count = result
                    return DatabaseQueryResult(
                        data=data or [], total_count=total_count or 0, success=True
                    )
                else:
                    return DatabaseQueryResult(
                        data=result or [],
                        total_count=len(result) if result else 0,
                        success=True,
                    )

            else:
                logger.warning("Database querier missing get_all_files method")
                return DatabaseQueryResult(
                    success=False,
                    error_message="Database querier not properly configured",
                )

        except Exception as e:
            logger.error(f"Database query error in safe_query_files: {e}")
            return DatabaseQueryResult(success=False, error_message=str(e))

    def safe_query_classes(self, limit: int = 1000) -> DatabaseQueryResult:
        """Safe class query with consistent error handling."""
        try:
            if hasattr(self.db_querier, "get_all_classes"):
                result = self.db_querier.get_all_classes()

                if isinstance(result, tuple):
                    data, total_count = result
                    return DatabaseQueryResult(
                        data=data or [], total_count=total_count or 0, success=True
                    )
                else:
                    return DatabaseQueryResult(
                        data=result or [],
                        total_count=len(result) if result else 0,
                        success=True,
                    )
            else:
                return DatabaseQueryResult(
                    success=False,
                    error_message="Database querier missing get_all_classes method",
                )

        except Exception as e:
            logger.error(f"Database query error in safe_query_classes: {e}")
            return DatabaseQueryResult(success=False, error_message=str(e))

    def safe_query_functions(self, limit: int = 1000) -> DatabaseQueryResult:
        """Safe function query with consistent error handling."""
        try:
            if hasattr(self.db_querier, "get_all_functions"):
                result = self.db_querier.get_all_functions()

                if isinstance(result, tuple):
                    data, total_count = result
                    return DatabaseQueryResult(
                        data=data or [], total_count=total_count or 0, success=True
                    )
                else:
                    return DatabaseQueryResult(
                        data=result or [],
                        total_count=len(result) if result else 0,
                        success=True,
                    )
            else:
                return DatabaseQueryResult(
                    success=False,
                    error_message="Database querier missing get_all_functions method",
                )

        except Exception as e:
            logger.error(f"Database query error in safe_query_functions: {e}")
            return DatabaseQueryResult(success=False, error_message=str(e))

    def safe_search_all(self, search_term: str, limit: int = 50) -> Dict[str, Any]:
        """
        Safe search across all entities.

        Args:
            search_term: Term to search for
            limit: Maximum results per category

        Returns:
            Dictionary with search results by category
        """
        try:
            if hasattr(self.db_querier, "search_all"):
                result = self.db_querier.search_all(search_term, limit=limit)
                return result if isinstance(result, dict) else {}
            else:
                logger.warning("Database querier missing search_all method")
                return {"files": [], "classes": [], "functions": []}

        except Exception as e:
            logger.error(f"Database search error: {e}")
            return {"files": [], "classes": [], "functions": []}

    def safe_get_system_stats(self) -> Optional[Any]:
        """Safe system statistics query."""
        try:
            if hasattr(self.db_querier, "get_system_stats"):
                return self.db_querier.get_system_stats()
            else:
                logger.warning("Database querier missing get_system_stats method")
                return None

        except Exception as e:
            logger.error(f"System stats query error: {e}")
            return None
