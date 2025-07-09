#!/usr/bin/env python3
"""
Dashboard Maintenance Tool
Consolidated fix and debug utilities for dashboard issues

**Last Updated:** 2025-01-27

This module consolidates all maintenance, fixing, and debugging functionality
from multiple utility files into a unified maintenance tool.

Features:
- Function parameter fixing
- Database issue resolution
- Data filtering and cleanup
- Debug utilities and diagnostics
- Performance optimization
- Data consistency checks
"""

import argparse
import ast
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

# Add API path
sys.path.append(os.path.dirname(__file__))
from types import TracebackType
from typing import Any, Dict, List

from api.sqlite_backend import DocumentationDatabase
from pydantic import BaseModel


class DashboardMaintenance:
    """Comprehensive dashboard maintenance and debugging tool."""

    project_root: Path
    db_path: Path
    db: Optional[DocumentationDatabase]
    results: Dict[str, Any]

    def __init__(self) -> None:
        self.project_root: Path = Path(__file__).parent.parent
        self.db_path: Path = (
            self.project_root
            / "docs"
            / "interactive-documentation-suite"
            / "documentation.db"
        )
        self.db: Optional[DocumentationDatabase] = None
        self.results: Dict[str, Any] = {}

    def should_skip_path(self, path: str) -> bool:
        """Check if a path should be skipped based on filtering rules."""
        path_lower = path.lower()

        # Skip virtual environment directories
        if ".venv/" in path or path.startswith(".venv/"):
            return True
        if "venv/" in path or path.startswith("venv/"):
            return True
        if "env/" in path or path.startswith("env/"):
            return True

        # Skip hidden directories and files (starting with .)
        if "/.git/" in path or path.startswith(".git/"):
            return True
        if "/.vscode/" in path or path.startswith(".vscode/"):
            return True
        if "/.idea/" in path or path.startswith(".idea/"):
            return True
        if path.startswith("."):
            return True

        # Skip cache and build directories
        if "__pycache__/" in path or path.startswith("__pycache__/"):
            return True
        if ".pytest_cache/" in path or path.startswith(".pytest_cache/"):
            return True
        if "node_modules/" in path or path.startswith("node_modules/"):
            return True
        if ".mypy_cache/" in path or path.startswith(".mypy_cache/"):
            return True
        if "/.tox/" in path or path.startswith(".tox/"):
            return True
        if "/build/" in path or path.startswith("build/"):
            return True
        if "/dist/" in path or path.startswith("dist/"):
            return True

        # Skip specific files
        if "/.coverage" in path or path.endswith(".coverage"):
            return True
        if path.endswith(".DS_Store"):
            return True
        if path.endswith(".pyc"):
            return True
        if path.endswith(".pyo"):
            return True

        return False

    def fix_function_parameters(self, limit: int = 100) -> Dict[str, Any]:
        """Fix function parameters by re-parsing source files."""
        print("🔧 Fixing Function Parameters")
        print("-" * 40)

        results: Dict[str, Any] = {
            "functions_checked": 0,
            "functions_fixed": 0,
            "files_processed": 0,
            "errors": [],
            "fixed_functions": [],
        }

        try:
            if not self.db_path.exists():
                results["errors"].append(f"Database not found at {self.db_path}")
                return results

            self.db = DocumentationDatabase(str(self.db_path))

            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Get functions that need parameter data
                cursor.execute(
                    """
                    SELECT f.id, f.name, f.file_path, f.line_number, f.parameters_count
                    FROM functions f
                    WHERE (f.parameters IS NULL OR f.parameters = '') 
                    AND f.parameters_count > 0
                    LIMIT ?
                """,
                    (limit,),
                )

                functions_to_fix = cursor.fetchall()
                results["functions_checked"] = len(functions_to_fix)
                print(
                    f"   📝 Found {len(functions_to_fix)} functions needing parameter fixes"
                )

                processed_files: set[str] = set()

                for (
                    func_id,
                    func_name,
                    file_path,
                    line_number,
                    param_count,
                ) in functions_to_fix:
                    try:
                        # Skip if we should skip this path
                        if self.should_skip_path(file_path):
                            continue

                        # Try to read the source file
                        full_path = self.project_root / file_path.lstrip("/")
                        if not full_path.exists():
                            continue

                        if str(full_path) not in processed_files:
                            processed_files.add(str(full_path))
                            results["files_processed"] += 1

                        with open(full_path, "r", encoding="utf-8") as f:
                            source_code = f.read()

                        # Parse the AST
                        tree = ast.parse(source_code)

                        # Find the function at the specified line
                        for node in ast.walk(tree):
                            if isinstance(
                                node, (ast.FunctionDef, ast.AsyncFunctionDef)
                            ):
                                if (
                                    node.name == func_name
                                    and node.lineno == line_number
                                ):
                                    # Extract parameter information
                                    params: list[str] = []
                                    for arg in node.args.args:
                                        params.append(arg.arg)

                                    # Handle *args and **kwargs
                                    if node.args.vararg:
                                        params.append(f"*{node.args.vararg.arg}")
                                    if node.args.kwarg:
                                        params.append(f"**{node.args.kwarg.arg}")

                                    param_string = ", ".join(params)

                                    # Update the database
                                    cursor.execute(
                                        "UPDATE functions SET parameters = ? WHERE id = ?",
                                        (param_string, func_id),
                                    )

                                    results["functions_fixed"] += 1
                                    results["fixed_functions"].append(
                                        {
                                            "id": func_id,
                                            "name": func_name,
                                            "parameters": param_string,
                                        }
                                    )

                                    print(f"   ✅ Fixed {func_name}: {param_string}")
                                    break

                    except Exception as e:
                        results["errors"].append(
                            f"Error processing {func_name}: {str(e)}"
                        )
                        continue

                # Commit changes
                conn.commit()

        except Exception as e:
            results["errors"].append(f"Database error: {str(e)}")

        print(
            f"   📊 Fixed {results['functions_fixed']}/{results['functions_checked']} functions"
        )
        print(f"   📊 Processed {results['files_processed']} files")

        if results["errors"]:
            print(f"   ⚠️  {len(results['errors'])} errors occurred")

        return results

    def clean_excluded_files(self) -> Dict[str, Any]:
        """Remove files that should be excluded from the database."""
        print("🧹 Cleaning Excluded Files")
        print("-" * 40)

        results: Dict[str, Any] = {
            "files_checked": 0,
            "files_removed": 0,
            "classes_removed": 0,
            "functions_removed": 0,
            "removed_files": [],
            "errors": [],
        }

        try:
            if not self.db_path.exists():
                results["errors"] = [f"Database not found at {self.db_path}"]
                return results

            self.db = DocumentationDatabase(str(self.db_path))

            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Get all files
                cursor.execute("SELECT id, path FROM files")
                all_files = cursor.fetchall()
                results["files_checked"] = len(all_files)

                files_to_remove: list[tuple[int, str]] = []
                for file_id, file_path in all_files:
                    if self.should_skip_path(file_path):
                        files_to_remove.append((file_id, file_path))

                print(f"   📝 Found {len(files_to_remove)} files to remove")

                for file_id, file_path in files_to_remove:
                    # Count related records before deletion
                    cursor.execute(
                        "SELECT COUNT(*) FROM classes WHERE file_id = ?", (file_id,)
                    )
                    class_count = cursor.fetchone()[0]

                    cursor.execute(
                        "SELECT COUNT(*) FROM functions WHERE file_id = ?", (file_id,)
                    )
                    function_count = cursor.fetchone()[0]

                    # Remove related records
                    cursor.execute(
                        "DELETE FROM functions WHERE file_id = ?", (file_id,)
                    )
                    cursor.execute("DELETE FROM classes WHERE file_id = ?", (file_id,))
                    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))

                    results["files_removed"] += 1
                    results["classes_removed"] += class_count
                    results["functions_removed"] += function_count
                    results["removed_files"].append(file_path)

                    print(
                        f"   🗑️  Removed {file_path} ({class_count} classes, {function_count} functions)"
                    )

                # Commit changes
                conn.commit()

        except Exception as e:
            results["errors"] = [f"Database error: {str(e)}"]

        print(f"   📊 Removed {results['files_removed']} files")
        print(f"   📊 Removed {results['classes_removed']} classes")
        print(f"   📊 Removed {results['functions_removed']} functions")

        return results

    def debug_file_detailed(self, file_id: int) -> Dict[str, Any]:
        """Debug file detailed content vs direct database query."""
        print(f"🔍 Debugging File Detailed Content (ID: {file_id})")
        print("-" * 40)

        results: Dict[str, Any] = {
            "file_id": file_id,
            "direct_query": {},
            "api_method": {},
            "consistency": True,
            "issues": [],
        }

        try:
            if not self.db_path.exists():
                results["issues"].append(f"Database not found at {self.db_path}")
                return results

            # Direct database query
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get file info
            cursor.execute("SELECT name, path FROM files WHERE id = ?", (file_id,))
            file_info = cursor.fetchone()
            if not file_info:
                results["issues"].append(f"File ID {file_id} not found")
                return results

            file_name, file_path = file_info
            print(f"   📄 File: {file_name}")
            print(f"   📁 Path: {file_path}")

            # Direct query for functions with parameters
            cursor.execute(
                "SELECT name, parameters FROM functions WHERE file_id = ? AND parameters != '' LIMIT 5",
                (file_id,),
            )
            direct_functions = cursor.fetchall()
            results["direct_query"]["functions_with_params"] = len(direct_functions)

            # Get all functions for this file (direct)
            cursor.execute(
                "SELECT COUNT(*) FROM functions WHERE file_id = ?", (file_id,)
            )
            total_direct = cursor.fetchone()[0]
            results["direct_query"]["total_functions"] = total_direct

            print(f"   📊 Direct query - Total functions: {total_direct}")
            print(
                f"   📊 Direct query - Functions with parameters: {len(direct_functions)}"
            )

            if direct_functions:
                print("   📝 Sample functions with parameters (direct):")
                for name, params in direct_functions[:3]:
                    print(f"      {name}: '{params}'")

            conn.close()

            # Get functions via get_file_detailed_content
            self.db = DocumentationDatabase(str(self.db_path))
            file_data = self.db.get_file_detailed_content(file_id)

            functions = file_data.get("functions", [])
            results["api_method"]["total_functions"] = len(functions)

            # Check if any have parameters
            functions_with_params = [
                f
                for f in functions
                if f.get("parameters") and f.get("parameters").strip()
            ]
            results["api_method"]["functions_with_params"] = len(functions_with_params)

            print(f"   📊 API method - Total functions: {len(functions)}")
            print(
                f"   📊 API method - Functions with parameters: {len(functions_with_params)}"
            )

            if functions_with_params:
                print("   📝 Sample functions with parameters (API):")
                for func in functions_with_params[:3]:
                    print(f"      {func.get('name')}: '{func.get('parameters')}'")

            # Check consistency
            if (
                results["direct_query"]["total_functions"]
                != results["api_method"]["total_functions"]
            ):
                results["consistency"] = False
                results["issues"].append(
                    "Function count mismatch between direct query and API method"
                )

            if (
                results["direct_query"]["functions_with_params"]
                != results["api_method"]["functions_with_params"]
            ):
                results["consistency"] = False
                results["issues"].append("Functions with parameters count mismatch")

            if results["consistency"]:
                print("   ✅ Consistency check passed")
            else:
                print("   ❌ Consistency issues found:")
                for issue in results["issues"]:
                    print(f"      - {issue}")

        except Exception as e:
            results["issues"].append(f"Debug error: {str(e)}")
            print(f"   ❌ Debug error: {e}")

        return results

    def analyze_database_stats(self) -> Dict[str, Any]:
        """Analyze database statistics and identify potential issues."""
        print("📊 Analyzing Database Statistics")
        print("-" * 40)

        results: Dict[str, Any] = {
            "total_files": 0,
            "total_classes": 0,
            "total_functions": 0,
            "functions_with_parameters": 0,
            "excluded_files": 0,
            "orphaned_records": 0,
            "domain_distribution": {},
            "complexity_distribution": {},
            "issues": [],
        }

        try:
            if not self.db_path.exists():
                results["issues"].append(f"Database not found at {self.db_path}")
                return results

            self.db = DocumentationDatabase(str(self.db_path))

            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Basic counts
                cursor.execute("SELECT COUNT(*) FROM files")
                results["total_files"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM classes")
                results["total_classes"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM functions")
                results["total_functions"] = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM functions WHERE parameters IS NOT NULL AND parameters != ''"
                )
                results["functions_with_parameters"] = cursor.fetchone()[0]

                # Check for excluded files
                cursor.execute(
                    "SELECT COUNT(*) FROM files WHERE path LIKE '%/.venv/%' OR path LIKE '%/__pycache__/%' OR path LIKE '%/.git/%'"
                )
                results["excluded_files"] = cursor.fetchone()[0]

                # Check for orphaned records
                cursor.execute(
                    "SELECT COUNT(*) FROM functions WHERE file_id NOT IN (SELECT id FROM files)"
                )
                orphaned_functions = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM classes WHERE file_id NOT IN (SELECT id FROM files)"
                )
                orphaned_classes = cursor.fetchone()[0]

                results["orphaned_records"] = orphaned_functions + orphaned_classes

                # Domain distribution
                cursor.execute(
                    "SELECT domain, COUNT(*) FROM files GROUP BY domain ORDER BY COUNT(*) DESC"
                )
                domain_data = cursor.fetchall()
                results["domain_distribution"] = {
                    domain: count for domain, count in domain_data
                }

                # Complexity distribution
                cursor.execute(
                    """
                    SELECT 
                        CASE 
                            WHEN complexity < 10 THEN 'Low (0-9)'
                            WHEN complexity < 20 THEN 'Medium (10-19)'
                            WHEN complexity < 50 THEN 'High (20-49)'
                            ELSE 'Very High (50+)'
                        END as complexity_range,
                        COUNT(*) as count
                    FROM files 
                    GROUP BY complexity_range
                    ORDER BY MIN(complexity)
                """
                )
                complexity_data = cursor.fetchall()
                results["complexity_distribution"] = {
                    range_name: count for range_name, count in complexity_data
                }

            # Print statistics
            print(f"   📊 Total files: {results['total_files']}")
            print(f"   📊 Total classes: {results['total_classes']}")
            print(f"   📊 Total functions: {results['total_functions']}")
            print(
                f"   📊 Functions with parameters: {results['functions_with_parameters']}"
            )

            if results["excluded_files"] > 0:
                print(f"   ⚠️  Excluded files found: {results['excluded_files']}")
                results["issues"].append(
                    f"{results['excluded_files']} excluded files in database"
                )

            if results["orphaned_records"] > 0:
                print(f"   ⚠️  Orphaned records found: {results['orphaned_records']}")
                results["issues"].append(
                    f"{results['orphaned_records']} orphaned records"
                )

            print("   📊 Domain distribution:")
            for domain, count in list(results["domain_distribution"].items())[:5]:
                print(f"      {domain}: {count}")

            print("   📊 Complexity distribution:")
            for range_name, count in results["complexity_distribution"].items():
                print(f"      {range_name}: {count}")

            if not results["issues"]:
                print("   ✅ No issues found")

        except Exception as e:
            results["issues"].append(f"Analysis error: {str(e)}")
            print(f"   ❌ Analysis error: {e}")

        return results

    def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance and structure."""
        print("⚡ Optimizing Database")
        print("-" * 40)

        results: Dict[str, Any] = {
            "operations_performed": [],
            "size_before": 0,
            "size_after": 0,
            "errors": [],
        }

        try:
            if not self.db_path.exists():
                results["errors"].append(f"Database not found at {self.db_path}")
                return results

            # Get initial size
            results["size_before"] = self.db_path.stat().st_size

            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                # Analyze database
                print("   🔍 Analyzing database...")
                cursor.execute("ANALYZE")
                results["operations_performed"].append("ANALYZE")

                # Vacuum database
                print("   🧹 Vacuuming database...")
                cursor.execute("VACUUM")
                results["operations_performed"].append("VACUUM")

                # Update statistics
                print("   📊 Updating statistics...")
                cursor.execute("PRAGMA optimize")
                results["operations_performed"].append("PRAGMA optimize")

                conn.commit()

            # Get final size
            results["size_after"] = self.db_path.stat().st_size
            size_reduction = results["size_before"] - results["size_after"]

            print(f"   📊 Size before: {results['size_before']:,} bytes")
            print(f"   📊 Size after: {results['size_after']:,} bytes")
            if size_reduction > 0:
                print(
                    f"   📉 Size reduced by: {size_reduction:,} bytes ({size_reduction/results['size_before']*100:.1f}%)"
                )
            else:
                print("   📊 No size reduction achieved")

            print("   ✅ Database optimization completed")

        except Exception as e:
            results["errors"].append(f"Optimization error: {str(e)}")
            print(f"   ❌ Optimization error: {e}")

        return results

    def run_comprehensive_maintenance(self) -> Dict[str, Any]:
        """Run comprehensive maintenance operations."""
        print("🔧 Running Comprehensive Dashboard Maintenance")
        print("=" * 60)
        print()

        all_results: Dict[str, Dict[str, Any]] = {}

        # Database analysis
        all_results["database_stats"] = self.analyze_database_stats()
        print()

        # Clean excluded files
        all_results["clean_excluded"] = self.clean_excluded_files()
        print()

        # Fix function parameters
        all_results["fix_parameters"] = self.fix_function_parameters()
        print()

        # Optimize database
        all_results["optimize_database"] = self.optimize_database()
        print()

        class MaintenanceSummary(BaseModel):
            timestamp: str
            operations_completed: int
            total_operations: int
            issues_found: int
            errors_encountered: int

        # Generate summary
        summary_data = {
            "timestamp": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
            "operations_completed": len(
                [
                    r
                    for r in all_results.values()
                    if not (
                        cast(List[Any], r.get("errors", []))
                        if isinstance(r, dict)
                        else [] if isinstance(r, dict) else False
                    )
                ]
            ),
            "total_operations": len(all_results),
            "issues_found": sum(
                len(cast(List[Any], r.get("issues", [])))
                for r in all_results.values()
                if isinstance(r, dict)
            ),
            "errors_encountered": sum(
                len(cast(List[Any], r.get("errors", [])))
                for r in all_results.values()
                if isinstance(r, dict)
            ),
        }

        summary = MaintenanceSummary(**summary_data)
        all_results["summary"] = summary.dict()

        print("📋 Maintenance Summary")
        print("=" * 60)
        print(
            f"Operations completed: {summary.operations_completed}/{summary.total_operations}"
        )
        print(f"Issues found: {summary.issues_found}")
        print(f"Errors encountered: {summary.errors_encountered}")
        print(f"Timestamp: {summary.timestamp}")

        return all_results

    def save_results(
        self, results: Dict[str, Any], filename: Optional[str] = None
    ) -> None:
        """Save maintenance results to JSON file."""
        if not filename:
            timestamp = __import__("time").strftime("%Y%m%d_%H%M%S")
            filename = f"maintenance_results_{timestamp}.json"

        filepath = Path(__file__).parent / filename
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {filepath}")


def main() -> None:
    """Main maintenance runner with command-line interface."""
    parser = argparse.ArgumentParser(description="Dashboard Maintenance Tool")
    parser.add_argument(
        "--operation",
        choices=[
            "fix-parameters",
            "clean-excluded",
            "debug-file",
            "analyze",
            "optimize",
            "all",
        ],
        default="all",
        help="Maintenance operation to perform",
    )
    parser.add_argument("--file-id", type=int, help="File ID for debug-file operation")
    parser.add_argument(
        "--limit", type=int, default=100, help="Limit for fix-parameters operation"
    )
    parser.add_argument("--save", action="store_true", help="Save results to JSON file")
    parser.add_argument("--output", help="Output filename for results")

    args = parser.parse_args()

    maintenance = DashboardMaintenance()

    results: Dict[str, Any] = {}
    if args.operation == "all":
        results = maintenance.run_comprehensive_maintenance()
    elif args.operation == "fix-parameters":
        results = {"fix_parameters": maintenance.fix_function_parameters(args.limit)}
    elif args.operation == "clean-excluded":
        results = {"clean_excluded": maintenance.clean_excluded_files()}
    elif args.operation == "debug-file":
        if not args.file_id:
            print("❌ --file-id is required for debug-file operation")
            return
        results = {"debug_file": maintenance.debug_file_detailed(args.file_id)}
    elif args.operation == "analyze":
        results = {"database_stats": maintenance.analyze_database_stats()}
    elif args.operation == "optimize":
        results = {"optimize_database": maintenance.optimize_database()}

    if args.save:
        maintenance.save_results(results, args.output)


if __name__ == "__main__":
    main()
