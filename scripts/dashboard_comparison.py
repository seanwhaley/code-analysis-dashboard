#!/usr/bin/env python3
"""
Dynamic Dashboard Comparison Tool
Analyzes actual dashboard files and provides real-time comparison of USWDS implementation.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def analyze_css_classes(file_path: Path) -> Dict[str, List[str]]:
    """Extract CSS classes from HTML/Python files."""
    if not file_path.exists():
        return {"error": [f"File not found: {file_path}"]}

    try:
        content = file_path.read_text(encoding="utf-8")

        # Find class attributes
        class_patterns = [
            r'class=["\']([^"\']+)["\']',  # HTML class attributes
            r"css_classes=\[([^\]]+)\]",  # Panel css_classes
            r'\.add_class\(["\']([^"\']+)["\']',  # JavaScript addClass
        ]

        classes = []
        for pattern in class_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str):
                    classes.extend(match.split())

        # Categorize classes
        uswds_classes = [c for c in classes if c.startswith("usa-")]
        dashboard_classes = [c for c in classes if c.startswith("dashboard-")]
        other_classes = [c for c in classes if not c.startswith(("usa-", "dashboard-"))]

        return {
            "uswds": uswds_classes,
            "dashboard": dashboard_classes,
            "other": other_classes,
            "total": len(classes),
        }
    except Exception as e:
        return {"error": [str(e)]}


def analyze_css_variables(file_path: Path) -> Dict[str, List[str]]:
    """Extract CSS variables from files."""
    if not file_path.exists():
        return {"error": [f"File not found: {file_path}"]}

    try:
        content = file_path.read_text(encoding="utf-8")

        # Find CSS variables
        var_pattern = r"--([a-zA-Z0-9-]+):\s*([^;]+);"
        matches = re.findall(var_pattern, content)

        uswds_vars = [
            (name, value) for name, value in matches if name.startswith("usa-")
        ]
        other_vars = [
            (name, value) for name, value in matches if not name.startswith("usa-")
        ]

        return {
            "uswds_variables": uswds_vars,
            "other_variables": other_vars,
            "total": len(matches),
        }
    except Exception as e:
        return {"error": [str(e)]}


def check_accessibility_features(file_path: Path) -> Dict[str, bool]:
    """Check for accessibility features in files."""
    if not file_path.exists():
        return {"error": True}

    try:
        content = file_path.read_text(encoding="utf-8")

        features = {
            "aria_roles": bool(re.search(r'role=["\'][^"\']+["\']', content)),
            "aria_labels": bool(re.search(r'aria-[a-z]+=["\'][^"\']+["\']', content)),
            "semantic_html": bool(
                re.search(r"<(header|nav|main|section|article|aside|footer)", content)
            ),
            "keyboard_navigation": bool(re.search(r"tabindex|keydown|keyup", content)),
            "screen_reader": bool(re.search(r"sr-only|screen-reader", content)),
        }

        return features
    except Exception as e:
        return {"error": True}


def analyze_dashboard_implementation():
    """Analyze the current dashboard implementation."""
    dashboard_path = Path(__file__).parent / "code-intelligence-dashboard"

    files_to_check = {
        "app.py": dashboard_path / "dashboard" / "app.py",
        "header.html": dashboard_path / "dashboard" / "templates" / "header.html",
        "footer.html": dashboard_path / "dashboard" / "templates" / "footer.html",
        "views.py": dashboard_path / "dashboard" / "views.py",
        "stats_card.html": dashboard_path
        / "dashboard"
        / "templates"
        / "components"
        / "stats_card.html",
    }

    print("🔍 DYNAMIC DASHBOARD ANALYSIS")
    print("=" * 60)

    total_uswds_classes = 0
    total_accessibility_features = 0

    for file_name, file_path in files_to_check.items():
        print(f"\n📁 {file_name}")
        print("-" * 40)

        # Analyze CSS classes
        class_analysis = analyze_css_classes(file_path)
        if "error" not in class_analysis:
            uswds_count = len(class_analysis["uswds"])
            total_uswds_classes += uswds_count

            print(
                f"   USWDS Classes ({uswds_count}): {', '.join(class_analysis['uswds'][:5])}"
            )
            if len(class_analysis["uswds"]) > 5:
                print(f"   ... and {len(class_analysis['uswds']) - 5} more")

            if class_analysis["dashboard"]:
                print(
                    f"   Custom Classes: {', '.join(class_analysis['dashboard'][:3])}"
                )
        else:
            print(f"   ❌ Error: {class_analysis['error'][0]}")

        # Check accessibility
        accessibility = check_accessibility_features(file_path)
        if "error" not in accessibility:
            accessible_features = sum(accessibility.values())
            total_accessibility_features += accessible_features

            print(f"   Accessibility Features: {accessible_features}/5")
            for feature, present in accessibility.items():
                status = "✅" if present else "❌"
                print(f"     {status} {feature.replace('_', ' ').title()}")

    # CSS Variables Analysis
    app_file = files_to_check["app.py"]
    css_analysis = analyze_css_variables(app_file)

    print(f"\n🎨 CSS VARIABLES ANALYSIS")
    print("-" * 40)
    if "error" not in css_analysis:
        print(f"   USWDS Variables: {len(css_analysis['uswds_variables'])}")
        for name, value in css_analysis["uswds_variables"][:3]:
            print(f"     --{name}: {value}")
        if len(css_analysis["uswds_variables"]) > 3:
            print(f"     ... and {len(css_analysis['uswds_variables']) - 3} more")

    # Summary
    print(f"\n📊 IMPLEMENTATION SUMMARY")
    print("=" * 60)
    print(f"   Total USWDS Classes Found: {total_uswds_classes}")
    print(f"   Total Accessibility Features: {total_accessibility_features}")

    # Determine implementation status
    if total_uswds_classes >= 15 and total_accessibility_features >= 10:
        print("   🎉 Status: FULLY IMPLEMENTED")
        print("   🎯 Expected Visual Changes:")
        print("     • Government blue header (#005ea2)")
        print("     • Professional typography (Source Sans Pro + Merriweather)")
        print("     • Card-based layouts with shadows")
        print("     • Accessible navigation and alerts")
        print("     • Government-standard color scheme")
    elif total_uswds_classes >= 5:
        print("   ⚠️  Status: PARTIALLY IMPLEMENTED")
        print("   🔧 Some USWDS components may be missing")
    else:
        print("   ❌ Status: NOT IMPLEMENTED")
        print("   🚨 USWDS classes not found - implementation may have failed")

    return total_uswds_classes, total_accessibility_features


def provide_troubleshooting():
    """Provide dynamic troubleshooting based on analysis."""
    print(f"\n🔧 TROUBLESHOOTING GUIDE")
    print("=" * 60)

    # Check if server is likely running
    dashboard_path = Path(__file__).parent / "code-intelligence-dashboard"
    app_file = dashboard_path / "dashboard" / "app.py"

    if app_file.exists():
        content = app_file.read_text(encoding="utf-8")
        has_raw_css = "raw_css=" in content
        has_uswds_vars = "--usa-color-primary" in content

        print("   📋 Implementation Status:")
        print(f"     {'✅' if has_raw_css else '❌'} Raw CSS embedded in app.py")
        print(f"     {'✅' if has_uswds_vars else '❌'} USWDS variables present")

        if has_raw_css and has_uswds_vars:
            print("\n   🚀 Implementation looks good! If not seeing changes:")
            print("     1. Hard refresh browser (Ctrl+Shift+R)")
            print("     2. Try incognito mode")
            print("     3. Check browser console (F12) for errors")
            print("     4. Restart Panel server completely")
        else:
            print("\n   ⚠️  Implementation issues detected:")
            if not has_raw_css:
                print("     • raw_css not found in app.py")
            if not has_uswds_vars:
                print("     • USWDS variables not found")
    else:
        print("   ❌ Dashboard app.py not found!")
        print("     • Check that you're in the correct directory")
        print("     • Verify the dashboard files exist")


def main():
    """Run dynamic dashboard comparison analysis."""
    try:
        uswds_classes, accessibility_features = analyze_dashboard_implementation()
        provide_troubleshooting()

        print(f"\n✅ ANALYSIS COMPLETE")
        print("=" * 60)
        print("This tool analyzed your actual dashboard files to determine")
        print("the current USWDS implementation status.")

        if uswds_classes >= 15:
            print(
                "\n🎉 Your dashboard should now have professional government styling!"
            )
        else:
            print("\n🔧 Some USWDS components may need attention.")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        print("Please ensure you're running this from the correct directory.")


if __name__ == "__main__":
    main()
