from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
from typing import List
import random
from app.database.database import get_db
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.user import User
from app.models.official_rules import OfficialRules
from app.schemas.admin import (
    AdminContestCreate, AdminContestUpdate, AdminContestResponse, 
    WinnerSelectionResponse, AdminAuthResponse
)
from app.core.admin_auth import get_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])


def validate_contest_compliance(contest_data: dict, official_rules_data: dict) -> None:
    """
    Validate that contest meets legal compliance requirements before activation.
    """
    required_fields = {
        'contest': ['name', 'start_time', 'end_time', 'prize_description'],
        'rules': ['eligibility_text', 'sponsor_name', 'start_date', 'end_date', 'prize_value_usd']
    }
    
    # Check required contest fields
    for field in required_fields['contest']:
        if not contest_data.get(field):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contest field '{field}' is required for legal compliance"
            )
    
    # Check required official rules fields
    for field in required_fields['rules']:
        if not official_rules_data.get(field):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Official rules field '{field}' is required for legal compliance"
            )
    
    # Validate prize value is reasonable
    if official_rules_data.get('prize_value_usd', 0) <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prize value must be greater than $0 for legal compliance"
        )


@router.get("/auth", response_model=AdminAuthResponse)
async def admin_auth_check(admin_user: dict = Depends(get_admin_user)):
    """Check admin authentication status"""
    return AdminAuthResponse(message="Admin authentication successful")


@router.post("/contests", response_model=AdminContestResponse)
async def create_contest(
    contest_data: AdminContestCreate,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new contest with official rules.
    Validates legal compliance before allowing activation.
    """
    # Convert Pydantic models to dict for validation
    contest_dict = contest_data.dict(exclude={'official_rules'})
    rules_dict = contest_data.official_rules.dict()
    
    # Validate legal compliance
    validate_contest_compliance(contest_dict, rules_dict)
    
    # Create contest
    contest = Contest(**contest_dict)
    db.add(contest)
    db.flush()  # Get the contest ID
    
    # Create official rules
    official_rules = OfficialRules(
        contest_id=contest.id,
        **rules_dict
    )
    db.add(official_rules)
    db.commit()
    
    # Refresh to get relationships
    db.refresh(contest)
    db.refresh(official_rules)
    
    # Get entry count (will be 0 for new contest)
    entry_count = db.query(Entry).filter(Entry.contest_id == contest.id).count()
    
    # Prepare response
    response_data = {
        **contest.__dict__,
        "entry_count": entry_count,
        "official_rules": official_rules
    }
    
    return AdminContestResponse(**response_data)


@router.put("/contests/{contest_id}", response_model=AdminContestResponse)
async def update_contest(
    contest_id: int,
    contest_update: AdminContestUpdate,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing contest and its official rules.
    """
    # Get existing contest
    contest = db.query(Contest).options(joinedload(Contest.official_rules)).filter(
        Contest.id == contest_id
    ).first()
    
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Update contest fields
    update_data = contest_update.dict(exclude={'official_rules'}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(contest, field, value)
    
    # Update official rules if provided
    if contest_update.official_rules:
        if contest.official_rules:
            # Update existing rules
            rules_update = contest_update.official_rules.dict(exclude_unset=True)
            for field, value in rules_update.items():
                setattr(contest.official_rules, field, value)
            contest.official_rules.updated_at = datetime.utcnow()
        else:
            # Create new rules if none exist
            rules_data = contest_update.official_rules.dict(exclude_unset=True)
            official_rules = OfficialRules(contest_id=contest.id, **rules_data)
            db.add(official_rules)
    
    # If activating contest, validate compliance
    if contest_update.active and contest.active != contest_update.active:
        contest_dict = {
            "name": contest.name,
            "start_time": contest.start_time,
            "end_time": contest.end_time,
            "prize_description": contest.prize_description
        }
        rules_dict = {}
        if contest.official_rules:
            rules_dict = {
                "eligibility_text": contest.official_rules.eligibility_text,
                "sponsor_name": contest.official_rules.sponsor_name,
                "start_date": contest.official_rules.start_date,
                "end_date": contest.official_rules.end_date,
                "prize_value_usd": contest.official_rules.prize_value_usd
            }
        validate_contest_compliance(contest_dict, rules_dict)
    
    db.commit()
    db.refresh(contest)
    
    # Get entry count
    entry_count = db.query(Entry).filter(Entry.contest_id == contest.id).count()
    
    # Prepare response
    response_data = {
        **contest.__dict__,
        "entry_count": entry_count,
        "official_rules": contest.official_rules
    }
    
    return AdminContestResponse(**response_data)


@router.get("/contests", response_model=List[AdminContestResponse])
async def list_contests(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all contests with admin details including entry counts.
    """
    contests = db.query(Contest).options(joinedload(Contest.official_rules)).all()
    
    response_list = []
    for contest in contests:
        entry_count = db.query(Entry).filter(Entry.contest_id == contest.id).count()
        response_data = {
            **contest.__dict__,
            "entry_count": entry_count,
            "official_rules": contest.official_rules
        }
        response_list.append(AdminContestResponse(**response_data))
    
    return response_list


@router.post("/contests/{contest_id}/select-winner", response_model=WinnerSelectionResponse)
async def select_winner(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Randomly select a winner from contest entries and mark as selected.
    """
    # Get contest
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Check if contest has ended
    if contest.end_time > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot select winner for an active contest. Contest must end first."
        )
    
    # Get all entries for this contest
    entries = db.query(Entry).options(joinedload(Entry.user)).filter(
        Entry.contest_id == contest_id
    ).all()
    
    if not entries:
        return WinnerSelectionResponse(
            success=False,
            message="No entries found for this contest",
            total_entries=0
        )
    
    # Check if winner already selected
    existing_winner = db.query(Entry).filter(
        Entry.contest_id == contest_id,
        Entry.selected == True
    ).first()
    
    if existing_winner:
        return WinnerSelectionResponse(
            success=False,
            message="Winner already selected for this contest",
            winner_entry_id=existing_winner.id,
            winner_user_phone=existing_winner.user.phone,
            total_entries=len(entries)
        )
    
    # Randomly select winner
    winner_entry = random.choice(entries)
    winner_entry.selected = True
    db.commit()
    
    return WinnerSelectionResponse(
        success=True,
        message=f"Winner selected successfully from {len(entries)} entries",
        winner_entry_id=winner_entry.id,
        winner_user_phone=winner_entry.user.phone,
        total_entries=len(entries)
    )
