#!/usr/bin/env python3
"""
Test script to validate UI fixes for the dashboard.
"""

import sys
from pathlib import Path

# Add the dashboard to the path
sys.path.insert(0, str(Path(__file__).parent / "code-intelligence-dashboard"))


def test_imports():
    """Test that all components can be imported without errors."""
    print("Testing imports...")

    try:
        from dashboard.views import DashboardState, FileExplorer

        print("✅ FileExplorer imported successfully")

        from dashboard.components.code_explorer import CodeExplorerComponent

        print("✅ CodeExplorerComponent imported successfully")

        from dashboard.views import create_dashboard

        print("✅ create_dashboard imported successfully")

        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_file_explorer_creation():
    """Test FileExplorer component creation."""
    print("\nTesting FileExplorer creation...")

    try:
        from dashboard.views import DashboardState, FileExplorer

        # Create state
        state = DashboardState(db_path="code_intelligence.db")
        print("✅ DashboardState created")

        # Create file explorer
        file_explorer = FileExplorer(state)
        print("✅ FileExplorer created")

        # Test view creation
        view = file_explorer.view()
        print("✅ FileExplorer view created")

        return True
    except Exception as e:
        print(f"❌ FileExplorer creation error: {e}")
        return False


def test_code_explorer_creation():
    """Test CodeExplorer component creation."""
    print("\nTesting CodeExplorer creation...")

    try:
        from dashboard.components.code_explorer import CodeExplorerComponent
        from dashboard.views import DashboardState

        # Create state
        state = DashboardState(db_path="code_intelligence.db")
        print("✅ DashboardState created")

        # Create code explorer
        code_explorer = CodeExplorerComponent(state)
        print("✅ CodeExplorerComponent created")

        # Test view creation
        view = code_explorer.view()
        print("✅ CodeExplorerComponent view created")

        return True
    except Exception as e:
        print(f"❌ CodeExplorer creation error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing UI Fixes\n" + "=" * 50)

    tests = [
        test_imports,
        test_file_explorer_creation,
        test_code_explorer_creation,
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
        print("🎉 All tests passed! UI fixes are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
