#!/usr/bin/env python3
"""
Database Population Script using Python AST Analysis

This module populates the SQLite database with comprehensive code structure data
extracted from the project files using Python's AST (Abstract Syntax Tree) module
for Python files and basic analysis for other file types.

The population logic is designed to be exactly aligned with the query logic
to ensure data consistency and integrity.
"""

import ast
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Add models to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.types import (
    ClassRecord,
    ComplexityLevel,
    DomainType,
    FileRecord,
    FileType,
    FunctionRecord,
    RelationshipRecord,
    RelationshipType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("populate_db.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


class ASTAnalyzer:
    """Analyzes Python files using AST to extract code structure."""

    def __init__(self):
        self.current_file_path = ""
        self.current_file_id = None

    def analyze_file(
        self, file_path: Path
    ) -> Tuple[
        FileRecord, List[ClassRecord], List[FunctionRecord], List[RelationshipRecord]
    ]:
        """Analyze a Python file and extract all code entities."""
        self.current_file_path = str(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content, filename=str(file_path))

            # Extract file-level information
            file_record = self._extract_file_info(file_path, content, tree)

            # Extract classes and functions
            classes = []
            functions = []
            relationships = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_record = self._extract_class_info(node, file_path)
                    classes.append(class_record)

                    # Extract methods from the class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) or isinstance(
                            item, ast.AsyncFunctionDef
                        ):
                            method_record = self._extract_function_info(
                                item, file_path, class_name=node.name
                            )
                            functions.append(method_record)

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Only top-level functions (not methods)
                    if self._is_top_level_function(node, tree):
                        function_record = self._extract_function_info(node, file_path)
                        functions.append(function_record)

            # Extract relationships
            relationships.extend(self._extract_relationships(tree, file_path))

            return file_record, classes, functions, relationships

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            # Return minimal file record on error
            file_record = FileRecord(
                name=file_path.name,
                path=self._get_relative_path(file_path),
                domain=self._classify_domain(file_path),
                file_type=self._classify_file_type(file_path),
                complexity=0,
                lines_of_code=0,
                classes_count=0,
                functions_count=0,
                imports_count=0,
                pydantic_models_count=0,
            )
            return file_record, [], [], []

    def _get_relative_path(self, file_path: Path) -> str:
        """Get relative path, handling cases where file is outside current directory."""
        try:
            return str(file_path.relative_to(Path.cwd())).replace("\\", "/")
        except ValueError:
            # File is outside current directory, use just the filename
            return file_path.name

    def _get_relative_path_to_root(self, file_path: Path, root_path: Path) -> str:
        """Get relative path to a specific root, handling cases where file is outside root."""
        try:
            return str(file_path.relative_to(root_path)).replace("\\", "/")
        except ValueError:
            # File is outside root directory, try to preserve some path structure
            # by using the last few parts of the path
            parts = file_path.parts
            if len(parts) >= 3:
                return "/".join(parts[-3:])
            elif len(parts) >= 2:
                return "/".join(parts[-2:])
            else:
                return file_path.name

    def _extract_file_info(
        self, file_path: Path, content: str, tree: ast.AST
    ) -> FileRecord:
        """Extract file-level information."""
        lines = content.split("\n")

        # Count different types of nodes
        classes_count = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        functions_count = len(
            [
                n
                for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
        )
        imports_count = len(
            [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        )

        # Count Pydantic models
        pydantic_models_count = self._count_pydantic_models(tree)

        # Calculate complexity (simplified cyclomatic complexity)
        complexity = self._calculate_complexity(tree)

        return FileRecord(
            name=file_path.name,
            path=self._get_relative_path(file_path),
            domain=self._classify_domain(file_path),
            file_type=self._classify_file_type(file_path),
            complexity=complexity,
            lines_of_code=len(lines),
            classes_count=classes_count,
            functions_count=functions_count,
            imports_count=imports_count,
            pydantic_models_count=pydantic_models_count,
        )

    def _extract_class_info(self, node: ast.ClassDef, file_path: Path) -> ClassRecord:
        """Extract information about a class."""
        # Count methods
        methods_count = len(
            [
                n
                for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
        )

        # Extract base classes
        base_classes = [self._get_name(base) for base in node.bases]

        # Extract decorators
        decorators = [self._get_name(dec) for dec in node.decorator_list]

        # Check if it's a Pydantic model
        is_pydantic_model = any("BaseModel" in base for base in base_classes) or any(
            "pydantic" in dec.lower() for dec in decorators
        )

        # Determine class type
        class_type = "pydantic_model" if is_pydantic_model else "class"
        if any("dataclass" in dec.lower() for dec in decorators):
            class_type = "dataclass"
        elif any("ABC" in base for base in base_classes):
            class_type = "abstract_class"

        return ClassRecord(
            name=node.name,
            file_id=0,  # Will be set when inserting
            file_path=self._get_relative_path(file_path),
            domain=self._classify_domain(file_path),
            class_type=class_type,
            line_number=node.lineno,
            methods_count=methods_count,
            is_abstract=any("ABC" in base for base in base_classes),
            is_pydantic_model=is_pydantic_model,
            base_classes=base_classes,
            decorators=decorators,
        )

    def _extract_function_info(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        file_path: Path,
        class_name: Optional[str] = None,
    ) -> FunctionRecord:
        """Extract information about a function or method."""
        # Extract parameters
        parameters = [arg.arg for arg in node.args.args]

        # Extract decorators
        decorators = [self._get_name(dec) for dec in node.decorator_list]

        # Determine function type
        function_type = "method" if class_name else "function"
        if "staticmethod" in decorators:
            function_type = "staticmethod"
        elif "classmethod" in decorators:
            function_type = "classmethod"
        elif "property" in decorators:
            function_type = "property"

        # Extract return type annotation
        return_type = None
        if node.returns:
            return_type = self._get_name(node.returns)

        # Calculate function complexity
        complexity = self._calculate_function_complexity(node)

        return FunctionRecord(
            name=node.name,
            file_id=0,  # Will be set when inserting
            class_id=None,  # Will be set if it's a method
            file_path=self._get_relative_path(file_path),
            function_type=function_type,
            line_number=node.lineno,
            parameters_count=len(parameters),
            parameters=parameters,
            return_type=return_type,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_generator=self._is_generator(node),
            decorators=decorators,
            complexity=complexity,
        )

    def _extract_relationships(
        self, tree: ast.AST, file_path: Path
    ) -> List[RelationshipRecord]:
        """Extract relationships between code entities."""
        relationships = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Inheritance relationships
                for base in node.bases:
                    base_name = self._get_name(base)
                    if base_name and base_name != "object":
                        relationships.append(
                            RelationshipRecord(
                                source_type="class",
                                source_id=0,  # Will be set when inserting
                                source_name=node.name,
                                target_type="class",
                                target_id=0,  # Will be resolved later
                                target_name=base_name,
                                relationship_type=RelationshipType.INHERITS,
                                file_path=self._get_relative_path(file_path),
                                line_number=node.lineno,
                            )
                        )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Function call relationships
                for call_node in ast.walk(node):
                    if isinstance(call_node, ast.Call):
                        func_name = self._get_name(call_node.func)
                        if func_name:
                            relationships.append(
                                RelationshipRecord(
                                    source_type="function",
                                    source_id=0,  # Will be set when inserting
                                    source_name=node.name,
                                    target_type="function",
                                    target_id=0,  # Will be resolved later
                                    target_name=func_name,
                                    relationship_type=RelationshipType.CALLS,
                                    file_path=self._get_relative_path(file_path),
                                    line_number=call_node.lineno,
                                )
                            )

        return relationships

    def _classify_domain(self, file_path: Path) -> DomainType:
        """Classify the architectural domain of a file based on its path."""
        path_str = str(file_path).lower()

        if "presentation" in path_str or "ui" in path_str or "dashboard" in path_str:
            return DomainType.PRESENTATION
        elif "application" in path_str or "app" in path_str:
            return DomainType.APPLICATION
        elif "domain" in path_str or "business" in path_str:
            return DomainType.DOMAIN
        elif "infrastructure" in path_str or "infra" in path_str:
            return DomainType.INFRASTRUCTURE
        elif "service" in path_str:
            return DomainType.SERVICES
        elif "model" in path_str or "entity" in path_str or "dto" in path_str:
            return DomainType.MODELS
        elif "util" in path_str or "helper" in path_str or "tool" in path_str:
            return DomainType.UTILS
        elif "test" in path_str:
            return DomainType.TESTS
        elif "config" in path_str or "setting" in path_str:
            return DomainType.CONFIG
        elif "doc" in path_str or "readme" in path_str:
            return DomainType.DOCS
        else:
            return DomainType.UNKNOWN

    def _classify_file_type(self, file_path: Path) -> FileType:
        """Classify the file type based on extension."""
        suffix = file_path.suffix.lower()

        if suffix == ".py":
            return FileType.PYTHON
        elif suffix == ".js":
            return FileType.JAVASCRIPT
        elif suffix == ".html":
            return FileType.HTML
        elif suffix == ".css":
            return FileType.CSS
        elif suffix in [".md", ".markdown"]:
            return FileType.MARKDOWN
        elif suffix == ".json":
            return FileType.JSON
        elif suffix in [".yml", ".yaml"]:
            return FileType.YAML
        else:
            return FileType.OTHER

    def _count_pydantic_models(self, tree: ast.AST) -> int:
        """Count Pydantic models in the AST."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_classes = [self._get_name(base) for base in node.bases]
                if any("BaseModel" in base for base in base_classes):
                    count += 1
        return count

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate simplified cyclomatic complexity for the entire file."""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity += 1

        return complexity

    def _calculate_function_complexity(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> int:
        """Calculate cyclomatic complexity for a specific function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _is_top_level_function(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], tree: ast.AST
    ) -> bool:
        """Check if a function is defined at the top level (not inside a class)."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return False
        return True

    def _is_generator(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool:
        """Check if a function is a generator (contains yield)."""
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _get_name(self, node: ast.AST) -> str:
        """Extract name from various AST node types."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif hasattr(node, "id"):
            return node.id
        else:
            return str(node)


class DatabasePopulator:
    """Populates the SQLite database with code analysis data."""

    def __init__(self, db_path: str = "code_intelligence.db"):
        self.db_path = db_path
        self.analyzer = ASTAnalyzer()

    def _get_relative_path_to_root(self, file_path: Path, root_path: Path) -> str:
        """Get relative path from root, handling different path formats."""
        try:
            return str(file_path.relative_to(root_path)).replace("\\", "/")
        except ValueError:
            # If file_path is not relative to root_path, return absolute path
            return str(file_path).replace("\\", "/")

    def create_tables(self):
        """Create database tables with exact schema matching query expectations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Files table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL UNIQUE,
                    domain TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    complexity INTEGER DEFAULT 0,
                    complexity_level TEXT DEFAULT 'low',
                    lines_of_code INTEGER DEFAULT 0,
                    classes_count INTEGER DEFAULT 0,
                    functions_count INTEGER DEFAULT 0,
                    imports_count INTEGER DEFAULT 0,
                    pydantic_models_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Classes table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    file_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    class_type TEXT DEFAULT 'class',
                    line_number INTEGER DEFAULT 1,
                    methods_count INTEGER DEFAULT 0,
                    is_abstract BOOLEAN DEFAULT FALSE,
                    is_pydantic_model BOOLEAN DEFAULT FALSE,
                    base_classes TEXT DEFAULT '[]',
                    decorators TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            """
            )

            # Functions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS functions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    file_id INTEGER NOT NULL,
                    class_id INTEGER,
                    file_path TEXT NOT NULL,
                    function_type TEXT DEFAULT 'function',
                    line_number INTEGER DEFAULT 1,
                    parameters_count INTEGER DEFAULT 0,
                    parameters TEXT DEFAULT '[]',
                    return_type TEXT,
                    is_async BOOLEAN DEFAULT FALSE,
                    is_generator BOOLEAN DEFAULT FALSE,
                    decorators TEXT DEFAULT '[]',
                    complexity INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files (id),
                    FOREIGN KEY (class_id) REFERENCES classes (id)
                )
            """
            )

            # Relationships table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_id INTEGER NOT NULL,
                    source_name TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id INTEGER NOT NULL,
                    target_name TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for better query performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_files_domain ON files (domain)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_files_type ON files (file_type)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_files_complexity ON files (complexity)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_classes_file_id ON classes (file_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_functions_file_id ON functions (file_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_functions_class_id ON functions (class_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_type, source_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_type, target_id)"
            )

            conn.commit()
            logger.info("Database tables created successfully")

    def populate_from_directory(
        self,
        project_root: Path,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
    ):
        """Populate database by analyzing all files in the project directory."""
        if include_patterns is None:
            include_patterns = [
                "*.py",
                "*.js",
                "*.html",
                "*.css",
                "*.md",
                "*.json",
                "*.yml",
                "*.yaml",
            ]

        if exclude_patterns is None:
            exclude_patterns = [
                "__pycache__",
                "*.pyc",
                "node_modules",
                ".git",
                ".vscode",
                "*.egg-info",
            ]

        logger.info(f"Starting analysis of project: {project_root}")

        # Clear existing data
        self._clear_database()

        # Find all files to analyze
        files_to_analyze = self._find_files(
            project_root, include_patterns, exclude_patterns
        )
        logger.info(f"Found {len(files_to_analyze)} files to analyze")

        # Analyze each file
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for file_path in files_to_analyze:
                try:
                    self._analyze_and_store_file(cursor, file_path, project_root)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue

            conn.commit()

        logger.info("Database population completed successfully")

    def _clear_database(self):
        """Clear all existing data from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM relationships")
            cursor.execute("DELETE FROM functions")
            cursor.execute("DELETE FROM classes")
            cursor.execute("DELETE FROM files")
            conn.commit()
            logger.info("Database cleared")

    def _find_files(
        self,
        project_root: Path,
        include_patterns: List[str],
        exclude_patterns: List[str],
    ) -> List[Path]:
        """Find all files matching the include patterns and not matching exclude patterns."""
        import fnmatch

        files = []

        for root, dirs, filenames in os.walk(project_root):
            # Filter out excluded directories
            dirs[:] = [
                d
                for d in dirs
                if not any(fnmatch.fnmatch(d, pattern) for pattern in exclude_patterns)
            ]

            for filename in filenames:
                file_path = Path(root) / filename

                # Check if file matches include patterns
                if any(
                    fnmatch.fnmatch(filename, pattern) for pattern in include_patterns
                ):
                    # Check if file doesn't match exclude patterns
                    if not any(
                        fnmatch.fnmatch(str(file_path), pattern)
                        for pattern in exclude_patterns
                    ):
                        files.append(file_path)

        return files

    def _analyze_and_store_file(
        self, cursor: sqlite3.Cursor, file_path: Path, project_root: Path
    ):
        """Analyze a single file and store the results in the database."""
        if file_path.suffix == ".py":
            # Use AST analysis for Python files
            file_record, classes, functions, relationships = self.analyzer.analyze_file(
                file_path
            )
        else:
            # Basic analysis for non-Python files
            file_record = self._basic_file_analysis(file_path, project_root)
            classes, functions, relationships = [], [], []

        # Insert file record
        file_id = self._insert_file_record(cursor, file_record)

        # Insert classes and get their IDs
        class_id_map = {}
        for class_record in classes:
            class_record.file_id = file_id
            class_id = self._insert_class_record(cursor, class_record)
            class_id_map[class_record.name] = class_id

        # Insert functions
        for function_record in functions:
            function_record.file_id = file_id
            # Set class_id if this is a method
            if function_record.function_type in [
                "method",
                "staticmethod",
                "classmethod",
                "property",
            ]:
                # Find the class this method belongs to
                for class_name, class_id in class_id_map.items():
                    if function_record.file_path == file_record.path:
                        function_record.class_id = class_id
                        break

            self._insert_function_record(cursor, function_record)

        # Insert relationships (will be resolved in a second pass)
        for relationship_record in relationships:
            self._insert_relationship_record(cursor, relationship_record)

    def _basic_file_analysis(self, file_path: Path, project_root: Path) -> FileRecord:
        """Perform basic analysis for non-Python files."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception:
            lines = []

        return FileRecord(
            name=file_path.name,
            path=self._get_relative_path_to_root(file_path, project_root),
            domain=self.analyzer._classify_domain(file_path),
            file_type=self.analyzer._classify_file_type(file_path),
            complexity=0,
            lines_of_code=len(lines),
            classes_count=0,
            functions_count=0,
            imports_count=0,
            pydantic_models_count=0,
        )

    def _insert_file_record(self, cursor: sqlite3.Cursor, record: FileRecord) -> int:
        """Insert a file record and return its ID."""
        cursor.execute(
            """
            INSERT INTO files (
                name, path, domain, file_type, complexity, complexity_level,
                lines_of_code, classes_count, functions_count, imports_count,
                pydantic_models_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.name,
                record.path,
                (
                    record.domain.value
                    if hasattr(record.domain, "value")
                    else record.domain
                ),
                (
                    record.file_type.value
                    if hasattr(record.file_type, "value")
                    else record.file_type
                ),
                record.complexity,
                (
                    record.complexity_level.value
                    if hasattr(record.complexity_level, "value")
                    else record.complexity_level
                ),
                record.lines_of_code,
                record.classes_count,
                record.functions_count,
                record.imports_count,
                record.pydantic_models_count,
            ),
        )
        return cursor.lastrowid

    def _insert_class_record(self, cursor: sqlite3.Cursor, record: ClassRecord) -> int:
        """Insert a class record and return its ID."""
        cursor.execute(
            """
            INSERT INTO classes (
                name, file_id, file_path, domain, class_type, line_number,
                methods_count, is_abstract, is_pydantic_model, base_classes, decorators
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.name,
                record.file_id,
                record.file_path,
                (
                    record.domain.value
                    if hasattr(record.domain, "value")
                    else record.domain
                ),
                record.class_type,
                record.line_number,
                record.methods_count,
                record.is_abstract,
                record.is_pydantic_model,
                json.dumps(record.base_classes),
                json.dumps(record.decorators),
            ),
        )
        return cursor.lastrowid

    def _insert_function_record(
        self, cursor: sqlite3.Cursor, record: FunctionRecord
    ) -> int:
        """Insert a function record and return its ID."""
        cursor.execute(
            """
            INSERT INTO functions (
                name, file_id, class_id, file_path, function_type, line_number,
                parameters_count, parameters, return_type, is_async, is_generator,
                decorators, complexity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.name,
                record.file_id,
                record.class_id,
                record.file_path,
                record.function_type,
                record.line_number,
                record.parameters_count,
                json.dumps(record.parameters),
                record.return_type,
                record.is_async,
                record.is_generator,
                json.dumps(record.decorators),
                record.complexity,
            ),
        )
        return cursor.lastrowid

    def _insert_relationship_record(
        self, cursor: sqlite3.Cursor, record: RelationshipRecord
    ) -> int:
        """Insert a relationship record and return its ID."""
        cursor.execute(
            """
            INSERT INTO relationships (
                source_type, source_id, source_name, target_type, target_id,
                target_name, relationship_type, file_path, line_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.source_type,
                record.source_id,
                record.source_name,
                record.target_type,
                record.target_id,
                record.target_name,
                (
                    record.relationship_type.value
                    if hasattr(record.relationship_type, "value")
                    else record.relationship_type
                ),
                record.file_path,
                record.line_number,
            ),
        )
        return cursor.lastrowid


def main():
    """Main function to run the database population."""
    import argparse

    parser = argparse.ArgumentParser(description="Populate code intelligence database")
    parser.add_argument("project_root", help="Path to the project root directory")
    parser.add_argument(
        "--db-path", default="code_intelligence.db", help="Path to SQLite database"
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=["*.py", "*.js", "*.html", "*.css", "*.md"],
        help="File patterns to include",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=["__pycache__", "*.pyc", "node_modules", ".git"],
        help="Patterns to exclude",
    )

    args = parser.parse_args()

    project_root = Path(args.project_root)
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        sys.exit(1)

    populator = DatabasePopulator(args.db_path)
    populator.create_tables()
    populator.populate_from_directory(project_root, args.include, args.exclude)

    logger.info(f"Database population completed. Database saved to: {args.db_path}")


if __name__ == "__main__":
    main()
