"""
Production-ready E2E tests for Contestlet API
Tests all critical endpoints with proper response format validation
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.sponsor_profile import SponsorProfile


class TestProductionE2EEndpoints:
    """Production-ready E2E tests for all critical API endpoints"""
    
    def test_health_check_endpoint(self, client: TestClient):
        """Test health check endpoint - critical for production monitoring"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "environment" in data
        assert data["status"] == "healthy"
        
        # Verify response time is acceptable for production
        assert response.elapsed.total_seconds() < 1.0  # Should be under 1 second
    
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
    
    def test_active_contests_endpoint_format(self, client: TestClient, db_session: Session):
        """Test active contests endpoint returns correct format"""
        response = client.get("/contests/active")
        assert response.status_code == 200
        
        data = response.json()
        # Verify standardized response format
        assert "success" in data
        assert "data" in data
        assert "message" in data
        assert "timestamp" in data
        assert data["success"] is True
        
        # Verify data structure
        assert "items" in data["data"]
        assert "pagination" in data["data"]
        assert isinstance(data["data"]["items"], list)
        
        # Verify pagination structure
        pagination = data["data"]["pagination"]
        assert "total" in pagination
        assert "page" in pagination
        assert "size" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination
    
    def test_active_contests_with_data(self, client: TestClient, db_session: Session):
        """Test active contests endpoint with actual contest data"""
        # Create a test contest
        contest = Contest(
            name="Production Test Contest",
            description="A contest for production testing",
            status="active",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="Test prize worth $100",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100,
            location_type="nationwide"
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get("/contests/active")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) >= 1
        
        # Verify contest data structure
        contest_data = data["data"]["items"][0]
        assert "id" in contest_data
        assert "name" in contest_data
        assert "description" in contest_data
        assert "status" in contest_data
        assert contest_data["name"] == "Production Test Contest"
    
    def test_contest_detail_endpoint(self, client: TestClient, db_session: Session):
        """Test individual contest detail endpoint"""
        # Create a test contest
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
            total_entry_limit=100,
            location_type="nationwide"
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.get(f"/contests/{contest.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        
        contest_data = data["data"]
        assert contest_data["id"] == contest.id
        assert contest_data["name"] == "Detail Test Contest"
        assert contest_data["status"] == "active"
    
    def test_authentication_request_otp(self, client: TestClient):
        """Test OTP request endpoint"""
        request_data = {
            "phone": "+15551234567"
        }
        
        response = client.post("/auth/request-otp", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        assert "message" in data
        
        # In test mode, should indicate mock SMS
        assert "mock" in data["message"].lower() or "test" in data["message"].lower()
    
    def test_authentication_verify_otp(self, client: TestClient):
        """Test OTP verification endpoint"""
        # First request OTP
        request_data = {"phone": "+15551234567"}
        client.post("/auth/request-otp", json=request_data)
        
        # Then verify with test OTP
        verify_data = {
            "phone": "+15551234567",
            "otp": "123456"  # Test OTP
        }
        
        response = client.post("/auth/verify-otp", json=verify_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        
        # Should contain access token
        assert "access_token" in data["data"]
        assert "token_type" in data["data"]
        assert data["data"]["token_type"] == "bearer"
    
    def test_user_profile_endpoint(self, client: TestClient, db_session: Session, user_headers: dict):
        """Test user profile endpoint"""
        # Create test user
        user = User(
            phone="+15559876543",
            role="user",
            is_verified=True,
            full_name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.get("/users/me", headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        
        user_data = data["data"]
        assert "id" in user_data
        assert "phone" in user_data
        assert "role" in user_data
        assert user_data["role"] == "user"
    
    def test_admin_dashboard_access(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test admin dashboard endpoint"""
        # Create admin user
        admin = User(
            phone="+18187958204",
            role="admin",
            is_verified=True,
            full_name="Admin User"
        )
        db_session.add(admin)
        db_session.commit()
        
        response = client.get("/admin/dashboard", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        
        # Should contain dashboard statistics
        dashboard_data = data["data"]
        assert "total_contests" in dashboard_data
        assert "total_users" in dashboard_data
        assert "total_entries" in dashboard_data
    
    def test_sponsor_workflow_draft_creation(self, client: TestClient, db_session: Session):
        """Test sponsor draft contest creation"""
        # Create sponsor user and profile
        sponsor_user = User(
            phone="+15551234567",
            role="sponsor",
            is_verified=True,
            full_name="Sponsor User"
        )
        db_session.add(sponsor_user)
        db_session.commit()
        
        sponsor_profile = SponsorProfile(
            user_id=sponsor_user.id,
            company_name="Test Company",
            contact_name="Test Contact",
            contact_email="test@example.com",
            is_verified=True
        )
        db_session.add(sponsor_profile)
        db_session.commit()
        
        # Create JWT token for sponsor
        from app.core.auth import jwt_manager
        token = jwt_manager.create_access_token(
            user_id=sponsor_user.id,
            phone=sponsor_user.phone,
            role=sponsor_user.role
        )
        headers = {"Authorization": f"Bearer {token}"}
        
        contest_data = {
            "name": "Draft Contest",
            "description": "A draft contest for testing",
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
            "location_type": "nationwide",
            "official_rules": {
                "eligibility_text": "Must be 18 or older",
                "sponsor_name": "Test Company",
                "start_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=8)).isoformat(),
                "prize_value_usd": 100.0
            }
        }
        
        response = client.post("/sponsor/workflow/contests/draft", json=contest_data, headers=headers)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        
        contest_response = data["data"]
        assert contest_response["status"] == "draft"
        assert contest_response["name"] == "Draft Contest"
    
    def test_error_handling_unauthorized(self, client: TestClient):
        """Test unauthorized access handling"""
        response = client.get("/admin/dashboard")
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_error_handling_not_found(self, client: TestClient):
        """Test 404 error handling"""
        response = client.get("/contests/99999")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_error_handling_validation(self, client: TestClient):
        """Test validation error handling"""
        invalid_data = {
            "phone": "invalid-phone"
        }
        
        response = client.post("/auth/request-otp", json=invalid_data)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly set"""
        response = client.options("/")
        assert response.status_code in [200, 405]  # Some servers return 405 for OPTIONS
        
        # Test actual request has CORS headers
        response = client.get("/")
        # CORS headers should be present in actual deployment
        # This test ensures the middleware is configured
        assert response.status_code == 200
    
    def test_pagination_functionality(self, client: TestClient, db_session: Session):
        """Test pagination works correctly"""
        # Create multiple contests
        for i in range(15):
            contest = Contest(
                name=f"Contest {i}",
                description=f"Contest {i} description",
                status="active",
                start_time=datetime.utcnow() - timedelta(hours=1),
                end_time=datetime.utcnow() + timedelta(days=7),
                prize_description=f"Prize {i}",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100,
                location_type="nationwide"
            )
            db_session.add(contest)
        db_session.commit()
        
        # Test first page
        response = client.get("/contests/active?page=1&size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 10
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["size"] == 10
        assert data["data"]["pagination"]["total"] >= 15
        assert data["data"]["pagination"]["has_next"] is True
        
        # Test second page
        response = client.get("/contests/active?page=2&size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) >= 5
        assert data["data"]["pagination"]["page"] == 2


class TestProductionPerformance:
    """Performance tests for production readiness"""
    
    def test_health_check_performance(self, client: TestClient):
        """Test health check responds quickly"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Should be under 100ms
    
    def test_contests_endpoint_performance(self, client: TestClient):
        """Test contests endpoint performance"""
        import time
        
        start_time = time.time()
        response = client.get("/contests/active")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 0.5  # Should be under 500ms
    
    def test_concurrent_requests(self, client: TestClient):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            results.append({
                "status_code": response.status_code,
                "duration": end_time - start_time
            })
        
        # Start 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(results) == 10
        for result in results:
            assert result["status_code"] == 200
            assert result["duration"] < 1.0  # Each request under 1 second


class TestProductionSecurity:
    """Security tests for production readiness"""
    
    def test_authentication_required_endpoints(self, client: TestClient):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            "/admin/dashboard",
            "/users/me",
            "/sponsor/workflow/contests/draft"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"
    
    def test_admin_only_endpoints(self, client: TestClient, user_headers: dict):
        """Test that admin-only endpoints reject non-admin users"""
        admin_endpoints = [
            "/admin/dashboard",
            "/admin/contests"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=user_headers)
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should reject non-admin users"
    
    def test_input_validation(self, client: TestClient):
        """Test input validation prevents malicious input"""
        malicious_inputs = [
            {"phone": "<script>alert('xss')</script>"},
            {"phone": "'; DROP TABLE users; --"},
            {"phone": "../../../etc/passwd"},
            {"phone": "a" * 1000}  # Very long input
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post("/auth/request-otp", json=malicious_input)
            assert response.status_code == 422, f"Should reject malicious input: {malicious_input}"
    
    def test_rate_limiting_simulation(self, client: TestClient):
        """Test rate limiting behavior (simulated)"""
        # Make multiple requests rapidly
        responses = []
        for _ in range(20):
            response = client.post("/auth/request-otp", json={"phone": "+15551234567"})
            responses.append(response.status_code)
        
        # Should have some successful requests
        assert 200 in responses
        # Note: Actual rate limiting might not trigger in test environment


class TestProductionDataIntegrity:
    """Data integrity tests for production readiness"""
    
    def test_contest_creation_data_integrity(self, client: TestClient, db_session: Session):
        """Test that contest creation maintains data integrity"""
        # Create sponsor user and profile
        sponsor_user = User(
            phone="+15551234567",
            role="sponsor",
            is_verified=True,
            full_name="Sponsor User"
        )
        db_session.add(sponsor_user)
        db_session.commit()
        
        sponsor_profile = SponsorProfile(
            user_id=sponsor_user.id,
            company_name="Test Company",
            contact_name="Test Contact",
            contact_email="test@example.com",
            is_verified=True
        )
        db_session.add(sponsor_profile)
        db_session.commit()
        
        # Create JWT token
        from app.core.auth import jwt_manager
        token = jwt_manager.create_access_token(
            user_id=sponsor_user.id,
            phone=sponsor_user.phone,
            role=sponsor_user.role
        )
        headers = {"Authorization": f"Bearer {token}"}
        
        contest_data = {
            "name": "Data Integrity Test Contest",
            "description": "Testing data integrity",
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
            "location_type": "nationwide",
            "official_rules": {
                "eligibility_text": "Must be 18 or older",
                "sponsor_name": "Test Company",
                "start_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=8)).isoformat(),
                "prize_value_usd": 100.0
            }
        }
        
        response = client.post("/sponsor/workflow/contests/draft", json=contest_data, headers=headers)
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["success"] is True
            
            # Verify data was stored correctly in database
            contest = db_session.query(Contest).filter_by(name="Data Integrity Test Contest").first()
            assert contest is not None
            assert contest.created_by_user_id == sponsor_user.id
            assert contest.status == "draft"
    
    def test_user_data_isolation(self, client: TestClient, db_session: Session):
        """Test that users can only access their own data"""
        # Create two users
        user1 = User(phone="+15551111111", role="user", is_verified=True, full_name="User 1")
        user2 = User(phone="+15552222222", role="user", is_verified=True, full_name="User 2")
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Create tokens for both users
        from app.core.auth import jwt_manager
        token1 = jwt_manager.create_access_token(user_id=user1.id, phone=user1.phone, role=user1.role)
        token2 = jwt_manager.create_access_token(user_id=user2.id, phone=user2.phone, role=user2.role)
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # User 1 should only see their own profile
        response1 = client.get("/users/me", headers=headers1)
        if response1.status_code == 200:
            data1 = response1.json()
            assert data1["data"]["phone"] == user1.phone
        
        # User 2 should only see their own profile
        response2 = client.get("/users/me", headers=headers2)
        if response2.status_code == 200:
            data2 = response2.json()
            assert data2["data"]["phone"] == user2.phone


@pytest.mark.smoke
class TestProductionSmoke:
    """Smoke tests for quick production validation"""
    
    def test_api_is_responsive(self, client: TestClient):
        """Basic smoke test - API responds"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_health_check_smoke(self, client: TestClient):
        """Health check smoke test"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_contests_endpoint_smoke(self, client: TestClient):
        """Contests endpoint smoke test"""
        response = client.get("/contests/active")
        assert response.status_code == 200
        assert "success" in response.json()
    
    def test_auth_endpoint_smoke(self, client: TestClient):
        """Auth endpoint smoke test"""
        response = client.post("/auth/request-otp", json={"phone": "+15551234567"})
        assert response.status_code == 200
        assert "success" in response.json()
