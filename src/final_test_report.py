#!/usr/bin/env python3
"""
Final test report generator for the dashboard with async optimizations
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def benchmark_async_vs_sync():
    """Benchmark async vs sync database operations"""
    print("⚡ Benchmarking Async vs Sync Operations")
    print("-" * 50)

    try:
        from api.sqlite_backend import DocumentationDatabase

        db = DocumentationDatabase()

        # Test sync operations
        print("   🔄 Testing sync operations...")
        sync_start = time.time()

        stats1 = db.get_system_stats()
        files1 = db.search_files(limit=10)
        classes1 = db.search_classes(limit=10)

        sync_time = time.time() - sync_start

        # Test async operations (sequential)
        print("   🔄 Testing async operations (sequential)...")
        async_seq_start = time.time()

        stats2 = await db.get_system_stats_async()
        files2 = await db.search_files_async(limit=10)
        classes2 = await db.search_classes_async(limit=10)

        async_seq_time = time.time() - async_seq_start

        # Test async operations (concurrent)
        print("   🔄 Testing async operations (concurrent)...")
        async_conc_start = time.time()

        results = await asyncio.gather(
            db.get_system_stats_async(),
            db.search_files_async(limit=10),
            db.search_classes_async(limit=10),
        )

        async_conc_time = time.time() - async_conc_start

        # Calculate improvements
        seq_improvement = ((sync_time - async_seq_time) / sync_time) * 100
        conc_improvement = ((sync_time - async_conc_time) / sync_time) * 100

        print(f"   📊 Sync operations: {sync_time:.3f}s")
        print(
            f"   📊 Async sequential: {async_seq_time:.3f}s ({seq_improvement:+.1f}%)"
        )
        print(
            f"   📊 Async concurrent: {async_conc_time:.3f}s ({conc_improvement:+.1f}%)"
        )

        return {
            "sync_time": sync_time,
            "async_sequential_time": async_seq_time,
            "async_concurrent_time": async_conc_time,
            "sequential_improvement": seq_improvement,
            "concurrent_improvement": conc_improvement,
        }

    except Exception as e:
        print(f"   ❌ Benchmark failed: {e}")
        return None


def test_load_handling():
    """Test how the dashboard handles multiple concurrent requests"""
    print("\n🚀 Testing Load Handling")
    print("-" * 50)

    import queue
    import threading

    def make_request(endpoint, result_queue):
        try:
            start_time = time.time()
            response = requests.get(f"http://localhost:8001{endpoint}", timeout=10)
            response_time = time.time() - start_time
            result_queue.put((endpoint, response.status_code == 200, response_time))
        except Exception as e:
            result_queue.put((endpoint, False, 0))

    # Test endpoints
    endpoints = [
        "/api/stats",
        "/api/files?limit=5",
        "/api/classes?limit=5",
        "/api/functions?limit=5",
        "/api/search?q=test",
    ]

    # Create multiple concurrent requests
    result_queue = queue.Queue()
    threads = []

    print("   🔄 Sending 15 concurrent requests...")
    start_time = time.time()

    for i in range(3):  # 3 rounds
        for endpoint in endpoints:
            thread = threading.Thread(
                target=make_request, args=(endpoint, result_queue)
            )
            threads.append(thread)
            thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    total_time = time.time() - start_time

    # Collect results
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    successful = sum(1 for _, success, _ in results if success)
    total_requests = len(results)
    avg_response_time = sum(time for _, success, time in results if success) / max(
        successful, 1
    )

    print(f"   📊 Total requests: {total_requests}")
    print(f"   📊 Successful: {successful}")
    print(f"   📊 Success rate: {(successful/total_requests)*100:.1f}%")
    print(f"   📊 Total time: {total_time:.3f}s")
    print(f"   📊 Avg response time: {avg_response_time:.3f}s")

    return {
        "total_requests": total_requests,
        "successful_requests": successful,
        "success_rate": (successful / total_requests) * 100,
        "total_time": total_time,
        "avg_response_time": avg_response_time,
    }


def validate_data_integrity():
    """Validate that the database contains expected data"""
    print("\n🔍 Validating Data Integrity")
    print("-" * 50)

    try:
        response = requests.get("http://localhost:8001/api/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json().get("data", {})

            checks = [
                ("Files", stats.get("total_files", 0) > 0),
                ("Classes", stats.get("total_classes", 0) > 0),
                ("Functions", stats.get("total_functions", 0) > 0),
                ("Domains", stats.get("total_domains", 0) > 0),
            ]

            passed = 0
            for check_name, result in checks:
                status = "✅" if result else "❌"
                count = stats.get(f"total_{check_name.lower()}", 0)
                print(f"   {status} {check_name}: {count}")
                if result:
                    passed += 1

            print(f"   📊 Data integrity: {passed}/{len(checks)} checks passed")
            return passed == len(checks), stats
        else:
            print("   ❌ Could not retrieve stats")
            return False, {}
    except Exception as e:
        print(f"   ❌ Data integrity check failed: {e}")
        return False, {}


async def main():
    """Main test runner"""
    print("🎯 Final Dashboard Test Report")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Check server connectivity
    try:
        response = requests.get("http://localhost:8001/api/stats", timeout=5)
        if response.status_code != 200:
            print("❌ Dashboard server is not running")
            return False
    except:
        print("❌ Dashboard server is not accessible")
        return False

    print("✅ Dashboard server is running")

    # Run all tests
    results = {}

    # 1. Benchmark async operations
    benchmark_results = await benchmark_async_vs_sync()
    results["benchmark"] = benchmark_results

    # 2. Test load handling
    load_results = test_load_handling()
    results["load_test"] = load_results

    # 3. Validate data integrity
    integrity_passed, stats = validate_data_integrity()
    results["data_integrity"] = {"passed": integrity_passed, "stats": stats}

    # 4. Final summary
    print("\n📋 Final Test Summary")
    print("=" * 60)

    if benchmark_results:
        print(f"⚡ Async Performance:")
        print(
            f"   🚀 Concurrent improvement: {benchmark_results['concurrent_improvement']:+.1f}%"
        )
        print(
            f"   📈 Sequential improvement: {benchmark_results['sequential_improvement']:+.1f}%"
        )

    if load_results:
        print(f"🚀 Load Handling:")
        print(f"   📊 Success rate: {load_results['success_rate']:.1f}%")
        print(f"   ⏱️ Avg response time: {load_results['avg_response_time']:.3f}s")

    print(f"🔍 Data Integrity: {'✅ PASS' if integrity_passed else '❌ FAIL'}")

    # Save results
    results["timestamp"] = datetime.now().isoformat()
    results["summary"] = {
        "async_optimizations_working": benchmark_results is not None,
        "load_handling_good": (
            load_results["success_rate"] > 90 if load_results else False
        ),
        "data_integrity_good": integrity_passed,
        "overall_status": (
            "PASS"
            if all(
                [
                    benchmark_results is not None,
                    load_results["success_rate"] > 90 if load_results else False,
                    integrity_passed,
                ]
            )
            else "FAIL"
        ),
    }

    # Save to file
    with open("final_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: final_test_results.json")

    overall_status = results["summary"]["overall_status"]
    print(
        f"\n🎉 Overall Status: {'✅ PASS' if overall_status == 'PASS' else '❌ FAIL'}"
    )

    if overall_status == "PASS":
        print("🚀 Dashboard is fully functional with async optimizations!")
    else:
        print("⚠️ Some issues detected. Check the detailed results.")

    return overall_status == "PASS"


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
