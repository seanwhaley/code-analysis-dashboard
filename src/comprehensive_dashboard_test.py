#!/usr/bin/env python3
"""
Comprehensive dashboard test including data population and full functionality testing
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import requests

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_server_connectivity():
    """Test if the dashboard server is running"""
    print("🔗 Testing Server Connectivity")
    print("-" * 40)

    try:
        response = requests.get("http://localhost:8001/api/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running")
            print(f"   📊 Files: {data.get('data', {}).get('total_files', 0)}")
            print(f"   📊 Classes: {data.get('data', {}).get('total_classes', 0)}")
            print(f"   📊 Functions: {data.get('data', {}).get('total_functions', 0)}")
            return True, data.get("data", {})
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False, {}
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False, {}


def test_api_endpoints():
    """Test all API endpoints"""
    print("\n🔌 Testing API Endpoints")
    print("-" * 40)

    endpoints = [
        ("/api/stats", "System statistics"),
        ("/api/files?limit=5", "Files list"),
        ("/api/classes?limit=5", "Classes list"),
        ("/api/functions?limit=5", "Functions list"),
        ("/api/search?q=test&limit=5", "Search functionality"),
        ("/api/domains", "Domain statistics"),
        ("/api/complexity/distribution", "Complexity distribution"),
    ]

    results = []
    for endpoint, description in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"http://localhost:8001{endpoint}", timeout=10)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                item_count = len(data.get("data", []))
                print(
                    f"✅ {endpoint} - {description} ({response_time:.1f}ms, {item_count} items)"
                )
                results.append(True)
            else:
                print(f"❌ {endpoint} - Status {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"   📊 Passed: {passed}/{total} endpoints")
    return passed == total


def test_frontend_accessibility():
    """Test frontend page accessibility"""
    print("\n📱 Testing Frontend Accessibility")
    print("-" * 40)

    try:
        response = requests.get("http://localhost:8001/", timeout=10)
        if response.status_code == 200:
            content = response.text

            # Check for key elements
            checks = [
                ("title", "<title>" in content),
                ("navigation", "nav" in content),
                ("main content", "main" in content),
                ("JavaScript", ".js" in content),
                ("CSS", ".css" in content),
            ]

            passed = 0
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"   {status} {check_name}")
                if result:
                    passed += 1

            print(f"   📊 Frontend checks: {passed}/{len(checks)}")
            return passed == len(checks)
        else:
            print(f"❌ Frontend not accessible (status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return False


def test_search_functionality():
    """Test search functionality with various queries"""
    print("\n🔍 Testing Search Functionality")
    print("-" * 40)

    search_queries = [
        ("test", "General search"),
        ("class", "Class search"),
        ("function", "Function search"),
        ("main", "Main function search"),
        ("init", "Init method search"),
    ]

    results = []
    for query, description in search_queries:
        try:
            response = requests.get(
                f"http://localhost:8001/api/search?q={query}&limit=5", timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get("data", []))
                print(f"✅ {description} ('{query}'): {result_count} results")
                results.append(True)
            else:
                print(f"❌ {description} failed")
                results.append(False)
        except Exception as e:
            print(f"❌ {description} error: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"   📊 Passed: {passed}/{total} searches")
    return passed == total


def test_performance():
    """Test API performance"""
    print("\n⚡ Testing Performance")
    print("-" * 40)

    performance_tests = [
        ("/api/stats", "System stats"),
        ("/api/files?limit=10", "Files query"),
        ("/api/search?q=test", "Search query"),
    ]

    for endpoint, description in performance_tests:
        times = []
        for _ in range(3):  # Run 3 times for average
            try:
                start_time = time.time()
                response = requests.get(f"http://localhost:8001{endpoint}", timeout=5)
                response_time = (time.time() - start_time) * 1000
                if response.status_code == 200:
                    times.append(response_time)
            except:
                pass

        if times:
            avg_time = sum(times) / len(times)
            print(f"   📊 {description}: {avg_time:.1f}ms avg")
        else:
            print(f"   ❌ {description}: Failed")


async def test_async_database_operations():
    """Test async database operations"""
    print("\n🚀 Testing Async Database Operations")
    print("-" * 40)

    try:
        from api.sqlite_backend import DocumentationDatabase

        db = DocumentationDatabase()

        # Test concurrent async operations
        start_time = time.time()

        tasks = [
            db.get_system_stats_async(),
            db.search_files_async(limit=5),
            db.search_classes_async(limit=5),
        ]

        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time

        print(f"✅ Concurrent async operations: {concurrent_time:.3f}s")
        print(f"   📊 Stats: {len(results[0])} items")
        print(f"   📄 Files: {len(results[1])} items")
        print(f"   🏗️ Classes: {len(results[2])} items")

        return True

    except Exception as e:
        print(f"❌ Async operations failed: {e}")
        return False


def main():
    """Main test runner"""
    print("🎯 Comprehensive Dashboard Test Suite")
    print("=" * 60)

    total_start = time.time()

    # Test server connectivity first
    server_running, stats = test_server_connectivity()
    if not server_running:
        print("\n❌ Server is not running. Please start the dashboard first:")
        print("   python launch.py --port 8001")
        return False

    # Run all tests
    tests = [
        ("API Endpoints", test_api_endpoints()),
        ("Frontend Accessibility", test_frontend_accessibility()),
        ("Search Functionality", test_search_functionality()),
    ]

    # Add performance test
    test_performance()

    # Add async test
    try:
        async_result = asyncio.run(test_async_database_operations())
        tests.append(("Async Operations", async_result))
    except Exception as e:
        print(f"\n❌ Async test failed: {e}")
        tests.append(("Async Operations", False))

    total_time = time.time() - total_start

    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\n🎉 Results: {passed}/{total} tests passed")
    print(f"⏱️ Total time: {total_time:.3f}s")

    if stats.get("total_files", 0) == 0:
        print("\n💡 Note: Database appears empty. Consider running data import:")
        print(
            "   python -c \"from api.sqlite_backend import DocumentationDatabase; db = DocumentationDatabase(); print('Database ready')\""
        )

    if passed == total:
        print("🚀 All dashboard tests passed!")
        return True
    else:
        print("⚠️ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)  #!/usr/bin/env python3
"""
Comprehensive dashboard test including data population and full functionality testing
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import requests

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_server_connectivity():
    """Test if the dashboard server is running"""
    print("🔗 Testing Server Connectivity")
    print("-" * 40)

    try:
        response = requests.get("http://localhost:8001/api/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running")
            print(f"   📊 Files: {data.get('data', {}).get('total_files', 0)}")
            print(f"   📊 Classes: {data.get('data', {}).get('total_classes', 0)}")
            print(f"   📊 Functions: {data.get('data', {}).get('total_functions', 0)}")
            return True, data.get("data", {})
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False, {}
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False, {}


def test_api_endpoints():
    """Test all API endpoints"""
    print("\n🔌 Testing API Endpoints")
    print("-" * 40)

    endpoints = [
        ("/api/stats", "System statistics"),
        ("/api/files?limit=5", "Files list"),
        ("/api/classes?limit=5", "Classes list"),
        ("/api/functions?limit=5", "Functions list"),
        ("/api/search?q=test&limit=5", "Search functionality"),
        ("/api/domains", "Domain statistics"),
        ("/api/complexity/distribution", "Complexity distribution"),
    ]

    results = []
    for endpoint, description in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"http://localhost:8001{endpoint}", timeout=10)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                item_count = len(data.get("data", []))
                print(
                    f"✅ {endpoint} - {description} ({response_time:.1f}ms, {item_count} items)"
                )
                results.append(True)
            else:
                print(f"❌ {endpoint} - Status {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"   📊 Passed: {passed}/{total} endpoints")
    return passed == total


def test_frontend_accessibility():
    """Test frontend page accessibility"""
    print("\n📱 Testing Frontend Accessibility")
    print("-" * 40)

    try:
        response = requests.get("http://localhost:8001/", timeout=10)
        if response.status_code == 200:
            content = response.text

            # Check for key elements
            checks = [
                ("title", "<title>" in content),
                ("navigation", "nav" in content),
                ("main content", "main" in content),
                ("JavaScript", ".js" in content),
                ("CSS", ".css" in content),
            ]

            passed = 0
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"   {status} {check_name}")
                if result:
                    passed += 1

            print(f"   📊 Frontend checks: {passed}/{len(checks)}")
            return passed == len(checks)
        else:
            print(f"❌ Frontend not accessible (status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return False


def test_search_functionality():
    """Test search functionality with various queries"""
    print("\n🔍 Testing Search Functionality")
    print("-" * 40)

    search_queries = [
        ("test", "General search"),
        ("class", "Class search"),
        ("function", "Function search"),
        ("main", "Main function search"),
        ("init", "Init method search"),
    ]

    results = []
    for query, description in search_queries:
        try:
            response = requests.get(
                f"http://localhost:8001/api/search?q={query}&limit=5", timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get("data", []))
                print(f"✅ {description} ('{query}'): {result_count} results")
                results.append(True)
            else:
                print(f"❌ {description} failed")
                results.append(False)
        except Exception as e:
            print(f"❌ {description} error: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"   📊 Passed: {passed}/{total} searches")
    return passed == total


def test_performance():
    """Test API performance"""
    print("\n⚡ Testing Performance")
    print("-" * 40)

    performance_tests = [
        ("/api/stats", "System stats"),
        ("/api/files?limit=10", "Files query"),
        ("/api/search?q=test", "Search query"),
    ]

    for endpoint, description in performance_tests:
        times = []
        for _ in range(3):  # Run 3 times for average
            try:
                start_time = time.time()
                response = requests.get(f"http://localhost:8001{endpoint}", timeout=5)
                response_time = (time.time() - start_time) * 1000
                if response.status_code == 200:
                    times.append(response_time)
            except:
                pass

        if times:
            avg_time = sum(times) / len(times)
            print(f"   📊 {description}: {avg_time:.1f}ms avg")
        else:
            print(f"   ❌ {description}: Failed")


async def test_async_database_operations():
    """Test async database operations"""
    print("\n🚀 Testing Async Database Operations")
    print("-" * 40)

    try:
        from api.sqlite_backend import DocumentationDatabase

        db = DocumentationDatabase()

        # Test concurrent async operations
        start_time = time.time()

        tasks = [
            db.get_system_stats_async(),
            db.search_files_async(limit=5),
            db.search_classes_async(limit=5),
        ]

        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time

        print(f"✅ Concurrent async operations: {concurrent_time:.3f}s")
        print(f"   📊 Stats: {len(results[0])} items")
        print(f"   📄 Files: {len(results[1])} items")
        print(f"   🏗️ Classes: {len(results[2])} items")

        return True

    except Exception as e:
        print(f"❌ Async operations failed: {e}")
        return False


def main():
    """Main test runner"""
    print("🎯 Comprehensive Dashboard Test Suite")
    print("=" * 60)

    total_start = time.time()

    # Test server connectivity first
    server_running, stats = test_server_connectivity()
    if not server_running:
        print("\n❌ Server is not running. Please start the dashboard first:")
        print("   python launch.py --port 8001")
        return False

    # Run all tests
    tests = [
        ("API Endpoints", test_api_endpoints()),
        ("Frontend Accessibility", test_frontend_accessibility()),
        ("Search Functionality", test_search_functionality()),
    ]

    # Add performance test
    test_performance()

    # Add async test
    try:
        async_result = asyncio.run(test_async_database_operations())
        tests.append(("Async Operations", async_result))
    except Exception as e:
        print(f"\n❌ Async test failed: {e}")
        tests.append(("Async Operations", False))

    total_time = time.time() - total_start

    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\n🎉 Results: {passed}/{total} tests passed")
    print(f"⏱️ Total time: {total_time:.3f}s")

    if stats.get("total_files", 0) == 0:
        print("\n💡 Note: Database appears empty. Consider running data import:")
        print(
            "   python -c \"from api.sqlite_backend import DocumentationDatabase; db = DocumentationDatabase(); print('Database ready')\""
        )

    if passed == total:
        print("🚀 All dashboard tests passed!")
        return True
    else:
        print("⚠️ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
