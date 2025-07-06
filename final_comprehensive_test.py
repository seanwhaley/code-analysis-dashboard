#!/usr/bin/env python3
"""
Final Comprehensive Dashboard Test Suite
Consolidates all testing functionality and validates complete dashboard operation
"""

import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# Add API path
sys.path.append(os.path.dirname(__file__))
from api.sqlite_backend import DocumentationDatabase


class FinalDashboardValidator:
    """Final comprehensive validation of all dashboard functionality."""

    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.project_root = Path(__file__).parent.parent
        self.db_path = (
            self.project_root
            / "docs"
            / "interactive-documentation-suite"
            / "documentation.db"
        )
        self.test_results = {}

    def test_database_quality(self) -> Dict:
        """Test database quality and content."""
        print("📊 Testing Database Quality")
        print("-" * 40)
        print("   🔄 Connecting to database...")

        results = {
            "total_files": 0,
            "total_classes": 0,
            "total_functions": 0,
            "functions_with_parameters": 0,
            "classes_with_methods": 0,
            "excluded_files_found": 0,
            "quality_score": 0,
        }

        try:
            db = DocumentationDatabase(str(self.db_path))
            print("   ✅ Database connected")

            with db._get_connection() as conn:
                cursor = conn.cursor()
                print("   🔄 Counting files...")

                # Basic counts
                cursor.execute("SELECT COUNT(*) FROM files")
                results["total_files"] = cursor.fetchone()[0]
                print("   🔄 Counting classes...")

                cursor.execute("SELECT COUNT(*) FROM classes")
                results["total_classes"] = cursor.fetchone()[0]
                print("   🔄 Counting functions...")

                cursor.execute("SELECT COUNT(*) FROM functions")
                results["total_functions"] = cursor.fetchone()[0]
                print("   🔄 Analyzing quality metrics...")

                # Quality metrics
                cursor.execute(
                    'SELECT COUNT(*) FROM functions WHERE parameters IS NOT NULL AND parameters != ""'
                )
                results["functions_with_parameters"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM classes WHERE methods_count > 0")
                results["classes_with_methods"] = cursor.fetchone()[0]

                # Check for excluded files
                cursor.execute(
                    "SELECT COUNT(*) FROM files WHERE path LIKE '%.venv/%' OR path LIKE '%__pycache__%' OR path LIKE '%.git/%'"
                )
                results["excluded_files_found"] = cursor.fetchone()[0]

                # Calculate quality score
                param_score = (
                    results["functions_with_parameters"]
                    / max(results["total_functions"], 1)
                ) * 100
                method_score = (
                    results["classes_with_methods"] / max(results["total_classes"], 1)
                ) * 100
                exclusion_penalty = (
                    results["excluded_files_found"] * 5
                )  # 5 points penalty per excluded file

                results["quality_score"] = max(
                    0, (param_score + method_score) / 2 - exclusion_penalty
                )

                print(f"✅ Files: {results['total_files']}")
                print(f"✅ Classes: {results['total_classes']}")
                print(f"✅ Functions: {results['total_functions']}")
                print(
                    f"✅ Functions with parameters: {results['functions_with_parameters']} ({param_score:.1f}%)"
                )
                print(
                    f"✅ Classes with methods: {results['classes_with_methods']} ({method_score:.1f}%)"
                )
                print(f"⚠️  Excluded files found: {results['excluded_files_found']}")
                print(f"📊 Quality Score: {results['quality_score']:.1f}/100")

        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Database quality test failed: {e}")

        return results

    def test_api_completeness(self) -> Dict:
        """Test all API endpoints for completeness and data quality."""
        print("\n🌐 Testing API Completeness")
        print("-" * 40)

        # First get a valid file ID
        valid_file_id = None
        try:
            files_response = requests.get(
                f"{self.base_url}/api/files?limit=1", timeout=10
            )
            if files_response.status_code == 200:
                files_data = files_response.json()
                if files_data.get("data"):
                    valid_file_id = files_data["data"][0]["id"]
        except:
            pass

        endpoints = {
            "health": {"url": "/health", "expected_fields": ["status", "database"]},
            "stats": {
                "url": "/api/stats",
                "expected_fields": ["total_files", "total_classes", "total_functions"],
            },
            "files": {
                "url": "/api/files?limit=5",
                "expected_fields": [
                    "name",
                    "path",
                    "complexity",
                    "classes",
                    "functions",
                ],
            },
            "classes": {
                "url": "/api/classes?limit=5",
                "expected_fields": ["name", "file_path", "methods_count", "class_type"],
            },
            "functions": {
                "url": "/api/functions?limit=5",
                "expected_fields": [
                    "name",
                    "file_path",
                    "parameters",
                    "parameters_count",
                ],
            },
            "services": {
                "url": "/api/services?limit=5",
                "expected_fields": ["name", "file_path", "class_type"],
            },
            "search": {
                "url": "/api/search?q=test&limit=5",
                "expected_fields": ["results", "total"],
            },
            "file_detail": {
                "url": f"/api/file/{valid_file_id or 1}/detailed",
                "expected_fields": ["name", "path", "classes", "functions"],
            },
        }

        results = {}

        for name, config in endpoints.items():
            print(f"   🔄 Testing {name} endpoint...")
            try:
                response = requests.get(f"{self.base_url}{config['url']}", timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    # Check expected fields
                    missing_fields = []
                    if name in ["health", "stats"]:
                        check_data = data.get("data", data)
                    elif name == "search":
                        check_data = data
                    elif name == "file_detail":
                        check_data = data.get("data", {})
                    else:
                        check_data = (
                            data.get("data", [{}])[0] if data.get("data") else {}
                        )

                    for field in config["expected_fields"]:
                        if field not in check_data:
                            missing_fields.append(field)

                    results[name] = {
                        "status": "ok",
                        "response_time": response.elapsed.total_seconds(),
                        "data_count": (
                            len(data.get("data", []))
                            if isinstance(data.get("data"), list)
                            else 1
                        ),
                        "missing_fields": missing_fields,
                        "total": data.get("pagination", {}).get(
                            "total", data.get("total", "N/A")
                        ),
                    }

                    status_icon = "✅" if not missing_fields else "⚠️"
                    print(
                        f"{status_icon} {name:<12} - {results[name]['total']} items, {len(missing_fields)} missing fields"
                    )

                else:
                    results[name] = {"status": "error", "code": response.status_code}
                    print(f"❌ {name:<12} - HTTP {response.status_code}")

            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
                print(f"❌ {name:<12} - {str(e)}")

        return results

    def test_data_linking_navigation(self) -> Dict:
        """Test data linking and navigation between content types."""
        print("\n🔗 Testing Data Linking & Navigation")
        print("-" * 40)

        results = {
            "file_to_classes": 0,
            "file_to_functions": 0,
            "class_to_methods": 0,
            "function_parameters_populated": 0,
            "navigation_links_working": 0,
            "issues": [],
        }

        try:
            print("   🔄 Testing file-to-content linking...")
            # Test file to classes/functions linking
            files_response = requests.get(
                f"{self.base_url}/api/files?limit=10", timeout=10
            )
            if files_response.status_code == 200:
                files_data = files_response.json()

                for i, file_data in enumerate(
                    files_data.get("data", [])[:5]
                ):  # Test first 5 files
                    file_id = file_data.get("id")
                    print(
                        f"   🔄 Testing file {i+1}/5: {file_data.get('name', 'Unknown')}"
                    )

                    # Test file detail endpoint
                    detail_response = requests.get(
                        f"{self.base_url}/api/file/{file_id}/detailed", timeout=10
                    )
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        file_detail = detail_data.get("data", {})

                        # Count linked classes and functions
                        classes = file_detail.get("classes", [])
                        functions = file_detail.get("functions", [])

                        results["file_to_classes"] += len(classes)
                        results["file_to_functions"] += len(functions)

                        # Test class methods linking
                        for cls in classes:
                            class_id = cls.get("id")
                            if class_id:
                                methods_response = requests.get(
                                    f"{self.base_url}/api/functions?class_id={class_id}",
                                    timeout=10,
                                )
                                if methods_response.status_code == 200:
                                    methods_data = methods_response.json()
                                    results["class_to_methods"] += len(
                                        methods_data.get("data", [])
                                    )

                        # Test function parameters
                        for func in functions:
                            parameters = func.get("parameters", "")
                            if parameters and parameters.strip():
                                results["function_parameters_populated"] += 1

            # Test navigation endpoints
            navigation_tests = [
                f"/api/classes/1",  # Individual class details
                f"/api/functions?class_id=1",  # Methods for a class
                f"/api/functions?file_id=1",  # Functions for a file
            ]

            for endpoint in navigation_tests:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        results["navigation_links_working"] += 1
                except:
                    pass

            print(f"✅ File-to-classes links: {results['file_to_classes']}")
            print(f"✅ File-to-functions links: {results['file_to_functions']}")
            print(f"✅ Class-to-methods links: {results['class_to_methods']}")
            print(
                f"✅ Function parameters populated: {results['function_parameters_populated']}"
            )
            print(
                f"✅ Navigation endpoints working: {results['navigation_links_working']}/3"
            )

        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Data linking test failed: {e}")

        return results

    def test_frontend_functionality(self) -> Dict:
        """Test frontend functionality and user interactions."""
        print("\n🖥️ Testing Frontend Functionality")
        print("-" * 40)

        results = {
            "dashboard_accessible": False,
            "sections_loading": 0,
            "search_functional": False,
            "modals_working": False,
            "navigation_working": False,
        }

        try:
            print("   🔄 Testing dashboard accessibility...")
            # Test dashboard accessibility
            response = requests.get(self.base_url, timeout=10)
            results["dashboard_accessible"] = response.status_code == 200

            print("   🔄 Testing section data loading...")
            # Test section data loading (simulate what JavaScript would do)
            sections = ["files", "classes", "functions", "services"]
            for section in sections:
                print(f"      🔄 Testing {section} section...")
                try:
                    section_response = requests.get(
                        f"{self.base_url}/api/{section}?limit=1", timeout=10
                    )
                    if section_response.status_code == 200:
                        results["sections_loading"] += 1
                except:
                    pass

            # Test search functionality
            search_response = requests.get(
                f"{self.base_url}/api/search?q=test", timeout=10
            )
            if search_response.status_code == 200:
                search_data = search_response.json()
                results["search_functional"] = search_data.get("total", 0) > 0

            # Test modal data endpoints - get a valid file ID first
            modal_working = 0
            try:
                files_response = requests.get(
                    f"{self.base_url}/api/files?limit=1", timeout=10
                )
                if files_response.status_code == 200:
                    files_data = files_response.json()
                    if files_data.get("data"):
                        valid_file_id = files_data["data"][0]["id"]
                        modal_response = requests.get(
                            f"{self.base_url}/api/file/{valid_file_id}/detailed",
                            timeout=10,
                        )
                        if modal_response.status_code == 200:
                            modal_working += 1
            except:
                pass
            results["modals_working"] = modal_working > 0

            # Test navigation endpoints
            nav_endpoints = ["/api/classes?file_id=1", "/api/functions?class_id=1"]
            nav_working = 0
            for endpoint in nav_endpoints:
                try:
                    nav_response = requests.get(
                        f"{self.base_url}{endpoint}", timeout=10
                    )
                    if nav_response.status_code == 200:
                        nav_working += 1
                except:
                    pass
            results["navigation_working"] = nav_working > 0

            print(f"✅ Dashboard accessible: {results['dashboard_accessible']}")
            print(f"✅ Sections loading: {results['sections_loading']}/4")
            print(f"✅ Search functional: {results['search_functional']}")
            print(f"✅ Modals working: {results['modals_working']}")
            print(f"✅ Navigation working: {results['navigation_working']}")

        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Frontend functionality test failed: {e}")

        return results

    def generate_final_report(self) -> Dict:
        """Generate final comprehensive report."""
        print("\n📋 FINAL DASHBOARD REPORT")
        print("=" * 60)

        # Calculate overall scores
        db_results = self.test_results.get("database_quality", {})
        api_results = self.test_results.get("api_completeness", {})
        linking_results = self.test_results.get("data_linking", {})
        frontend_results = self.test_results.get("frontend_functionality", {})

        # Database score
        db_score = db_results.get("quality_score", 0)

        # API score
        api_working = sum(
            1
            for r in api_results.values()
            if isinstance(r, dict) and r.get("status") == "ok"
        )
        api_total = len(api_results)
        api_score = (api_working / max(api_total, 1)) * 100

        # Data linking score
        params_populated = linking_results.get("function_parameters_populated", 0)
        total_functions = linking_results.get("file_to_functions", 1)
        linking_score = (params_populated / max(total_functions, 1)) * 100

        # Frontend score
        frontend_score = (
            (frontend_results.get("dashboard_accessible", False) * 25)
            + (frontend_results.get("sections_loading", 0) / 4 * 25)
            + (frontend_results.get("search_functional", False) * 25)
            + (frontend_results.get("modals_working", False) * 25)
        )

        # Overall score
        overall_score = (db_score + api_score + linking_score + frontend_score) / 4

        report = {
            "database_quality": {
                "score": db_score,
                "files": db_results.get("total_files", 0),
                "classes": db_results.get("total_classes", 0),
                "functions": db_results.get("total_functions", 0),
                "functions_with_parameters": db_results.get(
                    "functions_with_parameters", 0
                ),
            },
            "api_completeness": {
                "score": api_score,
                "working_endpoints": api_working,
                "total_endpoints": api_total,
            },
            "data_linking": {
                "score": linking_score,
                "parameters_populated": params_populated,
                "total_functions_tested": total_functions,
            },
            "frontend_functionality": {
                "score": frontend_score,
                "dashboard_accessible": frontend_results.get(
                    "dashboard_accessible", False
                ),
                "sections_working": frontend_results.get("sections_loading", 0),
            },
            "overall_score": overall_score,
            "grade": self.get_grade(overall_score),
            "recommendations": self.get_recommendations(
                overall_score,
                db_results,
                api_results,
                linking_results,
                frontend_results,
            ),
        }

        # Print report
        print(f"📊 Database Quality: {db_score:.1f}/100")
        print(f"🌐 API Completeness: {api_score:.1f}/100")
        print(f"🔗 Data Linking: {linking_score:.1f}/100")
        print(f"🖥️ Frontend Functionality: {frontend_score:.1f}/100")
        print(f"\n🎯 OVERALL SCORE: {overall_score:.1f}/100 ({report['grade']})")

        if report["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                print(f"   • {rec}")

        return report

    def get_grade(self, score: float) -> str:
        """Get letter grade based on score."""
        if score >= 90:
            return "A (Excellent)"
        elif score >= 80:
            return "B (Good)"
        elif score >= 70:
            return "C (Satisfactory)"
        elif score >= 60:
            return "D (Needs Improvement)"
        else:
            return "F (Poor)"

    def get_recommendations(
        self, overall_score, db_results, api_results, linking_results, frontend_results
    ) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        if db_results.get("quality_score", 0) < 80:
            if (
                db_results.get("functions_with_parameters", 0)
                < db_results.get("total_functions", 1) * 0.5
            ):
                recommendations.append(
                    "Improve function parameter population - many functions missing parameter data"
                )
            if db_results.get("excluded_files_found", 0) > 0:
                recommendations.append(
                    "Remove excluded files from database (.venv, __pycache__, .git directories)"
                )

        api_working = sum(
            1
            for r in api_results.values()
            if isinstance(r, dict) and r.get("status") == "ok"
        )
        if api_working < len(api_results):
            recommendations.append(
                "Fix broken API endpoints for complete functionality"
            )

        if linking_results.get("function_parameters_populated", 0) == 0:
            recommendations.append(
                "Critical: Function parameters are not being returned by API - check database schema and API response"
            )

        if not frontend_results.get("search_functional", False):
            recommendations.append(
                "Fix search functionality - users cannot find code components"
            )

        if overall_score < 70:
            recommendations.append(
                "Dashboard needs significant improvements before production use"
            )
        elif overall_score < 90:
            recommendations.append(
                "Dashboard is functional but could benefit from polish and optimization"
            )

        return recommendations

    def run_final_validation(self) -> Dict:
        """Run complete final validation."""
        print("🎯 FINAL COMPREHENSIVE DASHBOARD VALIDATION")
        print("=" * 60)

        start_time = time.time()

        # Check server availability
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                print("❌ Dashboard server is not running!")
                return {"error": "Server not available"}
        except requests.exceptions.RequestException:
            print("❌ Dashboard server is not running!")
            return {"error": "Server not available"}

        # Run all tests
        self.test_results = {
            "database_quality": self.test_database_quality(),
            "api_completeness": self.test_api_completeness(),
            "data_linking": self.test_data_linking_navigation(),
            "frontend_functionality": self.test_frontend_functionality(),
        }

        # Generate final report
        final_report = self.generate_final_report()

        # Add timing
        end_time = time.time()
        final_report["test_duration"] = end_time - start_time
        final_report["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

        print(
            f"\n⏱️  Validation completed in {final_report['test_duration']:.2f} seconds"
        )
        print(f"🎯 Dashboard URL: {self.base_url}")

        return final_report


def cleanup_old_test_files():
    """Remove old test files and consolidate into this single test."""
    print("🧹 Cleaning up old test files...")

    old_files = [
        "test_sections.py",
        "test_search.py",
        "schema_analysis.py",
        "final_verification.py",
        "final_completion_test.py",
        "comprehensive_dashboard_test.py",
        "comprehensive_analysis.py",
        "complete_verification.py",
        "analyze_dashboard_content.py",
        "update_class_types.py",
        "check_db.py",
    ]

    removed_count = 0
    for filename in old_files:
        file_path = Path(__file__).parent / filename
        if file_path.exists():
            try:
                file_path.unlink()
                removed_count += 1
                print(f"   ✅ Removed {filename}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {filename}: {e}")

    print(f"🧹 Cleaned up {removed_count} old test files")
    return removed_count


def main():
    """Run final comprehensive dashboard validation."""
    # Cleanup old files first
    cleanup_old_test_files()

    # Run validation
    validator = FinalDashboardValidator()
    results = validator.run_final_validation()

    # Save results
    results_file = Path(__file__).parent / "final_dashboard_report.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Final report saved to: {results_file}")

    # Print final status
    if results.get("overall_score", 0) >= 80:
        print(f"\n🎉 DASHBOARD READY FOR PRODUCTION!")
    elif results.get("overall_score", 0) >= 70:
        print(f"\n✅ DASHBOARD FUNCTIONAL - Minor improvements recommended")
    else:
        print(f"\n⚠️  DASHBOARD NEEDS IMPROVEMENTS - See recommendations above")


if __name__ == "__main__":
    main()
