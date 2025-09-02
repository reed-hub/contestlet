"""
Integration tests for universal timezone functionality.

Tests timezone preferences for all user roles using existing test infrastructure.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.sponsor_profile import SponsorProfile


@pytest.mark.api
class TestTimezoneIntegration:
    """Test timezone functionality integration with existing test infrastructure"""
    
    def test_timezone_supported_endpoint_unauthenticated(self, client: TestClient):
        """Test getting supported timezones without authentication"""
        response = client.get("/timezone/supported")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "timezones" in data["data"]
        assert len(data["data"]["timezones"]) > 0
        assert data["data"]["default_timezone"] == "UTC"
        assert data["data"]["user_detected_timezone"] is None
    
    def test_timezone_validation_valid(self, client: TestClient):
        """Test timezone validation with valid timezone"""
        response = client.post("/timezone/validate", json={
            "timezone": "America/New_York",
            "timezone_auto_detect": False
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["is_valid"] is True
        assert data["data"]["timezone"] == "America/New_York"
        assert "display_name" in data["data"]
        assert "current_time" in data["data"]
        assert "utc_offset" in data["data"]
    
    def test_timezone_validation_invalid(self, client: TestClient):
        """Test timezone validation with invalid timezone"""
        response = client.post("/timezone/validate", json={
            "timezone": "Invalid/Timezone",
            "timezone_auto_detect": False
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["is_valid"] is False
        assert data["data"]["timezone"] == "Invalid/Timezone"
        assert "error_message" in data["data"]
    
    def test_timezone_validation_null(self, client: TestClient):
        """Test timezone validation with null timezone (system default)"""
        response = client.post("/timezone/validate", json={
            "timezone": None,
            "timezone_auto_detect": True
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["is_valid"] is True
        assert data["data"]["timezone"] == "UTC"
        assert "System default" in data["message"]
    
    def test_timezone_me_requires_authentication(self, client: TestClient):
        """Test that timezone/me endpoint requires authentication"""
        response = client.get("/timezone/me")
        assert response.status_code == 401
        
        response = client.put("/timezone/me", json={
            "timezone": "America/New_York"
        })
        assert response.status_code == 401
    
    def test_profile_update_with_timezone_fields(self, client: TestClient, db_session: Session, user_headers):
        """Test updating profile with timezone via PUT /users/me"""
        # Create a test user in the database
        user = User(
            phone="+15559876543",
            role="user",
            is_verified=True,
            full_name="Test User",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        response = client.put("/users/me", headers=user_headers, json={
            "full_name": "Updated User",
            "timezone": "America/Denver",
            "timezone_auto_detect": False
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["full_name"] == "Updated User"
        assert data["data"]["timezone"] == "America/Denver"
        assert data["data"]["timezone_auto_detect"] is False
    
    def test_profile_get_includes_timezone_fields(self, client: TestClient, db_session: Session, user_headers):
        """Test getting profile includes timezone fields"""
        # Create a test user with timezone settings
        user = User(
            phone="+15559876543",
            role="user",
            is_verified=True,
            full_name="Test User",
            email="test@example.com",
            timezone="Europe/London",
            timezone_auto_detect=False
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        response = client.get("/users/me", headers=user_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "timezone" in data["data"]
        assert "timezone_auto_detect" in data["data"]
        assert data["data"]["timezone"] == "Europe/London"
        assert data["data"]["timezone_auto_detect"] is False
    
    def test_timezone_validation_in_profile_update(self, client: TestClient, user_headers):
        """Test timezone validation when updating via profile endpoint"""
        response = client.put("/users/me", headers=user_headers, json={
            "timezone": "Not/A/Valid/Timezone"
        })
        
        assert response.status_code == 422
        data = response.json()
        assert "Unsupported timezone" in str(data)
    
    def test_sponsor_profile_includes_timezone(self, client: TestClient, db_session: Session, sponsor_headers):
        """Test sponsor profile includes timezone fields"""
        # Create a sponsor user with timezone settings
        user = User(
            phone="+15551234567",
            role="sponsor",
            is_verified=True,
            full_name="Sponsor User",
            email="sponsor@example.com",
            timezone="Asia/Tokyo",
            timezone_auto_detect=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Create sponsor profile
        sponsor_profile = SponsorProfile(
            user_id=user.id,
            company_name="Test Company",
            contact_email="contact@testcompany.com"
        )
        db_session.add(sponsor_profile)
        db_session.commit()
        db_session.refresh(user)
        
        response = client.get("/users/me", headers=sponsor_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "timezone" in data["data"]
        assert "timezone_auto_detect" in data["data"]
        assert data["data"]["timezone"] == "Asia/Tokyo"
        assert data["data"]["timezone_auto_detect"] is True
        assert data["data"]["company_profile"] is not None
    
    def test_timezone_null_uses_system_default(self, client: TestClient, db_session: Session, user_headers):
        """Test that null timezone uses system default (UTC)"""
        # Create user with null timezone
        user = User(
            phone="+15559876543",
            role="user",
            is_verified=True,
            full_name="Test User",
            timezone=None,
            timezone_auto_detect=True
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.get("/users/me", headers=user_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["timezone"] is None
        assert data["data"]["timezone_auto_detect"] is True
    
    def test_timezone_persistence(self, client: TestClient, db_session: Session, user_headers):
        """Test that timezone preferences persist in database"""
        # Create user
        user = User(
            phone="+15559876543",
            role="user",
            is_verified=True,
            full_name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        
        # Update timezone
        response = client.put("/users/me", headers=user_headers, json={
            "timezone": "Australia/Sydney",
            "timezone_auto_detect": False
        })
        assert response.status_code == 200
        
        # Verify persistence by checking database directly
        db_session.refresh(user)
        assert user.timezone == "Australia/Sydney"
        assert user.timezone_auto_detect is False
        
        # Verify via API
        response = client.get("/users/me", headers=user_headers)
        data = response.json()
        assert data["data"]["timezone"] == "Australia/Sydney"
        assert data["data"]["timezone_auto_detect"] is False


@pytest.mark.api
class TestTimezoneValidation:
    """Test timezone validation functionality"""
    
    @pytest.mark.parametrize("timezone,expected_valid", [
        ("UTC", True),
        ("America/New_York", True),
        ("Europe/London", True),
        ("Asia/Tokyo", True),
        ("Invalid/Timezone", False),
        ("Not/A/Timezone", False),
        (None, True),  # Null is valid (system default)
    ])
    def test_timezone_validation_cases(self, client: TestClient, timezone, expected_valid):
        """Test various timezone validation cases"""
        response = client.post("/timezone/validate", json={
            "timezone": timezone,
            "timezone_auto_detect": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_valid"] == expected_valid
    
    @pytest.mark.parametrize("timezone", [
        "UTC",
        "America/New_York", 
        "America/Los_Angeles",
        "Europe/London",
        "Asia/Tokyo",
        None
    ])
    def test_profile_update_timezone_validation(self, client: TestClient, user_headers, timezone):
        """Test profile update accepts valid timezones"""
        response = client.put("/users/me", headers=user_headers, json={
            "timezone": timezone,
            "timezone_auto_detect": True
        })
        
        # Should succeed for valid timezones
        if timezone is None or timezone in ["UTC", "America/New_York", "America/Los_Angeles", "Europe/London", "Asia/Tokyo"]:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["timezone"] == timezone
        else:
            assert response.status_code == 422


@pytest.mark.api
@pytest.mark.integration
class TestTimezoneRoleConsistency:
    """Test timezone functionality consistency across user roles"""
    
    def test_all_roles_can_access_supported_timezones(self, client: TestClient, auth_headers, sponsor_headers, user_headers):
        """Test all roles can access supported timezones endpoint"""
        # Test unauthenticated
        response = client.get("/timezone/supported")
        assert response.status_code == 200
        
        # Test admin
        response = client.get("/timezone/supported", headers=auth_headers)
        assert response.status_code == 200
        
        # Test sponsor
        response = client.get("/timezone/supported", headers=sponsor_headers)
        assert response.status_code == 200
        
        # Test user
        response = client.get("/timezone/supported", headers=user_headers)
        assert response.status_code == 200
    
    def test_all_roles_can_validate_timezones(self, client: TestClient, auth_headers, sponsor_headers, user_headers):
        """Test all roles can validate timezones"""
        test_data = {"timezone": "America/New_York", "timezone_auto_detect": False}
        
        # Test unauthenticated
        response = client.post("/timezone/validate", json=test_data)
        assert response.status_code == 200
        
        # Test admin
        response = client.post("/timezone/validate", json=test_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Test sponsor
        response = client.post("/timezone/validate", json=test_data, headers=sponsor_headers)
        assert response.status_code == 200
        
        # Test user
        response = client.post("/timezone/validate", json=test_data, headers=user_headers)
        assert response.status_code == 200
    
    def test_all_roles_have_timezone_in_profile(self, client: TestClient, db_session: Session, auth_headers, sponsor_headers, user_headers):
        """Test all roles have timezone fields in their profile responses"""
        # Create users for each role
        admin_user = User(phone="+18187958204", role="admin", is_verified=True, timezone="America/New_York")
        sponsor_user = User(phone="+15551234567", role="sponsor", is_verified=True, timezone="Europe/London")
        regular_user = User(phone="+15559876543", role="user", is_verified=True, timezone="Asia/Tokyo")
        
        db_session.add_all([admin_user, sponsor_user, regular_user])
        db_session.commit()
        
        # Create sponsor profile
        sponsor_profile = SponsorProfile(user_id=sponsor_user.id, company_name="Test Company")
        db_session.add(sponsor_profile)
        db_session.commit()
        
        # Test admin profile
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "timezone" in data["data"]
        assert data["data"]["timezone"] == "America/New_York"
        
        # Test sponsor profile
        response = client.get("/users/me", headers=sponsor_headers)
        assert response.status_code == 200
        data = response.json()
        assert "timezone" in data["data"]
        assert data["data"]["timezone"] == "Europe/London"
        
        # Test user profile
        response = client.get("/users/me", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "timezone" in data["data"]
        assert data["data"]["timezone"] == "Asia/Tokyo"

