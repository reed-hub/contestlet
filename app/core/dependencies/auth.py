"""
Clean authentication dependencies.
Simplifies authentication complexity with standardized patterns.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.user import User
from app.core.services.auth_service import AuthService
from app.core.dependencies.services import get_auth_service
from app.shared.exceptions.base import AuthenticationException, AuthorizationException, ErrorCode
from app.shared.constants.auth import AuthConstants, AuthMessages

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Get the current authenticated user.
    Raises AuthenticationException if token is invalid or missing.
    """
    if not credentials:
        raise AuthenticationException(
            error_code=ErrorCode.TOKEN_MISSING,
            message=AuthMessages.MISSING_TOKEN
        )
    
    user = await auth_service.get_user_from_token(credentials.credentials)
    if not user:
        raise AuthenticationException(
            error_code=ErrorCode.TOKEN_INVALID,
            message=AuthMessages.INVALID_CREDENTIALS
        )
    
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    Get the current user if authenticated, None otherwise.
    Does not raise exceptions for missing/invalid tokens.
    """
    if not credentials:
        return None
    
    try:
        return await auth_service.get_user_from_token(credentials.credentials)
    except Exception:
        return None


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure the current user has admin role.
    Raises AuthorizationException if user is not admin.
    """
    if current_user.role != AuthConstants.ADMIN_ROLE:
        raise AuthorizationException(
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=AuthMessages.ADMIN_ACCESS_REQUIRED,
            details={
                "required_role": AuthConstants.ADMIN_ROLE,
                "user_role": current_user.role,
                "user_id": current_user.id
            }
        )
    
    return current_user


async def get_sponsor_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure the current user has sponsor role.
    Raises AuthorizationException if user is not sponsor.
    """
    if current_user.role != AuthConstants.SPONSOR_ROLE:
        raise AuthorizationException(
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=AuthMessages.SPONSOR_ACCESS_REQUIRED,
            details={
                "required_role": AuthConstants.SPONSOR_ROLE,
                "user_role": current_user.role,
                "user_id": current_user.id
            }
        )
    
    return current_user


async def get_admin_or_sponsor_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure the current user has admin or sponsor role.
    Raises AuthorizationException if user is neither admin nor sponsor.
    """
    allowed_roles = [AuthConstants.ADMIN_ROLE, AuthConstants.SPONSOR_ROLE]
    
    if current_user.role not in allowed_roles:
        raise AuthorizationException(
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message="Admin or sponsor access required",
            details={
                "allowed_roles": allowed_roles,
                "user_role": current_user.role,
                "user_id": current_user.id
            }
        )
    
    return current_user


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role("admin"))):
            ...
    """
    async def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise AuthorizationException(
                error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
                message=f"Role '{required_role}' required",
                details={
                    "required_role": required_role,
                    "user_role": current_user.role,
                    "user_id": current_user.id
                }
            )
        return current_user
    
    return role_dependency


def require_minimum_role(minimum_role: str):
    """
    Dependency factory for hierarchical role-based access control.
    
    Usage:
        @router.get("/sponsor-or-admin")
        async def privileged_endpoint(user: User = Depends(require_minimum_role("sponsor"))):
            ...
    """
    async def role_hierarchy_dependency(current_user: User = Depends(get_current_user)) -> User:
        user_level = AuthConstants.ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = AuthConstants.ROLE_HIERARCHY.get(minimum_role, 999)
        
        if user_level < required_level:
            raise AuthorizationException(
                error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
                message=f"Minimum role '{minimum_role}' required",
                details={
                    "minimum_role": minimum_role,
                    "user_role": current_user.role,
                    "user_id": current_user.id,
                    "user_level": user_level,
                    "required_level": required_level
                }
            )
        
        return current_user
    
    return role_hierarchy_dependency
