"""
SMS Notification Service for Contestlet
Handles sending SMS notifications to contest winners and other notifications.
"""

import logging
from typing import Tuple, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from app.core.config import settings
from app.core.vercel_config import get_environment_config

logger = logging.getLogger(__name__)


class SMSNotificationService:
    """Service for sending SMS notifications via Twilio"""
    
    def __init__(self):
        # Get environment-specific configuration
        self.env_config = get_environment_config()
        self.use_mock = settings.USE_MOCK_SMS or self.env_config.get("use_mock_sms", False)
        
        if not self.use_mock:
            if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
                logger.warning("Twilio credentials not configured. SMS notifications will use mock mode.")
                self.use_mock = True
            else:
                try:
                    self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                    self.from_phone = settings.TWILIO_PHONE_NUMBER
                    logger.info("SMS notification service initialized with Twilio")
                except Exception as e:
                    logger.error(f"Failed to initialize Twilio client: {e}")
                    self.use_mock = True
        
        if self.use_mock:
            logger.info("SMS notification service initialized in MOCK mode")
    
    def _is_phone_allowed_in_staging(self, phone: str) -> bool:
        """Check if phone number is allowed in staging environment"""
        if self.env_config.get("environment") != "staging":
            return True  # Not staging, allow all
        
        if not self.env_config.get("staging_sms_whitelist", False):
            return True  # Whitelist disabled, allow all
        
        allowed_phones = self.env_config.get("staging_allowed_phones", [])
        return phone in allowed_phones
    
    async def send_notification(self, to_phone: str, message: str, notification_type: str = "general", test_mode: bool = False) -> Tuple[bool, str, Optional[str]]:
        """
        Send SMS notification to a phone number
        
        Args:
            to_phone: Recipient phone number (E.164 format)
            message: SMS message content
            notification_type: Type of notification (winner, reminder, etc.)
            test_mode: If True, simulate sending without actually sending SMS
        
        Returns:
            Tuple of (success: bool, message: str, twilio_sid: Optional[str])
        """
        try:
            # Check staging whitelist if applicable
            if not self._is_phone_allowed_in_staging(to_phone):
                logger.warning(f"SMS to {self._mask_phone(to_phone)} blocked - not in staging whitelist")
                return False, "Phone number not allowed in staging environment", None
            
            if test_mode:
                return await self._send_test_notification(to_phone, message, notification_type)
            elif self.use_mock:
                return await self._send_mock_notification(to_phone, message, notification_type)
            else:
                return await self._send_real_notification(to_phone, message, notification_type)
        
        except Exception as e:
            logger.error(f"SMS notification error: {e}")
            return False, f"SMS notification failed: {str(e)}", None
    
    async def _send_test_notification(self, to_phone: str, message: str, notification_type: str) -> Tuple[bool, str, Optional[str]]:
        """Send test SMS notification (simulated, no actual SMS sent)"""
        masked_phone = f"{to_phone[:2]}***{to_phone[-4:]}" if len(to_phone) >= 6 else to_phone
        
        print(f"🧪 TEST SMS [{notification_type.upper()}] to {masked_phone}:")
        print(f"   Message: {message}")
        print(f"   Status: Simulated (test mode)")
        
        logger.info(f"Test SMS simulated to {masked_phone}: {message[:50]}...")
        
        return True, f"SMS notification simulated successfully (test mode)", "TEST_MODE_SID"
    
    async def _send_mock_notification(self, to_phone: str, message: str, notification_type: str) -> Tuple[bool, str, Optional[str]]:
        """Send mock SMS notification (for development/testing)"""
        masked_phone = f"{to_phone[:2]}***{to_phone[-4:]}" if len(to_phone) >= 6 else to_phone
        
        print(f"📱 MOCK SMS [{notification_type.upper()}] to {masked_phone}:")
        print(f"   Message: {message}")
        print(f"   Status: Delivered (mock)")
        
        logger.info(f"Mock SMS sent to {masked_phone}: {message[:50]}...")
        
        return True, f"SMS notification sent successfully (mock mode)", "MOCK_MODE_SID"
    
    async def _send_real_notification(self, to_phone: str, message: str, notification_type: str) -> Tuple[bool, str, Optional[str]]:
        """Send real SMS notification via Twilio"""
        try:
            # Send SMS via Twilio
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=to_phone
            )
            
            masked_phone = f"{to_phone[:2]}***{to_phone[-4:]}" if len(to_phone) >= 6 else to_phone
            logger.info(f"SMS sent to {masked_phone} - SID: {twilio_message.sid}")
            
            return True, f"SMS notification sent successfully - SID: {twilio_message.sid}", twilio_message.sid
        
        except TwilioException as e:
            logger.error(f"Twilio SMS error: {e}")
            return False, f"SMS delivery failed: {str(e)}", None
        
        except Exception as e:
            logger.error(f"Unexpected SMS error: {e}")
            return False, f"SMS notification failed: {str(e)}", None
    
    async def send_winner_notification(self, winner_phone: str, contest_name: str, custom_message: Optional[str] = None, test_mode: bool = False) -> Tuple[bool, str, Optional[str]]:
        """
        Send winner notification SMS
        
        Args:
            winner_phone: Winner's phone number
            contest_name: Name of the contest
            custom_message: Optional custom message, otherwise uses default template
            test_mode: If True, simulate sending without actually sending SMS
        
        Returns:
            Tuple of (success: bool, message: str, twilio_sid: Optional[str])
        """
        if custom_message:
            message = custom_message
        else:
            message = f"🎉 Congratulations! You're the winner of '{contest_name}'! We'll contact you soon with details about claiming your prize."
        
        return await self.send_notification(winner_phone, message, "winner", test_mode)
    
    async def send_contest_reminder(self, user_phone: str, contest_name: str, hours_remaining: int, test_mode: bool = False) -> Tuple[bool, str, Optional[str]]:
        """Send contest reminder SMS"""
        message = f"⏰ Reminder: The '{contest_name}' contest ends in {hours_remaining} hours! Don't miss your chance to win."
        
        return await self.send_notification(user_phone, message, "reminder", test_mode)
    
    def get_status(self) -> dict:
        """Get SMS service status"""
        return {
            "service": "SMS Notification Service",
            "mode": "mock" if self.use_mock else "production",
            "twilio_configured": not self.use_mock,
            "ready": True
        }


# Global instance
sms_notification_service = SMSNotificationService()
