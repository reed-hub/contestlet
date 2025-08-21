from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional
from sqlalchemy.orm import Session

from app.models.contest import Contest
from app.schemas.campaign_import import (
    CampaignOneSheet, 
    CampaignImportRequest, 
    CampaignImportSummary
)
from app.core.datetime_utils import utc_now


class CampaignImportService:
    """Service for importing campaign one-sheets into contest records"""
    
    def __init__(self):
        self.field_mappings = {
            # Direct field mappings
            'name': 'name',
            'description': 'description',
        }
        
        # Fields that require transformation
        self.transform_mappings = {
            'reward_logic.winner_reward': 'prize_description',
        }
        
        # Fields stored in metadata
        self.metadata_fields = [
            'day', 'entry_type', 'messaging', 'category', 
            'target_audience', 'budget', 'expected_entries',
            'reward_logic', 'duration_days'
        ]
    
    def import_campaign(
        self, 
        db: Session, 
        import_request: CampaignImportRequest,
        admin_user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Contest], List[str], Dict[str, Any]]:
        """
        Import a campaign one-sheet into a contest record.
        
        Returns:
            Tuple of (success, contest, warnings, import_summary)
        """
        try:
            campaign = import_request.campaign_json
            warnings = []
            
            # Build contest data
            contest_data = self._map_campaign_to_contest(campaign, import_request, warnings)
            
            # Calculate end time
            start_time = import_request.start_time or utc_now()
            end_time = start_time + timedelta(days=campaign.duration_days)
            
            # Build campaign metadata
            metadata = self._build_campaign_metadata(campaign, import_request)
            
            # Create contest
            contest = Contest(
                name=contest_data['name'],
                description=contest_data['description'],
                location=import_request.location or "TBD",
                latitude=import_request.latitude,
                longitude=import_request.longitude,
                start_time=start_time,
                end_time=end_time,
                prize_description=contest_data.get('prize_description', ''),
# Note: Active status is now computed automatically based on start/end times
                admin_user_id=admin_user_id or import_request.admin_user_id,
                campaign_metadata=metadata,
                created_at=utc_now()
            )
            
            db.add(contest)
            db.commit()
            db.refresh(contest)
            
            # Build import summary
            summary = self._build_import_summary(
                campaign, contest_data, metadata, start_time, end_time
            )
            
            return True, contest, warnings, summary
            
        except Exception as e:
            db.rollback()
            return False, None, [f"Import failed: {str(e)}"], {}
    
    def _map_campaign_to_contest(
        self, 
        campaign: CampaignOneSheet, 
        import_request: CampaignImportRequest,
        warnings: List[str]
    ) -> Dict[str, Any]:
        """Map campaign fields to contest model fields"""
        
        contest_data = {}
        
        # Direct mappings
        for campaign_field, contest_field in self.field_mappings.items():
            value = getattr(campaign, campaign_field, None)
            if value is not None:
                contest_data[contest_field] = value
        
        # Transform mappings
        # Extract prize description from reward_logic.winner_reward
        if campaign.reward_logic and campaign.reward_logic.winner_reward:
            contest_data['prize_description'] = campaign.reward_logic.winner_reward
        
        return contest_data
    
    def _build_campaign_metadata(
        self, 
        campaign: CampaignOneSheet, 
        import_request: CampaignImportRequest
    ) -> Dict[str, Any]:
        """Build metadata object containing original campaign data and import info"""
        
        metadata = {
            'import_info': {
                'import_timestamp': utc_now().isoformat(),
                'import_source': 'one_sheet_import',
                'import_version': '1.0'
            },
            'original_campaign': campaign.model_dump(),
            'import_overrides': {
                'location': import_request.location,
                'start_time': import_request.start_time.isoformat() if import_request.start_time else None,
                'admin_user_id': import_request.admin_user_id,
                'active': import_request.active,
                'latitude': import_request.latitude,
                'longitude': import_request.longitude
            }
        }
        
        return metadata
    
    def _build_import_summary(
        self,
        campaign: CampaignOneSheet,
        contest_data: Dict[str, Any],
        metadata: Dict[str, Any],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Build detailed import summary"""
        
        calculated_fields = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_days': campaign.duration_days
        }
        
        return {
            'original_campaign': campaign.model_dump(),
            'mapped_contest_fields': contest_data,
            'metadata_fields': metadata,
            'calculated_fields': calculated_fields,
            'field_mappings_used': self.field_mappings,
            'transform_mappings_used': self.transform_mappings
        }
    
    def validate_campaign_data(self, campaign: CampaignOneSheet) -> Tuple[bool, List[str]]:
        """Validate campaign data before import"""
        
        errors = []
        
        # Required field validation
        if not campaign.name or len(campaign.name.strip()) == 0:
            errors.append("Campaign name is required")
        
        if not campaign.description or len(campaign.description.strip()) == 0:
            errors.append("Campaign description is required")
        
        if not campaign.reward_logic or not campaign.reward_logic.winner_reward:
            errors.append("Reward logic with winner_reward is required")
        
        if campaign.duration_days <= 0:
            errors.append("Duration must be at least 1 day")
        
        # Business logic validation
        if campaign.name and len(campaign.name) > 200:
            errors.append("Campaign name too long (max 200 characters)")
        
        if campaign.description and len(campaign.description) > 2000:
            errors.append("Campaign description too long (max 2000 characters)")
        
        return len(errors) == 0, errors


# Create service instance
campaign_import_service = CampaignImportService()
