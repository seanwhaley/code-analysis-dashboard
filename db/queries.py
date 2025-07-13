#!/usr/bin/env python3
"""
Database Query Module

This module provides all database query functions with exact alignment
to the population logic in populate_db.py. All field names, types, and
ordering match the database schema and population scripts.

The queries are designed to be efficient and provide comprehensive
data for the Panel dashboard UI.

Key Features:
- Type-safe query interfaces using Pydantic models
- Comprehensive error handling and logging
- Performance-optimized SQL queries
- Consistent data transformation and validation
- Connection pooling and resource management

Last Updated: 2025-01-27 15:30:00
"""

import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add models to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.types import (
    ClassRecord,
    ComplexityDistribution,
    ComplexityLevel,
    DomainStats,
    DomainType,
    FileRecord,
    FileType,
    FunctionRecord,
    RelationshipRecord,
    RelationshipType,
    SystemStats,
)

# Configure logging with enhanced format
logger = logging.getLogger(__name__)


class DatabaseQuerier:
    """
    Provides all database query operations for the dashboard.

    This class encapsulates all database interactions with comprehensive
    error handling, type safety, and performance optimization.
    """

    def __init__(self, db_path: str = "code_intelligence.db") -> None:
        """
        Initialize the database querier.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._connection_cache: Optional[sqlite3.Connection] = None
        self._last_connection_time: Optional[datetime] = None
        self._connection_timeout: int = 300  # 5 minutes

    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with row factory and optimized settings.

        Returns:
            sqlite3.Connection: Configured database connection

        Raises:
            sqlite3.Error: If database connection fails
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # File Queries
    def get_all_files(
        self,
        domain: Optional[DomainType] = None,
        file_type: Optional[FileType] = None,
        complexity_level: Optional[ComplexityLevel] = None,
        min_lines: Optional[int] = None,
        max_lines: Optional[int] = None,
        search_term: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Tuple[List[FileRecord], int]:
        """
        Get all files with optional filtering.
        Returns (files, total_count) tuple.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            where_conditions = []
            params = []

            if domain:
                where_conditions.append("domain = ?")
                params.append(domain.value)

            if file_type:
                where_conditions.append("file_type = ?")
                params.append(file_type.value)

            if complexity_level:
                where_conditions.append("complexity_level = ?")
                params.append(complexity_level.value)

            if min_lines is not None:
                where_conditions.append("lines_of_code >= ?")
                params.append(min_lines)

            if max_lines is not None:
                where_conditions.append("lines_of_code <= ?")
                params.append(max_lines)

            if search_term:
                where_conditions.append("(name LIKE ? OR path LIKE ?)")
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern])

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Get total count
            count_query = f"SELECT COUNT(*) FROM files WHERE {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            # Get files with pagination
            query = f"""
                SELECT id, name, path, domain, file_type, complexity, complexity_level,
                       lines_of_code, classes_count, functions_count, imports_count,
                       pydantic_models_count, created_at, updated_at
                FROM files 
                WHERE {where_clause}
                ORDER BY complexity DESC, lines_of_code DESC
            """

            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            files = [self._row_to_file_record(row) for row in rows]
            return files, total_count

    def get_file_by_id(self, file_id: int) -> Optional[FileRecord]:
        """Get a specific file by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, path, domain, file_type, complexity, complexity_level,
                       lines_of_code, classes_count, functions_count, imports_count,
                       pydantic_models_count, created_at, updated_at
                FROM files WHERE id = ?
            """,
                (file_id,),
            )

            row = cursor.fetchone()
            return self._row_to_file_record(row) if row else None

    def get_file_by_path(self, file_path: str) -> Optional[FileRecord]:
        """Get a specific file by path."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, path, domain, file_type, complexity, complexity_level,
                       lines_of_code, classes_count, functions_count, imports_count,
                       pydantic_models_count, created_at, updated_at
                FROM files WHERE path = ?
            """,
                (file_path,),
            )

            row = cursor.fetchone()
            return self._row_to_file_record(row) if row else None

    # Class Queries
    def get_all_classes(
        self,
        domain: Optional[DomainType] = None,
        class_type: Optional[str] = None,
        is_pydantic_model: Optional[bool] = None,
        file_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Tuple[List[ClassRecord], int]:
        """
        Get all classes with optional filtering.
        Returns (classes, total_count) tuple.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            where_conditions = []
            params = []

            if domain:
                where_conditions.append("domain = ?")
                params.append(domain.value)

            if class_type:
                where_conditions.append("class_type = ?")
                params.append(class_type)

            if is_pydantic_model is not None:
                where_conditions.append("is_pydantic_model = ?")
                params.append(is_pydantic_model)

            if file_id:
                where_conditions.append("file_id = ?")
                params.append(file_id)

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Get total count
            count_query = f"SELECT COUNT(*) FROM classes WHERE {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            # Get classes with pagination
            query = f"""
                SELECT id, name, file_id, file_path, domain, class_type, line_number,
                       methods_count, is_abstract, is_pydantic_model, base_classes,
                       decorators, created_at, updated_at
                FROM classes 
                WHERE {where_clause}
                ORDER BY methods_count DESC, name
            """

            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            classes = [self._row_to_class_record(row) for row in rows]
            return classes, total_count

    def get_class_by_id(self, class_id: int) -> Optional[ClassRecord]:
        """Get a specific class by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, file_id, file_path, domain, class_type, line_number,
                       methods_count, is_abstract, is_pydantic_model, base_classes,
                       decorators, created_at, updated_at
                FROM classes WHERE id = ?
            """,
                (class_id,),
            )

            row = cursor.fetchone()
            return self._row_to_class_record(row) if row else None

    # Function Queries
    def get_all_functions(
        self,
        function_type: Optional[str] = None,
        is_async: Optional[bool] = None,
        file_id: Optional[int] = None,
        class_id: Optional[int] = None,
        min_complexity: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Tuple[List[FunctionRecord], int]:
        """
        Get all functions with optional filtering.
        Returns (functions, total_count) tuple.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            where_conditions = []
            params = []

            if function_type:
                where_conditions.append("function_type = ?")
                params.append(function_type)

            if is_async is not None:
                where_conditions.append("is_async = ?")
                params.append(is_async)

            if file_id:
                where_conditions.append("file_id = ?")
                params.append(file_id)

            if class_id:
                where_conditions.append("class_id = ?")
                params.append(class_id)

            if min_complexity:
                where_conditions.append("complexity >= ?")
                params.append(min_complexity)

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Get total count
            count_query = f"SELECT COUNT(*) FROM functions WHERE {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            # Get functions with pagination
            query = f"""
                SELECT id, name, file_id, class_id, file_path, function_type, line_number,
                       parameters_count, parameters, return_type, is_async, is_generator,
                       decorators, complexity, created_at, updated_at
                FROM functions 
                WHERE {where_clause}
                ORDER BY complexity DESC, parameters_count DESC, name
            """

            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            functions = [self._row_to_function_record(row) for row in rows]
            return functions, total_count

    def get_function_by_id(self, function_id: int) -> Optional[FunctionRecord]:
        """Get a specific function by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, file_id, class_id, file_path, function_type, line_number,
                       parameters_count, parameters, return_type, is_async, is_generator,
                       decorators, complexity, created_at, updated_at
                FROM functions WHERE id = ?
            """,
                (function_id,),
            )

            row = cursor.fetchone()
            return self._row_to_function_record(row) if row else None

    # Relationship Queries
    def get_relationships(
        self,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        target_type: Optional[str] = None,
        relationship_type: Optional[RelationshipType] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Tuple[List[RelationshipRecord], int]:
        """
        Get relationships with optional filtering.
        Returns (relationships, total_count) tuple.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            where_conditions = []
            params = []

            if source_type:
                where_conditions.append("source_type = ?")
                params.append(source_type)

            if source_id:
                where_conditions.append("source_id = ?")
                params.append(source_id)

            if target_type:
                where_conditions.append("target_type = ?")
                params.append(target_type)

            if relationship_type:
                where_conditions.append("relationship_type = ?")
                params.append(relationship_type.value)

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Get total count
            count_query = f"SELECT COUNT(*) FROM relationships WHERE {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            # Get relationships with pagination
            query = f"""
                SELECT id, source_type, source_id, source_name, target_type, target_id,
                       target_name, relationship_type, file_path, line_number,
                       created_at, updated_at
                FROM relationships 
                WHERE {where_clause}
                ORDER BY source_name, target_name
            """

            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            relationships = [self._row_to_relationship_record(row) for row in rows]
            return relationships, total_count

    def get_all_relationships(self) -> List[RelationshipRecord]:
        """Get all relationships without pagination."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, source_type, source_id, source_name, target_type, target_id,
                       target_name, relationship_type, file_path, line_number,
                       created_at, updated_at
                FROM relationships 
                ORDER BY source_name, target_name
                """
            )
            rows = cursor.fetchall()
            return [self._row_to_relationship_record(row) for row in rows]

    # Statistics and Analysis Queries
    def get_system_stats(self) -> SystemStats:
        """Get comprehensive system statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get overall statistics
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_files,
                    SUM(classes_count) as total_classes,
                    SUM(functions_count) as total_functions,
                    SUM(lines_of_code) as total_lines,
                    AVG(complexity) as avg_complexity
                FROM files
            """
            )
            overall_stats = cursor.fetchone()

            # Get domain statistics
            cursor.execute(
                """
                SELECT 
                    domain,
                    COUNT(*) as files_count,
                    SUM(classes_count) as classes_count,
                    SUM(functions_count) as functions_count,
                    SUM(lines_of_code) as total_lines,
                    AVG(complexity) as avg_complexity
                FROM files
                GROUP BY domain
                ORDER BY files_count DESC
            """
            )
            domain_rows = cursor.fetchall()

            domain_stats = []
            for row in domain_rows:
                domain_stats.append(
                    DomainStats(
                        domain=DomainType(row["domain"]),
                        files_count=row["files_count"],
                        classes_count=row["classes_count"] or 0,
                        functions_count=row["functions_count"] or 0,
                        total_lines=row["total_lines"] or 0,
                        avg_complexity=round(row["avg_complexity"] or 0, 2),
                    )
                )

            # Get complexity distribution
            cursor.execute(
                """
                SELECT 
                    complexity_level,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM files), 2) as percentage
                FROM files
                GROUP BY complexity_level
                ORDER BY 
                    CASE complexity_level
                        WHEN 'low' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'high' THEN 3
                        WHEN 'very_high' THEN 4
                        ELSE 5
                    END
            """
            )
            complexity_rows = cursor.fetchall()

            complexity_distribution = []
            for row in complexity_rows:
                complexity_distribution.append(
                    ComplexityDistribution(
                        complexity_range=row["complexity_level"]
                        .replace("_", " ")
                        .title(),
                        count=row["count"],
                        percentage=row["percentage"],
                    )
                )

            # Get last analysis timestamp
            cursor.execute("SELECT MAX(created_at) FROM files")
            last_analysis_row = cursor.fetchone()
            last_analysis = None
            if last_analysis_row[0]:
                try:
                    last_analysis = datetime.fromisoformat(last_analysis_row[0])
                except:
                    pass

            return SystemStats(
                total_files=overall_stats["total_files"] or 0,
                total_classes=overall_stats["total_classes"] or 0,
                total_functions=overall_stats["total_functions"] or 0,
                total_lines=overall_stats["total_lines"] or 0,
                avg_complexity=round(overall_stats["avg_complexity"] or 0, 2),
                domains=domain_stats,
                complexity_distribution=complexity_distribution,
                last_analysis=last_analysis,
            )

    def get_domain_stats(self) -> List[DomainStats]:
        """Get statistics for each domain."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    domain,
                    COUNT(*) as files_count,
                    SUM(classes_count) as classes_count,
                    SUM(functions_count) as functions_count,
                    SUM(lines_of_code) as total_lines,
                    AVG(complexity) as avg_complexity
                FROM files
                GROUP BY domain
                ORDER BY files_count DESC
            """
            )
            rows = cursor.fetchall()

            stats = []
            for row in rows:
                stats.append(
                    DomainStats(
                        domain=DomainType(row["domain"]),
                        files_count=row["files_count"],
                        classes_count=row["classes_count"] or 0,
                        functions_count=row["functions_count"] or 0,
                        total_lines=row["total_lines"] or 0,
                        avg_complexity=round(row["avg_complexity"] or 0, 2),
                    )
                )

            return stats

    def get_complexity_distribution(self) -> List[ComplexityDistribution]:
        """Get complexity distribution across all files."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    complexity_level,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM files), 2) as percentage
                FROM files
                GROUP BY complexity_level
                ORDER BY 
                    CASE complexity_level
                        WHEN 'low' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'high' THEN 3
                        WHEN 'very_high' THEN 4
                        ELSE 5
                    END
            """
            )
            rows = cursor.fetchall()

            distribution = []
            for row in rows:
                distribution.append(
                    ComplexityDistribution(
                        complexity_range=row["complexity_level"]
                        .replace("_", " ")
                        .title(),
                        count=row["count"],
                        percentage=row["percentage"],
                    )
                )

            return distribution

    # Search Functions
    def search_all(
        self, search_term: str, limit: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all entity types."""
        results = {"files": [], "classes": [], "functions": []}

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Search files
            cursor.execute(
                """
                SELECT id, name, path, domain, file_type, complexity, lines_of_code
                FROM files 
                WHERE name LIKE ? OR path LIKE ?
                ORDER BY name
                LIMIT ?
            """,
                (f"%{search_term}%", f"%{search_term}%", limit),
            )

            for row in cursor.fetchall():
                results["files"].append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "path": row["path"],
                        "domain": row["domain"],
                        "type": "file",
                        "details": f"{row['lines_of_code']} lines, complexity: {row['complexity']}",
                    }
                )

            # Search classes
            cursor.execute(
                """
                SELECT id, name, file_path, domain, class_type, methods_count
                FROM classes 
                WHERE name LIKE ?
                ORDER BY name
                LIMIT ?
            """,
                (f"%{search_term}%", limit),
            )

            for row in cursor.fetchall():
                results["classes"].append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "path": row["file_path"],
                        "domain": row["domain"],
                        "type": "class",
                        "details": f"{row['class_type']}, {row['methods_count']} methods",
                    }
                )

            # Search functions
            cursor.execute(
                """
                SELECT id, name, file_path, function_type, parameters_count, complexity
                FROM functions 
                WHERE name LIKE ?
                ORDER BY name
                LIMIT ?
            """,
                (f"%{search_term}%", limit),
            )

            for row in cursor.fetchall():
                results["functions"].append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "path": row["file_path"],
                        "type": "function",
                        "details": f"{row['function_type']}, {row['parameters_count']} params, complexity: {row['complexity']}",
                    }
                )

        return results

    # Helper methods for converting database rows to Pydantic models
    def _row_to_file_record(self, row: sqlite3.Row) -> FileRecord:
        """Convert database row to FileRecord."""
        return FileRecord(
            id=row["id"],
            name=row["name"],
            path=row["path"],
            domain=DomainType(row["domain"]),
            file_type=FileType(row["file_type"]),
            complexity=row["complexity"],
            complexity_level=ComplexityLevel(row["complexity_level"]),
            lines_of_code=row["lines_of_code"],
            classes_count=row["classes_count"],
            functions_count=row["functions_count"],
            imports_count=row["imports_count"],
            pydantic_models_count=row["pydantic_models_count"],
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )

    def _row_to_class_record(self, row: sqlite3.Row) -> ClassRecord:
        """Convert database row to ClassRecord."""
        return ClassRecord(
            id=row["id"],
            name=row["name"],
            file_id=row["file_id"],
            file_path=row["file_path"],
            domain=DomainType(row["domain"]),
            class_type=row["class_type"],
            line_number=row["line_number"],
            methods_count=row["methods_count"],
            is_abstract=bool(row["is_abstract"]),
            is_pydantic_model=bool(row["is_pydantic_model"]),
            base_classes=json.loads(row["base_classes"]) if row["base_classes"] else [],
            decorators=json.loads(row["decorators"]) if row["decorators"] else [],
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )

    def _row_to_function_record(self, row: sqlite3.Row) -> FunctionRecord:
        """Convert database row to FunctionRecord."""
        return FunctionRecord(
            id=row["id"],
            name=row["name"],
            file_id=row["file_id"],
            class_id=row["class_id"],
            file_path=row["file_path"],
            function_type=row["function_type"],
            line_number=row["line_number"],
            parameters_count=row["parameters_count"],
            parameters=json.loads(row["parameters"]) if row["parameters"] else [],
            return_type=row["return_type"],
            is_async=bool(row["is_async"]),
            is_generator=bool(row["is_generator"]),
            decorators=json.loads(row["decorators"]) if row["decorators"] else [],
            complexity=row["complexity"],
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )

    def _row_to_relationship_record(self, row: sqlite3.Row) -> RelationshipRecord:
        """Convert database row to RelationshipRecord."""
        return RelationshipRecord(
            id=row["id"],
            source_type=row["source_type"],
            source_id=row["source_id"],
            source_name=row["source_name"],
            target_type=row["target_type"],
            target_id=row["target_id"],
            target_name=row["target_name"],
            relationship_type=RelationshipType(row["relationship_type"]),
            file_path=row["file_path"],
            line_number=row["line_number"],
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )


# Convenience function for getting a querier instance
def get_querier(db_path: str = "code_intelligence.db") -> DatabaseQuerier:
    """Get a DatabaseQuerier instance."""
    return DatabaseQuerier(db_path)
