#!/usr/bin/env python3
"""
Final USWDS Implementation Check
Verifies all changes are in place and provides specific guidance.
"""

import sys
from pathlib import Path


def check_file_content(file_path, expected_content, description):
    """Check if a file contains expected content."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        found_items = []
        missing_items = []

        for item in expected_content:
            if item in content:
                found_items.append(item)
            else:
                missing_items.append(item)

        print(f"\n📁 {description}")
        print(f"   File: {file_path}")

        for item in found_items:
            print(f"   ✅ Found: {item}")

        for item in missing_items:
            print(f"   ❌ Missing: {item}")

        return len(missing_items) == 0

    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return False


def main():
    """Run comprehensive USWDS implementation check."""
    print("🔍 USWDS Implementation Final Check")
    print("=" * 50)

    dashboard_path = Path(__file__).parent / "code-intelligence-dashboard"

    all_good = True

    # Check app.py for USWDS CSS
    app_checks = [
        "raw_css=",
        "--usa-color-primary",
        ".usa-header",
        ".usa-card",
        "Source Sans Pro",
        "Merriweather",
    ]

    app_good = check_file_content(
        dashboard_path / "dashboard" / "app.py",
        app_checks,
        "App.py USWDS Configuration",
    )
    all_good = all_good and app_good

    # Check header template
    header_checks = ["usa-header", "usa-nav", 'role="banner"', 'role="navigation"']

    header_good = check_file_content(
        dashboard_path / "dashboard" / "templates" / "header.html",
        header_checks,
        "Header Template USWDS Classes",
    )
    all_good = all_good and header_good

    # Check footer template
    footer_checks = ["usa-footer", "usa-summary-box", 'role="contentinfo"']

    footer_good = check_file_content(
        dashboard_path / "dashboard" / "templates" / "footer.html",
        footer_checks,
        "Footer Template USWDS Classes",
    )
    all_good = all_good and footer_good

    # Check views.py for USWDS usage
    views_checks = [
        "usa-alert",
        "usa-card",
        "dashboard-file-tip",
        "usa-input",
        "usa-button",
    ]

    views_good = check_file_content(
        dashboard_path / "dashboard" / "views.py",
        views_checks,
        "Views.py USWDS Integration",
    )
    all_good = all_good and views_good

    # Check stats card template
    stats_checks = ["dashboard-stat-card", "dashboard-stat-value", 'role="region"']

    stats_good = check_file_content(
        dashboard_path / "dashboard" / "templates" / "components" / "stats_card.html",
        stats_checks,
        "Stats Card Template USWDS Classes",
    )
    all_good = all_good and stats_good

    print("\n" + "=" * 50)
    print("📊 IMPLEMENTATION SUMMARY")
    print("=" * 50)

    if all_good:
        print("✅ ALL USWDS COMPONENTS PROPERLY IMPLEMENTED!")
        print("\n🎯 What you should see when you restart the dashboard:")
        print("   • Blue government header (#005ea2)")
        print("   • Navigation menu with 5 tabs")
        print("   • Professional card layouts with shadows")
        print("   • Source Sans Pro and Merriweather fonts")
        print("   • Colored borders on statistics cards")
        print("   • Dark government footer")
        print("   • Professional alert boxes")

        print("\n🚀 NEXT STEPS:")
        print("   1. Stop your current Panel server (Ctrl+C)")
        print("   2. Hard refresh your browser (Ctrl+Shift+R)")
        print("   3. Restart server: panel serve dashboard/app.py --show --autoreload")
        print("   4. If still not working, try incognito mode")

    else:
        print("⚠️  Some USWDS components are missing or incomplete.")
        print(
            "   Check the missing items above and ensure all files are properly updated."
        )

    print("\n📋 TROUBLESHOOTING CHECKLIST:")
    print("   □ Hard refresh browser (Ctrl+Shift+R)")
    print("   □ Check browser console for errors (F12)")
    print("   □ Try incognito/private mode")
    print("   □ Restart Panel server completely")
    print("   □ Check that all files were saved properly")

    return all_good


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 USWDS implementation is complete and ready!")
    else:
        print("\n🔧 Please address the missing components above.")

    sys.exit(0 if success else 1)
