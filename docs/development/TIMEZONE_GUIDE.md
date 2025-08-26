# 🌍 Contestlet Timezone Guide

## Overview

Contestlet uses a comprehensive timezone system to ensure contest times are accurate across different timezones. This guide explains how timezone handling works for admins, developers, and end users.

## 🎯 Core Principles

### 1. **UTC Storage, Local Display**
- **All times stored in database**: UTC (Coordinated Universal Time) ✅ CONFIRMED
- **Admin interface**: Displays and accepts times in admin's preferred timezone
- **Public API**: Returns UTC times with timezone metadata
- **Automatic conversion**: System handles all timezone conversions
- **SQLite handling**: All models use timezone-aware UTC defaults for consistent storage

### 2. **Admin Timezone Preferences**
- Each admin can set their preferred timezone
- Times in admin interface are displayed in this timezone
- Contest creation times are entered in admin's timezone
- System automatically converts to UTC for storage

### 3. **Timezone Metadata**
- Every contest records the timezone it was created in
- Admin user ID tracked for audit trail
- Full timezone context preserved for compliance

## 🔧 How It Works

### **For Admins**

#### **Step 1: Set Your Timezone**
```
1. Go to Admin Profile (/admin/profile)
2. Select your timezone from the dropdown
3. Choose auto-detect or manual preference
4. Save preferences
```

#### **Step 2: Create Contests**
```
1. Enter contest times in YOUR timezone
2. System shows "Times will be entered in: Eastern Time (ET)"
3. You enter: "2024-01-15 14:30" (2:30 PM your time)
4. System stores: "2024-01-15 19:30:00 UTC" (automatically converted)
```

#### **Step 3: View Contests**
```
1. Contest times displayed in YOUR preferred timezone
2. Status calculations use YOUR timezone for context
3. Countdown timers show accurate local time
```

### **For Developers**

#### **Frontend Integration**
```javascript
// 1. Get admin timezone preferences
const preferences = await contestlet.admin.getTimezonePreferences();

// 2. Get supported timezones
const timezones = await contestlet.admin.getTimezones();

// 3. Set timezone preferences
await contestlet.admin.setTimezone('America/New_York', false);

// 4. Convert times for display
const localTime = convertUTCToTimezone(utcTime, preferences.timezone);
```

#### **API Behavior**
```javascript
// Admin creates contest at 2:30 PM Eastern Time
POST /admin/contests
{
  "start_time": "2024-01-15T19:30:00Z",  // UTC (converted by frontend)
  "end_time": "2024-01-16T19:30:00Z"     // UTC (converted by frontend)
}

// Backend response includes timezone metadata
{
  "id": 1,
  "start_time": "2024-01-15T19:30:00Z",     // UTC for storage
  "end_time": "2024-01-16T19:30:00Z",       // UTC for storage  
  "created_timezone": "America/New_York",    // Admin's timezone
  "admin_user_id": "admin_123"               // Who created it
}
```

## 🌎 Supported Timezones

### **United States**
- `America/New_York` - Eastern Time (ET)
- `America/Chicago` - Central Time (CT)  
- `America/Denver` - Mountain Time (MT)
- `America/Los_Angeles` - Pacific Time (PT)
- `America/Phoenix` - Arizona Time (MST)
- `America/Anchorage` - Alaska Time (AKT)
- `Pacific/Honolulu` - Hawaii Time (HST)

### **Canada**
- `Canada/Eastern` - Eastern Time (Canada)
- `Canada/Central` - Central Time (Canada)
- `Canada/Mountain` - Mountain Time (Canada)
- `Canada/Pacific` - Pacific Time (Canada)

### **International**
- `UTC` - Coordinated Universal Time
- `Europe/London` - Greenwich Mean Time (GMT)
- `Europe/Paris` - Central European Time (CET)
- `Europe/Berlin` - Central European Time (CET)
- `Asia/Tokyo` - Japan Standard Time (JST)
- `Asia/Shanghai` - China Standard Time (CST)
- `Australia/Sydney` - Australian Eastern Time (AET)

## 📊 API Endpoints

### **Timezone Management**

#### **Get Supported Timezones**
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
    }
  ],
  "default_timezone": "UTC"
}
```

#### **Set Admin Timezone Preferences**
```bash
POST /admin/profile/timezone
Authorization: Bearer {admin_jwt}

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

#### **Get Admin Timezone Preferences**
```bash
GET /admin/profile/timezone
Authorization: Bearer {admin_jwt}

# Response: Same as POST response above
```

## ⚠️ Important Notes

### **For Contest Creation**
1. **Always enter times in your preferred timezone**
2. **System automatically converts to UTC for storage**
3. **Times display in your timezone in admin interface**
4. **Public users see UTC times or their local timezone**

### **For Development**
1. **Frontend must handle timezone conversion to UTC**
2. **Use timezone utilities for consistent conversion**
3. **Always validate timezone identifiers**
4. **Handle daylight saving time transitions**

### **For Database Queries**
1. **All stored times are UTC**
2. **Use timezone-aware comparisons**
3. **Convert display times based on admin preferences**
4. **Preserve timezone metadata for audit trail**

## 🧪 Testing Examples

### **Example 1: Admin in New York Creates Contest**
```
Admin timezone: America/New_York (EST, UTC-5)
Admin enters: "January 15, 2024 at 2:30 PM"
Stored in DB: "2024-01-15 19:30:00 UTC"
Displayed to admin: "January 15, 2024 at 2:30 PM EST"
```

### **Example 2: Admin in Los Angeles Views Same Contest**  
```
Admin timezone: America/Los_Angeles (PST, UTC-8)
Stored in DB: "2024-01-15 19:30:00 UTC"
Displayed to admin: "January 15, 2024 at 11:30 AM PST"
```

### **Example 3: Public User in London Views Contest**
```
User timezone: Europe/London (GMT, UTC+0)
Stored in DB: "2024-01-15 19:30:00 UTC"  
Displayed to user: "January 15, 2024 at 7:30 PM GMT"
```

## 🚨 Common Pitfalls to Avoid

### **1. Mixing Timezone-Naive and Timezone-Aware Datetimes**
```python
# ❌ Wrong
contest_time = "2024-01-15 14:30:00"  # Ambiguous timezone

# ✅ Correct  
contest_time = "2024-01-15T19:30:00Z"  # Clear UTC time
```

### **2. Not Converting Frontend Input**
```javascript
// ❌ Wrong - sending local time as if it's UTC
const payload = {
  start_time: "2024-01-15T14:30:00"  // Local time, not UTC
};

// ✅ Correct - convert to UTC first
const payload = {
  start_time: datetimeLocalToUTC("2024-01-15T14:30:00", adminTimezone)
};
```

### **3. Ignoring Daylight Saving Time**
```javascript
// ❌ Wrong - manual offset calculation
const utcTime = localTime + (5 * 60 * 60 * 1000);  // Breaks during DST

// ✅ Correct - use timezone libraries
const utcTime = moment.tz(localTime, adminTimezone).utc();
```

## 🔄 Migration Guide

### **Existing Contests**
- Contests created before timezone implementation are treated as UTC
- `created_timezone` field will be `null` for legacy contests
- Display logic handles null timezone gracefully

### **Admin Preferences**
- New admins get UTC timezone by default with auto-detect enabled
- Existing admins can set preferences at any time
- System works without preferences (defaults to UTC)

## 🎯 Best Practices

### **For Frontend Developers**
1. **Always validate timezone identifiers** before sending to API
2. **Use moment.js or date-fns with timezone support** for conversions
3. **Cache admin timezone preferences** to avoid repeated API calls
4. **Show timezone context** to users when entering times
5. **Handle timezone conversion errors** gracefully

### **For Admin Users**
1. **Set your timezone preference** before creating contests  
2. **Verify contest times** after creation in multiple timezones if needed
3. **Be aware of daylight saving time** transitions
4. **Use clear timezone indicators** when communicating contest times

### **For API Integration**
1. **Send all times as UTC** to the backend
2. **Include timezone metadata** in responses
3. **Validate timezone fields** on both frontend and backend
4. **Use consistent datetime formatting** (ISO 8601)

## 📞 Support

If you encounter timezone-related issues:

1. **Check admin timezone preferences** in `/admin/profile`
2. **Verify contest timezone metadata** in contest details
3. **Test with different timezones** to ensure consistency
4. **Review browser timezone detection** for auto-detect issues

The timezone system is designed to be robust and handle edge cases, but proper frontend implementation is crucial for the best user experience.
