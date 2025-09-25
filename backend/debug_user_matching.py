#!/usr/bin/env python3
"""
Debug script to investigate user matching issues in Ballchasing.com API integration.
"""

import requests
import json
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ballchasing_service import ballchasing_service

async def debug_user_matching():
    """Debug the user matching logic with real Ballchasing.com data."""
    print("🔍 Debugging User Matching Issues")
    print("=" * 50)
    
    # Test with a known replay ID from the database
    test_replay_id = "fa250f0d-449f-42d9-ae9b-6c6cf58f21dc"  # From recent database entries
    test_user_steam_id = "76561197960287930"  # TestPlayer from database
    
    print(f"🎯 Testing with:")
    print(f"   Replay ID: {test_replay_id}")
    print(f"   User Steam ID: {test_user_steam_id}")
    
    try:
        # Step 1: Get raw replay data
        print(f"\n📡 Step 1: Fetching raw replay data...")
        raw_replay = await ballchasing_service.get_replay(test_replay_id)
        
        if not raw_replay:
            print("❌ Failed to fetch raw replay data")
            return
        
        print(f"✅ Raw replay data fetched successfully")
        print(f"   Keys in response: {list(raw_replay.keys())}")
        
        # Step 2: Check if there are players in the data
        if "blue" in raw_replay and "orange" in raw_replay:
            print(f"\n👥 Step 2: Analyzing player data structure...")
            
            for team_color in ["blue", "orange"]:
                team_data = raw_replay[team_color]
                if "players" in team_data:
                    players = team_data["players"]
                    print(f"\n🔵 {team_color.upper()} team has {len(players)} players:")
                    
                    for i, player in enumerate(players):
                        print(f"   Player {i+1}:")
                        print(f"     Name: {player.get('name', 'Unknown')}")
                        print(f"     ID structure: {player.get('id', {})}")
                        
                        # Check different possible ID fields
                        player_id_obj = player.get('id', {})
                        if isinstance(player_id_obj, dict):
                            print(f"     ID fields: {list(player_id_obj.keys())}")
                            for key, value in player_id_obj.items():
                                print(f"       {key}: {value}")
                        else:
                            print(f"     ID (direct): {player_id_obj}")
        
        # Step 3: Test the get_replay_stats method
        print(f"\n📊 Step 3: Testing get_replay_stats method...")
        replay_stats = await ballchasing_service.get_replay_stats(test_replay_id)
        
        if not replay_stats:
            print("❌ Failed to get replay stats")
            return
        
        print(f"✅ Replay stats processed successfully")
        print(f"   Keys in replay_stats: {list(replay_stats.keys())}")

        # Check match_info structure
        if "match_info" in replay_stats:
            match_info = replay_stats["match_info"]
            print(f"\n📋 Match Info Structure:")
            print(f"   Keys: {list(match_info.keys())}")
            print(f"   Playlist: {match_info.get('playlist', 'NOT_FOUND')}")
            print(f"   Duration: {match_info.get('duration', 'NOT_FOUND')}")
            print(f"   Date: {match_info.get('date', 'NOT_FOUND')}")
            print(f"   Score: {match_info.get('score', 'NOT_FOUND')}")

        if "players" in replay_stats:
            print(f"   Number of players: {len(replay_stats['players'])}")

            print(f"\n🔍 Player IDs in processed stats:")
            for i, player in enumerate(replay_stats["players"]):
                print(f"   Player {i+1}: {player.get('player_name', 'Unknown')}")
                print(f"     player_id: '{player.get('player_id', 'NOT_FOUND')}'")
                print(f"     team: {player.get('team', 'unknown')}")
                print(f"     goals: {player.get('goals', 0)}")
                print(f"     saves: {player.get('saves', 0)}")
                print(f"     score: {player.get('score', 0)}")
        
        # Step 4: Test user matching
        print(f"\n🎯 Step 4: Testing user matching...")
        user_stats = ballchasing_service.extract_player_stats_for_user(replay_stats, test_user_steam_id)
        
        if user_stats:
            print(f"✅ User found in replay!")
            print(f"   Goals: {user_stats.get('goals', 0)}")
            print(f"   Saves: {user_stats.get('saves', 0)}")
            print(f"   Score: {user_stats.get('score', 0)}")
        else:
            print(f"❌ User NOT found in replay")
            print(f"   Looking for Steam ID: '{test_user_steam_id}'")
            print(f"   Available player IDs:")
            if "players" in replay_stats:
                for player in replay_stats["players"]:
                    print(f"     - '{player.get('player_id', 'NOT_FOUND')}'")
        
        # Step 5: Try different Steam ID formats
        print(f"\n🔄 Step 5: Testing different Steam ID formats...")
        
        # Common Steam ID conversions
        steam_id_64 = test_user_steam_id
        
        # Try converting to Steam ID 3 format (if needed)
        try:
            steam_id_int = int(steam_id_64)
            steam_id_3 = steam_id_int - 76561197960265728  # Convert SteamID64 to SteamID3
            
            print(f"   Testing formats:")
            print(f"     SteamID64: '{steam_id_64}'")
            print(f"     SteamID3: '{steam_id_3}'")
            
            # Test both formats
            for format_name, steam_id in [("SteamID64", steam_id_64), ("SteamID3", str(steam_id_3))]:
                user_stats = ballchasing_service.extract_player_stats_for_user(replay_stats, steam_id)
                if user_stats:
                    print(f"   ✅ Match found with {format_name}: {steam_id}")
                    break
                else:
                    print(f"   ❌ No match with {format_name}: {steam_id}")
        
        except ValueError:
            print(f"   ⚠️  Could not convert Steam ID to integer: {steam_id_64}")
        
    except Exception as e:
        print(f"❌ Error during debugging: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_user_matching())
