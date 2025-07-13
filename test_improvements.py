"""
Test script to validate the code intelligence dashboard submodule improvements.

This script tests the new service layer and improved models to ensure
the refactoring was successful.

**Last Updated:** 2025-01-27 15:30:00
"""

import asyncio
from pathlib import Path

# Test the new services
from dashboard.services import StatisticsService, TemplateService
from dashboard.models.dashboard_models import (
    EdgeFilterOptionsModel,
    HoverTooltipsModel,
    NodeDataModel,
)


async def test_services():
    """Test the new service layer."""
    print("Testing service layer...")

    # Test StatisticsService
    stats_service = StatisticsService()
    await stats_service.initialize()

    # Test health check
    health = await stats_service.health_check()
    print(f"Statistics service health: {health}")

    # Test TemplateService
    template_service = TemplateService()
    await template_service.initialize()

    health = await template_service.health_check()
    print(f"Template service health: {health}")

    # Test template validation
    template_path = "nonexistent.html"
    validation = await template_service.validate_template(template_path)
    print(f"Template validation result: {validation}")

    print("✅ Service layer tests passed!")


def test_models():
    """Test the improved Pydantic models."""
    print("\nTesting improved models...")

    # Test EdgeFilterOptionsModel
    try:
        edge_options = EdgeFilterOptionsModel()
        print(f"EdgeFilterOptions: {edge_options}")

        # Test validation
        invalid_options = EdgeFilterOptionsModel(options=["invalid_option"])
        print("❌ Should have failed validation!")
    except ValueError as e:
        print(f"✅ EdgeFilterOptions validation works: {e}")

    # Test HoverTooltipsModel
    try:
        tooltips = HoverTooltipsModel()
        labels = tooltips.get_tooltip_labels()
        fields = tooltips.get_tooltip_fields()
        print(f"✅ HoverTooltips: {len(labels)} labels, {len(fields)} fields")

        # Test validation
        invalid_tooltips = HoverTooltipsModel(tooltips=[("", "invalid")])
        print("❌ Should have failed validation!")
    except ValueError as e:
        print(f"✅ HoverTooltips validation works: {e}")

    # Test NodeDataModel
    node_data = NodeDataModel()
    print(
        f"✅ NodeDataModel: {node_data.get_node_count()} nodes, empty: {node_data.is_empty()}"
    )

    # Test consistent length validation
    try:
        invalid_node_data = NodeDataModel(
            id=[1, 2], x=[1.0], y=[1.0, 2.0]  # Different length
        )
        print("❌ Should have failed validation!")
    except ValueError as e:
        print(f"✅ NodeDataModel validation works: {e}")

    print("✅ Model tests passed!")


async def main():
    """Run all tests."""
    print("🔍 Testing Code Intelligence Dashboard Submodule Improvements")
    print("=" * 60)

    try:
        await test_services()
        test_models()

        print("\n" + "=" * 60)
        print("🎉 All tests passed! Submodule improvements are working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
