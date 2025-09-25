#!/usr/bin/env python3
"""
Test script to run inside the API container.
"""
import asyncio
import os
import sys

# Add the app directory to the path
sys.path.append('/app')

from app.services.ballchasing_service import ballchasing_service

async def test_data_extraction():
    """Test data extraction directly."""
    print("🔍 Testing Ballchasing Data Extraction...")
    
    replay_id = "56d44232-9cc2-4778-a5ec-f20d01039e24"
    print(f"Testing replay: {replay_id}")
    
    try:
        replay_stats = await ballchasing_service.get_replay_stats(replay_id)
        
        if replay_stats:
            print("✅ Data extraction successful!")
            
            match_info = replay_stats.get("match_info", {})
            print(f"Playlist: {match_info.get('playlist')}")
            print(f"Duration: {match_info.get('duration')} seconds")
            
            score = match_info.get('score', {})
            print(f"Score: {score.get('blue')}-{score.get('orange')}")
            
            players = replay_stats.get("players", [])
            print(f"Players: {len(players)}")
            
            for player in players[:2]:
                print(f"  {player.get('player_name')}: {player.get('score')} points")
            
            return True
        else:
            print("❌ No data returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_data_extraction())
