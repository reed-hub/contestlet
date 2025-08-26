# 🔄 Unified User Profile Endpoints

**Status**: ✅ **IMPLEMENTED**  
**Version**: v1.0  
**Date**: August 2025

---

## 📋 **Overview**

The Contestlet API now provides unified user profile endpoints that replace role-specific endpoints, significantly reducing complexity while maintaining full security through Row Level Security (RLS).

### **Before (Deprecated)**
```
GET  /user/profile      - Get user profile
PUT  /user/profile      - Update user profile
GET  /sponsor/profile   - Get sponsor profile  
PUT  /sponsor/profile   - Update sponsor profile
GET  /admin/profile/    - Get admin profile
```

### **After (Unified)**
```
GET  /users/me         - Get own profile (all roles)
PUT  /users/me         - Update own profile (all roles)
```

---

## 🚀 **New Unified Endpoints**

### **GET /users/me**

**Description**: Get current user's profile information  
**Authentication**: Required (JWT token)  
**Method**: `GET`

**Response Format** (varies by role):

**Admin/User Response:**
```json
{
  "id": 1,
  "phone": "+18187958204",
  "role": "admin",
  "is_verified": true,
  "created_at": "2025-08-22T14:56:48.359178",
  "role_assigned_at": "2025-08-24T17:26:09",
  "created_by_user_id": null
}
```

**Sponsor Response:**
```json
{
  "user_id": 2,
  "phone": "+15551234567",
  "role": "sponsor",
  "is_verified": true,
  "created_at": "2025-08-24T21:56:34",
  "role_assigned_at": "2025-08-24T17:33:06.551967",
  "company_profile": {
    "id": 3,
    "user_id": 2,
    "company_name": "Test Company",
    "website_url": "https://testcompany.com",
    "industry": "Technology",
    "description": "Company description",
    "is_verified": false,
    "created_at": "2025-08-24T17:33:06.555411",
    "updated_at": "2025-08-26T22:04:05.706561"
  }
}
```

---

### **PUT /users/me**

**Description**: Update current user's profile information  
**Authentication**: Required (JWT token)  
**Method**: `PUT`  
**Content-Type**: `application/json`

**Request Body** (for sponsors):
```json
{
  "company_name": "Updated Company Name",
  "website_url": "https://newwebsite.com",
  "contact_name": "John Doe",
  "contact_email": "john@company.com",
  "contact_phone": "+1234567890",
  "industry": "Technology",
  "description": "Updated company description"
}
```

**Response**: Same format as GET /users/me

**Notes**:
- Admin/User roles: Limited updates (future expansion planned)
- Sponsor role: Full company profile updates supported
- Only updates provided fields (partial updates supported)

---

## 🔒 **Security**

### **Row Level Security (RLS)**
- Users can only access their own profile data
- Database-level security enforcement
- No additional endpoint-level security needed
- Role-based permissions maintained

### **Authentication**
- JWT token required for all operations
- Token must contain valid user ID and role
- Automatic user identification from token

---

## 💻 **Frontend Integration**

### **JavaScript/TypeScript Example**

```typescript
// Get current user profile
const getUserProfile = async () => {
  const response = await fetch('/users/me', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Update sponsor profile
const updateProfile = async (updates) => {
  const response = await fetch('/users/me', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  });
  return response.json();
};
```

### **React Hook Example**

```typescript
const useUserProfile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = async () => {
    try {
      const data = await getUserProfile();
      setProfile(data);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (updates) => {
    const updated = await updateProfile(updates);
    setProfile(updated);
    return updated;
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  return { profile, loading, updateProfile, refetch: fetchProfile };
};
```

---

## 🔄 **Migration Guide**

### **Step 1: Update API Calls**

**Before:**
```typescript
// Role-specific endpoints
const getProfile = async (role) => {
  const endpoint = role === 'sponsor' ? '/sponsor/profile' : '/user/profile';
  return fetch(endpoint, { headers: { Authorization: `Bearer ${token}` }});
};
```

**After:**
```typescript
// Single unified endpoint
const getProfile = async () => {
  return fetch('/users/me', { 
    headers: { Authorization: `Bearer ${token}` }
  });
};
```

### **Step 2: Remove Role Detection Logic**

**Before:**
```typescript
// Complex role-based logic
const updateProfile = async (data, userRole) => {
  let endpoint;
  switch(userRole) {
    case 'sponsor': endpoint = '/sponsor/profile'; break;
    case 'admin': endpoint = '/admin/profile/'; break;
    default: endpoint = '/user/profile';
  }
  return fetch(endpoint, { method: 'PUT', body: JSON.stringify(data) });
};
```

**After:**
```typescript
// Simple unified logic
const updateProfile = async (data) => {
  return fetch('/users/me', { 
    method: 'PUT', 
    body: JSON.stringify(data) 
  });
};
```

### **Step 3: Handle Response Formats**

```typescript
const handleProfileResponse = (profile) => {
  // Check if sponsor (has company_profile)
  if (profile.company_profile) {
    // Handle sponsor profile
    return {
      userId: profile.user_id,
      role: profile.role,
      company: profile.company_profile
    };
  } else {
    // Handle admin/user profile
    return {
      userId: profile.id,
      role: profile.role,
      phone: profile.phone
    };
  }
};
```

---

## 📊 **Benefits Achieved**

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Endpoints** | 5 endpoints | 2 endpoints | 60% reduction |
| **Frontend Logic** | Role detection required | No role logic needed | Simplified |
| **Maintenance** | 3x code paths | Single code path | 67% less maintenance |
| **Testing** | 5 test scenarios | 2 test scenarios | 60% less testing |
| **Documentation** | Multiple endpoint docs | Single endpoint docs | Simplified |

---

## 🔄 **Backward Compatibility**

### **Deprecated Endpoints**
The following endpoints are **deprecated** but still functional:

- `GET /user/profile` → Use `GET /users/me`
- `PUT /user/profile` → Use `PUT /users/me`
- `GET /sponsor/profile` → Use `GET /users/me`
- `PUT /sponsor/profile` → Use `PUT /users/me`
- `GET /admin/profile/` → Use `GET /users/me`

### **Migration Timeline**
- **Phase 1**: New endpoints available (✅ Complete)
- **Phase 2**: Frontend migration (In Progress)
- **Phase 3**: Deprecation warnings (✅ Complete)
- **Phase 4**: Remove old endpoints (Future)

---

## 🧪 **Testing**

### **Manual Testing**

```bash
# Test with admin token
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/users/me

# Test with sponsor token  
curl -H "Authorization: Bearer $SPONSOR_TOKEN" http://localhost:8000/users/me

# Test sponsor profile update
curl -X PUT -H "Authorization: Bearer $SPONSOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "New Company Name"}' \
  http://localhost:8000/users/me
```

### **Expected Results**
- ✅ Admin users get basic profile format
- ✅ Sponsor users get unified profile with company data
- ✅ Profile updates work correctly for sponsors
- ✅ Non-sponsor updates return basic profile
- ✅ Proper error handling for invalid tokens

---

## 🎯 **Next Steps**

### **Future Enhancements**
1. **Extended User Profiles**: Add name, email, preferences for admin/user roles
2. **Profile Validation**: Enhanced validation rules for different roles
3. **Profile Images**: Support for user avatar uploads
4. **Audit Trail**: Track profile changes for compliance

### **Frontend Recommendations**
1. **Migrate Gradually**: Update one component at a time
2. **Test Thoroughly**: Verify all user roles work correctly
3. **Update Documentation**: Update frontend API client documentation
4. **Remove Old Code**: Clean up deprecated endpoint usage

---

**🎉 The unified user profile endpoints are now live and ready for use!**

**Status**: 🟢 **PRODUCTION READY**  
**Migration**: 🔄 **BACKWARD COMPATIBLE**  
**Benefits**: 📈 **SIGNIFICANT COMPLEXITY REDUCTION**
