# 🔗 Frontend-Backend Integration Testing Guide

## 🚀 **Quick Start Testing**

### **1. Backend Server Status**
✅ Backend is running on `http://localhost:8000`
✅ Role system fully implemented
✅ Database schema migrated
✅ All API endpoints working

### **2. Test Authentication Flow**

#### **Admin User Test**
```bash
# Request OTP (optional in dev mode)
curl -X POST http://localhost:8000/auth/request-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "+18187958204"}'

# Verify OTP and get JWT with role
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "+18187958204", "code": "123456"}'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Phone verified successfully",
  "access_token": "eyJ...", // JWT with role: "admin"
  "token_type": "bearer",
  "user_id": 1
}
```

#### **Regular User Test**
```bash
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "+15551234567", "code": "123456"}'
```

### **3. Test Role-Based Endpoints**

#### **User Profile (Any Role)**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/user/profile
```

#### **Sponsor Analytics (Sponsor/Admin Only)**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/sponsor/analytics
```

#### **Admin Contests (Admin Only)**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/admin/contests
```

### **4. Test Role Upgrade**

#### **User → Sponsor Upgrade**
```bash
curl -X POST http://localhost:8000/sponsor/upgrade-request \
  -H "Authorization: Bearer USER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_role": "sponsor",
    "company_name": "Test Company",
    "website_url": "https://testcompany.com",
    "industry": "Technology",
    "description": "Test company description"
  }'
```

## 🎯 **Frontend Integration Points**

### **1. JWT Token Structure**
Your frontend JWT decoder should expect:
```json
{
  "sub": "1",                    // User ID
  "phone": "+18187958204",       // Phone number
  "role": "admin",               // User role (admin/sponsor/user)
  "exp": 1756144335              // Expiration
}
```

### **2. API Client Configuration**
```typescript
// In your apiClient.ts
const BASE_URL = 'http://localhost:8000';

// All endpoints are available:
// - /auth/verify-otp
// - /user/*
// - /sponsor/*
// - /admin/*
```

### **3. Error Handling**
The backend returns proper HTTP status codes:
- `401` - Authentication required
- `403` - Insufficient permissions (wrong role)
- `404` - Resource not found
- `422` - Validation error
- `500` - Server error

### **4. CORS Configuration**
✅ CORS is configured for `http://localhost:3000`
✅ All HTTP methods allowed
✅ Authorization headers supported

## 🧪 **Testing Scenarios**

### **Scenario 1: Admin User Flow**
1. Login with `+18187958204`
2. Should get `role: "admin"` in JWT
3. Can access all endpoints (`/user/*`, `/sponsor/*`, `/admin/*`)
4. Can view all contests and users

### **Scenario 2: Regular User Flow**
1. Login with `+15551234567`
2. Should get `role: "user"` in JWT
3. Can access `/user/*` endpoints only
4. Gets `403` on `/admin/*` and `/sponsor/*`
5. Can request sponsor upgrade

### **Scenario 3: Sponsor User Flow**
1. Login with `+15559876543`
2. Should get `role: "sponsor"` in JWT
3. Can access `/user/*` and `/sponsor/*` endpoints
4. Gets `403` on `/admin/*` endpoints
5. Can manage own contests and profile

## 🔧 **Troubleshooting**

### **Common Issues**

#### **401 Unauthorized**
- Check JWT token is included in Authorization header
- Verify token format: `Bearer YOUR_JWT_TOKEN`
- Check token hasn't expired

#### **403 Forbidden**
- User role doesn't have permission for endpoint
- Admin endpoints require `role: "admin"`
- Sponsor endpoints require `role: "sponsor"` or `role: "admin"`

#### **CORS Errors**
- Ensure frontend is running on `http://localhost:3000`
- Backend CORS is configured for this origin

#### **Phone Number Issues**
- Use test numbers: `+18187958204`, `+15551234567`, `+15559876543`
- Backend validates phone numbers in development mode

## ✅ **Integration Checklist**

### **Backend Ready**
- [x] Server running on port 8000
- [x] Database schema migrated
- [x] Role system implemented
- [x] All API endpoints working
- [x] JWT authentication working
- [x] CORS configured
- [x] Test data available

### **Frontend Tasks**
- [ ] Update API base URL to `http://localhost:8000`
- [ ] Test authentication flow with real backend
- [ ] Verify JWT token decoding with roles
- [ ] Test role-based route protection
- [ ] Test role upgrade workflow
- [ ] Validate error handling
- [ ] Test all user scenarios

## 🎉 **Ready for Full Integration!**

The backend is **completely ready** for your frontend integration. All the endpoints you've implemented in your API client are working and tested.

**Next Steps:**
1. Point your frontend to `http://localhost:8000`
2. Test with the provided phone numbers
3. Verify JWT role extraction
4. Test all role-based flows

**The multi-tier role system is ready for production! 🚀**
