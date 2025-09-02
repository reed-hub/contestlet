"""
Universal Timezone API Endpoints

Provides timezone utilities for all user roles, extending the admin-only system
to sponsors and regular users for consistent timezone handling across the platform.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.core.dependencies.auth import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.user_timezone import (
    UserTimezonePreferences,
    UserTimezoneUpdate,
    UserTimezoneResponse,
    SupportedTimezonesResponse,
    TimezoneValidationRequest,
    TimezoneValidationResponse,
    TimezoneInfo
)
from app.shared.types.responses import APIResponse
from app.core.timezone_utils import get_supported_timezones
import pytz
from datetime import datetime

router = APIRouter(prefix="/timezone", tags=["timezone"])


@router.get("/supported", response_model=APIResponse[SupportedTimezonesResponse])
async def get_supported_timezones_list(
    current_user: Optional[User] = Depends(get_optional_user)
) -> APIResponse[SupportedTimezonesResponse]:
    """
    Get list of supported timezones for all user roles.
    
    Returns timezone information including display names, current times,
    and UTC offsets. Available to all users (authenticated or not).
    """
    try:
        # Get timezone info from utility function
        timezone_list = get_supported_timezones()
        
        # Convert to our response format
        timezone_infos = []
        for tz_info in timezone_list:
            timezone_infos.append(TimezoneInfo(
                timezone=tz_info.timezone,
                display_name=tz_info.display_name,
                current_time=tz_info.current_time,
                utc_offset=tz_info.utc_offset,
                is_dst=tz_info.is_dst
            ))
        
        # Detect user's current timezone if authenticated
        user_detected_timezone = None
        if current_user and current_user.timezone:
            user_detected_timezone = current_user.timezone
        
        response_data = SupportedTimezonesResponse(
            timezones=timezone_infos,
            default_timezone="UTC",
            user_detected_timezone=user_detected_timezone
        )
        
        return APIResponse(
            success=True,
            data=response_data,
            message="Supported timezones retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve supported timezones: {str(e)}"
        )


@router.post("/validate", response_model=APIResponse[TimezoneValidationResponse])
async def validate_timezone_endpoint(
    request: TimezoneValidationRequest,
    current_user: Optional[User] = Depends(get_optional_user)
) -> APIResponse[TimezoneValidationResponse]:
    """
    Validate a timezone identifier and return detailed information.
    
    Available to all users. Validates IANA timezone identifiers and
    returns current time, UTC offset, and display information.
    """
    try:
        timezone_id = request.timezone
        
        if timezone_id is None:
            # NULL timezone is valid (uses system default)
            return APIResponse(
                success=True,
                data=TimezoneValidationResponse(
                    timezone="UTC",
                    is_valid=True,
                    display_name="Coordinated Universal Time (UTC)",
                    current_time=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                    utc_offset="+00:00"
                ),
                message="System default timezone (UTC) is valid"
            )
        
        # Validate timezone using pytz
        try:
            tz = pytz.timezone(timezone_id)
            now = datetime.now(tz)
            
            # Get display name and UTC offset
            display_name = timezone_id.replace('_', ' ')
            utc_offset = now.strftime('%z')
            if utc_offset:
                utc_offset = f"{utc_offset[:3]}:{utc_offset[3:]}"
            else:
                utc_offset = "+00:00"
            
            return APIResponse(
                success=True,
                data=TimezoneValidationResponse(
                    timezone=timezone_id,
                    is_valid=True,
                    display_name=display_name,
                    current_time=now.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    utc_offset=utc_offset
                ),
                message="Timezone is valid"
            )
            
        except pytz.exceptions.UnknownTimeZoneError:
            return APIResponse(
                success=True,
                data=TimezoneValidationResponse(
                    timezone=timezone_id,
                    is_valid=False,
                    error_message=f"Unknown timezone: {timezone_id}"
                ),
                message="Timezone validation failed"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate timezone: {str(e)}"
        )


@router.get("/me", response_model=APIResponse[UserTimezoneResponse])
async def get_my_timezone_preferences(
    current_user: User = Depends(get_current_user)
) -> APIResponse[UserTimezoneResponse]:
    """
    Get current user's timezone preferences.
    
    Available to all authenticated users (admin, sponsor, user).
    Returns the user's timezone setting and auto-detect preference.
    """
    try:
        # Determine effective timezone
        effective_timezone = current_user.timezone or "UTC"
        
        response_data = UserTimezoneResponse(
            user_id=current_user.id,
            timezone=current_user.timezone,
            timezone_auto_detect=current_user.timezone_auto_detect,
            effective_timezone=effective_timezone,
            updated_at=current_user.updated_at
        )
        
        return APIResponse(
            success=True,
            data=response_data,
            message="Timezone preferences retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve timezone preferences: {str(e)}"
        )


@router.put("/me", response_model=APIResponse[UserTimezoneResponse])
async def update_my_timezone_preferences(
    timezone_update: UserTimezoneUpdate,
    current_user: User = Depends(get_current_user)
) -> APIResponse[UserTimezoneResponse]:
    """
    Update current user's timezone preferences.
    
    Available to all authenticated users (admin, sponsor, user).
    This is a convenience endpoint that updates only timezone fields.
    For full profile updates, use PUT /users/me instead.
    """
    try:
        from app.core.services.user_service import UserService
        from app.schemas.role_system import UnifiedProfileUpdate
        from app.database.database import get_db
        from sqlalchemy.orm import Session
        
        # Create a profile update with only timezone fields
        profile_update = UnifiedProfileUpdate(
            timezone=timezone_update.timezone,
            timezone_auto_detect=timezone_update.timezone_auto_detect
        )
        
        # Get database session and create user service
        db: Session = next(get_db())
        user_service = UserService(user_repo=None, db=db)
        updated_user = await user_service.update_user_profile(
            user_id=current_user.id,
            profile_update=profile_update,
            user_role=current_user.role
        )
        
        # Determine effective timezone
        effective_timezone = updated_user.timezone or "UTC"
        
        response_data = UserTimezoneResponse(
            user_id=updated_user.id,
            timezone=updated_user.timezone,
            timezone_auto_detect=updated_user.timezone_auto_detect,
            effective_timezone=effective_timezone,
            updated_at=updated_user.updated_at
        )
        
        return APIResponse(
            success=True,
            data=response_data,
            message="Timezone preferences updated successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update timezone preferences: {str(e)}"
        )
