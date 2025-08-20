"""
Admin Profile Router for timezone preferences and admin settings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.models.admin_profile import AdminProfile
from app.schemas.timezone import (
    AdminProfileResponse, AdminProfileCreate, AdminProfileUpdate,
    TimezoneInfo, TimezoneListResponse
)
from app.core.admin_auth import get_admin_user
from app.core.timezone_utils import get_supported_timezones, validate_timezone

router = APIRouter(prefix="/admin/profile", tags=["admin-profile"])


@router.get("/timezones", response_model=TimezoneListResponse)
async def get_supported_timezones_list():
    """
    Get list of supported timezones with current time information.
    
    This endpoint provides the frontend with timezone options for admin preferences.
    Includes current time, UTC offset, and DST status for each timezone.
    """
    try:
        timezones = get_supported_timezones()
        
        return TimezoneListResponse(
            timezones=timezones,
            default_timezone="UTC",
            auto_detected_timezone=None  # Frontend will detect this
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load timezone information: {str(e)}"
        )


@router.get("/timezone", response_model=AdminProfileResponse)
async def get_admin_timezone_preferences(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get current admin's timezone preferences.
    
    Returns the admin's stored timezone preferences or creates default preferences
    if none exist yet.
    """
    admin_user_id = admin_user.get("sub", "unknown")
    
    # Try to find existing profile
    profile = db.query(AdminProfile).filter(
        AdminProfile.admin_user_id == admin_user_id
    ).first()
    
    if not profile:
        # Create default profile
        profile = AdminProfile(
            admin_user_id=admin_user_id,
            timezone="UTC",
            timezone_auto_detect=True
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return profile


@router.post("/timezone", response_model=AdminProfileResponse)
async def create_or_update_admin_timezone_preferences(
    preferences: AdminProfileCreate,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create or update admin timezone preferences.
    
    Sets the admin's preferred timezone for contest creation and display.
    All contest times will be converted to/from this timezone automatically.
    """
    admin_user_id = admin_user.get("sub", "unknown")
    
    # Validate timezone
    if not validate_timezone(preferences.timezone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timezone: {preferences.timezone}"
        )
    
    # Check if profile already exists
    profile = db.query(AdminProfile).filter(
        AdminProfile.admin_user_id == admin_user_id
    ).first()
    
    if profile:
        # Update existing profile
        profile.timezone = preferences.timezone
        profile.timezone_auto_detect = preferences.timezone_auto_detect
    else:
        # Create new profile
        profile = AdminProfile(
            admin_user_id=admin_user_id,
            timezone=preferences.timezone,
            timezone_auto_detect=preferences.timezone_auto_detect
        )
        db.add(profile)
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.put("/timezone", response_model=AdminProfileResponse)
async def update_admin_timezone_preferences(
    preferences: AdminProfileUpdate,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Partially update admin timezone preferences.
    
    Allows updating individual preference fields without affecting others.
    """
    admin_user_id = admin_user.get("sub", "unknown")
    
    # Find existing profile
    profile = db.query(AdminProfile).filter(
        AdminProfile.admin_user_id == admin_user_id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin profile not found. Create preferences first."
        )
    
    # Update provided fields
    if preferences.timezone is not None:
        if not validate_timezone(preferences.timezone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timezone: {preferences.timezone}"
            )
        profile.timezone = preferences.timezone
    
    if preferences.timezone_auto_detect is not None:
        profile.timezone_auto_detect = preferences.timezone_auto_detect
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.delete("/timezone")
async def reset_admin_timezone_preferences(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reset admin timezone preferences to defaults.
    
    Removes custom preferences and reverts to UTC timezone with auto-detect enabled.
    """
    admin_user_id = admin_user.get("sub", "unknown")
    
    # Find and delete existing profile
    profile = db.query(AdminProfile).filter(
        AdminProfile.admin_user_id == admin_user_id
    ).first()
    
    if profile:
        db.delete(profile)
        db.commit()
    
    return {"message": "Timezone preferences reset to defaults"}


@router.get("/", response_model=AdminProfileResponse)
async def get_admin_profile(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get complete admin profile information.
    
    Currently focuses on timezone preferences but can be extended for other settings.
    """
    # For now, this is the same as getting timezone preferences
    return await get_admin_timezone_preferences(admin_user, db)
