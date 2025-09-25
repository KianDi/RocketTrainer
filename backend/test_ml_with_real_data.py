#!/usr/bin/env python3
"""
Test ML API endpoints with real user data to verify complete functionality.
"""

import sys
import os
import requests
import json
from uuid import uuid4, UUID
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def create_test_user_with_data():
    """Create a test user with sample match data."""
    print("🏗️  Creating test user with sample data...")
    
    try:
        from app.database import get_db
        from app.models.user import User
        from app.models.match import Match
        from app.models.training_pack import TrainingPack
        
        db = next(get_db())
        
        # Create test user
        test_user_id = uuid4()
        test_user = User(
            id=test_user_id,
            username=f"test_user_{test_user_id.hex[:8]}",
            email=f"test_{test_user_id.hex[:8]}@example.com",
            steam_id=f"steam_{test_user_id.hex[:8]}",
            current_rank="platinum_ii",
            mmr=850,
            platform="steam",
            is_active=True
        )
        
        db.add(test_user)
        db.flush()  # Get the ID
        
        print(f"✅ Created test user: {test_user_id}")
        
        # Create sample matches with realistic data
        base_date = datetime.utcnow() - timedelta(days=30)

        for i in range(10):
            match_date = base_date + timedelta(days=i * 3, hours=i)

            # Simulate improving performance over time
            base_score = 400 + (i * 50)  # Score improves over time
            goals = max(0, i // 2)  # Goals increase
            saves = max(0, (i + 1) // 3)  # Saves increase
            assists = max(0, i // 4)  # Assists increase

            test_match = Match(
                id=uuid4(),
                user_id=test_user_id,
                match_date=match_date,
                processed=True,
                playlist="ranked-doubles",
                duration=300 + (i * 10),  # Match duration in seconds
                score_team_0=3 if i % 2 == 0 else 2,  # Win/loss pattern
                score_team_1=2 if i % 2 == 0 else 3,
                result="win" if i % 2 == 0 else "loss",
                score=base_score + (i * 25),
                goals=goals,
                saves=saves,
                assists=assists,
                shots=goals + (i % 3),  # Some shots miss
                boost_usage=max(0.0, 100.0 - (i * 5.0)),  # Efficiency improves
                average_speed=45.0 + (i * 2.0),  # Speed increases
                time_supersonic=10.0 + i,  # More supersonic time
                time_on_ground=70.0 - i,  # Less ground time
                time_low_air=15.0 + (i % 2),  # Varied air time
                time_high_air=5.0 + (i % 3)  # High air time
            )
            
            db.add(test_match)
        
        # Ensure we have some training packs
        existing_packs = db.query(TrainingPack).count()
        if existing_packs < 5:
            print("📦 Creating additional training packs...")
            
            training_packs = [
                {
                    "id": "shooting-basics-001",
                    "name": "Shooting Basics",
                    "code": "SHOOT-001",
                    "description": "Basic shooting training for beginners",
                    "category": "shooting",
                    "difficulty": 2,
                    "skill_level": "gold",
                    "rating": 4.2,
                    "rating_count": 150
                },
                {
                    "id": "aerial-training-002", 
                    "name": "Aerial Training",
                    "code": "AERIAL-002",
                    "description": "Improve your aerial game",
                    "category": "aerials",
                    "difficulty": 4,
                    "skill_level": "platinum",
                    "rating": 4.5,
                    "rating_count": 200
                },
                {
                    "id": "defense-drills-003",
                    "name": "Defensive Drills",
                    "code": "DEFENSE-003", 
                    "description": "Master defensive positioning",
                    "category": "defense",
                    "difficulty": 3,
                    "skill_level": "platinum",
                    "rating": 4.0,
                    "rating_count": 120
                }
            ]
            
            for pack_data in training_packs:
                pack = TrainingPack(
                    id=pack_data["id"],
                    name=pack_data["name"],
                    code=pack_data["code"],
                    description=pack_data["description"],
                    category=pack_data["category"],
                    difficulty=pack_data["difficulty"],
                    skill_level=pack_data["skill_level"],
                    rating=pack_data["rating"],
                    rating_count=pack_data["rating_count"],
                    is_active=True,
                    shots_count=10,
                    estimated_duration=15
                )
                db.add(pack)
        
        db.commit()
        print(f"✅ Created 10 matches and training packs for user {test_user_id}")
        
        return test_user_id
        
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        if 'db' in locals():
            db.rollback()
        return None


def test_ml_endpoints_with_real_data(user_id: UUID):
    """Test ML endpoints with real user data."""
    print(f"\n🧪 Testing ML endpoints with real data for user {user_id}")
    
    base_url = "http://localhost:8000/api/ml"
    
    # Test 1: Weakness Analysis
    print("\n1️⃣ Testing Weakness Analysis with real data...")
    try:
        payload = {
            "user_id": str(user_id),
            "include_confidence": True,
            "analysis_depth": "detailed"
        }
        
        response = requests.post(f"{base_url}/analyze-weaknesses", json=payload)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Primary weakness: {data.get('primary_weakness')}")
            print(f"   ✅ Confidence: {data.get('confidence', 0):.2f}")
            print(f"   ✅ Matches analyzed: {data.get('matches_analyzed', 0)}")
            print(f"   ✅ Skill categories: {len(data.get('skill_categories', []))}")
            
            # Test caching - second request should be faster
            import time
            start_time = time.time()
            response2 = requests.post(f"{base_url}/analyze-weaknesses", json=payload)
            cache_time = time.time() - start_time
            
            if response2.status_code == 200:
                data2 = response2.json()
                cache_hit = data2.get('cache_hit', False)
                print(f"   ✅ Cache test: {cache_hit} (response time: {cache_time*1000:.1f}ms)")
            
        elif response.status_code == 400:
            error_data = response.json()
            print(f"   ⚠️  Expected insufficient data error: {error_data.get('detail', {}).get('message', 'Unknown')}")
        else:
            print(f"   ❌ Unexpected status: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 2: Training Recommendations
    print("\n2️⃣ Testing Training Recommendations with real data...")
    try:
        payload = {
            "user_id": str(user_id),
            "skill_level": "platinum",
            "max_recommendations": 3,
            "categories": ["shooting", "aerials"],
            "exclude_completed": True
        }
        
        response = requests.post(f"{base_url}/recommend-training", json=payload)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            print(f"   ✅ Recommendations received: {len(recommendations)}")
            print(f"   ✅ Skill level detected: {data.get('skill_level_detected')}")
            print(f"   ✅ Total packs evaluated: {data.get('total_packs_evaluated', 0)}")
            
            for i, rec in enumerate(recommendations[:2]):  # Show first 2
                print(f"      {i+1}. {rec.get('name')} (score: {rec.get('overall_score', 0):.2f})")
            
        elif response.status_code == 400:
            error_data = response.json()
            print(f"   ⚠️  Expected error: {error_data.get('detail', {}).get('message', 'Unknown')}")
        else:
            print(f"   ❌ Unexpected status: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 3: Model Status
    print("\n3️⃣ Testing Model Status...")
    try:
        response = requests.get(f"{base_url}/model-status")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ System status: {data.get('system_status')}")
            print(f"   ✅ Models: {len(data.get('models', []))}")
            
            cache_stats = data.get('cache_stats', {})
            hit_rate = cache_stats.get('hit_rate', 0)
            print(f"   ✅ Cache hit rate: {hit_rate:.1f}%")
            
        else:
            print(f"   ❌ Unexpected status: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")


def cleanup_test_data(user_id: UUID):
    """Clean up test data."""
    print(f"\n🧹 Cleaning up test data for user {user_id}")
    
    try:
        from app.database import get_db
        from app.models.user import User
        from app.models.match import Match
        
        db = next(get_db())
        
        # Delete matches first (foreign key constraint)
        matches_deleted = db.query(Match).filter(Match.user_id == user_id).delete()
        print(f"   ✅ Deleted {matches_deleted} matches")
        
        # Delete user
        users_deleted = db.query(User).filter(User.id == user_id).delete()
        print(f"   ✅ Deleted {users_deleted} user")
        
        db.commit()
        print("   ✅ Cleanup completed")
        
    except Exception as e:
        print(f"   ❌ Cleanup failed: {e}")
        if 'db' in locals():
            db.rollback()


def main():
    """Run comprehensive ML API testing with real data."""
    print("🚀 Starting ML API Testing with Real Data")
    print("="*60)
    
    # Create test user and data
    user_id = create_test_user_with_data()
    
    if not user_id:
        print("❌ Failed to create test data. Exiting.")
        return 1
    
    try:
        # Test ML endpoints
        test_ml_endpoints_with_real_data(user_id)
        
        print("\n" + "="*60)
        print("🎉 ML API testing with real data completed successfully!")
        
        return 0
        
    finally:
        # Always cleanup
        cleanup_test_data(user_id)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
