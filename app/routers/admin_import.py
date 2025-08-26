from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.schemas.campaign_import import CampaignImportRequest, CampaignImportResponse
from app.core.admin_auth import get_admin_user
from app.services.campaign_import_service import campaign_import_service

router = APIRouter(prefix="/admin/import", tags=["admin-import"])


@router.post("/one-sheet", response_model=CampaignImportResponse)
async def import_campaign_from_sheet(
    file: UploadFile = File(...),
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Import campaign data from uploaded spreadsheet"""
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be Excel (.xlsx, .xls) or CSV format"
        )
    
    try:
        # Process the uploaded file
        result = await campaign_import_service.import_from_file(file, admin_user["sub"])
        
        return CampaignImportResponse(
            success=True,
            message=f"Successfully imported {result['contests_created']} contests",
            contests_created=result['contests_created'],
            contests_updated=result.get('contests_updated', 0),
            errors=result.get('errors', [])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.post("/validate-sheet")
async def validate_campaign_sheet(
    file: UploadFile = File(...),
    admin_user: dict = Depends(get_admin_user)
):
    """Validate campaign spreadsheet without importing"""
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be Excel (.xlsx, .xls) or CSV format"
        )
    
    try:
        # Validate the file structure and data
        validation_result = await campaign_import_service.validate_file(file)
        
        return {
            "valid": validation_result['valid'],
            "message": validation_result['message'],
            "errors": validation_result.get('errors', []),
            "warnings": validation_result.get('warnings', []),
            "contests_found": validation_result.get('contests_found', 0)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/templates")
async def get_import_templates(admin_user: dict = Depends(get_admin_user)):
    """Get import template files and instructions"""
    return {
        "templates": [
            {
                "name": "Campaign Import Template",
                "description": "Excel template for importing multiple contests",
                "format": "xlsx",
                "fields": [
                    "contest_name",
                    "description", 
                    "start_time",
                    "end_time",
                    "prize_description",
                    "max_entries_per_person",
                    "total_entry_limit"
                ]
            }
        ],
        "instructions": [
            "Download the template and fill in contest data",
            "Ensure dates are in ISO format (YYYY-MM-DD HH:MM:SS)",
            "Upload the completed file to import contests"
        ]
    }
