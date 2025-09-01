"""
Clean, refactored unified user profile endpoints.
Uses new clean architecture with service layer and proper error handling.
"""

from fastapi import APIRouter, Depends, Path
from typing import Union, Optional

from app.core.services.user_service import UserService
from app.core.dependencies.auth import get_current_user, get_admin_user
from app.core.dependencies.services import get_user_service
from app.models.user import User
from app.shared.types.pagination import PaginationParams, UserFilterParams
from app.shared.types.responses import APIResponse, PaginatedResponse
from app.api.responses.user import (
    UserProfileResponse,
    UserListResponse,
    UserUpdateResponse,
    SponsorListResponse
)
from app.schemas.role_system import (
    UserWithRole, 
    UnifiedSponsorProfileResponse,
    UnifiedProfileUpdate
)
from app.schemas.auth import UserMeResponse
from app.shared.constants.auth import AuthConstants, AuthMessages

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> UserProfileResponse:
    """
    Get current user's profile information.
    Clean controller with service delegation and type safety.
    """
    profile = await user_service.get_user_profile(current_user.id)
    
    # Return appropriate response based on role
    if profile.role == AuthConstants.SPONSOR_ROLE and profile.sponsor_profile:
        profile_data = UnifiedSponsorProfileResponse(
            user_id=profile.id,
            phone=profile.phone,
            role=profile.role,
            is_verified=profile.is_verified,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            role_assigned_at=profile.role_assigned_at,
            full_name=profile.full_name,
            email=profile.email,
            bio=profile.bio,
            company_profile=profile.sponsor_profile
        )
    else:
        profile_data = UserWithRole(
            id=profile.id,
            phone=profile.phone,
            role=profile.role,
            is_verified=profile.is_verified,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            role_assigned_at=profile.role_assigned_at,
            created_by_user_id=profile.created_by_user_id,
            role_assigned_by=profile.role_assigned_by,
            full_name=profile.full_name,
            email=profile.email,
            bio=profile.bio
        )
    
    return UserProfileResponse(
        success=True,
        data=profile_data,
        message="User profile retrieved successfully"
    )


@router.put("/me", response_model=UserUpdateResponse)
async def update_my_profile(
    profile_update: UnifiedProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> UserUpdateResponse:
    """
    Update current user's profile information.
    Handles all user roles with comprehensive profile updates.
    """
    updated_profile = await user_service.update_user_profile(
        user_id=current_user.id,
        profile_update=profile_update,
        user_role=current_user.role
    )
    
    # Return appropriate response based on role
    if updated_profile.role == AuthConstants.SPONSOR_ROLE and updated_profile.sponsor_profile:
        profile_data = UnifiedSponsorProfileResponse(
            user_id=updated_profile.id,
            phone=updated_profile.phone,
            role=updated_profile.role,
            is_verified=updated_profile.is_verified,
            created_at=updated_profile.created_at,
            updated_at=updated_profile.updated_at,
            role_assigned_at=updated_profile.role_assigned_at,
            full_name=updated_profile.full_name,
            email=updated_profile.email,
            bio=updated_profile.bio,
            company_profile=updated_profile.sponsor_profile
        )
    else:
        profile_data = UserWithRole(
            id=updated_profile.id,
            phone=updated_profile.phone,
            role=updated_profile.role,
            is_verified=updated_profile.is_verified,
            created_at=updated_profile.created_at,
            updated_at=updated_profile.updated_at,
            role_assigned_at=updated_profile.role_assigned_at,
            created_by_user_id=updated_profile.created_by_user_id,
            role_assigned_by=updated_profile.role_assigned_by,
            full_name=updated_profile.full_name,
            email=updated_profile.email,
            bio=updated_profile.bio
        )
    
    return UserUpdateResponse(
        success=True,
        data=profile_data,
        message="Profile updated successfully"
    )


@router.get("/", response_model=UserListResponse)
async def get_all_users(
    pagination: PaginationParams = Depends(),
    filters: UserFilterParams = Depends(),
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
) -> UserListResponse:
    """
    Get all users with pagination and filtering (admin only).
    Clean controller with service delegation.
    """
    users = await user_service.get_all_users_paginated(
        pagination=pagination,
        filters=filters
    )
    
    return UserListResponse(
        success=True,
        data=users,
        message="Users retrieved successfully"
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_by_id(
    user_id: int = Path(..., gt=0, description="User ID"),
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
) -> UserProfileResponse:
    """
    Get specific user by ID (admin only).
    Uses clean service delegation with proper authorization.
    """
    user = await user_service.get_user_profile(user_id)
    
    # Return appropriate response based on role
    if user.role == AuthConstants.SPONSOR_ROLE and user.sponsor_profile:
        profile_data = UnifiedSponsorProfileResponse(
            user_id=user.id,
            phone=user.phone,
            role=user.role,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            role_assigned_at=user.role_assigned_at,
            full_name=user.full_name,
            email=user.email,
            bio=user.bio,
            company_profile=user.sponsor_profile
        )
    else:
        profile_data = UserWithRole(
            id=user.id,
            phone=user.phone,
            role=user.role,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            role_assigned_at=user.role_assigned_at,
            created_by_user_id=user.created_by_user_id,
            role_assigned_by=user.role_assigned_by,
            full_name=user.full_name,
            email=user.email,
            bio=user.bio
        )
    
    return UserProfileResponse(
        success=True,
        data=profile_data,
        message="User profile retrieved successfully"
    )


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int = Path(..., gt=0, description="User ID"),
    new_role: str = Path(..., description="New role to assign"),
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
) -> APIResponse[dict]:
    """
    Update user role (admin only).
    Uses service layer with proper validation.
    """
    updated_user = await user_service.update_user_role(
        user_id=user_id,
        new_role=new_role,
        admin_user_id=admin_user.id
    )
    
    return APIResponse(
        success=True,
        data={
            "user_id": updated_user.id,
            "old_role": "previous_role",  # Could be tracked in service
            "new_role": updated_user.role,
            "updated_by": admin_user.id
        },
        message=f"User role updated to {new_role} successfully"
    )


@router.get("/sponsors", response_model=SponsorListResponse)
async def get_all_sponsors(
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
) -> SponsorListResponse:
    """
    Get all verified sponsor profiles for admin use.
    Clean endpoint with service delegation.
    """
    sponsors = await user_service.get_all_sponsors()
    
    sponsor_data = [
        {
            "id": sponsor.sponsor_profile.id if sponsor.sponsor_profile else sponsor.id,
            "company_name": sponsor.sponsor_profile.company_name if sponsor.sponsor_profile else "No Company",
            "contact_name": sponsor.sponsor_profile.contact_name if sponsor.sponsor_profile else sponsor.full_name,
            "contact_email": sponsor.sponsor_profile.contact_email if sponsor.sponsor_profile else sponsor.email,
            "user_id": sponsor.id,
            "is_verified": sponsor.sponsor_profile.is_verified if sponsor.sponsor_profile else False
        } for sponsor in sponsors
    ]
    
    return SponsorListResponse(
        success=True,
        data=sponsor_data,
        message="Sponsors retrieved successfully"
    )


# Legacy compatibility endpoint
@router.get("/me/basic", response_model=APIResponse[UserMeResponse])
async def get_basic_user_info(
    current_user: User = Depends(get_current_user)
) -> APIResponse[UserMeResponse]:
    """
    DEPRECATED: Use GET /users/me instead.
    Basic user info compatible with /auth/me format.
    """
    user_data = UserMeResponse(
        user_id=current_user.id,
        phone=current_user.phone,
        role=current_user.role,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )
    
    return APIResponse(
        success=True,
        data=user_data,
        message="Basic user info retrieved successfully"
    )
