from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database.database import get_db
from app.models.user import User
from app.models.entry import Entry
from app.schemas.entry import EntryResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/entries", tags=["entries"])


@router.get("/me", response_model=List[EntryResponse])
async def get_my_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all contest entries for the current user"""
    entries = db.query(Entry).options(
        joinedload(Entry.contest)
    ).filter(Entry.user_id == current_user.id).all()
    
    return entries
