# 🎯 Manual Entry API Documentation

## Overview
The Manual Entry API allows administrators to create contest entries for users who participated through offline channels (phone calls, events, paper forms, etc.).

## Authentication
All manual entry endpoints require admin authentication with JWT tokens containing `admin` or `sponsor` roles.

---

## 📋 **Endpoints**

### **1. Primary Endpoint (Recommended)**
```
POST /contests/{contest_id}/enter
```

**Description:** Enhanced contest entry endpoint that supports both regular user entries and admin manual entries.

#### **Regular User Entry (No Request Body)**
```bash
curl -X POST "http://localhost:8000/contests/1/enter" \
  -H "Authorization: Bearer {user_jwt_token}" \
  -H "Content-Type: application/json"
```

#### **Admin Manual Entry (With Request Body)**
```bash
curl -X POST "http://localhost:8000/contests/1/enter" \
  -H "Authorization: Bearer {admin_jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "admin_override": true,
    "source": "phone_call",
    "notes": "Customer called in to enter contest"
  }'
```

### **2. Dedicated Admin Endpoint**
```
POST /admin/contests/{contest_id}/manual-entry
```

**Description:** Dedicated admin endpoint for manual entry creation.

```bash
curl -X POST "http://localhost:8000/admin/contests/1/manual-entry" \
  -H "Authorization: Bearer {admin_jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "admin_override": true,
    "source": "event",
    "notes": "Entry collected at trade show booth"
  }'
```

---

## 📝 **Request Schema**

### **ManualEntryRequest**
```json
{
  "phone_number": "+1234567890",
  "admin_override": true,
  "source": "manual_admin",
  "notes": "Optional admin notes"
}
```

#### **Field Specifications**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | string | ✅ | Phone number in E.164 format (+1234567890) |
| `admin_override` | boolean | ✅ | Must be `true` for manual entries |
| `source` | string | ❌ | Entry source tracking (default: "manual_admin") |
| `notes` | string | ❌ | Admin notes (max 500 characters) |

#### **Valid Source Values**
- `manual_admin` (default)
- `phone_call`
- `event`
- `paper_form`
- `customer_service`
- `migration`
- `promotional`

---

## 📤 **Response Schemas**

### **Success Response (201 Created)**
```json
{
  "success": true,
  "message": "Manual entry created successfully",
  "contest_id": 1,
  "entry_id": 123,
  "user_id": 456,
  "entered_at": "2024-01-15T10:30:00Z"
}
```

### **Manual Entry Details Response**
```json
{
  "entry_id": 123,
  "contest_id": 1,
  "phone_number": "+1234567890",
  "created_at": "2024-01-15T10:30:00Z",
  "created_by_admin_id": 789,
  "source": "phone_call",
  "status": "active",
  "notes": "Customer called in to enter contest"
}
```

---

## ❌ **Error Responses**

### **400 Bad Request - Invalid Phone Number**
```json
{
  "success": false,
  "message": "Phone number must be in E.164 format (e.g., +1234567890)",
  "error_code": "INVALID_PHONE_NUMBER"
}
```

### **401 Unauthorized**
```json
{
  "success": false,
  "message": "Authentication required for manual entry creation",
  "error_code": "UNAUTHORIZED"
}
```

### **403 Forbidden**
```json
{
  "success": false,
  "message": "Admin privileges required for manual entry creation",
  "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

### **404 Not Found**
```json
{
  "success": false,
  "message": "Contest not found",
  "error_code": "CONTEST_NOT_FOUND"
}
```

### **409 Conflict - Duplicate Entry**
```json
{
  "success": false,
  "message": "Phone number +1234567890 has already entered this contest",
  "error_code": "DUPLICATE_ENTRY",
  "details": {
    "contest_id": 1,
    "phone_number": "+1234567890",
    "existing_entry_id": 456,
    "entry_source": "web_app"
  }
}
```

### **400 Bad Request - Entry Limit Exceeded**
```json
{
  "success": false,
  "message": "Contest has reached maximum entry limit of 1000",
  "error_code": "ENTRY_LIMIT_EXCEEDED",
  "details": {
    "limit": 1000,
    "current": 1000
  }
}
```

### **400 Bad Request - Contest Closed**
```json
{
  "success": false,
  "message": "Contest is not accepting entries (status: complete)",
  "error_code": "CONTEST_CLOSED"
}
```

---

## 🔒 **Security & Validation**

### **Authentication Requirements**
- Valid JWT token with `admin` or `sponsor` role
- Token must not be expired
- Admin must have contest management permissions

### **Phone Number Validation**
- Must be in E.164 format: `+[country_code][number]`
- Examples: `+1234567890`, `+447700900123`
- Automatically cleaned of spaces, dashes, parentheses

### **Contest Status Validation**
Manual entries are allowed for contests with these statuses:
- ✅ `active` - Currently accepting entries
- ✅ `upcoming` - Scheduled to start soon
- ✅ `ended` - Ended but no winner selected yet
- ❌ `draft` - Still being created
- ❌ `awaiting_approval` - Pending admin approval
- ❌ `rejected` - Rejected by admin
- ❌ `complete` - Winner already selected
- ❌ `cancelled` - Contest cancelled

### **Rate Limiting**
- Max 10 manual entries per admin per minute
- Max 100 manual entries per contest per day
- Rate limits enforced per admin user ID

---

## 🧪 **Testing Examples**

### **Test 1: Valid Manual Entry**
```bash
# Create manual entry for phone call participant
curl -X POST "http://localhost:8000/contests/1/enter" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1555123456",
    "admin_override": true,
    "source": "phone_call",
    "notes": "Customer called support line to enter"
  }'

# Expected: 201 Created with entry details
```

### **Test 2: Duplicate Entry (Should Fail)**
```bash
# Try to create entry for same phone number again
curl -X POST "http://localhost:8000/contests/1/enter" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1555123456",
    "admin_override": true,
    "source": "event"
  }'

# Expected: 409 Conflict - duplicate entry error
```

### **Test 3: Invalid Phone Format (Should Fail)**
```bash
# Try invalid phone number format
curl -X POST "http://localhost:8000/contests/1/enter" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "123-456-7890",
    "admin_override": true
  }'

# Expected: 400 Bad Request - invalid phone format
```

### **Test 4: Non-Admin User (Should Fail)**
```bash
# Try with regular user token
curl -X POST "http://localhost:8000/contests/1/enter" \
  -H "Authorization: Bearer {regular_user_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1555999888",
    "admin_override": true
  }'

# Expected: 403 Forbidden - insufficient permissions
```

---

## 📊 **Database Schema**

### **Updated Entry Model**
```sql
CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    contest_id INTEGER NOT NULL REFERENCES contests(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    selected BOOLEAN DEFAULT FALSE,
    status VARCHAR DEFAULT 'active',
    
    -- Manual Entry Fields
    source VARCHAR(50) DEFAULT 'web_app' NOT NULL,
    created_by_admin_id INTEGER REFERENCES users(id),
    admin_notes TEXT,
    
    -- Indexes
    INDEX idx_entries_source (source),
    INDEX idx_entries_admin (created_by_admin_id),
    INDEX idx_entries_source_admin (source, created_by_admin_id)
);
```

### **Entry Sources**
| Source | Description |
|--------|-------------|
| `web_app` | Regular web application entries (default) |
| `manual_admin` | Admin-created manual entries |
| `phone_call` | Entries from customer service calls |
| `event` | Entries collected at events/trade shows |
| `paper_form` | Entries from paper forms |
| `customer_service` | Customer service representative entries |
| `migration` | Imported from external systems |
| `promotional` | Special promotional entries |

---

## 🚀 **Frontend Integration Guide**

### **JavaScript Example**
```javascript
// Manual entry creation function
async function createManualEntry(contestId, phoneNumber, source, notes) {
  try {
    const response = await fetch(`/contests/${contestId}/enter`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${adminToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        phone_number: phoneNumber,
        admin_override: true,
        source: source || 'manual_admin',
        notes: notes
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to create manual entry');
    }

    const result = await response.json();
    console.log('Manual entry created:', result);
    return result;
    
  } catch (error) {
    console.error('Manual entry error:', error);
    throw error;
  }
}

// Usage
createManualEntry(1, '+1234567890', 'phone_call', 'Customer called in')
  .then(result => {
    alert('Entry created successfully!');
    refreshEntriesList();
  })
  .catch(error => {
    alert(`Error: ${error.message}`);
  });
```

### **Error Handling**
```javascript
function handleManualEntryError(error) {
  const errorCode = error.error_code;
  
  switch (errorCode) {
    case 'DUPLICATE_ENTRY':
      return 'This phone number has already entered the contest.';
    case 'INVALID_PHONE_NUMBER':
      return 'Please enter a valid phone number (e.g., +1234567890).';
    case 'CONTEST_CLOSED':
      return 'This contest is no longer accepting entries.';
    case 'ENTRY_LIMIT_EXCEEDED':
      return 'Contest has reached its maximum entry limit.';
    case 'INSUFFICIENT_PERMISSIONS':
      return 'Admin privileges required for manual entries.';
    default:
      return error.message || 'An unexpected error occurred.';
  }
}
```

---

## ✅ **Implementation Status**

### **Completed Features**
- ✅ Manual entry schema validation
- ✅ Phone number E.164 format validation
- ✅ Admin authentication and authorization
- ✅ Duplicate entry prevention
- ✅ Contest status validation
- ✅ Entry limit enforcement
- ✅ User auto-creation for new phone numbers
- ✅ Comprehensive error handling
- ✅ Database schema updates
- ✅ Two endpoint options (primary + dedicated)
- ✅ Source tracking and admin notes
- ✅ API documentation

### **Ready for Frontend Integration**
The manual entry API is fully implemented and ready for frontend integration. Use the examples above to integrate with your admin interface.

### **Next Steps for Frontend**
1. Update admin interface to include manual entry form
2. Implement phone number validation on frontend
3. Add error handling with user-friendly messages
4. Test with various scenarios (duplicates, limits, etc.)
5. Add manual entry indicators in entries list
