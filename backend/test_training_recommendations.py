#!/usr/bin/env python3
"""
Test script for Training Recommendation Engine.

Tests the complete training recommendation pipeline:
1. Training pack database seeding
2. ML-powered weakness detection
3. Personalized training recommendations
4. Training service integration
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.match import Match
from app.models.training_pack import TrainingPack
from app.models.user import User
from app.ml.models.recommendation_engine import TrainingRecommendationEngine
from app.ml.models.weakness_detector import WeaknessDetector
from app.services.training_service import TrainingService
from scripts.seed_data import create_training_packs
import structlog
import uuid

logger = structlog.get_logger()


def create_test_user(db: Session) -> User:
    """Create or get existing test user for recommendations."""
    # Try to find existing test user
    existing_user = db.query(User).filter(User.steam_id == "76561198000000001").first()
    if existing_user:
        print(f"   Using existing test user: {existing_user.username}")
        return existing_user

    # Create new test user
    test_user = User(
        id=uuid.uuid4(),
        steam_id="76561198000000001",
        username="TestPlayer",
        email="test@example.com",
        current_rank="platinum",
        platform="steam"
    )
    db.add(test_user)
    db.commit()
    print(f"   Created new test user: {test_user.username}")
    return test_user


def create_enhanced_mock_matches(db: Session, user_id: str, count: int = 8) -> list[Match]:
    """Create or get existing enhanced mock matches with varied performance patterns for testing."""
    # Check if matches already exist for this user
    existing_matches = (db.query(Match)
                       .filter(Match.user_id == user_id)
                       .filter(Match.processed == True)
                       .limit(count)
                       .all())

    if len(existing_matches) >= count:
        print(f"   Using {len(existing_matches)} existing matches")
        return existing_matches

    # Create new matches with unique IDs
    matches = []
    timestamp = int(datetime.now().timestamp())

    # Performance patterns for different weaknesses
    patterns = [
        # Poor shooting accuracy
        {"goals": 0, "shots": 8, "saves": 3, "assists": 1, "score": 180, "boost_usage": 0.6},
        {"goals": 1, "shots": 12, "saves": 2, "assists": 0, "score": 220, "boost_usage": 0.7},

        # Poor defending
        {"goals": 2, "shots": 6, "saves": 1, "assists": 1, "score": 280, "boost_usage": 0.5},
        {"goals": 1, "shots": 4, "saves": 0, "assists": 2, "score": 240, "boost_usage": 0.6},

        # Good mechanical skills
        {"goals": 3, "shots": 7, "saves": 4, "assists": 2, "score": 450, "boost_usage": 0.4},
        {"goals": 2, "shots": 5, "saves": 3, "assists": 1, "score": 380, "boost_usage": 0.5},

        # Mixed performance
        {"goals": 1, "shots": 6, "saves": 2, "assists": 1, "score": 320, "boost_usage": 0.6},
        {"goals": 2, "shots": 8, "saves": 1, "assists": 0, "score": 290, "boost_usage": 0.7}
    ]

    for i in range(min(count, len(patterns))):
        pattern = patterns[i]
        match = Match(
            id=uuid.uuid4(),
            user_id=user_id,
            ballchasing_id=f"test-match-{timestamp}-{i+1}",  # Unique ID with timestamp
            replay_filename=f"test_match_{timestamp}_{i+1}.replay",
            playlist="ranked-duels",
            duration=300,  # 5 minutes
            match_date=datetime.now(timezone.utc),
            score_team_0=pattern["goals"] + 1,
            score_team_1=2,
            result="win" if pattern["goals"] > 1 else "loss",
            goals=pattern["goals"],
            assists=pattern["assists"],
            saves=pattern["saves"],
            shots=pattern["shots"],
            score=pattern["score"],
            boost_usage=pattern["boost_usage"],
            average_speed=1200.0,
            time_supersonic=45.0,
            time_on_ground=200.0,
            time_low_air=40.0,
            time_high_air=15.0,
            processed=True,
            created_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc)
        )
        matches.append(match)
        db.add(match)

    db.commit()
    print(f"   Created {len(matches)} new matches")
    return matches


def test_training_pack_seeding(db: Session):
    """Test training pack database seeding."""
    print("🌱 Testing training pack seeding...")
    
    # Check if training packs exist
    existing_packs = db.query(TrainingPack).count()
    print(f"   Existing training packs: {existing_packs}")
    
    if existing_packs == 0:
        print("   Seeding training packs...")
        create_training_packs(db)
        
    total_packs = db.query(TrainingPack).count()
    print(f"✅ Training packs available: {total_packs}")
    
    # Show pack categories
    categories = db.query(TrainingPack.category).distinct().all()
    category_names = [cat[0] for cat in categories]
    print(f"   Categories: {category_names}")
    
    return total_packs > 0


def test_recommendation_engine(db: Session, user_id: str, matches: list[Match]):
    """Test the training recommendation engine."""
    print("\n🤖 Testing Training Recommendation Engine...")
    
    try:
        # Initialize recommendation engine
        engine = TrainingRecommendationEngine(db)
        print("✅ Recommendation engine initialized")
        
        # Initialize and train weakness detector
        weakness_detector = WeaknessDetector()
        weakness_detector.train(matches)
        print("✅ Weakness detector trained")
        
        # Detect weaknesses
        weaknesses = weakness_detector.predict(matches[:5])
        print(f"✅ Weaknesses detected: {len(weaknesses)}")

        # Debug: print the actual structure
        print(f"   Weakness structure: {weaknesses[0] if weaknesses else 'None'}")

        for i, weakness in enumerate(weaknesses):
            if isinstance(weakness, dict):
                category = weakness.get('category', weakness.get('weakness_category', 'unknown'))
                confidence = weakness.get('confidence', weakness.get('prediction_confidence', 0))
                print(f"   • {category}: {confidence:.1%} confidence")
            else:
                print(f"   • Weakness {i+1}: {weakness}")
        
        # Generate recommendations
        recommendations = engine.recommend_training_packs(
            user_id=user_id,
            weaknesses=weaknesses,
            player_skill_level="platinum",
            max_recommendations=5,
            include_variety=True
        )
        
        print(f"✅ Generated {len(recommendations)} recommendations")
        
        # Display recommendations
        for i, rec in enumerate(recommendations, 1):
            pack = rec["pack"]
            print(f"\n   Recommendation {i}:")
            print(f"     • Pack: {pack.name} ({pack.code})")
            print(f"     • Category: {pack.category}")
            print(f"     • Difficulty: {pack.difficulty}/10 ({pack.skill_level})")
            print(f"     • Score: {rec['total_score']:.3f}")
            print(f"     • Reasoning: {'; '.join(rec['reasoning'])}")
            print(f"     • Score breakdown:")
            print(f"       - Weakness relevance: {rec['weakness_score']:.3f}")
            print(f"       - Difficulty match: {rec['difficulty_score']:.3f}")
            print(f"       - Pack quality: {rec['quality_score']:.3f}")
            print(f"       - User preference: {rec['preference_score']:.3f}")
        
        return len(recommendations) > 0
        
    except Exception as e:
        print(f"❌ Recommendation engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_training_service_integration(db: Session, user_id: str):
    """Test the complete training service integration."""
    print("\n🔧 Testing Training Service Integration...")

    try:
        # Initialize training service
        training_service = TrainingService(db)
        print("✅ Training service initialized")

        # Get personalized recommendations
        recommendations = await training_service.get_recommendations(user_id)
        print(f"✅ Service recommendations: {len(recommendations)}")

        # Display service recommendations
        for i, rec in enumerate(recommendations, 1):
            pack = rec.training_pack
            print(f"\n   Service Recommendation {i}:")
            print(f"     • Pack: {pack.name} ({pack.code})")
            print(f"     • Category: {pack.category}")
            print(f"     • Reason: {rec.reason}")
            print(f"     • Confidence: {rec.confidence:.3f}")
            print(f"     • Priority: {rec.priority}")
            print(f"     • Weakness addressed: {rec.weakness_addressed}")
            print(f"     • Expected improvement: {rec.expected_improvement:.1%}")

        # Test user progress
        progress = await training_service.get_user_progress(user_id)
        print(f"\n✅ User progress analysis:")
        print(f"   • Total sessions: {progress.get('total_sessions', 0)}")
        print(f"   • Average accuracy: {progress.get('average_accuracy', 0):.1%}")
        print(f"   • Improvement rate: {progress.get('improvement_rate', 0):.1f}%")

        return len(recommendations) > 0

    except Exception as e:
        print(f"❌ Training service integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_recommendation_quality(db: Session, user_id: str, matches: list[Match]):
    """Test the quality and relevance of recommendations."""
    print("\n📊 Testing Recommendation Quality...")
    
    try:
        engine = TrainingRecommendationEngine(db)
        weakness_detector = WeaknessDetector()
        weakness_detector.train(matches)
        
        # Test different skill levels
        skill_levels = ["silver", "gold", "platinum", "diamond", "champion"]
        
        for skill_level in skill_levels:
            print(f"\n   Testing for {skill_level} skill level:")
            
            weaknesses = weakness_detector.predict(matches[:3])
            recommendations = engine.recommend_training_packs(
                user_id=user_id,
                weaknesses=weaknesses,
                player_skill_level=skill_level,
                max_recommendations=3,
                include_variety=True
            )
            
            if recommendations:
                avg_difficulty = sum(rec["pack"].difficulty for rec in recommendations) / len(recommendations)
                categories = set(rec["pack"].category for rec in recommendations)
                
                print(f"     • Recommendations: {len(recommendations)}")
                print(f"     • Average difficulty: {avg_difficulty:.1f}/10")
                print(f"     • Categories: {', '.join(categories)}")
                print(f"     • Average score: {sum(rec['total_score'] for rec in recommendations) / len(recommendations):.3f}")
            else:
                print(f"     • No recommendations generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Recommendation quality test failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🧪 Testing Training Recommendation Engine...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Test 1: Training pack seeding
        if not test_training_pack_seeding(db):
            print("❌ Training pack seeding failed")
            return
        
        # Test 2: Create test user and matches
        print("\n👤 Creating test user and matches...")
        test_user = create_test_user(db)
        matches = create_enhanced_mock_matches(db, str(test_user.id), count=8)
        print(f"✅ Created test user and {len(matches)} matches")
        
        # Test 3: Recommendation engine
        if not test_recommendation_engine(db, str(test_user.id), matches):
            print("❌ Recommendation engine test failed")
            return
        
        # Test 4: Training service integration
        if not await test_training_service_integration(db, str(test_user.id)):
            print("❌ Training service integration test failed")
            return
        
        # Test 5: Recommendation quality
        if not test_recommendation_quality(db, str(test_user.id), matches):
            print("❌ Recommendation quality test failed")
            return
        
        print("\n🎉 Training Recommendation Engine Test Complete!")
        print("✅ All components working correctly")
        print("✅ Ready for API integration")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
