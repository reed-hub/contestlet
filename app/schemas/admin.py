from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from .contest import ContestBase
from .official_rules import OfficialRulesCreate, OfficialRulesUpdate, OfficialRulesResponse


class AdminContestCreate(ContestBase):
    """Schema for admin contest creation with required official rules"""
    official_rules: OfficialRulesCreate = Field(..., description="Official contest rules (required)")


class AdminContestUpdate(BaseModel):
    """Schema for admin contest updates"""
    name: Optional[str] = Field(None, description="Contest name")
    description: Optional[str] = Field(None, description="Contest description")
    location: Optional[str] = Field(None, description="Contest location")
    latitude: Optional[float] = Field(None, description="Latitude for geolocation")
    longitude: Optional[float] = Field(None, description="Longitude for geolocation")
    start_time: Optional[datetime] = Field(None, description="Contest start time")
    end_time: Optional[datetime] = Field(None, description="Contest end time")
    prize_description: Optional[str] = Field(None, description="Prize description")
    active: Optional[bool] = Field(None, description="Whether the contest is active")
    official_rules: Optional[OfficialRulesUpdate] = Field(None, description="Official rules updates")

    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v


class AdminContestResponse(BaseModel):
    """Enhanced contest response for admin operations"""
    id: int
    name: str
    description: Optional[str]
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    start_time: datetime
    end_time: datetime
    prize_description: Optional[str]
    active: bool
    created_at: datetime
    entry_count: int = Field(..., description="Number of entries for this contest")
    official_rules: Optional[OfficialRulesResponse] = Field(None, description="Official contest rules")
    
    class Config:
        from_attributes = True


class WinnerSelectionResponse(BaseModel):
    """Response for winner selection"""
    success: bool
    message: str
    winner_entry_id: Optional[int] = None
    winner_user_phone: Optional[str] = None
    total_entries: int


class AdminAuthResponse(BaseModel):
    """Response for admin authentication"""
    message: str
    admin: bool = True
