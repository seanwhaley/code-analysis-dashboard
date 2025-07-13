#!/usr/bin/env python3
"""
Test Dashboard Creation
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


def test_dashboard_creation():
    """Test if the dashboard can be created successfully."""
    try:
        print("🔍 Testing dashboard creation...")

        # Test basic imports
        print("📦 Testing imports...")
        from dashboard.views import DashboardState, create_dashboard

        print("✅ Imports successful")

        # Test state creation
        print("🏗️ Testing state creation...")
        state = DashboardState()
        print("✅ State created successfully")

        # Test database connectivity
        print("🗄️ Testing database connectivity...")
        files_result = state.db_service.safe_query_files(limit=1)
        print(
            f"✅ Database query: success={files_result.success}, files={len(files_result.data) if files_result.success else 0}"
        )

        # Test dashboard creation
        print("📊 Testing dashboard creation...")
        dashboard = create_dashboard()
        print(f"✅ Dashboard created: {type(dashboard)}")
        print(f"📋 Dashboard has {len(dashboard)} tabs")

        # Test individual components
        print("🧩 Testing individual components...")
        from dashboard.views import FileExplorer, SearchPanel, StatisticsPanel

        file_explorer = FileExplorer(state)
        print("✅ FileExplorer created")

        stats_panel = StatisticsPanel(state)
        print("✅ StatisticsPanel created")

        search_panel = SearchPanel(state)
        print("✅ SearchPanel created")

        print("\n🎉 All tests passed! Dashboard should be working.")
        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_dashboard_creation()
    sys.exit(0 if success else 1)
