from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.core.auth import verify_token
from app.models.user import User
from typing import List, Optional

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        try:
            user_id = int(user_id)
        except ValueError:
            raise credentials_exception
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        
        return user
    
    except HTTPException:
        # Re-raise HTTP exceptions (like 401) as-is
        raise
    except Exception as e:
        # Convert any other exceptions to 401 to prevent 500 errors
        print(f"🚨 JWT validation error: {e}")
        raise credentials_exception


def require_roles(allowed_roles: List[str]):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_roles(["admin"]))):
            pass
    """
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}. Your role: {user.role}"
            )
        return user
    
    return role_checker


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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account verification required"
        )
    return user


async def get_admin_or_sponsor(user: User = Depends(require_roles(["admin", "sponsor"]))) -> User:
    """Dependency to require admin or sponsor role"""
    return user


# Legacy compatibility - keep existing admin dependency
async def get_admin_user_jwt_only(user: User = Depends(get_admin_user)) -> User:
    """Legacy admin dependency for backward compatibility"""
    return user
