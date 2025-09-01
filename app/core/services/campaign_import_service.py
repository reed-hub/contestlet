"""
Clean campaign import service for bulk contest operations.
Handles CSV imports and bulk contest creation with proper validation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import csv
import io
from sqlalchemy.orm import Session

from app.models.contest import Contest
from app.models.user import User
from app.models.sponsor_profile import SponsorProfile
from app.shared.exceptions.base import (
    BusinessException, 
    ValidationException,
    ErrorCode
)
from app.shared.constants.contest import ContestConstants
from app.core.datetime_utils import utc_now
from dateutil.parser import parse as parse_datetime
from app.core.services.contest_service import ContestService


class CampaignImportService:
    """
    Clean campaign import service with centralized business logic.
    """
    
    def __init__(self, contest_service: ContestService, db: Session):
        self.contest_service = contest_service
        self.db = db
    
    async def import_contests_from_csv(
        self,
        csv_content: str,
        admin_user: User,
        sponsor_profile_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import contests from CSV content.
        
        Args:
            csv_content: CSV file content as string
            admin_user: Admin user performing the import
            sponsor_profile_id: Optional sponsor profile to assign contests to
            
        Returns:
            Dictionary with import results and statistics
        """
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            results = {
                "total_rows": 0,
                "successful_imports": 0,
                "failed_imports": 0,
                "errors": [],
                "imported_contest_ids": []
            }
            
            for row_num, row in enumerate(csv_reader, start=1):
                results["total_rows"] += 1
                
                try:
                    # Validate and create contest from row
                    contest_data = self._parse_csv_row(row, sponsor_profile_id)
                    
                    # Create contest via contest service
                    contest = await self.contest_service.create_contest(
                        contest_data=contest_data,
                        creator_user=admin_user
                    )
                    
                    results["successful_imports"] += 1
                    results["imported_contest_ids"].append(contest.id)
                    
                except Exception as e:
                    results["failed_imports"] += 1
                    results["errors"].append({
                        "row": row_num,
                        "error": str(e),
                        "data": row
                    })
            
            return results
            
        except Exception as e:
            raise BusinessException(
                message=f"Failed to import contests from CSV: {str(e)}",
                error_code=ErrorCode.IMPORT_FAILED,
                details={"error": str(e)}
            )
    
    def _parse_csv_row(self, row: Dict[str, str], sponsor_profile_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Parse a CSV row into contest data.
        
        Args:
            row: CSV row as dictionary
            sponsor_profile_id: Optional sponsor profile ID
            
        Returns:
            Parsed contest data dictionary
        """
        try:
            # Required fields
            contest_data = {
                "name": self._get_required_field(row, "name"),
                "description": self._get_required_field(row, "description"),
                "start_time": self._parse_datetime_field(row, "start_time"),
                "end_time": self._parse_datetime_field(row, "end_time"),
            }
            
            # Optional fields with defaults
            contest_data.update({
                "location": row.get("location", "").strip() or None,
                "prize_description": row.get("prize_description", "").strip() or None,
                "contest_type": row.get("contest_type", ContestConstants.DEFAULT_CONTEST_TYPE),
                "entry_method": row.get("entry_method", ContestConstants.DEFAULT_ENTRY_METHOD),
                "winner_selection_method": row.get("winner_selection_method", ContestConstants.DEFAULT_WINNER_SELECTION_METHOD),
                "minimum_age": self._parse_int_field(row, "minimum_age", ContestConstants.DEFAULT_MINIMUM_AGE),
                "max_entries_per_person": self._parse_int_field(row, "max_entries_per_person", ContestConstants.DEFAULT_ENTRIES_PER_PERSON),
                "location_type": row.get("location_type", ContestConstants.DEFAULT_LOCATION_TYPE),
                "sponsor_profile_id": sponsor_profile_id
            })
            
            # Location-specific fields
            if contest_data["location_type"] == "specific_states":
                states_str = row.get("selected_states", "").strip()
                if states_str:
                    contest_data["selected_states"] = [s.strip().upper() for s in states_str.split(",")]
            
            elif contest_data["location_type"] == "radius":
                contest_data.update({
                    "radius_address": row.get("radius_address", "").strip() or None,
                    "radius_miles": self._parse_float_field(row, "radius_miles", 25.0)
                })
            
            # SMS templates
            contest_data.update({
                "entry_confirmation_sms": row.get("entry_confirmation_sms", "").strip() or None,
                "winner_notification_sms": row.get("winner_notification_sms", "").strip() or None,
                "non_winner_sms": row.get("non_winner_sms", "").strip() or None
            })
            
            # Official rules
            if any(row.get(field) for field in ["sponsor_name", "prize_value_usd", "terms_url", "eligibility_text"]):
                contest_data["official_rules"] = {
                    "sponsor_name": row.get("sponsor_name", "").strip() or None,
                    "prize_value_usd": self._parse_float_field(row, "prize_value_usd"),
                    "terms_url": row.get("terms_url", "").strip() or None,
                    "eligibility_text": row.get("eligibility_text", "").strip() or None
                }
            
            return contest_data
            
        except Exception as e:
            raise ValidationException(
                message=f"Failed to parse CSV row: {str(e)}",
                error_code=ErrorCode.VALIDATION_FAILED,
                details={"row": row, "error": str(e)}
            )
    
    def _get_required_field(self, row: Dict[str, str], field_name: str) -> str:
        """Get required field from CSV row with validation."""
        value = row.get(field_name, "").strip()
        if not value:
            raise ValidationException(
                message=f"Required field '{field_name}' is missing or empty",
                error_code=ErrorCode.MISSING_REQUIRED_FIELD,
                details={"field": field_name}
            )
        return value
    
    def _parse_datetime_field(self, row: Dict[str, str], field_name: str) -> datetime:
        """Parse datetime field from CSV row."""
        value = row.get(field_name, "").strip()
        if not value:
            raise ValidationException(
                message=f"Required datetime field '{field_name}' is missing",
                error_code=ErrorCode.MISSING_REQUIRED_FIELD,
                details={"field": field_name}
            )
        
        try:
            return parse_datetime(value)
        except Exception as e:
            raise ValidationException(
                message=f"Invalid datetime format for field '{field_name}': {value}",
                error_code=ErrorCode.FIELD_VALUE_INVALID,
                details={"field": field_name, "value": value, "error": str(e)}
            )
    
    def _parse_int_field(self, row: Dict[str, str], field_name: str, default: Optional[int] = None) -> Optional[int]:
        """Parse integer field from CSV row."""
        value = row.get(field_name, "").strip()
        if not value:
            return default
        
        try:
            return int(value)
        except ValueError:
            if default is not None:
                return default
            raise ValidationException(
                message=f"Invalid integer value for field '{field_name}': {value}",
                error_code=ErrorCode.FIELD_VALUE_INVALID,
                details={"field": field_name, "value": value}
            )
    
    def _parse_float_field(self, row: Dict[str, str], field_name: str, default: Optional[float] = None) -> Optional[float]:
        """Parse float field from CSV row."""
        value = row.get(field_name, "").strip()
        if not value:
            return default
        
        try:
            return float(value)
        except ValueError:
            if default is not None:
                return default
            raise ValidationException(
                message=f"Invalid float value for field '{field_name}': {value}",
                error_code=ErrorCode.FIELD_VALUE_INVALID,
                details={"field": field_name, "value": value}
            )
    
    async def validate_csv_format(self, csv_content: str) -> Dict[str, Any]:
        """
        Validate CSV format and required columns.
        
        Args:
            csv_content: CSV file content as string
            
        Returns:
            Validation results with column information
        """
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Required columns
            required_columns = ["name", "description", "start_time", "end_time"]
            
            # Optional columns
            optional_columns = [
                "location", "prize_description", "contest_type", "entry_method",
                "winner_selection_method", "minimum_age", "max_entries_per_person",
                "location_type", "selected_states", "radius_address", "radius_miles",
                "entry_confirmation_sms", "winner_notification_sms", "non_winner_sms",
                "sponsor_name", "prize_value_usd", "terms_url", "eligibility_text"
            ]
            
            # Check columns
            fieldnames = csv_reader.fieldnames or []
            missing_required = [col for col in required_columns if col not in fieldnames]
            extra_columns = [col for col in fieldnames if col not in required_columns + optional_columns]
            
            # Count rows
            row_count = sum(1 for _ in csv_reader)
            
            return {
                "valid": len(missing_required) == 0,
                "total_columns": len(fieldnames),
                "total_rows": row_count,
                "required_columns": required_columns,
                "optional_columns": optional_columns,
                "present_columns": fieldnames,
                "missing_required_columns": missing_required,
                "extra_columns": extra_columns,
                "validation_errors": [f"Missing required column: {col}" for col in missing_required]
            }
            
        except Exception as e:
            raise ValidationException(
                message=f"Failed to validate CSV format: {str(e)}",
                error_code=ErrorCode.VALIDATION_FAILED,
                details={"error": str(e)}
            )
    
    async def get_import_template(self) -> str:
        """
        Generate CSV template for contest imports.
        
        Returns:
            CSV template as string
        """
        headers = [
            "name", "description", "start_time", "end_time",
            "location", "prize_description", "contest_type", "entry_method",
            "winner_selection_method", "minimum_age", "max_entries_per_person",
            "location_type", "selected_states", "radius_address", "radius_miles",
            "entry_confirmation_sms", "winner_notification_sms", "non_winner_sms",
            "sponsor_name", "prize_value_usd", "terms_url", "eligibility_text"
        ]
        
        # Create sample row
        sample_row = [
            "Sample Contest",
            "This is a sample contest description",
            "2024-01-01T10:00:00Z",
            "2024-01-31T23:59:59Z",
            "United States",
            "$1000 Cash Prize",
            "general",
            "sms",
            "random",
            "18",
            "1",
            "united_states",
            "",
            "",
            "",
            "Thanks for entering! Good luck!",
            "Congratulations! You won!",
            "Thanks for participating!",
            "Sample Company",
            "1000.00",
            "https://example.com/terms",
            "Must be 18+ and US resident"
        ]
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(sample_row)
        
        return output.getvalue()
