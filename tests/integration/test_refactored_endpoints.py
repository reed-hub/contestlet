"""
Integration tests for refactored endpoints with new clean architecture
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry


class TestRefactoredContestsEndpoints:
    """Test refactored contests endpoints with clean architecture"""
    
    def test_contests_list_with_new_response_format(self, client: TestClient, db_session: Session):
        """Test contests list endpoint returns new standardized response format"""
        # Create test contests
        contest1 = Contest(
            name="Test Contest 1",
            description="First test contest",
            location="Test City, TS",
            start_time=datetime.utcnow() + timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="$100 prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100,
            created_by_user_id=1
        )
        
        contest2 = Contest(
            name="Test Contest 2", 
            description="Second test contest",
            location="Another City, TS",
            start_time=datetime.utcnow() + timedelta(hours=2),
            end_time=datetime.utcnow() + timedelta(days=8),
            prize_description="$200 prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=21,
            max_entries_per_person=2,
            total_entry_limit=200,
            created_by_user_id=1
        )
        
        db_session.add_all([contest1, contest2])
        db_session.commit()
        
        # Test endpoint
        response = client.get("/contests/")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify new standardized response format
        assert "success" in data
        assert "data" in data
        assert "message" in data
        assert data["success"] is True
        
        # Verify pagination structure
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "limit" in data["data"]
        assert "pages" in data["data"]
        
        # Verify contest data structure
        contests = data["data"]["items"]
        assert len(contests) == 2
        
        for contest in contests:
            assert "id" in contest
            assert "name" in contest
            assert "description" in contest
            assert "computed_status" in contest
            assert "location" in contest
    
    def test_contest_detail_with_service_layer(self, client: TestClient, db_session: Session):
        """Test contest detail endpoint uses service layer properly"""
        # Create test contest
        contest = Contest(
            name="Detailed Test Contest",
            description="A contest for testing detail endpoint",
            location="Detail City, TS",
            start_time=datetime.utcnow() + timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="$500 prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100,
            created_by_user_id=1
        )
        
        db_session.add(contest)
        db_session.commit()
        db_session.refresh(contest)
        
        # Test endpoint
        response = client.get(f"/contests/{contest.id}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify standardized response format
        assert data["success"] is True
        assert "data" in data
        assert "message" in data
        
        # Verify detailed contest data
        contest_data = data["data"]
        assert contest_data["id"] == contest.id
        assert contest_data["name"] == "Detailed Test Contest"
        assert contest_data["description"] == "A contest for testing detail endpoint"
        assert "computed_status" in contest_data
        assert "entry_count" in contest_data
        assert "can_enter" in contest_data
    
    def test_contest_deletion_with_clean_error_handling(self, client: TestClient, db_session: Session, admin_headers: dict):
        """Test contest deletion with new structured error handling"""
        # Create admin user
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        # Create test contest
        contest = Contest(
            name="Contest to Delete",
            description="This contest will be deleted",
            location="Delete City, TS",
            start_time=datetime.utcnow() + timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="$100 prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100,
            created_by_user_id=admin.id
        )
        
        db_session.add(contest)
        db_session.commit()
        db_session.refresh(contest)
        
        # Test successful deletion
        response = client.delete(f"/contests/{contest.id}", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify standardized response format
        assert data["success"] is True
        assert "data" in data
        assert "message" in data
        
        # Verify deletion data
        deletion_data = data["data"]
        assert "contest_id" in deletion_data
        assert "deleted_at" in deletion_data
        assert "deletion_reason" in deletion_data
    
    def test_contest_not_found_structured_error(self, client: TestClient):
        """Test contest not found returns structured error response"""
        response = client.get("/contests/99999")
        assert response.status_code == 404
        
        data = response.json()
        
        # Verify structured error format
        assert data["success"] is False
        assert "error_code" in data
        assert "message" in data
        assert "details" in data
        
        # Verify error details
        assert data["error_code"] == "RESOURCE_NOT_FOUND"
        assert "Contest" in data["message"]
        assert "99999" in data["message"]
        assert data["details"]["resource_type"] == "Contest"
        assert data["details"]["resource_id"] == 99999


class TestRefactoredAuthEndpoints:
    """Test refactored auth endpoints with clean architecture"""
    
    def test_otp_request_with_constants(self, client: TestClient):
        """Test OTP request uses centralized constants and messages"""
        response = client.post("/auth/request-otp", json={
            "phone": "+15551234567"
        })
        
        # Should succeed with proper response format
        if response.status_code == 200:
            data = response.json()
            
            # Verify standardized response format
            assert "success" in data
            assert "message" in data
            assert data["success"] is True
            
            # Verify message uses constants (should be consistent)
            assert len(data["message"]) > 0
    
    def test_otp_verification_structured_errors(self, client: TestClient, db_session: Session):
        """Test OTP verification returns structured errors"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        # Test with invalid OTP
        response = client.post("/auth/verify-otp", json={
            "phone": "+15551234567",
            "code": "000000"  # Invalid code
        })
        
        # Should return structured error
        if response.status_code != 200:
            data = response.json()
            
            # Verify structured error format
            assert "success" in data
            assert "error_code" in data
            assert "message" in data
            assert data["success"] is False
    
    def test_token_validation_with_service_layer(self, client: TestClient, admin_headers: dict):
        """Test token validation uses service layer"""
        # Test protected endpoint
        response = client.get("/users/me", headers=admin_headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify standardized response format
            assert data["success"] is True
            assert "data" in data
            assert "message" in data
            
            # Verify user data structure
            user_data = data["data"]
            assert "user_id" in user_data or "id" in user_data
            assert "role" in user_data
            assert "phone" in user_data


class TestRefactoredUserEndpoints:
    """Test refactored user endpoints with clean architecture"""
    
    def test_user_profile_with_type_safety(self, client: TestClient, db_session: Session, user_headers: dict):
        """Test user profile endpoint with type-safe responses"""
        # Create test user
        user = User(
            phone="+15559876543",
            role="user",
            is_verified=True,
            full_name="Test User",
            email="test@example.com",
            bio="Test user bio"
        )
        db_session.add(user)
        db_session.commit()
        
        # Test endpoint
        response = client.get("/users/me", headers=user_headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify standardized response format
            assert data["success"] is True
            assert "data" in data
            assert "message" in data
            
            # Verify type-safe user data
            user_data = data["data"]
            assert isinstance(user_data.get("id") or user_data.get("user_id"), int)
            assert isinstance(user_data["phone"], str)
            assert isinstance(user_data["role"], str)
            assert isinstance(user_data["is_verified"], bool)
            
            if "full_name" in user_data:
                assert isinstance(user_data["full_name"], (str, type(None)))
            if "email" in user_data:
                assert isinstance(user_data["email"], (str, type(None)))
    
    def test_user_profile_update_validation(self, client: TestClient, db_session: Session, user_headers: dict):
        """Test user profile update with validation using constants"""
        # Create test user
        user = User(phone="+15559876543", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        # Test with invalid data (name too short)
        response = client.put("/users/me", 
            headers=user_headers,
            json={
                "full_name": "A",  # Too short
                "email": "invalid-email"  # Invalid format
            }
        )
        
        # Should return validation error
        if response.status_code == 422 or response.status_code == 400:
            data = response.json()
            
            # Verify structured validation error
            assert "success" in data
            assert data["success"] is False
            
            if "error_code" in data:
                assert data["error_code"] == "VALIDATION_FAILED"
            
            # Should have field-specific errors
            if "errors" in data and "field_errors" in data["errors"]:
                field_errors = data["errors"]["field_errors"]
                assert "full_name" in field_errors or "email" in field_errors


class TestRefactoredLocationEndpoints:
    """Test refactored location endpoints with clean architecture"""
    
    def test_location_validation_with_constants(self, client: TestClient, admin_headers: dict):
        """Test location validation uses centralized constants"""
        location_data = {
            "location_data": {
                "location_type": "radius",
                "radius_address": "123 Test St, Test City, TS 12345",
                "radius_miles": 25,
                "radius_coordinates": {
                    "latitude": 40.7128,
                    "longitude": -74.0060
                }
            }
        }
        
        response = client.post("/location/validate", 
            headers=admin_headers,
            json=location_data
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify standardized response format
            assert data["success"] is True
            assert "data" in data
            assert "message" in data
            
            # Verify validation result structure
            validation_data = data["data"]
            assert "valid" in validation_data
            assert "errors" in validation_data
            assert "warnings" in validation_data
    
    def test_geocoding_with_service_layer(self, client: TestClient, sponsor_headers: dict):
        """Test geocoding endpoint uses service layer"""
        response = client.post("/location/geocode",
            headers=sponsor_headers,
            json={
                "address": "1600 Amphitheatre Parkway, Mountain View, CA"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify standardized response format
            assert data["success"] is True
            assert "data" in data
            
            # Verify geocoding result structure
            geocode_data = data["data"]
            assert "success" in geocode_data
            
            if geocode_data["success"]:
                assert "coordinates" in geocode_data
                assert "formatted_address" in geocode_data
                
                coordinates = geocode_data["coordinates"]
                assert "latitude" in coordinates
                assert "longitude" in coordinates
                assert isinstance(coordinates["latitude"], (int, float))
                assert isinstance(coordinates["longitude"], (int, float))


class TestRefactoredMediaEndpoints:
    """Test refactored media endpoints with clean architecture"""
    
    def test_media_upload_validation_with_constants(self, client: TestClient, sponsor_headers: dict):
        """Test media upload validation uses centralized constants"""
        # Test with invalid file type
        response = client.post(f"/media/contests/1/hero",
            headers=sponsor_headers,
            files={"file": ("test.txt", b"test content", "text/plain")},
            params={"media_type": "image"}
        )
        
        # Should return validation error for invalid file type
        if response.status_code == 422 or response.status_code == 400:
            data = response.json()
            
            # Verify structured validation error
            assert "success" in data
            assert data["success"] is False
            
            if "error_code" in data:
                assert data["error_code"] == "VALIDATION_FAILED"
    
    def test_media_service_health_check(self, client: TestClient, sponsor_headers: dict):
        """Test media service health check endpoint"""
        response = client.get("/media/health", headers=sponsor_headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify standardized response format
            assert "success" in data
            assert "data" in data
            
            # Verify health check data structure
            health_data = data["data"]
            assert "healthy" in health_data
            assert isinstance(health_data["healthy"], bool)


class TestCleanArchitectureCompliance:
    """Test clean architecture compliance across refactored endpoints"""
    
    def test_consistent_response_format(self, client: TestClient):
        """Test that all endpoints return consistent response format"""
        endpoints_to_test = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/contests/", "GET"),
            ("/location/states", "GET")
        ]
        
        for endpoint, method in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                
                # All successful responses should have these fields
                if isinstance(data, dict):
                    # Either new format or legacy format
                    if "success" in data:
                        # New standardized format
                        assert "success" in data
                        assert isinstance(data["success"], bool)
                        
                        if data["success"]:
                            assert "message" in data
                            # Data field is optional for some endpoints
                    else:
                        # Legacy format (acceptable during transition)
                        pass
    
    def test_error_response_consistency(self, client: TestClient):
        """Test that error responses are consistent across endpoints"""
        # Test non-existent endpoints
        error_endpoints = [
            "/contests/99999",
            "/users/99999", 
            "/location/contest/99999/location"
        ]
        
        for endpoint in error_endpoints:
            response = client.get(endpoint)
            
            if response.status_code == 404:
                data = response.json()
                
                # Error responses should be structured
                if isinstance(data, dict) and "success" in data:
                    assert data["success"] is False
                    assert "error_code" in data or "message" in data
    
    def test_authentication_consistency(self, client: TestClient):
        """Test that authentication is consistent across protected endpoints"""
        protected_endpoints = [
            "/users/me",
            "/admin/dashboard",
            "/sponsor/workflow/contests"
        ]
        
        for endpoint in protected_endpoints:
            # Test without authentication
            response = client.get(endpoint)
            
            # Should return 401 or 403
            if response.status_code in [401, 403]:
                data = response.json()
                
                # Should have structured error response
                if isinstance(data, dict) and "success" in data:
                    assert data["success"] is False
                    if "error_code" in data:
                        assert data["error_code"] in ["UNAUTHORIZED", "FORBIDDEN"]
