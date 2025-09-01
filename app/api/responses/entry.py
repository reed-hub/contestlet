"""
Entry-specific response models with type safety.
Provides standardized responses for all entry endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.shared.types.responses import APIResponse, PaginatedResponse
from app.schemas.entry import EntryResponse


class EntryListResponse(APIResponse[PaginatedResponse[EntryResponse]]):
    """Type-safe response for entry lists with pagination"""
    pass


class EntryDetailResponse(APIResponse[EntryResponse]):
    """Type-safe response for single entry details"""
    pass


class EntryCreationResponse(APIResponse[EntryResponse]):
    """Type-safe response for entry creation"""
    pass


class EntryDeletionResponse(BaseModel):
    """Response for entry deletion operations"""
    success: bool = Field(..., description="Deletion success status")
    message: str = Field(..., description="Deletion confirmation message")
    entry_id: int = Field(..., description="ID of deleted entry")
    deleted_at: datetime = Field(..., description="Deletion timestamp")
    deleted_by: int = Field(..., description="User who performed deletion")


class EntryStatisticsResponse(APIResponse[dict]):
    """Type-safe response for entry statistics"""
    pass
