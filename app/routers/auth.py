from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.database import get_db
from app.models.user import User
from app.schemas.auth import PhoneVerificationRequest, TokenResponse
from app.schemas.otp import OTPRequest, OTPVerification, OTPResponse, OTPVerificationResponse
from app.core.auth import create_access_token
from app.core.twilio_verify_service import twilio_verify_service
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/auth", tags=["authentication"])


# normalize_phone function removed - using Twilio Verify's phone validation instead


@router.post("/request-otp", response_model=OTPResponse)
async def request_otp(
    otp_request: OTPRequest,
    db: Session = Depends(get_db)
):
    """
    Request OTP code for phone verification using Twilio Verify API.
    Includes rate limiting to prevent abuse.
    """
    # Check rate limiting (using original phone for consistency)
    rate_limit_key = f"otp_request:{otp_request.phone}"
    if not rate_limiter.is_allowed(rate_limit_key):
        remaining_time = rate_limiter.get_reset_time(rate_limit_key)
        retry_after = int(remaining_time - datetime.now().timestamp()) if remaining_time else 300
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please try again later.",
            headers={"Retry-After": str(retry_after)}
        )
    
    # Send verification using Twilio Verify API
    success, message = await twilio_verify_service.send_verification(otp_request.phone)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return OTPResponse(
        message=message,
        retry_after=None
    )


@router.post("/verify-otp", response_model=OTPVerificationResponse)
async def verify_otp(
    otp_verification: OTPVerification,
    db: Session = Depends(get_db)
):
    """
    Verify OTP code using Twilio Verify API and return JWT token on success.
    """
    # Check verification using Twilio Verify API
    success, message = await twilio_verify_service.check_verification(
        otp_verification.phone, 
        otp_verification.code
    )
    
    if not success:
        return OTPVerificationResponse(
            success=False,
            message=message
        )
    
    # Verification successful - get the validated phone number
    is_valid, formatted_phone, error = twilio_verify_service.validate_phone_number(otp_verification.phone)
    if not is_valid:
        return OTPVerificationResponse(
            success=False,
            message=error or "Phone number validation failed"
        )
    
    # Get or create user with the formatted phone number
    user = db.query(User).filter(User.phone == formatted_phone).first()
    if not user:
        user = User(phone=formatted_phone)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return OTPVerificationResponse(
        success=True,
        message="Phone verified successfully",
        access_token=access_token,
        token_type="bearer",
        user_id=user.id
    )


@router.post("/verify-phone", response_model=TokenResponse)
async def verify_phone(
    phone_data: PhoneVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Legacy endpoint: Verify phone number and return JWT token.
    DEPRECATED: Use request-otp and verify-otp instead.
    """
    # Validate phone number using the same validation as Twilio Verify
    is_valid, formatted_phone, error = twilio_verify_service.validate_phone_number(phone_data.phone)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Invalid phone number format"
        )
    
    # Check if user exists, create if not
    user = db.query(User).filter(User.phone == formatted_phone).first()
    if not user:
        user = User(phone=formatted_phone)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id
    )
