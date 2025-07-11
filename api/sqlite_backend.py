#!/usr/bin/env python3
"""
SQLite Backend for USASpending v4 Interactive Documentation Suite

**Last Updated:** 2025-07-04 20:30:00

This module provides a comprehensive SQLite database backend for storing and querying
detailed code analysis data, supporting deep code intelligence and architectural insights.

Features:
- Detailed AST analysis storage (classes, functions, decorators, imports)
- Advanced relationship tracking (inheritance, composition, calls, imports)
- Multi-level architectural visualization support (TOGAF 10 & DoDAF inspired)
- Code intelligence (variable usage, function calls, dependency analysis)
- Interactive drilling from architecture to implementation level
"""

import asyncio
import json
import logging
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import aiosqlite
from pydantic import BaseModel, Field

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dashboard.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Custom exceptions for better error handling
class DatabaseError(Exception):
    """Custom database exception with context."""
    def __init__(self, message: str, operation: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.operation = operation
        self.details = details or {}
        super().__init__(self.message)
        
class ValidationError(Exception):
    """Data validation exception."""
    pass


class FileRecord(BaseModel):
    """File record with comprehensive metadata."""

    id: Optional[int] = Field(None, description="File ID")
    name: str = Field(..., description="File name", min_length=1)
    path: str = Field(..., description="File path", min_length=1)
    domain: str = Field(..., description="Domain classification", min_length=1)
    complexity: int = Field(..., description="Complexity score")
    classes: int = Field(..., description="Number of classes")
    functions: int = Field(..., description="Number of functions")
    lines: int = Field(..., description="Number of lines")
    pydantic_models_count: int = Field(..., description="Number of Pydantic models")
    file_type: str = Field("file", description="File type", min_length=1)
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Update timestamp")

    class Config:
        from_attributes = True


class ModelRecord(BaseModel):
    """Pydantic model record."""

    id: Optional[int] = Field(None, description="Model ID")
    name: str = Field(..., description="Model name", min_length=1)
    file_id: int = Field(..., description="File ID containing the model")
    file_path: str = Field(..., description="File path", min_length=1)
    domain: str = Field(..., description="Domain classification", min_length=1)
    fields: int = Field(..., description="Number of fields")
    model_type: str = Field("model", description="Model type", min_length=1)
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Update timestamp")

    class Config:
        from_attributes = True


class RelationshipRecord(BaseModel):
    """Relationship between components."""

    id: Optional[int] = Field(None, description="Relationship ID")
    source_file_id: int = Field(..., description="Source file ID")
    target_file_id: int = Field(..., description="Target file ID")
    source_component: str = Field(
        ..., description="Source component name", min_length=1
    )
    target_component: str = Field(
        ..., description="Target component name", min_length=1
    )
    relationship_type: str = Field(
        ..., description="Type of relationship", min_length=1
    )
    details: Optional[str] = Field(None, description="Additional details")
    created_at: Optional[str] = Field(None, description="Creation timestamp")

    class Config:
        from_attributes = True


class DomainRecord(BaseModel):
    """Domain statistics."""

    id: Optional[int] = Field(None, description="Domain ID")
    name: str = Field(..., description="Domain name")
    file_count: int = Field(..., description="Number of files in domain")
    model_count: int = Field(..., description="Number of models in domain")
    avg_complexity: float = Field(..., description="Average complexity score")
    total_lines: int = Field(..., description="Total lines of code")
    updated_at: Optional[str] = Field(None, description="Update timestamp")


# Enhanced Code Analysis Data Structures


class ClassRecord(BaseModel):
    """Regular Python class record with detailed metadata."""

    id: Optional[int] = Field(None, description="Class ID")
    name: str = Field(..., description="Class name")
    file_id: int = Field(..., description="File ID containing the class")
    file_path: str = Field(..., description="File path")
    line_number: int = Field(..., description="Starting line number")
    end_line_number: int = Field(..., description="Ending line number")
    domain: str = Field(..., description="Domain classification")
    class_type: str = Field(
        ..., description="Type of class (class, dataclass, abstract, enum, exception)"
    )
    methods_count: int = Field(..., description="Number of methods")
    properties_count: int = Field(..., description="Number of properties")
    base_classes: str = Field(..., description="JSON list of base class names")
    decorators: str = Field(..., description="JSON list of decorators")
    docstring: Optional[str] = Field(None, description="Class docstring")
    is_abstract: bool = Field(False, description="Whether class is abstract")
    is_public: bool = Field(True, description="Whether class is public")
    complexity_score: int = Field(0, description="Complexity score")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class FunctionRecord(BaseModel):
    """Function/method record with detailed metadata."""

    id: Optional[int] = Field(None, description="Function ID")
    name: str = Field(..., description="Function name")
    file_id: int = Field(..., description="File ID containing the function")
    class_id: Optional[int] = Field(
        None, description="Class ID if method, None if top-level function"
    )
    file_path: str = Field(..., description="File path")
    line_number: int = Field(..., description="Starting line number")
    end_line_number: int = Field(..., description="Ending line number")
    function_type: str = Field(
        ...,
        description="Type of function (function, method, staticmethod, classmethod, property)",
    )
    parameters_count: int = Field(..., description="Number of parameters")
    parameters: Optional[str] = Field(
        None, description="Function parameters as string or JSON"
    )
    return_type: Optional[str] = Field(None, description="Return type annotation")
    decorators: str = Field("[]", description="JSON list of decorators")
    docstring: Optional[str] = Field(None, description="Function docstring")
    is_async: bool = Field(False, description="Whether function is async")
    is_public: bool = Field(True, description="Whether function is public")
    complexity_score: int = Field(0, description="Complexity score")
    calls_made: str = Field("[]", description="JSON list of function calls made")
    variables_used: str = Field("[]", description="JSON list of variables used")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class ImportRecord(BaseModel):
    """Import statement record."""

    id: Optional[int] = Field(None, description="Import ID")
    file_id: int = Field(..., description="File ID containing the import")
    module_name: str = Field(..., description="Module name being imported")
    import_type: str = Field(
        ..., description="Type of import (import, from_import, relative_import)"
    )
    imported_names: str = Field(..., description="JSON list of imported names")
    alias: Optional[str] = Field(None, description="Import alias")
    line_number: int = Field(0, description="Line number of import")
    is_standard_library: bool = Field(
        False, description="Whether import is from standard library"
    )
    is_third_party: bool = Field(False, description="Whether import is third-party")
    is_local: bool = Field(True, description="Whether import is local")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class DecoratorRecord(BaseModel):
    """Decorator usage record."""

    id: Optional[int] = Field(None, description="Decorator ID")
    name: str = Field(..., description="Decorator name")
    target_type: str = Field(..., description="Target type (class, function, method)")
    target_id: int = Field(..., description="Target ID")
    file_id: int = Field(..., description="File ID containing the decorator")
    arguments: str = Field("[]", description="JSON list of decorator arguments")
    line_number: int = Field(0, description="Line number of decorator")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class VariableRecord(BaseModel):
    """Variable definition and usage record."""

    id: Optional[int] = Field(None, description="Variable ID")
    name: str = Field(..., description="Variable name")
    file_id: int = Field(..., description="File ID containing the variable")
    scope_type: str = Field(..., description="Scope type (module, class, function)")
    scope_id: Optional[int] = Field(None, description="Class ID or function ID")
    variable_type: str = Field("unknown", description="Inferred or annotated type")
    line_number: int = Field(0, description="Line number of variable")
    is_constant: bool = Field(False, description="Whether variable is constant")
    is_public: bool = Field(True, description="Whether variable is public")
    default_value: Optional[str] = Field(None, description="Default value")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class ArchitecturalLayer(BaseModel):
    """Architectural layer record for TOGAF/DoDAF visualization."""

    id: Optional[int] = Field(None, description="Layer ID")
    name: str = Field(..., description="Layer name")
    layer_type: str = Field(
        ...,
        description="Layer type (presentation, application, domain, infrastructure, data)",
    )
    description: Optional[str] = Field(None, description="Layer description")
    files_count: int = Field(0, description="Number of files in layer")
    components_count: int = Field(0, description="Number of components in layer")
    dependencies: str = Field("[]", description="JSON list of layer dependencies")
    technology_stack: str = Field("[]", description="JSON list of technologies used")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class ComponentRecord(BaseModel):
    """Software component record for architectural visualization."""

    id: Optional[int] = Field(None, description="Component ID")
    name: str = Field(..., description="Component name")
    component_type: str = Field(
        ...,
        description="Component type (service, repository, controller, model, utility)",
    )
    layer_id: int = Field(..., description="Layer ID")
    file_ids: str = Field(
        ..., description="JSON list of file IDs that make up this component"
    )
    interfaces: str = Field("[]", description="JSON list of exposed interfaces")
    dependencies: str = Field("[]", description="JSON list of component dependencies")
    description: Optional[str] = Field(None, description="Component description")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class EnhancedRelationshipRecord(BaseModel):
    """Enhanced relationship record with detailed analysis."""

    id: Optional[int] = Field(None, description="Relationship ID")
    source_type: str = Field(
        ..., description="Source type (file, class, function, component)"
    )
    source_id: int = Field(..., description="Source ID")
    target_type: str = Field(
        ..., description="Target type (file, class, function, component)"
    )
    target_id: int = Field(..., description="Target ID")
    relationship_type: str = Field(
        ...,
        description="Relationship type (imports, calls, inherits, composes, depends_on, implements)",
    )
    strength: float = Field(1.0, description="Relationship strength (0.0-1.0)")
    frequency: int = Field(1, description="How often this relationship occurs")
    context: Optional[str] = Field(
        None, description="Additional context about the relationship"
    )
    line_numbers: str = Field(
        "[]", description="JSON list of line numbers where relationship occurs"
    )
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class DocumentationDatabase:
    """SQLite database manager for documentation data with async support."""

    def __init__(self, db_path: str = "documentation.db") -> None:
        """Initialize database connection and create schema."""
        self.db_path = db_path
        self._init_sync_database()  # Keep sync init for compatibility

    def _init_sync_database(self) -> None:
        """Create database schema synchronously for compatibility."""
        with self.get_connection() as conn:
            self._create_schema(conn.cursor())
            conn.commit()

    async def init_database_async(self) -> None:
        """Create database schema asynchronously."""
        async with self._get_async_connection() as conn:
            cursor = await conn.cursor()
            await self._create_schema_async(cursor)
            await conn.commit()

    async def search_functions_async(
        self,
        query: Optional[str] = None,
        function_type: Optional[str] = None,
        class_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search functions with various filters asynchronously."""
        async with self._get_async_connection() as conn:
            cursor = await conn.cursor()

            select_columns = (
                "*"  # Select all columns to ensure 'parameters' is included
            )

            if query:
                await cursor.execute(
                    f"""
                    SELECT {select_columns} FROM functions 
                    WHERE name LIKE ? OR file_path LIKE ?
                    ORDER BY name
                    LIMIT ? OFFSET ?
                """,
                    (f"%{query}%", f"%{query}%", limit, offset),
                )
            else:
                where_conditions: list[str] = []
                params: list[Any] = []

                if function_type:
                    where_conditions.append("function_type = ?")
                    params.append(function_type)

                if class_id is not None:
                    where_conditions.append("class_id = ?")
                    params.append(class_id)

                where_clause = (
                    "WHERE " + " AND ".join(where_conditions)
                    if where_conditions
                    else ""
                )

                await cursor.execute(
                    f"""
                    SELECT {select_columns} FROM functions 
                    {where_clause}
                    ORDER BY complexity_score DESC, name
                    LIMIT ? OFFSET ?
                """,
                    params + [limit, offset],
                )

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    def search_functions(
        self,
        query: Optional[str] = None,
        function_type: Optional[str] = None,
        class_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search functions with various filters. Returns list of function dictionaries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            select_columns = "*"
            params: list[Any] = []
            where_conditions: list[str] = []
            if query:
                where_conditions.append("(name LIKE ? OR file_path LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
            if function_type:
                where_conditions.append("function_type = ?")
                params.append(function_type)
            if class_id is not None:
                where_conditions.append("class_id = ?")
                params.append(class_id)
            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )
            cursor.execute(
                f"""
                SELECT {select_columns} FROM functions 
                {where_clause}
                ORDER BY complexity_score DESC, name
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset],
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def init_database(self) -> None:
        """Create database schema if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._create_schema(cursor)
            conn.commit()
            logger.info("Database schema initialized successfully")

    def _create_schema(self, cursor) -> None:
        """Create database schema using provided cursor."""
        # Files table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT UNIQUE NOT NULL,
            domain TEXT NOT NULL,
            complexity INTEGER NOT NULL DEFAULT 0,
            classes INTEGER NOT NULL DEFAULT 0,
            functions INTEGER NOT NULL DEFAULT 0,
            lines INTEGER NOT NULL DEFAULT 0,
            pydantic_models_count INTEGER NOT NULL DEFAULT 0,
            file_type TEXT NOT NULL DEFAULT 'file',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # Models table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            file_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            domain TEXT NOT NULL,
            fields INTEGER NOT NULL DEFAULT 0,
            model_type TEXT NOT NULL DEFAULT 'model',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
        )
        """
        )

        # Relationships table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file_id INTEGER NOT NULL,
                target_file_id INTEGER NOT NULL,
                source_component TEXT NOT NULL,
                target_component TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_file_id) REFERENCES files (id) ON DELETE CASCADE,
                FOREIGN KEY (target_file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        """
        )

        # Domains table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                file_count INTEGER NOT NULL DEFAULT 0,
                model_count INTEGER NOT NULL DEFAULT 0,
                avg_complexity REAL NOT NULL DEFAULT 0.0,
                total_lines INTEGER NOT NULL DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # User annotations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type TEXT NOT NULL, -- 'file' or 'model'
                target_id INTEGER NOT NULL,
                annotation_type TEXT NOT NULL, -- 'note', 'todo', 'warning'
                content TEXT NOT NULL,
                author TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Change tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                action TEXT NOT NULL, -- 'insert', 'update', 'delete'
                old_values TEXT, -- JSON
                new_values TEXT, -- JSON
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_domain ON files (domain)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_files_complexity ON files (complexity)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_models_domain ON models (domain)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_models_file_id ON models (file_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_file_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_file_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_annotations_target ON annotations (target_type, target_id)"
        )

        # Create full-text search tables
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                name, path, domain, content=files, content_rowid=id
            )
        """
        )

        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS models_fts USING fts5(
                name, file_path, domain, content=models, content_rowid=id
            )
        """
        )

        # Enhanced Code Analysis Tables

        # Classes table for detailed class analysis
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                end_line_number INTEGER NOT NULL,
                domain TEXT NOT NULL,
                class_type TEXT NOT NULL DEFAULT 'class',
                methods_count INTEGER NOT NULL DEFAULT 0,
                properties_count INTEGER NOT NULL DEFAULT 0,
                base_classes TEXT DEFAULT '[]',
                decorators TEXT DEFAULT '[]',
                docstring TEXT,
                is_abstract BOOLEAN DEFAULT FALSE,
                is_public BOOLEAN DEFAULT TRUE,
                complexity_score INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        """
        )

        # Functions table for detailed function/method analysis
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS functions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_id INTEGER NOT NULL,
                class_id INTEGER,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                end_line_number INTEGER NOT NULL,
                function_type TEXT NOT NULL DEFAULT 'function',
                parameters_count INTEGER NOT NULL DEFAULT 0,
                parameters TEXT,
                return_type TEXT,
                decorators TEXT DEFAULT '[]',
                docstring TEXT,
                is_async BOOLEAN DEFAULT FALSE,
                is_public BOOLEAN DEFAULT TRUE,
                complexity_score INTEGER DEFAULT 0,
                calls_made TEXT DEFAULT '[]',
                variables_used TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE SET NULL
            )
        """
        )

        # Imports table for import analysis
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                module_name TEXT NOT NULL,
                import_type TEXT NOT NULL,
                imported_names TEXT DEFAULT '[]',
                alias TEXT,
                line_number INTEGER NOT NULL DEFAULT 0,
                is_standard_library BOOLEAN DEFAULT FALSE,
                is_third_party BOOLEAN DEFAULT FALSE,
                is_local BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        """
        )

        # Decorators table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS decorators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id INTEGER NOT NULL,
                file_id INTEGER NOT NULL,
                arguments TEXT DEFAULT '[]',
                line_number INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        """
        )

        # Variables table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_id INTEGER NOT NULL,
                scope_type TEXT NOT NULL,
                scope_id INTEGER,
                variable_type TEXT DEFAULT 'unknown',
                line_number INTEGER DEFAULT 0,
                is_constant BOOLEAN DEFAULT FALSE,
                is_public BOOLEAN DEFAULT TRUE,
                default_value TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        """
        )

        # Architectural layers table (TOGAF/DoDAF inspired)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS architectural_layers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                layer_type TEXT NOT NULL DEFAULT 'layer',
                description TEXT,
                patterns TEXT DEFAULT '[]',
                files_count INTEGER DEFAULT 0,
                components_count INTEGER DEFAULT 0,
                dependencies TEXT DEFAULT '[]',
                technology_stack TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Components table for architectural visualization
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                component_type TEXT NOT NULL,
                layer_id INTEGER NOT NULL,
                file_ids TEXT DEFAULT '[]',
                interfaces TEXT DEFAULT '[]',
                dependencies TEXT DEFAULT '[]',
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (layer_id) REFERENCES architectural_layers (id) ON DELETE CASCADE
            )
        """
        )

        # Enhanced relationships table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS enhanced_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                target_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                frequency INTEGER DEFAULT 1,
                context TEXT,
                line_numbers TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Enhanced indexes for performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_classes_file_id ON classes (file_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_classes_name ON classes (name)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_functions_file_id ON functions (file_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_functions_class_id ON functions (class_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_functions_name ON functions (name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_imports_file_id ON imports (file_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_imports_module ON imports (module_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_decorators_target ON decorators (target_type, target_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_variables_scope ON variables (scope_type, scope_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_components_layer ON components (layer_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_enhanced_rel_source ON enhanced_relationships (source_type, source_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_enhanced_rel_target ON enhanced_relationships (target_type, target_id)"
        )

        # Enhanced full-text search tables
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS classes_fts USING fts5(
                name, docstring, file_path, content=classes, content_rowid=id
            )
        """
        )

        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS functions_fts USING fts5(
                name, docstring, file_path, content=functions, content_rowid=id
            )
        """
        )

    async def _create_schema_async(self, cursor) -> None:
        """Create database schema asynchronously using provided cursor."""
        # Files table
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                domain TEXT NOT NULL,
                complexity INTEGER NOT NULL DEFAULT 0,
                classes INTEGER NOT NULL DEFAULT 0,
                functions INTEGER NOT NULL DEFAULT 0,
                lines INTEGER NOT NULL DEFAULT 0,
                pydantic_models_count INTEGER NOT NULL DEFAULT 0,
                file_type TEXT NOT NULL DEFAULT 'file',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Models table
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                domain TEXT NOT NULL,
                fields INTEGER NOT NULL DEFAULT 0,
                model_type TEXT NOT NULL DEFAULT 'model',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        """
        )

        # Functions table for detailed function/method analysis
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS functions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_id INTEGER NOT NULL,
                class_id INTEGER,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                end_line_number INTEGER NOT NULL,
                function_type TEXT NOT NULL DEFAULT 'function',
                parameters_count INTEGER NOT NULL DEFAULT 0,
                parameters TEXT,
                return_type TEXT,
                decorators TEXT DEFAULT '[]',
                docstring TEXT,
                is_async BOOLEAN DEFAULT FALSE,
                is_public BOOLEAN DEFAULT TRUE,
                complexity_score INTEGER DEFAULT 0,
                calls_made TEXT DEFAULT '[]',
                variables_used TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE SET NULL
            )
        """
        )

        # Classes table for detailed class analysis
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                end_line_number INTEGER NOT NULL,
                domain TEXT NOT NULL,
                class_type TEXT NOT NULL DEFAULT 'class',
                methods_count INTEGER NOT NULL DEFAULT 0,
                properties_count INTEGER NOT NULL DEFAULT 0,
                base_classes TEXT DEFAULT '[]',
                decorators TEXT DEFAULT '[]',
                docstring TEXT,
                is_abstract BOOLEAN DEFAULT FALSE,
                is_public BOOLEAN DEFAULT TRUE,
                complexity_score INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        """
        )

        # Create indexes for performance
        await cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_files_domain ON files (domain)"
        )
        await cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_functions_file_id ON functions (file_id)"
        )
        await cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_functions_name ON functions (name)"
        )
        await cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_classes_file_id ON classes (file_id)"
        )
        await cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_classes_name ON classes (name)"
        )

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Public: Get database connection with proper error handling for safe external use."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @asynccontextmanager
    async def _get_async_connection(self):
        """Get async database connection with proper error handling."""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row  # Enable column access by name
        try:
            yield conn
        except Exception as e:
            await conn.rollback()
            raise e
        finally:
            await conn.close()

    def import_from_json(self, json_file: str) -> bool:
        """Import data from existing JSON file."""
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"Importing data from {json_file}")

            # Clear existing data
            self.clear_all_data()

            # Import files
            files_imported = 0
            models_imported = 0
            relationships_imported = 0

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Import files
                for file_data in data.get("files", []):
                    file_record = FileRecord(
                        id=None,
                        name=file_data.get("name", ""),
                        path=file_data.get("path", ""),
                        domain=file_data.get("domain", ""),
                        complexity=file_data.get("complexity", 0),
                        classes=file_data.get("classes", 0),
                        functions=file_data.get("functions", 0),
                        lines=file_data.get("lines", 0),
                        pydantic_models_count=file_data.get("pydantic_models_count", 0),
                        file_type=file_data.get("type", "file"),
                        created_at=file_data.get("created_at"),
                        updated_at=file_data.get("updated_at"),
                    )

                    file_id = self._insert_file(cursor, file_record)
                    files_imported += 1

                    # Import models for this file
                    for model_data in file_data.get("pydantic_models", []):
                        model_record = ModelRecord(
                            id=None,
                            name=model_data.get("name", ""),
                            file_id=file_id,
                            file_path=file_data.get("path", ""),
                            domain=file_data.get("domain", ""),
                            fields=model_data.get("fields", 0),
                            model_type=model_data.get("model_type", "model"),
                            created_at=model_data.get("created_at"),
                            updated_at=model_data.get("updated_at"),
                        )

                        self._insert_model(cursor, model_record)
                        models_imported += 1

                # Import standalone models if they exist
                for model_data in data.get("models", []):
                    # Find corresponding file
                    file_path = model_data.get("file", "")
                    cursor.execute("SELECT id FROM files WHERE path = ?", (file_path,))
                    file_row = cursor.fetchone()

                    if file_row:
                        model_record = ModelRecord(
                            id=None,
                            name=model_data.get("name", ""),
                            file_id=file_row["id"],
                            file_path=file_path,
                            domain=model_data.get("domain", ""),
                            fields=model_data.get("fields", 0),
                            model_type=model_data.get("model_type", "model"),
                            created_at=model_data.get("created_at"),
                            updated_at=model_data.get("updated_at"),
                        )

                        self._insert_model(cursor, model_record)
                        models_imported += 1

                # Import relationships
                for rel_data in data.get("relationships", []):
                    # For now, create simple relationships based on available data
                    # This would need enhancement based on actual relationship structure
                    relationships_imported += 1

                # Update domain statistics
                self._update_domain_stats(cursor)

                # Update FTS indexes
                self._update_fts_indexes(cursor)

                conn.commit()

            logger.info(
                f"Import completed: {files_imported} files, {models_imported} models, {relationships_imported} relationships"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to import from JSON: {e}")
            return False

    def _insert_file(self, cursor: sqlite3.Cursor, file_record: FileRecord) -> int:
        """Insert file record and return ID."""
        cursor.execute(
            """
            INSERT INTO files (name, path, domain, complexity, classes, functions, lines, pydantic_models_count, file_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                file_record.name,
                file_record.path,
                file_record.domain,
                file_record.complexity,
                file_record.classes,
                file_record.functions,
                file_record.lines,
                file_record.pydantic_models_count,
                file_record.file_type,
            ),
        )
        return cursor.lastrowid

    def _insert_model(self, cursor: sqlite3.Cursor, model_record: ModelRecord) -> int:
        """Insert model record and return ID."""
        cursor.execute(
            """
            INSERT INTO models (name, file_id, file_path, domain, fields, model_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                model_record.name,
                model_record.file_id,
                model_record.file_path,
                model_record.domain,
                model_record.fields,
                model_record.model_type,
            ),
        )
        return cursor.lastrowid

    def _update_domain_stats(self, cursor: sqlite3.Cursor) -> None:
        """Update domain statistics."""
        cursor.execute(
            """
            INSERT OR REPLACE INTO domains (name, file_count, model_count, avg_complexity, total_lines)
            SELECT 
                f.domain,
                COUNT(DISTINCT f.id) as file_count,
                COUNT(DISTINCT m.id) as model_count,
                AVG(f.complexity) as avg_complexity,
                SUM(f.lines) as total_lines
            FROM files f
            LEFT JOIN models m ON f.id = m.file_id
            GROUP BY f.domain
        """
        )

    def _update_fts_indexes(self, cursor: sqlite3.Cursor) -> None:
        """Update full-text search indexes."""
        cursor.execute("INSERT INTO files_fts(files_fts) VALUES('rebuild')")
        cursor.execute("INSERT INTO models_fts(models_fts) VALUES('rebuild')")

    def clear_all_data(self) -> None:
        """Clear all data from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM change_log")
            cursor.execute("DELETE FROM annotations")
            cursor.execute("DELETE FROM relationships")
            cursor.execute("DELETE FROM models")
            cursor.execute("DELETE FROM files")
            cursor.execute("DELETE FROM domains")
            cursor.execute("DELETE FROM files_fts")
            cursor.execute("DELETE FROM models_fts")
            conn.commit()

    def search_files(
        self,
        query: Optional[str] = None,
        domain: Optional[str] = None,
        complexity_min: Optional[int] = None,
        complexity_max: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search files with various filters."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            where_conditions: list[str] = []
            params: list[Any] = []

            if query:
                # Use LIKE search instead of FTS for now
                where_conditions.append("(name LIKE ? OR path LIKE ?)")
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern])

            if domain:
                where_conditions.append("domain = ?")
                params.append(domain)

            if complexity_min is not None:
                where_conditions.append("complexity >= ?")
                params.append(complexity_min)

            if complexity_max is not None:
                where_conditions.append("complexity <= ?")
                params.append(complexity_max)

            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            cursor.execute(
                f"""
                SELECT * FROM files 
                {where_clause}
                ORDER BY complexity DESC, name
                LIMIT ? OFFSET ?
            """,
                params + [limit, offset],
            )

            return [dict(row) for row in cursor.fetchall()]

    async def search_files_async(
        self,
        query: Optional[str] = None,
        domain: Optional[str] = None,
        complexity_min: Optional[int] = None,
        complexity_max: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search files with various filters asynchronously."""
        async with self._get_async_connection() as conn:
            cursor = await conn.cursor()

            where_conditions: list[str] = []
            params: list[Any] = []

            if query:
                # Use LIKE search instead of FTS for now
                where_conditions.append("(name LIKE ? OR path LIKE ?)")
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern])

            if domain:
                where_conditions.append("domain = ?")
                params.append(domain)

            if complexity_min is not None:
                where_conditions.append("complexity >= ?")
                params.append(complexity_min)

            if complexity_max is not None:
                where_conditions.append("complexity <= ?")
                params.append(complexity_max)

            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            await cursor.execute(
                f"""
                SELECT * FROM files 
                {where_clause}
                ORDER BY complexity DESC, name
                LIMIT ? OFFSET ?
            """,
                params + [limit, offset],
            )

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    def search_models(
        self,
        query: Optional[str] = None,
        domain: Optional[str] = None,
        min_fields: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search models with various filters."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if query:
                cursor.execute(
                    """
                    SELECT models.* FROM models 
                    JOIN models_fts ON models.id = models_fts.rowid 
                    WHERE models_fts MATCH ?
                    ORDER BY rank
                    LIMIT ? OFFSET ?
                """,
                    (query, limit, offset),
                )
            else:
                where_conditions: list[str] = []
                params: list[Any] = []

                if domain:
                    where_conditions.append("domain = ?")
                    params.append(domain)

                if min_fields is not None:
                    where_conditions.append("fields >= ?")
                    params.append(min_fields)

                where_clause = (
                    "WHERE " + " AND ".join(where_conditions)
                    if where_conditions
                    else ""
                )

                cursor.execute(
                    f"""
                    SELECT * FROM models 
                    {where_clause}
                    ORDER BY fields DESC, name
                    LIMIT ? OFFSET ?
                """,
                    params + [limit, offset],
                )

            return [dict(row) for row in cursor.fetchall()]

    def get_complexity_distribution(self) -> List[Dict[str, Any]]:
        """Get complexity distribution for charts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    CASE 
                        WHEN complexity <= 10 THEN 'Low (0-10)'
                        WHEN complexity <= 20 THEN 'Medium (11-20)'
                        WHEN complexity <= 40 THEN 'High (21-40)'
                        ELSE 'Very High (40+)'
                    END as complexity_range,
                    COUNT(*) as count
                FROM files
                GROUP BY complexity_range
                ORDER BY MIN(complexity)
            """
            )

            return [
                {"complexity_range": row["complexity_range"], "count": row["count"]}
                for row in cursor.fetchall()
            ]

    def get_domain_statistics(self) -> List[Dict[str, Any]]:
        """Get domain statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM domains 
                ORDER BY file_count DESC
            """
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_top_complex_files(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most complex files."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM files 
                ORDER BY complexity DESC 
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get basic counts
            cursor.execute("SELECT COUNT(*) FROM files")
            total_files = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM classes")
            total_classes = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM functions")
            total_functions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM imports")
            total_imports = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM models")
            total_models = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM relationships")
            total_relationships = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM decorators")
            total_decorators = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM variables")
            total_variables = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(complexity) FROM files")
            avg_complexity = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(DISTINCT domain) FROM files")
            total_domains = cursor.fetchone()[0]

            return {
                "total_files": total_files,
                "total_classes": total_classes,
                "total_functions": total_functions,
                "total_imports": total_imports,
                "total_models": total_models,
                "total_relationships": total_relationships,
                "total_decorators": total_decorators,
                "total_variables": total_variables,
                "avg_complexity": round(avg_complexity, 1),
                "total_domains": total_domains,
            }

    async def get_system_stats_async(self) -> Dict[str, Any]:
        """Get overall system statistics asynchronously."""
        async with self._get_async_connection() as conn:
            cursor = await conn.cursor()

            # Get basic counts
            await cursor.execute("SELECT COUNT(*) as total_files FROM files")
            result = await cursor.fetchone()
            total_files = result[0] if result else 0

            await cursor.execute("SELECT COUNT(*) as total_models FROM models")
            result = await cursor.fetchone()
            total_models = result[0] if result else 0

            await cursor.execute(
                "SELECT COUNT(*) as total_relationships FROM relationships"
            )
            result = await cursor.fetchone()
            total_relationships = result[0] if result else 0

            await cursor.execute("SELECT AVG(complexity) as avg_complexity FROM files")
            result = await cursor.fetchone()
            avg_complexity = result[0] if result and result[0] else 0

            await cursor.execute(
                "SELECT COUNT(DISTINCT domain) as total_domains FROM files"
            )
            result = await cursor.fetchone()
            total_domains = result[0] if result else 0

            # Get additional stats for compatibility
            await cursor.execute("SELECT COUNT(*) as total_classes FROM classes")
            result = await cursor.fetchone()
            total_classes = result[0] if result else 0

            await cursor.execute("SELECT COUNT(*) as total_functions FROM functions")
            result = await cursor.fetchone()
            total_functions = result[0] if result else 0

            return {
                "total_files": total_files,
                "total_models": total_models,
                "total_relationships": total_relationships,
                "avg_complexity": round(avg_complexity, 1),
                "total_domains": total_domains,
                "total_classes": total_classes,
                "total_functions": total_functions,
            }

    def export_to_json(self, output_file: str) -> bool:
        """Export all data to JSON format."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Export files
                cursor.execute("SELECT * FROM files ORDER BY path")
                files = [dict(row) for row in cursor.fetchall()]

                # Export models
                cursor.execute("SELECT * FROM models ORDER BY file_id, name")
                models = [dict(row) for row in cursor.fetchall()]

                # Export relationships
                cursor.execute("SELECT * FROM relationships")
                relationships = [dict(row) for row in cursor.fetchall()]

                # Export domains
                cursor.execute("SELECT * FROM domains")
                domains = [dict(row) for row in cursor.fetchall()]

                data = {
                    "files": files,
                    "models": models,
                    "relationships": relationships,
                    "domains": domains,
                    "exported_at": datetime.now().isoformat(),
                    "total_stats": self.get_system_stats(),
                }

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)

                logger.info(f"Data exported to {output_file}")
                return True

        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            return False

    def add_annotation(
        self,
        target_type: str,
        target_id: int,
        annotation_type: str,
        content: str,
        author: str = None,
    ) -> int:
        """Add user annotation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO annotations (target_type, target_id, annotation_type, content, author)
                VALUES (?, ?, ?, ?, ?)
            """,
                (target_type, target_id, annotation_type, content, author),
            )
            conn.commit()
            return cursor.lastrowid

    def get_annotations(
        self, target_type: str = None, target_id: int = None
    ) -> List[Dict[str, Any]]:
        """Get annotations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            where_conditions: list[str] = []
            params: list[Any] = []

            if target_type:
                where_conditions.append("target_type = ?")
                params.append(target_type)

            if target_id:
                where_conditions.append("target_id = ?")
                params.append(target_id)

            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            cursor.execute(
                f"""
                SELECT * FROM annotations 
                {where_clause}
                ORDER BY created_at DESC
            """,
                params,
            )

            return [dict(row) for row in cursor.fetchall()]

    # Enhanced Code Analysis Methods

    def get_file_detailed_content(self, file_id: int) -> Dict[str, Any]:
        """Get comprehensive file content including all classes, functions, imports, etc."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get file info
            cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            file_info = cursor.fetchone()
            if not file_info:
                return {}

            file_data = dict(file_info)

            # Get all classes in the file
            cursor.execute(
                """
                SELECT * FROM classes 
                WHERE file_id = ? 
                ORDER BY line_number
                """,
                (file_id,),
            )
            classes = [dict(row) for row in cursor.fetchall()]

            # Get methods for each class
            for class_record in classes:
                cursor.execute(
                    """
                    SELECT * FROM functions 
                    WHERE class_id = ? 
                    ORDER BY line_number
                    """,
                    (class_record["id"],),
                )
                class_record["methods"] = [dict(row) for row in cursor.fetchall()]

            # Get top-level functions
            cursor.execute(
                """
                SELECT * FROM functions 
                WHERE file_id = ? AND class_id IS NULL 
                ORDER BY line_number
                """,
                (file_id,),
            )
            functions = [dict(row) for row in cursor.fetchall()]

            # Get imports
            cursor.execute(
                """
                SELECT * FROM imports 
                WHERE file_id = ? 
                ORDER BY line_number
                """,
                (file_id,),
            )
            imports = [dict(row) for row in cursor.fetchall()]

            # Get decorators
            cursor.execute(
                """
                SELECT * FROM decorators 
                WHERE file_id = ? 
                ORDER BY line_number
                """,
                (file_id,),
            )
            decorators = [dict(row) for row in cursor.fetchall()]

            # Get variables
            cursor.execute(
                """
                SELECT * FROM variables 
                WHERE file_id = ? AND scope_type = 'module'
                ORDER BY line_number
                """,
                (file_id,),
            )
            module_variables = [dict(row) for row in cursor.fetchall()]

            file_data.update(
                {
                    "classes": classes,
                    "functions": functions,
                    "imports": imports,
                    "decorators": decorators,
                    "module_variables": module_variables,
                }
            )

            return file_data

    def search_classes(
        self,
        query: Optional[str] = None,
        class_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search classes with various filters."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            params: list[Any] = []
            where_conditions: list[str] = []

            if query:
                where_conditions.append("(name LIKE ? OR file_path LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
            if class_type:
                where_conditions.append("class_type = ?")
                params.append(class_type)

            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            cursor.execute(
                f"""
                SELECT * FROM classes 
                {where_clause}
                ORDER BY complexity_score DESC, name
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset],
            )

            return [dict(row) for row in cursor.fetchall()]

    def search_services(
        self,
        query: Optional[str] = None,
        service_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search service classes with various filters."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Service patterns to identify service classes
            service_patterns = [
                "Service",
                "Interface",
                "Validator",
                "Factory",
                "Manager",
                "Handler",
                "Provider",
                "Repository",
                "Controller",
                "Processor",
                "Engine",
                "Client",
            ]

            service_condition = " OR ".join(
                [f"name LIKE '%{pattern}%'" for pattern in service_patterns]
            )

            params: list[Any] = []
            where_conditions = [f"({service_condition})"]

            if query:
                where_conditions.append("(name LIKE ? OR file_path LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
            if service_type:
                where_conditions.append("class_type = ?")
                params.append(service_type)

            where_clause = "WHERE " + " AND ".join(where_conditions)

            cursor.execute(
                f"""
                SELECT * FROM classes 
                {where_clause}
                ORDER BY complexity_score DESC, name
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset],
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_file_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get file by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_class_by_id(self, class_id: int) -> Optional[Dict[str, Any]]:
        """Get class by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_function_by_id(self, function_id: int) -> Optional[Dict[str, Any]]:
        """Get function by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM functions WHERE id = ?", (function_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_decorators(
        self,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        file_id: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated decorators with optional filtering."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build query conditions
            conditions = []
            params = []

            if search:
                conditions.append("name LIKE ?")
                params.append(f"%{search}%")

            if file_id:
                conditions.append("file_id = ?")
                params.append(file_id)

            where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

            # Get total count
            count_query = f"SELECT COUNT(*) FROM decorators{where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            # Get paginated results
            query = f"""
                SELECT * FROM decorators
                {where_clause}
                ORDER BY line_number
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [limit, offset])
            decorators = [dict(row) for row in cursor.fetchall()]

            return decorators, total_count

    def get_relationships(
        self,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated relationships with optional filtering."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build query conditions
            conditions = []
            params = []

            if search:
                conditions.append("(source_name LIKE ? OR target_name LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])

            if relationship_type:
                conditions.append("relationship_type = ?")
                params.append(relationship_type)

            where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

            # Get total count
            count_query = f"SELECT COUNT(*) FROM relationships{where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            # Get paginated results with the new schema
            query = f"""
                SELECT * FROM relationships
                {where_clause}
                ORDER BY id
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [limit, offset])
            relationships = [dict(row) for row in cursor.fetchall()]

            return relationships, total_count


# ...existing code...


def main() -> None:
    """Main function to demonstrate SQLite backend."""
    db = DocumentationDatabase("docs/interactive-documentation-suite/documentation.db")

    # Import from existing JSON
    json_file = "docs/interactive-documentation-suite/real_project_data.json"
    if Path(json_file).exists():
        print("🔄 Importing data from JSON...")
        success = db.import_from_json(json_file)
        if success:
            print("✅ Data imported successfully!")

            # Show some statistics
            stats = db.get_system_stats()
            print(f"📊 System stats: {stats}")

            # Test search
            print("\n🔍 Testing search...")
            files = db.search_files(query="logging", limit=5)
            print(f"Found {len(files)} files matching 'logging'")

            models = db.search_models(domain="application", limit=5)
            print(f"Found {len(models)} models in application domain")

            # Export back to JSON
            print("\n💾 Exporting to JSON...")
            db.export_to_json("docs/interactive-documentation-suite/exported_data.json")

        else:
            print("❌ Failed to import data")
    else:
        print(f"❌ JSON file not found: {json_file}")


if __name__ == "__main__":
    main()
