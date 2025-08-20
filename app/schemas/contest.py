from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


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
    status: Optional[str] = Field(None, description="Contest status: active, inactive, ended, upcoming")
    
    def __init__(self, **data):
        # Compute status before creating the object
        if 'status' not in data:
            now = datetime.utcnow()
            active = data.get('active', True)
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            
            if not active:
                # If manually set to inactive, check if it has ended
                if end_time and end_time <= now:
                    data['status'] = "ended"
                else:
                    data['status'] = "inactive"
            else:
                # If active, check if it's actually started/ended
                if start_time and start_time > now:
                    data['status'] = "upcoming"
                elif end_time and end_time <= now:
                    data['status'] = "ended"
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
