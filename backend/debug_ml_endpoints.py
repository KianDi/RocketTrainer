#!/usr/bin/env python3
"""
Debug ML API endpoints to identify specific issues.
"""

import sys
import os
import traceback
from uuid import UUID

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def debug_weakness_analysis():
    """Debug the weakness analysis endpoint logic."""
    print("🔍 Debugging Weakness Analysis Logic...")
    
    try:
        from app.database import get_db
        from app.models.user import User
        from app.models.match import Match
        from app.api.ml.model_manager import get_model_manager
        from app.api.ml.cache import MLModelCache
        
        # Test database connection
        db = next(get_db())
        print("✅ Database connection successful")
        
        # Test user query
        test_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        user = db.query(User).filter(User.id == test_user_id).first()
        print(f"👤 User query result: {user}")
        
        if not user:
            print("ℹ️  Test user doesn't exist - this is expected")
            
            # Test if we can create a test user
            try:
                test_user = User(
                    id=test_user_id,
                    username="test_user",
                    email="test@example.com",
                    steam_id="test_steam_id"
                )
                db.add(test_user)
                db.commit()
                print("✅ Created test user successfully")
                
                # Now test matches query
                matches = (db.query(Match)
                          .filter(Match.user_id == test_user_id)
                          .filter(Match.processed == True)
                          .order_by(Match.match_date.desc())
                          .limit(10)
                          .all())
                print(f"📊 Found {len(matches)} matches for test user")
                
                if len(matches) < 3:
                    print("ℹ️  Insufficient matches - this should trigger InsufficientDataError")
                    
                    # Let's create some test matches
                    from datetime import datetime
                    for i in range(3):
                        test_match = Match(
                            id=UUID(f"123e4567-e89b-12d3-a456-42661417400{i}"),
                            user_id=test_user_id,
                            match_date=datetime.utcnow(),
                            processed=True,
                            score=500 + i * 50,
                            goals=i + 1,
                            saves=i,
                            assists=i
                        )
                        db.add(test_match)
                    db.commit()
                    print("✅ Created test matches")
                
            except Exception as e:
                print(f"⚠️  Could not create test data: {e}")
                db.rollback()
        
        # Test model manager
        model_manager = get_model_manager()
        model_manager.set_db_session(db)
        print("✅ Model manager initialized")
        
        # Test cache
        cache = MLModelCache()
        print("✅ Cache manager initialized")
        
        # Test getting models
        try:
            weakness_detector = model_manager.get_weakness_detector()
            print("✅ WeaknessDetector loaded")
        except Exception as e:
            print(f"❌ WeaknessDetector failed: {e}")
            traceback.print_exc()
        
        try:
            skill_analyzer = model_manager.get_skill_analyzer()
            print("✅ SkillAnalyzer loaded")
        except Exception as e:
            print(f"❌ SkillAnalyzer failed: {e}")
            traceback.print_exc()
        
        db.close()
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        traceback.print_exc()


def debug_training_recommendations():
    """Debug the training recommendations endpoint logic."""
    print("\n🔍 Debugging Training Recommendations Logic...")
    
    try:
        from app.database import get_db
        from app.models.user import User
        from app.models.training_pack import TrainingPack
        from app.api.ml.model_manager import get_model_manager
        
        # Test database connection
        db = next(get_db())
        print("✅ Database connection successful")
        
        # Check training packs
        training_packs = db.query(TrainingPack).limit(5).all()
        print(f"🎯 Found {len(training_packs)} training packs")
        
        if len(training_packs) == 0:
            print("ℹ️  No training packs found - creating test data")
            
            # Create test training pack
            test_pack = TrainingPack(
                id="test-pack-1",
                name="Test Shooting Pack",
                code="TEST-SHOT-001",
                description="Test training pack for shooting",
                category="shooting",
                difficulty=3,
                skill_level="platinum",
                is_active=True,
                rating=4.5,
                rating_count=100
            )
            db.add(test_pack)
            db.commit()
            print("✅ Created test training pack")
        
        # Test model manager
        model_manager = get_model_manager()
        model_manager.set_db_session(db)
        print("✅ Model manager initialized")
        
        # Test getting recommendation engine
        try:
            recommendation_engine = model_manager.get_recommendation_engine()
            print("✅ TrainingRecommendationEngine loaded")
        except Exception as e:
            print(f"❌ TrainingRecommendationEngine failed: {e}")
            traceback.print_exc()
        
        db.close()
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        traceback.print_exc()


def debug_model_loading():
    """Debug ML model loading issues."""
    print("\n🔍 Debugging ML Model Loading...")
    
    try:
        from app.ml.models.weakness_detector import WeaknessDetector
        from app.ml.models.skill_analyzer import SkillAnalyzer
        from app.ml.models.recommendation_engine import TrainingRecommendationEngine
        from app.database import get_db
        
        db = next(get_db())
        
        # Test direct model instantiation
        print("Testing direct model instantiation...")
        
        try:
            weakness_detector = WeaknessDetector()
            print("✅ WeaknessDetector instantiated directly")
        except Exception as e:
            print(f"❌ WeaknessDetector direct instantiation failed: {e}")
            traceback.print_exc()
        
        try:
            skill_analyzer = SkillAnalyzer()
            print("✅ SkillAnalyzer instantiated directly")
        except Exception as e:
            print(f"❌ SkillAnalyzer direct instantiation failed: {e}")
            traceback.print_exc()
        
        try:
            recommendation_engine = TrainingRecommendationEngine(db)
            print("✅ TrainingRecommendationEngine instantiated directly")
        except Exception as e:
            print(f"❌ TrainingRecommendationEngine direct instantiation failed: {e}")
            traceback.print_exc()
        
        db.close()
        
    except Exception as e:
        print(f"❌ Model loading debug failed: {e}")
        traceback.print_exc()


def main():
    """Run all debug tests."""
    print("🚀 Starting ML API Debug Session")
    print("="*50)
    
    debug_model_loading()
    debug_weakness_analysis()
    debug_training_recommendations()
    
    print("\n" + "="*50)
    print("🏁 Debug session completed")


if __name__ == "__main__":
    main()
