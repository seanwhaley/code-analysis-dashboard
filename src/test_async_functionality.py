#!/usr/bin/env python3
"""
Test script to validate async functionality in the dashboard
"""
import asyncio
import os
import sys
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.sqlite_backend import DocumentationDatabase


async def test_async_database_operations():
    """Test async database operations"""
    print("🔄 Testing Async Database Operations")
    print("=" * 50)

    # Initialize database
    db = DocumentationDatabase()

    # Test async system stats
    start_time = time.time()
    stats = await db.get_system_stats_async()
    async_time = time.time() - start_time

    print(f"✅ Async system stats: {async_time:.3f}s")
    print(f"   📊 Files: {stats.get('total_files', 0)}")
    print(f"   📊 Classes: {stats.get('total_classes', 0)}")
    print(f"   📊 Functions: {stats.get('total_functions', 0)}")

    # Test async file search
    start_time = time.time()
    files = await db.search_files_async(limit=5)
    async_search_time = time.time() - start_time

    print(f"✅ Async file search: {async_search_time:.3f}s")
    print(f"   📄 Found {len(files)} files")

    # Test async class search
    start_time = time.time()
    classes = await db.search_classes_async(limit=5)
    async_class_time = time.time() - start_time

    print(f"✅ Async class search: {async_class_time:.3f}s")
    print(f"   🏗️ Found {len(classes)} classes")

    # Test concurrent operations
    print("\n🚀 Testing Concurrent Operations")
    print("-" * 30)

    start_time = time.time()

    # Run multiple async operations concurrently
    tasks = [
        db.get_system_stats_async(),
        db.search_files_async(limit=10),
        db.search_classes_async(limit=10),
    ]

    results = await asyncio.gather(*tasks)
    concurrent_time = time.time() - start_time

    print(f"✅ Concurrent operations: {concurrent_time:.3f}s")
    print(f"   📊 Stats: {len(results[0])} items")
    print(f"   📄 Files: {len(results[1])} items")
    print(f"   🏗️ Classes: {len(results[2])} items")

    # Compare with sequential execution
    print("\n⏱️ Performance Comparison")
    print("-" * 30)

    start_time = time.time()
    await db.get_system_stats_async()
    await db.search_files_async(limit=10)
    await db.search_classes_async(limit=10)
    sequential_time = time.time() - start_time

    improvement = ((sequential_time - concurrent_time) / sequential_time) * 100

    print(f"   Sequential: {sequential_time:.3f}s")
    print(f"   Concurrent: {concurrent_time:.3f}s")
    print(f"   🚀 Performance improvement: {improvement:.1f}%")

    return True


async def test_async_maintenance():
    """Test async maintenance operations"""
    print("\n🔧 Testing Async Maintenance")
    print("=" * 50)

    try:
        from dashboard_maintenance import DashboardMaintenance

        maintenance = DashboardMaintenance()

        # Test async database stats
        start_time = time.time()
        stats = await maintenance.analyze_database_stats_async()
        maintenance_time = time.time() - start_time

        print(f"✅ Async maintenance stats: {maintenance_time:.3f}s")
        print(f"   📊 Analysis completed")

        return True

    except Exception as e:
        print(f"❌ Async maintenance test failed: {e}")
        return False


async def test_async_validation():
    """Test async validation operations"""
    print("\n🔍 Testing Async Validation")
    print("=" * 50)

    try:
        from dashboard_validator import DashboardValidator

        validator = DashboardValidator()

        # Test async API validation
        start_time = time.time()
        results = await validator.validate_api_integration_async()
        validation_time = time.time() - start_time

        print(f"✅ Async API validation: {validation_time:.3f}s")
        print(f"   🔌 Endpoints tested: {len(results.get('endpoints', []))}")

        return True

    except Exception as e:
        print(f"❌ Async validation test failed: {e}")
        return False


async def main():
    """Main test runner"""
    print("🎯 Async Functionality Test Suite")
    print("=" * 60)

    total_start = time.time()

    # Run all async tests
    tests = [
        ("Database Operations", test_async_database_operations()),
        ("Maintenance Operations", test_async_maintenance()),
        ("Validation Operations", test_async_validation()),
    ]

    results = []
    for test_name, test_coro in tests:
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))

    total_time = time.time() - total_start

    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\n🎉 Results: {passed}/{total} tests passed")
    print(f"⏱️ Total time: {total_time:.3f}s")

    if passed == total:
        print("🚀 All async functionality tests passed!")
        return True
    else:
        print("⚠️ Some async tests failed")
        return False


if __name__ == "__main__":
    # Check if required dependencies are available
    try:
        import aiohttp
        import aiosqlite
    except ImportError as e:
        print(f"❌ Missing async dependencies: {e}")
        print("💡 Install with: pip install aiosqlite aiohttp")
        sys.exit(1)

    # Run async tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
