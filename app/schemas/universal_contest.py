"""
Universal Contest Form Schemas

Unified schemas for contest creation and editing that provide consistent
validation and user experience across both operations.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from .official_rules import OfficialRulesCreate, OfficialRulesUpdate
from .sms_template import SMSTemplateDict


class UniversalOfficialRules(BaseModel):
    """Universal official rules form for both creation and editing"""
    
    # Always Required Fields
    eligibility_text: str = Field(..., min_length=10, max_length=2000, description="Contest eligibility requirements")
    sponsor_name: str = Field(..., min_length=2, max_length=200, description="Contest sponsor name")
    prize_value_usd: float = Field(..., ge=0, le=1000000, description="Prize value in USD")
    
    # Date Fields (Auto-populated from contest dates)
    start_date: datetime = Field(..., description="Contest start date (matches contest start_time)")
    end_date: datetime = Field(..., description="Contest end date (matches contest end_time)")
    
    # Optional but Recommended Fields
    terms_url: Optional[str] = Field(None, max_length=500, description="URL to full terms and conditions")
    
    @validator('prize_value_usd')
    def validate_prize_value(cls, v):
        if v <= 0:
            raise ValueError('Prize value must be greater than 0')
        return v
    
    @validator('end_date')
    def validate_date_order(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v <= start_date:
            raise ValueError('End date must be after start date')
        return v


class UniversalContestForm(BaseModel):
    """Universal form schema for contest creation and editing"""
    
    # =====================================================
    # CORE CONTEST FIELDS (Always Required)
    # =====================================================
    
    name: str = Field(..., min_length=3, max_length=200, description="Contest name")
    description: str = Field(..., min_length=10, max_length=2000, description="Contest description")
    start_time: datetime = Field(..., description="Contest start time")
    end_time: datetime = Field(..., description="Contest end time")
    prize_description: str = Field(..., min_length=5, max_length=1000, description="Prize description")
    
    # =====================================================
    # SPONSOR ASSIGNMENT (Role-based)
    # =====================================================
    
    sponsor_profile_id: Optional[int] = Field(None, description="Sponsor profile ID (admin only, auto-assigned for sponsors)")
    
    # =====================================================
    # OFFICIAL RULES (Always Required)
    # =====================================================
    
    official_rules: UniversalOfficialRules = Field(..., description="Official contest rules")
    
    # =====================================================
    # LOCATION TARGETING (Optional but Structured)
    # =====================================================
    
    location: Optional[str] = Field(None, max_length=500, description="Contest location display text")
    location_type: str = Field("united_states", description="Location targeting type")
    selected_states: Optional[List[str]] = Field(None, max_items=50, description="State codes for specific_states targeting")
    radius_address: Optional[str] = Field(None, max_length=500, description="Address for radius targeting")
    radius_miles: Optional[int] = Field(None, ge=1, le=500, description="Radius in miles for targeting")
    radius_latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude for radius center")
    radius_longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude for radius center")
    
    # =====================================================
    # CONTEST CONFIGURATION (With Sensible Defaults)
    # =====================================================
    
    contest_type: str = Field("general", description="Contest type (general, sweepstakes, instant_win)")
    entry_method: str = Field("sms", description="Entry method (sms, email, web_form)")
    winner_selection_method: str = Field("random", description="Winner selection method (random, scheduled, instant)")
    minimum_age: int = Field(18, ge=13, le=120, description="Minimum age requirement")
    max_entries_per_person: Optional[int] = Field(None, ge=1, le=1000, description="Maximum entries per person (null = unlimited)")
    total_entry_limit: Optional[int] = Field(None, ge=1, le=1000000, description="Total entry limit (null = unlimited)")
    
    # =====================================================
    # ADDITIONAL DETAILS (Optional)
    # =====================================================
    
    consolation_offer: Optional[str] = Field(None, max_length=500, description="Consolation prize/offer for non-winners")
    geographic_restrictions: Optional[str] = Field(None, max_length=500, description="Geographic limitations or restrictions")
    contest_tags: Optional[List[str]] = Field(None, max_items=20, description="Tags for contest organization and filtering")
    promotion_channels: Optional[List[str]] = Field(None, max_items=10, description="Promotion channels used for marketing")
    
    # =====================================================
    # VISUAL BRANDING (Optional)
    # =====================================================
    
    image_url: Optional[str] = Field(None, max_length=500, description="CDN URL to contest hero image")
    sponsor_url: Optional[str] = Field(None, max_length=500, description="Sponsor's website URL")
    
    # =====================================================
    # SMS TEMPLATES (Optional - Phase 2)
    # =====================================================
    
    sms_templates: Optional[SMSTemplateDict] = Field(None, description="Custom SMS message templates")
    
    # =====================================================
    # EDIT-SPECIFIC FIELDS (Only for Updates)
    # =====================================================
    
    admin_override: Optional[bool] = Field(False, description="Admin override for active contest modifications")
    override_reason: Optional[str] = Field(None, description="Reason for admin override (required when admin_override=True)")
    
    # =====================================================
    # VALIDATION
    # =====================================================
    
    @validator('contest_type')
    def validate_contest_type(cls, v):
        valid_types = ['general', 'sweepstakes', 'instant_win']
        if v not in valid_types:
            raise ValueError(f'Contest type must be one of: {valid_types}')
        return v
    
    @validator('entry_method')
    def validate_entry_method(cls, v):
        valid_methods = ['sms', 'email', 'web_form']
        if v not in valid_methods:
            raise ValueError(f'Entry method must be one of: {valid_methods}')
        return v
    
    @validator('winner_selection_method')
    def validate_winner_selection_method(cls, v):
        valid_methods = ['random', 'scheduled', 'instant']
        if v not in valid_methods:
            raise ValueError(f'Winner selection method must be one of: {valid_methods}')
        return v
    
    @validator('minimum_age')
    def validate_minimum_age(cls, v):
        if v < 13:  # COPPA compliance
            raise ValueError('Minimum age cannot be less than 13 for legal compliance')
        return v
    
    @validator('end_time')
    def validate_contest_dates(cls, v, values):
        start_time = values.get('start_time')
        if start_time and v <= start_time:
            raise ValueError('Contest end time must be after start time')
        return v
    
    @validator('override_reason')
    def validate_override_reason(cls, v, values):
        admin_override = values.get('admin_override', False)
        if admin_override and not v:
            raise ValueError('Override reason is required when admin_override is True')
        return v
    
    @validator('official_rules')
    def sync_official_rules_dates(cls, v, values):
        """Ensure official rules dates match contest dates"""
        start_time = values.get('start_time')
        end_time = values.get('end_time')
        
        if start_time:
            v.start_date = start_time
        if end_time:
            v.end_date = end_time
            
        return v
    
    @validator('location_type')
    def validate_location_type(cls, v):
        valid_types = ['united_states', 'specific_states', 'radius']
        if v not in valid_types:
            raise ValueError(f'Location type must be one of: {valid_types}')
        return v
    
    @validator('selected_states')
    def validate_selected_states(cls, v, values):
        location_type = values.get('location_type')
        if location_type == 'specific_states' and not v:
            raise ValueError('Selected states are required when location_type is specific_states')
        return v
    
    @validator('radius_miles')
    def validate_radius_config(cls, v, values):
        location_type = values.get('location_type')
        if location_type == 'radius':
            if not v:
                raise ValueError('Radius miles is required when location_type is radius')
            radius_address = values.get('radius_address')
            radius_lat = values.get('radius_latitude')
            radius_lng = values.get('radius_longitude')
            
            if not radius_address and not (radius_lat and radius_lng):
                raise ValueError('Either radius_address or radius coordinates are required for radius targeting')
        return v


class UniversalContestResponse(BaseModel):
    """Universal response for contest operations"""
    
    # Contest Data
    id: int
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    prize_description: str
    status: str
    created_at: datetime
    
    # Sponsor Information
    sponsor_profile_id: Optional[int] = None
    sponsor_name: Optional[str] = None
    
    # Location Data
    location: Optional[str] = None
    location_type: str = "united_states"
    selected_states: Optional[List[str]] = None
    radius_address: Optional[str] = None
    radius_miles: Optional[int] = None
    location_summary: Optional[str] = None  # Computed field for frontend display
    
    # Configuration
    contest_type: str = "general"
    entry_method: str = "sms"
    winner_selection_method: str = "random"
    minimum_age: int = 18
    max_entries_per_person: Optional[int] = None
    total_entry_limit: Optional[int] = None
    
    # Additional Data
    consolation_offer: Optional[str] = None
    geographic_restrictions: Optional[str] = None
    contest_tags: Optional[List[str]] = None
    promotion_channels: Optional[List[str]] = None
    
    # Visual Branding
    image_url: Optional[str] = None
    sponsor_url: Optional[str] = None
    
    # Metadata
    entry_count: int = 0
    winner_entry_id: Optional[int] = None
    winner_phone: Optional[str] = None
    winner_selected_at: Optional[datetime] = None
    
    # Official Rules
    official_rules: Optional[dict] = None
    
    # Status Information
    is_active: bool = False
    can_edit: bool = True
    edit_restrictions: Optional[List[str]] = None
    
    class Config:
        from_attributes = True
