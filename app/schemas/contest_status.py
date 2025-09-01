"""
Contest Status Management Schemas

Schemas for managing contest status transitions, approvals, and workflow.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class StatusTransitionRequest(BaseModel):
    """Request to transition contest to a new status"""
    new_status: str = Field(..., description="Target status to transition to")
    reason: Optional[str] = Field(None, description="Reason for status change")
    
    @validator('new_status')
    def validate_status(cls, v):
        from app.core.contest_status import ContestStatus
        valid_statuses = [status.value for status in ContestStatus]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v


class ContestApprovalRequest(BaseModel):
    """Request to approve a contest"""
    approved: bool = Field(..., description="Whether to approve or reject")
    reason: Optional[str] = Field(None, description="Reason for approval/rejection")
    
    @validator('reason')
    def validate_reason(cls, v, values):
        # Require reason for rejections
        if not values.get('approved', True) and not v:
            raise ValueError('Reason is required when rejecting a contest')
        return v


class ContestSubmissionRequest(BaseModel):
    """Request to submit contest for approval"""
    message: Optional[str] = Field(None, description="Optional message to admin reviewers")


class ContestStatusResponse(BaseModel):
    """Response with contest status information"""
    contest_id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by_user_id: Optional[int] = None
    reason: Optional[str] = None
    changed_at: datetime
    success: bool = True
    message: str = "Status updated successfully"


class ApprovalQueueItem(BaseModel):
    """Contest item in admin approval queue"""
    contest_id: int
    name: str
    description: Optional[str] = None
    created_by_user_id: int
    creator_name: Optional[str] = None
    sponsor_company: Optional[str] = None
    submitted_at: datetime
    start_time: datetime
    end_time: datetime
    prize_description: Optional[str] = None
    entry_method: str = "sms"
    contest_type: str = "general"
    
    # Computed fields
    days_pending: int = Field(..., description="Days since submission")
    priority: str = Field(..., description="Priority level based on start date")
    
    class Config:
        from_attributes = True


class ApprovalQueueResponse(BaseModel):
    """Response for approval queue listing"""
    pending_contests: List[ApprovalQueueItem]
    total_pending: int
    average_approval_time_days: Optional[float] = None
    oldest_pending_days: Optional[int] = None
    
    class Config:
        from_attributes = True


class ContestStatusAuditResponse(BaseModel):
    """Response for contest status audit trail"""
    id: int
    contest_id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by_user_id: Optional[int] = None
    changed_by_name: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class StatusStatistics(BaseModel):
    """Statistics about contest statuses"""
    total_contests: int
    by_status: dict = Field(..., description="Count of contests by status")
    recent_transitions: List[ContestStatusAuditResponse] = Field(..., description="Recent status changes")
    
    # Workflow metrics
    avg_approval_time_hours: Optional[float] = None
    pending_approval_count: int = 0
    rejection_rate_percent: Optional[float] = None
    
    class Config:
        from_attributes = True
