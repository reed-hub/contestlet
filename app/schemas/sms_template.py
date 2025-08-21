from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any


class SMSTemplateBase(BaseModel):
    template_type: str = Field(..., description="Template type (entry_confirmation, winner_notification, non_winner)")
    message_content: str = Field(..., min_length=1, max_length=1600, description="SMS message content (max 1600 chars)")
    variables: Optional[Dict[str, Any]] = Field(None, description="Available template variables")

    @validator('template_type')
    def validate_template_type(cls, v):
        valid_types = [
            'entry_confirmation',
            'winner_notification', 
            'non_winner',
            'reminder',
            'follow_up'
        ]
        if v not in valid_types:
            raise ValueError(f'Template type must be one of: {valid_types}')
        return v

    @validator('message_content')
    def validate_message_content(cls, v):
        if not v.strip():
            raise ValueError('Message content cannot be empty')
        # Check for basic template variables
        if len(v) > 1600:  # SMS limit consideration
            raise ValueError('Message content too long for SMS (max 1600 characters)')
        return v.strip()


class SMSTemplateCreate(SMSTemplateBase):
    contest_id: int = Field(..., description="Contest ID this template belongs to")


class SMSTemplateUpdate(BaseModel):
    message_content: Optional[str] = Field(None, min_length=1, max_length=1600, description="SMS message content")
    variables: Optional[Dict[str, Any]] = Field(None, description="Available template variables")


class SMSTemplateResponse(SMSTemplateBase):
    id: int
    contest_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Schema for form integration - matches the frontend form structure
class SMSTemplateDict(BaseModel):
    """Schema for SMS templates as used in contest creation form"""
    entry_confirmation: Optional[str] = Field(
        None, 
        description="Entry confirmation SMS template",
        example="🎉 You're entered! Contest details: {contest_name}. Good luck!"
    )
    winner_notification: Optional[str] = Field(
        None,
        description="Winner notification SMS template", 
        example="🏆 Congratulations! You won: {prize_description}. Instructions: {claim_instructions}"
    )
    non_winner: Optional[str] = Field(
        None,
        description="Non-winner SMS template (optional)",
        example="Thanks for participating in {contest_name}! {consolation_offer}"
    )
    
    @validator('entry_confirmation', 'winner_notification', 'non_winner')
    def validate_template_length(cls, v):
        if v and len(v) > 1600:
            raise ValueError('SMS template too long (max 1600 characters)')
        return v


# Available template variables for reference
TEMPLATE_VARIABLES = {
    'entry_confirmation': [
        '{contest_name}',
        '{contest_description}',
        '{end_time}',
        '{prize_description}',
        '{sponsor_name}'
    ],
    'winner_notification': [
        '{contest_name}',
        '{prize_description}',
        '{winner_name}',
        '{claim_instructions}',
        '{sponsor_name}',
        '{terms_url}'
    ],
    'non_winner': [
        '{contest_name}',
        '{consolation_offer}',
        '{sponsor_name}',
        '{next_contest_info}'
    ]
}
