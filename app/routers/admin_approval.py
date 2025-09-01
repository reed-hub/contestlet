"""
Admin Approval Workflow Endpoints

New endpoints for admins to manage contest approvals in the enhanced
status system with dedicated approval queue and workflow management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.database.database import get_db
from app.models.user import User
from app.models.contest import Contest
from app.models.contest_status_audit import ContestStatusAudit
from app.schemas.contest_status import (
    ContestApprovalRequest, ContestStatusResponse, ApprovalQueueResponse,
    ApprovalQueueItem, StatusStatistics, ContestStatusAuditResponse
)
from app.core.admin_auth import get_admin_user
from app.services.contest_service import ContestService
from app.core.contest_status import ContestStatus
from app.core.datetime_utils import utc_now

router = APIRouter(prefix="/admin/approval", tags=["admin-approval"])


# =====================================================
# APPROVAL QUEUE MANAGEMENT
# =====================================================

@router.get("/queue", response_model=ApprovalQueueResponse)
async def get_approval_queue(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get contests awaiting approval with detailed information"""
    
    # Get contests awaiting approval with related data
    query = db.query(Contest).options(
        joinedload(Contest.creator),
        joinedload(Contest.sponsor_profile),
        joinedload(Contest.official_rules)
    ).filter(
        Contest.status == ContestStatus.AWAITING_APPROVAL
    ).order_by(Contest.submitted_at.asc())  # Oldest submissions first for FIFO processing
    
    # Get total count
    total_pending = query.count()
    
    # Apply pagination
    contests = query.offset((page - 1) * size).limit(size).all()
    
    # Convert to approval queue items
    queue_items = []
    now = utc_now()
    
    for contest in contests:
        # Calculate days pending
        submitted_at = contest.submitted_at or contest.created_at
        
        # Ensure both datetimes are timezone-aware for comparison
        if submitted_at.tzinfo is None:
            from datetime import timezone
            submitted_at = submitted_at.replace(tzinfo=timezone.utc)
        
        days_pending = (now - submitted_at).days
        
        # Determine priority based on start date
        start_time = contest.start_time
        if start_time.tzinfo is None:
            from datetime import timezone
            start_time = start_time.replace(tzinfo=timezone.utc)
        
        days_until_start = (start_time - now).days if start_time > now else 0
        if days_until_start <= 7:
            priority = "high"
        elif days_until_start <= 30:
            priority = "medium"
        else:
            priority = "low"
        
        # Get creator info
        creator_name = None
        sponsor_company = None
        if contest.creator:
            creator_name = contest.creator.full_name or contest.creator.phone
            if contest.sponsor_profile:
                sponsor_company = contest.sponsor_profile.company_name
        
        queue_item = ApprovalQueueItem(
            contest_id=contest.id,
            name=contest.name,
            description=contest.description,
            created_by_user_id=contest.created_by_user_id or 1,  # Default to admin user if None
            creator_name=creator_name,
            sponsor_company=sponsor_company,
            submitted_at=submitted_at,
            start_time=contest.start_time,
            end_time=contest.end_time,
            prize_description=contest.prize_description,
            entry_method=contest.entry_method or "sms",
            contest_type=contest.contest_type or "general",
            days_pending=days_pending,
            priority=priority
        )
        queue_items.append(queue_item)
    
    # Calculate approval statistics
    avg_approval_time = None
    oldest_pending_days = None
    
    if queue_items:
        oldest_pending_days = max(item.days_pending for item in queue_items)
        
        # Calculate average approval time from recent approvals
        recent_approvals = db.query(ContestStatusAudit).filter(
            ContestStatusAudit.new_status.in_([
                ContestStatus.UPCOMING, ContestStatus.ACTIVE
            ]),
            ContestStatusAudit.old_status == ContestStatus.AWAITING_APPROVAL,
            ContestStatusAudit.created_at >= now - timedelta(days=30)
        ).all()
        
        if recent_approvals:
            approval_times = []
            for approval in recent_approvals:
                # Find when it was submitted for approval
                submission = db.query(ContestStatusAudit).filter(
                    ContestStatusAudit.contest_id == approval.contest_id,
                    ContestStatusAudit.new_status == ContestStatus.AWAITING_APPROVAL
                ).first()
                
                if submission:
                    approval_time = (approval.created_at - submission.created_at).total_seconds() / 3600
                    approval_times.append(approval_time)
            
            if approval_times:
                avg_approval_time = sum(approval_times) / len(approval_times)
    
    return ApprovalQueueResponse(
        pending_contests=queue_items,
        total_pending=total_pending,
        average_approval_time_days=avg_approval_time / 24 if avg_approval_time else None,
        oldest_pending_days=oldest_pending_days
    )


# =====================================================
# APPROVAL ACTIONS
# =====================================================

@router.post("/contests/{contest_id}/approve", response_model=ContestStatusResponse)
async def approve_contest(
    contest_id: int,
    approval_request: ContestApprovalRequest,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Approve or reject a contest"""
    contest_service = ContestService(db)
    admin_user_id = int(admin_user["user_id"]) if admin_user["user_id"] != "legacy_admin" else 1
    
    try:
        if approval_request.approved:
            # Approve the contest
            updated_contest = contest_service.approve_contest(
                contest_id, admin_user_id, approval_request.reason
            )
            
            return ContestStatusResponse(
                contest_id=contest_id,
                old_status=ContestStatus.AWAITING_APPROVAL,
                new_status=updated_contest.status,
                changed_by_user_id=admin_user_id,
                changed_at=utc_now(),
                message=f"Contest approved and set to {updated_contest.status}"
            )
        else:
            # Reject the contest
            updated_contest = contest_service.reject_contest(
                contest_id, admin_user_id, approval_request.reason
            )
            
            return ContestStatusResponse(
                contest_id=contest_id,
                old_status=ContestStatus.AWAITING_APPROVAL,
                new_status=updated_contest.status,
                changed_by_user_id=admin_user_id,
                changed_at=utc_now(),
                message="Contest rejected and returned to sponsor"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/contests/bulk-approve")
async def bulk_approve_contests(
    contest_ids: List[int],
    approval_request: ContestApprovalRequest,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Bulk approve or reject multiple contests"""
    contest_service = ContestService(db)
    admin_user_id = int(admin_user["user_id"]) if admin_user["user_id"] != "legacy_admin" else 1
    
    results = []
    errors = []
    
    for contest_id in contest_ids:
        try:
            if approval_request.approved:
                updated_contest = contest_service.approve_contest(
                    contest_id, admin_user_id, approval_request.reason
                )
                results.append({
                    "contest_id": contest_id,
                    "status": "approved",
                    "new_status": updated_contest.status
                })
            else:
                updated_contest = contest_service.reject_contest(
                    contest_id, admin_user_id, approval_request.reason
                )
                results.append({
                    "contest_id": contest_id,
                    "status": "rejected",
                    "new_status": updated_contest.status
                })
                
        except Exception as e:
            errors.append({
                "contest_id": contest_id,
                "error": str(e)
            })
    
    return {
        "success_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors
    }


# =====================================================
# STATUS MANAGEMENT
# =====================================================

@router.post("/contests/{contest_id}/status", response_model=ContestStatusResponse)
async def change_contest_status(
    contest_id: int,
    status_request: dict,  # Simple dict for flexibility
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Change contest status (admin override)"""
    contest_service = ContestService(db)
    admin_user_id = int(admin_user["user_id"]) if admin_user["user_id"] != "legacy_admin" else 1
    
    new_status = status_request.get("status")
    reason = status_request.get("reason", "Admin status change")
    
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    try:
        updated_contest = contest_service.transition_contest_status(
            contest_id, new_status, admin_user_id, "admin", reason
        )
        
        return ContestStatusResponse(
            contest_id=contest_id,
            old_status=updated_contest.status,  # This will be the old status in audit
            new_status=new_status,
            changed_by_user_id=admin_user_id,
            changed_at=utc_now(),
            message=f"Contest status changed to {new_status}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =====================================================
# STATISTICS AND REPORTING
# =====================================================

@router.get("/statistics", response_model=StatusStatistics)
async def get_approval_statistics(
    days: int = Query(30, ge=1, le=365, description="Days to include in statistics"),
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive approval workflow statistics"""
    
    now = utc_now()
    since_date = now - timedelta(days=days)
    
    # Get total contest counts by status
    status_counts = db.query(
        Contest.status,
        func.count(Contest.id).label('count')
    ).group_by(Contest.status).all()
    
    by_status = {status: count for status, count in status_counts}
    total_contests = sum(by_status.values())
    
    # Get recent status transitions
    recent_transitions = db.query(ContestStatusAudit).options(
        joinedload(ContestStatusAudit.changed_by)
    ).filter(
        ContestStatusAudit.created_at >= since_date
    ).order_by(desc(ContestStatusAudit.created_at)).limit(20).all()
    
    transition_responses = []
    for audit in recent_transitions:
        changed_by_name = None
        if audit.changed_by:
            changed_by_name = f"{audit.changed_by.first_name} {audit.changed_by.last_name}".strip()
        
        transition_responses.append(ContestStatusAuditResponse(
            id=audit.id,
            contest_id=audit.contest_id,
            old_status=audit.old_status,
            new_status=audit.new_status,
            changed_by_user_id=audit.changed_by_user_id,
            changed_by_name=changed_by_name,
            reason=audit.reason,
            created_at=audit.created_at
        ))
    
    # Calculate approval metrics
    pending_count = by_status.get(ContestStatus.AWAITING_APPROVAL, 0)
    
    # Calculate average approval time
    approvals = db.query(ContestStatusAudit).filter(
        ContestStatusAudit.new_status.in_([
            ContestStatus.UPCOMING, ContestStatus.ACTIVE
        ]),
        ContestStatusAudit.old_status == ContestStatus.AWAITING_APPROVAL,
        ContestStatusAudit.created_at >= since_date
    ).all()
    
    avg_approval_time_hours = None
    if approvals:
        approval_times = []
        for approval in approvals:
            # Find submission time
            submission = db.query(ContestStatusAudit).filter(
                ContestStatusAudit.contest_id == approval.contest_id,
                ContestStatusAudit.new_status == ContestStatus.AWAITING_APPROVAL,
                ContestStatusAudit.created_at <= approval.created_at
            ).order_by(desc(ContestStatusAudit.created_at)).first()
            
            if submission:
                hours = (approval.created_at - submission.created_at).total_seconds() / 3600
                approval_times.append(hours)
        
        if approval_times:
            avg_approval_time_hours = sum(approval_times) / len(approval_times)
    
    # Calculate rejection rate
    rejections = db.query(ContestStatusAudit).filter(
        ContestStatusAudit.new_status == ContestStatus.REJECTED,
        ContestStatusAudit.created_at >= since_date
    ).count()
    
    total_decisions = len(approvals) + rejections
    rejection_rate = (rejections / total_decisions * 100) if total_decisions > 0 else None
    
    return StatusStatistics(
        total_contests=total_contests,
        by_status=by_status,
        recent_transitions=transition_responses,
        avg_approval_time_hours=avg_approval_time_hours,
        pending_approval_count=pending_count,
        rejection_rate_percent=rejection_rate
    )


@router.get("/contests/{contest_id}/audit", response_model=List[ContestStatusAuditResponse])
async def get_contest_audit_trail(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get complete audit trail for a contest"""
    
    # Verify contest exists
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Get audit trail
    audit_entries = db.query(ContestStatusAudit).options(
        joinedload(ContestStatusAudit.changed_by)
    ).filter(
        ContestStatusAudit.contest_id == contest_id
    ).order_by(desc(ContestStatusAudit.created_at)).all()
    
    # Convert to response format
    responses = []
    for audit in audit_entries:
        changed_by_name = None
        if audit.changed_by:
            changed_by_name = f"{audit.changed_by.first_name} {audit.changed_by.last_name}".strip()
        
        responses.append(ContestStatusAuditResponse(
            id=audit.id,
            contest_id=audit.contest_id,
            old_status=audit.old_status,
            new_status=audit.new_status,
            changed_by_user_id=audit.changed_by_user_id,
            changed_by_name=changed_by_name,
            reason=audit.reason,
            created_at=audit.created_at
        ))
    
    return responses


# =====================================================
# BATCH OPERATIONS
# =====================================================

@router.post("/update-statuses")
async def update_contest_statuses(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Batch update contest statuses based on current time"""
    contest_service = ContestService(db)
    
    updated_count = contest_service.update_contest_statuses()
    
    return {
        "message": f"Updated {updated_count} contest statuses",
        "updated_count": updated_count,
        "updated_at": utc_now()
    }
