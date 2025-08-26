from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.database import get_db
from app.models.user import User
from app.schemas.auth import PhoneVerificationRequest, TokenResponse, UserMeResponse
from app.schemas.otp import OTPRequest, OTPVerification, OTPResponse, OTPVerificationResponse
from app.core.auth import create_access_token, create_user_token, verify_token
from app.core.twilio_verify_service import twilio_verify_service
from app.core.rate_limiter import rate_limiter
from app.core.config import get_settings

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
        # Create new user with default role
        settings = get_settings()
        admin_phones = settings.phone_set
        default_role = "admin" if formatted_phone in admin_phones else "user"
        
        user = User(
            phone=formatted_phone,
            role=default_role,
            is_verified=True  # Phone is verified through OTP
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update verification status for existing user
        if not user.is_verified:
            user.is_verified = True
            db.commit()
    
    # Create JWT token with user's actual role from database
    access_token = create_user_token(
        user_id=user.id,
        phone=user.phone,
        role=user.role
    )
    
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
    
    # Determine user role based on admin phone list  
    settings = get_settings()
    admin_phones = settings.phone_set
    user_role = "admin" if formatted_phone in admin_phones else "user"
    
    # Create JWT token with role
    access_token = create_access_token(data={
        "sub": str(user.id),
        "phone": formatted_phone,
        "role": user_role
    })
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id
    )


def get_token_payload(authorization: str = Header(None, alias="Authorization")):
    """Extract and verify JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_info(
    payload: dict = Depends(get_token_payload)
):
    """
    Get current user information from JWT token.
    Returns user ID, phone, and role.
    """
    return UserMeResponse(
        user_id=int(payload.get("sub")),
        phone=payload.get("phone", ""),
        role=payload.get("role", "user")
    )
