#!/usr/bin/env python3
"""
Enhanced test script for Contestlet API with OTP and geolocation features
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_enhanced_api():
    print("🧪 Testing Enhanced Contestlet API...")
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test 2: Request OTP
    print("\n2. Testing OTP request...")
    phone_data = {"phone": "555-123-4567"}
    response = requests.post(f"{BASE_URL}/auth/request-otp", json=phone_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code != 200:
        print("❌ OTP request failed, continuing with other tests")
    
    # Test 3: Verify OTP (this will fail since we don't know the actual OTP)
    print("\n3. Testing OTP verification (will fail with wrong code)...")
    otp_data = {"phone": "555-123-4567", "code": "123456"}
    response = requests.post(f"{BASE_URL}/auth/verify-otp", json=otp_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test 4: Use legacy auth for token
    print("\n4. Getting auth token via legacy endpoint...")
    phone_data = {"phone": "555-123-4567"}
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
    
    # Test 5: Get nearby contests (should return empty but work)
    print("\n5. Testing nearby contests endpoint...")
    # Times Square coordinates
    lat, lng = 40.7589, -73.9851
    response = requests.get(f"{BASE_URL}/contests/nearby?lat={lat}&lng={lng}", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 6: Test invalid coordinates
    print("\n6. Testing invalid coordinates...")
    response = requests.get(f"{BASE_URL}/contests/nearby?lat=999&lng=999", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test 7: Test rate limiting (make multiple OTP requests)
    print("\n7. Testing rate limiting...")
    for i in range(3):
        response = requests.post(f"{BASE_URL}/auth/request-otp", json={"phone": "555-999-8888"})
        print(f"   Request {i+1} Status: {response.status_code}")
        if response.status_code == 429:
            print(f"   Rate limited: {response.json()}")
            break
    
    # Test 8: Regular active contests
    print("\n8. Testing regular active contests...")
    response = requests.get(f"{BASE_URL}/contests/active", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print("\n✅ Enhanced API tests completed!")
    print(f"\n📚 API Documentation: {BASE_URL}/docs")
    print(f"📖 ReDoc Documentation: {BASE_URL}/redoc")
    
    print("\n🆕 New Features Added:")
    print("   • OTP-based phone verification with rate limiting")
    print("   • Geolocation support for contests")
    print("   • Nearby contests search using Haversine distance")
    print("   • Mock SMS service (set USE_MOCK_SMS=False for real Twilio)")

if __name__ == "__main__":
    try:
        test_enhanced_api()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running with:")
        print("   python3 run.py")
    except Exception as e:
        print(f"❌ Error: {e}")
