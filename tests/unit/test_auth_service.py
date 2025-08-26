"""
Unit tests for authentication service
"""
import pytest
from datetime import datetime, timedelta
from app.core.auth import JWTManager, jwt_manager
from app.core.config import get_settings


class TestJWTManager:
    """Test JWT manager functionality"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        token = jwt_manager.create_access_token(
            user_id=1,
            phone="+15551234567",
            role="admin"
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token = jwt_manager.create_refresh_token(
            user_id=1,
            phone="+15551234567"
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_access_token(self):
        """Test valid access token verification"""
        token = jwt_manager.create_access_token(
            user_id=1,
            phone="+15551234567",
            role="admin"
        )
        
        payload = jwt_manager.verify_token(token, "access")
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["phone"] == "+15551234567"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"
    
    def test_verify_valid_refresh_token(self):
        """Test valid refresh token verification"""
        token = jwt_manager.create_refresh_token(
            user_id=1,
            phone="+15551234567"
        )
        
        payload = jwt_manager.verify_token(token, "refresh")
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["phone"] == "+15551234567"
        assert payload["type"] == "refresh"
    
    def test_verify_invalid_token(self):
        """Test invalid token verification"""
        payload = jwt_manager.verify_token("invalid_token", "access")
        assert payload is None
    
    def test_verify_wrong_token_type(self):
        """Test token type mismatch"""
        access_token = jwt_manager.create_access_token(
            user_id=1,
            phone="+15551234567",
            role="admin"
        )
        
        # Try to verify access token as refresh token
        payload = jwt_manager.verify_token(access_token, "refresh")
        assert payload is None
    
    def test_extract_user_info(self):
        """Test user info extraction from token"""
        token = jwt_manager.create_access_token(
            user_id=1,
            phone="+15551234567",
            role="admin"
        )
        
        user_info = jwt_manager.extract_user_info(token)
        assert user_info is not None
        assert user_info["user_id"] == 1
        assert user_info["phone"] == "+15551234567"
        assert user_info["role"] == "admin"
        assert "exp" in user_info
        assert "iat" in user_info
    
    def test_refresh_access_token(self):
        """Test access token refresh"""
        refresh_token = jwt_manager.create_refresh_token(
            user_id=1,
            phone="+15551234567"
        )
        
        new_access_token = jwt_manager.refresh_access_token(refresh_token)
        assert new_access_token is not None
        
        # Verify the new token
        payload = jwt_manager.verify_token(new_access_token, "access")
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["phone"] == "+15551234567"
        assert payload["role"] == "user"  # Default role for refresh
    
    def test_token_expiration(self):
        """Test token expiration handling"""
        # Create token with short expiration
        token = jwt_manager.create_token(
            {"user_id": 1},
            expires_delta=timedelta(seconds=1),
            token_type="access"
        )
        
        # Token should be valid initially
        payload = jwt_manager.verify_token(token, "access")
        assert payload is not None
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Token should now be expired
        payload = jwt_manager.verify_token(token, "access")
        assert payload is None
    
    def test_token_with_extra_claims(self):
        """Test token creation with extra claims"""
        token = jwt_manager.create_access_token(
            user_id=1,
            phone="+15551234567",
            role="admin",
            custom_field="custom_value"
        )
        
        payload = jwt_manager.verify_token(token, "access")
        assert payload is not None
        assert payload["custom_field"] == "custom_value"
    
    def test_token_pair_creation(self):
        """Test token pair creation utility"""
        from app.core.auth import create_token_pair
        
        token_pair = create_token_pair(
            user_id=1,
            phone="+15551234567",
            role="admin"
        )
        
        assert token_pair.access_token is not None
        assert token_pair.refresh_token is not None
        assert token_pair.to_dict()["token_type"] == "bearer"


class TestJWTManagerSettings:
    """Test JWT manager with different settings"""
    
    def test_jwt_expiration_settings(self):
        """Test JWT expiration settings"""
        settings = get_settings()
        
        # Test access token expiration
        token = jwt_manager.create_access_token(
            user_id=1,
            phone="+15551234567",
            role="admin"
        )
        
        payload = jwt_manager.verify_token(token, "access")
        assert payload is not None
        
        # Test refresh token expiration
        refresh_token = jwt_manager.create_refresh_token(
            user_id=1,
            phone="+15551234567"
        )
        
        payload = jwt_manager.verify_token(refresh_token, "refresh")
        assert payload is not None
    
    def test_jwt_algorithm_settings(self):
        """Test JWT algorithm settings"""
        settings = get_settings()
        assert settings.security.jwt_algorithm == "HS256"
        
        # Verify token uses correct algorithm
        token = jwt_manager.create_access_token(
            user_id=1,
            phone="+15551234567",
            role="admin"
        )
        
        payload = jwt_manager.verify_token(token, "access")
        assert payload is not None


class TestJWTManagerEdgeCases:
    """Test JWT manager edge cases"""
    
    def test_empty_token(self):
        """Test empty token handling"""
        payload = jwt_manager.verify_token("", "access")
        assert payload is None
    
    def test_none_token(self):
        """Test None token handling"""
        payload = jwt_manager.verify_token(None, "access")
        assert payload is None
    
    def test_malformed_token(self):
        """Test malformed token handling"""
        payload = jwt_manager.verify_token("not.a.valid.token", "access")
        assert payload is None
    
    def test_token_without_required_fields(self):
        """Test token without required fields"""
        # Create token manually without required fields
        from jose import jwt
        from app.core.config import get_settings
        
        settings = get_settings()
        token = jwt.encode(
            {"user_id": 1},  # Missing required fields
            settings.security.secret_key,
            algorithm=settings.security.jwt_algorithm
        )
        
        # Should fail verification
        payload = jwt_manager.verify_token(token, "access")
        assert payload is None
    
    def test_token_with_invalid_signature(self):
        """Test token with invalid signature"""
        # Create token with wrong secret
        from jose import jwt
        
        token = jwt.encode(
            {"sub": "1", "phone": "+15551234567", "role": "admin", "type": "access"},
            "wrong_secret",
            algorithm="HS256"
        )
        
        # Should fail verification
        payload = jwt_manager.verify_token(token, "access")
        assert payload is None
