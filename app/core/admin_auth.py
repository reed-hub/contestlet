from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.auth import verify_token

security = HTTPBearer()


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify admin authentication token using JWT with role checking.
    Supports both legacy admin tokens and new role-based JWT tokens.
    """
    token = credentials.credentials
    
    # First try JWT token with role verification
    payload = verify_token(token)
    if payload and payload.get("role") == "admin":
        return payload
    
    # Fallback to legacy admin token for backward compatibility
    if token == settings.ADMIN_TOKEN:
        return {
            "sub": "legacy_admin",
            "role": "admin",
            "phone": "legacy",
            "legacy": True
        }
    
    # Neither JWT admin nor legacy token
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid admin credentials. Admin access required.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_admin_user(
    admin_payload: dict = Depends(verify_admin_token)
) -> dict:
    """
    Get admin user information from JWT payload.
    Returns admin user details with permissions.
    """
    return {
        "admin": True,
        "role": "admin",
        "user_id": admin_payload.get("sub"),
        "phone": admin_payload.get("phone"),
        "legacy": admin_payload.get("legacy", False),
        "permissions": ["contest_management", "winner_selection", "user_management"]
    }
