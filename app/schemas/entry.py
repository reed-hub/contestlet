from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .contest import ContestResponse


class EntryBase(BaseModel):
    contest_id: int = Field(..., description="Contest ID")


class EntryCreate(EntryBase):
    pass


class EntryResponse(BaseModel):
    id: int
    user_id: int
    contest_id: int
    created_at: datetime
    selected: bool
    contest: Optional[ContestResponse] = None
    
    class Config:
        from_attributes = True


class EntryInDB(EntryResponse):
    pass
