#!/usr/bin/env python3
"""
🧪 Smoke Tests for Contestlet API

Quick validation tests to ensure the deployment is working correctly.
Run after each deployment to verify core functionality.
"""

import requests
import json
import sys
import os
import argparse
from datetime import datetime


class SmokeTests:
    def __init__(self, base_url, environment):
        self.base_url = base_url.rstrip('/')
        self.environment = environment
        self.passed = 0
        self.failed = 0
        
    def test_health_check(self):
        """Test basic health endpoint"""
        print("🏥 Testing health check...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "healthy"
            assert "message" in data
            print("✅ Health check passed")
            self.passed += 1
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            self.failed += 1
            
    def test_documentation(self):
        """Test API documentation endpoints"""
        print("📚 Testing documentation...")
        try:
            # Test OpenAPI docs
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            assert response.status_code == 200
            assert "Contestlet API" in response.text
            
            # Test ReDoc
            response = requests.get(f"{self.base_url}/redoc", timeout=10)
            assert response.status_code == 200
            
            print("✅ Documentation endpoints accessible")
            self.passed += 1
        except Exception as e:
            print(f"❌ Documentation test failed: {e}")
            self.failed += 1
            
    def test_timezone_endpoints(self):
        """Test timezone functionality"""
        print("🌍 Testing timezone endpoints...")
        try:
            # Test timezone list
            response = requests.get(f"{self.base_url}/admin/profile/timezones", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert "timezones" in data
            assert len(data["timezones"]) >= 10  # Should have multiple timezones
            
            print("✅ Timezone endpoints working")
            self.passed += 1
        except Exception as e:
            print(f"❌ Timezone test failed: {e}")
            self.failed += 1
            
    def test_contest_endpoints(self):
        """Test contest listing (public endpoint)"""
        print("🏆 Testing contest endpoints...")
        try:
            # Test active contests endpoint
            response = requests.get(f"{self.base_url}/contests/active", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            
            print("✅ Contest endpoints accessible")
            self.passed += 1
        except Exception as e:
            print(f"❌ Contest test failed: {e}")
            self.failed += 1
            
    def test_admin_auth_required(self):
        """Test that admin endpoints require authentication"""
        print("🔐 Testing admin authentication...")
        try:
            # Test admin endpoint without auth
            response = requests.get(f"{self.base_url}/admin/contests", timeout=10)
            assert response.status_code in [401, 403]  # Should be unauthorized
            
            print("✅ Admin authentication required")
            self.passed += 1
        except Exception as e:
            print(f"❌ Admin auth test failed: {e}")
            self.failed += 1
            
    def test_cors_headers(self):
        """Test CORS headers are present"""
        print("🌐 Testing CORS headers...")
        try:
            response = requests.options(f"{self.base_url}/", timeout=10)
            # CORS headers should be present
            headers = response.headers
            assert "Access-Control-Allow-Origin" in headers
            
            print("✅ CORS headers present")
            self.passed += 1
        except Exception as e:
            print(f"❌ CORS test failed: {e}")
            self.failed += 1
            
    def test_error_handling(self):
        """Test error handling for invalid endpoints"""
        print("🚫 Testing error handling...")
        try:
            # Test 404 endpoint
            response = requests.get(f"{self.base_url}/nonexistent", timeout=10)
            assert response.status_code == 404
            
            print("✅ Error handling working")
            self.passed += 1
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            self.failed += 1
            
    def test_database_connectivity(self):
        """Test database connectivity through API"""
        print("🗄️ Testing database connectivity...")
        try:
            # Test endpoint that requires database
            response = requests.get(f"{self.base_url}/contests/active", timeout=10)
            assert response.status_code == 200
            # If we get here, database is connected
            
            print("✅ Database connectivity verified")
            self.passed += 1
        except Exception as e:
            print(f"❌ Database connectivity test failed: {e}")
            self.failed += 1
            
    def run_all_tests(self):
        """Run all smoke tests"""
        print(f"🧪 Starting smoke tests for {self.environment} environment")
        print(f"🔗 Base URL: {self.base_url}")
        print("=" * 50)
        
        # Run all tests
        self.test_health_check()
        self.test_documentation()
        self.test_timezone_endpoints()
        self.test_contest_endpoints()
        self.test_admin_auth_required()
        self.test_cors_headers()
        self.test_error_handling()
        self.test_database_connectivity()
        
        # Summary
        print("=" * 50)
        print(f"📊 Smoke Test Results:")
        print(f"   ✅ Passed: {self.passed}")
        print(f"   ❌ Failed: {self.failed}")
        print(f"   📊 Total: {self.passed + self.failed}")
        
        success_rate = (self.passed / (self.passed + self.failed)) * 100 if (self.passed + self.failed) > 0 else 0
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            print("🎉 All smoke tests passed!")
            return True
        else:
            print(f"⚠️ {self.failed} smoke tests failed!")
            return False


def main():
    parser = argparse.ArgumentParser(description="Run smoke tests for Contestlet API")
    parser.add_argument("--env", required=True, choices=["development", "staging", "production"],
                      help="Environment to test")
    parser.add_argument("--url", help="Custom base URL (overrides environment default)")
    
    args = parser.parse_args()
    
    # Environment-specific URLs
    urls = {
        "development": "http://localhost:8000",
        "staging": "https://staging-api.contestlet.com",
        "production": "https://api.contestlet.com"
    }
    
    base_url = args.url or urls[args.env]
    
    # Run smoke tests
    smoke_tests = SmokeTests(base_url, args.env)
    success = smoke_tests.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
