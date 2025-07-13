#!/usr/bin/env python3
"""
Database Population Script using Python AST Analysis

This module populates the SQLite database with comprehensive code structure data
extracted from the project files using Python's AST (Abstract Syntax Tree) module
for Python files and basic analysis for other file types.

The population logic is designed to be exactly aligned with the query logic
to ensure data consistency and integrity.

Key Features:
- Comprehensive AST analysis for Python files
- Relationship extraction between code entities
- Pydantic model detection and classification
- Domain classification based on file paths
- Complexity analysis and metrics calculation
- Robust error handling and progress tracking

Last Updated: 2025-01-27 15:30:00
"""

import ast
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Add models to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dashboard.dashboard_logging import get_logger
from dashboard.settings import DashboardSettings
from db.schema_manager import DatabaseSchemaManager

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

# Configure enhanced logging with structured format
# Logging configuration will be loaded from settings
logger = get_logger(__name__)


class ASTAnalyzer:
    """
    Analyzes Python files using AST to extract code structure.

    This class provides comprehensive analysis of Python source files,
    extracting classes, functions, relationships, and metrics using
    the Abstract Syntax Tree representation.
    """

    def __init__(self, settings: Optional[DashboardSettings] = None) -> None:
        """Initialize the AST analyzer with tracking state."""
        if settings is None:
            try:
                settings = DashboardSettings.from_yaml()
            except Exception as e:
                logger.warning(f"Could not load settings, using defaults: {e}")
                settings = DashboardSettings()

        self.settings = settings
        self.current_file_path: str = ""
        self.current_file_id: Optional[int] = None
        self.analysis_cache: Dict[str, Any] = {}
        self.error_count: int = 0
        self.success_count: int = 0

    def analyze_file(
        self, file_path: Path
    ) -> Tuple[
        FileRecord, List[ClassRecord], List[FunctionRecord], List[RelationshipRecord]
    ]:
        """
        Analyze a Python file and extract all code entities.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            Tuple containing file record, classes, functions, and relationships

        Raises:
            Various exceptions are caught and logged, returning minimal records on error
        """
        self.current_file_path = str(file_path)
        logger.debug(f"Starting analysis of file: {file_path}")

        try:
            # Read file content with encoding detection fallback
            content = self._read_file_content(file_path)

            # Parse AST with enhanced error reporting
            tree = self._parse_ast_safely(content, file_path)
            if tree is None:
                return self._create_error_file_record(file_path), [], [], []

            # Extract file-level information
            file_record = self._extract_file_info(file_path, content, tree)

            # Extract classes and functions with progress tracking
            classes, functions, relationships = self._extract_code_entities(
                tree, file_path
            )

            self.success_count += 1
            logger.debug(
                f"Successfully analyzed {file_path}: {len(classes)} classes, {len(functions)} functions"
            )

            return file_record, classes, functions, relationships

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error analyzing file {file_path}: {e}", exc_info=True)
            return self._create_error_file_record(file_path), [], [], []

    def _get_relative_path(self, file_path: Path) -> str:
        """Get relative path, handling cases where file is outside current directory."""
        try:
            return str(file_path.relative_to(Path.cwd())).replace("\\", "/")
        except ValueError:
            # File is outside current directory, use just the filename
            return file_path.name

    def _get_relative_path_to_root(self, file_path: Path, root_path: Path) -> str:
        """Get relative path from root, handling different path formats."""
        try:
            return str(file_path.relative_to(root_path)).replace("\\", "/")
        except ValueError:
            # If file_path is not relative to root_path, return absolute path
            return str(file_path).replace("\\", "/")

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
        if not self.settings.ast_analysis.enable_relationship_extraction:
            return []

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
        if not self.settings.ast_analysis.enable_pydantic_detection:
            return 0

        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_classes = [self._get_name(base) for base in node.bases]
                if any("BaseModel" in base for base in base_classes):
                    count += 1
        return count

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate simplified cyclomatic complexity for the entire file."""
        complexity = (
            self.settings.ast_analysis.complexity_base
        )  # Base complexity from settings

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += self.settings.ast_analysis.complexity_increment
            elif isinstance(node, ast.ExceptHandler):
                complexity += self.settings.ast_analysis.complexity_increment
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity += self.settings.ast_analysis.complexity_increment

        return min(complexity, self.settings.ast_analysis.max_file_complexity)

    def _calculate_function_complexity(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> int:
        """Calculate cyclomatic complexity for a specific function."""
        complexity = (
            self.settings.ast_analysis.complexity_base
        )  # Base complexity from settings

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += self.settings.ast_analysis.complexity_increment
            elif isinstance(child, ast.ExceptHandler):
                complexity += self.settings.ast_analysis.complexity_increment
            elif isinstance(child, ast.BoolOp):
                complexity += (
                    len(child.values) - 1
                ) * self.settings.ast_analysis.complexity_increment

        return min(complexity, self.settings.ast_analysis.max_function_complexity)

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

    def _read_file_content(self, file_path: Path) -> str:
        """
        Read file content with encoding detection fallback.

        Args:
            file_path: Path to file to read

        Returns:
            File content as string

        Raises:
            UnicodeDecodeError: If file cannot be decoded with any encoding
            FileNotFoundError: If file does not exist
        """
        # Use settings for encoding configuration
        default_encoding = self.settings.file_analysis.default_encoding
        fallback_encodings = self.settings.file_analysis.encoding_fallbacks

        # Try default encoding first, then fallbacks
        encodings = [default_encoding] + fallback_encodings

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        # If all encodings fail, raise a proper UnicodeDecodeError
        raise UnicodeDecodeError(
            "utf-8", b"", 0, 1, f"Unable to decode file {file_path} with any encoding"
        )

    def _parse_ast_safely(self, content: str, file_path: Path) -> Optional[ast.AST]:
        """
        Parse AST with enhanced error reporting.

        Args:
            content: File content to parse
            file_path: Path for error reporting

        Returns:
            Parsed AST tree or None on error
        """
        try:
            return ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse AST for {file_path}: {e}")
            return None

    def _create_error_file_record(self, file_path: Path) -> FileRecord:
        """
        Create a minimal file record for files that couldn't be analyzed.

        Args:
            file_path: Path to the file that failed analysis

        Returns:
            Minimal FileRecord with error indication
        """
        return FileRecord(
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

    def _extract_code_entities(
        self, tree: ast.AST, file_path: Path
    ) -> Tuple[List[ClassRecord], List[FunctionRecord], List[RelationshipRecord]]:
        """
        Extract classes, functions, and relationships from AST.

        Args:
            tree: Parsed AST tree
            file_path: Path to the source file

        Returns:
            Tuple of classes, functions, and relationships lists
        """
        classes: List[ClassRecord] = []
        functions: List[FunctionRecord] = []
        relationships: List[RelationshipRecord] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_record = self._extract_class_info(node, file_path)
                classes.append(class_record)

                # Extract methods from the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
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

        return classes, functions, relationships


class DatabasePopulator:
    """
    Populates the SQLite database with code analysis data.

    This class uses the DatabaseSchemaManager for all schema operations
    and focuses on data analysis and insertion operations.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        settings: Optional[DashboardSettings] = None,
    ) -> None:
        """
        Initialize the database populator.

        Args:
            db_path: Path to the SQLite database file (optional, uses settings if not provided)
            settings: Dashboard settings object (loads from config if not provided)
        """
        # Load settings if not provided
        if settings is None:
            try:
                settings = DashboardSettings.from_yaml()
            except Exception as e:
                logger.warning(f"Could not load settings, using defaults: {e}")
                settings = DashboardSettings()

        self.settings = settings

        # Set database path from settings or parameter
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = getattr(
                settings, "db_path", settings.population.default_db_path
            )

        self.analyzer = ASTAnalyzer(settings)
        self.schema_manager = DatabaseSchemaManager(self.db_path)

    def create_tables(self) -> None:
        """
        Create database tables using the schema manager.

        This method delegates to the DatabaseSchemaManager for all
        schema operations, maintaining separation of concerns.
        """
        try:
            self.schema_manager.initialize_database()
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database schema: {e}")
            raise

    def populate_from_directory(
        self,
        project_root: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """Populate database by analyzing all files in the project directory."""
        if include_patterns is None:
            include_patterns = self.settings.file_analysis.include_patterns

        if exclude_patterns is None:
            exclude_patterns = self.settings.file_analysis.exclude_patterns

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

    def _clear_database(self) -> None:
        """Clear all existing data from the database using schema manager."""
        try:
            self.schema_manager.clear_data()
            logger.info("Database data cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            raise

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

    def _get_relative_path_to_root(self, file_path: Path, root_path: Path) -> str:
        """Get relative path from root, handling different path formats."""
        try:
            return str(file_path.relative_to(root_path)).replace("\\", "/")
        except ValueError:
            # If file_path is not relative to root_path, return absolute path
            return str(file_path).replace("\\", "/")

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


def main() -> None:
    """Main function to run the database population."""
    import argparse

    parser = argparse.ArgumentParser(description="Populate code intelligence database")
    parser.add_argument("project_root", help="Path to the project root directory")
    parser.add_argument("--db-path", help="Path to SQLite database (overrides config)")
    parser.add_argument(
        "--include",
        nargs="*",
        help="File patterns to include (overrides config)",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        help="Patterns to exclude (overrides config)",
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file (defaults to dashboard_config.yaml)",
    )

    args = parser.parse_args()

    project_root = Path(args.project_root)
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        sys.exit(1)

    # Load settings
    try:
        if args.config:
            settings = DashboardSettings.from_yaml(Path(args.config))
        else:
            settings = DashboardSettings.from_yaml()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load configuration, using defaults: {e}")
        settings = DashboardSettings()

    # Setup logging from settings
    try:
        logging.basicConfig(
            level=getattr(logging, settings.logging.level.upper(), logging.INFO),
            format=settings.logging.format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    settings.logging.files.get("populate_db", "populate_db.log"),
                    encoding=settings.logging.encoding,
                ),
            ],
        )
        logger.info(f"Logging configured with level: {settings.logging.level}")
    except Exception as e:
        logger.warning(f"Could not configure logging from settings: {e}")
        # Fallback to basic logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    # Create populator with settings
    populator = DatabasePopulator(args.db_path, settings)
    populator.create_tables()

    # Use command line args if provided, otherwise use settings
    include_patterns = args.include if args.include else None
    exclude_patterns = args.exclude if args.exclude else None

    populator.populate_from_directory(project_root, include_patterns, exclude_patterns)

    db_path = args.db_path or populator.db_path
    logger.info(f"Database population completed. Database saved to: {db_path}")


if __name__ == "__main__":
    main()
