#!/usr/bin/env python3
"""
Frontend Layout Validation Script
Validates the actual served page layout and functionality via HTTP requests
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup


class FrontendValidator:
    """Validates frontend layout and functionality."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.results = {}

    def validate_html_structure(self) -> Dict:
        """Validate HTML structure and required elements."""
        print("🔍 Validating HTML Structure")
        print("-" * 40)

        results = {
            "page_accessible": False,
            "required_sections": [],
            "missing_sections": [],
            "javascript_files": [],
            "css_files": [],
            "errors": [],
        }

        try:
            print("   🔄 Fetching dashboard HTML...")
            response = requests.get(self.base_url, timeout=10)

            if response.status_code != 200:
                results["errors"].append(
                    f"Dashboard not accessible: HTTP {response.status_code}"
                )
                return results

            results["page_accessible"] = True
            print("   ✅ Dashboard page accessible")

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Check for required sections (using actual IDs from dashboard.html)
            required_sections = [
                "files",
                "classes",
                "functions",
                "services",
                "search",
                "architecture",
            ]

            print("   🔄 Checking required sections...")
            for section_id in required_sections:
                element = soup.find(id=section_id)
                if element:
                    results["required_sections"].append(section_id)
                    print(f"      ✅ Found {section_id}")
                else:
                    results["missing_sections"].append(section_id)
                    print(f"      ❌ Missing {section_id}")

            # Check for JavaScript files
            print("   🔄 Checking JavaScript files...")
            script_tags = soup.find_all("script", src=True)
            for script in script_tags:
                src = script.get("src")
                if src:
                    results["javascript_files"].append(src)
                    print(f"      📄 Found JS: {src}")

            # Check for CSS files
            print("   🔄 Checking CSS files...")
            link_tags = soup.find_all("link", rel="stylesheet")
            for link in link_tags:
                href = link.get("href")
                if href:
                    results["css_files"].append(href)
                    print(f"      🎨 Found CSS: {href}")

        except Exception as e:
            results["errors"].append(f"HTML validation failed: {str(e)}")
            print(f"   ❌ HTML validation failed: {e}")

        return results

    def validate_javascript_loading(self, html_results: Dict = None) -> Dict:
        """Validate JavaScript files are accessible."""
        print("\n📜 Validating JavaScript Loading")
        print("-" * 40)

        results = {"accessible_js": [], "inaccessible_js": [], "total_js_files": 0}

        # Get JS files from HTML validation
        if html_results is None:
            html_results = self.results.get("html_structure", {})
        js_files = html_results.get("javascript_files", [])

        results["total_js_files"] = len(js_files)

        for js_file in js_files:
            print(f"   🔄 Testing {js_file}...")
            try:
                # Handle relative URLs
                if js_file.startswith("/"):
                    url = f"{self.base_url}{js_file}"
                else:
                    url = js_file

                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    results["accessible_js"].append(js_file)
                    print(f"      ✅ Accessible")
                else:
                    results["inaccessible_js"].append(js_file)
                    print(f"      ❌ HTTP {response.status_code}")

            except Exception as e:
                results["inaccessible_js"].append(js_file)
                print(f"      ❌ Error: {e}")

        return results

    def validate_api_integration(self) -> Dict:
        """Validate API endpoints are working for frontend."""
        print("\n🌐 Validating API Integration")
        print("-" * 40)

        results = {
            "working_endpoints": [],
            "broken_endpoints": [],
            "response_times": {},
        }

        # Key endpoints used by frontend
        endpoints = [
            "/api/stats",
            "/api/files?limit=10",
            "/api/classes?limit=10",
            "/api/functions?limit=10",
            "/api/services?limit=10",
            "/api/search?q=test&limit=5",
        ]

        for endpoint in endpoints:
            print(f"   🔄 Testing {endpoint}...")
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                duration = (time.time() - start_time) * 1000

                results["response_times"][endpoint] = duration

                if response.status_code == 200:
                    results["working_endpoints"].append(endpoint)
                    print(f"      ✅ OK ({duration:.1f}ms)")
                else:
                    results["broken_endpoints"].append(endpoint)
                    print(f"      ❌ HTTP {response.status_code}")

            except Exception as e:
                results["broken_endpoints"].append(endpoint)
                print(f"      ❌ Error: {e}")

        return results

    def validate_responsive_design(self) -> Dict:
        """Validate responsive design elements."""
        print("\n📱 Validating Responsive Design")
        print("-" * 40)

        results = {
            "viewport_meta": False,
            "responsive_css": False,
            "mobile_friendly": False,
        }

        try:
            print("   🔄 Checking viewport meta tag...")
            response = requests.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            # Check for viewport meta tag
            viewport_meta = soup.find("meta", attrs={"name": "viewport"})
            if viewport_meta:
                results["viewport_meta"] = True
                print("      ✅ Viewport meta tag found")
            else:
                print("      ❌ Viewport meta tag missing")

            # Check for responsive CSS patterns
            print("   🔄 Checking for responsive CSS...")
            css_links = soup.find_all("link", rel="stylesheet")
            for link in css_links:
                href = link.get("href")
                if href:
                    try:
                        css_response = requests.get(f"{self.base_url}{href}", timeout=5)
                        if "@media" in css_response.text:
                            results["responsive_css"] = True
                            print("      ✅ Responsive CSS found")
                            break
                    except:
                        pass

            if not results["responsive_css"]:
                print("      ⚠️  No responsive CSS detected")

            # Basic mobile-friendly check
            results["mobile_friendly"] = (
                results["viewport_meta"] and results["responsive_css"]
            )

        except Exception as e:
            print(f"   ❌ Responsive design validation failed: {e}")

        return results

    def validate_accessibility(self) -> Dict:
        """Validate basic accessibility features."""
        print("\n♿ Validating Accessibility")
        print("-" * 40)

        results = {
            "alt_texts": 0,
            "aria_labels": 0,
            "heading_structure": [],
            "form_labels": 0,
            "accessibility_score": 0,
        }

        try:
            print("   🔄 Checking accessibility features...")
            response = requests.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            # Check for alt texts
            images = soup.find_all("img")
            for img in images:
                if img.get("alt"):
                    results["alt_texts"] += 1
            print(
                f"      📷 Images with alt text: {results['alt_texts']}/{len(images)}"
            )

            # Check for ARIA labels
            aria_elements = soup.find_all(attrs={"aria-label": True})
            results["aria_labels"] = len(aria_elements)
            print(f"      🏷️  Elements with ARIA labels: {results['aria_labels']}")

            # Check heading structure
            headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
            for heading in headings:
                results["heading_structure"].append(heading.name)
            print(f"      📝 Heading elements found: {len(headings)}")

            # Check form labels
            labels = soup.find_all("label")
            results["form_labels"] = len(labels)
            print(f"      📋 Form labels: {results['form_labels']}")

            # Calculate basic accessibility score
            total_checks = 4
            passed_checks = 0
            if results["alt_texts"] > 0:
                passed_checks += 1
            if results["aria_labels"] > 0:
                passed_checks += 1
            if len(results["heading_structure"]) > 0:
                passed_checks += 1
            if results["form_labels"] > 0:
                passed_checks += 1

            results["accessibility_score"] = (passed_checks / total_checks) * 100

        except Exception as e:
            print(f"   ❌ Accessibility validation failed: {e}")

        return results

    def generate_report(self) -> Dict:
        """Generate comprehensive frontend validation report."""
        print("\n📋 FRONTEND VALIDATION REPORT")
        print("=" * 50)

        # Calculate overall scores
        html_results = self.results.get("html_structure", {})
        js_results = self.results.get("javascript_loading", {})
        api_results = self.results.get("api_integration", {})
        responsive_results = self.results.get("responsive_design", {})
        accessibility_results = self.results.get("accessibility", {})

        # HTML Structure Score
        required_sections = len(html_results.get("required_sections", []))
        total_sections = required_sections + len(
            html_results.get("missing_sections", [])
        )
        html_score = (required_sections / max(total_sections, 1)) * 100

        # JavaScript Loading Score
        accessible_js = len(js_results.get("accessible_js", []))
        total_js = js_results.get("total_js_files", 1)
        js_score = (accessible_js / max(total_js, 1)) * 100

        # API Integration Score
        working_endpoints = len(api_results.get("working_endpoints", []))
        total_endpoints = working_endpoints + len(
            api_results.get("broken_endpoints", [])
        )
        api_score = (working_endpoints / max(total_endpoints, 1)) * 100

        # Responsive Design Score
        responsive_score = 0
        if responsive_results.get("viewport_meta"):
            responsive_score += 50
        if responsive_results.get("responsive_css"):
            responsive_score += 50

        # Overall Score
        overall_score = (
            html_score
            + js_score
            + api_score
            + responsive_score
            + accessibility_results.get("accessibility_score", 0)
        ) / 5

        report = {
            "html_structure": {
                "score": html_score,
                "sections_found": required_sections,
                "total_sections": total_sections,
                "missing_sections": html_results.get("missing_sections", []),
            },
            "javascript_loading": {
                "score": js_score,
                "accessible_files": accessible_js,
                "total_files": total_js,
            },
            "api_integration": {
                "score": api_score,
                "working_endpoints": working_endpoints,
                "total_endpoints": total_endpoints,
                "avg_response_time": sum(api_results.get("response_times", {}).values())
                / max(len(api_results.get("response_times", {})), 1),
            },
            "responsive_design": {
                "score": responsive_score,
                "mobile_friendly": responsive_results.get("mobile_friendly", False),
            },
            "accessibility": {
                "score": accessibility_results.get("accessibility_score", 0),
                "aria_labels": accessibility_results.get("aria_labels", 0),
                "alt_texts": accessibility_results.get("alt_texts", 0),
            },
            "overall_score": overall_score,
            "grade": self.get_grade(overall_score),
            "recommendations": self.get_recommendations(
                overall_score, html_results, js_results, api_results
            ),
        }

        # Print summary
        print(f"🏗️  HTML Structure: {html_score:.1f}/100")
        print(f"📜 JavaScript Loading: {js_score:.1f}/100")
        print(f"🌐 API Integration: {api_score:.1f}/100")
        print(f"📱 Responsive Design: {responsive_score:.1f}/100")
        print(
            f"♿ Accessibility: {accessibility_results.get('accessibility_score', 0):.1f}/100"
        )
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
        self, overall_score, html_results, js_results, api_results
    ) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        if html_results.get("missing_sections"):
            recommendations.append(
                f"Fix missing HTML sections: {', '.join(html_results['missing_sections'])}"
            )

        if js_results.get("inaccessible_js"):
            recommendations.append("Fix broken JavaScript file loading")

        if api_results.get("broken_endpoints"):
            recommendations.append("Fix broken API endpoints for frontend integration")

        avg_response_time = sum(api_results.get("response_times", {}).values()) / max(
            len(api_results.get("response_times", {})), 1
        )
        if avg_response_time > 500:
            recommendations.append("Optimize API response times (currently > 500ms)")

        if overall_score < 70:
            recommendations.append(
                "Frontend needs significant improvements before production"
            )
        elif overall_score < 90:
            recommendations.append(
                "Frontend is functional but could benefit from optimization"
            )

        return recommendations

    def run_validation(self) -> Dict:
        """Run complete frontend validation."""
        print("🎯 FRONTEND LAYOUT VALIDATION")
        print("=" * 50)

        start_time = time.time()

        # Run all validations
        html_results = self.validate_html_structure()
        self.results = {
            "html_structure": html_results,
            "javascript_loading": self.validate_javascript_loading(html_results),
            "api_integration": self.validate_api_integration(),
            "responsive_design": self.validate_responsive_design(),
            "accessibility": self.validate_accessibility(),
        }

        # Generate final report
        final_report = self.generate_report()

        # Add timing
        end_time = time.time()
        final_report["validation_duration"] = end_time - start_time
        final_report["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

        print(
            f"\n⏱️  Validation completed in {final_report['validation_duration']:.2f} seconds"
        )

        return final_report


def main():
    """Run frontend validation."""
    validator = FrontendValidator()
    results = validator.run_validation()

    # Save results
    results_file = Path(__file__).parent / "frontend_validation_report.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Frontend validation report saved to: {results_file}")

    # Print final status
    if results.get("overall_score", 0) >= 80:
        print(f"\n🎉 FRONTEND READY FOR PRODUCTION!")
    elif results.get("overall_score", 0) >= 70:
        print(f"\n✅ FRONTEND FUNCTIONAL - Minor improvements recommended")
    else:
        print(f"\n⚠️  FRONTEND NEEDS IMPROVEMENTS - See recommendations above")


if __name__ == "__main__":
    main()
