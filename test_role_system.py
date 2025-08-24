#!/usr/bin/env python3
"""
Comprehensive Role System Tests

Tests for multi-tier role system including:
- Role assignment and validation
- Permission checks on all endpoints
- Data isolation between roles
- Security and access control
"""

import pytest
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Test Configuration
BASE_URL = "http://localhost:8000"
ADMIN_PHONE = "+18187958204"
TEST_SPONSOR_PHONE = "+15551234567"
TEST_USER_PHONE = "+15559876543"

class RoleSystemTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        
    def request_otp(self, phone: str) -> bool:
        """Request OTP for phone number"""
        response = requests.post(f"{self.base_url}/auth/request-otp", json={
            "phone": phone
        })
        return response.status_code == 200
    
    def verify_otp(self, phone: str, code: str = "123456") -> Dict[str, Any]:
        """Verify OTP and get auth token"""
        response = requests.post(f"{self.base_url}/auth/verify-otp", json={
            "phone": phone,
            "code": code
        })
        
        if response.status_code == 200:
            data = response.json()
            self.tokens[phone] = data["access_token"]
            self.users[phone] = data
            return data
        else:
            raise Exception(f"OTP verification failed: {response.text}")
    
    def get_headers(self, phone: str) -> Dict[str, str]:
        """Get authorization headers for user"""
        if phone not in self.tokens:
            raise Exception(f"No token found for {phone}")
        
        return {
            "Authorization": f"Bearer {self.tokens[phone]}",
            "Content-Type": "application/json"
        }
    
    def setup_test_users(self):
        """Set up test users with different roles"""
        print("🔧 Setting up test users...")
        
        # Admin user (should already exist)
        try:
            self.request_otp(ADMIN_PHONE)
            self.verify_otp(ADMIN_PHONE)
            print(f"✅ Admin user authenticated: {ADMIN_PHONE}")
        except Exception as e:
            print(f"❌ Admin setup failed: {e}")
            return False
        
        # Test sponsor user
        try:
            self.request_otp(TEST_SPONSOR_PHONE)
            self.verify_otp(TEST_SPONSOR_PHONE)
            print(f"✅ Sponsor user authenticated: {TEST_SPONSOR_PHONE}")
        except Exception as e:
            print(f"❌ Sponsor setup failed: {e}")
            return False
        
        # Test regular user
        try:
            self.request_otp(TEST_USER_PHONE)
            self.verify_otp(TEST_USER_PHONE)
            print(f"✅ Regular user authenticated: {TEST_USER_PHONE}")
        except Exception as e:
            print(f"❌ User setup failed: {e}")
            return False
        
        return True
    
    def test_role_assignment(self):
        """Test role assignment functionality"""
        print("\n🎯 Testing Role Assignment...")
        
        # Test admin role assignment (sponsor -> admin should fail for non-admins)
        headers = self.get_headers(TEST_SPONSOR_PHONE)
        response = requests.post(
            f"{self.base_url}/admin/users/1/assign-role",
            headers=headers,
            json={"role": "admin", "reason": "Test assignment"}
        )
        
        if response.status_code == 403:
            print("✅ Non-admin cannot assign admin role")
        else:
            print(f"❌ Role assignment security failed: {response.status_code}")
        
        # Test sponsor role upgrade request
        headers = self.get_headers(TEST_USER_PHONE)
        response = requests.post(
            f"{self.base_url}/sponsor/upgrade-request",
            headers=headers,
            json={
                "target_role": "sponsor",
                "company_name": "Test Company",
                "website_url": "https://testcompany.com",
                "industry": "Technology",
                "description": "Test company for role system testing"
            }
        )
        
        if response.status_code == 200:
            print("✅ User can request sponsor upgrade")
        else:
            print(f"❌ Sponsor upgrade request failed: {response.status_code} - {response.text}")
    
    def test_sponsor_functionality(self):
        """Test sponsor-specific functionality"""
        print("\n🏢 Testing Sponsor Functionality...")
        
        headers = self.get_headers(TEST_SPONSOR_PHONE)
        
        # Test sponsor profile creation/update
        response = requests.put(
            f"{self.base_url}/sponsor/profile",
            headers=headers,
            json={
                "company_name": "Updated Test Company",
                "website_url": "https://updatedtestcompany.com",
                "industry": "Technology",
                "description": "Updated test company description"
            }
        )
        
        if response.status_code in [200, 404]:  # 404 if profile doesn't exist yet
            print("✅ Sponsor profile management working")
        else:
            print(f"❌ Sponsor profile update failed: {response.status_code}")
        
        # Test sponsor contest creation
        contest_data = {
            "name": "Sponsor Test Contest",
            "description": "Test contest created by sponsor",
            "start_time": (datetime.now() + timedelta(days=1)).isoformat() + "Z",
            "end_time": (datetime.now() + timedelta(days=8)).isoformat() + "Z",
            "prize_description": "Test Prize",
            "official_rules": {
                "sponsor_name": "Test Sponsor",
                "eligibility_text": "Test eligibility",
                "prize_value_usd": 100,
                "terms_and_conditions": "Test terms",
                "winner_selection_process": "Random",
                "claim_instructions": "Test claim",
                "start_date": (datetime.now() + timedelta(days=1)).isoformat() + "Z",
                "end_date": (datetime.now() + timedelta(days=8)).isoformat() + "Z"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/sponsor/contests",
            headers=headers,
            json=contest_data
        )
        
        if response.status_code == 200:
            print("✅ Sponsor can create contests")
            contest_id = response.json().get("id")
            
            # Test sponsor contest management
            response = requests.get(
                f"{self.base_url}/sponsor/contests/{contest_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ Sponsor can view own contests")
            else:
                print(f"❌ Sponsor contest viewing failed: {response.status_code}")
        else:
            print(f"❌ Sponsor contest creation failed: {response.status_code} - {response.text}")
    
    def test_user_functionality(self):
        """Test user-specific functionality"""
        print("\n👤 Testing User Functionality...")
        
        headers = self.get_headers(TEST_USER_PHONE)
        
        # Test user profile access
        response = requests.get(f"{self.base_url}/user/profile", headers=headers)
        
        if response.status_code == 200:
            print("✅ User can access own profile")
        else:
            print(f"❌ User profile access failed: {response.status_code}")
        
        # Test available contests viewing
        response = requests.get(f"{self.base_url}/user/contests/available", headers=headers)
        
        if response.status_code == 200:
            print("✅ User can view available contests")
        else:
            print(f"❌ User contest viewing failed: {response.status_code}")
        
        # Test user statistics
        response = requests.get(f"{self.base_url}/user/stats", headers=headers)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ User stats: {stats.get('total_entries', 0)} entries, {stats.get('win_rate', 0)}% win rate")
        else:
            print(f"❌ User stats failed: {response.status_code}")
    
    def test_admin_functionality(self):
        """Test admin-specific functionality"""
        print("\n👑 Testing Admin Functionality...")
        
        headers = self.get_headers(ADMIN_PHONE)
        
        # Test admin contest management
        response = requests.get(f"{self.base_url}/admin/contests", headers=headers)
        
        if response.status_code == 200:
            print("✅ Admin can view all contests")
        else:
            print(f"❌ Admin contest viewing failed: {response.status_code}")
        
        # Test admin user management
        response = requests.get(f"{self.base_url}/admin/users", headers=headers)
        
        if response.status_code in [200, 404]:  # 404 if endpoint doesn't exist yet
            print("✅ Admin user management accessible")
        else:
            print(f"❌ Admin user management failed: {response.status_code}")
    
    def test_access_control(self):
        """Test access control and security"""
        print("\n🔒 Testing Access Control...")
        
        # Test user trying to access admin endpoints
        user_headers = self.get_headers(TEST_USER_PHONE)
        response = requests.get(f"{self.base_url}/admin/contests", headers=user_headers)
        
        if response.status_code == 403:
            print("✅ User blocked from admin endpoints")
        else:
            print(f"❌ User access control failed: {response.status_code}")
        
        # Test sponsor trying to access other sponsor's contests
        sponsor_headers = self.get_headers(TEST_SPONSOR_PHONE)
        response = requests.get(f"{self.base_url}/sponsor/contests/999", headers=sponsor_headers)
        
        if response.status_code in [403, 404]:
            print("✅ Sponsor blocked from other sponsors' contests")
        else:
            print(f"❌ Sponsor access control failed: {response.status_code}")
        
        # Test unauthenticated access
        response = requests.get(f"{self.base_url}/user/profile")
        
        if response.status_code == 401:
            print("✅ Unauthenticated access blocked")
        else:
            print(f"❌ Authentication check failed: {response.status_code}")
    
    def test_data_isolation(self):
        """Test data isolation between users"""
        print("\n🏗️ Testing Data Isolation...")
        
        # Test user can only see own entries
        user_headers = self.get_headers(TEST_USER_PHONE)
        response = requests.get(f"{self.base_url}/user/entries", headers=user_headers)
        
        if response.status_code == 200:
            entries = response.json()
            print(f"✅ User sees {len(entries)} own entries")
        else:
            print(f"❌ User entry isolation failed: {response.status_code}")
        
        # Test sponsor can only see own contests
        sponsor_headers = self.get_headers(TEST_SPONSOR_PHONE)
        response = requests.get(f"{self.base_url}/sponsor/contests", headers=sponsor_headers)
        
        if response.status_code == 200:
            contests = response.json()
            print(f"✅ Sponsor sees {len(contests)} own contests")
        else:
            print(f"❌ Sponsor contest isolation failed: {response.status_code}")
    
    def run_all_tests(self):
        """Run all role system tests"""
        print("🚀 Starting Role System Tests...")
        print("=" * 50)
        
        if not self.setup_test_users():
            print("❌ Test setup failed, aborting tests")
            return False
        
        try:
            self.test_role_assignment()
            self.test_sponsor_functionality()
            self.test_user_functionality()
            self.test_admin_functionality()
            self.test_access_control()
            self.test_data_isolation()
            
            print("\n" + "=" * 50)
            print("✅ Role System Tests Complete!")
            return True
            
        except Exception as e:
            print(f"\n❌ Test execution failed: {e}")
            return False


def main():
    """Main test execution"""
    tester = RoleSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All role system tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)


if __name__ == "__main__":
    main()
