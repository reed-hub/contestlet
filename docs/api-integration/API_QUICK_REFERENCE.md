# 📋 Contestlet API - Quick Reference

## 🔗 Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

## 🔐 Authentication

### Request OTP
```bash
POST /auth/request-otp
Content-Type: application/json

{
  "phone": "5551234567"
}
```

### Verify OTP
```bash
POST /auth/verify-otp
Content-Type: application/json

{
  "phone": "5551234567",
  "code": "123456"
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

## 🔑 Admin Token
```
Authorization: Bearer contestlet-admin-super-secret-token-change-in-production
```

## 📱 Phone Format
- US numbers: `5551234567` or `15551234567`
- International: `+15551234567`

## 📍 Geolocation
- Latitude: -90 to 90
- Longitude: -180 to 180
- Radius: 0.1 to 100 miles

## ⏱️ Rate Limits
- OTP requests: 5 per 5 minutes per phone number
- General API: No specific limits (reasonable use)

## 🧪 Development
- Mock SMS codes appear in server console
- Database auto-creates on first run
- Interactive docs: `/docs`
