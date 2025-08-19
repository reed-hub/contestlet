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
