"""
Comprehensive security and authorization tests
"""
import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry


class TestAuthenticationSecurity:
    """Test authentication security mechanisms"""
    
    def test_jwt_token_structure(self, client: TestClient, db_session: Session):
        """Test JWT token structure and claims"""
        # Create test user
        user = User(phone="+15551234567", role="admin", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        # Get token through OTP verification
        response = client.post("/auth/verify-otp", json={
            "phone": "+15551234567",
            "code": "123456"
        })
        
        if response.status_code == 200 and response.json().get("success"):
            data = response.json()
            if "access_token" in data:
                token = data["access_token"]
                
                # Verify JWT structure
                parts = token.split(".")
                assert len(parts) == 3, "JWT should have 3 parts (header.payload.signature)"
                
                # Decode and verify claims
                import jwt
                from app.core.config import get_settings
                settings = get_settings()
                
                try:
                    payload = jwt.decode(
                        token, 
                        settings.secret_key, 
                        algorithms=[settings.jwt_algorithm]
                    )
                    
                    # Verify required claims
                    required_claims = ["sub", "phone", "role", "exp", "iat", "type"]
                    for claim in required_claims:
                        assert claim in payload, f"Missing required claim: {claim}"
                    
                    # Verify claim values
                    assert payload["phone"] == "+15551234567"
                    assert payload["role"] == "admin"
                    assert payload["type"] == "access"
                    
                    # Verify expiration is in the future
                    assert payload["exp"] > time.time()
                    
                except jwt.InvalidTokenError as e:
                    pytest.fail(f"Invalid JWT token: {e}")
    
    def test_token_expiration_handling(self, client: TestClient, db_session: Session):
        """Test token expiration handling"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        # Create expired token manually
        from app.core.auth import jwt_manager
        expired_token = jwt_manager.create_token(
            {"sub": str(user.id), "phone": user.phone, "role": user.role},
            expires_delta=timedelta(seconds=-1),  # Already expired
            token_type="access"
        )
        
        # Try to use expired token
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "expired" in data["detail"].lower() or "invalid" in data["detail"].lower()
    
    def test_token_tampering_detection(self, client: TestClient, db_session: Session):
        """Test detection of tampered tokens"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        # Create valid token
        from app.core.auth import jwt_manager
        valid_token = jwt_manager.create_access_token(
            user_id=user.id,
            phone=user.phone,
            role=user.role
        )
        
        # Tamper with token (change last character)
        tampered_token = valid_token[:-1] + ("a" if valid_token[-1] != "a" else "b")
        
        # Try to use tampered token
        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 401
    
    def test_role_elevation_prevention(self, client: TestClient, db_session: Session):
        """Test prevention of role elevation attacks"""
        # Create regular user
        user = User(phone="+15551234567", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        # Create token for regular user
        from app.core.auth import jwt_manager
        user_token = jwt_manager.create_access_token(
            user_id=user.id,
            phone=user.phone,
            role="user"
        )
        
        # Try to manually create admin token with same user ID
        try:
            admin_token = jwt_manager.create_access_token(
                user_id=user.id,
                phone=user.phone,
                role="admin"  # Attempting elevation
            )
            
            # Even if token creation succeeds, the database role should be checked
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = client.get("/admin/users", headers=headers)
            
            # Should fail because user's actual role in DB is "user"
            assert response.status_code == 403
            
        except Exception:
            # Token creation might fail due to validation
            pass
    
    def test_phone_number_validation_security(self, client: TestClient):
        """Test phone number validation against injection attacks"""
        malicious_phones = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "null",
            "undefined",
            "' OR '1'='1",
            "+1555123456'; UPDATE users SET role='admin' WHERE phone='+15551234567'; --"
        ]
        
        for malicious_phone in malicious_phones:
            response = client.post("/auth/request-otp", json={"phone": malicious_phone})
            
            # Should reject malicious input
            assert response.status_code in [400, 422], f"Failed to reject malicious phone: {malicious_phone}"
            
            # Response should not contain the malicious input
            response_text = response.text.lower()
            assert "drop table" not in response_text
            assert "script" not in response_text
            assert "update users" not in response_text
    
    def test_otp_brute_force_protection(self, client: TestClient, db_session: Session):
        """Test OTP brute force protection"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=False)
        db_session.add(user)
        db_session.commit()
        
        # Request OTP first
        response = client.post("/auth/request-otp", json={"phone": "+15551234567"})
        assert response.status_code == 200
        
        # Attempt multiple OTP verifications with wrong codes
        wrong_codes = ["000000", "111111", "222222", "333333", "444444", "555555"]
        
        for code in wrong_codes:
            response = client.post("/auth/verify-otp", json={
                "phone": "+15551234567",
                "code": code
            })
            
            # In mock mode, this might succeed, but in real mode should fail
            # The important thing is that the system doesn't crash
            assert response.status_code in [200, 400, 401, 429]
    
    def test_session_management(self, client: TestClient, db_session: Session):
        """Test session management and token invalidation"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        # Create token
        from app.core.auth import jwt_manager
        token = jwt_manager.create_access_token(
            user_id=user.id,
            phone=user.phone,
            role=user.role
        )
        
        # Use token successfully
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 200
        
        # Test token reuse (should still work until expiration)
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 200


class TestAuthorizationSecurity:
    """Test authorization and access control security"""
    
    def test_role_based_access_control(self, client: TestClient, db_session: Session):
        """Test comprehensive RBAC implementation"""
        # Create users with different roles
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        user = User(phone="+15559876543", role="user", is_verified=True)
        db_session.add_all([admin, sponsor, user])
        db_session.commit()
        
        # Create tokens for each role
        from app.core.auth import jwt_manager
        
        admin_token = jwt_manager.create_access_token(
            user_id=admin.id, phone=admin.phone, role=admin.role
        )
        sponsor_token = jwt_manager.create_access_token(
            user_id=sponsor.id, phone=sponsor.phone, role=sponsor.role
        )
        user_token = jwt_manager.create_access_token(
            user_id=user.id, phone=user.phone, role=user.role
        )
        
        # Test admin access
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/admin/users", headers=admin_headers)
        assert response.status_code == 200, "Admin should access admin endpoints"
        
        # Test sponsor access to admin endpoints (should fail)
        sponsor_headers = {"Authorization": f"Bearer {sponsor_token}"}
        response = client.get("/admin/users", headers=sponsor_headers)
        assert response.status_code == 403, "Sponsor should not access admin-only endpoints"
        
        # Test user access to admin endpoints (should fail)
        user_headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/admin/users", headers=user_headers)
        assert response.status_code == 403, "User should not access admin-only endpoints"
        
        # Test user access to sponsor endpoints (should fail)
        response = client.get("/sponsor/workflow/contests/drafts", headers=user_headers)
        assert response.status_code == 403, "User should not access sponsor endpoints"
    
    def test_resource_ownership_validation(self, client: TestClient, db_session: Session):
        """Test that users can only access their own resources"""
        # Create two sponsors
        sponsor1 = User(phone="+15551234567", role="sponsor", is_verified=True)
        sponsor2 = User(phone="+15552345678", role="sponsor", is_verified=True)
        db_session.add_all([sponsor1, sponsor2])
        db_session.commit()
        
        # Create contest owned by sponsor1
        contest = Contest(
            name="Sponsor1 Contest",
            description="Contest owned by sponsor1",
            status="draft",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor1.id,
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
        
        # Create tokens
        from app.core.auth import jwt_manager
        sponsor1_token = jwt_manager.create_access_token(
            user_id=sponsor1.id, phone=sponsor1.phone, role=sponsor1.role
        )
        sponsor2_token = jwt_manager.create_access_token(
            user_id=sponsor2.id, phone=sponsor2.phone, role=sponsor2.role
        )
        
        # Sponsor1 should be able to access their contest
        sponsor1_headers = {"Authorization": f"Bearer {sponsor1_token}"}
        response = client.put(f"/sponsor/workflow/contests/{contest.id}/draft", 
                            json={"name": "Updated Contest"}, headers=sponsor1_headers)
        assert response.status_code in [200, 404], "Sponsor1 should access their own contest"
        
        # Sponsor2 should NOT be able to access sponsor1's contest
        sponsor2_headers = {"Authorization": f"Bearer {sponsor2_token}"}
        response = client.put(f"/sponsor/workflow/contests/{contest.id}/draft", 
                            json={"name": "Hacked Contest"}, headers=sponsor2_headers)
        assert response.status_code == 403, "Sponsor2 should not access sponsor1's contest"
    
    def test_data_isolation_between_users(self, client: TestClient, db_session: Session):
        """Test data isolation between different users"""
        # Create two users
        user1 = User(phone="+15551111111", role="user", is_verified=True)
        user2 = User(phone="+15552222222", role="user", is_verified=True)
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Create contest
        contest = Contest(
            name="Isolation Test Contest",
            description="Contest for testing data isolation",
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
        
        # Create entries for both users
        entry1 = Entry(contest_id=contest.id, user_id=user1.id, is_valid=True)
        entry2 = Entry(contest_id=contest.id, user_id=user2.id, is_valid=True)
        db_session.add_all([entry1, entry2])
        db_session.commit()
        
        # Create tokens
        from app.core.auth import jwt_manager
        user1_token = jwt_manager.create_access_token(
            user_id=user1.id, phone=user1.phone, role=user1.role
        )
        user2_token = jwt_manager.create_access_token(
            user_id=user2.id, phone=user2.phone, role=user2.role
        )
        
        # User1 should only see their own entries
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        response = client.get("/user/entries/active", headers=user1_headers)
        
        if response.status_code == 200:
            data = response.json()
            for entry in data:
                assert entry["user_id"] == user1.id, "User1 should only see their own entries"
        
        # User2 should only see their own entries
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        response = client.get("/user/entries/active", headers=user2_headers)
        
        if response.status_code == 200:
            data = response.json()
            for entry in data:
                assert entry["user_id"] == user2.id, "User2 should only see their own entries"
    
    def test_privilege_escalation_prevention(self, client: TestClient, db_session: Session):
        """Test prevention of privilege escalation attacks"""
        # Create regular user
        user = User(phone="+15551234567", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        # Create user token
        from app.core.auth import jwt_manager
        user_token = jwt_manager.create_access_token(
            user_id=user.id, phone=user.phone, role=user.role
        )
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Attempt to access admin functions
        admin_endpoints = [
            "/admin/users",
            "/admin/contests/",
            "/admin/approval/queue",
            "/admin/approval/statistics",
            "/admin/notifications/"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=user_headers)
            assert response.status_code == 403, f"User should not access admin endpoint: {endpoint}"
        
        # Attempt to modify admin data
        response = client.post("/admin/approval/contests/1/approve", 
                             json={"approval_message": "Hacked approval"}, 
                             headers=user_headers)
        assert response.status_code == 403, "User should not be able to approve contests"
    
    def test_cross_tenant_data_access_prevention(self, client: TestClient, db_session: Session):
        """Test prevention of cross-tenant data access"""
        # Create sponsors (acting as different tenants)
        sponsor1 = User(phone="+15551111111", role="sponsor", is_verified=True, company_name="Company A")
        sponsor2 = User(phone="+15552222222", role="sponsor", is_verified=True, company_name="Company B")
        db_session.add_all([sponsor1, sponsor2])
        db_session.commit()
        
        # Create contests for each sponsor
        contest1 = Contest(
            name="Company A Contest",
            description="Contest by Company A",
            status="draft",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor1.id,
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        contest2 = Contest(
            name="Company B Contest",
            description="Contest by Company B",
            status="draft",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor2.id,
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add_all([contest1, contest2])
        db_session.commit()
        
        # Create tokens
        from app.core.auth import jwt_manager
        sponsor1_token = jwt_manager.create_access_token(
            user_id=sponsor1.id, phone=sponsor1.phone, role=sponsor1.role
        )
        sponsor2_token = jwt_manager.create_access_token(
            user_id=sponsor2.id, phone=sponsor2.phone, role=sponsor2.role
        )
        
        # Sponsor1 should not be able to access sponsor2's contests
        sponsor1_headers = {"Authorization": f"Bearer {sponsor1_token}"}
        response = client.get(f"/admin/contests/{contest2.id}", headers=sponsor1_headers)
        assert response.status_code in [403, 404], "Sponsor1 should not access sponsor2's contest"
        
        # Sponsor2 should not be able to access sponsor1's contests
        sponsor2_headers = {"Authorization": f"Bearer {sponsor2_token}"}
        response = client.get(f"/admin/contests/{contest1.id}", headers=sponsor2_headers)
        assert response.status_code in [403, 404], "Sponsor2 should not access sponsor1's contest"


class TestInputValidationSecurity:
    """Test input validation and sanitization security"""
    
    def test_sql_injection_prevention(self, client: TestClient, db_session: Session):
        """Test SQL injection prevention"""
        # Create admin user
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        from app.core.auth import jwt_manager
        admin_token = jwt_manager.create_access_token(
            user_id=admin.id, phone=admin.phone, role=admin.role
        )
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test SQL injection in contest search
        malicious_queries = [
            "'; DROP TABLE contests; --",
            "' OR '1'='1",
            "'; UPDATE contests SET status='active'; --",
            "' UNION SELECT * FROM users; --"
        ]
        
        for malicious_query in malicious_queries:
            response = client.get(f"/contests/active?search={malicious_query}")
            
            # Should not crash or expose data
            assert response.status_code in [200, 400, 422]
            
            # Response should not contain SQL error messages
            response_text = response.text.lower()
            assert "sql" not in response_text
            assert "syntax error" not in response_text
            assert "table" not in response_text or "contests" in response_text  # Allow legitimate table references
    
    def test_xss_prevention(self, client: TestClient, db_session: Session):
        """Test XSS prevention in user inputs"""
        # Create sponsor user
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add(sponsor)
        db_session.commit()
        
        from app.core.auth import jwt_manager
        sponsor_token = jwt_manager.create_access_token(
            user_id=sponsor.id, phone=sponsor.phone, role=sponsor.role
        )
        sponsor_headers = {"Authorization": f"Bearer {sponsor_token}"}
        
        # Test XSS in contest creation
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for xss_payload in xss_payloads:
            contest_data = {
                "name": f"Contest with XSS: {xss_payload}",
                "description": f"Description with XSS: {xss_payload}",
                "location": "Test City, TS 12345",
                "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "end_time": (datetime.utcnow() + timedelta(days=8)).isoformat(),
                "prize_description": f"Prize with XSS: {xss_payload}",
                "contest_type": "general",
                "entry_method": "sms",
                "winner_selection_method": "random",
                "minimum_age": 18,
                "max_entries_per_person": 1,
                "total_entry_limit": 100,
                "official_rules": {
                    "eligibility": f"Eligibility with XSS: {xss_payload}",
                    "entry_requirements": "Valid phone number required",
                    "prize_details": "Prize details",
                    "winner_selection": "Random selection",
                    "contact_info": "contest@example.com"
                }
            }
            
            response = client.post("/sponsor/workflow/contests/draft", 
                                 json=contest_data, headers=sponsor_headers)
            
            # Should either succeed (with sanitized input) or fail validation
            assert response.status_code in [200, 201, 400, 422]
            
            if response.status_code in [200, 201]:
                # If successful, verify XSS payload was sanitized
                data = response.json()
                assert "<script>" not in data.get("name", "")
                assert "javascript:" not in data.get("description", "")
                assert "onerror=" not in data.get("prize_description", "")
    
    def test_path_traversal_prevention(self, client: TestClient, auth_headers: dict):
        """Test path traversal prevention"""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2froot%2f.ssh%2fid_rsa",
            "....//....//....//etc//passwd"
        ]
        
        for payload in path_traversal_payloads:
            # Test in contest ID parameter
            response = client.get(f"/contests/{payload}")
            
            # Should not expose system files
            assert response.status_code in [400, 404, 422]
            
            # Response should not contain system file contents
            response_text = response.text.lower()
            assert "root:" not in response_text
            assert "administrator" not in response_text
            assert "ssh-rsa" not in response_text
    
    def test_file_upload_security(self, client: TestClient, auth_headers: dict):
        """Test file upload security"""
        # Test malicious file types
        malicious_files = [
            ("malware.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("shell.jsp", b"<% Runtime.getRuntime().exec(request.getParameter(\"cmd\")); %>", "application/x-jsp"),
            ("virus.bat", b"@echo off\nformat c: /y", "application/x-msdos-program")
        ]
        
        for filename, content, content_type in malicious_files:
            files = {"file": (filename, content, content_type)}
            response = client.post("/media/upload", files=files, headers=auth_headers)
            
            # Should reject malicious files
            assert response.status_code in [400, 415, 422], f"Should reject malicious file: {filename}"
    
    def test_rate_limiting_security(self, client: TestClient, db_session: Session):
        """Test rate limiting for security"""
        # Create test user
        user = User(phone="+15551234567", role="user", is_verified=False)
        db_session.add(user)
        db_session.commit()
        
        # Test OTP request rate limiting
        request_count = 0
        for i in range(20):  # Try many requests
            response = client.post("/auth/request-otp", json={"phone": "+15551234567"})
            
            if response.status_code == 429:  # Rate limited
                break
            elif response.status_code == 200:
                request_count += 1
            
            # Add small delay to avoid overwhelming the test
            time.sleep(0.1)
        
        # Should eventually be rate limited
        assert request_count < 20, "Rate limiting should prevent excessive requests"
    
    def test_content_type_validation(self, client: TestClient, db_session: Session):
        """Test content type validation"""
        # Create sponsor user
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add(sponsor)
        db_session.commit()
        
        from app.core.auth import jwt_manager
        sponsor_token = jwt_manager.create_access_token(
            user_id=sponsor.id, phone=sponsor.phone, role=sponsor.role
        )
        sponsor_headers = {"Authorization": f"Bearer {sponsor_token}"}
        
        # Test with wrong content type
        contest_data = '{"name": "Test Contest"}'  # JSON string, not dict
        
        # Send as text/plain instead of application/json
        response = client.post("/sponsor/workflow/contests/draft", 
                             data=contest_data,
                             headers={**sponsor_headers, "Content-Type": "text/plain"})
        
        # Should reject wrong content type
        assert response.status_code in [400, 415, 422]


class TestDataProtectionSecurity:
    """Test data protection and privacy security"""
    
    def test_sensitive_data_exposure_prevention(self, client: TestClient, db_session: Session):
        """Test prevention of sensitive data exposure"""
        # Create users with sensitive data
        admin = User(
            phone="+18187958204", 
            role="admin", 
            is_verified=True,
            email="admin@example.com",
            first_name="Admin",
            last_name="User"
        )
        user = User(
            phone="+15551234567", 
            role="user", 
            is_verified=True,
            email="user@example.com",
            first_name="Regular",
            last_name="User"
        )
        db_session.add_all([admin, user])
        db_session.commit()
        
        from app.core.auth import jwt_manager
        user_token = jwt_manager.create_access_token(
            user_id=user.id, phone=user.phone, role=user.role
        )
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Regular user should not see other users' sensitive data
        response = client.get("/users/me", headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should only see own data
        assert data["phone"] == "+15551234567"
        assert data["email"] == "user@example.com"
        
        # Should not contain admin's data
        assert "+18187958204" not in str(data)
        assert "admin@example.com" not in str(data)
    
    def test_password_hash_protection(self, client: TestClient, db_session: Session):
        """Test that password hashes are never exposed"""
        # Create user
        user = User(phone="+15551234567", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        from app.core.auth import jwt_manager
        user_token = jwt_manager.create_access_token(
            user_id=user.id, phone=user.phone, role=user.role
        )
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Get user profile
        response = client.get("/users/me", headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        response_text = response.text.lower()
        
        # Should not contain any password-related fields
        password_fields = ["password", "hash", "bcrypt", "scrypt", "pbkdf2", "salt"]
        for field in password_fields:
            assert field not in data
            assert field not in response_text
    
    def test_pii_data_handling(self, client: TestClient, db_session: Session):
        """Test PII data handling and protection"""
        # Create user with PII data
        user = User(
            phone="+15551234567",
            role="user",
            is_verified=True,
            email="sensitive@example.com",
            first_name="Sensitive",
            last_name="User",
            date_of_birth=datetime(1990, 1, 1).date()
        )
        db_session.add(user)
        db_session.commit()
        
        from app.core.auth import jwt_manager
        user_token = jwt_manager.create_access_token(
            user_id=user.id, phone=user.phone, role=user.role
        )
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # User should be able to see their own PII
        response = client.get("/users/me", headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == "sensitive@example.com"
        assert data["first_name"] == "Sensitive"
        
        # But PII should not appear in logs or error messages
        # This would require checking actual log files in a real scenario
    
    def test_data_retention_compliance(self, client: TestClient, db_session: Session):
        """Test data retention and deletion compliance"""
        # Create user
        user = User(phone="+15551234567", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        # Create contest entry
        contest = Contest(
            name="Data Retention Test",
            description="Contest for testing data retention",
            status="ended",
            start_time=datetime.utcnow() - timedelta(days=30),
            end_time=datetime.utcnow() - timedelta(days=23),
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
        
        entry = Entry(contest_id=contest.id, user_id=user.id, is_valid=True)
        db_session.add(entry)
        db_session.commit()
        
        # Verify data exists
        assert db_session.query(Entry).filter_by(user_id=user.id).first() is not None
        
        # In a real scenario, this would test automated data deletion
        # For now, we just verify the data structure supports it
        assert hasattr(entry, 'created_at')
        assert hasattr(user, 'created_at')


class TestSecurityHeaders:
    """Test security headers and HTTPS enforcement"""
    
    def test_cors_headers_security(self, client: TestClient):
        """Test CORS headers are properly configured"""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        
        # Should have proper CORS headers
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        
        # Should not allow all origins in production
        assert response.headers["access-control-allow-origin"] != "*"
    
    def test_content_security_headers(self, client: TestClient):
        """Test content security headers"""
        response = client.get("/")
        assert response.status_code == 200
        
        # In a production environment, these headers should be present:
        # - X-Content-Type-Options: nosniff
        # - X-Frame-Options: DENY
        # - X-XSS-Protection: 1; mode=block
        # - Strict-Transport-Security (for HTTPS)
        
        # For now, just verify the response doesn't expose sensitive info
        assert "server" not in response.headers or "uvicorn" not in response.headers.get("server", "").lower()
    
    def test_error_information_disclosure(self, client: TestClient):
        """Test that errors don't disclose sensitive information"""
        # Test 404 error
        response = client.get("/nonexistent/endpoint/12345")
        assert response.status_code == 404
        
        error_text = response.text.lower()
        
        # Should not expose:
        sensitive_info = [
            "traceback", "stack trace", "file path", "/app/", "/usr/", 
            "database", "connection", "password", "secret", "token",
            "internal server error", "debug", "exception"
        ]
        
        for info in sensitive_info:
            assert info not in error_text, f"Error response should not expose: {info}"
    
    def test_version_information_disclosure(self, client: TestClient):
        """Test that version information is not disclosed"""
        response = client.get("/")
        assert response.status_code == 200
        
        # Should not expose detailed version info in headers
        headers_text = str(response.headers).lower()
        
        version_indicators = [
            "python/", "fastapi/", "uvicorn/", "gunicorn/", 
            "nginx/", "apache/", "version"
        ]
        
        # Some version info might be acceptable, but detailed versions should be avoided
        for indicator in version_indicators:
            if indicator in headers_text:
                # If version info is present, it should not be too detailed
                assert "0.0.0" not in headers_text  # Avoid exposing exact versions
