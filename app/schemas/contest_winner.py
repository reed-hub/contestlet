"""
Pydantic schemas for Contest Winner operations.

Handles validation and serialization for multiple winners feature.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class PrizeTier(BaseModel):
    """Schema for individual prize tier configuration"""
    position: int = Field(..., ge=1, le=50, description="Winner position (1st, 2nd, 3rd, etc.)")
    prize: str = Field(..., min_length=1, max_length=200, description="Prize description")
    description: Optional[str] = Field(None, max_length=500, description="Detailed prize description")


class PrizeTiers(BaseModel):
    """Schema for complete prize tiers configuration"""
    tiers: List[PrizeTier] = Field(..., min_items=1, max_items=50, description="List of prize tiers")
    total_value: Optional[float] = Field(None, ge=0, description="Total prize value in USD")
    currency: str = Field(default="USD", description="Prize currency")
    
    @validator('tiers')
    def validate_tiers(cls, v):
        """Validate that positions are sequential and unique"""
        positions = [tier.position for tier in v]
        
        # Check for duplicates
        if len(positions) != len(set(positions)):
            raise ValueError("Prize tier positions must be unique")
        
        # Check for sequential positions starting from 1
        expected_positions = list(range(1, len(v) + 1))
        if sorted(positions) != expected_positions:
            raise ValueError("Prize tier positions must be sequential starting from 1")
        
        return v


class ContestWinnerBase(BaseModel):
    """Base schema for contest winner"""
    winner_position: int = Field(..., ge=1, le=50, description="Winner position")
    prize_description: Optional[str] = Field(None, max_length=500, description="Prize for this winner")


class ContestWinnerCreate(ContestWinnerBase):
    """Schema for creating a contest winner"""
    contest_id: int = Field(..., description="Contest ID")
    entry_id: int = Field(..., description="Winning entry ID")


class ContestWinnerUpdate(BaseModel):
    """Schema for updating a contest winner"""
    prize_description: Optional[str] = Field(None, max_length=500, description="Updated prize description")
    notified_at: Optional[datetime] = Field(None, description="When winner was notified")
    claimed_at: Optional[datetime] = Field(None, description="When winner claimed prize")


class ContestWinnerResponse(ContestWinnerBase):
    """Schema for contest winner API responses"""
    id: int
    contest_id: int
    entry_id: int
    selected_at: datetime
    notified_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    phone: Optional[str] = Field(None, description="Winner's phone number (masked)")
    is_notified: bool = Field(description="Whether winner has been notified")
    is_claimed: bool = Field(description="Whether winner has claimed their prize")
    
    class Config:
        from_attributes = True


class MultipleWinnerSelectionRequest(BaseModel):
    """Schema for selecting multiple winners"""
    winner_count: int = Field(..., ge=1, le=50, description="Number of winners to select")
    selection_method: str = Field(default="random", description="Winner selection method")
    prize_tiers: Optional[List[PrizeTier]] = Field(None, description="Optional prize tier configuration")
    
    @validator('selection_method')
    def validate_selection_method(cls, v):
        valid_methods = ['random', 'manual']
        if v not in valid_methods:
            raise ValueError(f'Selection method must be one of: {valid_methods}')
        return v
    
    @validator('prize_tiers')
    def validate_prize_tiers_count(cls, v, values):
        """Ensure prize tiers count matches winner count"""
        if v is not None:
            winner_count = values.get('winner_count')
            if winner_count and len(v) != winner_count:
                raise ValueError(f'Number of prize tiers ({len(v)}) must match winner count ({winner_count})')
        return v


class MultipleWinnerSelectionResponse(BaseModel):
    """Schema for multiple winner selection response"""
    success: bool
    message: str
    winners: List[ContestWinnerResponse] = Field(default_factory=list)
    total_winners: int = Field(description="Total number of winners selected")
    total_entries: int = Field(description="Total number of eligible entries")
    selection_method: str = Field(description="Method used for selection")


class WinnerManagementRequest(BaseModel):
    """Schema for winner management operations"""
    action: str = Field(..., description="Action to perform: reselect, notify, mark_claimed")
    winner_position: Optional[int] = Field(None, ge=1, le=50, description="Specific winner position")
    custom_message: Optional[str] = Field(None, max_length=1000, description="Custom notification message")
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['reselect', 'notify', 'mark_claimed', 'remove']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {valid_actions}')
        return v


class ContestWinnersListResponse(BaseModel):
    """Schema for listing all winners of a contest"""
    contest_id: int
    contest_name: str
    winner_count: int
    selected_winners: int = Field(description="Number of winners currently selected")
    winners: List[ContestWinnerResponse] = Field(default_factory=list)
    prize_tiers: Optional[PrizeTiers] = None
    
    class Config:
        from_attributes = True


class WinnerNotificationRequest(BaseModel):
    """Schema for sending winner notifications"""
    winner_positions: Optional[List[int]] = Field(None, description="Specific winner positions to notify (null = all)")
    custom_message: Optional[str] = Field(None, max_length=1000, description="Custom notification message")
    test_mode: bool = Field(default=False, description="Test mode - don't actually send SMS")


class WinnerNotificationResponse(BaseModel):
    """Schema for winner notification response"""
    success: bool
    message: str
    notifications_sent: int
    failed_notifications: int
    details: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed notification results")
