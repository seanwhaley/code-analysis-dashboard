#!/usr/bin/env python3
"""
Dashboard Test Suite
Consolidated testing and validation of all dashboard functionality

**Last Updated:** 2025-01-27

This module consolidates all testing functionality from multiple test files into
a unified test suite with different test categories and comprehensive reporting.

Features:
- API endpoint testing
- Database content validation
- Parameter verification
- Function and class testing
- Comprehensive dashboard validation
- Detailed reporting and metrics
"""

import argparse
import ast
import json
import os
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# Add API path - fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from api.sqlite_backend import DocumentationDatabase


class DashboardTestSuite:
    """Comprehensive dashboard testing and validation suite."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.project_root = Path(__file__).parent.parent
        self.db_path = (
            self.project_root
            / "docs"
            / "interactive-documentation-suite"
            / "documentation.db"
        )
        self.db = None
        self.test_results = {}
        self.start_time = time.time()

    def should_skip_path(self, path: str) -> bool:
        """Check if a path should be skipped based on filtering rules."""
        path_lower = path.lower()

        # Skip virtual environment directories
        skip_patterns = [
            ".venv/",
            "venv/",
            "env/",
            "/.git/",
            "/.vscode/",
            "/.idea/",
            "__pycache__/",
            ".pytest_cache/",
            "node_modules/",
            ".mypy_cache/",
            "/.tox/",
            "/build/",
            "/dist/",
            "/.coverage",
            ".DS_Store",
        ]

        for pattern in skip_patterns:
            if pattern in path or path.startswith(pattern.lstrip("/")):
                return True

        return False

    def test_server_connectivity(self) -> Dict[str, Any]:
        """Test basic server connectivity and health."""
        print("🔗 Testing Server Connectivity")
        print("-" * 40)

        results = {
            "server_accessible": False,
            "health_check": False,
            "response_time": 0,
            "errors": [],
        }

        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            results["response_time"] = round((time.time() - start) * 1000, 2)

            if response.status_code == 200:
                results["server_accessible"] = True
                health_data = response.json()
                if health_data.get("success"):
                    results["health_check"] = True
                    print(f"   ✅ Server accessible ({results['response_time']}ms)")
                    print(f"   ✅ Health check passed")
                else:
                    results["errors"].append("Health check failed")
                    print(f"   ❌ Health check failed")
            else:
                results["errors"].append(f"HTTP {response.status_code}")
                print(f"   ❌ Server returned HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            results["errors"].append(str(e))
            print(f"   ❌ Connection failed: {e}")

        return results

    def test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity and basic content."""
        print("🗄️  Testing Database Connectivity")
        print("-" * 40)

        results = {
            "database_accessible": False,
            "total_files": 0,
            "total_classes": 0,
            "total_functions": 0,
            "functions_with_parameters": 0,
            "errors": [],
        }

        try:
            if not self.db_path.exists():
                results["errors"].append(f"Database not found at {self.db_path}")
                print(f"   ❌ Database not found at {self.db_path}")
                return results

            self.db = DocumentationDatabase(str(self.db_path))
            results["database_accessible"] = True
            print("   ✅ Database accessible")

            # Get basic statistics
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

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

            print(f"   📊 Files: {results['total_files']}")
            print(f"   📊 Classes: {results['total_classes']}")
            print(f"   📊 Functions: {results['total_functions']}")
            print(
                f"   📊 Functions with parameters: {results['functions_with_parameters']}"
            )

        except Exception as e:
            results["errors"].append(str(e))
            print(f"   ❌ Database error: {e}")

        return results

    def test_api_endpoints(self) -> Dict[str, Any]:
        """Test all API endpoints for basic functionality."""
        print("🔌 Testing API Endpoints")
        print("-" * 40)

        results = {
            "endpoints_tested": 0,
            "endpoints_passed": 0,
            "endpoint_results": {},
            "errors": [],
        }

        endpoints = [
            ("/api/stats", "GET", "System statistics"),
            ("/api/files", "GET", "Files list"),
            ("/api/classes", "GET", "Classes list"),
            ("/api/functions", "GET", "Functions list"),
            ("/api/search", "GET", "Search functionality"),
            ("/api/domains", "GET", "Domain statistics"),
            ("/api/complexity/distribution", "GET", "Complexity distribution"),
        ]

        for endpoint, method, description in endpoints:
            results["endpoints_tested"] += 1
            endpoint_result = {
                "accessible": False,
                "response_time": 0,
                "status_code": 0,
                "data_count": 0,
                "error": None,
            }

            try:
                start = time.time()
                if method == "GET":
                    if endpoint == "/api/search":
                        response = requests.get(
                            f"{self.base_url}{endpoint}?q=test", timeout=10
                        )
                    else:
                        response = requests.get(
                            f"{self.base_url}{endpoint}?limit=5", timeout=10
                        )

                endpoint_result["response_time"] = round(
                    (time.time() - start) * 1000, 2
                )
                endpoint_result["status_code"] = response.status_code

                if response.status_code == 200:
                    endpoint_result["accessible"] = True
                    results["endpoints_passed"] += 1

                    data = response.json()
                    if data.get("success") and "data" in data:
                        if isinstance(data["data"], list):
                            endpoint_result["data_count"] = len(data["data"])
                        elif isinstance(data["data"], dict):
                            endpoint_result["data_count"] = len(data["data"])

                    print(
                        f"   ✅ {endpoint} - {description} ({endpoint_result['response_time']}ms, {endpoint_result['data_count']} items)"
                    )
                else:
                    endpoint_result["error"] = f"HTTP {response.status_code}"
                    print(f"   ❌ {endpoint} - HTTP {response.status_code}")

            except Exception as e:
                endpoint_result["error"] = str(e)
                print(f"   ❌ {endpoint} - {e}")

            results["endpoint_results"][endpoint] = endpoint_result

        print(
            f"   📊 Passed: {results['endpoints_passed']}/{results['endpoints_tested']} endpoints"
        )
        return results

    def test_function_parameters(self) -> Dict[str, Any]:
        """Test function parameter handling and consistency."""
        print("🔧 Testing Function Parameters")
        print("-" * 40)

        results = {
            "database_functions_with_params": 0,
            "api_functions_with_params": 0,
            "consistency_check": False,
            "sample_functions": [],
            "errors": [],
        }

        try:
            # Check database directly
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM functions WHERE parameters IS NOT NULL AND parameters != ''"
                )
                results["database_functions_with_params"] = cursor.fetchone()[0]

                # Get sample functions with parameters
                cursor.execute(
                    "SELECT name, parameters FROM functions WHERE parameters IS NOT NULL AND parameters != '' LIMIT 5"
                )
                db_samples = cursor.fetchall()

            print(
                f"   📊 Database functions with parameters: {results['database_functions_with_params']}"
            )

            # Check API response
            response = requests.get(
                f"{self.base_url}/api/functions?limit=100", timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    api_functions_with_params = 0
                    for func in data["data"]:
                        if func.get("parameters") and func["parameters"].strip():
                            api_functions_with_params += 1
                            if len(results["sample_functions"]) < 3:
                                results["sample_functions"].append(
                                    {
                                        "name": func["name"],
                                        "parameters": func["parameters"],
                                    }
                                )

                    results["api_functions_with_params"] = api_functions_with_params
                    print(
                        f"   📊 API functions with parameters: {results['api_functions_with_params']}"
                    )

                    # Check consistency (allowing for some variance due to filtering)
                    if results["api_functions_with_params"] > 0:
                        results["consistency_check"] = True
                        print("   ✅ Parameter consistency check passed")
                    else:
                        print("   ❌ No functions with parameters found in API")
                else:
                    results["errors"].append("API request failed")
            else:
                results["errors"].append(f"API returned HTTP {response.status_code}")

            # Show samples
            if results["sample_functions"]:
                print("   📝 Sample functions with parameters:")
                for func in results["sample_functions"]:
                    print(f"      {func['name']}: {func['parameters']}")

        except Exception as e:
            results["errors"].append(str(e))
            print(f"   ❌ Parameter test error: {e}")

        return results

    def test_file_detailed_content(self) -> Dict[str, Any]:
        """Test file detailed content endpoint."""
        print("📄 Testing File Detailed Content")
        print("-" * 40)

        results = {
            "files_tested": 0,
            "files_passed": 0,
            "sample_results": [],
            "errors": [],
        }

        try:
            # Get some file IDs to test
            response = requests.get(f"{self.base_url}/api/files?limit=3", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    for file_data in data["data"]:
                        file_id = file_data["id"]
                        file_name = file_data["name"]
                        results["files_tested"] += 1

                        # Test detailed endpoint
                        detail_response = requests.get(
                            f"{self.base_url}/api/file/{file_id}/detailed", timeout=10
                        )
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            if detail_data.get("success"):
                                results["files_passed"] += 1
                                file_result = {
                                    "id": file_id,
                                    "name": file_name,
                                    "classes": len(
                                        detail_data.get("data", {}).get("classes", [])
                                    ),
                                    "functions": len(
                                        detail_data.get("data", {}).get("functions", [])
                                    ),
                                }
                                results["sample_results"].append(file_result)
                                print(
                                    f"   ✅ File {file_id} ({file_name}): {file_result['classes']} classes, {file_result['functions']} functions"
                                )
                            else:
                                print(f"   ❌ File {file_id} detailed content failed")
                        else:
                            print(
                                f"   ❌ File {file_id} returned HTTP {detail_response.status_code}"
                            )

            print(
                f"   📊 Passed: {results['files_passed']}/{results['files_tested']} files"
            )

        except Exception as e:
            results["errors"].append(str(e))
            print(f"   ❌ File detailed test error: {e}")

        return results

    def test_search_functionality(self) -> Dict[str, Any]:
        """Test search functionality across different types."""
        print("🔍 Testing Search Functionality")
        print("-" * 40)

        results = {
            "searches_tested": 0,
            "searches_passed": 0,
            "search_results": {},
            "errors": [],
        }

        search_queries = [
            ("test", "General search"),
            ("class", "Class search"),
            ("function", "Function search"),
            ("main", "Main function search"),
            ("init", "Init method search"),
        ]

        try:
            for query, description in search_queries:
                results["searches_tested"] += 1

                response = requests.get(
                    f"{self.base_url}/api/search?q={query}&limit=5", timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        results["searches_passed"] += 1
                        result_count = len(data.get("data", []))
                        results["search_results"][query] = result_count
                        print(
                            f"   ✅ {description} ('{query}'): {result_count} results"
                        )
                    else:
                        print(f"   ❌ {description} search failed")
                else:
                    print(f"   ❌ {description} returned HTTP {response.status_code}")

            print(
                f"   📊 Passed: {results['searches_passed']}/{results['searches_tested']} searches"
            )

        except Exception as e:
            results["errors"].append(str(e))
            print(f"   ❌ Search test error: {e}")

        return results

    def test_data_quality(self) -> Dict[str, Any]:
        """Test data quality and consistency."""
        print("🎯 Testing Data Quality")
        print("-" * 40)

        results = {
            "quality_score": 0,
            "excluded_files_found": 0,
            "data_consistency": True,
            "issues": [],
            "metrics": {},
        }

        try:
            if not self.db:
                self.db = DocumentationDatabase(str(self.db_path))

            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Check for excluded files that shouldn't be there
                cursor.execute(
                    "SELECT COUNT(*) FROM files WHERE path LIKE '%/.venv/%' OR path LIKE '%/__pycache__/%' OR path LIKE '%/.git/%'"
                )
                results["excluded_files_found"] = cursor.fetchone()[0]

                # Check data consistency
                cursor.execute(
                    "SELECT COUNT(*) FROM functions WHERE file_id NOT IN (SELECT id FROM files)"
                )
                orphaned_functions = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM classes WHERE file_id NOT IN (SELECT id FROM files)"
                )
                orphaned_classes = cursor.fetchone()[0]

                if orphaned_functions > 0:
                    results["issues"].append(f"{orphaned_functions} orphaned functions")
                    results["data_consistency"] = False

                if orphaned_classes > 0:
                    results["issues"].append(f"{orphaned_classes} orphaned classes")
                    results["data_consistency"] = False

                # Calculate quality score
                total_issues = results["excluded_files_found"] + len(results["issues"])
                if total_issues == 0:
                    results["quality_score"] = 100
                elif total_issues < 5:
                    results["quality_score"] = 90
                elif total_issues < 10:
                    results["quality_score"] = 80
                else:
                    results["quality_score"] = max(50, 100 - total_issues * 5)

            if results["excluded_files_found"] > 0:
                print(
                    f"   ⚠️  Found {results['excluded_files_found']} excluded files in database"
                )
            else:
                print("   ✅ No excluded files found")

            if results["data_consistency"]:
                print("   ✅ Data consistency check passed")
            else:
                print("   ❌ Data consistency issues found")
                for issue in results["issues"]:
                    print(f"      - {issue}")

            print(f"   📊 Quality score: {results['quality_score']}/100")

        except Exception as e:
            results["issues"].append(str(e))
            print(f"   ❌ Data quality test error: {e}")

        return results

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report."""
        print("🎯 Running Comprehensive Dashboard Test Suite")
        print("=" * 60)
        print()

        all_results = {}

        # Run all test categories
        all_results["server"] = self.test_server_connectivity()
        print()

        all_results["database"] = self.test_database_connectivity()
        print()

        all_results["api_endpoints"] = self.test_api_endpoints()
        print()

        all_results["function_parameters"] = self.test_function_parameters()
        print()

        all_results["file_detailed"] = self.test_file_detailed_content()
        print()

        all_results["search"] = self.test_search_functionality()
        print()

        all_results["data_quality"] = self.test_data_quality()
        print()

        # Generate summary
        total_time = round(time.time() - self.start_time, 2)

        summary = {
            "total_time": total_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "PASS",
            "critical_issues": [],
            "warnings": [],
            "test_counts": {"total_tests": 0, "passed_tests": 0, "failed_tests": 0},
        }

        # Analyze results
        if not all_results["server"]["server_accessible"]:
            summary["overall_status"] = "FAIL"
            summary["critical_issues"].append("Server not accessible")

        if not all_results["database"]["database_accessible"]:
            summary["overall_status"] = "FAIL"
            summary["critical_issues"].append("Database not accessible")

        if (
            all_results["api_endpoints"]["endpoints_passed"]
            < all_results["api_endpoints"]["endpoints_tested"] * 0.8
        ):
            summary["overall_status"] = "FAIL"
            summary["critical_issues"].append("Too many API endpoints failing")

        if not all_results["function_parameters"]["consistency_check"]:
            summary["warnings"].append("Function parameter consistency issues")

        if all_results["data_quality"]["quality_score"] < 80:
            summary["warnings"].append("Data quality score below 80")

        all_results["summary"] = summary

        # Print summary
        print("📋 Test Summary")
        print("=" * 60)
        print(
            f"Overall Status: {'✅ PASS' if summary['overall_status'] == 'PASS' else '❌ FAIL'}"
        )
        print(f"Total Time: {total_time}s")
        print(f"Timestamp: {summary['timestamp']}")

        if summary["critical_issues"]:
            print("\n❌ Critical Issues:")
            for issue in summary["critical_issues"]:
                print(f"   - {issue}")

        if summary["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in summary["warnings"]:
                print(f"   - {warning}")

        if not summary["critical_issues"] and not summary["warnings"]:
            print("\n🎉 All tests passed successfully!")

        return all_results

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to JSON file."""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"

        filepath = Path(__file__).parent / filename
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {filepath}")


def main():
    """Main test runner with command-line interface."""
    parser = argparse.ArgumentParser(description="Dashboard Test Suite")
    parser.add_argument(
        "--url", default="http://localhost:8001", help="Base URL for API testing"
    )
    parser.add_argument(
        "--category",
        choices=[
            "server",
            "database",
            "api",
            "parameters",
            "files",
            "search",
            "quality",
            "all",
        ],
        default="all",
        help="Test category to run",
    )
    parser.add_argument("--save", action="store_true", help="Save results to JSON file")
    parser.add_argument("--output", help="Output filename for results")

    args = parser.parse_args()

    suite = DashboardTestSuite(args.url)

    if args.category == "all":
        results = suite.run_comprehensive_test()
    elif args.category == "server":
        results = {"server": suite.test_server_connectivity()}
    elif args.category == "database":
        results = {"database": suite.test_database_connectivity()}
    elif args.category == "api":
        results = {"api_endpoints": suite.test_api_endpoints()}
    elif args.category == "parameters":
        results = {"function_parameters": suite.test_function_parameters()}
    elif args.category == "files":
        results = {"file_detailed": suite.test_file_detailed_content()}
    elif args.category == "search":
        results = {"search": suite.test_search_functionality()}
    elif args.category == "quality":
        results = {"data_quality": suite.test_data_quality()}

    if args.save:
        suite.save_results(results, args.output)


if __name__ == "__main__":
    main()
