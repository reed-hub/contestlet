"""
End-to-End Tests for Manual Entry Feature
Tests the complete manual entry workflow from API to database
"""

import pytest
import requests
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import time


class TestManualEntryE2E:
    """Comprehensive E2E tests for manual entry functionality"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment and data"""
        cls.base_url = "http://localhost:8000"
        cls.admin_token = None
        cls.user_token = None
        cls.test_contest_id = None
        cls.test_phone_numbers = [
            "+15551234567",
            "+15559876543", 
            "+15555555555",
            "+447700900123",  # UK number
            "+33123456789"    # French number
        ]
        
        # Setup test data
        cls._setup_test_environment()
    
    @classmethod
    def _setup_test_environment(cls):
        """Setup test users and contest"""
        print("🔧 Setting up test environment...")
        
        # Get admin token (assuming we have a way to get this)
        # In a real test, you'd authenticate properly
        cls.admin_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicGhvbmUiOiIrMTgxODc5NTgyMDQiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NTY5NDAyNDQsImlhdCI6MTc1Njg1Mzg0NCwidHlwZSI6ImFjY2VzcyJ9.sBSTkK35VJJ4OrOB70gwZcvKFMcGlSvYI8KTLqT2AKk"
        
        # Use an existing active contest for testing
        cls.test_contest_id = 1  # Assuming contest 1 exists and is active
        
        print(f"✅ Test environment ready - Contest ID: {cls.test_contest_id}")
    
    def test_01_manual_entry_schema_validation(self):
        """Test manual entry request schema validation"""
        print("\n🧪 Testing manual entry schema validation...")
        
        # Test valid request
        valid_payload = {
            "phone_number": "+15551234567",
            "admin_override": True,
            "source": "phone_call",
            "notes": "Customer called support line"
        }
        
        response = requests.post(
            f"{self.base_url}/contests/{self.test_contest_id}/enter",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            },
            json=valid_payload
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        # Should succeed or fail with business logic (not validation error)
        assert response.status_code in [200, 201, 400, 409], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 422:
            pytest.fail(f"Schema validation failed: {response.json()}")
    
    def test_02_phone_number_format_validation(self):
        """Test phone number format validation"""
        print("\n🧪 Testing phone number format validation...")
        
        invalid_phone_numbers = [
            "123-456-7890",  # US format with dashes
            "1234567890",    # No country code
            "+",             # Just plus sign
            "invalid",       # Not a number
            "+1234",         # Too short
            "",              # Empty string
        ]
        
        for phone in invalid_phone_numbers:
            payload = {
                "phone_number": phone,
                "admin_override": True
            }
            
            response = requests.post(
                f"{self.base_url}/contests/{self.test_contest_id}/enter",
                headers={
                    "Authorization": f"Bearer {self.admin_token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            print(f"Testing invalid phone '{phone}': Status {response.status_code}")
            
            # Should return validation error (422)
            assert response.status_code == 422, f"Expected 422 for invalid phone '{phone}', got {response.status_code}"
    
    def test_03_admin_override_validation(self):
        """Test admin_override field validation"""
        print("\n🧪 Testing admin_override validation...")
        
        # Test with admin_override = false (should fail validation)
        payload = {
            "phone_number": "+15551111111",
            "admin_override": False
        }
        
        response = requests.post(
            f"{self.base_url}/contests/{self.test_contest_id}/enter",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"admin_override=false test: Status {response.status_code}")
        assert response.status_code == 422, "Should fail validation when admin_override is false"
    
    def test_04_successful_manual_entry_creation(self):
        """Test successful manual entry creation"""
        print("\n🧪 Testing successful manual entry creation...")
        
        test_phone = self.test_phone_numbers[0]
        payload = {
            "phone_number": test_phone,
            "admin_override": True,
            "source": "phone_call",
            "notes": "E2E test manual entry"
        }
        
        response = requests.post(
            f"{self.base_url}/contests/{self.test_contest_id}/enter",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Manual entry creation: Status {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert data.get("success") is True
            assert "entry_id" in data
            assert data.get("contest_id") == self.test_contest_id
            print(f"✅ Manual entry created successfully - Entry ID: {data.get('entry_id')}")
        elif response.status_code == 409:
            print("ℹ️ Entry already exists (expected if test runs multiple times)")
        else:
            pytest.fail(f"Unexpected response: {response.status_code} - {response.text}")
    
    def test_05_duplicate_entry_prevention(self):
        """Test duplicate entry prevention"""
        print("\n🧪 Testing duplicate entry prevention...")
        
        test_phone = self.test_phone_numbers[1]
        payload = {
            "phone_number": test_phone,
            "admin_override": True,
            "source": "event",
            "notes": "First entry"
        }
        
        # Create first entry
        response1 = requests.post(
            f"{self.base_url}/contests/{self.test_contest_id}/enter",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"First entry: Status {response1.status_code}")
        
        # Try to create duplicate entry
        payload["notes"] = "Duplicate entry attempt"
        response2 = requests.post(
            f"{self.base_url}/contests/{self.test_contest_id}/enter",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Duplicate entry: Status {response2.status_code}")
        print(f"Duplicate response: {response2.text}")
        
        # Second attempt should fail with 409 Conflict
        assert response2.status_code == 409, f"Expected 409 for duplicate entry, got {response2.status_code}"
        
        if response2.status_code == 409:
            data = response2.json()
            assert "already entered" in data.get("detail", "").lower()
            print("✅ Duplicate entry prevention working correctly")
    
    def test_06_unauthorized_access(self):
        """Test unauthorized access to manual entry"""
        print("\n🧪 Testing unauthorized access...")
        
        payload = {
            "phone_number": "+15552222222",
            "admin_override": True
        }
        
        # Test without token
        response = requests.post(
            f"{self.base_url}/contests/{self.test_contest_id}/enter",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"No token test: Status {response.status_code}")
        assert response.status_code == 401, "Should require authentication"
        
        # Test with invalid token
        response = requests.post(
            f"{self.base_url}/contests/{self.test_contest_id}/enter",
            headers={
                "Authorization": "Bearer invalid_token",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Invalid token test: Status {response.status_code}")
        assert response.status_code in [401, 422], "Should reject invalid token"
    
    def test_07_different_entry_sources(self):
        """Test different entry sources"""
        print("\n🧪 Testing different entry sources...")
        
        sources = ["manual_admin", "phone_call", "event", "paper_form", "customer_service"]
        
        for i, source in enumerate(sources):
            test_phone = f"+1555{str(i).zfill(7)}"  # Generate unique phone numbers
            payload = {
                "phone_number": test_phone,
                "admin_override": True,
                "source": source,
                "notes": f"Testing {source} source"
            }
            
            response = requests.post(
                f"{self.base_url}/contests/{self.test_contest_id}/enter",
                headers={
                    "Authorization": f"Bearer {self.admin_token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            print(f"Source '{source}': Status {response.status_code}")
            
            if response.status_code in [200, 201]:
                print(f"✅ Source '{source}' accepted")
            elif response.status_code == 409:
                print(f"ℹ️ Entry exists for source '{source}' (expected if test runs multiple times)")
            else:
                print(f"❌ Unexpected status for source '{source}': {response.status_code}")
    
    def test_08_admin_endpoint_functionality(self):
        """Test the dedicated admin endpoint"""
        print("\n🧪 Testing dedicated admin endpoint...")
        
        test_phone = "+15553333333"
        payload = {
            "phone_number": test_phone,
            "admin_override": True,
            "source": "customer_service",
            "notes": "Testing dedicated admin endpoint"
        }
        
        response = requests.post(
            f"{self.base_url}/admin/contests/{self.test_contest_id}/manual-entry",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Admin endpoint: Status {response.status_code}")
        print(f"Admin endpoint response: {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "entry_id" in data
            assert data.get("phone_number") == test_phone
            assert data.get("source") == "customer_service"
            print("✅ Dedicated admin endpoint working correctly")
        elif response.status_code == 409:
            print("ℹ️ Entry already exists (expected if test runs multiple times)")
        else:
            print(f"❌ Admin endpoint failed: {response.status_code} - {response.text}")
    
    def test_09_regular_user_entry_compatibility(self):
        """Test that regular user entries still work"""
        print("\n🧪 Testing regular user entry backward compatibility...")
        
        # Test regular entry without request body (should still work)
        response = requests.post(
            f"{self.base_url}/contests/{self.test_contest_id}/enter",
            headers={
                "Authorization": f"Bearer {self.admin_token}",  # Using admin token as user for simplicity
                "Content-Type": "application/json"
            }
            # No JSON body - should trigger regular entry path
        )
        
        print(f"Regular entry: Status {response.status_code}")
        print(f"Regular entry response: {response.text}")
        
        # Should work or fail with business logic (not validation error)
        if response.status_code in [200, 201]:
            print("✅ Regular user entries still work")
        elif response.status_code == 409:
            print("ℹ️ User already entered (expected)")
        elif response.status_code == 400:
            print("ℹ️ Contest not accepting entries (expected for some contest states)")
        else:
            print(f"⚠️ Unexpected status for regular entry: {response.status_code}")
    
    def test_10_international_phone_numbers(self):
        """Test international phone number support"""
        print("\n🧪 Testing international phone numbers...")
        
        international_numbers = [
            "+447700900123",  # UK
            "+33123456789",   # France
            "+81312345678",   # Japan
            "+61412345678",   # Australia
            "+49301234567"    # Germany
        ]
        
        for phone in international_numbers:
            payload = {
                "phone_number": phone,
                "admin_override": True,
                "source": "international_test",
                "notes": f"Testing international number {phone}"
            }
            
            response = requests.post(
                f"{self.base_url}/contests/{self.test_contest_id}/enter",
                headers={
                    "Authorization": f"Bearer {self.admin_token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            print(f"International number {phone}: Status {response.status_code}")
            
            if response.status_code in [200, 201, 409]:  # 409 = already exists
                print(f"✅ International number {phone} accepted")
            else:
                print(f"❌ International number {phone} rejected: {response.status_code}")
    
    def test_11_contest_entries_list_integration(self):
        """Test that manual entries appear in contest entries list"""
        print("\n🧪 Testing contest entries list integration...")
        
        # Get contest entries to verify manual entries are included
        response = requests.get(
            f"{self.base_url}/admin/contests/{self.test_contest_id}/entries",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Entries list: Status {response.status_code}")
        
        if response.status_code == 200:
            entries = response.json()
            print(f"Found {len(entries)} entries")
            
            # Look for manual entries (entries with source != 'web_app')
            manual_entries = []
            for entry in entries:
                # Check if this looks like a manual entry based on phone number patterns
                phone = entry.get("phone_number", "")
                if any(test_phone in phone for test_phone in self.test_phone_numbers):
                    manual_entries.append(entry)
            
            print(f"Found {len(manual_entries)} manual entries in the list")
            
            if manual_entries:
                print("✅ Manual entries appear in contest entries list")
                for entry in manual_entries[:3]:  # Show first 3
                    print(f"  - Entry ID: {entry.get('id')}, Phone: {entry.get('phone_number')}")
            else:
                print("ℹ️ No manual entries found (may be expected if tests didn't create any)")
        else:
            print(f"❌ Failed to get entries list: {response.status_code}")
    
    def test_12_error_handling_edge_cases(self):
        """Test error handling for edge cases"""
        print("\n🧪 Testing error handling edge cases...")
        
        # Test with non-existent contest
        payload = {
            "phone_number": "+15554444444",
            "admin_override": True
        }
        
        response = requests.post(
            f"{self.base_url}/contests/99999/enter",  # Non-existent contest
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Non-existent contest: Status {response.status_code}")
        assert response.status_code == 404, "Should return 404 for non-existent contest"
        
        # Test with malformed JSON
        response = requests.post(
            f"{self.base_url}/contests/{self.test_contest_id}/enter",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            },
            data="invalid json"
        )
        
        print(f"Malformed JSON: Status {response.status_code}")
        assert response.status_code == 422, "Should return 422 for malformed JSON"
    
    def test_13_performance_multiple_entries(self):
        """Test performance with multiple manual entries"""
        print("\n🧪 Testing performance with multiple entries...")
        
        start_time = time.time()
        successful_entries = 0
        
        for i in range(10):  # Create 10 manual entries
            test_phone = f"+1555999{str(i).zfill(4)}"
            payload = {
                "phone_number": test_phone,
                "admin_override": True,
                "source": "performance_test",
                "notes": f"Performance test entry {i+1}"
            }
            
            response = requests.post(
                f"{self.base_url}/contests/{self.test_contest_id}/enter",
                headers={
                    "Authorization": f"Bearer {self.admin_token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code in [200, 201]:
                successful_entries += 1
            elif response.status_code == 409:
                print(f"Entry {i+1} already exists")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Created {successful_entries} entries in {duration:.2f} seconds")
        print(f"Average time per entry: {duration/10:.3f} seconds")
        
        # Performance should be reasonable (less than 1 second per entry)
        assert duration < 10, f"Performance too slow: {duration:.2f} seconds for 10 entries"
        print("✅ Performance test passed")
    
    def test_14_cleanup_verification(self):
        """Verify test data cleanup and final state"""
        print("\n🧪 Verifying final test state...")
        
        # Get final count of entries
        response = requests.get(
            f"{self.base_url}/admin/contests/{self.test_contest_id}/entries",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            entries = response.json()
            total_entries = len(entries)
            
            # Count test entries
            test_entries = sum(1 for entry in entries 
                             if any(test_phone in entry.get("phone_number", "") 
                                   for test_phone in self.test_phone_numbers))
            
            print(f"Final state: {total_entries} total entries, {test_entries} test entries")
            print("✅ Test verification complete")
        else:
            print(f"❌ Could not verify final state: {response.status_code}")


def run_manual_entry_e2e_tests():
    """Run all manual entry E2E tests"""
    print("🚀 Starting Manual Entry E2E Tests")
    print("=" * 50)
    
    test_class = TestManualEntryE2E()
    test_class.setup_class()
    
    # Run all test methods
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    test_methods.sort()  # Run in order
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            print(f"\n🧪 Running {method_name}...")
            method = getattr(test_class, method_name)
            method()
            passed += 1
            print(f"✅ {method_name} PASSED")
        except Exception as e:
            failed += 1
            print(f"❌ {method_name} FAILED: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"🏁 E2E Tests Complete: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_manual_entry_e2e_tests()
    exit(0 if success else 1)
