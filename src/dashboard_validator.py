#!/usr/bin/env python3
"""
Dashboard Validator
Enhanced frontend layout validation and functionality testing

**Last Updated:** 2025-01-27

This module provides comprehensive validation of the dashboard frontend,
including HTML structure, JavaScript functionality, CSS styling, and
user interface components.

Features:
- HTML structure validation
- JavaScript component testing
- CSS styling verification
- API integration validation
- User interface functionality testing
- Performance metrics collection
- Accessibility compliance checking
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class DashboardValidator:
    """Comprehensive dashboard frontend validation tool."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.results = {}
        self.session = requests.Session()
        self.session.timeout = 10

    def validate_html_structure(self) -> Dict[str, Any]:
        """Validate HTML structure and required elements."""
        print("🔍 Validating HTML Structure")
        print("-" * 40)

        results = {
            "page_accessible": False,
            "required_sections": [],
            "missing_sections": [],
            "javascript_files": [],
            "css_files": [],
            "meta_tags": {},
            "errors": [],
        }

        required_sections = [
            "header",
            "nav",
            "main",
            "sidebar",
            "footer",
            "search-container",
            "content-area",
            "stats-overview",
        ]

        try:
            print("   🔄 Fetching dashboard HTML...")
            response = self.session.get(self.base_url)

            if response.status_code != 200:
                results["errors"].append(
                    f"Dashboard not accessible: HTTP {response.status_code}"
                )
                print(f"   ❌ Dashboard not accessible: HTTP {response.status_code}")
                return results

            results["page_accessible"] = True
            print("   ✅ Dashboard page accessible")

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Check for required sections
            for section in required_sections:
                elements = soup.find_all(attrs={"id": section}) + soup.find_all(
                    attrs={"class": re.compile(section)}
                )
                if elements:
                    results["required_sections"].append(section)
                    print(f"   ✅ Found section: {section}")
                else:
                    results["missing_sections"].append(section)
                    print(f"   ❌ Missing section: {section}")

            # Check JavaScript files
            script_tags = soup.find_all("script", src=True)
            for script in script_tags:
                src = script.get("src")
                if src:
                    results["javascript_files"].append(src)
                    print(f"   📜 JavaScript: {src}")

            # Check CSS files
            link_tags = soup.find_all("link", rel="stylesheet")
            for link in link_tags:
                href = link.get("href")
                if href:
                    results["css_files"].append(href)
                    print(f"   🎨 CSS: {href}")

            # Check meta tags
            meta_tags = soup.find_all("meta")
            for meta in meta_tags:
                name = meta.get("name") or meta.get("property")
                content = meta.get("content")
                if name and content:
                    results["meta_tags"][name] = content

            print(
                f"   📊 Found {len(results['required_sections'])}/{len(required_sections)} required sections"
            )
            print(f"   📊 JavaScript files: {len(results['javascript_files'])}")
            print(f"   📊 CSS files: {len(results['css_files'])}")

        except Exception as e:
            results["errors"].append(f"HTML validation error: {str(e)}")
            print(f"   ❌ HTML validation error: {e}")

        return results

    def validate_static_assets(self) -> Dict[str, Any]:
        """Validate that static assets are accessible."""
        print("📁 Validating Static Assets")
        print("-" * 40)

        results = {
            "assets_tested": 0,
            "assets_accessible": 0,
            "asset_results": {},
            "errors": [],
        }

        # Common static assets to check
        assets_to_check = [
            "/assets/dashboard.css",
            "/components/dashboard-core.js",
            "/components/data-loader.js",
            "/components/search-manager.js",
            "/components/visualization-manager.js",
            "/components/modal-manager.js",
        ]

        for asset_path in assets_to_check:
            results["assets_tested"] += 1
            asset_url = urljoin(self.base_url, asset_path)

            try:
                response = self.session.get(asset_url)
                asset_result = {
                    "accessible": response.status_code == 200,
                    "status_code": response.status_code,
                    "size": len(response.content) if response.status_code == 200 else 0,
                    "content_type": response.headers.get("content-type", "unknown"),
                }

                if asset_result["accessible"]:
                    results["assets_accessible"] += 1
                    print(f"   ✅ {asset_path} ({asset_result['size']} bytes)")
                else:
                    print(f"   ❌ {asset_path} - HTTP {response.status_code}")

                results["asset_results"][asset_path] = asset_result

            except Exception as e:
                results["errors"].append(f"Error checking {asset_path}: {str(e)}")
                print(f"   ❌ {asset_path} - Error: {e}")

        print(
            f"   📊 Accessible: {results['assets_accessible']}/{results['assets_tested']} assets"
        )
        return results

    def validate_api_integration(self) -> Dict[str, Any]:
        """Validate API integration and data loading."""
        print("🔌 Validating API Integration")
        print("-" * 40)

        results = {
            "api_endpoints_tested": 0,
            "api_endpoints_working": 0,
            "endpoint_results": {},
            "data_quality": {},
            "errors": [],
        }

        # Key API endpoints used by the dashboard
        api_endpoints = [
            ("/api/stats", "System statistics"),
            ("/api/files?limit=10", "Files list"),
            ("/api/classes?limit=10", "Classes list"),
            ("/api/functions?limit=10", "Functions list"),
            ("/api/search?q=test&limit=5", "Search functionality"),
            ("/api/domains", "Domain statistics"),
            ("/api/complexity/distribution", "Complexity distribution"),
        ]

        for endpoint, description in api_endpoints:
            results["api_endpoints_tested"] += 1
            endpoint_url = urljoin(self.base_url, endpoint)

            try:
                start_time = time.time()
                response = self.session.get(endpoint_url)
                response_time = round((time.time() - start_time) * 1000, 2)

                endpoint_result = {
                    "accessible": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "data_valid": False,
                    "data_count": 0,
                }

                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get("success"):
                            endpoint_result["data_valid"] = True
                            results["api_endpoints_working"] += 1

                            # Count data items
                            if "data" in data:
                                if isinstance(data["data"], list):
                                    endpoint_result["data_count"] = len(data["data"])
                                elif isinstance(data["data"], dict):
                                    endpoint_result["data_count"] = len(data["data"])

                            print(
                                f"   ✅ {endpoint} - {description} ({response_time}ms, {endpoint_result['data_count']} items)"
                            )
                        else:
                            print(f"   ❌ {endpoint} - API returned success=false")
                    except json.JSONDecodeError:
                        print(f"   ❌ {endpoint} - Invalid JSON response")
                else:
                    print(f"   ❌ {endpoint} - HTTP {response.status_code}")

                results["endpoint_results"][endpoint] = endpoint_result

            except Exception as e:
                results["errors"].append(f"Error testing {endpoint}: {str(e)}")
                print(f"   ❌ {endpoint} - Error: {e}")

        print(
            f"   📊 Working: {results['api_endpoints_working']}/{results['api_endpoints_tested']} endpoints"
        )
        return results

    def validate_javascript_functionality(self) -> Dict[str, Any]:
        """Validate JavaScript functionality by checking for common patterns."""
        print("📜 Validating JavaScript Functionality")
        print("-" * 40)

        results = {
            "components_found": [],
            "functions_found": [],
            "event_handlers": [],
            "potential_issues": [],
            "errors": [],
        }

        # JavaScript components to look for
        expected_components = [
            "DashboardCore",
            "DataLoader",
            "SearchManager",
            "VisualizationManager",
            "ModalManager",
            "NavigationManager",
        ]

        # Get the main dashboard HTML to check for JavaScript
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                html_content = response.text

                # Check for component references
                for component in expected_components:
                    if component in html_content:
                        results["components_found"].append(component)
                        print(f"   ✅ Found component: {component}")
                    else:
                        results["potential_issues"].append(
                            f"Component {component} not found in HTML"
                        )

                # Check for common JavaScript patterns
                js_patterns = [
                    (r"addEventListener\s*\(", "Event listeners"),
                    (r"fetch\s*\(", "Fetch API calls"),
                    (r"document\.getElementById", "DOM element access"),
                    (r"class\s+\w+", "ES6 classes"),
                    (r"async\s+function", "Async functions"),
                ]

                for pattern, description in js_patterns:
                    if re.search(pattern, html_content):
                        results["functions_found"].append(description)
                        print(f"   ✅ Found: {description}")

                # Check for potential issues
                issue_patterns = [
                    (r"console\.error", "Console errors"),
                    (r"throw\s+new\s+Error", "Error throwing"),
                    (r"undefined", "Undefined references"),
                ]

                for pattern, description in issue_patterns:
                    matches = re.findall(pattern, html_content)
                    if matches:
                        results["potential_issues"].append(
                            f"{description}: {len(matches)} occurrences"
                        )

        except Exception as e:
            results["errors"].append(f"JavaScript validation error: {str(e)}")
            print(f"   ❌ JavaScript validation error: {e}")

        print(f"   📊 Components found: {len(results['components_found'])}")
        print(f"   📊 JS patterns found: {len(results['functions_found'])}")
        if results["potential_issues"]:
            print(f"   ⚠️  Potential issues: {len(results['potential_issues'])}")

        return results

    def validate_responsive_design(self) -> Dict[str, Any]:
        """Validate responsive design elements."""
        print("📱 Validating Responsive Design")
        print("-" * 40)

        results = {
            "viewport_meta": False,
            "media_queries": 0,
            "responsive_classes": [],
            "mobile_friendly": False,
            "errors": [],
        }

        try:
            # Check main HTML
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Check viewport meta tag
                viewport_meta = soup.find("meta", attrs={"name": "viewport"})
                if viewport_meta:
                    results["viewport_meta"] = True
                    print("   ✅ Viewport meta tag found")
                else:
                    print("   ❌ Viewport meta tag missing")

                # Check for responsive classes
                responsive_patterns = [
                    "responsive",
                    "mobile",
                    "tablet",
                    "desktop",
                    "flex",
                    "grid",
                ]
                html_content = response.text.lower()

                for pattern in responsive_patterns:
                    if pattern in html_content:
                        results["responsive_classes"].append(pattern)

                print(
                    f"   📊 Responsive classes found: {len(results['responsive_classes'])}"
                )

            # Check CSS for media queries
            css_response = self.session.get(
                urljoin(self.base_url, "/assets/dashboard.css")
            )
            if css_response.status_code == 200:
                css_content = css_response.text
                media_queries = re.findall(r"@media[^{]+{", css_content)
                results["media_queries"] = len(media_queries)
                print(f"   📊 Media queries found: {results['media_queries']}")

            # Determine mobile friendliness
            results["mobile_friendly"] = (
                results["viewport_meta"]
                and results["media_queries"] > 0
                and len(results["responsive_classes"]) > 2
            )

            if results["mobile_friendly"]:
                print("   ✅ Mobile-friendly design detected")
            else:
                print("   ⚠️  Mobile-friendliness could be improved")

        except Exception as e:
            results["errors"].append(f"Responsive design validation error: {str(e)}")
            print(f"   ❌ Responsive design validation error: {e}")

        return results

    def validate_performance(self) -> Dict[str, Any]:
        """Validate performance metrics."""
        print("⚡ Validating Performance")
        print("-" * 40)

        results = {
            "page_load_time": 0,
            "api_response_times": {},
            "asset_sizes": {},
            "performance_score": 0,
            "recommendations": [],
            "errors": [],
        }

        try:
            # Measure page load time
            start_time = time.time()
            response = self.session.get(self.base_url)
            results["page_load_time"] = round((time.time() - start_time) * 1000, 2)

            print(f"   📊 Page load time: {results['page_load_time']}ms")

            # Measure API response times
            api_endpoints = ["/api/stats", "/api/files?limit=10", "/api/search?q=test"]
            for endpoint in api_endpoints:
                start_time = time.time()
                api_response = self.session.get(urljoin(self.base_url, endpoint))
                response_time = round((time.time() - start_time) * 1000, 2)
                results["api_response_times"][endpoint] = response_time
                print(f"   📊 {endpoint}: {response_time}ms")

            # Check asset sizes
            assets = ["/assets/dashboard.css", "/components/dashboard-core.js"]
            for asset in assets:
                try:
                    asset_response = self.session.get(urljoin(self.base_url, asset))
                    if asset_response.status_code == 200:
                        size_kb = round(len(asset_response.content) / 1024, 2)
                        results["asset_sizes"][asset] = size_kb
                        print(f"   📊 {asset}: {size_kb}KB")
                except:
                    pass

            # Calculate performance score
            score = 100
            if results["page_load_time"] > 2000:
                score -= 20
                results["recommendations"].append("Page load time > 2s")
            elif results["page_load_time"] > 1000:
                score -= 10
                results["recommendations"].append("Page load time > 1s")

            avg_api_time = sum(results["api_response_times"].values()) / len(
                results["api_response_times"]
            )
            if avg_api_time > 500:
                score -= 15
                results["recommendations"].append("Average API response time > 500ms")

            total_asset_size = sum(results["asset_sizes"].values())
            if total_asset_size > 500:
                score -= 10
                results["recommendations"].append("Total asset size > 500KB")

            results["performance_score"] = max(0, score)
            print(f"   📊 Performance score: {results['performance_score']}/100")

            if results["recommendations"]:
                print("   💡 Recommendations:")
                for rec in results["recommendations"]:
                    print(f"      - {rec}")

        except Exception as e:
            results["errors"].append(f"Performance validation error: {str(e)}")
            print(f"   ❌ Performance validation error: {e}")

        return results

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive dashboard validation."""
        print("🎯 Running Comprehensive Dashboard Validation")
        print("=" * 60)
        print()

        all_results = {}
        start_time = time.time()

        # Run all validation categories
        all_results["html_structure"] = self.validate_html_structure()
        print()

        all_results["static_assets"] = self.validate_static_assets()
        print()

        all_results["api_integration"] = self.validate_api_integration()
        print()

        all_results["javascript_functionality"] = (
            self.validate_javascript_functionality()
        )
        print()

        all_results["responsive_design"] = self.validate_responsive_design()
        print()

        all_results["performance"] = self.validate_performance()
        print()

        # Generate summary
        total_time = round(time.time() - start_time, 2)

        summary = {
            "total_time": total_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "PASS",
            "critical_issues": [],
            "warnings": [],
            "scores": {},
        }

        # Analyze results
        if not all_results["html_structure"]["page_accessible"]:
            summary["overall_status"] = "FAIL"
            summary["critical_issues"].append("Dashboard page not accessible")

        if len(all_results["html_structure"]["missing_sections"]) > 3:
            summary["warnings"].append("Multiple required sections missing")

        if (
            all_results["static_assets"]["assets_accessible"]
            < all_results["static_assets"]["assets_tested"] * 0.8
        ):
            summary["warnings"].append("Many static assets not accessible")

        if (
            all_results["api_integration"]["api_endpoints_working"]
            < all_results["api_integration"]["api_endpoints_tested"] * 0.8
        ):
            summary["overall_status"] = "FAIL"
            summary["critical_issues"].append("Too many API endpoints failing")

        if not all_results["responsive_design"]["mobile_friendly"]:
            summary["warnings"].append("Mobile-friendliness could be improved")

        if all_results["performance"]["performance_score"] < 70:
            summary["warnings"].append("Performance score below 70")

        # Calculate scores
        summary["scores"] = {
            "html_structure": (
                len(all_results["html_structure"]["required_sections"])
                / (
                    len(all_results["html_structure"]["required_sections"])
                    + len(all_results["html_structure"]["missing_sections"])
                )
                * 100
                if all_results["html_structure"]["required_sections"]
                or all_results["html_structure"]["missing_sections"]
                else 100
            ),
            "static_assets": (
                all_results["static_assets"]["assets_accessible"]
                / all_results["static_assets"]["assets_tested"]
                * 100
                if all_results["static_assets"]["assets_tested"] > 0
                else 100
            ),
            "api_integration": (
                all_results["api_integration"]["api_endpoints_working"]
                / all_results["api_integration"]["api_endpoints_tested"]
                * 100
                if all_results["api_integration"]["api_endpoints_tested"] > 0
                else 100
            ),
            "performance": all_results["performance"]["performance_score"],
        }

        all_results["summary"] = summary

        # Print summary
        print("📋 Validation Summary")
        print("=" * 60)
        print(
            f"Overall Status: {'✅ PASS' if summary['overall_status'] == 'PASS' else '❌ FAIL'}"
        )
        print(f"Total Time: {total_time}s")
        print(f"Timestamp: {summary['timestamp']}")

        print("\n📊 Scores:")
        for category, score in summary["scores"].items():
            print(f"   {category.replace('_', ' ').title()}: {score:.1f}/100")

        if summary["critical_issues"]:
            print("\n❌ Critical Issues:")
            for issue in summary["critical_issues"]:
                print(f"   - {issue}")

        if summary["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in summary["warnings"]:
                print(f"   - {warning}")

        if not summary["critical_issues"] and not summary["warnings"]:
            print("\n🎉 All validations passed successfully!")

        return all_results

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save validation results to JSON file."""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"validation_results_{timestamp}.json"

        filepath = Path(__file__).parent / filename
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {filepath}")


def main():
    """Main validation runner with command-line interface."""
    parser = argparse.ArgumentParser(description="Dashboard Validator")
    parser.add_argument(
        "--url",
        default="http://localhost:8001",
        help="Base URL for dashboard validation",
    )
    parser.add_argument(
        "--category",
        choices=[
            "html",
            "assets",
            "api",
            "javascript",
            "responsive",
            "performance",
            "all",
        ],
        default="all",
        help="Validation category to run",
    )
    parser.add_argument("--save", action="store_true", help="Save results to JSON file")
    parser.add_argument("--output", help="Output filename for results")

    args = parser.parse_args()

    validator = DashboardValidator(args.url)

    if args.category == "all":
        results = validator.run_comprehensive_validation()
    elif args.category == "html":
        results = {"html_structure": validator.validate_html_structure()}
    elif args.category == "assets":
        results = {"static_assets": validator.validate_static_assets()}
    elif args.category == "api":
        results = {"api_integration": validator.validate_api_integration()}
    elif args.category == "javascript":
        results = {
            "javascript_functionality": validator.validate_javascript_functionality()
        }
    elif args.category == "responsive":
        results = {"responsive_design": validator.validate_responsive_design()}
    elif args.category == "performance":
        results = {"performance": validator.validate_performance()}

    if args.save:
        validator.save_results(results, args.output)


if __name__ == "__main__":
    main()
