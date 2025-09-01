"""
Clean, refactored contests API endpoints.
Demonstrates the new clean architecture with thin controllers.
"""

from fastapi import APIRouter, Depends, Query, Path
from typing import Optional

from app.core.services.contest_service import ContestService
from app.core.dependencies.auth import get_current_user, get_optional_user
from app.core.dependencies.services import get_contest_service
from app.models.user import User
from app.shared.types.pagination import PaginationParams, ContestFilterParams
from app.shared.types.responses import APIResponse
from app.api.responses.contest import (
    ContestListResponse,
    ContestDetailResponse,
    ContestEntryResponse,
    ContestDeletionResponse,
    NearbyContestsResponse,
    ActiveContestsResponse
)
from app.shared.constants.contest import ContestConstants, ContestMessages
from app.shared.exceptions.base import raise_not_found, raise_validation_error

router = APIRouter(prefix="/contests", tags=["contests"])


@router.get("/active", response_model=ActiveContestsResponse)
async def get_active_contests(
    pagination: PaginationParams = Depends(),
    filters: ContestFilterParams = Depends(),
    contest_service: ContestService = Depends(get_contest_service)
) -> ActiveContestsResponse:
    """
    Get currently active contests with pagination and filtering.
    Clean controller with single responsibility - delegates to service layer.
    """
    contests = await contest_service.get_active_contests(pagination, filters)
    
    return ActiveContestsResponse(
        success=True,
        data=contests,
        message="Active contests retrieved successfully"
    )


@router.get("/nearby", response_model=NearbyContestsResponse)
async def get_nearby_contests(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius: float = Query(
        default=ContestConstants.DEFAULT_SEARCH_RADIUS_MILES,
        ge=ContestConstants.MIN_SEARCH_RADIUS,
        le=ContestConstants.MAX_SEARCH_RADIUS,
        description="Search radius in miles"
    ),
    pagination: PaginationParams = Depends(),
    contest_service: ContestService = Depends(get_contest_service)
) -> NearbyContestsResponse:
    """
    Get contests near a specific location.
    Uses constants for validation and clean service delegation.
    """
    contests = await contest_service.get_nearby_contests(
        latitude=lat,
        longitude=lng,
        radius_miles=radius,
        pagination=pagination
    )
    
    return NearbyContestsResponse(
        success=True,
        data=contests,
        message=f"Found {contests.total} contests within {radius} miles"
    )


@router.get("/{contest_id}", response_model=ContestDetailResponse)
async def get_contest_details(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    current_user: Optional[User] = Depends(get_optional_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestDetailResponse:
    """
    Get public details for a specific contest.
    No authentication required, but user context provided if available.
    """
    contest = await contest_service.get_contest_details(contest_id, current_user)
    
    return ContestDetailResponse(
        success=True,
        data=contest,
        message="Contest details retrieved successfully"
    )


@router.post("/{contest_id}/enter", response_model=ContestEntryResponse)
async def enter_contest(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    current_user: User = Depends(get_current_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestEntryResponse:
    """
    Enter the current user into a contest.
    All business logic delegated to service layer.
    """
    entry = await contest_service.enter_contest(contest_id, current_user.id)
    
    return ContestEntryResponse(
        success=True,
        message=ContestMessages.ENTRY_SUCCESSFUL,
        contest_id=contest_id,
        entry_id=entry.id,
        user_id=current_user.id,
        entered_at=entry.created_at
    )


@router.delete("/{contest_id}", response_model=ContestDeletionResponse)
async def delete_contest(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    current_user: User = Depends(get_current_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestDeletionResponse:
    """
    Delete a contest with proper authorization and business rules.
    Clean delegation to service layer for all business logic.
    """
    deletion_result = await contest_service.delete_contest(
        contest_id=contest_id,
        user_id=current_user.id,
        user_role=current_user.role
    )
    
    return ContestDeletionResponse(
        success=True,
        message=ContestMessages.DELETED_SUCCESSFULLY,
        contest_id=contest_id,
        contest_name=deletion_result.contest_name,
        deleted_at=deletion_result.deleted_at,
        deleted_by={
            "user_id": current_user.id,
            "role": current_user.role
        },
        cleanup_summary=deletion_result.cleanup_summary
    )
