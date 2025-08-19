from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security = HTTPBearer()


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> bool:
    """
    Verify admin authentication token.
    For now, this uses a simple hardcoded token.
    In production, implement proper admin user management.
    """
    if credentials.credentials != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token. Access denied.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True


async def get_admin_user(
    admin_verified: bool = Depends(verify_admin_token)
) -> dict:
    """
    Get admin user information.
    Returns a simple admin user dict for now.
    """
    return {
        "admin": True,
        "permissions": ["contest_management", "winner_selection", "user_management"]
    }
