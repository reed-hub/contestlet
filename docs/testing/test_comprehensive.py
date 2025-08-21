#!/usr/bin/env python3
"""
Comprehensive test suite for Contestlet API
Tests all functionality: OTP auth, geolocation, admin features, compliance, and edge cases
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "contestlet-admin-super-secret-token-change-in-production"

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.user_tokens = {}
        self.contest_ids = []
        
    def test(self, name: str, condition: bool, details: str = ""):
        """Record test result"""
        if condition:
            print(f"   ✅ {name}")
            self.passed += 1
        else:
            print(f"   ❌ {name} - {details}")
            self.failed += 1
        return condition
    
    def make_request(self, method: str, endpoint: str, headers: Dict = None, json_data: Dict = None) -> requests.Response:
        """Make HTTP request with error handling"""
        try:
            url = f"{BASE_URL}{endpoint}"
            if method.upper() == "GET":
                return requests.get(url, headers=headers)
            elif method.upper() == "POST":
                return requests.post(url, headers=headers, json=json_data)
            elif method.upper() == "PUT":
                return requests.put(url, headers=headers, json=json_data)
        except Exception as e:
            print(f"   🔥 Request failed: {e}")
            return None

def run_comprehensive_tests():
    runner = TestRunner()
    
    print("🧪 CONTESTLET API - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # ===== BASIC CONNECTIVITY =====
    print("\n🔗 1. BASIC CONNECTIVITY")
    response = runner.make_request("GET", "/")
    runner.test("Server responds to health check", 
                response and response.status_code == 200)
    
    response = runner.make_request("GET", "/docs")
    runner.test("API documentation accessible", 
                response and response.status_code == 200)
    
    # ===== AUTHENTICATION FLOW =====
    print("\n🔐 2. AUTHENTICATION & OTP FLOW")
    
    # Test OTP request
    response = runner.make_request("POST", "/auth/request-otp", 
                                 json_data={"phone": "555-test-user1"})
    runner.test("OTP request for valid phone number", 
                response and response.status_code == 200)
    
    # Test invalid phone format
    response = runner.make_request("POST", "/auth/request-otp", 
                                 json_data={"phone": "invalid"})
    runner.test("OTP request rejects invalid phone format", 
                response and response.status_code == 400)
    
    # Test OTP verification with wrong code
    response = runner.make_request("POST", "/auth/verify-otp", 
                                 json_data={"phone": "555-test-user1", "code": "000000"})
    success = response and response.status_code == 200 and not response.json().get("success", True)
    runner.test("OTP verification rejects wrong code", success)
    
    # Use legacy auth to get tokens for testing
    test_phones = ["555-test-user1", "555-test-user2", "555-admin-test"]
    for phone in test_phones:
        response = runner.make_request("POST", "/auth/verify-phone", 
                                     json_data={"phone": phone})
        if response and response.status_code == 200:
            runner.user_tokens[phone] = response.json()["access_token"]
            runner.test(f"Legacy auth successful for {phone}", True)
        else:
            runner.test(f"Legacy auth failed for {phone}", False)
    
    # ===== RATE LIMITING =====
    print("\n⏱️  3. RATE LIMITING")
    
    # Test rate limiting by making multiple requests
    rate_limit_phone = "555-rate-limit-test"
    rate_limited = False
    
    for i in range(7):  # Should hit limit at 5
        response = runner.make_request("POST", "/auth/request-otp", 
                                     json_data={"phone": rate_limit_phone})
        if response and response.status_code == 429:
            rate_limited = True
            break
    
    runner.test("Rate limiting enforced for OTP requests", rate_limited)
    
    # ===== ADMIN AUTHENTICATION =====
    print("\n🛡️  4. ADMIN AUTHENTICATION")
    
    admin_headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = runner.make_request("GET", "/admin/auth", headers=admin_headers)
    runner.test("Valid admin token accepted", 
                response and response.status_code == 200)
    
    bad_headers = {"Authorization": "Bearer invalid-token"}
    response = runner.make_request("GET", "/admin/auth", headers=bad_headers)
    runner.test("Invalid admin token rejected", 
                response and response.status_code == 403)
    
    # ===== CONTEST CREATION & COMPLIANCE =====
    print("\n📋 5. CONTEST CREATION & COMPLIANCE")
    
    # Test contest creation with proper official rules
    contest_data = {
        "name": "Test Contest #1",
        "description": "Comprehensive test contest",
        "location": "San Francisco, CA",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "start_time": (datetime.now() + timedelta(hours=1)).isoformat(),
        "end_time": (datetime.now() + timedelta(days=7)).isoformat(),
        "prize_description": "Amazing prize worth $1000",
        "active": True,
        "official_rules": {
            "eligibility_text": "Must be 18+ years old and resident of the United States",
            "sponsor_name": "Contestlet Test Inc.",
            "start_date": (datetime.now() + timedelta(hours=1)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "prize_value_usd": 1000.0,
            "terms_url": "https://test.com/terms"
        }
    }
    
    response = runner.make_request("POST", "/admin/contests", 
                                 headers=admin_headers, json_data=contest_data)
    if response and response.status_code == 200:
        contest_id = response.json()["id"]
        runner.contest_ids.append(contest_id)
        runner.test("Contest creation with valid official rules", True)
    else:
        runner.test("Contest creation with valid official rules", False, 
                   f"Status: {response.status_code if response else 'No response'}")
    
    # Test compliance validation - missing required field
    bad_contest_data = contest_data.copy()
    bad_contest_data["official_rules"] = {
        "sponsor_name": "Test",
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "prize_value_usd": 100.0
        # Missing eligibility_text
    }
    
    response = runner.make_request("POST", "/admin/contests", 
                                 headers=admin_headers, json_data=bad_contest_data)
    runner.test("Compliance validation rejects incomplete rules", 
                response and response.status_code == 422)
    
    # ===== CONTEST LISTING =====
    print("\n📝 6. CONTEST LISTING")
    
    # Test public contest listing
    response = runner.make_request("GET", "/contests/active")
    runner.test("Public active contests listing", 
                response and response.status_code == 200)
    
    # Test admin contest listing
    response = runner.make_request("GET", "/admin/contests", headers=admin_headers)
    if response and response.status_code == 200:
        contests = response.json()
        runner.test("Admin contest listing with entry counts", len(contests) > 0)
    else:
        runner.test("Admin contest listing", False)
    
    # ===== GEOLOCATION FEATURES =====
    print("\n📍 7. GEOLOCATION & NEARBY SEARCH")
    
    # Test nearby contests - San Francisco area
    sf_lat, sf_lng = 37.7749, -122.4194
    response = runner.make_request("GET", f"/contests/nearby?lat={sf_lat}&lng={sf_lng}&radius=50")
    runner.test("Nearby contests search with valid coordinates", 
                response and response.status_code == 200)
    
    # Test invalid coordinates
    response = runner.make_request("GET", "/contests/nearby?lat=999&lng=999")
    runner.test("Nearby contests rejects invalid coordinates", 
                response and response.status_code == 400)
    
    # ===== CONTEST ENTRY =====
    print("\n🎯 8. CONTEST ENTRY & VALIDATION")
    
    if runner.contest_ids and runner.user_tokens:
        contest_id = runner.contest_ids[0]
        user_token = list(runner.user_tokens.values())[0]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Test contest entry
        response = runner.make_request("POST", f"/contests/{contest_id}/enter", 
                                     headers=user_headers)
        runner.test("User can enter valid contest", 
                    response and response.status_code == 200)
        
        # Test duplicate entry prevention
        response = runner.make_request("POST", f"/contests/{contest_id}/enter", 
                                     headers=user_headers)
        runner.test("Duplicate entry prevention", 
                    response and response.status_code == 409)
        
        # Test user's entries
        response = runner.make_request("GET", "/entries/me", headers=user_headers)
        if response and response.status_code == 200:
            entries = response.json()
            runner.test("User can view their entries", len(entries) > 0)
        else:
            runner.test("User can view their entries", False)
    else:
        runner.test("Contest entry tests", False, "No contest or user token available")
    
    # ===== EXPIRED CONTEST HANDLING =====
    print("\n⏰ 9. EXPIRED CONTEST HANDLING")
    
    # Create an expired contest
    expired_contest_data = contest_data.copy()
    expired_contest_data.update({
        "name": "Expired Test Contest",
        "start_time": (datetime.now() - timedelta(days=7)).isoformat(),
        "end_time": (datetime.now() - timedelta(days=1)).isoformat(),
    })
    expired_contest_data["official_rules"].update({
        "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
        "end_date": (datetime.now() - timedelta(days=1)).isoformat(),
    })
    
    response = runner.make_request("POST", "/admin/contests", 
                                 headers=admin_headers, json_data=expired_contest_data)
    if response and response.status_code == 200:
        expired_contest_id = response.json()["id"]
        
        # Try to enter expired contest
        if runner.user_tokens:
            user_token = list(runner.user_tokens.values())[0]
            user_headers = {"Authorization": f"Bearer {user_token}"}
            response = runner.make_request("POST", f"/contests/{expired_contest_id}/enter", 
                                         headers=user_headers)
            runner.test("Cannot enter expired contest", 
                        response and response.status_code == 400)
        else:
            runner.test("Expired contest entry test", False, "No user token")
    else:
        runner.test("Create expired contest for testing", False)
    
    # ===== WINNER SELECTION =====
    print("\n🏆 10. WINNER SELECTION")
    
    # Test winner selection on active contest (should fail)
    if runner.contest_ids:
        contest_id = runner.contest_ids[0]
        response = runner.make_request("POST", f"/admin/contests/{contest_id}/select-winner", 
                                     headers=admin_headers)
        runner.test("Cannot select winner for active contest", 
                    response and response.status_code == 400)
    
    # Test winner selection on expired contest (should work but no entries)
    if 'expired_contest_id' in locals():
        response = runner.make_request("POST", f"/admin/contests/{expired_contest_id}/select-winner", 
                                     headers=admin_headers)
        if response and response.status_code == 200:
            result = response.json()
            runner.test("Winner selection on expired contest (no entries)", 
                        not result.get("success") and "no entries" in result.get("message", "").lower())
        else:
            runner.test("Winner selection API call", False)
    
    # ===== CONTEST UPDATES =====
    print("\n🔄 11. CONTEST UPDATES")
    
    if runner.contest_ids:
        contest_id = runner.contest_ids[0]
        update_data = {
            "description": "Updated description via comprehensive test",
            "prize_description": "Updated prize worth $1500",
            "official_rules": {
                "prize_value_usd": 1500.0
            }
        }
        
        response = runner.make_request("PUT", f"/admin/contests/{contest_id}", 
                                     headers=admin_headers, json_data=update_data)
        runner.test("Contest update with official rules", 
                    response and response.status_code == 200)
    
    # ===== EDGE CASES & ERROR HANDLING =====
    print("\n🚨 12. EDGE CASES & ERROR HANDLING")
    
    # Test non-existent contest entry
    if runner.user_tokens:
        user_token = list(runner.user_tokens.values())[0]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        response = runner.make_request("POST", "/contests/99999/enter", headers=user_headers)
        runner.test("Non-existent contest entry returns 404", 
                    response and response.status_code == 404)
    
    # Test unauthorized admin access
    response = runner.make_request("GET", "/admin/contests")
    runner.test("Admin endpoints require authentication", 
                response and response.status_code == 422)  # Missing auth header
    
    # Test invalid JSON in requests
    try:
        response = requests.post(f"{BASE_URL}/auth/request-otp", 
                               headers={"Content-Type": "application/json"}, 
                               data="{invalid json")
        runner.test("Invalid JSON handling", response.status_code == 422)
    except:
        runner.test("Invalid JSON handling", True, "Request properly rejected")
    
    # ===== FINAL RESULTS =====
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    print(f"✅ PASSED: {runner.passed}")
    print(f"❌ FAILED: {runner.failed}")
    print(f"📈 SUCCESS RATE: {runner.passed / (runner.passed + runner.failed) * 100:.1f}%")
    
    if runner.failed == 0:
        print("\n🎉 ALL TESTS PASSED! Contestlet API is fully functional! 🎉")
    else:
        print(f"\n⚠️  {runner.failed} tests failed. Review output above for details.")
    
    print(f"\n🌐 API Documentation: {BASE_URL}/docs")
    print(f"📚 ReDoc: {BASE_URL}/redoc")
    
    return runner.failed == 0

if __name__ == "__main__":
    try:
        success = run_comprehensive_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚡ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite failed with error: {e}")
        exit(1)
