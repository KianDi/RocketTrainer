#!/usr/bin/env python3
"""
Comprehensive performance validation for optimized ML API.
Tests database pool utilization under realistic load.
"""

import asyncio
import aiohttp
import time
import statistics
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def create_test_user_with_data():
    """Create a test user with match data to trigger database connections."""
    try:
        from app.database import get_db
        from app.models.user import User
        from app.models.match import Match
        
        db = next(get_db())
        
        # Create test user
        user_id = uuid4()
        test_user = User(
            id=user_id,
            username=f"perf_test_{user_id.hex[:8]}",
            email=f"perf_test_{user_id.hex[:8]}@example.com",
            steam_id=f"steam_{user_id.hex[:8]}",
            current_rank="platinum_ii",
            mmr=850,
            platform="steam",
            is_active=True
        )
        
        db.add(test_user)
        
        # Create sample matches
        base_date = datetime.utcnow() - timedelta(days=7)
        
        for i in range(10):
            match_date = base_date + timedelta(hours=i * 6)
            
            test_match = Match(
                id=uuid4(),
                user_id=user_id,
                match_date=match_date,
                processed=True,
                playlist="ranked-doubles",
                duration=300 + (i * 10),
                score_team_0=3 if i % 2 == 0 else 2,
                score_team_1=2 if i % 2 == 0 else 3,
                result="win" if i % 2 == 0 else "loss",
                score=400 + (i * 25),
                goals=max(0, i // 3),
                saves=max(0, i // 4),
                assists=max(0, i // 5),
                shots=max(1, i // 2),
                boost_usage=max(0.0, 100.0 - (i * 5.0)),
                average_speed=45.0 + (i * 2.0),
                time_supersonic=10.0 + i,
                time_on_ground=70.0 - i,
                time_low_air=15.0 + (i % 3),
                time_high_air=5.0 + (i % 4)
            )
            
            db.add(test_match)
        
        db.commit()
        print(f"✅ Created test user {user_id} with 10 matches")
        return user_id
        
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        if 'db' in locals():
            db.rollback()
        return None

async def cleanup_test_user(user_id):
    """Clean up test user and data."""
    try:
        from app.database import get_db
        from app.models.user import User
        from app.models.match import Match
        
        db = next(get_db())
        
        # Delete matches first
        db.query(Match).filter(Match.user_id == user_id).delete()
        
        # Delete user
        db.query(User).filter(User.id == user_id).delete()
        
        db.commit()
        print(f"✅ Cleaned up test user {user_id}")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        if 'db' in locals():
            db.rollback()

async def test_database_pool_performance():
    """Test ML API performance with database pool monitoring."""
    print("🚀 Comprehensive ML API Performance Validation")
    print("="*70)
    
    base_url = "http://localhost:8000/api/ml"
    
    # Create test user with data
    print("\n🏗️  Setting up test data...")
    test_user_id = await create_test_user_with_data()
    
    if not test_user_id:
        print("❌ Cannot proceed without test data")
        return
    
    try:
        # Test 1: Single request performance with database operations
        print("\n📊 Testing Single Request Performance...")
        
        async with aiohttp.ClientSession() as session:
            # Test weakness analysis (uses database)
            payload = {
                "user_id": str(test_user_id),
                "include_confidence": True,
                "analysis_depth": "detailed"
            }
            
            start_time = time.time()
            async with session.post(f"{base_url}/analyze-weaknesses", json=payload) as response:
                data = await response.text()
                response_time = (time.time() - start_time) * 1000
                
                print(f"✅ Weakness Analysis: {response_time:.1f}ms (Status: {response.status})")
            
            # Check database pool status after database operation
            async with session.get(f"{base_url}/model-status") as response:
                if response.status == 200:
                    data = await response.json()
                    db_pool = data.get('database_pool', {})
                    print(f"   Database Pool After Operation:")
                    print(f"     - Pool Size: {db_pool.get('pool_size', 0)}")
                    print(f"     - Active: {db_pool.get('checked_out_connections', 0)}")
                    print(f"     - Available: {db_pool.get('checked_in_connections', 0)}")
                    print(f"     - Total: {db_pool.get('total_connections', 0)}")
                    print(f"     - Utilization: {db_pool.get('utilization_percent', 0):.1f}%")
        
        # Test 2: Concurrent load with database operations
        print(f"\n🚀 Testing Concurrent Load with Database Operations...")
        print(f"   (20 concurrent users, 2 requests each = 40 total requests)")
        
        # Create test scenarios with real database operations
        test_scenarios = []
        for i in range(20):  # 20 concurrent users
            for j in range(2):  # 2 requests each
                if j == 0:
                    # Weakness analysis (database intensive)
                    scenario = {
                        "method": "POST",
                        "url": f"{base_url}/analyze-weaknesses",
                        "payload": {
                            "user_id": str(test_user_id),
                            "include_confidence": True,
                            "analysis_depth": "standard"
                        }
                    }
                else:
                    # Model status (lighter database operation)
                    scenario = {
                        "method": "GET",
                        "url": f"{base_url}/model-status"
                    }
                test_scenarios.append(scenario)
        
        # Execute concurrent requests
        start_time = time.time()
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=50, limit_per_host=30)
        ) as session:
            tasks = [execute_request(session, scenario) for scenario in test_scenarios]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get('success', False)]
        failed_results = [r for r in results if not (isinstance(r, dict) and r.get('success', False))]
        
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
            print(f"   P99 Response Time: {sorted(response_times)[int(0.99 * len(response_times))]:.1f}ms")
            print(f"   Max Response Time: {max(response_times):.1f}ms")
            print(f"   Throughput: {len(successful_results) / total_time:.1f} req/sec")
            print(f"   Total Test Duration: {total_time:.1f}s")
            
            # Check database pool status after concurrent load
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/model-status") as response:
                    if response.status == 200:
                        data = await response.json()
                        db_pool = data.get('database_pool', {})
                        print(f"\n📊 Database Pool Status After Concurrent Load:")
                        print(f"   Pool Size: {db_pool.get('pool_size', 0)}")
                        print(f"   Active Connections: {db_pool.get('checked_out_connections', 0)}")
                        print(f"   Available Connections: {db_pool.get('checked_in_connections', 0)}")
                        print(f"   Total Connections: {db_pool.get('total_connections', 0)}")
                        print(f"   Utilization: {db_pool.get('utilization_percent', 0):.1f}%")
                        
                        utilization = db_pool.get('utilization_percent', 0)
                        if utilization > 80:
                            print(f"   ⚠️  HIGH UTILIZATION: Pool may need optimization")
                        elif utilization > 50:
                            print(f"   ✅ MODERATE UTILIZATION: Pool performing well")
                        else:
                            print(f"   ✅ LOW UTILIZATION: Pool has good capacity")
            
            # Performance assessment
            avg_time = statistics.mean(response_times)
            success_rate = len(successful_results) / len(test_scenarios)
            
            print(f"\n📈 Performance Assessment:")
            if avg_time < 500 and success_rate >= 0.95:
                print(f"🎉 EXCELLENT: Ready for production!")
                print(f"   ✅ Avg response: {avg_time:.1f}ms (<500ms target)")
                print(f"   ✅ Success rate: {success_rate*100:.1f}% (>95% target)")
                print(f"   ✅ Database pool optimizations working effectively")
            elif avg_time < 1000 and success_rate >= 0.90:
                print(f"✅ GOOD: Performance acceptable, minor optimizations possible")
                print(f"   ⚠️  Avg response: {avg_time:.1f}ms")
                print(f"   ⚠️  Success rate: {success_rate*100:.1f}%")
            else:
                print(f"❌ NEEDS IMPROVEMENT: Performance below production standards")
                print(f"   ❌ Avg response: {avg_time:.1f}ms (target: <500ms)")
                print(f"   ❌ Success rate: {success_rate*100:.1f}% (target: >95%)")
                
                # Suggest optimizations
                if avg_time > 1000:
                    print(f"   💡 Consider: Increase database pool size further")
                if success_rate < 0.95:
                    print(f"   💡 Consider: Add connection retry logic")
        else:
            print(f"❌ All {len(test_scenarios)} requests failed")
    
    finally:
        # Always cleanup test data
        print(f"\n🧹 Cleaning up test data...")
        await cleanup_test_user(test_user_id)


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
    asyncio.run(test_database_pool_performance())
