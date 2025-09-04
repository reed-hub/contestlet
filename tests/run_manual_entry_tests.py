#!/usr/bin/env python3
"""
Manual Entry Test Runner
Comprehensive test suite for the Manual Entry feature
"""

import os
import sys
import subprocess
import time
from pathlib import Path


class ManualEntryTestRunner:
    """Test runner specifically for manual entry functionality"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = Path(__file__).parent
        
    def run_validation_tests(self):
        """Run schema validation tests"""
        print("🧪 Running Manual Entry Validation Tests...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                str(self.tests_dir / "unit" / "test_manual_entry_validation.py"),
                "-v", "--tb=short"
            ], cwd=self.project_root)
            
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Validation tests failed: {e}")
            return False
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("🧪 Running Manual Entry Integration Tests...")
        
        try:
            result = subprocess.run([
                sys.executable, 
                str(self.tests_dir / "integration" / "test_manual_entry_integration.py")
            ], cwd=self.project_root)
            
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Integration tests failed: {e}")
            return False
    
    def run_e2e_tests(self):
        """Run E2E tests"""
        print("🧪 Running Manual Entry E2E Tests...")
        
        try:
            result = subprocess.run([
                sys.executable,
                str(self.tests_dir / "e2e" / "test_manual_entry_e2e.py")
            ], cwd=self.project_root)
            
            return result.returncode == 0
        except Exception as e:
            print(f"❌ E2E tests failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints directly"""
        print("🧪 Testing Manual Entry API Endpoints...")
        
        base_url = "http://localhost:8000"
        
        # Test schema validation
        print("  📋 Testing schema validation...")
        validation_tests = [
            {
                "name": "Invalid phone number",
                "payload": '{"phone_number": "invalid", "admin_override": true}',
                "expected_status": 422
            },
            {
                "name": "admin_override false",
                "payload": '{"phone_number": "+1234567890", "admin_override": false}',
                "expected_status": 422
            },
            {
                "name": "Invalid source",
                "payload": '{"phone_number": "+1234567890", "admin_override": true, "source": "invalid"}',
                "expected_status": 422
            },
            {
                "name": "Valid payload (no auth)",
                "payload": '{"phone_number": "+1234567890", "admin_override": true}',
                "expected_status": 401
            }
        ]
        
        all_passed = True
        
        for test in validation_tests:
            try:
                result = subprocess.run([
                    "curl", "-X", "POST", f"{base_url}/contests/1/enter",
                    "-H", "Content-Type: application/json",
                    "-d", test["payload"],
                    "-s", "-w", "%{http_code}"
                ], capture_output=True, text=True)
                
                # Extract status code from curl output
                status_code = int(result.stdout[-3:])
                
                if status_code == test["expected_status"]:
                    print(f"    ✅ {test['name']}: {status_code}")
                else:
                    print(f"    ❌ {test['name']}: Expected {test['expected_status']}, got {status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"    ❌ {test['name']}: Error - {e}")
                all_passed = False
        
        return all_passed
    
    def check_server_status(self):
        """Check if the server is running"""
        print("🔍 Checking server status...")
        
        try:
            result = subprocess.run([
                "curl", "-s", "-f", "http://localhost:8000/docs"
            ], capture_output=True)
            
            if result.returncode == 0:
                print("✅ Server is running")
                return True
            else:
                print("❌ Server is not responding")
                return False
                
        except Exception as e:
            print(f"❌ Server check failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all manual entry tests"""
        print("🚀 Starting Manual Entry Test Suite")
        print("=" * 50)
        
        start_time = time.time()
        results = {}
        
        # Check server status first
        if not self.check_server_status():
            print("⚠️ Server not running - some tests may fail")
        
        # Run validation tests
        results["validation"] = self.run_validation_tests()
        
        # Test API endpoints
        results["api_endpoints"] = self.test_api_endpoints()
        
        # Run integration tests
        results["integration"] = self.run_integration_tests()
        
        # Run E2E tests (may fail without proper auth)
        print("\n⚠️ E2E tests may fail without valid authentication tokens")
        results["e2e"] = self.run_e2e_tests()
        
        # Summary
        duration = time.time() - start_time
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        print("\n" + "=" * 50)
        print("🏁 Manual Entry Test Results")
        print("=" * 50)
        
        for test_type, passed_test in results.items():
            status = "✅ PASSED" if passed_test else "❌ FAILED"
            print(f"{test_type.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} test suites passed")
        print(f"Duration: {duration:.2f} seconds")
        
        if passed == total:
            print("\n🎉 All manual entry tests passed!")
            return True
        else:
            print(f"\n⚠️ {total - passed} test suite(s) failed")
            return False


def main():
    """Main entry point"""
    runner = ManualEntryTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
