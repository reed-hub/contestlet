#!/usr/bin/env python3
"""
Admin API test script for Contestlet with compliance and winner selection features
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "contestlet-admin-super-secret-token-change-in-production"

def test_admin_api():
    print("🛡️  Testing Contestlet Admin API...")
    
    # Admin headers
    admin_headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test 1: Admin auth check
    print("\n1. Testing admin authentication...")
    response = requests.get(f"{BASE_URL}/admin/auth", headers=admin_headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code != 200:
        print("❌ Admin auth failed, stopping tests")
        return
    
    # Test 2: Test invalid admin token
    print("\n2. Testing invalid admin token...")
    bad_headers = {"Authorization": "Bearer invalid-token"}
    response = requests.get(f"{BASE_URL}/admin/auth", headers=bad_headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test 3: Create contest with official rules
    print("\n3. Testing contest creation with official rules...")
    contest_data = {
        "name": "Admin Test Contest",
        "description": "A test contest created via admin API",
        "location": "New York, NY",
        "latitude": 40.7589,
        "longitude": -73.9851,
        "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now() + timedelta(days=8)).isoformat(),
        "prize_description": "Amazing prize worth $500",
        "active": True,
        "official_rules": {
            "eligibility_text": "Must be 18+ years old and resident of the United States",
            "sponsor_name": "Contestlet Inc.",
            "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=8)).isoformat(),
            "prize_value_usd": 500.0,
            "terms_url": "https://contestlet.com/terms"
        }
    }
    
    response = requests.post(f"{BASE_URL}/admin/contests", json=contest_data, headers=admin_headers)
    print(f"   Status: {response.status_code}")
    contest_response = response.json()
    print(f"   Created Contest ID: {contest_response.get('id')}")
    print(f"   Prize Value: ${contest_response.get('official_rules', {}).get('prize_value_usd')}")
    
    if response.status_code != 200:
        print("❌ Contest creation failed, stopping tests")
        return
    
    contest_id = contest_response["id"]
    
    # Test 4: List all contests (admin view)
    print("\n4. Testing admin contest listing...")
    response = requests.get(f"{BASE_URL}/admin/contests", headers=admin_headers)
    print(f"   Status: {response.status_code}")
    contests = response.json()
    print(f"   Total contests: {len(contests)}")
    if contests:
        print(f"   First contest entry count: {contests[0]['entry_count']}")
    
    # Test 5: Test compliance validation (missing required field)
    print("\n5. Testing compliance validation...")
    bad_contest_data = {
        "name": "Incomplete Contest",
        "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now() + timedelta(days=8)).isoformat(),
        "active": True,
        "official_rules": {
            "sponsor_name": "Test Sponsor",
            "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=8)).isoformat(),
            "prize_value_usd": 100.0
            # Missing eligibility_text - should fail
        }
    }
    
    response = requests.post(f"{BASE_URL}/admin/contests", json=bad_contest_data, headers=admin_headers)
    print(f"   Status: {response.status_code}")
    print(f"   Error: {response.json().get('detail')}")
    
    # Test 6: Update contest
    print("\n6. Testing contest update...")
    update_data = {
        "description": "Updated description via admin API",
        "prize_description": "Updated prize worth $750",
        "official_rules": {
            "prize_value_usd": 750.0
        }
    }
    
    response = requests.put(f"{BASE_URL}/admin/contests/{contest_id}", json=update_data, headers=admin_headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        updated_contest = response.json()
        print(f"   Updated prize value: ${updated_contest.get('official_rules', {}).get('prize_value_usd')}")
    
    # Test 7: Add entries to contest (for winner selection test)
    print("\n7. Setting up contest entries for winner selection...")
    
    # First get a user token
    auth_response = requests.post(f"{BASE_URL}/auth/verify-phone", json={"phone": "555-test-1"})
    if auth_response.status_code == 200:
        user_token = auth_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Try to enter the contest
        entry_response = requests.post(f"{BASE_URL}/contests/{contest_id}/enter", headers=user_headers)
        print(f"   Contest entry status: {entry_response.status_code}")
        if entry_response.status_code != 200:
            print(f"   Entry error: {entry_response.json()}")
    
    # Test 8: Try winner selection on active contest (should fail)
    print("\n8. Testing winner selection on active contest...")
    response = requests.post(f"{BASE_URL}/admin/contests/{contest_id}/select-winner", headers=admin_headers)
    print(f"   Status: {response.status_code}")
    print(f"   Message: {response.json().get('message')}")
    
    # Test 9: Create an ended contest for winner selection
    print("\n9. Creating ended contest for winner selection test...")
    ended_contest_data = {
        "name": "Ended Contest for Winner Test",
        "description": "Contest that has already ended",
        "start_time": (datetime.now() - timedelta(days=7)).isoformat(),
        "end_time": (datetime.now() - timedelta(days=1)).isoformat(),
        "prize_description": "Test prize",
        "active": True,
        "official_rules": {
            "eligibility_text": "Test eligibility",
            "sponsor_name": "Test Sponsor",
            "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "prize_value_usd": 100.0
        }
    }
    
    response = requests.post(f"{BASE_URL}/admin/contests", json=ended_contest_data, headers=admin_headers)
    if response.status_code == 200:
        ended_contest_id = response.json()["id"]
        
        # Test winner selection on ended contest
        print("\n10. Testing winner selection on ended contest...")
        response = requests.post(f"{BASE_URL}/admin/contests/{ended_contest_id}/select-winner", headers=admin_headers)
        print(f"   Status: {response.status_code}")
        winner_result = response.json()
        print(f"   Success: {winner_result.get('success')}")
        print(f"   Message: {winner_result.get('message')}")
        print(f"   Total entries: {winner_result.get('total_entries')}")
    
    print("\n✅ Admin API tests completed!")
    print(f"\n📚 Admin API Documentation: {BASE_URL}/docs#/admin")
    
    print("\n🆕 Admin Features Added:")
    print("   • Admin authentication with bearer token")
    print("   • Contest creation with mandatory official rules")
    print("   • Legal compliance validation")
    print("   • Contest management (create, update, list)")
    print("   • Random winner selection for ended contests")
    print("   • Duplicate entry prevention")
    print("   • Enhanced validation and error handling")

if __name__ == "__main__":
    try:
        test_admin_api()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running with:")
        print("   python3 run.py")
    except Exception as e:
        print(f"❌ Error: {e}")
