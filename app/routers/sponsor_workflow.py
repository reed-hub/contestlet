"""
Enhanced Sponsor Workflow Endpoints

New endpoints for the enhanced contest status system that supports
draft creation, submission workflow, and status management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.database import get_db
from app.models.user import User
from app.models.contest import Contest
from app.schemas.admin import AdminContestCreate, AdminContestUpdate, AdminContestResponse
from app.schemas.contest_status import (
    ContestSubmissionRequest, ContestStatusResponse, 
    StatusTransitionRequest, ContestStatusAuditResponse
)
from app.core.dependencies import get_admin_or_sponsor_user
from app.services.contest_service import ContestService
from app.core.contest_status import ContestStatus, can_edit_contest, can_delete_contest
from app.core.datetime_utils import utc_now

router = APIRouter(prefix="/sponsor/workflow", tags=["sponsor-workflow"])


# =====================================================
# DRAFT CONTEST MANAGEMENT
# =====================================================

@router.post("/contests/draft", response_model=AdminContestResponse)
async def create_draft_contest(
    contest_data: AdminContestCreate,
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
):
    """Create a new contest in draft status for iterative development"""
    contest_service = ContestService(db)
    
    # Create contest in draft status
    contest = contest_service.create_draft_contest(contest_data, current_user.id)
    
    # Prepare response
    response_data = {
        **contest.__dict__,
        "entry_count": 0,  # New draft has no entries
        "official_rules": contest.official_rules
    }
    
    return AdminContestResponse(**response_data)


@router.put("/contests/{contest_id}/draft", response_model=AdminContestResponse)
async def update_draft_contest(
    contest_id: int,
    contest_update: AdminContestUpdate,
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
):
    """Update a draft contest (only allowed for draft/rejected status)"""
    contest_service = ContestService(db)
    
    # Get existing contest
    contest = contest_service.get_contest_by_id(contest_id)
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Verify ownership (admins can edit any contest for customer support)
    if current_user.role != "admin" and contest.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own contests"
        )
    
    # Check if contest can be edited
    if not can_edit_contest(contest.status, "sponsor", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot edit contest with status '{contest.status}'. Only draft and rejected contests can be edited."
        )
    
    # Update contest using existing service method
    updated_contest = contest_service.update_contest(contest_id, contest_update, current_user.id)
    
    # Prepare response
    response_data = {
        **updated_contest.__dict__,
        "entry_count": len(updated_contest.entries) if updated_contest.entries else 0,
        "official_rules": updated_contest.official_rules
    }
    
    return AdminContestResponse(**response_data)


@router.get("/contests/drafts", response_model=List[AdminContestResponse])
async def get_draft_contests(
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
):
    """Get all draft and rejected contests (admins see all, sponsors see their own)"""
    query = db.query(Contest).filter(
        Contest.status.in_([ContestStatus.DRAFT, ContestStatus.REJECTED])
    )
    
    # Sponsors only see their own contests, admins see all for customer support
    if current_user.role != "admin":
        query = query.filter(Contest.created_by_user_id == current_user.id)
    
    contests = query.order_by(Contest.updated_at.desc()).all()
    
    # Convert to response format
    contest_responses = []
    for contest in contests:
        response_data = {
            **contest.__dict__,
            "entry_count": len(contest.entries) if contest.entries else 0,
            "official_rules": contest.official_rules
        }
        contest_responses.append(AdminContestResponse(**response_data))
    
    return contest_responses


# =====================================================
# SUBMISSION WORKFLOW
# =====================================================

@router.post("/contests/{contest_id}/submit", response_model=ContestStatusResponse)
async def submit_contest_for_approval(
    contest_id: int,
    submission_request: ContestSubmissionRequest,
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
):
    """Submit a draft contest for admin approval"""
    contest_service = ContestService(db)
    
    # Get contest and verify ownership
    contest = contest_service.get_contest_by_id(contest_id)
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Verify ownership (admins can submit any contest for customer support)
    if current_user.role != "admin" and contest.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit your own contests"
        )
    
    try:
        # Submit for approval
        updated_contest = contest_service.submit_contest_for_approval(
            contest_id, current_user.id, submission_request.message
        )
        
        # Add audit message for admin assistance
        message = "Contest submitted for admin approval"
        if current_user.role == "admin":
            message += f" (admin assistance for contest {contest_id})"
        
        return ContestStatusResponse(
            contest_id=contest_id,
            old_status=ContestStatus.DRAFT,
            new_status=updated_contest.status,
            changed_by_user_id=current_user.id,
            changed_at=utc_now(),
            message=message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/contests/{contest_id}/withdraw", response_model=ContestStatusResponse)
async def withdraw_contest_submission(
    contest_id: int,
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
):
    """Withdraw a contest from approval queue (back to draft)"""
    contest_service = ContestService(db)
    
    # Get contest and verify ownership
    contest = contest_service.get_contest_by_id(contest_id)
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Verify ownership (admins can withdraw any contest for customer support)
    if current_user.role != "admin" and contest.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only withdraw your own contests"
        )
    
    if contest.status != ContestStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot withdraw contest with status '{contest.status}'"
        )
    
    # Transition back to draft
    withdrawal_message = "Contest withdrawn from approval queue"
    if current_user.role == "admin":
        withdrawal_message += f" (admin assistance for contest {contest_id})"
    
    updated_contest = contest_service.transition_contest_status(
        contest_id, ContestStatus.DRAFT, current_user.id, current_user.role,
        withdrawal_message
    )
    
    return ContestStatusResponse(
        contest_id=contest_id,
        old_status=ContestStatus.AWAITING_APPROVAL,
        new_status=updated_contest.status,
        changed_by_user_id=current_user.id,
        changed_at=utc_now(),
        message=withdrawal_message
    )


# =====================================================
# STATUS TRACKING
# =====================================================

@router.get("/contests/{contest_id}/status", response_model=ContestStatusResponse)
async def get_contest_status(
    contest_id: int,
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
):
    """Get current status of a contest"""
    contest_service = ContestService(db)
    
    contest = contest_service.get_contest_by_id(contest_id)
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Verify ownership (admins can view any contest status for customer support)
    if current_user.role != "admin" and contest.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view status of your own contests"
        )
    
    return ContestStatusResponse(
        contest_id=contest_id,
        new_status=contest.status,
        changed_at=contest.updated_at or contest.created_at,
        message=f"Contest is currently {contest.status}"
    )


@router.get("/contests/{contest_id}/status-history", response_model=List[ContestStatusAuditResponse])
async def get_contest_status_history(
    contest_id: int,
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
):
    """Get status change history for a contest"""
    # Verify contest ownership
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Verify ownership (admins can access any contest for customer support)
    if current_user.role != "admin" and contest.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view history of your own contests"
        )
    
    # Get status audit trail
    from app.models.contest_status_audit import ContestStatusAudit
    audit_entries = db.query(ContestStatusAudit).filter(
        ContestStatusAudit.contest_id == contest_id
    ).order_by(ContestStatusAudit.created_at.desc()).all()
    
    # Convert to response format
    return [
        ContestStatusAuditResponse(
            id=entry.id,
            contest_id=entry.contest_id,
            old_status=entry.old_status,
            new_status=entry.new_status,
            changed_by_user_id=entry.changed_by_user_id,
            reason=entry.reason,
            created_at=entry.created_at
        )
        for entry in audit_entries
    ]


# =====================================================
# ENHANCED CONTEST MANAGEMENT
# =====================================================

@router.get("/contests/pending", response_model=List[AdminContestResponse])
async def get_pending_contests(
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
):
    """Get contests awaiting approval (admins see all, sponsors see their own)"""
    query = db.query(Contest).filter(
        Contest.status == ContestStatus.AWAITING_APPROVAL
    )
    
    # Sponsors only see their own contests, admins see all for customer support
    if current_user.role != "admin":
        query = query.filter(Contest.created_by_user_id == current_user.id)
    
    contests = query.order_by(Contest.updated_at.desc()).all()
    
    # Convert to response format
    contest_responses = []
    for contest in contests:
        response_data = {
            **contest.__dict__,
            "entry_count": len(contest.entries) if contest.entries else 0,
            "official_rules": contest.official_rules
        }
        contest_responses.append(AdminContestResponse(**response_data))
    
    return contest_responses


@router.delete("/contests/{contest_id}/draft")
async def delete_draft_contest(
    contest_id: int,
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
):
    """Delete a draft contest (only allowed for draft/rejected status)"""
    contest_service = ContestService(db)
    
    # Get contest and verify ownership
    contest = contest_service.get_contest_by_id(contest_id)
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Verify ownership (admins can access any contest for customer support)
    if current_user.role != "admin" and contest.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own contests"
        )
    
    # Check if contest can be deleted
    has_entries = len(contest.entries) > 0 if contest.entries else False
    if not can_delete_contest(contest.status, "sponsor", True, has_entries):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot delete contest with status '{contest.status}'"
        )
    
    # Delete contest
    success = contest_service.delete_contest(contest_id)
    
    if success:
        return {"message": "Draft contest deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete contest"
        )
