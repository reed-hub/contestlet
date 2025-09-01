"""
Contest-specific response models with type safety.
Provides standardized responses for all contest endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.shared.types.responses import APIResponse, PaginatedResponse
from app.schemas.contest import ContestResponse


class ContestDetailResponse(APIResponse[ContestResponse]):
    """Type-safe response for single contest details"""
    pass


class ContestListResponse(APIResponse[PaginatedResponse[ContestResponse]]):
    """Type-safe response for contest lists with pagination"""
    pass


class ContestCreationResponse(APIResponse[ContestResponse]):
    """Type-safe response for contest creation"""
    pass


class ContestUpdateResponse(APIResponse[ContestResponse]):
    """Type-safe response for contest updates"""
    pass


class ContestDeletionResponse(BaseModel):
    """Response for contest deletion operations"""
    success: bool = Field(..., description="Deletion success status")
    message: str = Field(..., description="Deletion confirmation message")
    contest_id: int = Field(..., description="ID of deleted contest")
    contest_name: str = Field(..., description="Name of deleted contest")
    deleted_at: datetime = Field(..., description="Deletion timestamp")
    deleted_by: dict = Field(..., description="User who performed deletion")
    cleanup_summary: Optional[dict] = Field(None, description="Cleanup operation summary")


class ContestEntryResponse(BaseModel):
    """Response for contest entry operations"""
    success: bool = Field(..., description="Entry success status")
    message: str = Field(..., description="Entry confirmation message")
    contest_id: int = Field(..., description="Contest ID")
    entry_id: int = Field(..., description="Entry ID")
    user_id: int = Field(..., description="User ID")
    entered_at: datetime = Field(..., description="Entry timestamp")


class ContestStatusResponse(BaseModel):
    """Response for contest status operations"""
    success: bool = Field(..., description="Status update success")
    message: str = Field(..., description="Status update message")
    contest_id: int = Field(..., description="Contest ID")
    old_status: str = Field(..., description="Previous status")
    new_status: str = Field(..., description="New status")
    updated_at: datetime = Field(..., description="Update timestamp")
    updated_by: Optional[int] = Field(None, description="User who updated status")


class ContestProtectionResponse(BaseModel):
    """Response when contest is protected from deletion"""
    success: bool = Field(False, description="Always false for protection")
    error: str = Field(..., description="Protection error code")
    message: str = Field(..., description="Protection reason message")
    contest_id: int = Field(..., description="Contest ID")
    contest_name: str = Field(..., description="Contest name")
    protection_reason: str = Field(..., description="Protection reason code")
    protection_errors: List[str] = Field(..., description="List of protection reasons")
    details: dict = Field(..., description="Detailed contest status information")


class NearbyContestsResponse(APIResponse[PaginatedResponse[ContestResponse]]):
    """Type-safe response for nearby contests with location data"""
    pass


class ActiveContestsResponse(APIResponse[PaginatedResponse[ContestResponse]]):
    """Type-safe response for active contests"""
    pass
