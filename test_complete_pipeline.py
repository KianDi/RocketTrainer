#!/usr/bin/env python3
"""
Test the complete data extraction pipeline with real Ballchasing.com data.
"""

import requests
import json
import time
import sys
import os

def test_complete_pipeline():
    """Test the complete data extraction pipeline."""
    print("🚀 Testing Complete Data Extraction Pipeline")
    print("=" * 60)
    
    # Step 1: Get authentication token
    print("🔐 Step 1: Getting authentication token...")
    auth_response = requests.post(
        "http://localhost:8000/auth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"username": "testuser", "password": "testpass123"}
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        print(f"Response: {auth_response.text}")
        return
    
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # Step 2: Create a new match with a known replay ID
    print("\n📝 Step 2: Creating new match for testing...")
    test_replay_id = "fa250f0d-449f-42d9-ae9b-6c6cf58f21dc"  # Known working replay
    
    match_data = {
        "ballchasing_id": test_replay_id,
        "replay_filename": f"test_replay_{int(time.time())}.replay"
    }
    
    create_response = requests.post(
        "http://localhost:8000/replays/",
        headers=headers,
        json=match_data
    )
    
    if create_response.status_code != 201:
        print(f"❌ Match creation failed: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return
    
    match_info = create_response.json()
    match_id = match_info["id"]
    print(f"✅ Match created successfully: {match_id}")
    
    # Step 3: Wait for background processing
    print(f"\n⏳ Step 3: Waiting for background processing...")
    max_wait = 30  # seconds
    wait_time = 0
    
    while wait_time < max_wait:
        # Check match status
        status_response = requests.get(
            f"http://localhost:8000/replays/{match_id}",
            headers=headers
        )
        
        if status_response.status_code == 200:
            match_data = status_response.json()
            if match_data.get("processed"):
                print(f"✅ Processing completed after {wait_time} seconds")
                break
        
        time.sleep(2)
        wait_time += 2
        print(f"   Waiting... ({wait_time}s)")
    
    if wait_time >= max_wait:
        print(f"⚠️  Processing timeout after {max_wait} seconds")
    
    # Step 4: Check the results
    print(f"\n📊 Step 4: Checking extraction results...")
    
    final_response = requests.get(
        f"http://localhost:8000/replays/{match_id}",
        headers=headers
    )
    
    if final_response.status_code != 200:
        print(f"❌ Failed to get match data: {final_response.status_code}")
        return
    
    match_result = final_response.json()
    
    print(f"📋 Match Results:")
    print(f"   Processed: {match_result.get('processed', False)}")
    print(f"   Playlist: {match_result.get('playlist', 'unknown')}")
    print(f"   Duration: {match_result.get('duration', 0)} seconds")
    print(f"   Match Date: {match_result.get('match_date', 'unknown')}")
    print(f"   Score Team 0: {match_result.get('score_team_0', 0)}")
    print(f"   Score Team 1: {match_result.get('score_team_1', 0)}")
    print(f"   Result: {match_result.get('result', 'unknown')}")
    
    print(f"\n🎯 Player Statistics:")
    print(f"   Goals: {match_result.get('goals', 0)}")
    print(f"   Assists: {match_result.get('assists', 0)}")
    print(f"   Saves: {match_result.get('saves', 0)}")
    print(f"   Shots: {match_result.get('shots', 0)}")
    print(f"   Score: {match_result.get('score', 0)}")
    print(f"   Boost Usage: {match_result.get('boost_usage', 0.0)}")
    print(f"   Average Speed: {match_result.get('average_speed', 0.0)}")
    
    # Step 5: Verify success criteria
    print(f"\n✅ Success Criteria Check:")
    
    success_checks = [
        ("Processed", match_result.get('processed', False)),
        ("Non-zero goals", match_result.get('goals', 0) > 0),
        ("Non-zero score", match_result.get('score', 0) > 0),
        ("Valid playlist", match_result.get('playlist', 'unknown') != 'unknown'),
        ("Valid duration", match_result.get('duration', 0) > 0),
        ("Valid match date", match_result.get('match_date') is not None),
    ]
    
    all_passed = True
    for check_name, passed in success_checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}: {passed}")
        if not passed:
            all_passed = False
    
    print(f"\n🎉 Overall Result: {'SUCCESS' if all_passed else 'PARTIAL SUCCESS'}")
    
    if all_passed:
        print("🎯 All data extraction issues have been resolved!")
        print("   - Real player statistics are being extracted")
        print("   - Database fields are being populated correctly")
        print("   - Background processing is working")
    else:
        print("⚠️  Some issues remain - check the failed criteria above")
    
    return match_result

if __name__ == "__main__":
    test_complete_pipeline()
