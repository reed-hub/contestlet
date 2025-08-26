from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.config import get_settings
from functools import wraps


class JWTManager:
    """Elegant JWT token management with refresh capabilities"""
    
    def __init__(self):
        self._settings = get_settings()
    
    def create_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None,
        token_type: str = "access"
    ) -> str:
        """Create JWT token with automatic expiration handling"""
        to_encode = data.copy()
        
        # Set expiration based on token type
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        elif token_type == "refresh":
            expire = datetime.utcnow() + timedelta(minutes=self._settings.jwt_refresh_expire_minutes)
        else:
            expire = datetime.utcnow() + timedelta(minutes=self._settings.jwt_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": token_type
        })
        
        return jwt.encode(
            to_encode, 
            self._settings.secret_key, 
            algorithm=self._settings.jwt_algorithm
        )
    
    def create_access_token(self, user_id: int, phone: str, role: str = "user", **extra_claims) -> str:
        """Create access token with user information"""
        token_data = {
            "sub": str(user_id),
            "phone": phone,
            "role": role,
            **extra_claims
        }
        return self.create_token(token_data, token_type="access")
    
    def create_refresh_token(self, user_id: int, phone: str) -> str:
        """Create refresh token for user"""
        token_data = {
            "sub": str(user_id),
            "phone": phone,
            "role": "refresh"  # Special role for refresh tokens
        }
        return self.create_token(token_data, token_type="refresh")
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token with type validation"""
        try:
            payload = jwt.decode(
                token, 
                self._settings.secret_key, 
                algorithms=[self._settings.jwt_algorithm]
            )
            
            # Validate token type
            if payload.get("type") != token_type:
                return None
            
            # Check if token is expired
            if datetime.fromtimestamp(payload.get("exp", 0)) < datetime.utcnow():
                return None
            
            return payload
            
        except JWTError:
            return None
    
    def extract_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Extract user information from access token"""
        payload = self.verify_token(token, "access")
        if not payload:
            return None
        
        try:
            return {
                "user_id": int(payload.get("sub")),
                "phone": payload.get("phone"),
                "role": payload.get("role", "user"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
                **{k: v for k, v in payload.items() 
                   if k not in ["sub", "phone", "role", "exp", "iat", "type"]}
            }
        except (ValueError, TypeError):
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        try:
            user_id = int(payload.get("sub"))
            phone = payload.get("phone")
            return self.create_access_token(user_id, phone, role="user")
        except (ValueError, TypeError):
            return None


# Global JWT manager instance
jwt_manager = JWTManager()

# Convenience functions for backward compatibility
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token (legacy function)"""
    return jwt_manager.create_token(data, expires_delta, "access")

def create_user_token(user_id: int, phone: str, role: str = "user", **extra_claims) -> str:
    """Create JWT token for user (legacy function)"""
    return jwt_manager.create_access_token(user_id, phone, role, **extra_claims)

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token (legacy function)"""
    return jwt_manager.verify_token(token, "access")

def extract_user_info(token: str) -> Optional[dict]:
    """Extract user information from JWT token (legacy function)"""
    return jwt_manager.extract_user_info(token)


# Decorator for JWT validation
def require_jwt(func):
    """Decorator to require valid JWT token"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would be used in FastAPI dependencies
        # For now, it's a placeholder for the pattern
        return await func(*args, **kwargs)
    return wrapper


# JWT token pair response model
class TokenPair:
    """JWT token pair with access and refresh tokens"""
    
    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": "bearer"
        }


# Utility function to create token pairs
def create_token_pair(user_id: int, phone: str, role: str = "user") -> TokenPair:
    """Create access and refresh token pair for user"""
    access_token = jwt_manager.create_access_token(user_id, phone, role)
    refresh_token = jwt_manager.create_refresh_token(user_id, phone)
    return TokenPair(access_token, refresh_token)