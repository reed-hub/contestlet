from functools import lru_cache, wraps
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.core.auth import jwt_manager
from app.models.user import User
from app.core.exceptions import (
    raise_authentication_error,
    raise_authorization_error,
    ErrorCode
)
from typing import List, Optional, Callable, TypeVar, Union

security = HTTPBearer()
T = TypeVar('T')


class DependencyCache:
    """Elegant dependency caching with automatic cleanup"""
    
    def __init__(self):
        self._cache = {}
        self._max_size = 1000
    
    def get(self, key: str, factory: Callable[[], T]) -> T:
        """Get cached value or create new one"""
        if key not in self._cache:
            if len(self._cache) >= self._max_size:
                # Remove oldest entry
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            self._cache[key] = factory()
        
        return self._cache[key]
    
    def clear(self):
        """Clear all cached dependencies"""
        self._cache.clear()
    
    def remove(self, key: str):
        """Remove specific cached dependency"""
        if key in self._cache:
            del self._cache[key]


# Global dependency cache
dependency_cache = DependencyCache()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token with caching"""
    
    # Extract and validate JWT token
    try:
        payload = jwt_manager.verify_token(credentials.credentials, "access")
        if not payload:
            raise_authentication_error("Invalid or expired token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise_authentication_error("Missing user ID in token")
        
        try:
            user_id = int(user_id)
        except ValueError:
            raise_authentication_error("Invalid user ID format in token")
        
        # Check cache first
        cache_key = f"user:{user_id}"
        user = dependency_cache.get(cache_key, lambda: db.query(User).filter(User.id == user_id).first())
        
        if not user:
            raise_authentication_error("User not found")
        
        return user
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise_authentication_error(f"Authentication failed: {str(e)}")


def require_roles(allowed_roles: List[str]) -> Callable:
    """
    Dependency factory for role-based access control with caching.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_roles(["admin"]))):
            pass
    """
    
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise_authorization_error(
                f"Access denied. Required roles: {allowed_roles}. Your role: {user.role}",
                {"required_roles": allowed_roles, "user_role": user.role}
            )
        return user
    
    return role_checker


def require_permissions(required_permissions: List[str]) -> Callable:
    """
    Dependency factory for permission-based access control.
    
    Usage:
        @router.get("/sms-admin")
        async def sms_endpoint(user: User = Depends(require_permissions(["sms_notifications"]))):
            pass
    """
    
    def permission_checker(user: User = Depends(get_current_user)) -> User:
        user_permissions = get_user_permissions(user)
        
        missing_permissions = [perm for perm in required_permissions if perm not in user_permissions]
        if missing_permissions:
            raise_authorization_error(
                f"Access denied. Required permissions: {missing_permissions}",
                {"required_permissions": required_permissions, "user_permissions": user_permissions}
            )
        
        return user
    
    return permission_checker


def get_user_permissions(user: User) -> List[str]:
    """Get user permissions based on role"""
    role_permissions = {
        "admin": [
            "contest_management",
            "winner_selection",
            "user_management",
            "sms_notifications",
            "system_administration",
            "campaign_import",
            "audit_logs"
        ],
        "sponsor": [
            "contest_creation",
            "contest_management",
            "entry_viewing",
            "basic_analytics"
        ],
        "user": [
            "contest_entry",
            "profile_management"
        ]
    }
    
    return role_permissions.get(user.role, [])


# Convenience dependencies for common role checks
async def get_admin_user(user: User = Depends(require_roles(["admin"]))) -> User:
    """Dependency to require admin role"""
    return user


async def get_sponsor_user(user: User = Depends(require_roles(["sponsor", "admin"]))) -> User:
    """Dependency to require sponsor or admin role"""
    return user


async def get_verified_user(user: User = Depends(get_current_user)) -> User:
    """Dependency to require verified user"""
    if not user.is_verified:
        raise_authorization_error(
            "Account verification required",
            {"verification_status": user.is_verified}
        )
    return user


async def get_admin_or_sponsor(user: User = Depends(require_roles(["admin", "sponsor"]))) -> User:
    """Dependency to require admin or sponsor role"""
    return user


# Enhanced dependencies with additional validation
async def get_active_admin_user(user: User = Depends(get_admin_user)) -> User:
    """Dependency to require active admin user"""
    if not user.is_verified:
        raise_authorization_error("Admin account must be verified")
    return user


async def get_sms_admin_user(user: User = Depends(require_permissions(["sms_notifications"]))) -> User:
    """Dependency to require SMS notification permissions"""
    return user


# Legacy compatibility - keep existing admin dependency
async def get_admin_user_jwt_only(user: User = Depends(get_admin_user)) -> User:
    """Legacy admin dependency for backward compatibility"""
    return user


# Dependency decorators for common patterns
def cache_dependency(ttl_seconds: int = 300):
    """Decorator to cache dependency results"""
    def decorator(func: Callable) -> Callable:
        @lru_cache(maxsize=128)
        def cached_func(*args, **kwargs):
            return func(*args, **kwargs)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return cached_func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_user_state(required_states: List[str]):
    """Decorator to validate user state before processing"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from dependencies
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                for value in kwargs.values():
                    if isinstance(value, User):
                        user = value
                        break
            
            if user:
                missing_states = []
                if "verified" in required_states and not user.is_verified:
                    missing_states.append("verified")
                
                if missing_states:
                    raise_authorization_error(
                        f"User account requirements not met: {missing_states}",
                        {"required_states": required_states, "user_states": {"verified": user.is_verified}}
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
