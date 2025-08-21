from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Union
from datetime import datetime


class RewardLogic(BaseModel):
    """Schema for reward logic in campaign one-sheets"""
    type: str = Field(..., description="Type of reward logic (e.g., 'random_winner', 'daily_winner')")
    winner_reward: str = Field(..., description="Description of what the winner receives")
    additional_params: Optional[Dict[str, Any]] = Field(default=None, description="Additional reward parameters")


class CampaignMessaging(BaseModel):
    """Schema for messaging templates in campaign one-sheets"""
    initial_sms: Optional[str] = Field(None, description="SMS sent when user enters contest")
    winner_sms: Optional[str] = Field(None, description="SMS sent to winner")
    reminder_sms: Optional[str] = Field(None, description="SMS sent as reminder")
    follow_up_sms: Optional[str] = Field(None, description="Follow-up SMS after contest")


class CampaignOneSheet(BaseModel):
    """Schema for campaign one-sheet JSON structure"""
    name: str = Field(..., description="Campaign name")
    description: str = Field(..., description="Campaign description")
    day: Optional[str] = Field(None, description="Day of week for recurring campaigns")
    duration_days: int = Field(1, ge=1, description="Duration of contest in days")
    entry_type: Optional[str] = Field(None, description="Type of entry mechanism")
    reward_logic: RewardLogic = Field(..., description="Reward logic configuration")
    messaging: Optional[CampaignMessaging] = Field(None, description="Messaging templates")
    
    # Additional campaign metadata
    category: Optional[str] = Field(None, description="Campaign category")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    budget: Optional[float] = Field(None, description="Campaign budget")
    expected_entries: Optional[int] = Field(None, description="Expected number of entries")


class CampaignImportRequest(BaseModel):
    """Schema for campaign import API request"""
    campaign_json: CampaignOneSheet = Field(..., description="Campaign one-sheet data")
    location: Optional[str] = Field(None, description="Contest location override")
    start_time: Optional[datetime] = Field(None, description="Contest start time override")
    admin_user_id: Optional[str] = Field(None, description="Admin user ID override")
    active: Optional[bool] = Field(False, description="Whether contest should be active immediately")
    
    # Geolocation overrides
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude override")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude override")


class CampaignImportResponse(BaseModel):
    """Schema for campaign import API response"""
    success: bool = Field(..., description="Whether import was successful")
    contest_id: Optional[int] = Field(None, description="ID of created contest")
    message: str = Field(..., description="Success or error message")
    warnings: Optional[list[str]] = Field(None, description="Any warnings during import")
    
    # Import metadata
    fields_mapped: Optional[Dict[str, str]] = Field(None, description="Fields that were mapped")
    fields_stored_in_metadata: Optional[list[str]] = Field(None, description="Fields stored in campaign_metadata")


class CampaignImportSummary(BaseModel):
    """Schema for detailed import summary"""
    original_campaign: CampaignOneSheet = Field(..., description="Original campaign data")
    mapped_contest_fields: Dict[str, Any] = Field(..., description="Fields mapped to contest model")
    metadata_fields: Dict[str, Any] = Field(..., description="Fields stored in campaign_metadata")
    calculated_fields: Dict[str, Any] = Field(..., description="Fields calculated during import")
    import_timestamp: datetime = Field(..., description="When import was performed")
    import_source: str = Field(default="one_sheet_import", description="Source of import")
