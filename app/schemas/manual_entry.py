"""
Manual Entry Schemas for Admin Contest Entry Creation
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
import re


class ManualEntryRequest(BaseModel):
    """Schema for admin manual entry creation"""
    
    phone_number: str = Field(..., description="Phone number in E.164 format (+1234567890)")
    admin_override: bool = Field(..., description="Must be true for manual entry")
    source: Optional[str] = Field("manual_admin", description="Entry source tracking")
    notes: Optional[str] = Field(None, max_length=500, description="Admin notes about the entry")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format (E.164)"""
        if not v:
            raise ValueError('Phone number is required')
        
        # Remove any spaces, dashes, or parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        
        # Check E.164 format: +1234567890 (1-15 digits after +)
        if not re.match(r'^\+[1-9]\d{1,14}$', cleaned):
            raise ValueError('Phone number must be in E.164 format (e.g., +1234567890)')
        
        return cleaned
    
    @validator('admin_override')
    def validate_admin_override(cls, v):
        """Ensure admin_override is True for manual entries"""
        if not v:
            raise ValueError('admin_override must be true for manual entry creation')
        return v
    
    @validator('source')
    def validate_source(cls, v):
        """Validate entry source"""
        allowed_sources = [
            'manual_admin', 'phone_call', 'event', 'paper_form', 
            'customer_service', 'migration', 'promotional'
        ]
        if v and v not in allowed_sources:
            raise ValueError(f'Source must be one of: {", ".join(allowed_sources)}')
        return v or 'manual_admin'


class ManualEntryResponse(BaseModel):
    """Response schema for successful manual entry creation"""
    
    entry_id: int = Field(..., description="Created entry ID")
    contest_id: int = Field(..., description="Contest ID")
    phone_number: str = Field(..., description="Entry phone number")
    created_at: datetime = Field(..., description="Entry creation timestamp")
    created_by_admin_id: int = Field(..., description="Admin who created the entry")
    source: str = Field(..., description="Entry source")
    status: str = Field(default="active", description="Entry status")
    notes: Optional[str] = Field(None, description="Admin notes")
    
    class Config:
        from_attributes = True


class ManualEntryErrorResponse(BaseModel):
    """Error response schema for manual entry failures"""
    
    success: bool = Field(False, description="Always false for errors")
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Specific error code")
    details: Optional[dict] = Field(None, description="Additional error details")


class ManualEntryStats(BaseModel):
    """Statistics for manual entries"""
    
    total_manual_entries: int = Field(..., description="Total manual entries created")
    entries_by_source: dict = Field(..., description="Breakdown by source type")
    entries_by_admin: dict = Field(..., description="Breakdown by admin creator")
    recent_entries: int = Field(..., description="Manual entries in last 24 hours")
