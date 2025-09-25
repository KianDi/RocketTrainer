#!/usr/bin/env python3
"""
Test rate limit headers functionality.
"""

import requests
import json
from uuid import uuid4

def test_rate_limit_headers():
    """Test that rate limit headers are properly added to responses."""
    
    base_url = "http://localhost:8000/api/ml"
    
    # Create a test user in the database first
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
    
    try:
        from app.database import get_db
        from app.models.user import User
        
        db = next(get_db())
        
        # Create test user
        test_user_id = uuid4()
        test_user = User(
            id=test_user_id,
            username=f"test_{test_user_id.hex[:8]}",
            email=f"test_{test_user_id.hex[:8]}@example.com",
            steam_id=f"{test_user_id.hex[:16]}",
            current_rank="gold_ii",
            mmr=750,
            platform="steam",
            is_active=True,
            is_premium=False  # Free tier
        )
        
        db.add(test_user)
        db.commit()
        
        print(f"✅ Created test user: {test_user_id}")
        
        # Test rate limit headers
        payload = {
            "user_id": str(test_user_id),
            "include_confidence": True,
            "analysis_depth": "standard"
        }
        
        print(f"\n🔍 Testing rate limit headers...")
        
        # Make a request
        response = requests.post(f"{base_url}/analyze-weaknesses", json=payload)
        
        print(f"Status: {response.status_code}")
        
        # Check for rate limit headers
        headers = dict(response.headers)
        rate_limit_headers = {
            'X-RateLimit-Limit': headers.get('X-RateLimit-Limit'),
            'X-RateLimit-Remaining': headers.get('X-RateLimit-Remaining'),
            'X-RateLimit-Reset': headers.get('X-RateLimit-Reset')
        }
        
        print(f"Rate limit headers: {rate_limit_headers}")
        
        # Check if headers are present
        if all(rate_limit_headers.values()):
            print("✅ All rate limit headers present!")
            print(f"   Limit: {rate_limit_headers['X-RateLimit-Limit']}")
            print(f"   Remaining: {rate_limit_headers['X-RateLimit-Remaining']}")
            print(f"   Reset: {rate_limit_headers['X-RateLimit-Reset']}")
        else:
            print("⚠️  Some rate limit headers missing")
            for header, value in rate_limit_headers.items():
                if value:
                    print(f"   ✅ {header}: {value}")
                else:
                    print(f"   ❌ {header}: Missing")
        
        # Make multiple requests to test rate limiting
        print(f"\n🔄 Testing rate limit enforcement...")
        
        for i in range(12):  # Should hit rate limit after 10
            response = requests.post(f"{base_url}/analyze-weaknesses", json=payload)
            headers = dict(response.headers)
            
            if response.status_code == 429:
                print(f"   Request {i+1}: 🚫 Rate limited (Status: {response.status_code})")
                print(f"      Retry-After: {headers.get('Retry-After', 'N/A')}")
                break
            else:
                remaining = headers.get('X-RateLimit-Remaining', 'N/A')
                print(f"   Request {i+1}: Status {response.status_code} (Remaining: {remaining})")
        
        # Cleanup
        db.delete(test_user)
        db.commit()
        print(f"\n✅ Cleaned up test user")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if 'db' in locals() and 'test_user' in locals():
            try:
                db.delete(test_user)
                db.commit()
            except:
                pass

if __name__ == "__main__":
    test_rate_limit_headers()
