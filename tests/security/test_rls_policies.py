"""
Security tests for Row Level Security (RLS) policies
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry


class TestRLSAuthentication:
    """Test RLS authentication requirements"""
    
    def test_public_endpoints_no_auth_required(self, client: TestClient, db_session: Session):
        """Test that public endpoints don't require authentication"""
        # Create test contest
        contest = Contest(
            name="Public Contest",
            description="Public contest for testing",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            active=True
        )
        db_session.add(contest)
        db_session.commit()
        
        # Test public contest viewing without auth
        response = client.get(f"/contests/{contest.id}")
        assert response.status_code == 200
        
        # Test active contests list without auth
        response = client.get("/contests/active")
        assert response.status_code == 200
    
    def test_protected_endpoints_require_auth(self, client: TestClient):
        """Test that protected endpoints require authentication"""
        # Test user profile without auth
        response = client.get("/user/profile")
        assert response.status_code == 401
        
        # Test admin dashboard without auth
        response = client.get("/admin/dashboard")
        assert response.status_code == 401
        
        # Test contest creation without auth
        response = client.post("/admin/contests/", json={})
        assert response.status_code == 401
    
    def test_invalid_token_rejected(self, client: TestClient):
        """Test that invalid tokens are rejected"""
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/user/profile", headers=headers)
        assert response.status_code == 401
        
        # Test with malformed token
        headers = {"Authorization": "Bearer not.a.valid.token"}
        response = client.get("/user/profile", headers=headers)
        assert response.status_code == 401
        
        # Test with expired token (would need to create expired token)
        # This is tested in the auth service unit tests


class TestRLSRoleBasedAccess:
    """Test RLS role-based access control"""
    
    def test_admin_access_to_all_data(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test that admin users can access all data"""
        # Create test users
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        regular_user = User(phone="+15551234567", role="user", is_verified=True)
        db_session.add_all([admin_user, regular_user])
        db_session.commit()
        
        # Admin should be able to view all users
        response = client.get("/admin/users", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 2  # Should see both users
        
        # Admin should be able to view all contests
        response = client.get("/admin/contests", headers=auth_headers)
        assert response.status_code == 200
    
    def test_sponsor_access_limited(self, client: TestClient, db_session: Session, sponsor_headers: dict):
        """Test that sponsor users have limited access"""
        # Create test data
        sponsor_user = User(phone="+15551234567", role="sponsor", is_verified=True)
        other_user = User(phone="+15559876543", role="user", is_verified=True)
        db_session.add_all([sponsor_user, other_user])
        db_session.commit()
        
        # Sponsor should not be able to view all users
        response = client.get("/admin/users", headers=sponsor_headers)
        assert response.status_code == 403
        
        # Sponsor should be able to view their own contests
        contest = Contest(
            name="Sponsor Contest",
            description="Contest created by sponsor",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by_user_id=sponsor_user.id,
            active=True
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get(f"/admin/contests/{contest.id}", headers=sponsor_headers)
        assert response.status_code == 200
    
    def test_user_access_isolated(self, client: TestClient, db_session: Session, user_headers: dict):
        """Test that regular users can only access their own data"""
        # Create test users
        user1 = User(phone="+15559876543", role="user", is_verified=True)
        user2 = User(phone="+15551111111", role="user", is_verified=True)
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # User should not be able to view all users
        response = client.get("/admin/users", headers=user_headers)
        assert response.status_code == 403
        
        # User should not be able to view admin dashboard
        response = client.get("/admin/dashboard", headers=user_headers)
        assert response.status_code == 403


class TestRLSDataIsolation:
    """Test RLS data isolation between users"""
    
    def test_user_can_only_see_own_entries(self, client: TestClient, db_session: Session, user_headers: dict):
        """Test that users can only see their own contest entries"""
        # Create test users
        user1 = User(phone="+15559876543", role="user", is_verified=True)
        user2 = User(phone="+15551111111", role="user", is_verified=True)
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Create test contest
        contest = Contest(
            name="Test Contest",
            description="Contest for testing entries",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            active=True
        )
        db_session.add(contest)
        db_session.commit()
        
        # Create entries for both users
        entry1 = Entry(contest_id=contest.id, user_id=user1.id, is_valid=True)
        entry2 = Entry(contest_id=contest.id, user_id=user2.id, is_valid=True)
        db_session.add_all([entry1, entry2])
        db_session.commit()
        
        # User1 should only see their own entries
        response = client.get("/entries/mine", headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == user1.id
    
    def test_sponsor_can_only_see_own_contests(self, client: TestClient, db_session: Session, sponsor_headers: dict):
        """Test that sponsors can only see their own contests"""
        # Create test users
        sponsor1 = User(phone="+15551234567", role="sponsor", is_verified=True)
        sponsor2 = User(phone="+15552222222", role="sponsor", is_verified=True)
        db_session.add_all([sponsor1, sponsor2])
        db_session.commit()
        
        # Create contests for both sponsors
        contest1 = Contest(
            name="Sponsor1 Contest",
            description="Contest by sponsor1",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by_user_id=sponsor1.id,
            active=True
        )
        contest2 = Contest(
            name="Sponsor2 Contest",
            description="Contest by sponsor2",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by_user_id=sponsor2.id,
            active=True
        )
        db_session.add_all([contest1, contest2])
        db_session.commit()
        
        # Sponsor1 should only see their own contests
        response = client.get("/admin/contests", headers=sponsor_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should only see contests created by sponsor1
        for contest in data:
            assert contest["created_by_user_id"] == sponsor1.id


class TestRLSContestAccess:
    """Test RLS contest access policies"""
    
    def test_public_contest_viewing(self, client: TestClient, db_session: Session):
        """Test public contest viewing without authentication"""
        # Create active contest
        contest = Contest(
            name="Public Contest",
            description="Public contest for testing",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            active=True
        )
        db_session.add(contest)
        db_session.commit()
        
        # Should be able to view contest details
        response = client.get(f"/contests/{contest.id}")
        assert response.status_code == 200
        
        # Should be able to view active contests list
        response = client.get("/contests/active")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["contests"]) >= 1
    
    def test_contest_creation_requires_auth(self, client: TestClient, db_session: Session):
        """Test that contest creation requires authentication"""
        contest_data = {
            "name": "Test Contest",
            "description": "Test contest",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-12-31T23:59:59Z"
        }
        
        # Without auth, should fail
        response = client.post("/admin/contests/", json=contest_data)
        assert response.status_code == 401
        
        # With auth, should succeed (tested in other tests)
    
    def test_contest_modification_requires_ownership(self, client: TestClient, db_session: Session, user_headers: dict):
        """Test that contest modification requires ownership or admin role"""
        # Create test users
        user1 = User(phone="+15559876543", role="user", is_verified=True)
        user2 = User(phone="+15551111111", role="user", is_verified=True)
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Create contest owned by user1
        contest = Contest(
            name="User1 Contest",
            description="Contest owned by user1",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by_user_id=user1.id,
            active=True
        )
        db_session.add(contest)
        db_session.commit()
        
        # User2 should not be able to modify user1's contest
        update_data = {"name": "Modified Contest"}
        response = client.put(f"/admin/contests/{contest.id}", json=update_data, headers=user_headers)
        assert response.status_code == 403


class TestRLSErrorHandling:
    """Test RLS error handling and security"""
    
    def test_unauthorized_access_returns_403(self, client: TestClient, db_session: Session, user_headers: dict):
        """Test that unauthorized access returns proper error codes"""
        # Regular user trying to access admin endpoint
        response = client.get("/admin/users", headers=user_headers)
        assert response.status_code == 403
        
        # Check error response structure
        data = response.json()
        assert "detail" in data
        assert "Access denied" in data["detail"]
    
    def test_invalid_token_returns_401(self, client: TestClient):
        """Test that invalid tokens return proper error codes"""
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/user/profile", headers=headers)
        assert response.status_code == 401
        
        # Check error response structure
        data = response.json()
        assert "detail" in data
        assert "Could not validate credentials" in data["detail"]
    
    def test_missing_token_returns_401(self, client: TestClient):
        """Test that missing tokens return proper error codes"""
        # Test without token
        response = client.get("/user/profile")
        assert response.status_code == 401
        
        # Check error response structure
        data = response.json()
        assert "detail" in data
        assert "Not authenticated" in data["detail"]


class TestRLSIntegration:
    """Test RLS integration with other security features"""
    
    def test_rls_with_rate_limiting(self, client: TestClient, db_session: Session):
        """Test that RLS works correctly with rate limiting"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=False)
        db_session.add(user)
        db_session.commit()
        
        # Make multiple OTP requests to trigger rate limiting
        for i in range(10):
            response = client.post("/auth/request-otp", json={"phone": "+15551234567"})
            
            if response.status_code == 429:  # Rate limited
                # Even when rate limited, RLS should still work
                # Test that public endpoints are still accessible
                response = client.get("/contests/active")
                assert response.status_code == 200
                break
    
    def test_rls_with_validation(self, client: TestClient, db_session: Session):
        """Test that RLS works correctly with input validation"""
        # Test with malformed input that should fail validation
        response = client.post("/auth/request-otp", json={"phone": "invalid"})
        assert response.status_code == 400
        
        # RLS should not interfere with validation errors
        data = response.json()
        assert "detail" in data
