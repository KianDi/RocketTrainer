#!/usr/bin/env python3
"""
Direct endpoint testing to identify the exact issue.
"""

import sys
import os
import traceback
from uuid import UUID
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_weakness_analysis_direct():
    """Test weakness analysis endpoint logic directly."""
    print("🔍 Testing Weakness Analysis Endpoint Logic Directly...")
    
    try:
        from app.database import get_db
        from app.models.user import User
        from app.models.match import Match
        from app.api.ml.model_manager import get_model_manager
        from app.api.ml.cache import MLModelCache
        from app.api.ml.schemas import WeaknessAnalysisRequest, SkillCategoryScore
        from app.api.ml.exceptions import InsufficientDataError, handle_ml_exception
        
        # Create request object
        request = WeaknessAnalysisRequest(
            user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            include_confidence=True,
            analysis_depth="standard"
        )
        
        print(f"✅ Request object created: {request.user_id}")
        
        # Get database session
        db = next(get_db())
        print("✅ Database session obtained")
        
        # Initialize components
        model_manager = get_model_manager()
        model_manager.set_db_session(db)
        cache = MLModelCache()
        print("✅ Components initialized")
        
        # Check cache first
        cached_result = cache.get_weakness_analysis(request.user_id, None)
        print(f"📦 Cache result: {cached_result is not None}")
        
        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        print(f"👤 User found: {user is not None}")
        
        if not user:
            print("ℹ️  User not found - this should trigger 404")
            # This should raise HTTPException with 404
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
    except Exception as e:
        print(f"🎯 Expected exception caught: {type(e).__name__}: {e}")
        
        # Test our exception handler
        try:
            from app.api.ml.exceptions import handle_ml_exception
            handled_exception = handle_ml_exception(e, {"user_id": str(request.user_id)})
            print(f"✅ Exception handled: {handled_exception.status_code}")
            print(f"   Detail: {handled_exception.detail}")
        except Exception as handler_error:
            print(f"❌ Exception handler failed: {handler_error}")
            traceback.print_exc()


def test_training_recommendation_direct():
    """Test training recommendation endpoint logic directly."""
    print("\n🔍 Testing Training Recommendation Endpoint Logic Directly...")
    
    try:
        from app.database import get_db
        from app.models.user import User
        from app.api.ml.model_manager import get_model_manager
        from app.api.ml.cache import MLModelCache
        from app.api.ml.schemas import TrainingRecommendationRequest
        from fastapi import HTTPException, status
        
        # Create request object
        request = TrainingRecommendationRequest(
            user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            skill_level="platinum",
            max_recommendations=5,
            categories=["shooting", "aerials"],
            exclude_completed=True
        )
        
        print(f"✅ Request object created: {request.user_id}")
        
        # Get database session
        db = next(get_db())
        print("✅ Database session obtained")
        
        # Initialize components
        model_manager = get_model_manager()
        model_manager.set_db_session(db)
        cache = MLModelCache()
        print("✅ Components initialized")
        
        # Check cache first
        cached_result = cache.get_training_recommendations(
            request.user_id, 
            request.skill_level,
            request.categories
        )
        print(f"📦 Cache result: {cached_result is not None}")
        
        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        print(f"👤 User found: {user is not None}")
        
        if not user:
            print("ℹ️  User not found - this should trigger 404")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
    except Exception as e:
        print(f"🎯 Expected exception caught: {type(e).__name__}: {e}")
        
        # Test our exception handler
        try:
            from app.api.ml.exceptions import handle_ml_exception
            handled_exception = handle_ml_exception(e, {"user_id": str(request.user_id)})
            print(f"✅ Exception handled: {handled_exception.status_code}")
            print(f"   Detail: {handled_exception.detail}")
        except Exception as handler_error:
            print(f"❌ Exception handler failed: {handler_error}")
            traceback.print_exc()


def test_actual_endpoint_call():
    """Test making actual HTTP calls to the endpoints."""
    print("\n🔍 Testing Actual HTTP Endpoint Calls...")
    
    import requests
    import json
    
    base_url = "http://localhost:8000/api/ml"
    
    # Test weakness analysis
    try:
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "include_confidence": True,
            "analysis_depth": "standard"
        }
        
        print("📡 Making weakness analysis request...")
        response = requests.post(f"{base_url}/analyze-weaknesses", json=payload)
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 422:
            error_detail = response.json()
            print(f"   Error detail: {json.dumps(error_detail, indent=2)}")
        
    except Exception as e:
        print(f"❌ HTTP request failed: {e}")
    
    # Test training recommendations
    try:
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "skill_level": "platinum",
            "max_recommendations": 5,
            "categories": ["shooting", "aerials"],
            "exclude_completed": True
        }
        
        print("\n📡 Making training recommendation request...")
        response = requests.post(f"{base_url}/recommend-training", json=payload)
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 422:
            error_detail = response.json()
            print(f"   Error detail: {json.dumps(error_detail, indent=2)}")
        
    except Exception as e:
        print(f"❌ HTTP request failed: {e}")


def main():
    """Run direct endpoint tests."""
    print("🚀 Starting Direct Endpoint Testing")
    print("="*50)
    
    test_weakness_analysis_direct()
    test_training_recommendation_direct()
    test_actual_endpoint_call()
    
    print("\n" + "="*50)
    print("🏁 Direct endpoint testing completed")


if __name__ == "__main__":
    main()
