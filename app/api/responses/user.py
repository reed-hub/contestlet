"""
User-specific response models with type safety.
Provides standardized responses for all user endpoints.
"""

from typing import List, Union
from datetime import datetime
from pydantic import BaseModel, Field

from app.shared.types.responses import APIResponse, PaginatedResponse
from app.schemas.role_system import UserWithRole, UnifiedSponsorProfileResponse
from app.schemas.auth import UserMeResponse


class UserProfileResponse(APIResponse[Union[UserWithRole, UnifiedSponsorProfileResponse]]):
    """Type-safe response for user profile (adapts based on role)"""
    pass


class UserUpdateResponse(APIResponse[Union[UserWithRole, UnifiedSponsorProfileResponse]]):
    """Type-safe response for user profile updates"""
    pass


class UserListResponse(APIResponse[PaginatedResponse[UserWithRole]]):
    """Type-safe response for user lists with pagination"""
    pass


class UserRoleUpdateResponse(BaseModel):
    """Response for user role update operations"""
    success: bool = Field(..., description="Update success status")
    message: str = Field(..., description="Update confirmation message")
    user_id: int = Field(..., description="Updated user ID")
    old_role: str = Field(..., description="Previous role")
    new_role: str = Field(..., description="New role")
    updated_by: int = Field(..., description="Admin who performed update")
    updated_at: datetime = Field(..., description="Update timestamp")


class SponsorInfo(BaseModel):
    """Sponsor information for admin use"""
    id: int = Field(..., description="Sponsor profile ID")
    company_name: str = Field(..., description="Company name")
    contact_name: str = Field(..., description="Contact person name")
    contact_email: str = Field(..., description="Contact email")
    user_id: int = Field(..., description="Associated user ID")
    is_verified: bool = Field(..., description="Verification status")


class SponsorListResponse(APIResponse[List[SponsorInfo]]):
    """Type-safe response for sponsor lists"""
    pass


class UserStatisticsResponse(APIResponse[dict]):
    """Type-safe response for user statistics"""
    pass


class BasicUserResponse(APIResponse[UserMeResponse]):
    """Type-safe response for basic user info (legacy compatibility)"""
    pass
