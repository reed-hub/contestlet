# 📋 Contestlet API - Quick Reference

**Complete API reference with 100% form support and SMS integration.**

---

## 🔗 **Base URLs**
```
Development: http://localhost:8000
Staging:     https://contestlet-git-staging.vercel.app
Production:  https://contestlet.vercel.app
```

---

## 🔐 **Authentication (Twilio Verify API)**

### **Request OTP**
```bash
POST /auth/request-otp
Content-Type: application/json

{
  "phone": "18187958204"  # US phone number (E.164 format)
}

# Response
{
  "message": "Verification code sent successfully",
  "retry_after": null
}
```

### **Verify OTP**
```bash
POST /auth/verify-otp
Content-Type: application/json

{
  "phone": "18187958204",
  "code": "123456"  # 6-digit code from SMS
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
  "message": "Phone verified successfully - Admin access granted",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  # JWT includes role="admin"
  "token_type": "bearer",
  "user_id": 1,
  "role": "admin"
}
```

### **Get Current User**
```bash
GET /auth/me
Authorization: Bearer <token>

# Response
{
  "id": 1,
  "phone": "+18187958204",
  "created_at": "2024-01-15T10:30:00Z",
  "role": "admin"  # Only present for admin users
}
```

---

## 🎯 **Contests (Public)**

### **List Active Contests**
```bash
GET /contests/active?page=1&size=10

# Response
{
  "contests": [
    {
      "id": 1,
      "name": "Summer Sweepstakes 2025",
      "description": "Win amazing summer prizes!",
      "location": "Boulder, CO",
      "latitude": 40.0150,
      "longitude": -105.2705,
      "start_time": "2025-08-22T10:00:00Z",
      "end_time": "2025-08-25T23:59:59Z",
      "prize_description": "$500 Cash Prize",
      "status": "active",  # upcoming, active, ended, complete
      "created_at": "2025-01-15T10:00:00Z",
      
      # Advanced Configuration (NEW)
      "contest_type": "sweepstakes",
      "entry_method": "sms",
      "winner_selection_method": "random",
      "minimum_age": 21,
      "max_entries_per_person": 5,
      "total_entry_limit": 1000,
      "consolation_offer": "20% discount code",
      "geographic_restrictions": "US residents only",
      "contest_tags": ["summer", "sweepstakes", "mobile"],
      "promotion_channels": ["instagram", "facebook", "sms"]
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

### **Find Nearby Contests**
```bash
GET /contests/nearby?lat=40.0150&lng=-105.2705&radius=25&page=1&size=10

# Response (same as active contests + distance_miles field)
{
  "contests": [
    {
      "id": 1,
      "name": "Local Contest",
      "distance_miles": 12.5,  # Distance from query point
      # ... other contest fields
    }
  ]
}
```

### **Enter Contest**
```bash
POST /contests/1/enter
Authorization: Bearer <token>

# Response
{
  "id": 1,
  "user_id": 2,
  "contest_id": 1,
  "created_at": "2025-01-15T14:30:00Z",
  "message": "Successfully entered contest!"
}

# Error Response (Entry Limit Reached)
{
  "detail": "Maximum 5 entries per person allowed"
}

# Error Response (Contest Full)
{
  "detail": "Contest has reached maximum entry limit"
}
```

---

## 📝 **Entries**

### **Get User's Entries**
```bash
GET /entries/me
Authorization: Bearer <token>

# Response
{
  "entries": [
    {
      "id": 1,
      "contest_id": 1,
      "contest_name": "Summer Sweepstakes",
      "created_at": "2025-01-15T14:30:00Z",
      "contest_status": "active",
      "is_winner": false
    }
  ],
  "total": 1
}
```

---

## 👑 **Admin Endpoints (JWT Required)**

### **Create Contest (100% Form Support)**
```bash
POST /admin/contests
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  # Basic Information
  "name": "Complete Form Contest",
  "description": "Testing all form fields",
  "location": "Boulder, CO",
  "latitude": 40.0150,
  "longitude": -105.2705,
  "start_time": "2025-08-22T10:00:00Z",
  "end_time": "2025-08-25T23:59:59Z",
  "prize_description": "$500 Cash Prize + Gift Cards",
  
  # Advanced Configuration (Phase 1)
  "contest_type": "sweepstakes",  # general, sweepstakes, instant_win
  "entry_method": "sms",          # sms, email, web_form
  "winner_selection_method": "random",  # random, scheduled, instant
  "minimum_age": 21,              # 13-100, COPPA compliance
  "max_entries_per_person": 5,    # null = unlimited
  "total_entry_limit": 1000,      # null = unlimited
  "consolation_offer": "20% discount on next purchase",
  "geographic_restrictions": "US residents only, excluding NY and FL",
  "contest_tags": ["summer", "sweepstakes", "mobile", "retail"],
  "promotion_channels": ["instagram", "facebook", "email", "sms", "website"],
  
  # SMS Templates (Phase 2)
  "sms_templates": {
    "entry_confirmation": "🎉 You're entered in {contest_name}! Prize: {prize_description}. Good luck!",
    "winner_notification": "🏆 Congratulations! You won {prize_description}! Check email for claim instructions.",
    "non_winner": "Thanks for entering {contest_name}! Here's your consolation offer: {consolation_offer}"
  },
  
  # Official Rules (Required)
  "official_rules": {
    "eligibility_text": "Open to legal residents of the United States who are at least 21 years old.",
    "sponsor_name": "Contestlet Demo Company",
    "start_date": "2025-08-22T10:00:00Z",
    "end_date": "2025-08-25T23:59:59Z",
    "prize_value_usd": 500.00,
    "terms_url": "https://contestlet.com/terms"
  }
}

# Success Response
{
  "id": 1,
  "name": "Complete Form Contest",
  "status": "upcoming",
  # ... all submitted fields returned
  "entry_count": 0,
  "official_rules": { /* official rules data */ },
  "message": "Contest created successfully with official rules"
}
```

### **List All Contests (Admin View)**
```bash
GET /admin/contests?page=1&size=10
Authorization: Bearer <admin-token>

# Response
{
  "contests": [
    {
      "id": 1,
      "name": "Summer Sweepstakes",
      "status": "active",  # computed status
      "entry_count": 25,
      "winner_phone": null,
      "winner_selected_at": null,
      # ... all contest fields including advanced configuration
      "official_rules": { /* official rules */ }
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

### **Update Contest**
```bash
PUT /admin/contests/1
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "name": "Updated Contest Name",
  "prize_description": "Updated prize",
  "max_entries_per_person": 10,  # Update entry limits
  "sms_templates": {
    "entry_confirmation": "Updated entry message"
  },
  "official_rules": {
    "prize_value_usd": 750.00
  }
}

# Response: Updated contest object
```

### **Delete Contest**
```bash
DELETE /admin/contests/1
Authorization: Bearer <admin-token>

# Response
{
  "success": true,
  "message": "Contest deleted successfully",
  "contest_id": 1,
  "deletion_summary": {
    "entries_deleted": 5,
    "notifications_deleted": 3,
    "sms_templates_deleted": 2,
    "official_rules_deleted": 1
  }
}

# Error Response (Contest Still Running)
{
  "detail": "Cannot delete running contest with 25 entries. Contest ends at 2025-08-25T23:59:59Z."
}
```

### **Select Contest Winner**
```bash
POST /admin/contests/1/select-winner
Authorization: Bearer <admin-token>

# Response
{
  "success": true,
  "message": "Winner selected successfully",
  "winner": {
    "entry_id": 15,
    "user_phone": "+18187958204",
    "selected_at": "2025-01-15T16:00:00Z"
  },
  "total_entries": 42
}
```

### **Send Winner Notification**
```bash
POST /admin/contests/1/notify-winner
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "test_mode": false,  # true for testing without sending SMS
  "custom_message": "Congratulations! You won our contest!"  # optional override
}

# Response
{
  "success": true,
  "message": "Winner notification sent successfully",
  "recipient": "+18187958204",
  "sms_content": "🏆 Congratulations! You won $500 Cash Prize! Check email for claim instructions.",
  "notification_id": 123
}
```

### **View Contest Entries**
```bash
GET /admin/contests/1/entries?page=1&size=20
Authorization: Bearer <admin-token>

# Response
{
  "entries": [
    {
      "id": 1,
      "user_phone": "+18187958204",
      "created_at": "2025-01-15T14:30:00Z",
      "is_winner": true,
      "winner_selected_at": "2025-01-15T16:00:00Z"
    }
  ],
  "total": 1,
  "contest_name": "Summer Sweepstakes",
  "contest_status": "complete"
}
```

### **Import Campaign One-Sheet**
```bash
POST /admin/contests/import-one-sheet
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "campaign_data": {
    "name": "Summer Flash Sale Contest",
    "description": "Win big with our summer promotion!",
    "reward_logic": {
      "winner_reward": "$100 Gift Card"
    },
    "consolation_offer": "15% off next purchase",
    "non_winner_sms": "Thanks for playing! Use code SUMMER15 for 15% off.",
    "promotion_channels": ["instagram", "email", "sms"],
    "activation_hooks": ["contest_start", "winner_selected"]
  },
  "location": "Denver, CO",
  "latitude": 39.7392,
  "longitude": -104.9903,
  "start_time": "2025-09-01T10:00:00Z",
  "duration_days": 7,
  "admin_user_id": "admin_123"
}

# Response
{
  "success": true,
  "contest_id": 15,
  "message": "Campaign imported successfully as contest",
  "warnings": [],
  "contest_preview": {
    "name": "Summer Flash Sale Contest",
    "prize_description": "$100 Gift Card",
    "status": "upcoming"
  }
}
```

### **View SMS Notification Logs**
```bash
GET /admin/notifications?page=1&size=20&contest_id=1&notification_type=winner_notification
Authorization: Bearer <admin-token>

# Response
{
  "notifications": [
    {
      "id": 123,
      "contest_id": 1,
      "contest_name": "Summer Sweepstakes",
      "recipient_phone": "+18187958204",
      "notification_type": "winner_notification",
      "message_content": "🏆 Congratulations! You won $500 Cash Prize!",
      "sent_at": "2025-01-15T16:05:00Z",
      "delivery_status": "delivered"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

---

## 📱 **SMS Template Variables**

### **Available Variables**
```javascript
// Entry Confirmation Templates
{contest_name}        // "Summer Sweepstakes"
{prize_description}   // "$500 Cash Prize"
{end_time}           // "August 25, 2025 at 11:59 PM"
{sponsor_name}       // "Contestlet Demo Company"

// Winner Notification Templates
{contest_name}        // Contest name
{prize_description}   // Prize details
{winner_name}        // Winner's name (if available)
{claim_instructions} // How to claim prize
{sponsor_name}       // Contest sponsor
{terms_url}          // Terms and conditions URL

// Non-Winner Templates
{contest_name}        // Contest name
{consolation_offer}   // "20% discount code"
{sponsor_name}       // Contest sponsor
{next_contest_info}  // Information about upcoming contests
```

### **Template Examples**
```javascript
// Entry Confirmation
"🎉 You're entered in {contest_name}! Prize: {prize_description}. Drawing on {end_time}. Good luck!"

// Winner Notification
"🏆 WINNER! Congratulations! You won {prize_description} in {contest_name}! Check your email for claim instructions."

// Non-Winner
"Thanks for entering {contest_name}! You didn't win this time, but here's your consolation offer: {consolation_offer}"
```

---

## 🔧 **Form Field Mapping**

### **✅ 100% Supported Form Fields**

| Frontend Field | API Field | Type | Validation |
|----------------|-----------|------|------------|
| **Contest Name** | `name` | string | Required |
| **Description** | `description` | string | Optional |
| **Location** | `location` | string | Optional |
| **Prize Description** | `prize_description` | string | Optional |
| **Prize Value** | `official_rules.prize_value_usd` | number | ≥0, required |
| **Eligibility** | `official_rules.eligibility_text` | string | Required |
| **Start Date/Time** | `start_time` | datetime | Required, ISO format |
| **End Date/Time** | `end_time` | datetime | Required, > start_time |
| **Contest Type** | `contest_type` | enum | general, sweepstakes, instant_win |
| **Entry Method** | `entry_method` | enum | sms, email, web_form |
| **Winner Selection** | `winner_selection_method` | enum | random, scheduled, instant |
| **Minimum Age** | `minimum_age` | integer | 13-100, COPPA compliance |
| **Max Entries/Person** | `max_entries_per_person` | integer | ≥1 or null |
| **Total Entry Limit** | `total_entry_limit` | integer | ≥1 or null |
| **Consolation Offer** | `consolation_offer` | string | Optional |
| **Geographic Restrictions** | `geographic_restrictions` | string | Optional |
| **Contest Tags** | `contest_tags` | array | Optional, comma-separated |
| **Promotion Channels** | `promotion_channels` | array | Optional, checkboxes |
| **Sponsor Name** | `official_rules.sponsor_name` | string | Required |
| **Terms URL** | `official_rules.terms_url` | string | Optional, valid URL |
| **Entry Confirmation SMS** | `sms_templates.entry_confirmation` | string | ≤1600 chars |
| **Winner Notification SMS** | `sms_templates.winner_notification` | string | ≤1600 chars |
| **Non-Winner SMS** | `sms_templates.non_winner` | string | ≤1600 chars |

---

## ⚠️ **Error Responses**

### **Common Error Formats**
```javascript
// Validation Error
{
  "detail": [
    {
      "loc": ["body", "minimum_age"],
      "msg": "Minimum age cannot be less than 13 for legal compliance",
      "type": "value_error"
    }
  ]
}

// Authentication Error
{
  "detail": "Could not validate credentials"
}

// Business Logic Error
{
  "detail": "Maximum 5 entries per person allowed"
}

// Rate Limiting Error
{
  "detail": "Too many OTP requests. Try again in 4 minutes and 30 seconds.",
  "retry_after": 270
}
```

### **HTTP Status Codes**
- **200**: Success
- **201**: Created
- **400**: Bad Request (validation error)
- **401**: Unauthorized (invalid/missing token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **409**: Conflict (business rule violation)
- **422**: Unprocessable Entity (validation error)
- **429**: Too Many Requests (rate limited)
- **500**: Internal Server Error

---

## 🌍 **Environment-Specific Behavior**

### **Development**
- **SMS**: Mock OTP (code: 123456)
- **Database**: Local Supabase or SQLite
- **CORS**: Localhost origins enabled

### **Staging**
- **SMS**: Real Twilio (whitelist enabled)
- **Database**: Supabase staging branch
- **URL**: https://contestlet-git-staging.vercel.app

### **Production**
- **SMS**: Full Twilio integration
- **Database**: Supabase production branch
- **URL**: https://contestlet.vercel.app

---

## 🎯 **Quick Testing**

### **Test Contest Creation (All Fields)**
```bash
curl -X POST "https://contestlet.vercel.app/admin/contests" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Contest",
    "contest_type": "sweepstakes",
    "entry_method": "sms",
    "minimum_age": 21,
    "max_entries_per_person": 5,
    "sms_templates": {
      "entry_confirmation": "You are entered! Good luck!"
    },
    "official_rules": {
      "eligibility_text": "21+ US residents",
      "sponsor_name": "Test Company",
      "start_date": "2025-08-22T10:00:00Z",
      "end_date": "2025-08-25T23:59:59Z",
      "prize_value_usd": 100
    }
  }'
```

### **Test OTP Flow**
```bash
# 1. Request OTP
curl -X POST "https://contestlet.vercel.app/auth/request-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone": "18187958204"}'

# 2. Verify OTP (use code from SMS or 123456 in development)
curl -X POST "https://contestlet.vercel.app/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone": "18187958204", "code": "123456"}'
```

---

**📋 This API reference covers all endpoints with 100% form support and comprehensive SMS integration. All features are production-ready.** ✨