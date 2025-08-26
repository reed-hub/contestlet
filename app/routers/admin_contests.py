from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminContestCreate, AdminContestUpdate, AdminContestResponse,
    AdminEntryResponse, WinnerSelectionResponse, WinnerNotificationResponse,
    ContestDeleteResponse, ContestDeletionSummary
)
from app.schemas.role_system import UserWithRole
from app.core.admin_auth import get_admin_user
from app.core.dependencies import get_admin_user as get_admin_user_dependency
from app.core.exceptions import raise_authorization_error
from app.services.contest_service import ContestService
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin/contests", tags=["admin-contests"])


@router.post("/", response_model=AdminContestResponse)
async def create_contest(
    contest_data: AdminContestCreate,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new contest with admin validation"""
    contest_service = ContestService(db)
    contest = contest_service.create_contest(contest_data, admin_user["sub"])
    return AdminContestResponse.from_orm(contest)


@router.put("/{contest_id}", response_model=AdminContestResponse)
async def update_contest(
    contest_id: int,
    contest_data: AdminContestUpdate,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update existing contest"""
    contest_service = ContestService(db)
    contest = contest_service.update_contest(contest_id, contest_data)
    return AdminContestResponse.from_orm(contest)


@router.get("/", response_model=List[AdminContestResponse])
async def get_all_contests(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all contests with admin access"""
    contest_service = ContestService(db)
    contests = contest_service.get_all_contests()
    return [AdminContestResponse.from_orm(contest) for contest in contests]


@router.get("/{contest_id}/entries", response_model=List[AdminEntryResponse])
async def get_contest_entries(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all entries for a specific contest"""
    contest_service = ContestService(db)
    entries = contest_service.get_contest_entries(contest_id)
    return [AdminEntryResponse.from_orm(entry) for entry in entries]


@router.post("/{contest_id}/select-winner", response_model=WinnerSelectionResponse)
async def select_winner(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Select a random winner for a contest"""
    contest_service = ContestService(db)
    winner = contest_service.select_winner(contest_id, admin_user["sub"])
    
    if not winner:
        return WinnerSelectionResponse(
            success=False,
            message="No eligible entries found for winner selection"
        )
    
    return WinnerSelectionResponse(
        success=True,
        message=f"Winner selected: {winner.user.phone}",
        winner_entry_id=winner.id,
        winner_phone=winner.user.phone
    )


@router.delete("/{contest_id}", response_model=ContestDeleteResponse)
async def delete_contest(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete contest and related data"""
    contest_service = ContestService(db)
    success = contest_service.delete_contest(contest_id)
    
    return ContestDeleteResponse(
        success=success,
        message=f"Contest {contest_id} deleted successfully"
    )


@router.get("/{contest_id}/statistics")
async def get_contest_statistics(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive statistics for a contest"""
    contest_service = ContestService(db)
    stats = contest_service.get_contest_statistics(contest_id)
    return stats
