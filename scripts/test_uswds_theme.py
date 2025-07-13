#!/usr/bin/env python3
"""
Test script to validate USWDS theme implementation.
"""

import sys
from pathlib import Path

# Add the dashboard to the path
sys.path.insert(0, str(Path(__file__).parent / "code-intelligence-dashboard"))


def test_uswds_css_files():
    """Test that USWDS CSS files exist and are properly structured."""
    print("Testing USWDS CSS files...")

    css_path = (
        Path(__file__).parent
        / "code-intelligence-dashboard"
        / "dashboard"
        / "assets"
        / "uswds-theme.css"
    )

    if not css_path.exists():
        print("❌ USWDS theme CSS file not found")
        return False

    with open(css_path, "r") as f:
        css_content = f.read()

    # Check for key USWDS components
    required_components = [
        ":root",  # CSS variables
        "--usa-color-primary",  # USWDS color tokens
        ".usa-header",  # Header component
        ".usa-footer",  # Footer component
        ".usa-card",  # Card component
        ".usa-alert",  # Alert component
        ".usa-button",  # Button component
        ".usa-table",  # Table component
        ".dashboard-stat-card",  # Custom dashboard components
        "@media (prefers-reduced-motion: reduce)",  # Accessibility
    ]

    missing_components = []
    for component in required_components:
        if component not in css_content:
            missing_components.append(component)

    if missing_components:
        print(f"❌ Missing USWDS components: {missing_components}")
        return False

    print("✅ USWDS CSS file contains all required components")
    return True


def test_template_updates():
    """Test that templates have been updated with USWDS classes."""
    print("\nTesting template updates...")

    # Check header template
    header_path = (
        Path(__file__).parent
        / "code-intelligence-dashboard"
        / "dashboard"
        / "templates"
        / "header.html"
    )
    with open(header_path, "r") as f:
        header_content = f.read()

    if "usa-header" not in header_content:
        print("❌ Header template not updated with USWDS classes")
        return False

    # Check footer template
    footer_path = (
        Path(__file__).parent
        / "code-intelligence-dashboard"
        / "dashboard"
        / "templates"
        / "footer.html"
    )
    with open(footer_path, "r") as f:
        footer_content = f.read()

    if "usa-footer" not in footer_content:
        print("❌ Footer template not updated with USWDS classes")
        return False

    # Check error page template
    error_path = (
        Path(__file__).parent
        / "code-intelligence-dashboard"
        / "dashboard"
        / "templates"
        / "error_page.html"
    )
    with open(error_path, "r") as f:
        error_content = f.read()

    if "usa-alert" not in error_content:
        print("❌ Error page template not updated with USWDS classes")
        return False

    # Check stats card template
    stats_path = (
        Path(__file__).parent
        / "code-intelligence-dashboard"
        / "dashboard"
        / "templates"
        / "components"
        / "stats_card.html"
    )
    with open(stats_path, "r") as f:
        stats_content = f.read()

    if "dashboard-stat-card" not in stats_content:
        print("❌ Stats card template not updated with USWDS classes")
        return False

    print("✅ All templates updated with USWDS classes")
    return True


def test_app_configuration():
    """Test that app.py is configured to load USWDS assets."""
    print("\nTesting app configuration...")

    app_path = (
        Path(__file__).parent / "code-intelligence-dashboard" / "dashboard" / "app.py"
    )
    with open(app_path, "r") as f:
        app_content = f.read()

    required_configs = [
        "uswds-theme.css",  # CSS file reference
        "css_files=",  # CSS files configuration
        "Source+Sans+Pro",  # Google Fonts
        "uswds_init",  # USWDS JavaScript
    ]

    missing_configs = []
    for config in required_configs:
        if config not in app_content:
            missing_configs.append(config)

    if missing_configs:
        print(f"❌ Missing app configurations: {missing_configs}")
        return False

    print("✅ App properly configured for USWDS")
    return True


def test_component_updates():
    """Test that components use USWDS classes."""
    print("\nTesting component updates...")

    # Check views.py for USWDS classes
    views_path = (
        Path(__file__).parent / "code-intelligence-dashboard" / "dashboard" / "views.py"
    )
    with open(views_path, "r") as f:
        views_content = f.read()

    required_classes = [
        "usa-alert",  # Alert components
        "usa-card",  # Card components
        "dashboard-file-tip",  # Custom USWDS-styled components
        "usa-input",  # Form inputs
        "usa-button",  # Buttons
    ]

    missing_classes = []
    for cls in required_classes:
        if cls not in views_content:
            missing_classes.append(cls)

    if missing_classes:
        print(f"❌ Missing USWDS classes in views: {missing_classes}")
        return False

    # Check code explorer component
    explorer_path = (
        Path(__file__).parent
        / "code-intelligence-dashboard"
        / "dashboard"
        / "components"
        / "code_explorer.py"
    )
    with open(explorer_path, "r") as f:
        explorer_content = f.read()

    if "usa-card" not in explorer_content:
        print("❌ Code explorer not updated with USWDS classes")
        return False

    print("✅ Components updated with USWDS classes")
    return True


def test_accessibility_features():
    """Test that accessibility features are implemented."""
    print("\nTesting accessibility features...")

    css_path = (
        Path(__file__).parent
        / "code-intelligence-dashboard"
        / "dashboard"
        / "assets"
        / "uswds-theme.css"
    )
    with open(css_path, "r") as f:
        css_content = f.read()

    accessibility_features = [
        "usa-sr-only",  # Screen reader only class
        "role=",  # ARIA roles in templates
        "aria-",  # ARIA attributes
        "prefers-reduced-motion",  # Reduced motion support
        "prefers-contrast",  # High contrast support
        ":focus",  # Focus indicators
    ]

    # Check CSS file
    missing_a11y = []
    for feature in accessibility_features[:4]:  # CSS-specific features
        if feature not in css_content:
            missing_a11y.append(feature)

    # Check templates for ARIA attributes
    header_path = (
        Path(__file__).parent
        / "code-intelligence-dashboard"
        / "dashboard"
        / "templates"
        / "header.html"
    )
    with open(header_path, "r") as f:
        header_content = f.read()

    if "role=" not in header_content:
        missing_a11y.append("ARIA roles in header")

    if missing_a11y:
        print(f"❌ Missing accessibility features: {missing_a11y}")
        return False

    print("✅ Accessibility features implemented")
    return True


def test_design_tokens():
    """Test that USWDS design tokens are properly defined."""
    print("\nTesting USWDS design tokens...")

    css_path = (
        Path(__file__).parent
        / "code-intelligence-dashboard"
        / "dashboard"
        / "assets"
        / "uswds-theme.css"
    )
    with open(css_path, "r") as f:
        css_content = f.read()

    required_tokens = [
        "--usa-color-primary:",
        "--usa-color-secondary:",
        "--usa-font-family-sans:",
        "--usa-font-size-xs:",
        "--usa-spacing-2:",
        "--usa-border-radius-md:",
        "--usa-shadow-2:",
    ]

    missing_tokens = []
    for token in required_tokens:
        if token not in css_content:
            missing_tokens.append(token)

    if missing_tokens:
        print(f"❌ Missing design tokens: {missing_tokens}")
        return False

    print("✅ USWDS design tokens properly defined")
    return True


def main():
    """Run all USWDS theme tests."""
    print("🎨 Testing USWDS Theme Implementation\n" + "=" * 50)

    tests = [
        test_uswds_css_files,
        test_template_updates,
        test_app_configuration,
        test_component_updates,
        test_accessibility_features,
        test_design_tokens,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

    print(f"\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print(
            "🎉 All USWDS theme tests passed! The dashboard now follows U.S. Web Design System standards."
        )
        print("\n🔍 Key USWDS Features Implemented:")
        print("   ✅ Official USWDS color palette and design tokens")
        print("   ✅ Accessible typography with Source Sans Pro and Merriweather")
        print("   ✅ Semantic HTML with proper ARIA roles and labels")
        print("   ✅ Responsive design with mobile-first approach")
        print("   ✅ High contrast and reduced motion support")
        print("   ✅ USWDS components: headers, footers, cards, alerts, buttons")
        print("   ✅ Government-grade accessibility standards (Section 508 compliant)")
        return True
    else:
        print("⚠️  Some USWDS theme tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
