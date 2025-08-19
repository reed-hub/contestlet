#!/usr/bin/env python3
"""
Simple test script for Contestlet API
This script demonstrates the API functionality and can be used for testing.
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_api():
    print("🧪 Testing Contestlet API...")
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test 2: Phone verification (auth)
    print("\n2. Testing phone verification...")
    phone_data = {"phone": "+15551234567"}
    response = requests.post(f"{BASE_URL}/auth/verify-phone", json=phone_data)
    print(f"   Status: {response.status_code}")
    auth_response = response.json()
    print(f"   Response: {auth_response}")
    
    if response.status_code != 200:
        print("❌ Auth failed, stopping tests")
        return
    
    # Extract token for authenticated requests
    token = auth_response["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 3: Get active contests (should be empty)
    print("\n3. Testing active contests...")
    response = requests.get(f"{BASE_URL}/contests/active", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test 4: Get user entries (should be empty)
    print("\n4. Testing user entries...")
    response = requests.get(f"{BASE_URL}/entries/me", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test 5: Try to enter a non-existent contest (should fail)
    print("\n5. Testing contest entry (non-existent contest)...")
    response = requests.post(f"{BASE_URL}/contests/999/enter", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print("\n✅ API tests completed!")
    print("\n📚 To see interactive documentation, visit: http://localhost:8000/docs")
    print("📖 To see ReDoc documentation, visit: http://localhost:8000/redoc")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running with:")
        print("   python3 -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
