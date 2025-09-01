# 🛠️ **Profile Update Troubleshooting Guide**

**Last Updated**: August 30, 2025  
**Status**: ✅ **All Issues Resolved**  

---

## 📋 **Common Issues & Solutions**

### **✅ RESOLVED: PUT /users/me 500 Internal Server Error**

**Issue**: Profile update endpoint failing with 500 error  
**Root Cause**: Invalid `admin_profile` relationship reference in user service  
**Status**: ✅ **FIXED** (August 30, 2025)  

#### **Symptoms**
- PUT /users/me returns 500 Internal Server Error
- CORS policy violations due to server errors
- AttributeError in server logs: `User has no attribute 'admin_profile'`

#### **Solution Applied**
```python
# Fixed in app/core/services/user_service.py
# BEFORE (Broken)
user = self.db.query(User).options(
    joinedload(User.sponsor_profile),
    joinedload(User.admin_profile)  # ❌ Non-existent relationship
).filter(User.id == user_id).first()

# AFTER (Fixed)
user = self.db.query(User).options(
    joinedload(User.sponsor_profile)  # ✅ Only valid relationships
).filter(User.id == user_id).first()
```

#### **Verification**
```bash
# Test the endpoint
curl -X PUT http://localhost:8000/users/me \
  -H "Authorization: Bearer <valid_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Test User", "email": "test@example.com"}'

# Expected: 200 OK with updated profile data
```

---

## 🔧 **Current Working Configuration**

### **✅ Endpoint Status**
- **PUT /users/me**: ✅ Fully operational
- **GET /users/me**: ✅ Working correctly
- **GET /auth/me**: ✅ Working correctly
- **CORS Headers**: ✅ Properly configured

### **✅ Supported Profile Fields**
```json
{
  "full_name": "string",     // All user roles
  "email": "string",         // All user roles  
  "bio": "string",           // All user roles
  "company_name": "string",  // Sponsor role only
  "website_url": "string",   // Sponsor role only
  "industry": "string"       // Sponsor role only
}
```

### **✅ Response Format**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "phone": "+18187958204",
    "role": "admin",
    "is_verified": true,
    "created_at": "2025-08-29T21:58:05.147569",
    "updated_at": "2025-08-30T19:42:03.946855",
    "full_name": "Updated Name",
    "email": "updated@email.com",
    "bio": "Updated bio"
  },
  "message": "Profile updated successfully",
  "timestamp": "2025-08-30T19:42:03.948812"
}
```

---

## 🌐 **CORS Configuration**

### **✅ Working CORS Settings**
```python
# In app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "Accept", "Accept-Language", "Content-Language",
        "Content-Type", "Authorization", "X-Requested-With",
        "Origin", "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ]
)
```

### **✅ CORS Verification**
```bash
# Test CORS preflight
curl -X OPTIONS http://localhost:8000/users/me \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: PUT" \
  -H "Access-Control-Request-Headers: Authorization, Content-Type"

# Expected headers:
# access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS
# access-control-allow-origin: http://localhost:3000
# access-control-allow-credentials: true
```

---

## 🔍 **Debugging Steps**

### **1. Check Server Status**
```bash
curl -s http://localhost:8000/health
# Expected: {"status":"healthy","environment":"development"}
```

### **2. Verify Authentication**
```bash
# Get JWT token
curl -X POST http://localhost:8000/auth/verify-phone \
  -H "Content-Type: application/json" \
  -d '{"phone": "+18187958204"}'

# Test auth endpoint
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <token>"
```

### **3. Test Profile Update**
```bash
# Basic profile update
curl -X PUT http://localhost:8000/users/me \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Test Name"}'
```

### **4. Check Server Logs**
```bash
# Look for errors in server output
# Should NOT see: AttributeError: 'User' has no attribute 'admin_profile'
# Should see: INFO: 127.0.0.1:xxxxx - "PUT /users/me HTTP/1.1" 200 OK
```

---

## ⚠️ **Known Limitations**

### **AdminProfile Relationship**
- The `AdminProfile` model exists but uses string-based user ID mapping
- No direct SQLAlchemy relationship between User and AdminProfile
- Admin preferences stored separately from user profile data

### **Role-Specific Fields**
- Company fields (company_name, website_url, etc.) only available for sponsor role
- Admin-specific fields handled through separate AdminProfile model
- Basic profile fields (full_name, email, bio) available for all roles

---

## 📞 **Support Information**

### **If Issues Persist**
1. **Check server logs** for specific error messages
2. **Verify JWT token** is valid and not expired
3. **Test with curl** to isolate frontend vs backend issues
4. **Check CORS headers** in browser developer tools

### **Contact Information**
- **Backend Team**: For server-side issues
- **Frontend Team**: For client-side integration issues
- **DevOps Team**: For CORS and deployment issues

---

**Last Verified**: August 30, 2025  
**Next Review**: As needed based on issues reported
