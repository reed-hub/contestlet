"""
Contest Winners API Router

Handles all multiple winner management operations including:
- Winner selection (single and multiple)
- Winner management (list, update, remove, reselect)
- Winner notifications
- Prize tier management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.admin_auth import get_admin_user
from app.core.services.winner_service import WinnerService
from app.core.services.notification_service import NotificationService
from app.models.contest import Contest
from app.models.contest_winner import ContestWinner
from app.schemas.contest_winner import (
    MultipleWinnerSelectionRequest,
    MultipleWinnerSelectionResponse,
    ContestWinnerResponse,
    ContestWinnersListResponse,
    WinnerManagementRequest,
    WinnerNotificationRequest,
    WinnerNotificationResponse
)
from app.schemas.admin import WinnerSelectionResponse  # Legacy single winner response
from app.shared.exceptions.base import BusinessException, ResourceNotFoundException


router = APIRouter(prefix="/admin/contests", tags=["contest-winners"])


@router.post("/{contest_id}/select-winners", response_model=MultipleWinnerSelectionResponse)
async def select_multiple_winners(
    contest_id: int,
    request: MultipleWinnerSelectionRequest,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Select multiple winners for a contest.
    
    Supports 1-50 winners with optional prize tier configuration.
    Replaces the legacy single winner selection endpoint.
    """
    try:
        winner_service = WinnerService(db)
        
        # Extract prize tiers if provided
        prize_tiers = None
        if request.prize_tiers:
            prize_tiers = [tier.dict() for tier in request.prize_tiers]
        
        result = winner_service.select_winners(
            contest_id=contest_id,
            winner_count=request.winner_count,
            selection_method=request.selection_method,
            prize_tiers=prize_tiers,
            admin_user_id=admin_user.get("sub")
        )
        
        # Convert winners to response format
        winner_responses = []
        for winner in result.winners:
            winner_responses.append(ContestWinnerResponse(
                id=winner.id,
                contest_id=winner.contest_id,
                entry_id=winner.entry_id,
                winner_position=winner.winner_position,
                prize_description=winner.prize_description,
                selected_at=winner.selected_at,
                notified_at=winner.notified_at,
                claimed_at=winner.claimed_at,
                phone=winner.entry.user.phone if winner.entry and winner.entry.user else "Unknown",
                is_notified=winner.is_notified,
                is_claimed=winner.is_claimed
            ))
        
        return MultipleWinnerSelectionResponse(
            success=result.success,
            message=result.message,
            winners=winner_responses,
            total_winners=result.total_winners,
            total_entries=result.total_entries,
            selection_method=result.selection_method
        )
        
    except (BusinessException, ResourceNotFoundException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to select winners: {str(e)}"
        )


@router.post("/{contest_id}/select-winner", response_model=WinnerSelectionResponse)
async def select_single_winner(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Legacy single winner selection endpoint.
    
    Maintained for backward compatibility. Uses the new multiple winner system
    with winner_count=1.
    """
    try:
        winner_service = WinnerService(db)
        
        result = winner_service.select_winners(
            contest_id=contest_id,
            winner_count=1,
            selection_method="random",
            admin_user_id=admin_user.get("sub")
        )
        
        if not result.success or not result.winners:
            return WinnerSelectionResponse(
                success=False,
                message=result.message,
                total_entries=result.total_entries
            )
        
        winner = result.winners[0]
        return WinnerSelectionResponse(
            success=True,
            message=f"Winner selected: {winner.entry.user.phone if winner.entry and winner.entry.user else 'Unknown'}",
            winner_entry_id=winner.entry_id,
            winner_phone=winner.entry.user.phone if winner.entry and winner.entry.user else "Unknown",
            total_entries=result.total_entries
        )
        
    except (BusinessException, ResourceNotFoundException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to select winner: {str(e)}"
        )


@router.get("/{contest_id}/winners", response_model=ContestWinnersListResponse)
async def get_contest_winners(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all winners for a contest with their positions and prize information.
    """
    try:
        # Get contest
        contest = db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contest {contest_id} not found"
            )
        
        winner_service = WinnerService(db)
        winners = winner_service.get_contest_winners(contest_id)
        
        # Convert to response format
        winner_responses = []
        for winner in winners:
            winner_responses.append(ContestWinnerResponse(
                id=winner.id,
                contest_id=winner.contest_id,
                entry_id=winner.entry_id,
                winner_position=winner.winner_position,
                prize_description=winner.prize_description,
                selected_at=winner.selected_at,
                notified_at=winner.notified_at,
                claimed_at=winner.claimed_at,
                phone=winner.entry.user.phone if winner.entry and winner.entry.user else "Unknown",
                is_notified=winner.is_notified,
                is_claimed=winner.is_claimed
            ))
        
        return ContestWinnersListResponse(
            contest_id=contest_id,
            contest_name=contest.name,
            winner_count=contest.winner_count or 1,
            selected_winners=len(winners),
            winners=winner_responses,
            prize_tiers=contest.prize_tiers
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get winners: {str(e)}"
        )


@router.post("/{contest_id}/winners/{position}/manage")
async def manage_winner(
    contest_id: int,
    position: int,
    request: WinnerManagementRequest,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Manage individual winners (reselect, notify, mark claimed, remove).
    """
    try:
        winner_service = WinnerService(db)
        
        if request.action == "reselect":
            winner = winner_service.reselect_winner(
                contest_id=contest_id,
                position=position,
                admin_user_id=admin_user.get("sub")
            )
            return {
                "success": True,
                "message": f"Winner at position {position} reselected",
                "winner": ContestWinnerResponse.from_orm(winner)
            }
            
        elif request.action == "notify":
            winner = winner_service.get_winner_by_position(contest_id, position)
            if not winner:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Winner at position {position} not found"
                )
            
            # Send notification
            notification_service = NotificationService(db)
            await notification_service.send_winner_notification(
                entry=winner.entry,
                contest=winner.contest,
                user=winner.entry.user,
                custom_message=request.custom_message
            )
            
            # Mark as notified
            winner_service.mark_winner_notified(contest_id, position)
            
            return {
                "success": True,
                "message": f"Winner at position {position} notified",
                "phone": winner.entry.user.phone if winner.entry and winner.entry.user else "Unknown"
            }
            
        elif request.action == "mark_claimed":
            winner = winner_service.mark_winner_claimed(contest_id, position)
            return {
                "success": True,
                "message": f"Winner at position {position} marked as claimed",
                "winner": ContestWinnerResponse.from_orm(winner)
            }
            
        elif request.action == "remove":
            winner_service.remove_winner(contest_id, position)
            return {
                "success": True,
                "message": f"Winner at position {position} removed"
            }
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {request.action}"
            )
            
    except (BusinessException, ResourceNotFoundException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to manage winner: {str(e)}"
        )


@router.post("/{contest_id}/winners/notify", response_model=WinnerNotificationResponse)
async def notify_winners(
    contest_id: int,
    request: WinnerNotificationRequest,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Send notifications to contest winners.
    
    Can notify specific winner positions or all winners.
    """
    try:
        winner_service = WinnerService(db)
        notification_service = NotificationService(db)
        
        # Get winners to notify
        if request.winner_positions:
            winners_to_notify = []
            for position in request.winner_positions:
                winner = winner_service.get_winner_by_position(contest_id, position)
                if winner:
                    winners_to_notify.append(winner)
        else:
            winners_to_notify = winner_service.get_contest_winners(contest_id)
        
        if not winners_to_notify:
            return WinnerNotificationResponse(
                success=False,
                message="No winners found to notify",
                notifications_sent=0,
                failed_notifications=0
            )
        
        # Send notifications
        notifications_sent = 0
        failed_notifications = 0
        details = []
        
        for winner in winners_to_notify:
            try:
                if not request.test_mode:
                    await notification_service.send_winner_notification(
                        entry=winner.entry,
                        contest=winner.contest,
                        user=winner.entry.user,
                        custom_message=request.custom_message
                    )
                    
                    # Mark as notified
                    winner_service.mark_winner_notified(contest_id, winner.winner_position)
                
                notifications_sent += 1
                details.append({
                    "position": winner.winner_position,
                    "phone": winner.entry.user.phone if winner.entry and winner.entry.user else "Unknown",
                    "status": "sent" if not request.test_mode else "test_mode",
                    "prize": winner.prize_description
                })
                
            except Exception as e:
                failed_notifications += 1
                details.append({
                    "position": winner.winner_position,
                    "phone": winner.entry.user.phone if winner.entry and winner.entry.user else "Unknown",
                    "status": "failed",
                    "error": str(e)
                })
        
        return WinnerNotificationResponse(
            success=failed_notifications == 0,
            message=f"Sent {notifications_sent} notifications, {failed_notifications} failed",
            notifications_sent=notifications_sent,
            failed_notifications=failed_notifications,
            details=details
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to notify winners: {str(e)}"
        )


@router.get("/{contest_id}/winners/stats")
async def get_winner_stats(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get winner statistics for a contest.
    """
    try:
        contest = db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contest {contest_id} not found"
            )
        
        winner_service = WinnerService(db)
        winners = winner_service.get_contest_winners(contest_id)
        
        # Calculate statistics
        total_winners = len(winners)
        notified_winners = sum(1 for w in winners if w.is_notified)
        claimed_winners = sum(1 for w in winners if w.is_claimed)
        
        return {
            "contest_id": contest_id,
            "contest_name": contest.name,
            "winner_count": contest.winner_count or 1,
            "selected_winners": total_winners,
            "notified_winners": notified_winners,
            "claimed_winners": claimed_winners,
            "notification_rate": notified_winners / total_winners if total_winners > 0 else 0,
            "claim_rate": claimed_winners / total_winners if total_winners > 0 else 0,
            "has_prize_tiers": contest.prize_tiers is not None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get winner stats: {str(e)}"
        )
