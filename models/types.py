#!/usr/bin/env python3
"""
Pydantic Models for Code Intelligence Dashboard

This module defines all data models used throughout the dashboard,
providing validation, serialization, and auto-generated UI forms
via Pydantic-Panel integration.

All models include comprehensive field descriptions for UI generation
and validation rules for data integrity.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class FileType(str, Enum):
    """Enumeration of supported file types."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    HTML = "html"
    CSS = "css"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    OTHER = "other"


class DomainType(str, Enum):
    """Enumeration of architectural domains."""

    PRESENTATION = "presentation"
    APPLICATION = "application"
    DOMAIN = "domain"
    INFRASTRUCTURE = "infrastructure"
    SERVICES = "services"
    MODELS = "models"
    UTILS = "utils"
    TESTS = "tests"
    CONFIG = "config"
    DOCS = "docs"
    UNKNOWN = "unknown"


class ComplexityLevel(str, Enum):
    """Enumeration of complexity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RelationshipType(str, Enum):
    """Types of relationships between code entities."""

    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    IMPORTS = "imports"
    USES = "uses"
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"


# Base Models
class BaseRecord(BaseModel):
    """Base model for all database records."""

    id: Optional[int] = Field(None, description="Unique identifier for the record")
    created_at: Optional[datetime] = Field(
        None, description="Timestamp when the record was created"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when the record was last updated"
    )

    class Config:
        from_attributes = True
        use_enum_values = True


# Core Entity Models
class FileRecord(BaseRecord):
    """Model representing a file in the codebase."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the file (without path)"
    )
    path: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Full path to the file relative to project root",
    )
    domain: DomainType = Field(..., description="Architectural domain classification")
    file_type: FileType = Field(
        ..., description="Type of file based on extension and content"
    )
    complexity: int = Field(
        0, ge=0, le=1000, description="Calculated complexity score (0-1000)"
    )
    complexity_level: ComplexityLevel = Field(
        ComplexityLevel.LOW, description="Human-readable complexity level"
    )
    lines_of_code: int = Field(0, ge=0, description="Total number of lines in the file")
    classes_count: int = Field(
        0, ge=0, description="Number of classes defined in the file"
    )
    functions_count: int = Field(
        0, ge=0, description="Number of functions defined in the file"
    )
    imports_count: int = Field(0, ge=0, description="Number of import statements")
    pydantic_models_count: int = Field(
        0, ge=0, description="Number of Pydantic models (if Python file)"
    )

    @model_validator(mode="before")
    @classmethod
    def set_complexity_level(cls, values):
        """Automatically set complexity level based on complexity score."""
        if isinstance(values, dict):
            complexity = values.get("complexity", 0)
            if "complexity_level" not in values or values["complexity_level"] is None:
                if complexity < 10:
                    values["complexity_level"] = ComplexityLevel.LOW
                elif complexity < 25:
                    values["complexity_level"] = ComplexityLevel.MEDIUM
                elif complexity < 50:
                    values["complexity_level"] = ComplexityLevel.HIGH
                else:
                    values["complexity_level"] = ComplexityLevel.VERY_HIGH
        return values

    @field_validator("path")
    @classmethod
    def validate_path(cls, v):
        """Ensure path uses forward slashes for consistency."""
        return v.replace("\\", "/")


class ClassRecord(BaseRecord):
    """Model representing a class in the codebase."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the class"
    )
    file_id: int = Field(..., description="ID of the file containing this class")
    file_path: str = Field(..., description="Path to the file containing this class")
    domain: DomainType = Field(..., description="Architectural domain of the class")
    class_type: str = Field(
        "class", description="Type of class (class, dataclass, pydantic model, etc.)"
    )
    line_number: int = Field(
        1, ge=1, description="Line number where the class is defined"
    )
    methods_count: int = Field(0, ge=0, description="Number of methods in the class")
    is_abstract: bool = Field(False, description="Whether the class is abstract")
    is_pydantic_model: bool = Field(
        False, description="Whether the class is a Pydantic model"
    )
    base_classes: List[str] = Field(
        default_factory=list, description="List of base class names"
    )
    decorators: List[str] = Field(
        default_factory=list, description="List of decorators applied to the class"
    )


class FunctionRecord(BaseRecord):
    """Model representing a function or method in the codebase."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the function"
    )
    file_id: int = Field(..., description="ID of the file containing this function")
    class_id: Optional[int] = Field(
        None, description="ID of the class containing this function (if it's a method)"
    )
    file_path: str = Field(..., description="Path to the file containing this function")
    function_type: str = Field(
        "function",
        description="Type of function (function, method, staticmethod, classmethod, property)",
    )
    line_number: int = Field(
        1, ge=1, description="Line number where the function is defined"
    )
    parameters_count: int = Field(
        0, ge=0, description="Number of parameters the function accepts"
    )
    parameters: List[str] = Field(
        default_factory=list, description="List of parameter names"
    )
    return_type: Optional[str] = Field(
        None, description="Return type annotation (if available)"
    )
    is_async: bool = Field(False, description="Whether the function is asynchronous")
    is_generator: bool = Field(False, description="Whether the function is a generator")
    decorators: List[str] = Field(
        default_factory=list, description="List of decorators applied to the function"
    )
    complexity: int = Field(
        1, ge=1, description="Cyclomatic complexity of the function"
    )


class RelationshipRecord(BaseRecord):
    """Model representing relationships between code entities."""

    source_type: str = Field(
        ..., description="Type of source entity (file, class, function)"
    )
    source_id: int = Field(..., description="ID of the source entity")
    source_name: str = Field(..., description="Name of the source entity")
    target_type: str = Field(
        ..., description="Type of target entity (file, class, function)"
    )
    target_id: int = Field(..., description="ID of the target entity")
    target_name: str = Field(..., description="Name of the target entity")
    relationship_type: RelationshipType = Field(
        ..., description="Type of relationship between entities"
    )
    file_path: str = Field(..., description="File where the relationship is defined")
    line_number: Optional[int] = Field(
        None, description="Line number where the relationship occurs"
    )


# Analysis and Statistics Models
class DomainStats(BaseModel):
    """Statistics for a specific domain."""

    domain: DomainType = Field(..., description="Domain name")
    files_count: int = Field(0, ge=0, description="Number of files in this domain")
    classes_count: int = Field(0, ge=0, description="Number of classes in this domain")
    functions_count: int = Field(
        0, ge=0, description="Number of functions in this domain"
    )
    total_lines: int = Field(0, ge=0, description="Total lines of code in this domain")
    avg_complexity: float = Field(
        0.0, ge=0.0, description="Average complexity score for files in this domain"
    )


class ComplexityDistribution(BaseModel):
    """Distribution of complexity across the codebase."""

    complexity_range: str = Field(
        ..., description="Complexity range (e.g., '0-10', '11-25')"
    )
    count: int = Field(0, ge=0, description="Number of files in this complexity range")
    percentage: float = Field(
        0.0, ge=0.0, le=100.0, description="Percentage of total files in this range"
    )


class SystemStats(BaseModel):
    """Overall system statistics."""

    total_files: int = Field(0, ge=0, description="Total number of files analyzed")
    total_classes: int = Field(0, ge=0, description="Total number of classes")
    total_functions: int = Field(0, ge=0, description="Total number of functions")
    total_lines: int = Field(0, ge=0, description="Total lines of code")
    avg_complexity: float = Field(
        0.0, ge=0.0, description="Average complexity across all files"
    )
    domains: List[DomainStats] = Field(
        default_factory=list, description="Statistics broken down by domain"
    )
    complexity_distribution: List[ComplexityDistribution] = Field(
        default_factory=list, description="Distribution of complexity levels"
    )
    last_analysis: Optional[datetime] = Field(
        None, description="Timestamp of last analysis run"
    )


# UI Form Models (for Pydantic-Panel integration)
class FileFilterForm(BaseModel):
    """Form model for filtering files."""

    domain: Optional[DomainType] = Field(None, description="Filter by domain")
    file_type: Optional[FileType] = Field(None, description="Filter by file type")
    complexity_level: Optional[ComplexityLevel] = Field(
        None, description="Filter by complexity level"
    )
    min_lines: Optional[int] = Field(None, ge=0, description="Minimum lines of code")
    max_lines: Optional[int] = Field(None, ge=0, description="Maximum lines of code")
    search_term: Optional[str] = Field(
        None, max_length=100, description="Search in file names and paths"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_line_range(cls, values):
        """Ensure min_lines <= max_lines."""
        if isinstance(values, dict):
            min_lines = values.get("min_lines")
            max_lines = values.get("max_lines")
            if (
                min_lines is not None
                and max_lines is not None
                and min_lines > max_lines
            ):
                raise ValueError("min_lines must be less than or equal to max_lines")
        return values


class AnalysisConfigForm(BaseModel):
    """Form model for configuring analysis parameters."""

    project_root: str = Field(..., description="Path to the project root directory")
    include_patterns: List[str] = Field(
        default_factory=lambda: ["*.py", "*.js", "*.html", "*.css"],
        description="File patterns to include in analysis",
    )
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["__pycache__", "*.pyc", "node_modules", ".git"],
        description="Patterns to exclude from analysis",
    )
    max_file_size: int = Field(
        1024 * 1024,  # 1MB
        ge=1024,
        description="Maximum file size to analyze (in bytes)",
    )
    enable_ast_analysis: bool = Field(
        True, description="Enable detailed AST analysis for Python files"
    )
    calculate_complexity: bool = Field(True, description="Calculate complexity metrics")

    @field_validator("project_root")
    @classmethod
    def validate_project_root(cls, v):
        """Ensure project root exists."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Project root directory does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Project root must be a directory: {v}")
        return str(path.resolve())


# Export all models for easy importing
__all__ = [
    "FileType",
    "DomainType",
    "ComplexityLevel",
    "RelationshipType",
    "BaseRecord",
    "FileRecord",
    "ClassRecord",
    "FunctionRecord",
    "RelationshipRecord",
    "DomainStats",
    "ComplexityDistribution",
    "SystemStats",
    "FileFilterForm",
    "AnalysisConfigForm",
]
