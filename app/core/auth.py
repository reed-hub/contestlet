from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token with enhanced role information"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_user_token(user_id: int, phone: str, role: str = "user", **extra_claims) -> str:
    """
    Create a JWT token for a user with role information.
    
    Args:
        user_id: User's database ID
        phone: User's phone number
        role: User's role (admin, sponsor, user)
        **extra_claims: Additional claims to include in token
    
    Returns:
        JWT token string
    """
    token_data = {
        "sub": str(user_id),
        "phone": phone,
        "role": role,
        **extra_claims
    }
    return create_access_token(token_data)


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def extract_user_info(token: str) -> Optional[dict]:
    """
    Extract user information from JWT token.
    
    Returns:
        Dict with user_id, phone, role, and other claims if valid, None otherwise
    """
    payload = verify_token(token)
    if not payload:
        return None
    
    try:
        return {
            "user_id": int(payload.get("sub")),
            "phone": payload.get("phone"),
            "role": payload.get("role", "user"),
            "exp": payload.get("exp"),
            **{k: v for k, v in payload.items() if k not in ["sub", "phone", "role", "exp"]}
        }
    except (ValueError, TypeError):
        return None