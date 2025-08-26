"""
Unified User Profile Endpoints

Single endpoint for all user profile operations regardless of role.
Replaces role-specific endpoints:
- PUT /user/profile
- PUT /sponsor/profile  
- PUT /admin/profile

Uses RLS for security - users can only access their own data.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Union
from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas.role_system import (
    UserWithRole, 
    UnifiedSponsorProfileResponse,
    SponsorProfileUpdate
)
from app.schemas.auth import UserMeResponse
from app.core.datetime_utils import utc_now

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=Union[UserWithRole, UnifiedSponsorProfileResponse])
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile information.
    
    Returns different response formats based on user role:
    - Admin/User: UserWithRole (basic user info)
    - Sponsor: UnifiedSponsorProfileResponse (includes company profile)
    
    Security: RLS ensures users can only access their own data.
    """
    # Reload user with sponsor_profile relationship to avoid session issues
    from sqlalchemy.orm import joinedload
    user_with_profile = db.query(User).options(
        joinedload(User.sponsor_profile)
    ).filter(User.id == current_user.id).first()
    
    if not user_with_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_with_profile.role == "sponsor" and user_with_profile.sponsor_profile:
        # Return unified sponsor profile
        return UnifiedSponsorProfileResponse(
            user_id=user_with_profile.id,
            phone=user_with_profile.phone,
            role=user_with_profile.role,
            is_verified=user_with_profile.is_verified,
            created_at=user_with_profile.created_at,
            role_assigned_at=user_with_profile.role_assigned_at,
            company_profile=user_with_profile.sponsor_profile
        )
    else:
        # Return basic user profile for admin/user roles
        return UserWithRole(
            id=user_with_profile.id,
            phone=user_with_profile.phone,
            role=user_with_profile.role,
            is_verified=user_with_profile.is_verified,
            created_at=user_with_profile.created_at,
            role_assigned_at=user_with_profile.role_assigned_at,
            created_by_user_id=user_with_profile.created_by_user_id
        )


@router.put("/me", response_model=Union[UserWithRole, UnifiedSponsorProfileResponse])
async def update_my_profile(
    profile_update: SponsorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.
    
    Handles all user roles in a single endpoint:
    - Admin/User: Limited profile updates (future expansion)
    - Sponsor: Full company profile updates
    
    Security: RLS ensures users can only update their own data.
    """
    # Reload user with sponsor_profile relationship to avoid session issues
    from sqlalchemy.orm import joinedload
    user_with_profile = db.query(User).options(
        joinedload(User.sponsor_profile)
    ).filter(User.id == current_user.id).first()
    
    if not user_with_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_with_profile.role == "sponsor":
        # Handle sponsor profile updates
        if not user_with_profile.sponsor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sponsor profile not found. Contact admin to set up sponsor profile."
            )
        
        # Update sponsor profile fields
        update_data = profile_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user_with_profile.sponsor_profile, field):
                setattr(user_with_profile.sponsor_profile, field, value)
        
        user_with_profile.sponsor_profile.updated_at = utc_now()
        
        db.commit()
        db.refresh(user_with_profile.sponsor_profile)
        db.refresh(user_with_profile)  # Refresh the user object too
        
        # Return unified sponsor profile response
        return UnifiedSponsorProfileResponse(
            user_id=user_with_profile.id,
            phone=user_with_profile.phone,
            role=user_with_profile.role,
            is_verified=user_with_profile.is_verified,
            created_at=user_with_profile.created_at,
            role_assigned_at=user_with_profile.role_assigned_at,
            company_profile=user_with_profile.sponsor_profile
        )
    
    else:
        # Handle admin/user profile updates
        # Currently limited - future expansion for name, email, preferences, etc.
        
        # For now, just return current user info
        # Future: Allow updating name, email, preferences, etc.
        
        return UserWithRole(
            id=user_with_profile.id,
            phone=user_with_profile.phone,
            role=user_with_profile.role,
            is_verified=user_with_profile.is_verified,
            created_at=user_with_profile.created_at,
            role_assigned_at=user_with_profile.role_assigned_at,
            created_by_user_id=user_with_profile.created_by_user_id
        )


# Legacy compatibility endpoints - will be deprecated
# These redirect to the unified endpoints above

@router.get("/me/basic", response_model=UserMeResponse, deprecated=True)
async def get_basic_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    DEPRECATED: Use GET /users/me instead.
    
    Basic user info compatible with /auth/me format.
    """
    return UserMeResponse(
        user_id=current_user.id,
        phone=current_user.phone,
        role=current_user.role,
        authenticated=True
    )
