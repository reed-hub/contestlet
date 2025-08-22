from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


class ContestBase(BaseModel):
    name: str = Field(..., description="Contest name")
    description: Optional[str] = Field(None, description="Contest description")
    location: Optional[str] = Field(None, description="Contest location (city, state, zip)")
    latitude: Optional[float] = Field(None, description="Latitude for geolocation")
    longitude: Optional[float] = Field(None, description="Longitude for geolocation")
    start_time: datetime = Field(..., description="Contest start time")
    end_time: datetime = Field(..., description="Contest end time")
    prize_description: Optional[str] = Field(None, description="Prize description")
    active: bool = Field(True, description="Whether the contest is active")
    
    # Contest configuration (Phase 1 form support) - Optional for base schema
    contest_type: Optional[str] = Field("general", description="Contest type")
    entry_method: Optional[str] = Field("sms", description="Entry method")
    winner_selection_method: Optional[str] = Field("random", description="Winner selection method")
    minimum_age: Optional[int] = Field(18, description="Minimum age requirement")
    max_entries_per_person: Optional[int] = Field(None, description="Maximum entries per person")
    total_entry_limit: Optional[int] = Field(None, description="Total entry limit")
    consolation_offer: Optional[str] = Field(None, description="Consolation prize/offer")
    geographic_restrictions: Optional[str] = Field(None, description="Geographic restrictions")
    contest_tags: Optional[List[str]] = Field(None, description="Contest tags")
    promotion_channels: Optional[List[str]] = Field(None, description="Promotion channels")
    
    # Visual branding and sponsor information
    image_url: Optional[str] = Field(None, description="CDN URL to contest hero image (1:1 aspect ratio)")
    sponsor_url: Optional[str] = Field(None, description="Sponsor's website URL")
    
    # Smart Location System fields
    location_type: Optional[str] = Field("united_states", description="Location targeting type")
    selected_states: Optional[List[str]] = Field(None, description="State codes for specific_states targeting")
    radius_address: Optional[str] = Field(None, description="Address for radius targeting")
    radius_miles: Optional[int] = Field(None, description="Radius in miles for targeting")
    radius_latitude: Optional[float] = Field(None, description="Latitude for radius center")
    radius_longitude: Optional[float] = Field(None, description="Longitude for radius center")

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


class ContestCreate(ContestBase):
    pass


class ContestResponse(ContestBase):
    id: int
    created_at: datetime
    distance_miles: Optional[float] = Field(None, description="Distance from query point in miles")
    status: Optional[str] = Field(None, description="Contest status: upcoming, active, ended, complete")
    
    def __init__(self, **data):
        # Compute status before creating the object based purely on time
        if 'status' not in data:
            from app.core.datetime_utils import utc_now
            now = utc_now()
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            winner_selected_at = data.get('winner_selected_at')
            
            # Make datetime objects timezone-aware for comparison if they aren't already
            if start_time and start_time.tzinfo is None:
                from datetime import timezone
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time and end_time.tzinfo is None:
                from datetime import timezone
                end_time = end_time.replace(tzinfo=timezone.utc)
            
            # Simplified time-based status calculation
            if winner_selected_at:
                data['status'] = "complete"
            elif end_time and end_time <= now:
                data['status'] = "ended"
            elif start_time and start_time > now:
                data['status'] = "upcoming"
            else:
                data['status'] = "active"
        
        super().__init__(**data)
    
    class Config:
        from_attributes = True


class ContestInDB(ContestResponse):
    pass


class ContestListResponse(BaseModel):
    contests: list[ContestResponse]
    total: int
    page: int
    size: int
    
    class Config:
        from_attributes = True
