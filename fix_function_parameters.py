#!/usr/bin/env python3
"""
Fix Function Parameters Issue
Ensure function parameters are properly populated and returned by API
"""

import ast
import sqlite3
import sys
from pathlib import Path

# Add API path
sys.path.append(".")
from api.sqlite_backend import DocumentationDatabase


def fix_function_parameters():
    """Fix function parameters by re-parsing source files."""
    print("🔧 Fixing Function Parameters")
    print("-" * 40)

    project_root = Path(__file__).parent.parent
    db_path = (
        project_root / "docs" / "interactive-documentation-suite" / "documentation.db"
    )

    db = DocumentationDatabase(str(db_path))

    with db._get_connection() as conn:
        cursor = conn.cursor()

        # Get functions that need parameter data (empty parameters but have parameters_count > 0)
        cursor.execute(
            """
            SELECT f.id, f.name, f.file_path, f.line_number, f.parameters_count
            FROM functions f
            WHERE (f.parameters IS NULL OR f.parameters = '') 
            AND f.parameters_count > 0
            LIMIT 50
        """
        )

        functions_to_fix = cursor.fetchall()
        print(f"📝 Found {len(functions_to_fix)} functions needing parameter fixes")

        fixed_count = 0

        for func_id, func_name, file_path, line_number, param_count in functions_to_fix:
            try:
                # Try to read the source file
                source_file = project_root / file_path.replace("\\", "/").lstrip("/")
                if source_file.exists():
                    with open(source_file, "r", encoding="utf-8", errors="ignore") as f:
                        source_code = f.read()

                    # Parse with AST to extract function parameters
                    tree = ast.parse(source_code)

                    for node in ast.walk(tree):
                        if (
                            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and node.name == func_name
                            and node.lineno == line_number
                        ):

                            # Extract parameters
                            params = []

                            # Regular arguments
                            for arg in node.args.args:
                                param_str = arg.arg
                                if arg.annotation:
                                    try:
                                        param_str += f": {ast.unparse(arg.annotation)}"
                                    except:
                                        param_str += ": Any"
                                params.append(param_str)

                            # Add defaults
                            defaults = node.args.defaults
                            if defaults:
                                num_defaults = len(defaults)
                                for i, default in enumerate(defaults):
                                    param_idx = len(params) - num_defaults + i
                                    if param_idx >= 0 and param_idx < len(params):
                                        try:
                                            default_str = ast.unparse(default)
                                            params[param_idx] += f" = {default_str}"
                                        except:
                                            params[param_idx] += " = ..."

                            # Add *args
                            if node.args.vararg:
                                vararg_str = f"*{node.args.vararg.arg}"
                                if node.args.vararg.annotation:
                                    try:
                                        vararg_str += f": {ast.unparse(node.args.vararg.annotation)}"
                                    except:
                                        pass
                                params.append(vararg_str)

                            # Add **kwargs
                            if node.args.kwarg:
                                kwarg_str = f"**{node.args.kwarg.arg}"
                                if node.args.kwarg.annotation:
                                    try:
                                        kwarg_str += f": {ast.unparse(node.args.kwarg.annotation)}"
                                    except:
                                        pass
                                params.append(kwarg_str)

                            parameters_str = ", ".join(params)

                            # Update database
                            cursor.execute(
                                """
                                UPDATE functions 
                                SET parameters = ?
                                WHERE id = ?
                            """,
                                (parameters_str, func_id),
                            )

                            fixed_count += 1
                            print(f"   ✅ Fixed {func_name}: {parameters_str}")
                            break

            except Exception as e:
                print(f"   ⚠️  Failed to fix {func_name}: {str(e)}")

        conn.commit()
        print(f"\n✅ Fixed {fixed_count} functions")

        # Verify the fix
        cursor.execute(
            """
            SELECT COUNT(*) FROM functions 
            WHERE parameters IS NOT NULL AND parameters != ''
        """
        )
        total_with_params = cursor.fetchone()[0]
        print(f"📊 Total functions with parameters: {total_with_params}")


def test_api_response():
    """Test if API now returns parameters."""
    print("\n🌐 Testing API Response")
    print("-" * 40)

    import requests

    try:
        response = requests.get("http://localhost:8001/api/functions?limit=3")
        if response.status_code == 200:
            data = response.json()
            functions = data.get("data", [])

            for func in functions:
                func_id = func.get("id")
                func_name = func.get("name")
                parameters = func.get("parameters", "NOT_FOUND")
                param_count = func.get("parameters_count", 0)

                print(f"   Function {func_id}: {func_name}")
                print(f"     Parameters: {parameters}")
                print(f"     Count: {param_count}")
                print()
        else:
            print(f"❌ API error: {response.status_code}")

    except Exception as e:
        print(f"❌ API test failed: {e}")


if __name__ == "__main__":
    fix_function_parameters()
    test_api_response()
