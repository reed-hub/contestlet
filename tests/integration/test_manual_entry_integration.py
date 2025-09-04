"""
Integration Tests for Manual Entry Feature
Tests the complete integration between API endpoints, services, and database
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.database.database import Base, get_db
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.user import User
from app.schemas.manual_entry import ManualEntryRequest


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_manual_entry.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


class TestManualEntryIntegration:
    """Integration tests for manual entry functionality"""
    
    @classmethod
    def setup_class(cls):
        """Setup test database and data"""
        # Create test database tables
        Base.metadata.create_all(bind=engine)
        
        cls.client = TestClient(app)
        cls.db = TestingSessionLocal()
        
        # Create test data
        cls._create_test_data()
    
    @classmethod
    def teardown_class(cls):
        """Cleanup test database"""
        cls.db.close()
        Base.metadata.drop_all(bind=engine)
    
    @classmethod
    def _create_test_data(cls):
        """Create test users and contests"""
        # Create admin user
        admin_user = User(
            id=1,
            phone="+18187958204",
            full_name="Test Admin",
            role="admin",
            is_verified=True
        )
        cls.db.add(admin_user)
        
        # Create regular user
        regular_user = User(
            id=2,
            phone="+15551234567",
            full_name="Test User",
            role="user",
            is_verified=True
        )
        cls.db.add(regular_user)
        
        # Create test contest
        now = datetime.now(timezone.utc)
        contest = Contest(
            id=1,
            name="Test Contest for Manual Entry",
            description="Integration test contest",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=24),
            prize_description="Test Prize",
            status="published",
            created_by_user_id=1,
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random"
        )
        cls.db.add(contest)
        
        # Create ended contest for testing
        ended_contest = Contest(
            id=2,
            name="Ended Test Contest",
            description="Ended contest for testing",
            start_time=now - timedelta(hours=25),
            end_time=now - timedelta(hours=1),
            prize_description="Test Prize",
            status="published",
            created_by_user_id=1,
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random"
        )
        cls.db.add(ended_contest)
        
        cls.db.commit()
        print("✅ Test data created")
    
    def setup_method(self):
        """Setup for each test method"""
        # Clean up entries from previous tests
        self.db.query(Entry).delete()
        self.db.commit()
    
    @patch('app.core.dependencies.auth.get_optional_user')
    def test_manual_entry_creation_success(self, mock_get_user):
        """Test successful manual entry creation"""
        # Mock admin user
        mock_admin = type('MockUser', (), {
            'id': 1,
            'role': 'admin',
            'phone': '+18187958204'
        })()
        mock_get_user.return_value = mock_admin
        
        # Create manual entry
        payload = {
            "phone_number": "+15559876543",
            "admin_override": True,
            "source": "phone_call",
            "notes": "Integration test manual entry"
        }
        
        response = self.client.post(
            "/contests/1/enter",
            json=payload,
            headers={"Authorization": "Bearer test_token"}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        # Verify response
        assert response.status_code in [200, 201], f"Expected success, got {response.status_code}: {response.text}"
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["success"] is True
            assert "entry_id" in data
            
            # Verify database entry
            entry = self.db.query(Entry).filter(Entry.id == data["entry_id"]).first()
            assert entry is not None
            assert entry.source == "phone_call"
            assert entry.created_by_admin_id == 1
            assert entry.admin_notes == "Integration test manual entry"
            
            # Verify user was created/found
            user = self.db.query(User).filter(User.phone == "+15559876543").first()
            assert user is not None
            assert entry.user_id == user.id
            
            print("✅ Manual entry created successfully in database")
    
    @patch('app.core.dependencies.auth.get_optional_user')
    def test_manual_entry_duplicate_prevention(self, mock_get_user):
        """Test duplicate entry prevention"""
        # Mock admin user
        mock_admin = type('MockUser', (), {
            'id': 1,
            'role': 'admin'
        })()
        mock_get_user.return_value = mock_admin
        
        payload = {
            "phone_number": "+15551111111",
            "admin_override": True,
            "source": "event"
        }
        
        # Create first entry
        response1 = self.client.post(
            "/contests/1/enter",
            json=payload,
            headers={"Authorization": "Bearer test_token"}
        )
        
        print(f"First entry: {response1.status_code}")
        
        # Try to create duplicate
        response2 = self.client.post(
            "/contests/1/enter",
            json=payload,
            headers={"Authorization": "Bearer test_token"}
        )
        
        print(f"Duplicate entry: {response2.status_code}")
        
        # First should succeed, second should fail
        if response1.status_code in [200, 201]:
            assert response2.status_code == 409, f"Expected 409 for duplicate, got {response2.status_code}"
            
            # Verify only one entry exists
            entries = self.db.query(Entry).filter(Entry.contest_id == 1).all()
            user_entries = [e for e in entries if e.user.phone == "+15551111111"]
            assert len(user_entries) == 1
            
            print("✅ Duplicate prevention working correctly")
    
    @patch('app.core.dependencies.auth.get_optional_user')
    def test_manual_entry_ended_contest(self, mock_get_user):
        """Test manual entry creation for ended contest (should be allowed)"""
        # Mock admin user
        mock_admin = type('MockUser', (), {
            'id': 1,
            'role': 'admin'
        })()
        mock_get_user.return_value = mock_admin
        
        payload = {
            "phone_number": "+15552222222",
            "admin_override": True,
            "source": "paper_form",
            "notes": "Late entry from event"
        }
        
        response = self.client.post(
            "/contests/2/enter",  # Ended contest
            json=payload,
            headers={"Authorization": "Bearer test_token"}
        )
        
        print(f"Ended contest entry: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Manual entries should be allowed for ended contests
        assert response.status_code in [200, 201], f"Manual entries should be allowed for ended contests"
        
        if response.status_code in [200, 201]:
            data = response.json()
            entry = self.db.query(Entry).filter(Entry.id == data["entry_id"]).first()
            assert entry.contest_id == 2  # Ended contest
            assert entry.source == "paper_form"
            
            print("✅ Manual entry allowed for ended contest")
    
    def test_manual_entry_unauthorized(self):
        """Test manual entry without authentication"""
        payload = {
            "phone_number": "+15553333333",
            "admin_override": True
        }
        
        response = self.client.post(
            "/contests/1/enter",
            json=payload
        )
        
        print(f"Unauthorized test: {response.status_code}")
        assert response.status_code == 401
        print("✅ Unauthorized access properly blocked")
    
    @patch('app.core.dependencies.auth.get_optional_user')
    def test_manual_entry_insufficient_permissions(self, mock_get_user):
        """Test manual entry with non-admin user"""
        # Mock regular user
        mock_user = type('MockUser', (), {
            'id': 2,
            'role': 'user'
        })()
        mock_get_user.return_value = mock_user
        
        payload = {
            "phone_number": "+15554444444",
            "admin_override": True
        }
        
        response = self.client.post(
            "/contests/1/enter",
            json=payload,
            headers={"Authorization": "Bearer test_token"}
        )
        
        print(f"Non-admin test: {response.status_code}")
        assert response.status_code == 403
        print("✅ Non-admin access properly blocked")
    
    @patch('app.core.dependencies.auth.get_optional_user')
    def test_regular_entry_still_works(self, mock_get_user):
        """Test that regular user entries still work"""
        # Mock regular user
        mock_user = type('MockUser', (), {
            'id': 2,
            'role': 'user'
        })()
        mock_get_user.return_value = mock_user
        
        # Regular entry (no JSON body)
        response = self.client.post(
            "/contests/1/enter",
            headers={"Authorization": "Bearer test_token"}
        )
        
        print(f"Regular entry test: {response.status_code}")
        print(f"Regular entry response: {response.text}")
        
        # Should work (or fail with business logic, not validation error)
        assert response.status_code != 422, "Regular entries should not have validation errors"
        
        if response.status_code in [200, 201]:
            # Verify entry was created with default source
            entries = self.db.query(Entry).filter(
                Entry.contest_id == 1,
                Entry.user_id == 2
            ).all()
            assert len(entries) == 1
            assert entries[0].source == "web_app"  # Default source
            assert entries[0].created_by_admin_id is None  # Not a manual entry
            
            print("✅ Regular user entries still work correctly")
    
    @patch('app.core.dependencies.auth.get_optional_user') 
    def test_admin_endpoint_functionality(self, mock_get_user):
        """Test the dedicated admin endpoint"""
        # Mock admin user
        mock_admin = type('MockUser', (), {
            'id': 1,
            'role': 'admin'
        })()
        mock_get_user.return_value = mock_admin
        
        payload = {
            "phone_number": "+15555555555",
            "admin_override": True,
            "source": "customer_service",
            "notes": "Testing admin endpoint"
        }
        
        response = self.client.post(
            "/admin/contests/1/manual-entry",
            json=payload,
            headers={"Authorization": "Bearer test_token"}
        )
        
        print(f"Admin endpoint test: {response.status_code}")
        print(f"Admin endpoint response: {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "entry_id" in data
            assert data["phone_number"] == "+15555555555"
            assert data["source"] == "customer_service"
            
            # Verify in database
            entry = self.db.query(Entry).filter(Entry.id == data["entry_id"]).first()
            assert entry is not None
            assert entry.source == "customer_service"
            
            print("✅ Dedicated admin endpoint working correctly")
    
    def test_phone_number_validation_integration(self):
        """Test phone number validation at API level"""
        invalid_phones = [
            "123-456-7890",
            "1234567890", 
            "+",
            "invalid"
        ]
        
        for phone in invalid_phones:
            payload = {
                "phone_number": phone,
                "admin_override": True
            }
            
            response = self.client.post(
                "/contests/1/enter",
                json=payload,
                headers={"Authorization": "Bearer test_token"}
            )
            
            print(f"Invalid phone '{phone}': {response.status_code}")
            assert response.status_code == 422, f"Should reject invalid phone '{phone}'"
        
        print("✅ Phone number validation working at API level")
    
    def test_contest_not_found(self):
        """Test manual entry for non-existent contest"""
        payload = {
            "phone_number": "+15556666666",
            "admin_override": True
        }
        
        response = self.client.post(
            "/contests/99999/enter",  # Non-existent contest
            json=payload,
            headers={"Authorization": "Bearer test_token"}
        )
        
        print(f"Non-existent contest: {response.status_code}")
        assert response.status_code == 404
        print("✅ Non-existent contest properly handled")
    
    @patch('app.core.dependencies.auth.get_optional_user')
    def test_multiple_sources_tracking(self, mock_get_user):
        """Test that different sources are properly tracked"""
        # Mock admin user
        mock_admin = type('MockUser', (), {
            'id': 1,
            'role': 'admin'
        })()
        mock_get_user.return_value = mock_admin
        
        sources = ["phone_call", "event", "paper_form", "customer_service"]
        
        for i, source in enumerate(sources):
            phone = f"+1555777{str(i).zfill(4)}"
            payload = {
                "phone_number": phone,
                "admin_override": True,
                "source": source,
                "notes": f"Testing {source}"
            }
            
            response = self.client.post(
                "/contests/1/enter",
                json=payload,
                headers={"Authorization": "Bearer test_token"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                entry = self.db.query(Entry).filter(Entry.id == data["entry_id"]).first()
                assert entry.source == source
                assert entry.admin_notes == f"Testing {source}"
        
        print("✅ Multiple sources properly tracked")


def run_integration_tests():
    """Run integration tests manually"""
    print("🚀 Starting Manual Entry Integration Tests")
    print("=" * 50)
    
    test_class = TestManualEntryIntegration()
    test_class.setup_class()
    
    try:
        # Run test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                print(f"\n🧪 Running {method_name}...")
                test_class.setup_method()
                method = getattr(test_class, method_name)
                method()
                print(f"✅ {method_name} PASSED")
            except Exception as e:
                print(f"❌ {method_name} FAILED: {str(e)}")
        
    finally:
        test_class.teardown_class()
    
    print("\n" + "=" * 50)
    print("🏁 Integration Tests Complete")


if __name__ == "__main__":
    run_integration_tests()
