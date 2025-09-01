"""
Comprehensive tests for all API endpoints
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry


class TestPublicEndpoints:
    """Test public API endpoints that don't require authentication"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert "environment" in data
        assert "version" in data
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "environment" in data
        assert "vercel_env" in data
        assert "git_branch" in data
        assert data["status"] == "healthy"
    
    def test_manifest_endpoint(self, client: TestClient):
        """Test PWA manifest endpoint"""
        response = client.get("/manifest.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "short_name" in data
        assert "description" in data
        assert "start_url" in data
        assert "display" in data
        assert data["name"] == "Contestlet"
    
    def test_active_contests_endpoint(self, client: TestClient, db_session: Session):
        """Test active contests listing"""
        # Create active contest
        contest = Contest(
            name="Active Contest",
            description="An active contest for testing",
            status="active",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get("/contests/active")
        assert response.status_code == 200
        
        data = response.json()
        assert "contests" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["contests"]) >= 1
    
    def test_contest_detail_endpoint(self, client: TestClient, db_session: Session):
        """Test individual contest detail"""
        contest = Contest(
            name="Detail Test Contest",
            description="Contest for testing detail view",
            status="active",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="Test prize worth $100",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get(f"/contests/{contest.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == contest.id
        assert data["name"] == "Detail Test Contest"
        assert data["status"] == "active"
        assert "is_draft" in data
        assert "is_published" in data
    
    def test_nearby_contests_endpoint(self, client: TestClient, db_session: Session):
        """Test nearby contests endpoint"""
        # Create contest with location
        contest = Contest(
            name="Nearby Contest",
            description="Contest for testing nearby search",
            status="active",
            location="Los Angeles, CA 90210",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get("/contests/nearby?lat=34.0522&lng=-118.2437&radius=50")
        assert response.status_code == 200
        
        data = response.json()
        assert "contests" in data
        assert "total" in data
    
    def test_location_states_endpoint(self, client: TestClient):
        """Test US states endpoint"""
        response = client.get("/location/states")
        assert response.status_code == 200
        
        data = response.json()
        assert "states" in data
        assert len(data["states"]) == 50  # US states
        
        # Check structure of first state
        first_state = data["states"][0]
        assert "code" in first_state
        assert "name" in first_state


class TestAuthenticationEndpoints:
    """Test authentication-related endpoints"""
    
    def test_request_otp_endpoint(self, client: TestClient, db_session: Session):
        """Test OTP request endpoint"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=False)
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/auth/request-otp", json={"phone": "+15551234567"})
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "retry_after" in data
    
    def test_verify_otp_endpoint(self, client: TestClient, db_session: Session):
        """Test OTP verification endpoint"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=False)
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/auth/verify-otp", json={
            "phone": "+15551234567",
            "code": "123456"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
    
    def test_refresh_token_endpoint(self, client: TestClient, db_session: Session):
        """Test token refresh endpoint"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        # This would require a valid refresh token in real scenario
        # For now, test the endpoint exists and handles invalid tokens
        response = client.post("/auth/refresh", json={"refresh_token": "invalid_token"})
        assert response.status_code in [400, 401]  # Should reject invalid token


class TestUserEndpoints:
    """Test user-related endpoints"""
    
    def test_user_profile_endpoint(self, client: TestClient, db_session: Session, user_headers: dict):
        """Test user profile endpoint"""
        # Create test user
        user = User(
            phone="+15559876543", 
            role="user", 
            is_verified=True,
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.get("/users/me", headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["phone"] == "+15559876543"
        assert data["role"] == "user"
        assert data["is_verified"] is True
    
    def test_update_user_profile_endpoint(self, client: TestClient, db_session: Session, user_headers: dict):
        """Test user profile update endpoint"""
        # Create test user
        user = User(phone="+15559876543", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        update_data = {
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com"
        }
        
        response = client.put("/users/me", json=update_data, headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "User"
        assert data["email"] == "updated@example.com"
    
    def test_user_active_entries_endpoint(self, client: TestClient, db_session: Session, user_headers: dict):
        """Test user's active entries endpoint"""
        # Create test user and contest
        user = User(phone="+15559876543", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        contest = Contest(
            name="User Entry Contest",
            description="Contest for testing user entries",
            status="active",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        # Create entry
        entry = Entry(contest_id=contest.id, user_id=user.id, is_valid=True)
        db_session.add(entry)
        db_session.commit()
        
        response = client.get("/user/entries/active", headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        assert data[0]["contest_id"] == contest.id


class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    def test_admin_contests_endpoint(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test admin contests listing"""
        # Create admin user
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        # Create test contest
        contest = Contest(
            name="Admin Test Contest",
            description="Contest for admin testing",
            status="upcoming",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get("/admin/contests/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert len(data["data"]) >= 1
    
    def test_admin_contest_detail_endpoint(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test admin contest detail endpoint"""
        # Create admin user
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        contest = Contest(
            name="Admin Detail Contest",
            description="Contest for admin detail testing",
            status="upcoming",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get(f"/admin/contests/{contest.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == contest.id
        assert data["name"] == "Admin Detail Contest"
    
    def test_admin_notifications_endpoint(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test admin notifications endpoint"""
        # Create admin user
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        response = client.get("/admin/notifications/?limit=10", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "data" in data
    
    def test_admin_users_endpoint(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test admin users listing endpoint"""
        # Create admin user
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        response = client.get("/admin/users", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1  # Should include at least the admin user


class TestSponsorWorkflowEndpoints:
    """Test sponsor workflow endpoints"""
    
    def test_create_draft_contest_endpoint(self, client: TestClient, db_session: Session, sponsor_headers: dict):
        """Test sponsor draft contest creation"""
        # Create sponsor user
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add(sponsor)
        db_session.commit()
        
        contest_data = {
            "name": "Sponsor Draft Contest",
            "description": "Draft contest created by sponsor",
            "location": "Test City, TS 12345",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=8)).isoformat(),
            "prize_description": "Test prize worth $100",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": {
                "eligibility": "Must be 18 or older",
                "entry_requirements": "Valid phone number required",
                "prize_details": "Prize worth $100",
                "winner_selection": "Random selection",
                "contact_info": "contest@example.com"
            }
        }
        
        response = client.post("/sponsor/workflow/contests/draft", json=contest_data, headers=sponsor_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Sponsor Draft Contest"
        assert data["status"] == "draft"
    
    def test_sponsor_drafts_listing_endpoint(self, client: TestClient, db_session: Session, sponsor_headers: dict):
        """Test sponsor drafts listing"""
        # Create sponsor user
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add(sponsor)
        db_session.commit()
        
        # Create draft contest
        contest = Contest(
            name="Draft for Listing",
            description="Draft contest for listing test",
            status="draft",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor.id,
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get("/sponsor/workflow/contests/drafts", headers=sponsor_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["contests"]) >= 1
        assert data["contests"][0]["status"] == "draft"
    
    def test_sponsor_pending_contests_endpoint(self, client: TestClient, db_session: Session, sponsor_headers: dict):
        """Test sponsor pending contests listing"""
        # Create sponsor user
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add(sponsor)
        db_session.commit()
        
        # Create pending contest
        contest = Contest(
            name="Pending Contest",
            description="Contest pending approval",
            status="awaiting_approval",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor.id,
            submitted_at=datetime.utcnow(),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get("/sponsor/workflow/contests/pending", headers=sponsor_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["contests"]) >= 1
        assert data["contests"][0]["status"] == "awaiting_approval"


class TestAdminApprovalEndpoints:
    """Test admin approval workflow endpoints"""
    
    def test_approval_queue_endpoint(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test admin approval queue"""
        # Create admin and sponsor users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add_all([admin, sponsor])
        db_session.commit()
        
        # Create contest awaiting approval
        contest = Contest(
            name="Queue Test Contest",
            description="Contest for approval queue testing",
            status="awaiting_approval",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor.id,
            submitted_at=datetime.utcnow(),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get("/admin/approval/queue", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "contests" in data
        assert len(data["contests"]) >= 1
    
    def test_approval_statistics_endpoint(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test admin approval statistics"""
        # Create admin user
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        response = client.get("/admin/approval/statistics", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_pending" in data
        assert "total_approved_today" in data
        assert "total_rejected_today" in data
    
    def test_approval_audit_trail_endpoint(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test admin approval audit trail"""
        # Create admin user
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        response = client.get("/admin/approval/audit-trail", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "audit_records" in data


class TestLocationEndpoints:
    """Test location-related endpoints"""
    
    def test_location_validation_endpoint(self, client: TestClient):
        """Test location validation endpoint"""
        location_data = {
            "address": "1600 Amphitheatre Parkway, Mountain View, CA 94043"
        }
        
        response = client.post("/location/validate", json=location_data)
        # This might return 422 if geocoding is not configured
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert "valid" in data
    
    def test_location_geocode_endpoint(self, client: TestClient):
        """Test location geocoding endpoint"""
        response = client.get("/location/geocode?address=Los Angeles, CA")
        # This might return 422 if geocoding is not configured
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert "lat" in data
            assert "lng" in data


class TestMediaEndpoints:
    """Test media-related endpoints"""
    
    def test_media_upload_endpoint(self, client: TestClient, auth_headers: dict):
        """Test media upload endpoint"""
        # This would require actual file upload in real scenario
        # For now, test that endpoint exists and requires auth
        response = client.post("/media/upload", headers=auth_headers)
        # Should fail without proper file data, but not with auth error
        assert response.status_code != 401
    
    def test_media_delete_endpoint(self, client: TestClient, auth_headers: dict):
        """Test media deletion endpoint"""
        response = client.delete("/media/test-media-id", headers=auth_headers)
        # Should fail with not found, but not with auth error
        assert response.status_code != 401


class TestContestDeletionEndpoint:
    """Test unified contest deletion endpoint"""
    
    def test_delete_draft_contest(self, client: TestClient, db_session: Session, sponsor_headers: dict):
        """Test deleting draft contest"""
        # Create sponsor user
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add(sponsor)
        db_session.commit()
        
        # Create draft contest
        contest = Contest(
            name="Draft to Delete",
            description="Draft contest for deletion testing",
            status="draft",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor.id,
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.delete(f"/contests/{contest.id}", headers=sponsor_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["contest_id"] == contest.id
    
    def test_delete_protected_contest(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test attempting to delete protected contest"""
        # Create admin user
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        # Create active contest (protected)
        contest = Contest(
            name="Protected Contest",
            description="Active contest that cannot be deleted",
            status="active",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.delete(f"/contests/{contest.id}", headers=auth_headers)
        assert response.status_code == 403
        
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "CONTEST_PROTECTED"


class TestErrorHandling:
    """Test error handling across all endpoints"""
    
    def test_404_endpoints(self, client: TestClient):
        """Test 404 handling for non-existent endpoints"""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client: TestClient):
        """Test 405 handling for wrong HTTP methods"""
        response = client.post("/")  # Root only accepts GET
        assert response.status_code == 405
    
    def test_401_unauthorized_access(self, client: TestClient):
        """Test 401 handling for protected endpoints"""
        protected_endpoints = [
            "/users/me",
            "/admin/contests/",
            "/sponsor/workflow/contests/drafts",
            "/admin/approval/queue"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_403_forbidden_access(self, client: TestClient, user_headers: dict):
        """Test 403 handling for insufficient permissions"""
        admin_only_endpoints = [
            "/admin/users",
            "/admin/approval/queue",
            "/admin/approval/statistics"
        ]
        
        for endpoint in admin_only_endpoints:
            response = client.get(endpoint, headers=user_headers)
            assert response.status_code == 403
    
    def test_422_validation_errors(self, client: TestClient):
        """Test 422 handling for validation errors"""
        # Test invalid phone number
        response = client.post("/auth/request-otp", json={"phone": "invalid"})
        assert response.status_code == 400
        
        # Test missing required fields
        response = client.post("/auth/request-otp", json={})
        assert response.status_code == 422
    
    def test_cors_headers_on_errors(self, client: TestClient):
        """Test that CORS headers are present on error responses"""
        response = client.get("/nonexistent", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 404
        
        # Should have CORS headers even on errors
        assert "access-control-allow-origin" in response.headers


class TestPaginationAndFiltering:
    """Test pagination and filtering across endpoints"""
    
    def test_contests_pagination(self, client: TestClient, db_session: Session):
        """Test contest listing pagination"""
        # Create multiple contests
        for i in range(15):
            contest = Contest(
                name=f"Pagination Test Contest {i+1}",
                description=f"Contest {i+1} for pagination testing",
                status="active",
                start_time=datetime.utcnow() - timedelta(hours=1),
                end_time=datetime.utcnow() + timedelta(days=7),
                prize_description="Test prize",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            db_session.add(contest)
        db_session.commit()
        
        # Test first page
        response = client.get("/contests/active?page=1&size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["contests"]) == 10
        assert data["page"] == 1
        assert data["size"] == 10
        assert data["total"] >= 15
        assert data["has_next_page"] is True
        
        # Test second page
        response = client.get("/contests/active?page=2&size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["contests"]) >= 5
        assert data["page"] == 2
    
    def test_contests_filtering(self, client: TestClient, db_session: Session):
        """Test contest filtering by various criteria"""
        # Create contests with different types
        contest_types = ["general", "photo", "video", "text"]
        for i, contest_type in enumerate(contest_types):
            contest = Contest(
                name=f"Filter Test Contest {i+1}",
                description=f"Contest {i+1} for filter testing",
                status="active",
                contest_type=contest_type,
                start_time=datetime.utcnow() - timedelta(hours=1),
                end_time=datetime.utcnow() + timedelta(days=7),
                prize_description="Test prize",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            db_session.add(contest)
        db_session.commit()
        
        # Test filtering by contest type
        response = client.get("/contests/active?contest_type=photo")
        assert response.status_code == 200
        
        data = response.json()
        for contest in data["contests"]:
            assert contest["contest_type"] == "photo"
