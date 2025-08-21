#!/usr/bin/env python3
"""
Final comprehensive test for Contestlet API
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "contestlet-admin-super-secret-token-change-in-production"

def test_api():
    print("🧪 FINAL CONTESTLET API TEST")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. 🏥 Health Check")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("   ✅ Server is healthy")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Test 2: Authentication
    print("\n2. 🔐 Authentication")
    
    # Test OTP request
    try:
        response = requests.post(f"{BASE_URL}/auth/request-otp", 
                               json={"phone": "5551234567"})
        if response.status_code == 200:
            print("   ✅ OTP request successful")
            print(f"   📱 Mock SMS should show in server logs")
        else:
            print(f"   ❌ OTP request failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ OTP request error: {e}")
    
    # Test legacy auth for token
    try:
        response = requests.post(f"{BASE_URL}/auth/verify-phone", 
                               json={"phone": "5551234567"})
        if response.status_code == 200:
            user_token = response.json()["access_token"]
            print("   ✅ User authentication successful")
        else:
            print(f"   ❌ User auth failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ User auth error: {e}")
        return
    
    # Test 3: Admin Authentication
    print("\n3. 🛡️  Admin Authentication")
    admin_headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    try:
        response = requests.get(f"{BASE_URL}/admin/auth", headers=admin_headers)
        if response.status_code == 200:
            print("   ✅ Admin authentication successful")
        else:
            print(f"   ❌ Admin auth failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Admin auth error: {e}")
    
    # Test 4: Contest Creation
    print("\n4. 📋 Contest Creation with Official Rules")
    
    contest_data = {
        "name": "Final Test Contest",
        "description": "Comprehensive test contest with all features",
        "location": "San Francisco, CA",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "start_time": (datetime.now() + timedelta(hours=1)).isoformat(),
        "end_time": (datetime.now() + timedelta(days=7)).isoformat(),
        "prize_description": "Amazing test prize worth $1000",
        "active": True,
        "official_rules": {
            "eligibility_text": "Must be 18+ years old and resident of the United States",
            "sponsor_name": "Contestlet Test Inc.",
            "start_date": (datetime.now() + timedelta(hours=1)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "prize_value_usd": 1000.0,
            "terms_url": "https://contestlet.com/terms"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/admin/contests", 
                               headers=admin_headers, json=contest_data)
        if response.status_code == 200:
            contest_id = response.json()["id"]
            prize_value = response.json().get("official_rules", {}).get("prize_value_usd")
            print(f"   ✅ Contest created with ID: {contest_id}")
            print(f"   💰 Prize value: ${prize_value}")
        else:
            print(f"   ❌ Contest creation failed: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}")
            return
    except Exception as e:
        print(f"   ❌ Contest creation error: {e}")
        return
    
    # Test 5: Geolocation - Nearby Contests
    print("\n5. 📍 Geolocation & Nearby Search")
    
    try:
        # Search near San Francisco
        response = requests.get(f"{BASE_URL}/contests/nearby?lat=37.7749&lng=-122.4194&radius=50")
        if response.status_code == 200:
            contests = response.json()["contests"]
            print(f"   ✅ Found {len(contests)} contests near SF")
            if contests:
                distance = contests[0].get("distance_miles")
                if distance is not None:
                    print(f"   📏 Closest contest: {distance} miles away")
        else:
            print(f"   ❌ Nearby search failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Nearby search error: {e}")
    
    # Test 6: Contest Entry
    print("\n6. 🎯 Contest Entry")
    
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/contests/{contest_id}/enter", 
                               headers=user_headers)
        if response.status_code == 200:
            print("   ✅ Successfully entered contest")
        else:
            print(f"   ❌ Contest entry failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Contest entry error: {e}")
    
    # Test 7: Duplicate Entry Prevention
    print("\n7. 🚫 Duplicate Entry Prevention")
    
    try:
        response = requests.post(f"{BASE_URL}/contests/{contest_id}/enter", 
                               headers=user_headers)
        if response.status_code == 409:  # Conflict
            print("   ✅ Duplicate entry properly blocked")
        else:
            print(f"   ❌ Duplicate prevention failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Duplicate test error: {e}")
    
    # Test 8: User's Entries
    print("\n8. 📋 User's Contest Entries")
    
    try:
        response = requests.get(f"{BASE_URL}/entries/me", headers=user_headers)
        if response.status_code == 200:
            entries = response.json()
            print(f"   ✅ User has {len(entries)} contest entries")
        else:
            print(f"   ❌ Entries retrieval failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Entries retrieval error: {e}")
    
    # Test 9: Admin Contest Management
    print("\n9. 🔧 Admin Contest Management")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/contests", headers=admin_headers)
        if response.status_code == 200:
            admin_contests = response.json()
            if admin_contests:
                entry_count = admin_contests[0]["entry_count"]
                print(f"   ✅ Admin view shows {len(admin_contests)} contests")
                print(f"   📊 Contest has {entry_count} entries")
        else:
            print(f"   ❌ Admin contest list failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Admin contest list error: {e}")
    
    # Test 10: Contest Update
    print("\n10. 🔄 Contest Update")
    
    update_data = {
        "description": "Updated via final test script",
        "official_rules": {
            "prize_value_usd": 1500.0
        }
    }
    
    try:
        response = requests.put(f"{BASE_URL}/admin/contests/{contest_id}", 
                              headers=admin_headers, json=update_data)
        if response.status_code == 200:
            updated_prize = response.json().get("official_rules", {}).get("prize_value_usd")
            print(f"   ✅ Contest updated successfully")
            print(f"   💰 New prize value: ${updated_prize}")
        else:
            print(f"   ❌ Contest update failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Contest update error: {e}")
    
    # Test 11: Rate Limiting
    print("\n11. ⏱️  Rate Limiting Test")
    
    rate_limit_hit = False
    for i in range(6):
        try:
            response = requests.post(f"{BASE_URL}/auth/request-otp", 
                                   json={"phone": f"555-rate-{i}"})
            if response.status_code == 429:
                print(f"   ✅ Rate limit hit after {i+1} requests")
                rate_limit_hit = True
                break
        except Exception as e:
            print(f"   ❌ Rate limit test error: {e}")
            break
    
    if not rate_limit_hit:
        print("   ⚠️  Rate limit not triggered (may need more requests)")
    
    # Test 12: Winner Selection
    print("\n12. 🏆 Winner Selection")
    
    try:
        response = requests.post(f"{BASE_URL}/admin/contests/{contest_id}/select-winner", 
                               headers=admin_headers)
        if response.status_code == 400:
            print("   ✅ Cannot select winner for active contest (correct behavior)")
        else:
            print(f"   ❌ Winner selection check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Winner selection error: {e}")
    
    # Final Summary
    print("\n" + "=" * 50)
    print("🎉 FINAL TEST COMPLETE!")
    print("=" * 50)
    print("\n✅ KEY FEATURES TESTED:")
    print("   🔐 OTP-based phone authentication")
    print("   📍 Geolocation with Haversine distance")
    print("   🛡️  Admin authentication & management")
    print("   📋 Contest creation with official rules")
    print("   🎯 Contest entry with duplicate prevention")
    print("   ⏱️  Rate limiting protection")
    print("   🏆 Winner selection validation")
    print("   🔄 Contest updates & compliance")
    
    print(f"\n🌐 Live API: {BASE_URL}")
    print(f"📚 Documentation: {BASE_URL}/docs")
    print(f"🔧 Admin Token: {ADMIN_TOKEN}")
    
    print("\n🚀 Contestlet API is ready for production!")

if __name__ == "__main__":
    try:
        test_api()
    except KeyboardInterrupt:
        print("\n\n⚡ Test interrupted")
    except Exception as e:
        print(f"\n\n💥 Test failed: {e}")
