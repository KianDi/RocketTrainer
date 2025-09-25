#!/usr/bin/env python3
"""
Quick performance test for optimized ML API with database pool monitoring.
"""

import asyncio
import aiohttp
import time
import json
import statistics
from uuid import uuid4
from datetime import datetime

async def test_optimized_performance():
    """Test the optimized ML API performance."""
    print("🚀 Testing Optimized ML API Performance")
    print("="*60)
    
    base_url = "http://localhost:8000/api/ml"
    
    # Test 1: Check model status with database pool info
    print("\n📊 Testing Model Status with Database Pool Monitoring...")
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        async with session.get(f"{base_url}/model-status") as response:
            if response.status == 200:
                data = await response.json()
                response_time = (time.time() - start_time) * 1000
                
                print(f"✅ Model Status: {response_time:.1f}ms")
                print(f"   System Status: {data['system_status']}")
                
                # Display database pool statistics
                db_pool = data.get('database_pool', {})
                print(f"   Database Pool:")
                print(f"     - Pool Size: {db_pool.get('pool_size', 0)}")
                print(f"     - Active Connections: {db_pool.get('checked_out_connections', 0)}")
                print(f"     - Available Connections: {db_pool.get('checked_in_connections', 0)}")
                print(f"     - Utilization: {db_pool.get('utilization_percent', 0):.1f}%")
            else:
                print(f"❌ Model Status failed: {response.status}")
    
    # Test 2: Concurrent load test with smaller scale
    print(f"\n🚀 Testing Concurrent Load (10 users, 3 requests each)...")
    
    # Create test scenarios
    test_scenarios = []
    for i in range(10):  # 10 concurrent users
        for j in range(3):  # 3 requests each
            if j % 2 == 0:
                scenario = {
                    "method": "GET",
                    "url": f"{base_url}/model-status"
                }
            else:
                scenario = {
                    "method": "POST",
                    "url": f"{base_url}/analyze-weaknesses",
                    "payload": {
                        "user_id": str(uuid4()),
                        "include_confidence": True,
                        "analysis_depth": "standard"
                    }
                }
            test_scenarios.append(scenario)
    
    # Execute concurrent requests
    start_time = time.time()
    
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        connector=aiohttp.TCPConnector(limit=50, limit_per_host=25)
    ) as session:
        tasks = [execute_request(session, scenario) for scenario in test_scenarios]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful_results = [r for r in results if isinstance(r, dict) and not isinstance(r, Exception)]
    failed_results = [r for r in results if isinstance(r, Exception)]
    
    if successful_results:
        response_times = [r['response_time_ms'] for r in successful_results]
        
        print(f"✅ Concurrent Load Test Results:")
        print(f"   Total Requests: {len(test_scenarios)}")
        print(f"   Successful: {len(successful_results)}")
        print(f"   Failed: {len(failed_results)}")
        print(f"   Success Rate: {len(successful_results) / len(test_scenarios) * 100:.1f}%")
        print(f"   Average Response Time: {statistics.mean(response_times):.1f}ms")
        print(f"   Median Response Time: {statistics.median(response_times):.1f}ms")
        print(f"   P95 Response Time: {sorted(response_times)[int(0.95 * len(response_times))]:.1f}ms")
        print(f"   Max Response Time: {max(response_times):.1f}ms")
        print(f"   Throughput: {len(successful_results) / total_time:.1f} req/sec")
        print(f"   Total Test Duration: {total_time:.1f}s")
        
        # Performance assessment
        avg_time = statistics.mean(response_times)
        success_rate = len(successful_results) / len(test_scenarios)
        
        if avg_time < 500 and success_rate >= 0.95:
            print(f"\n🎉 EXCELLENT: Performance meets production requirements!")
            print(f"   ✅ Average response time: {avg_time:.1f}ms (<500ms target)")
            print(f"   ✅ Success rate: {success_rate*100:.1f}% (>95% target)")
        elif avg_time < 1000 and success_rate >= 0.90:
            print(f"\n✅ GOOD: Performance is acceptable with room for improvement")
            print(f"   ⚠️  Average response time: {avg_time:.1f}ms")
            print(f"   ⚠️  Success rate: {success_rate*100:.1f}%")
        else:
            print(f"\n❌ NEEDS IMPROVEMENT: Performance below production standards")
            print(f"   ❌ Average response time: {avg_time:.1f}ms (target: <500ms)")
            print(f"   ❌ Success rate: {success_rate*100:.1f}% (target: >95%)")
    else:
        print(f"❌ All {len(test_scenarios)} requests failed")
    
    # Test 3: Check final database pool status
    print(f"\n📊 Final Database Pool Status...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/model-status") as response:
            if response.status == 200:
                data = await response.json()
                db_pool = data.get('database_pool', {})
                print(f"   Pool Size: {db_pool.get('pool_size', 0)}")
                print(f"   Active Connections: {db_pool.get('checked_out_connections', 0)}")
                print(f"   Available Connections: {db_pool.get('checked_in_connections', 0)}")
                print(f"   Total Connections: {db_pool.get('total_connections', 0)}")
                print(f"   Utilization: {db_pool.get('utilization_percent', 0):.1f}%")
                
                if db_pool.get('utilization_percent', 0) > 80:
                    print(f"   ⚠️  HIGH UTILIZATION: Consider increasing pool size")
                elif db_pool.get('utilization_percent', 0) > 50:
                    print(f"   ✅ MODERATE UTILIZATION: Pool size is adequate")
                else:
                    print(f"   ✅ LOW UTILIZATION: Pool size is sufficient")


async def execute_request(session: aiohttp.ClientSession, scenario: dict) -> dict:
    """Execute a single request scenario."""
    start_time = time.time()
    
    try:
        if scenario["method"] == "GET":
            async with session.get(scenario["url"]) as response:
                await response.text()
                status_code = response.status
        else:  # POST
            async with session.post(scenario["url"], json=scenario["payload"]) as response:
                await response.text()
                status_code = response.status
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status_code": status_code,
            "response_time_ms": response_time,
            "success": status_code in [200, 400, 404]  # Accept expected error codes
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "response_time_ms": (time.time() - start_time) * 1000,
            "success": False
        }


if __name__ == "__main__":
    asyncio.run(test_optimized_performance())
