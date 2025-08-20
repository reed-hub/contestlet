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

### Delete Contest
```bash
DELETE /admin/contests/{contest_id}
Authorization: Bearer {admin_token}

# Success Response (200)
{
  "status": "success",
  "message": "Contest 'Summer Giveaway' deleted successfully",
  "deleted_contest_id": 123,
  "cleanup_summary": {
    "entries_deleted": 45,
    "notifications_deleted": 12,
    "official_rules_deleted": 1,
    "dependencies_cleared": 58
  }
}

# Error Responses
# 404 - Contest not found
{
  "detail": "Contest not found"
}

# 403 - Admin authentication required  
{
  "detail": "Not authenticated"
}

# 409 - Cannot delete active contest
{
  "detail": "Cannot delete active contest with 45 entries. Contest ends at 2024-07-31T23:59:59Z."
}
```

### View All Contests
```bash
GET /admin/contests
Authorization: Bearer {admin_token}

# Response includes status field
{
  "id": 11,
  "name": "Contest Name",
  "active": false,
  "start_time": "2024-01-01T10:00:00",
  "end_time": "2024-01-02T10:00:00",
  "status": "ended",  # ended, active, upcoming, inactive
  "entry_count": 5
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
Authorization: Bearer {admin_jwt_token}  # ⚠️ JWT REQUIRED (not legacy token)
Content-Type: application/json

{
  "entry_id": 12,
  "message": "🎉 Congrats! You're the winner of our Coca-Cola Summer Contest!",
  "test_mode": false  # Optional: true to simulate without sending SMS
}

# Success Response
{
  "success": true,
  "message": "Winner notification sent successfully",
  "entry_id": 12,
  "contest_id": 1,
  "winner_phone": "+1***8204",
  "sms_status": "SMS notification sent successfully - SID: SM...",
  "test_mode": false,
  "notification_id": 5,
  "twilio_sid": "SM1234567890abcdef...",
  "notification_sent_at": "2025-08-20T04:20:45.480744"
}

# Rate Limited Response (429)
{
  "detail": "Too many SMS notifications. Please wait before sending another."
}

# Legacy Token Rejected (403)
{
  "detail": "SMS notifications require admin JWT authentication. Please authenticate via OTP."
}
```

### View SMS Notification Logs
```bash
GET /admin/notifications?contest_id=1&notification_type=winner&limit=50
Authorization: Bearer {admin_token}

# Query Parameters (all optional)
# - contest_id: Filter by specific contest
# - notification_type: Filter by type (winner, reminder, general)
# - limit: Number of records (default: 50, max: 50)

# Response
[
  {
    "id": 5,
    "contest_id": 1,
    "user_id": 2,
    "entry_id": 12,
    "message": "🎉 Congrats! You're the winner!",
    "notification_type": "winner",
    "status": "sent",          # sent, failed, pending
    "twilio_sid": "SM1234567890abcdef...",
    "error_message": null,
    "test_mode": false,
    "sent_at": "2025-08-20T04:20:45.480744",
    "admin_user_id": "1",
    "contest_name": "Summer Contest",
    "user_phone": "+1***8204"  # Masked for privacy
  }
]
```

## 🌍 Timezone Management

### Get Supported Timezones
```bash
GET /admin/profile/timezones

# Response
{
  "timezones": [
    {
      "timezone": "America/New_York",
      "display_name": "Eastern Time (ET)",
      "current_time": "2024-01-15T14:30:00-05:00",
      "utc_offset": "-05:00",
      "is_dst": false
    },
    {
      "timezone": "America/Los_Angeles", 
      "display_name": "Pacific Time (PT)",
      "current_time": "2024-01-15T11:30:00-08:00",
      "utc_offset": "-08:00",
      "is_dst": false
    }
  ],
  "default_timezone": "UTC"
}
```

### Set Admin Timezone Preferences
```bash
POST /admin/profile/timezone
Authorization: Bearer {admin_jwt}
Content-Type: application/json

{
  "timezone": "America/New_York",
  "timezone_auto_detect": false
}

# Response
{
  "admin_user_id": "admin_123",
  "timezone": "America/New_York",
  "timezone_auto_detect": false,
  "created_at": "2024-01-15T19:30:00Z",
  "updated_at": "2024-01-15T19:30:00Z"
}
```

### Get Admin Timezone Preferences  
```bash
GET /admin/profile/timezone
Authorization: Bearer {admin_jwt}

# Response: Same format as POST /admin/profile/timezone
```

### Update Admin Timezone Preferences
```bash
PUT /admin/profile/timezone
Authorization: Bearer {admin_jwt}
Content-Type: application/json

{
  "timezone": "America/Los_Angeles"  # Only update timezone, keep auto_detect
}

# Response: Updated admin profile
```

### Reset Timezone Preferences
```bash
DELETE /admin/profile/timezone
Authorization: Bearer {admin_jwt}

# Response
{
  "message": "Timezone preferences reset to defaults"
}
```

### 🛑 SMS Notification Security
- **Rate Limited**: 5 SMS per 5 minutes per admin
- **JWT Required**: Must use admin JWT from OTP auth (legacy tokens rejected)
- **Entry Validation**: User must have actually entered the contest
- **Audit Trail**: All SMS attempts logged to database

### 📊 Contest Status Values
- **"ended"**: Contest has finished (past end_time)
- **"active"**: Contest is currently running
- **"upcoming"**: Contest hasn't started yet (future start_time)  
- **"inactive"**: Contest is manually disabled but hasn't ended

### 🌍 How Timezone Handling Works

#### **Core Principle: UTC Storage, Local Display**
- **Database**: All times stored as UTC
- **Admin Interface**: Times displayed in admin's preferred timezone
- **API**: Always sends/receives UTC times with timezone metadata

#### **Contest Creation Flow**
```javascript
// 1. Admin enters time in their timezone
Admin input: "2024-01-15 14:30" (2:30 PM Eastern)

// 2. Frontend converts to UTC for API
API payload: {
  "start_time": "2024-01-15T19:30:00Z"  // UTC
}

// 3. Backend adds timezone metadata
Stored contest: {
  "start_time": "2024-01-15T19:30:00Z",     // UTC for storage
  "created_timezone": "America/New_York",    // Admin's timezone context
  "admin_user_id": "admin_123"               // Who created it
}
```

#### **Admin Timezone Workflow**
1. **Set preferences**: Choose timezone in `/admin/profile`
2. **Create contests**: Enter times in your timezone
3. **View contests**: Times display in your timezone
4. **System handles conversion**: UTC storage + timezone context

#### **Supported Timezones**
- **US**: Eastern, Central, Mountain, Pacific, Arizona, Alaska, Hawaii
- **International**: UTC, GMT, CET, JST, CST, AEST
- **Canada**: Eastern, Central, Mountain, Pacific

#### **Important Notes**
- ⚠️ **Frontend must convert to UTC** before sending to API
- ⚠️ **Always include timezone metadata** in contest responses
- ⚠️ **Handle daylight saving time** transitions properly
- ⚠️ **Validate timezone identifiers** before API calls

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
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_VERIFY_SERVICE_SID=VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
USE_MOCK_SMS=true  # false for production SMS
```
