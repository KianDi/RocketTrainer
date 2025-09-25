#!/usr/bin/env python3
"""
Debug script to test database persistence in background tasks.
This will trigger a replay import and monitor the detailed logging.
"""

import requests
import json
import time
import sys

def debug_database_persistence():
    """Debug the database persistence issue with detailed monitoring."""
    print("🔧 RocketTrainer Database Persistence Debugging")
    print("=" * 60)
    
    # Step 1: Authentication
    print("🔐 Step 1: Authenticating...")
    
    login_data = {
        "steam_id": "76561197960287930",
        "username": "debug_user"
    }
    
    auth_response = requests.post(
        "http://localhost:8000/auth/steam-login",
        headers={"Content-Type": "application/json"},
        json=login_data
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        print(f"Response: {auth_response.text}")
        return False
    
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # Step 2: Check current database state
    print(f"\n📊 Step 2: Checking current database state...")
    
    # Step 3: Import a new replay with unique ID
    print(f"\n📝 Step 3: Importing replay for debugging...")
    
    # Use a known working replay ID
    test_replay_id = "fa250f0d-449f-42d9-ae9b-6c6cf58f21dc"
    
    # First, try to delete any existing match with this ID to ensure clean test
    print(f"   Using replay ID: {test_replay_id}")
    
    match_data = {
        "ballchasing_id": test_replay_id,
        "replay_filename": f"debug_replay_{int(time.time())}.replay"
    }
    
    create_response = requests.post(
        "http://localhost:8000/replays/ballchasing-import",
        headers=headers,
        json=match_data
    )
    
    if create_response.status_code == 400 and "already imported" in create_response.text:
        print("   ⚠️  Replay already exists - this is expected for debugging")
        print("   We'll check the existing match data instead")
        
        # Get existing matches to find the match ID
        matches_response = requests.get("http://localhost:8000/replays/", headers=headers)
        if matches_response.status_code == 200:
            matches = matches_response.json()
            existing_match = None
            for match in matches:
                if match.get("ballchasing_id") == test_replay_id:
                    existing_match = match
                    break
            
            if existing_match:
                match_id = existing_match["id"]
                print(f"   Found existing match ID: {match_id}")
            else:
                print("   ❌ Could not find existing match")
                return False
        else:
            print("   ❌ Could not retrieve matches")
            return False
            
    elif create_response.status_code == 201:
        match_info = create_response.json()
        match_id = match_info["id"]
        print(f"✅ New match created successfully")
        print(f"   Match ID: {match_id}")
    else:
        print(f"❌ Match creation failed: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return False
    
    # Step 4: Monitor background processing with detailed checks
    print(f"\n⏳ Step 4: Monitoring background processing...")
    print("   Checking every 2 seconds for up to 30 seconds...")
    
    max_wait = 30
    wait_time = 0
    
    while wait_time < max_wait:
        # Check processing status
        status_response = requests.get(
            f"http://localhost:8000/replays/{match_id}",
            headers=headers
        )
        
        if status_response.status_code == 200:
            match_data = status_response.json()
            
            print(f"\n   📊 Status at {wait_time}s:")
            print(f"      Processed: {match_data.get('processed', False)}")
            print(f"      Playlist: '{match_data.get('playlist', 'unknown')}'")
            print(f"      Duration: {match_data.get('duration', 0)} seconds")
            print(f"      Goals: {match_data.get('goals', 0)}")
            print(f"      Assists: {match_data.get('assists', 0)}")
            print(f"      Saves: {match_data.get('saves', 0)}")
            print(f"      Score: {match_data.get('score', 0)}")
            
            # Check if we have real data (non-default values)
            score_value = match_data.get('score', 0)
            score_numeric = score_value if isinstance(score_value, (int, float)) else 0

            has_real_data = (
                match_data.get('playlist', 'unknown') != 'unknown' or
                match_data.get('duration', 0) > 0 or
                match_data.get('goals', 0) > 0 or
                score_numeric > 0
            )
            
            if match_data.get('processed') and has_real_data:
                print(f"   ✅ Processing completed with real data!")
                break
            elif match_data.get('processed') and not has_real_data:
                print(f"   ⚠️  Processing marked complete but data still shows defaults")
                print(f"   This indicates the database persistence issue!")
                break
        
        time.sleep(2)
        wait_time += 2
        print(f"   Processing... ({wait_time}s)")
    
    # Step 5: Final analysis
    print(f"\n🔍 Step 5: Final analysis...")
    
    final_response = requests.get(f"http://localhost:8000/replays/{match_id}", headers=headers)
    if final_response.status_code == 200:
        final_data = final_response.json()
        
        print(f"\n📋 FINAL MATCH DATA:")
        print(f"   Match ID: {match_id}")
        print(f"   Ballchasing ID: {final_data.get('ballchasing_id', 'unknown')}")
        print(f"   Processed: {final_data.get('processed', False)}")
        print(f"   Playlist: '{final_data.get('playlist', 'unknown')}'")
        print(f"   Duration: {final_data.get('duration', 0)} seconds")
        print(f"   Goals: {final_data.get('goals', 0)}")
        print(f"   Assists: {final_data.get('assists', 0)}")
        print(f"   Saves: {final_data.get('saves', 0)}")
        print(f"   Shots: {final_data.get('shots', 0)}")
        print(f"   Score: {final_data.get('score', 0)}")
        
        # Diagnosis
        print(f"\n🩺 DIAGNOSIS:")
        if final_data.get('processed'):
            if (final_data.get('playlist', 'unknown') != 'unknown' and 
                final_data.get('duration', 0) > 0):
                print("   ✅ SUCCESS: Data extraction and persistence working correctly!")
                return True
            else:
                print("   ❌ ISSUE CONFIRMED: Background task completes but data not persisted")
                print("   📝 Next steps:")
                print("      1. Check API logs for detailed database operation logs")
                print("      2. Look for transaction commit issues")
                print("      3. Verify session management in background tasks")
                return False
        else:
            print("   ⚠️  Background task not completed yet or failed")
            return False
    else:
        print(f"   ❌ Could not retrieve final match data: {final_response.status_code}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database persistence debugging...")
    print("📋 This script will:")
    print("   1. Import a replay (or use existing one)")
    print("   2. Monitor background processing")
    print("   3. Check if extracted data persists to database")
    print("   4. Provide diagnosis of any issues found")
    print()
    
    success = debug_database_persistence()
    
    if not success:
        print(f"\n🔧 DEBUGGING TIPS:")
        print("   1. Check API container logs: docker logs rockettrainer-api-1")
        print("   2. Look for detailed database operation logs we just added")
        print("   3. Check for any transaction rollback messages")
        print("   4. Verify the match_updates data is being passed correctly")
    
    sys.exit(0 if success else 1)
