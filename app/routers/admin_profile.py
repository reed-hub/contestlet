"""
Admin Profile Router for timezone preferences and admin settings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import User
from app.schemas.admin import AdminAuthResponse
from app.schemas.role_system import UserWithRole
from app.core.admin_auth import get_admin_user
from app.core.dependencies import get_admin_user as get_admin_user_dependency
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin/profile", tags=["admin-profile"])


@router.get("/", response_model=UserWithRole, deprecated=True)
async def get_admin_profile(
    admin_user: User = Depends(get_admin_user_dependency),
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: Use GET /users/me instead.
    
    Get admin's user account profile (consistent with /user/profile).
    """
    return admin_user


@router.get("/auth", response_model=AdminAuthResponse)
async def admin_auth_check(admin_user: dict = Depends(get_admin_user)):
    """Check admin authentication status"""
    return AdminAuthResponse(message="Admin authentication successful")


@router.get("/permissions")
async def get_admin_permissions(admin_user: dict = Depends(get_admin_user)):
    """Get admin permissions and capabilities"""
    return {
        "admin": True,
        "role": admin_user.get("role", "admin"),
        "user_id": admin_user.get("sub"),
        "phone": admin_user.get("phone"),
        "legacy": admin_user.get("legacy", False),
        "permissions": [
            "contest_management",
            "winner_selection", 
            "user_management",
            "sms_notifications",
            "system_administration"
        ]
    }
