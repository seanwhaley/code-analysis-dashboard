#!/usr/bin/env python3
"""
Consolidated Dashboard Test Suite
Comprehensive testing and validation of all dashboard functionality
"""

import ast
import json
import os
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# Add API path
sys.path.append(os.path.dirname(__file__))
from api.sqlite_backend import DocumentationDatabase


class DashboardTester:
    """Comprehensive dashboard testing and validation."""

    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.project_root = Path(__file__).parent.parent
        self.db_path = (
            self.project_root
            / "docs"
            / "interactive-documentation-suite"
            / "documentation.db"
        )
        self.db = None
        self.test_results = {}

    def should_skip_path(self, path: str) -> bool:
        """Check if a path should be skipped based on filtering rules."""
        path_lower = path.lower()

        # Skip hidden directories and files (starting with .)
        if "/.git/" in path or path.startswith(".git/"):
            return True
        if "/.vscode/" in path or path.startswith(".vscode/"):
            return True
        if path.startswith("."):
            return True

        # Skip cache directories
        if "__pycache__" in path:
            return True
        if ".mypy_cache" in path:
            return True
        if ".pytest_cache" in path:
            return True
        if "node_modules" in path:
            return True

        # Skip build/dist directories
        if "/build/" in path or path.startswith("build/"):
            return True
        if "/dist/" in path or path.startswith("dist/"):
            return True

        # Skip temporary files
        if path.endswith(".tmp") or path.endswith(".temp"):
            return True
        if path.endswith(".pyc") or path.endswith(".pyo"):
            return True

        return False

    def test_database_filtering(self) -> Dict:
        """Test database filtering to ensure proper file exclusion."""
        print("🔍 Testing Database Filtering")
        print("-" * 40)

        results = {
            "total_files_in_db": 0,
            "excluded_files": 0,
            "file_types": {},
            "domains": {},
            "issues": [],
        }

        try:
            self.db = DocumentationDatabase(str(self.db_path))

            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Get all files and check filtering
                cursor.execute("SELECT id, name, path, file_type, domain FROM files")
                all_files = cursor.fetchall()

                excluded_count = 0
                valid_files = []

                for file_id, name, path, file_type, domain in all_files:
                    if self.should_skip_path(path):
                        excluded_count += 1
                        results["issues"].append(f"Should exclude: {path}")
                    else:
                        valid_files.append((file_id, name, path, file_type, domain))

                results["total_files_in_db"] = len(all_files)
                results["excluded_files"] = excluded_count
                results["valid_files"] = len(valid_files)

                # Analyze file types
                file_type_counts = Counter(f[3] for f in valid_files)
                results["file_types"] = dict(file_type_counts)

                # Analyze domains
                domain_counts = Counter(f[4] for f in valid_files if f[4])
                results["domains"] = dict(domain_counts)

                print(f"✅ Total files in database: {results['total_files_in_db']}")
                print(f"⚠️  Files that should be excluded: {results['excluded_files']}")
                print(f"✅ Valid files: {results['valid_files']}")

                if results["excluded_files"] > 0:
                    print(
                        f"❌ Database contains {results['excluded_files']} files that should be excluded"
                    )
                    for issue in results["issues"][:5]:  # Show first 5
                        print(f"   - {issue}")
                    if len(results["issues"]) > 5:
                        print(f"   ... and {len(results['issues']) - 5} more")

        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Database filtering test failed: {e}")

        return results

    def test_api_endpoints(self) -> Dict:
        """Test all API endpoints for functionality and data quality."""
        print("\n🌐 Testing API Endpoints")
        print("-" * 40)

        endpoints = {
            "health": "/health",
            "stats": "/api/stats",
            "files": "/api/files?limit=10",
            "classes": "/api/classes?limit=10",
            "functions": "/api/functions?limit=10",
            "services": "/api/services?limit=10",
            "search": "/api/search?q=logging&limit=5",
        }

        results = {}

        for name, endpoint in endpoints.items():
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    if name == "health":
                        results[name] = {"status": "ok", "response": data}
                    elif "data" in data:
                        count = (
                            len(data["data"]) if isinstance(data["data"], list) else 1
                        )
                        total = data.get("pagination", {}).get("total", count)
                        results[name] = {
                            "status": "ok",
                            "count": count,
                            "total": total,
                            "sample_data": (
                                data["data"][:2]
                                if isinstance(data["data"], list)
                                else data["data"]
                            ),
                        }
                    else:
                        results[name] = {"status": "ok", "data": data}

                    print(
                        f"✅ {name:<10} - OK ({results[name].get('total', 'N/A')} total)"
                    )
                else:
                    results[name] = {"status": "error", "code": response.status_code}
                    print(f"❌ {name:<10} - HTTP {response.status_code}")

            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
                print(f"❌ {name:<10} - {str(e)}")

        return results

    def test_data_linking(self) -> Dict:
        """Test data linking between different content types."""
        print("\n🔗 Testing Data Linking")
        print("-" * 40)

        results = {
            "file_to_classes": 0,
            "file_to_functions": 0,
            "class_methods": 0,
            "function_parameters": 0,
            "issues": [],
        }

        try:
            # Test file to classes linking
            response = requests.get(f"{self.base_url}/api/files?limit=5", timeout=10)
            if response.status_code == 200:
                files_data = response.json()
                for file_data in files_data.get("data", []):
                    file_id = file_data.get("id")
                    if file_id:
                        # Check classes in this file
                        class_response = requests.get(
                            f"{self.base_url}/api/classes?file_id={file_id}", timeout=10
                        )
                        if class_response.status_code == 200:
                            class_data = class_response.json()
                            class_count = len(class_data.get("data", []))
                            results["file_to_classes"] += class_count

                            # Check if classes have method counts
                            for class_item in class_data.get("data", []):
                                methods_count = class_item.get("methods_count", 0)
                                if methods_count > 0:
                                    results["class_methods"] += methods_count
                                elif class_item.get("name") and not class_item.get(
                                    "name"
                                ).startswith("_"):
                                    results["issues"].append(
                                        f"Class {class_item.get('name')} has no methods count"
                                    )

                        # Check functions in this file
                        func_response = requests.get(
                            f"{self.base_url}/api/functions?file_id={file_id}",
                            timeout=10,
                        )
                        if func_response.status_code == 200:
                            func_data = func_response.json()
                            func_count = len(func_data.get("data", []))
                            results["file_to_functions"] += func_count

                            # Check if functions have parameters
                            for func_item in func_data.get("data", []):
                                params = func_item.get("parameters", "")
                                if params and params.strip():
                                    results["function_parameters"] += 1
                                elif func_item.get("name") and not func_item.get(
                                    "name"
                                ).startswith("_"):
                                    results["issues"].append(
                                        f"Function {func_item.get('name')} has no parameters data"
                                    )

            print(f"✅ File-to-classes links: {results['file_to_classes']}")
            print(f"✅ File-to-functions links: {results['file_to_functions']}")
            print(f"✅ Classes with methods: {results['class_methods']}")
            print(f"✅ Functions with parameters: {results['function_parameters']}")

            if results["issues"]:
                print(f"⚠️  Data linking issues found: {len(results['issues'])}")
                for issue in results["issues"][:3]:
                    print(f"   - {issue}")

        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Data linking test failed: {e}")

        return results

    def test_class_methods_population(self) -> Dict:
        """Test class methods count and details population."""
        print("\n🏗️ Testing Class Methods Population")
        print("-" * 40)

        results = {
            "total_classes": 0,
            "classes_with_methods": 0,
            "classes_without_methods": 0,
            "method_details_available": 0,
            "issues": [],
        }

        try:
            # Get classes data
            response = requests.get(f"{self.base_url}/api/classes?limit=50", timeout=10)
            if response.status_code == 200:
                data = response.json()
                classes = data.get("data", [])
                results["total_classes"] = len(classes)

                for class_item in classes:
                    class_name = class_item.get("name", "Unknown")
                    methods_count = class_item.get("methods_count", 0)

                    if methods_count > 0:
                        results["classes_with_methods"] += 1

                        # Check if we can get detailed class info
                        class_id = class_item.get("id")
                        if class_id:
                            detail_response = requests.get(
                                f"{self.base_url}/api/classes/{class_id}", timeout=10
                            )
                            if detail_response.status_code == 200:
                                detail_data = detail_response.json()
                                if detail_data.get("success"):
                                    results["method_details_available"] += 1
                    else:
                        results["classes_without_methods"] += 1
                        if not class_name.startswith("_"):  # Skip private classes
                            results["issues"].append(
                                f"Class '{class_name}' has no methods count"
                            )

                print(f"✅ Total classes tested: {results['total_classes']}")
                print(f"✅ Classes with methods: {results['classes_with_methods']}")
                print(
                    f"❌ Classes without methods: {results['classes_without_methods']}"
                )
                print(
                    f"✅ Method details available: {results['method_details_available']}"
                )

        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Class methods test failed: {e}")

        return results

    def test_function_parameters(self) -> Dict:
        """Test function parameters population."""
        print("\n⚙️ Testing Function Parameters")
        print("-" * 40)

        results = {
            "total_functions": 0,
            "functions_with_params": 0,
            "functions_without_params": 0,
            "param_details_available": 0,
            "issues": [],
        }

        try:
            # Get functions data
            response = requests.get(
                f"{self.base_url}/api/functions?limit=50", timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                functions = data.get("data", [])
                results["total_functions"] = len(functions)

                for func_item in functions:
                    func_name = func_item.get("name", "Unknown")
                    parameters = func_item.get("parameters", "")

                    if parameters and parameters.strip():
                        results["functions_with_params"] += 1

                        # Check parameter details
                        if "," in parameters or "=" in parameters or ":" in parameters:
                            results["param_details_available"] += 1
                    else:
                        results["functions_without_params"] += 1
                        if not func_name.startswith("_"):  # Skip private functions
                            results["issues"].append(
                                f"Function '{func_name}' has no parameters data"
                            )

                print(f"✅ Total functions tested: {results['total_functions']}")
                print(
                    f"✅ Functions with parameters: {results['functions_with_params']}"
                )
                print(
                    f"❌ Functions without parameters: {results['functions_without_params']}"
                )
                print(
                    f"✅ Parameter details available: {results['param_details_available']}"
                )

        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Function parameters test failed: {e}")

        return results

    def fix_database_filtering(self) -> Dict:
        """Fix database filtering by removing excluded files."""
        print("\n🔧 Fixing Database Filtering")
        print("-" * 40)

        results = {
            "files_removed": 0,
            "classes_removed": 0,
            "functions_removed": 0,
            "issues": [],
        }

        try:
            self.db = DocumentationDatabase(str(self.db_path))

            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Get files that should be excluded
                cursor.execute("SELECT id, name, path FROM files")
                all_files = cursor.fetchall()

                files_to_remove = []
                for file_id, name, path in all_files:
                    if self.should_skip_path(path):
                        files_to_remove.append(file_id)

                if files_to_remove:
                    print(f"🗑️  Removing {len(files_to_remove)} excluded files...")

                    # Remove related classes and functions first
                    for file_id in files_to_remove:
                        # Remove classes
                        cursor.execute(
                            "DELETE FROM classes WHERE file_id = ?", (file_id,)
                        )
                        classes_removed = cursor.rowcount
                        results["classes_removed"] += classes_removed

                        # Remove functions
                        cursor.execute(
                            "DELETE FROM functions WHERE file_id = ?", (file_id,)
                        )
                        functions_removed = cursor.rowcount
                        results["functions_removed"] += functions_removed

                        # Remove file
                        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                        results["files_removed"] += cursor.rowcount

                    conn.commit()
                    print(f"✅ Removed {results['files_removed']} files")
                    print(f"✅ Removed {results['classes_removed']} classes")
                    print(f"✅ Removed {results['functions_removed']} functions")
                else:
                    print("✅ No files need to be removed")

        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Database filtering fix failed: {e}")

        return results

    def run_comprehensive_test(self) -> Dict:
        """Run all tests and return comprehensive results."""
        print("🎯 CONSOLIDATED DASHBOARD TEST SUITE")
        print("=" * 60)

        start_time = time.time()

        # Run all tests
        self.test_results = {
            "database_filtering": self.test_database_filtering(),
            "api_endpoints": self.test_api_endpoints(),
            "data_linking": self.test_data_linking(),
            "class_methods": self.test_class_methods_population(),
            "function_parameters": self.test_function_parameters(),
        }

        # Generate summary
        end_time = time.time()
        self.test_results["summary"] = {
            "total_time": end_time - start_time,
            "tests_run": len(self.test_results) - 1,  # Exclude summary itself
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.print_summary()
        return self.test_results

    def print_summary(self):
        """Print test summary."""
        print("\n📊 TEST SUMMARY")
        print("=" * 60)

        # API Status
        api_results = self.test_results.get("api_endpoints", {})
        working_apis = sum(
            1
            for r in api_results.values()
            if isinstance(r, dict) and r.get("status") == "ok"
        )
        total_apis = len(api_results)
        print(f"🌐 API Endpoints: {working_apis}/{total_apis} working")

        # Database Status
        db_results = self.test_results.get("database_filtering", {})
        excluded_files = db_results.get("excluded_files", 0)
        if excluded_files > 0:
            print(f"⚠️  Database Filtering: {excluded_files} files should be excluded")
        else:
            print(f"✅ Database Filtering: Clean")

        # Data Quality
        class_results = self.test_results.get("class_methods", {})
        func_results = self.test_results.get("function_parameters", {})

        classes_with_methods = class_results.get("classes_with_methods", 0)
        total_classes = class_results.get("total_classes", 0)
        if total_classes > 0:
            class_percentage = (classes_with_methods / total_classes) * 100
            print(
                f"🏗️  Class Methods: {classes_with_methods}/{total_classes} ({class_percentage:.1f}%) populated"
            )

        functions_with_params = func_results.get("functions_with_params", 0)
        total_functions = func_results.get("total_functions", 0)
        if total_functions > 0:
            func_percentage = (functions_with_params / total_functions) * 100
            print(
                f"⚙️  Function Parameters: {functions_with_params}/{total_functions} ({func_percentage:.1f}%) populated"
            )

        # Overall Status
        issues = []
        for test_name, test_result in self.test_results.items():
            if isinstance(test_result, dict) and test_result.get("issues"):
                issues.extend(test_result["issues"])

        if issues:
            print(f"\n⚠️  Issues Found: {len(issues)}")
            print("Top issues:")
            for issue in issues[:5]:
                print(f"   - {issue}")
        else:
            print(f"\n✅ No major issues found")

        print(
            f"\n⏱️  Test completed in {self.test_results['summary']['total_time']:.2f} seconds"
        )
        print(f"🎯 Dashboard URL: {self.base_url}")


def main():
    """Run consolidated dashboard tests."""
    tester = DashboardTester()

    # Check if server is running
    try:
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Dashboard server is not running!")
            print(f"Please start the server with: python launch.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Dashboard server is not running!")
        print(f"Please start the server with: python launch.py")
        return

    # Run comprehensive tests
    results = tester.run_comprehensive_test()

    # Offer to fix issues
    db_results = results.get("database_filtering", {})
    if db_results.get("excluded_files", 0) > 0:
        print(f"\n🔧 FIXING DATABASE ISSUES")
        print("-" * 40)
        fix_results = tester.fix_database_filtering()
        print(f"✅ Database cleanup completed")

    # Save results
    results_file = Path(__file__).parent / "test_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📄 Detailed results saved to: {results_file}")


if __name__ == "__main__":
    main()
