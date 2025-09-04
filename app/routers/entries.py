"""
Clean, refactored entries API endpoints.
Uses new clean architecture with service layer and proper error handling.
"""

from fastapi import APIRouter, Depends, Path, Query
from typing import List, Optional

from app.core.services.entry_service import EntryService
from app.core.dependencies.auth import get_current_user, get_admin_user
from app.core.dependencies.services import get_entry_service
from app.models.user import User
from app.shared.types.pagination import PaginationParams
from app.shared.types.responses import APIResponse, PaginatedResponse
from app.api.responses.entry import EntryListResponse, EntryDetailResponse
from app.schemas.entry import EntryResponse

router = APIRouter(prefix="/entries", tags=["entries"])


@router.get("/me", response_model=EntryListResponse)
async def get_my_entries(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    entry_service: EntryService = Depends(get_entry_service)
) -> EntryListResponse:
    """
    Get all contest entries for the current user with pagination.
    Clean controller with service delegation and type safety.
    """
    paginated_result = await entry_service.get_user_entries(
        user_id=current_user.id,
        pagination=pagination
    )
    
    # Convert Entry models to EntryResponse schemas
    entry_responses = [
        EntryResponse.model_validate(entry) for entry in paginated_result.items
    ]
    
    # Create PaginatedResponse
    from app.shared.types.responses import PaginatedResponse, PaginationMeta
    paginated_response = PaginatedResponse[EntryResponse](
        items=entry_responses,
        pagination=PaginationMeta(
            total=paginated_result.total,
            page=paginated_result.page,
            size=paginated_result.size,
            total_pages=paginated_result.total_pages,
            has_next=paginated_result.has_next,
            has_prev=paginated_result.has_prev
        )
    )
    
    return EntryListResponse(
        success=True,
        data=paginated_response,
        message="User entries retrieved successfully"
    )


@router.get("/contest/{contest_id}", response_model=EntryListResponse)
async def get_contest_entries(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    pagination: PaginationParams = Depends(),
    admin_user: User = Depends(get_admin_user),
    entry_service: EntryService = Depends(get_entry_service)
) -> EntryListResponse:
    """
    Get all entries for a specific contest (admin only).
    Uses admin authentication and proper pagination.
    """
    paginated_result = await entry_service.get_contest_entries(
        contest_id=contest_id,
        pagination=pagination
    )
    
    # Convert Entry models to EntryResponse schemas
    entry_responses = [
        EntryResponse.model_validate(entry) for entry in paginated_result.items
    ]
    
    # Create PaginatedResponse
    from app.shared.types.responses import PaginatedResponse, PaginationMeta
    paginated_response = PaginatedResponse[EntryResponse](
        items=entry_responses,
        pagination=PaginationMeta(
            total=paginated_result.total,
            page=paginated_result.page,
            size=paginated_result.size,
            total_pages=paginated_result.total_pages,
            has_next=paginated_result.has_next,
            has_prev=paginated_result.has_prev
        )
    )
    
    return EntryListResponse(
        success=True,
        data=paginated_response,
        message=f"Contest {contest_id} entries retrieved successfully"
    )


@router.get("/{entry_id}", response_model=EntryDetailResponse)
async def get_entry_details(
    entry_id: int = Path(..., gt=0, description="Entry ID"),
    current_user: User = Depends(get_current_user),
    entry_service: EntryService = Depends(get_entry_service)
) -> EntryDetailResponse:
    """
    Get details for a specific entry.
    Users can only view their own entries, admins can view any entry.
    """
    entry = await entry_service.get_entry_details(
        entry_id=entry_id,
        requesting_user_id=current_user.id,
        user_role=current_user.role
    )
    
    return EntryDetailResponse(
        success=True,
        data=entry,
        message="Entry details retrieved successfully"
    )


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: int = Path(..., gt=0, description="Entry ID"),
    current_user: User = Depends(get_current_user),
    entry_service: EntryService = Depends(get_entry_service)
) -> APIResponse[dict]:
    """
    Delete a specific entry.
    Users can only delete their own entries, admins can delete any entry.
    """
    await entry_service.delete_entry(
        entry_id=entry_id,
        requesting_user_id=current_user.id,
        user_role=current_user.role
    )
    
    return APIResponse(
        success=True,
        data={"entry_id": entry_id},
        message="Entry deleted successfully"
    )
