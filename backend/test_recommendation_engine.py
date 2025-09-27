#!/usr/bin/env python3
"""
Test script to debug the recommendation engine directly.
"""

import sys
import os
sys.path.append('/app')

from app.database import get_db
from app.api.ml.model_manager import get_model_manager
from app.models.training_pack import TrainingPack

def test_recommendation_engine():
    """Test the recommendation engine directly."""
    print("🔧 Testing Recommendation Engine")
    
    # Get database session
    db = next(get_db())
    print(f"✅ Database session obtained")
    
    # Check training packs in database
    packs = db.query(TrainingPack).limit(3).all()
    print(f"📦 Found {len(packs)} training packs in database:")
    for pack in packs:
        print(f"   - {pack.name} ({pack.code}) - {pack.category}")
    
    # Get model manager
    model_manager = get_model_manager()
    model_manager.set_db_session(db)
    print(f"✅ Model manager initialized with DB session")
    
    # Try to get recommendation engine
    try:
        print("🤖 Attempting to get recommendation engine...")
        recommendation_engine = model_manager.get_recommendation_engine()
        print(f"✅ Recommendation engine obtained: {type(recommendation_engine)}")
        
        # Test recommendation generation
        print("🎯 Testing recommendation generation...")
        weaknesses = [{
            "weakness": "mechanical",
            "confidence": 0.8,
            "category": "mechanical"
        }]
        
        recommendations = recommendation_engine.recommend_training_packs(
            user_id="test-user-123",
            weaknesses=weaknesses,
            player_skill_level="platinum",
            max_recommendations=3,
            include_variety=True
        )
        
        print(f"✅ Generated {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations):
            pack = rec.get("pack")
            if pack:
                print(f"   {i+1}. {pack.name} ({pack.code}) - Score: {rec.get('total_score', 0):.3f}")
            else:
                print(f"   {i+1}. No pack data - {rec}")
                
    except Exception as e:
        print(f"❌ Error with recommendation engine: {e}")
        import traceback
        traceback.print_exc()
    
    print("🏁 Test completed")

if __name__ == "__main__":
    test_recommendation_engine()
