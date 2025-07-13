#!/usr/bin/env python3
"""
Python AST Code Structure Extractor

This tool extracts comprehensive code structure and relationships from Python files
including classes, functions, variables, Pydantic models, calls, inheritance,
composition, and imports. Outputs normalized JSON for dashboard ingestion.

Key Features:
- Complete AST traversal and analysis
- Pydantic model detection and classification
- Relationship extraction (inheritance, composition, calls)
- Import analysis and dependency mapping
- Type annotation extraction
- Comprehensive metadata collection

Last Updated: 2025-01-27 15:30:00
"""

import ast
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union


def extract_from_file(filepath: Union[str, Path], file_id: int) -> Dict[str, Any]:
    """
    Extract code structure from a Python file.

    Args:
        filepath: Path to the Python file to analyze
        file_id: Unique identifier for the file

    Returns:
        Dictionary containing extracted code structure data

    Raises:
        FileNotFoundError: If the file doesn't exist
        SyntaxError: If the Python file has syntax errors
        UnicodeDecodeError: If the file cannot be decoded
    """
    filepath = Path(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in {filepath}: {e}")

    visitor = CodeVisitor(str(filepath), file_id)
    visitor.visit(tree)
    return visitor.to_dict()


class CodeVisitor(ast.NodeVisitor):
    """
    AST visitor class for extracting code structure and relationships.

    This visitor traverses the entire AST and extracts detailed information
    about classes, functions, variables, imports, and their relationships.
    """

    def __init__(self, filepath: str, file_id: int) -> None:
        """
        Initialize the code visitor.

        Args:
            filepath: Path to the file being analyzed
            file_id: Unique identifier for the file
        """
        self.filepath = filepath
        self.file_id = file_id

        # Storage for extracted entities
        self.classes: List[Dict[str, Any]] = []
        self.functions: List[Dict[str, Any]] = []
        self.variables: List[Dict[str, Any]] = []
        self.imports: List[Dict[str, Any]] = []
        self.relationships: List[Dict[str, Any]] = []

        # Context tracking
        self.class_stack: List[str] = []
        self.func_stack: List[str] = []

        # Name tracking for relationship resolution
        self.known_class_names: Set[str] = set()
        self.pydantic_model_names: Set[str] = set()

        # Module-level information
        self.module_docstring: Optional[str] = None

    def visit_Module(self, node: ast.Module) -> None:
        """Visit module node and extract module-level docstring."""
        self.module_docstring = ast.get_docstring(node)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement and extract import information."""
        for alias in node.names:
            self.imports.append(
                {
                    "file_id": self.file_id,
                    "module_name": alias.name,
                    "import_type": "import",
                    "imported_names": [alias.asname or alias.name],
                    "alias": alias.asname,
                    "line_number": node.lineno,
                    "is_standard_library": self._is_standard_library(alias.name),
                    "is_third_party": self._is_third_party(alias.name),
                    "is_local": self._is_local_import(alias.name),
                }
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self.imports.append(
                {
                    "file_id": self.file_id,
                    "module_name": module,
                    "import_type": "from_import",
                    "imported_names": [alias.name],
                    "alias": alias.asname,
                    "line_number": node.lineno,
                    "is_standard_library": False,
                    "is_third_party": False,
                    "is_local": True,
                }
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        class_id = len(self.classes) + 1
        self.class_stack.append(class_id)
        bases = [
            ast.unparse(b) if hasattr(ast, "unparse") else getattr(b, "id", "<unknown>")
            for b in node.bases
        ]
        is_pydantic = any("BaseModel" in base for base in bases)
        class_type = "pydantic_model" if is_pydantic else "class"
        if is_pydantic:
            self.pydantic_model_names.add(node.name)
        self.known_class_names.add(node.name)
        fields = []
        validators = []
        config_class = None
        properties_count = 0

        # Parse fields, validators, config
        for body_item in node.body:
            if isinstance(body_item, ast.AnnAssign):  # x: int = 5
                field_name = (
                    body_item.target.id
                    if isinstance(body_item.target, ast.Name)
                    else None
                )
                field_type = (
                    ast.unparse(body_item.annotation)
                    if hasattr(ast, "unparse")
                    else None
                )
                default_value = (
                    ast.unparse(body_item.value) if body_item.value else None
                )
                fields.append(
                    {"name": field_name, "type": field_type, "default": default_value}
                )
                # Track composition: if field_type is another model, note relationship
                if is_pydantic and field_type in self.pydantic_model_names:
                    self.relationships.append(
                        {
                            "source_type": "pydantic_model",
                            "source_id": class_id,
                            "target_type": "pydantic_model",
                            "target_name": field_type,
                            "relationship_type": "composes",
                            "strength": 1.0,
                        }
                    )
            elif isinstance(body_item, ast.Assign):  # x = 5
                for target in body_item.targets:
                    if isinstance(target, ast.Name):
                        self.variables.append(
                            {
                                "name": target.id,
                                "file_id": self.file_id,
                                "scope_type": "class",
                                "scope_id": class_id,
                                "variable_type": None,
                                "line_number": body_item.lineno,
                                "is_constant": target.id.isupper(),
                                "is_public": not target.id.startswith("_"),
                                "default_value": (
                                    ast.unparse(body_item.value)
                                    if hasattr(ast, "unparse")
                                    else None
                                ),
                            }
                        )
            elif isinstance(body_item, ast.FunctionDef):
                # Validators
                for deco in body_item.decorator_list:
                    if (
                        isinstance(deco, ast.Name)
                        and deco.id in ("validator", "root_validator")
                    ) or (
                        isinstance(deco, ast.Attribute)
                        and deco.attr in ("validator", "root_validator")
                    ):
                        validators.append(body_item.name)
                # @property
                for deco in body_item.decorator_list:
                    if isinstance(deco, ast.Name) and deco.id == "property":
                        properties_count += 1
            elif isinstance(body_item, ast.ClassDef) and body_item.name == "Config":
                config_class = ast.get_docstring(body_item)

        class_rec = {
            "id": class_id,
            "name": node.name,
            "file_id": self.file_id,
            "file_path": self.filepath,
            "line_number": node.lineno,
            "end_line_number": getattr(node, "end_lineno", node.lineno),
            "domain": "",
            "class_type": class_type,
            "base_classes": bases,
            "fields": fields,
            "validators": validators,
            "config": config_class,
            "methods_count": sum(
                isinstance(item, ast.FunctionDef) for item in node.body
            ),
            "properties_count": properties_count,
            "decorators": [
                ast.unparse(d) if hasattr(ast, "unparse") else "<decorator>"
                for d in node.decorator_list
            ],
            "docstring": ast.get_docstring(node),
            "is_abstract": any("abstract" in b.lower() for b in bases),
            "is_public": not node.name.startswith("_"),
            "complexity_score": 0,
        }
        self.classes.append(class_rec)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        parent_class_id = self.class_stack[-1] if self.class_stack else None
        func_id = len(self.functions) + 1
        decorators = [
            ast.unparse(d) if hasattr(ast, "unparse") else "<decorator>"
            for d in node.decorator_list
        ]
        parameters = []
        for a in node.args.args:
            param = {"name": a.arg, "type": None, "default": None}
            if hasattr(a, "annotation") and a.annotation:
                param["type"] = (
                    ast.unparse(a.annotation) if hasattr(ast, "unparse") else None
                )
            parameters.append(param)
        func_rec = {
            "id": func_id,
            "name": node.name,
            "file_id": self.file_id,
            "class_id": parent_class_id,
            "file_path": self.filepath,
            "line_number": node.lineno,
            "end_line_number": getattr(node, "end_lineno", node.lineno),
            "function_type": "method" if parent_class_id else "function",
            "parameters_count": len(parameters),
            "parameters": parameters,
            "return_type": (
                ast.unparse(node.returns)
                if hasattr(node, "returns") and node.returns
                else None
            ),
            "decorators": decorators,
            "docstring": ast.get_docstring(node),
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "is_public": not node.name.startswith("_"),
            "complexity_score": 0,
            "calls_made": [],
            "variables_used": [],
        }
        self.functions.append(func_rec)
        self.func_stack.append(func_id)
        self.generic_visit(node)
        self.func_stack.pop()

    def visit_Call(self, node):
        if self.func_stack:
            func_id = self.func_stack[-1]
            called = None
            if isinstance(node.func, ast.Name):
                called = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
            if called:
                self.relationships.append(
                    {
                        "source_type": "function",
                        "source_id": func_id,
                        "target_type": "function",
                        "target_name": called,
                        "relationship_type": "calls",
                        "strength": 1.0,
                    }
                )
        self.generic_visit(node)

    def visit_Assign(self, node):
        # Module-level variables
        if not self.class_stack and not self.func_stack:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.variables.append(
                        {
                            "name": target.id,
                            "file_id": self.file_id,
                            "scope_type": "module",
                            "scope_id": None,
                            "variable_type": None,
                            "line_number": node.lineno,
                            "is_constant": target.id.isupper(),
                            "is_public": not target.id.startswith("_"),
                            "default_value": (
                                ast.unparse(node.value)
                                if hasattr(ast, "unparse")
                                else None
                            ),
                        }
                    )
        self.generic_visit(node)

    def to_dict(self):
        return {
            "name": os.path.basename(self.filepath),
            "path": self.filepath,
            "file_id": self.file_id,
            "lines": None,  # Can be filled in by counting lines in file if needed.
            "docstring": self.module_docstring,
            "imports": self.imports,
            "classes": self.classes,
            "functions": self.functions,
            "variables": self.variables,
            "relationships": self.relationships,
        }


def walk_project(root_dir):
    all_files = []
    file_id = 1
    for path in Path(root_dir).rglob("*.py"):
        try:
            file_data = extract_from_file(str(path), file_id)
            with open(path, "r", encoding="utf-8") as f:
                file_data["lines"] = len(f.readlines())
            all_files.append(file_data)
            file_id += 1
        except Exception as e:
            print(f"Error parsing {path}: {e}")
    return all_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract Python code entities and relationships."
    )
    parser.add_argument("root", help="Project root directory")
    parser.add_argument("--out", default="code_structure.json", help="Output JSON file")
    args = parser.parse_args()

    files = walk_project(args.root)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"files": files}, f, indent=2)
    print(f"Wrote {len(files)} files to {args.out}")
