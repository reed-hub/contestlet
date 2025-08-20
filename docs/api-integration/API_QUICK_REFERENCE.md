# 📋 Contestlet API - Quick Reference

## 🔗 Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

## 🔐 Authentication (Twilio Verify API)

### Request OTP
```bash
POST /auth/request-otp
Content-Type: application/json

{
  "phone": "18187958204"  # US phone number (10 digits)
}

# Response
{
  "message": "Verification code sent successfully",
  "retry_after": null
}
```

### Verify OTP
```bash
POST /auth/verify-otp
Content-Type: application/json

{
  "phone": "18187958204",
  "code": "123456"  # 6-digit code from SMS (or 123456 in mock mode)
}

# Success Response (Regular User)
{
  "success": true,
  "message": "Phone verified successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 2
}

# Success Response (Admin User)
{
  "success": true,
  "message": "Phone verified successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  # JWT includes role="admin"
  "token_type": "bearer",
  "user_id": 1
}

# Error Response
{
  "success": false,
  "message": "Invalid verification code",
  "access_token": null,
  "token_type": "bearer",
  "user_id": null
}
```

### Get Current User Info
```bash
GET /auth/me
Authorization: Bearer <access_token>

# Response (Regular User)
{
  "user_id": 2,
  "phone": "+15551234567",
  "role": "user",
  "authenticated": true
}

# Response (Admin User)
{
  "user_id": 1,
  "phone": "+18187958204",
  "role": "admin",
  "authenticated": true
}
```

### Legacy Phone Verification (DEPRECATED)
```bash
POST /auth/verify-phone
Content-Type: application/json

{
  "phone": "18187958204"
}
```

## 🎯 Contest Endpoints

### Get Active Contests
```bash
GET /contests/active?page=1&size=10&location=SF
```

### Find Nearby Contests
```bash
GET /contests/nearby?lat=37.7749&lng=-122.4194&radius=25
```

### Enter Contest
```bash
POST /contests/{contest_id}/enter
Authorization: Bearer {token}
```

### User's Entries
```bash
GET /entries/me
Authorization: Bearer {token}
```

## 🛡️ Admin Endpoints

### Create Contest
```bash
POST /admin/contests
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "name": "Contest Name",
  "description": "Contest description",
  "location": "San Francisco, CA",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "start_time": "2025-08-20T10:00:00",
  "end_time": "2025-08-27T10:00:00",
  "prize_description": "Amazing prize",
  "active": true,
  "official_rules": {
    "eligibility_text": "Must be 18+ and US resident",
    "sponsor_name": "Your Company",
    "start_date": "2025-08-20T10:00:00",
    "end_date": "2025-08-27T10:00:00",
    "prize_value_usd": 1000.0,
    "terms_url": "https://yoursite.com/terms"
  }
}
```

### View Contest Entries
```bash
GET /admin/contests/{contest_id}/entries
Authorization: Bearer {admin_token}
```

### Select Winner
```bash
POST /admin/contests/{contest_id}/select-winner
Authorization: Bearer {admin_token}
```

### Notify Winner via SMS
```bash
POST /admin/contests/{contest_id}/notify-winner
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "entry_id": 12,
  "message": "🎉 Congrats! You're the winner of our Coca-Cola Summer Contest!"
}

# Response
{
  "success": true,
  "message": "Winner notification sent successfully",
  "entry_id": 12,
  "contest_id": 1,
  "winner_phone": "+1***8204",
  "sms_status": "SMS notification sent successfully - SID: SM...",
  "notification_sent_at": "2025-08-20T04:20:45.480744"
}
```

## 📊 Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid data) |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (admin access required) |
| 404 | Not Found |
| 409 | Conflict (duplicate entry) |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Server Error |

## 🔑 Admin Authentication

### OTP-Based Admin Access (Recommended)
```bash
# 1. Request OTP with admin phone number
POST /auth/request-otp
{
  "phone": "18187958204"  # Must be configured as admin phone
}

# 2. Verify OTP to get admin JWT
POST /auth/verify-otp  
{
  "phone": "18187958204",
  "code": "123456"
}
# Returns JWT with role="admin"

# 3. Use admin JWT for all admin endpoints
Authorization: Bearer <admin_jwt_token>
```

### Legacy Admin Token (Deprecated)
```
Authorization: Bearer contestlet-admin-super-secret-token-change-in-production
```

### Configuration
```env
# Add admin phone numbers to .env
ADMIN_PHONES=+18187958204,+15551234567
```

## 📱 SMS Notifications

### Twilio Configuration (SMS)
```env
# Required for SMS notifications
TWILIO_PHONE_NUMBER=+15551234567  # Your Twilio phone number
TWILIO_ACCOUNT_SID=AC...           # Same as OTP verification
TWILIO_AUTH_TOKEN=...              # Same as OTP verification
USE_MOCK_SMS=true                  # Set to false for production SMS
```

## 📱 Phone Format (Twilio Verify)
- **US numbers only**: `5551234567`, `15551234567`, `+15551234567`
- **Auto-formatting**: API accepts various formats, converts to E.164
- **Validation**: Uses `phonenumbers` library for robust validation
- **Test number**: `18187958204` (for development)

## 📍 Geolocation
- Latitude: -90 to 90
- Longitude: -180 to 180
- Radius: 0.1 to 100 miles

## ⏱️ Rate Limits (Twilio Protected)
- **OTP requests**: 5 per 5 minutes per phone number
- **Automatic blocking**: Returns 429 status after limit
- **Reset time**: Provided in `Retry-After` header
- **General API**: No specific limits (reasonable use)

## 🧪 Development Mode
- **Mock SMS**: `USE_MOCK_SMS=true` (default)
- **Test code**: `123456` (always works in mock mode)
- **Real SMS**: Set `USE_MOCK_SMS=false` for production
- **Twilio logs**: Check server console for verification attempts
- **Database**: Auto-creates on first run
- **Interactive docs**: `/docs`

## 🔧 Twilio Configuration
```env
TWILIO_ACCOUNT_SID=AC829dbe9395c71407a7f60887cb816a3a
TWILIO_AUTH_TOKEN=3f376878eacd0d7e81e090c1aeae5368
TWILIO_VERIFY_SERVICE_SID=VA89f2b01132c234a3fd2f3981f81bb773
USE_MOCK_SMS=true  # false for production SMS
```
