"""
Clean, refactored sponsor workflow endpoints.
Uses new clean architecture with service layer and proper error handling.
"""

from fastapi import APIRouter, Depends, Path, Query
from typing import List, Optional

from app.core.services.contest_service import ContestService
from app.core.services.sponsor_service import SponsorService
from app.core.dependencies.auth import get_sponsor_user
from app.core.dependencies.services import get_contest_service, get_sponsor_service
from app.models.user import User
from app.shared.types.pagination import PaginationParams, ContestFilterParams
from app.shared.types.responses import APIResponse
from app.api.responses.contest import (
    ContestListResponse,
    ContestDetailResponse,
    ContestCreationResponse,
    ContestUpdateResponse,
    ContestStatusResponse
)
from app.schemas.contest import ContestCreate, ContestUpdate
from app.schemas.contest_status import ContestSubmissionRequest, StatusTransitionRequest
from app.shared.constants.contest import ContestConstants, ContestMessages

router = APIRouter(prefix="/sponsor/workflow", tags=["sponsor-workflow"])


# =====================================================
# DRAFT CONTEST MANAGEMENT
# =====================================================

@router.post("/contests/draft", response_model=ContestCreationResponse)
async def create_draft_contest(
    contest_data: ContestCreate,
    sponsor_user: User = Depends(get_sponsor_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestCreationResponse:
    """
    Create a new draft contest.
    Clean controller with service delegation and validation.
    """
    draft_contest = await contest_service.create_draft_contest(
        contest_data=contest_data,
        sponsor_user_id=sponsor_user.id
    )
    
    return ContestCreationResponse(
        success=True,
        data=draft_contest,
        message=ContestMessages.DRAFT_CREATED
    )


@router.get("/contests/drafts", response_model=ContestListResponse)
async def get_sponsor_drafts(
    pagination: PaginationParams = Depends(),
    sponsor_user: User = Depends(get_sponsor_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestListResponse:
    """
    Get all draft contests for the sponsor.
    Clean controller with pagination and filtering.
    """
    drafts = await contest_service.get_sponsor_drafts(
        sponsor_user_id=sponsor_user.id,
        pagination=pagination
    )
    
    return ContestListResponse(
        success=True,
        data=drafts,
        message="Draft contests retrieved successfully"
    )


@router.put("/contests/{contest_id}/draft", response_model=ContestUpdateResponse)
async def update_draft_contest(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    contest_data: ContestUpdate = ...,
    sponsor_user: User = Depends(get_sponsor_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestUpdateResponse:
    """
    Update a draft contest.
    Clean controller with proper authorization and validation.
    """
    updated_contest = await contest_service.update_draft_contest(
        contest_id=contest_id,
        contest_data=contest_data,
        sponsor_user_id=sponsor_user.id
    )
    
    return ContestUpdateResponse(
        success=True,
        data=updated_contest,
        message=ContestMessages.DRAFT_UPDATED
    )


# =====================================================
# SUBMISSION WORKFLOW
# =====================================================

@router.post("/contests/{contest_id}/submit", response_model=ContestStatusResponse)
async def submit_contest_for_approval(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    submission_data: ContestSubmissionRequest = ...,
    sponsor_user: User = Depends(get_sponsor_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestStatusResponse:
    """
    Submit contest for admin approval.
    Clean controller with workflow validation.
    """
    submission_result = await contest_service.submit_contest_for_approval(
        contest_id=contest_id,
        submission_notes=submission_data.submission_notes,
        sponsor_user_id=sponsor_user.id
    )
    
    return ContestStatusResponse(
        success=True,
        data=submission_result,
        message=ContestMessages.SUBMITTED_FOR_APPROVAL
    )


@router.post("/contests/{contest_id}/withdraw", response_model=ContestStatusResponse)
async def withdraw_contest_submission(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    sponsor_user: User = Depends(get_sponsor_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestStatusResponse:
    """
    Withdraw contest from approval queue.
    Clean controller with proper authorization.
    """
    withdrawal_result = await contest_service.withdraw_contest_submission(
        contest_id=contest_id,
        sponsor_user_id=sponsor_user.id
    )
    
    return ContestStatusResponse(
        success=True,
        data=withdrawal_result,
        message=ContestMessages.SUBMISSION_WITHDRAWN
    )


# =====================================================
# CONTEST MANAGEMENT
# =====================================================

@router.get("/contests", response_model=ContestListResponse)
async def get_sponsor_contests(
    pagination: PaginationParams = Depends(),
    filters: ContestFilterParams = Depends(),
    sponsor_user: User = Depends(get_sponsor_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestListResponse:
    """
    Get all contests for the sponsor with filtering.
    Clean controller with comprehensive filtering support.
    """
    contests = await contest_service.get_sponsor_contests(
        sponsor_user_id=sponsor_user.id,
        pagination=pagination,
        filters=filters
    )
    
    return ContestListResponse(
        success=True,
        data=contests,
        message="Sponsor contests retrieved successfully"
    )


@router.get("/contests/{contest_id}", response_model=ContestDetailResponse)
async def get_sponsor_contest_detail(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    sponsor_user: User = Depends(get_sponsor_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestDetailResponse:
    """
    Get detailed contest information for sponsor.
    Clean controller with authorization and detailed data.
    """
    contest_detail = await contest_service.get_sponsor_contest_detail(
        contest_id=contest_id,
        sponsor_user_id=sponsor_user.id
    )
    
    return ContestDetailResponse(
        success=True,
        data=contest_detail,
        message="Contest details retrieved successfully"
    )


@router.put("/contests/{contest_id}", response_model=ContestUpdateResponse)
async def update_sponsor_contest(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    contest_data: ContestUpdate = ...,
    sponsor_user: User = Depends(get_sponsor_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestUpdateResponse:
    """
    Update sponsor contest (if editable).
    Clean controller with status-aware editing.
    """
    updated_contest = await contest_service.update_sponsor_contest(
        contest_id=contest_id,
        contest_data=contest_data,
        sponsor_user_id=sponsor_user.id
    )
    
    return ContestUpdateResponse(
        success=True,
        data=updated_contest,
        message=ContestMessages.CONTEST_UPDATED
    )


# =====================================================
# STATUS AND ANALYTICS
# =====================================================

@router.get("/contests/{contest_id}/status", response_model=ContestStatusResponse)
async def get_contest_status(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    sponsor_user: User = Depends(get_sponsor_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestStatusResponse:
    """
    Get contest status and workflow information.
    Clean controller with detailed status information.
    """
    status_info = await contest_service.get_contest_status_info(
        contest_id=contest_id,
        user_id=sponsor_user.id,
        user_role=sponsor_user.role
    )
    
    return ContestStatusResponse(
        success=True,
        data=status_info,
        message="Contest status retrieved successfully"
    )


@router.get("/dashboard", response_model=APIResponse[dict])
async def get_sponsor_dashboard(
    sponsor_user: User = Depends(get_sponsor_user),
    sponsor_service: SponsorService = Depends(get_sponsor_service)
) -> APIResponse[dict]:
    """
    Get sponsor dashboard with statistics and recent activity.
    Clean controller with service delegation.
    """
    dashboard_data = await sponsor_service.get_sponsor_dashboard(
        sponsor_user_id=sponsor_user.id
    )
    
    return APIResponse(
        success=True,
        data=dashboard_data,
        message="Sponsor dashboard retrieved successfully"
    )


@router.get("/analytics", response_model=APIResponse[dict])
async def get_sponsor_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics"),
    sponsor_user: User = Depends(get_sponsor_user),
    sponsor_service: SponsorService = Depends(get_sponsor_service)
) -> APIResponse[dict]:
    """
    Get sponsor analytics and performance metrics.
    Clean controller with configurable time ranges.
    """
    analytics_data = await sponsor_service.get_sponsor_analytics(
        sponsor_user_id=sponsor_user.id,
        days=days
    )
    
    return APIResponse(
        success=True,
        data=analytics_data,
        message=f"Analytics for last {days} days retrieved successfully"
    )


# =====================================================
# PROFILE MANAGEMENT
# =====================================================

@router.get("/profile", response_model=APIResponse[dict])
async def get_sponsor_profile(
    sponsor_user: User = Depends(get_sponsor_user),
    sponsor_service: SponsorService = Depends(get_sponsor_service)
) -> APIResponse[dict]:
    """
    Get sponsor profile information.
    Clean controller with comprehensive profile data.
    """
    profile_data = await sponsor_service.get_sponsor_profile(
        sponsor_user_id=sponsor_user.id
    )
    
    return APIResponse(
        success=True,
        data=profile_data,
        message="Sponsor profile retrieved successfully"
    )


@router.put("/profile", response_model=APIResponse[dict])
async def update_sponsor_profile(
    profile_data: dict,  # Could be a proper Pydantic model
    sponsor_user: User = Depends(get_sponsor_user),
    sponsor_service: SponsorService = Depends(get_sponsor_service)
) -> APIResponse[dict]:
    """
    Update sponsor profile information.
    Clean controller with validation and authorization.
    """
    updated_profile = await sponsor_service.update_sponsor_profile(
        sponsor_user_id=sponsor_user.id,
        profile_data=profile_data
    )
    
    return APIResponse(
        success=True,
        data=updated_profile,
        message="Sponsor profile updated successfully"
    )
