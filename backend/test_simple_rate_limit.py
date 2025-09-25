#!/usr/bin/env python3
"""
Simple test for rate limiting functionality.
"""

import requests
import json
from uuid import uuid4

def test_simple_rate_limit():
    """Test basic rate limiting functionality."""
    
    base_url = "http://localhost:8000/api/ml"
    
    # Test with a simple user_id
    test_user_id = str(uuid4())
    
    payload = {
        "user_id": test_user_id,
        "include_confidence": True,
        "analysis_depth": "standard"
    }
    
    print(f"Testing with user_id: {test_user_id}")
    
    # Make a single request
    try:
        response = requests.post(f"{base_url}/analyze-weaknesses", json=payload)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"Response body: {response.text}")
        else:
            print("✅ Request successful!")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_simple_rate_limit()
