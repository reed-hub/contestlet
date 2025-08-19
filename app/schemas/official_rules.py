from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


class OfficialRulesBase(BaseModel):
    eligibility_text: str = Field(..., description="Contest eligibility requirements")
    sponsor_name: str = Field(..., description="Name of the contest sponsor")
    start_date: datetime = Field(..., description="Official contest start date")
    end_date: datetime = Field(..., description="Official contest end date")
    prize_value_usd: float = Field(..., ge=0, description="Prize value in USD")
    terms_url: Optional[str] = Field(None, description="URL to full terms and conditions")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('prize_value_usd')
    def validate_prize_value(cls, v):
        if v < 0:
            raise ValueError('Prize value must be non-negative')
        return v


class OfficialRulesCreate(OfficialRulesBase):
    pass


class OfficialRulesUpdate(BaseModel):
    eligibility_text: Optional[str] = Field(None, description="Contest eligibility requirements")
    sponsor_name: Optional[str] = Field(None, description="Name of the contest sponsor")
    start_date: Optional[datetime] = Field(None, description="Official contest start date")
    end_date: Optional[datetime] = Field(None, description="Official contest end date")
    prize_value_usd: Optional[float] = Field(None, ge=0, description="Prize value in USD")
    terms_url: Optional[str] = Field(None, description="URL to full terms and conditions")


class OfficialRulesResponse(OfficialRulesBase):
    id: int
    contest_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
