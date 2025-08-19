from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import re
from app.database.database import get_db
from app.models.user import User
from app.models.otp import OTP
from app.schemas.auth import PhoneVerificationRequest, TokenResponse
from app.schemas.otp import OTPRequest, OTPVerification, OTPResponse, OTPVerificationResponse
from app.core.auth import create_access_token
from app.core.sms_service import sms_service
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/auth", tags=["authentication"])


def normalize_phone(phone: str) -> str:
    """Normalize phone number to E.164 format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Add country code if missing (assuming US)
    if len(digits) == 10:
        digits = '1' + digits
    elif len(digits) == 11 and digits.startswith('1'):
        pass
    else:
        raise ValueError("Invalid phone number format")
    
    return '+' + digits


@router.post("/request-otp", response_model=OTPResponse)
async def request_otp(
    otp_request: OTPRequest,
    db: Session = Depends(get_db)
):
    """
    Request OTP code for phone verification.
    Includes rate limiting to prevent abuse.
    """
    try:
        phone = normalize_phone(otp_request.phone)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    # Check rate limiting
    rate_limit_key = f"otp_request:{phone}"
    if not rate_limiter.is_allowed(rate_limit_key):
        remaining_time = rate_limiter.get_reset_time(rate_limit_key)
        retry_after = int(remaining_time - datetime.now().timestamp()) if remaining_time else 300
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please try again later.",
            headers={"Retry-After": str(retry_after)}
        )
    
    # Generate OTP code
    code = sms_service.generate_otp()
    
    # Store OTP in database (expires in 5 minutes)
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    # Clean up old OTPs for this phone
    db.query(OTP).filter(OTP.phone == phone, OTP.verified == False).delete()
    
    # Create new OTP
    otp_record = OTP(
        phone=phone,
        code=code,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()
    
    # Send SMS
    sms_sent = await sms_service.send_otp(phone, code)
    
    if not sms_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again."
        )
    
    return OTPResponse(
        message="OTP sent successfully",
        retry_after=None
    )


@router.post("/verify-otp", response_model=OTPVerificationResponse)
async def verify_otp(
    otp_verification: OTPVerification,
    db: Session = Depends(get_db)
):
    """
    Verify OTP code and return JWT token on success.
    """
    try:
        phone = normalize_phone(otp_verification.phone)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    # Find the OTP record
    otp_record = db.query(OTP).filter(
        OTP.phone == phone,
        OTP.verified == False,
        OTP.expires_at > datetime.utcnow()
    ).order_by(OTP.created_at.desc()).first()
    
    if not otp_record:
        return OTPVerificationResponse(
            success=False,
            message="Invalid or expired OTP code"
        )
    
    # Increment attempts
    otp_record.attempts += 1
    
    # Check max attempts (3 attempts allowed)
    if otp_record.attempts > 3:
        db.commit()
        return OTPVerificationResponse(
            success=False,
            message="Too many verification attempts. Please request a new OTP."
        )
    
    # Verify the code
    if otp_record.code != otp_verification.code:
        db.commit()
        return OTPVerificationResponse(
            success=False,
            message="Invalid OTP code"
        )
    
    # Mark OTP as verified
    otp_record.verified = True
    
    # Get or create user
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        user = User(phone=phone)
        db.add(user)
        db.flush()  # Get the ID without committing
    
    db.commit()
    
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
    # Normalize phone number (basic validation)
    try:
        phone = normalize_phone(phone_data.phone)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    # Check if user exists, create if not
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        user = User(phone=phone)
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
