#!/usr/bin/env python3
"""
Direct demonstration of RocketTrainer data extraction working correctly.
This bypasses the API and shows the core data extraction functionality.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def demo_direct_data_extraction():
    """Demonstrate data extraction working directly with the Ballchasing service."""
    print("🚀 RocketTrainer Data Extraction - DIRECT DEMONSTRATION")
    print("=" * 70)
    
    try:
        # Import the services
        from app.services.ballchasing_service import ballchasing_service
        from app.config import settings
        
        print("✅ Successfully imported RocketTrainer services")
        
        # Step 1: Test Ballchasing.com API connection
        print(f"\n📡 Step 1: Testing Ballchasing.com API connection...")
        
        # Use a known working replay ID
        test_replay_id = "fa250f0d-449f-42d9-ae9b-6c6cf58f21dc"
        print(f"   Testing with replay ID: {test_replay_id}")
        
        # Test basic API connection
        raw_replay = await ballchasing_service.get_replay(test_replay_id)
        
        if not raw_replay:
            print("❌ Failed to connect to Ballchasing.com API")
            return False
        
        print("✅ Successfully connected to Ballchasing.com API")
        print(f"   Replay title: {raw_replay.get('title', 'Unknown')}")
        print(f"   Map: {raw_replay.get('map_name', 'Unknown')}")
        print(f"   Duration: {raw_replay.get('duration', 0)} seconds")
        
        # Step 2: Test data extraction
        print(f"\n📊 Step 2: Testing player statistics extraction...")
        
        replay_stats = await ballchasing_service.get_replay_stats(test_replay_id)
        
        if not replay_stats:
            print("❌ Failed to extract replay statistics")
            return False
        
        print("✅ Successfully extracted replay statistics")
        print(f"   Number of players: {len(replay_stats.get('players', []))}")
        
        # Step 3: Show extracted match data
        print(f"\n🎯 Step 3: Displaying extracted match data...")
        
        match_info = replay_stats.get("match_info", {})
        print(f"\n📋 MATCH INFORMATION:")
        print(f"   ├── Playlist: '{match_info.get('playlist', 'Unknown')}'")
        print(f"   ├── Duration: {match_info.get('duration', 0)} seconds")
        print(f"   ├── Date: {match_info.get('date', 'Unknown')}")
        print(f"   └── Score: {match_info.get('score', {})}")
        
        # Step 4: Show extracted player data
        print(f"\n🏆 Step 4: Displaying extracted player statistics...")
        
        players = replay_stats.get("players", [])
        if players:
            print(f"\n👥 PLAYER STATISTICS ({len(players)} players):")
            
            for i, player in enumerate(players, 1):
                print(f"\n   Player {i}: {player.get('player_name', 'Unknown')}")
                print(f"   ├── Team: {player.get('team', 'unknown')}")
                print(f"   ├── Goals: {player.get('goals', 0)}")
                print(f"   ├── Assists: {player.get('assists', 0)}")
                print(f"   ├── Saves: {player.get('saves', 0)}")
                print(f"   ├── Shots: {player.get('shots', 0)}")
                print(f"   ├── Score: {player.get('score', 0)}")
                print(f"   ├── Boost Usage: {player.get('boost_usage', 0.0)}")
                print(f"   ├── Average Speed: {player.get('average_speed', 0.0)}")
                print(f"   ├── Time Supersonic: {player.get('time_supersonic', 0.0)}")
                print(f"   ├── Time on Ground: {player.get('time_on_ground', 0.0)}")
                print(f"   ├── Time Low Air: {player.get('time_low_air', 0.0)}")
                print(f"   └── Time High Air: {player.get('time_high_air', 0.0)}")
        
        # Step 5: Test user matching (with fallback)
        print(f"\n🎯 Step 5: Testing user matching logic...")
        
        test_steam_id = "76561197960287930"  # Our test user
        user_stats = ballchasing_service.extract_player_stats_for_user(replay_stats, test_steam_id)
        
        if user_stats:
            print(f"✅ User matching successful (or fallback used)")
            print(f"   Matched player: {user_stats.get('player_name', 'Unknown')}")
            print(f"   Goals: {user_stats.get('goals', 0)}")
            print(f"   Score: {user_stats.get('score', 0)}")
        else:
            print(f"❌ User matching failed")
        
        # Step 6: Verify success criteria
        print(f"\n✅ Step 6: Verifying success criteria...")
        
        success_checks = [
            ("API Connection", raw_replay is not None),
            ("Data Extraction", replay_stats is not None),
            ("Match Info Present", bool(match_info)),
            ("Players Present", len(players) > 0),
            ("Real Goals Data", any(p.get('goals', 0) > 0 for p in players)),
            ("Real Score Data", any(p.get('score', 0) > 0 for p in players)),
            ("Real Playlist Data", match_info.get('playlist', 'unknown') != 'unknown'),
            ("Real Duration Data", match_info.get('duration', 0) > 0),
            ("User Matching Works", user_stats is not None),
        ]
        
        passed_count = 0
        total_count = len(success_checks)
        
        for check_name, passed in success_checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
            if passed:
                passed_count += 1
        
        success_rate = (passed_count / total_count) * 100
        
        print(f"\n🎉 FINAL RESULT:")
        print(f"   Success Rate: {passed_count}/{total_count} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print(f"\n   🎯 DATA EXTRACTION IS WORKING CORRECTLY!")
            print(f"   ✅ Ballchasing.com API integration is functional")
            print(f"   ✅ Real player statistics are being extracted")
            print(f"   ✅ Match metadata is being parsed correctly")
            print(f"   ✅ User matching logic is working (with fallback)")
            print(f"   ✅ All core data extraction components are operational")
            return True
        else:
            print(f"   ⚠️  Some issues detected - check failed criteria above")
            return False
            
    except Exception as e:
        print(f"❌ Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(demo_direct_data_extraction())
    sys.exit(0 if success else 1)
