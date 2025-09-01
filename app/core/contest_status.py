"""
Contest Status Management Utilities

This module provides utilities for calculating and managing contest status
in the enhanced status system that separates publication workflow from
contest lifecycle.
"""

from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class ContestStatus(str, Enum):
    """Enhanced contest status enumeration"""
    # Publication workflow statuses
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    REJECTED = "rejected"
    
    # Published contest lifecycle statuses
    UPCOMING = "upcoming"
    ACTIVE = "active"
    ENDED = "ended"
    COMPLETE = "complete"
    
    # Administrative statuses
    CANCELLED = "cancelled"


def calculate_contest_status(
    current_status: str,
    start_time: datetime,
    end_time: datetime,
    winner_selected_at: Optional[datetime] = None,
    now: Optional[datetime] = None
) -> str:
    """
    Calculate the appropriate contest status based on current state and time.
    
    Args:
        current_status: Current status in database
        start_time: Contest start time
        end_time: Contest end time
        winner_selected_at: When winner was selected (if any)
        now: Current time (defaults to utc_now)
    
    Returns:
        Calculated contest status
    """
    if now is None:
        now = datetime.now(timezone.utc)
    
    # Ensure datetime objects are timezone-aware
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    
    # Publication workflow statuses don't change based on time
    if current_status in [ContestStatus.DRAFT, ContestStatus.AWAITING_APPROVAL, ContestStatus.REJECTED]:
        return current_status
    
    # Administrative statuses are permanent
    if current_status == ContestStatus.CANCELLED:
        return current_status
    
    # For published contests, calculate lifecycle status based on time and winner
    if winner_selected_at:
        return ContestStatus.COMPLETE
    elif end_time <= now:
        return ContestStatus.ENDED
    elif start_time > now:
        return ContestStatus.UPCOMING
    else:
        return ContestStatus.ACTIVE


def is_published_status(status: str) -> bool:
    """Check if a status represents a published contest"""
    return status in [
        ContestStatus.UPCOMING,
        ContestStatus.ACTIVE,
        ContestStatus.ENDED,
        ContestStatus.COMPLETE
    ]


def is_draft_status(status: str) -> bool:
    """Check if a status represents a draft/unpublished contest"""
    return status in [
        ContestStatus.DRAFT,
        ContestStatus.AWAITING_APPROVAL,
        ContestStatus.REJECTED
    ]


def can_edit_contest(status: str, user_role: str, is_creator: bool = False) -> bool:
    """
    Determine if a contest can be edited based on status and user permissions.
    
    Args:
        status: Current contest status
        user_role: User's role (admin, sponsor, user)
        is_creator: Whether user is the contest creator
    
    Returns:
        True if contest can be edited
    """
    # Admins can always edit (with override for active contests)
    if user_role == "admin":
        return True
    
    # Sponsors can only edit their own contests
    if user_role == "sponsor" and is_creator:
        # Can edit draft and rejected contests freely
        if status in [ContestStatus.DRAFT, ContestStatus.REJECTED]:
            return True
        # Cannot edit once submitted for approval or published
        return False
    
    # Regular users cannot edit contests
    return False


def can_delete_contest(
    status: str, 
    user_role: str, 
    is_creator: bool = False,
    has_entries: bool = False
) -> bool:
    """
    Determine if a contest can be deleted based on status and conditions.
    
    Args:
        status: Current contest status
        user_role: User's role (admin, sponsor, user)
        is_creator: Whether user is the contest creator
        has_entries: Whether contest has any entries
    
    Returns:
        True if contest can be deleted
    """
    # Regular users cannot delete contests
    if user_role not in ["admin", "sponsor"]:
        return False
    
    # Sponsors can only delete their own contests
    if user_role == "sponsor" and not is_creator:
        return False
    
    # Cannot delete contests with entries (protection rule)
    if has_entries:
        return False
    
    # Cannot delete active or complete contests
    if status in [ContestStatus.ACTIVE, ContestStatus.COMPLETE]:
        return False
    
    # Can delete draft, rejected, awaiting approval, upcoming, or ended contests (without entries)
    return True


def can_enter_contest(status: str) -> bool:
    """Check if users can enter a contest based on its status"""
    return status == ContestStatus.ACTIVE


def get_status_display_info(status: str) -> dict:
    """Get display information for a contest status"""
    status_info = {
        ContestStatus.DRAFT: {
            "label": "Draft",
            "description": "Contest is being prepared",
            "color": "gray",
            "icon": "edit"
        },
        ContestStatus.AWAITING_APPROVAL: {
            "label": "Awaiting Approval",
            "description": "Submitted for admin review",
            "color": "yellow",
            "icon": "clock"
        },
        ContestStatus.REJECTED: {
            "label": "Rejected",
            "description": "Needs revision before resubmission",
            "color": "red",
            "icon": "x-circle"
        },
        ContestStatus.UPCOMING: {
            "label": "Upcoming",
            "description": "Scheduled to start soon",
            "color": "blue",
            "icon": "calendar"
        },
        ContestStatus.ACTIVE: {
            "label": "Active",
            "description": "Currently accepting entries",
            "color": "green",
            "icon": "play-circle"
        },
        ContestStatus.ENDED: {
            "label": "Ended",
            "description": "No longer accepting entries",
            "color": "orange",
            "icon": "stop-circle"
        },
        ContestStatus.COMPLETE: {
            "label": "Complete",
            "description": "Winner has been selected",
            "color": "purple",
            "icon": "trophy"
        },
        ContestStatus.CANCELLED: {
            "label": "Cancelled",
            "description": "Contest has been cancelled",
            "color": "red",
            "icon": "x-circle"
        }
    }
    
    return status_info.get(status, {
        "label": status.title(),
        "description": "Unknown status",
        "color": "gray",
        "icon": "help-circle"
    })


def get_next_possible_statuses(current_status: str, user_role: str) -> list:
    """Get list of possible next statuses based on current status and user role"""
    transitions = {
        ContestStatus.DRAFT: {
            "sponsor": [ContestStatus.AWAITING_APPROVAL],
            "admin": [ContestStatus.AWAITING_APPROVAL, ContestStatus.UPCOMING, ContestStatus.ACTIVE]
        },
        ContestStatus.AWAITING_APPROVAL: {
            "admin": [ContestStatus.UPCOMING, ContestStatus.ACTIVE, ContestStatus.REJECTED]
        },
        ContestStatus.REJECTED: {
            "sponsor": [ContestStatus.AWAITING_APPROVAL],
            "admin": [ContestStatus.UPCOMING, ContestStatus.ACTIVE]
        },
        ContestStatus.UPCOMING: {
            "admin": [ContestStatus.ACTIVE, ContestStatus.CANCELLED]
        },
        ContestStatus.ACTIVE: {
            "admin": [ContestStatus.ENDED, ContestStatus.COMPLETE, ContestStatus.CANCELLED]
        },
        ContestStatus.ENDED: {
            "admin": [ContestStatus.COMPLETE]
        }
    }
    
    return transitions.get(current_status, {}).get(user_role, [])
