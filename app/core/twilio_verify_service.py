import logging
import phonenumbers
from typing import Optional, Tuple, Dict, Any
from functools import wraps
from app.core.config import get_settings
from app.core.exceptions import raise_validation_error, raise_business_logic_error, ErrorCode

logger = logging.getLogger(__name__)


class TwilioVerifyService:
    """Elegant Twilio Verify service with graceful fallbacks and async support"""
    
    def __init__(self):
        self._settings = get_settings()
        self._client = None
        self._verify_service_sid = None
        self._use_mock = True
        self._twilio_available = False
        
        self._initialize_twilio()
        self._log_configuration()
    
    def _initialize_twilio(self):
        """Initialize Twilio client with graceful fallbacks"""
        try:
            # Force mock mode in development environment
            if self._settings.environment == "development" or self._settings.use_mock_sms:
                logger.info("Development environment detected - forcing mock SMS mode")
                self._use_mock = True
                self._twilio_available = False
                return
            
            # Check if Twilio library is available
            try:
                from twilio.rest import Client
                self._twilio_available = True
            except ImportError:
                logger.warning("Twilio library not available, using mock mode")
                self._twilio_available = False
                self._use_mock = True
                return
            
            # Check configuration
            if not self._settings.is_twilio_configured:
                logger.warning("Twilio not fully configured, using mock mode")
                self._use_mock = True
                return
            
            # Initialize Twilio client
            try:
                from twilio.rest import Client
                self._client = Client(
                    self._settings.twilio_account_sid,
                    self._settings.twilio_auth_token
                )
                self._verify_service_sid = self._settings.twilio_verify_service_sid
                self._use_mock = False
                logger.info("Twilio client initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self._use_mock = True
                
        except Exception as e:
            logger.error(f"Critical error in Twilio initialization: {e}")
            self._use_mock = True
            self._twilio_available = False
    
    def _log_configuration(self):
        """Log the final service configuration"""
        mode = "MOCK" if self._use_mock else "REAL"
        logger.info(f"TwilioVerifyService initialized in {mode} mode")
    
    @property
    def is_mock_mode(self) -> bool:
        """Check if service is running in mock mode"""
        return self._use_mock
    
    @property
    def is_available(self) -> bool:
        """Check if Twilio service is available"""
        return self._twilio_available and not self._use_mock
    
    def validate_phone_number(self, phone: str) -> Tuple[bool, str, Optional[str]]:
        """Validate and format phone number with comprehensive validation"""
        try:
            # Handle mock mode test numbers
            if self._use_mock:
                return self._validate_mock_phone(phone)
            
            # Real phone number validation
            return self._validate_real_phone(phone)
            
        except Exception as e:
            logger.error(f"Phone validation error: {e}")
            return False, phone, f"Validation error: {str(e)}"
    
    def _validate_mock_phone(self, phone: str) -> Tuple[bool, str, Optional[str]]:
        """Validate phone numbers in mock mode"""
        # Allow common test phone number patterns
        test_patterns = [
            "+15551234567", "+15559876543", "+15551111111", 
            "+15552222222", "+15553333333", "+15554444444",
            "+18187958204"  # Admin number
        ]
        
        if phone in test_patterns:
            logger.info(f"MOCK MODE: Accepting test phone number {self._mask_phone(phone)}")
            return True, phone, None
        
        # In mock mode, also accept any valid US format
        try:
            parsed = phonenumbers.parse(phone, "US")
            if phonenumbers.is_valid_number(parsed):
                formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                return True, formatted, None
        except phonenumbers.NumberParseException:
            pass
        
        return False, phone, "Invalid phone number format"
    
    def _validate_real_phone(self, phone: str) -> Tuple[bool, str, Optional[str]]:
        """Validate real phone numbers with strict requirements"""
        try:
            parsed = phonenumbers.parse(phone, "US")
            
            if not phonenumbers.is_valid_number(parsed):
                return False, phone, "Invalid phone number"
            
            # Check if it's a US number
            if phonenumbers.region_code_for_number(parsed) != "US":
                return False, phone, "Only US phone numbers are supported"
            
            # Format in E.164 format
            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            return True, formatted, None
            
        except phonenumbers.NumberParseException as e:
            return False, phone, f"Phone number parse error: {e}"
    
    async def send_verification(self, phone: str) -> Tuple[bool, str]:
        """Send verification code via Twilio Verify API"""
        try:
            # Validate phone number first
            is_valid, formatted_phone, error = self.validate_phone_number(phone)
            if not is_valid:
                return False, error or "Invalid phone number"
            
            if self._use_mock:
                return self._mock_send_verification(formatted_phone)
            
            return await self._real_send_verification(formatted_phone)
            
        except Exception as e:
            logger.error(f"Send verification error: {e}")
            return False, f"Failed to send verification: {str(e)}"
    
    def _mock_send_verification(self, phone: str) -> Tuple[bool, str]:
        """Mock verification sending for development"""
        mock_code = "123456"  # Fixed code for development
        logger.info(f"🔐 MOCK SMS to {phone}: Your verification code is: {mock_code}")
        print(f"🔐 MOCK SMS to {phone}: Your verification code is: {mock_code}")
        return True, "Verification code sent successfully (mock mode)"
    
    async def _real_send_verification(self, phone: str) -> Tuple[bool, str]:
        """Real verification sending via Twilio"""
        try:
            verification = self._client.verify.v2.services(
                self._verify_service_sid
            ).verifications.create(
                to=phone,
                channel='sms'
            )
            
            logger.info(f"Verification sent to {self._mask_phone(phone)} via Twilio")
            return True, "Verification code sent successfully"
            
        except Exception as e:
            logger.error(f"Twilio verification error: {e}")
            return False, f"Failed to send verification: {str(e)}"
    
    async def check_verification(self, phone: str, code: str) -> Tuple[bool, str]:
        """Check verification code via Twilio Verify API"""
        try:
            # Validate phone number first
            is_valid, formatted_phone, error = self.validate_phone_number(phone)
            if not is_valid:
                return False, error or "Invalid phone number"
            
            if self._use_mock:
                return self._mock_check_verification(formatted_phone, code)
            
            return await self._real_check_verification(formatted_phone, code)
            
        except Exception as e:
            logger.error(f"Check verification error: {e}")
            return False, f"Failed to check verification: {str(e)}"
    
    def _mock_check_verification(self, phone: str, code: str) -> Tuple[bool, str]:
        """Mock verification checking for development"""
        # Validate basic format
        if not code.isdigit() or len(code) != 6:
            return False, "Invalid verification code (must be 6 digits)"
        
        # Reject obviously invalid codes for security testing
        # Note: 123456 is allowed as it's the standard mock code
        invalid_codes = ["000000", "111111", "222222", "333333", "444444", "555555", 
                        "666666", "777777", "888888", "999999", "654321"]
        
        if code in invalid_codes:
            logger.info(f"🔐 MOCK: Rejected invalid test code {code} for {self._mask_phone(phone)}")
            print(f"🔐 MOCK: Rejected invalid test code {code} for {phone}")
            return False, "Invalid verification code"
        
        # Accept other 6-digit codes in development
        logger.info(f"🔐 MOCK: Verification successful for {self._mask_phone(phone)} with code {code}")
        print(f"🔐 MOCK: Verification successful for {phone} with code {code}")
        return True, "Verification successful (mock mode)"
    
    async def _real_check_verification(self, phone: str, code: str) -> Tuple[bool, str]:
        """Real verification checking via Twilio"""
        try:
            verification_check = self._client.verify.v2.services(
                self._verify_service_sid
            ).verification_checks.create(
                to=phone,
                code=code
            )
            
            if verification_check.status == 'approved':
                logger.info(f"Verification successful for {self._mask_phone(phone)}")
                return True, "Verification successful"
            else:
                logger.warning(f"Verification failed for {self._mask_phone(phone)}: {verification_check.status}")
                return False, "Invalid verification code"
                
        except Exception as e:
            logger.error(f"Twilio verification check error: {e}")
            return False, f"Failed to check verification: {str(e)}"
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for logging privacy"""
        if len(phone) >= 6:
            return f"{phone[:2]}***{phone[-4:]}"
        return phone
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration"""
        return {
            "mode": "mock" if self._use_mock else "real",
            "twilio_available": self._twilio_available,
            "configured": self._settings.is_twilio_configured,
            "verify_service_sid": self._verify_service_sid,
            "account_sid": self._settings.twilio_account_sid[:8] + "..." if self._settings.twilio_account_sid else None
        }


# Global service instance
twilio_verify_service = TwilioVerifyService()


# Decorator for phone validation
def validate_phone(func):
    """Decorator to validate phone numbers before processing"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract phone from kwargs or first argument
        phone = kwargs.get('phone')
        if not phone and args:
            # Try to find phone in the first argument (usually a Pydantic model)
            if hasattr(args[0], 'phone'):
                phone = args[0].phone
        
        if phone:
            is_valid, formatted_phone, error = twilio_verify_service.validate_phone_number(phone)
            if not is_valid:
                raise_validation_error(error or "Invalid phone number", "phone")
            
            # Update the phone with formatted version
            if kwargs.get('phone'):
                kwargs['phone'] = formatted_phone
            elif args and hasattr(args[0], 'phone'):
                args[0].phone = formatted_phone
        
        return await func(*args, **kwargs)
    return wrapper
