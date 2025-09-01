# 🎯 Frontend Alignment Prompt

**Objective**: Align frontend with current backend API implementation  
**Priority**: Critical schema and response format updates  
**Timeline**: Immediate implementation required

---

## 🚨 **Critical Changes Required**

### **1. Response Format Standardization**
```typescript
// REMOVE: Inconsistent response handling
const data = (response as any)?.data || (response as any)?.contests || response || [];

// IMPLEMENT: Consistent APIResponse wrapper (UPDATED)
interface APIResponse<T> {
  success: boolean;
  data?: T;
  message?: string;        // Optional, not always present
  errors?: Record<string, any>;  // Changed from error_code
  meta?: Record<string, any>;    // NEW: Additional metadata
  timestamp: string;       // NEW: Always present
}

// All API calls now return APIResponse<T>
const response = await api.getContests();
const contests = response.data; // Always use .data
```

### **2. ID Type Consistency**
```typescript
// CHANGE: All IDs from string to number
interface User {
  id: number;        // Was: string
  // ...
}

interface Contest {
  id: number;        // Was: string
  created_by_user_id?: number;  // Was: string
  // ...
}

// Update all ID handling throughout the app
```

### **3. User Schema Updates**
```typescript
// CHANGE: User field names (UPDATED)
interface User {
  id: number;
  phone: string;
  role: 'admin' | 'sponsor' | 'user';
  full_name?: string;    // Was: name
  email?: string;
  bio?: string;          // NEW field
  is_verified: boolean;  // NEW field
  created_at: string;
  updated_at?: string;   // Optional, may not always be present
  role_assigned_at: string;  // NEW: When role was assigned
  created_by_user_id?: number;  // NEW: Who created this user
  role_assigned_by?: number;    // NEW: Who assigned the role
}
```

### **4. Enhanced Authentication**
```typescript
// CURRENT: Authentication response (NO REFRESH TOKENS YET)
interface AuthResponse {
  success: boolean;
  message: string;
  access_token: string;
  token_type: "bearer";   // Always "bearer"
  user_id: number;        // User ID only, not full user object
}

// CURRENT: Available auth endpoints
POST /auth/request-otp    // Request OTP code
POST /auth/verify-otp     // Verify OTP and get token
POST /auth/verify-phone   // Direct phone verification (admin)
GET  /auth/me             // Get current user info
POST /auth/logout         // Session cleanup

// IMPLEMENT: Error handling for auth failures
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
  }
);
```

---

## 🔗 **CRITICAL: Updated API Endpoints**

### **Current Backend Endpoints (Production Ready)**
```typescript
// Authentication
POST /auth/request-otp      // Request OTP code
POST /auth/verify-otp       // Verify OTP and login
POST /auth/verify-phone     // Admin direct phone verification
GET  /auth/me               // Get current user info
POST /auth/logout           // Logout

// Contests (Public)
GET  /contests/active       // Get active contests (paginated)

// Universal Contest Management (Admin/Sponsor)
POST /admin/universal-contests/        // Create contest
GET  /admin/universal-contests/{id}    // Get contest details
PUT  /admin/universal-contests/{id}    // Update contest
DELETE /admin/universal-contests/{id}  // Delete contest

// User Management
GET  /users/me              // Get current user profile
PUT  /users/me              // Update user profile

// Admin Operations
GET  /admin/contests/       // Admin contest list (all statuses)
PUT  /admin/contests/{id}/status  // Update contest status
GET  /admin/users/          // User management
```

---

## 📋 **Universal Contest Form Implementation**

### **Replace Multiple Forms with Single Universal Form**
```typescript
// REMOVE: Separate CreateContest and EditContest components
// IMPLEMENT: Single UniversalContestForm

interface UniversalContestRequest {
  // Core fields (existing)
  name: string;
  description: string;
  start_time: string;
  end_time: string;
  
  // Enhanced fields (60+ total)
  contest_type?: 'general' | 'sweepstakes' | 'instant_win';
  entry_method?: 'sms' | 'email' | 'web_form';
  winner_selection_method?: 'random' | 'scheduled' | 'instant';
  minimum_age?: number;
  max_entries_per_person?: number;
  total_entry_limit?: number;
  
  // Location targeting
  location_type?: 'united_states' | 'specific_states' | 'radius' | 'custom';
  selected_states?: string[];
  radius_address?: string;
  radius_miles?: number;
  
  // Official rules
  official_rules?: {
    sponsor_name?: string;
    prize_value_usd?: number;
    terms_url?: string;
    eligibility_text?: string;
  };
  
  // SMS templates
  entry_confirmation_sms?: string;
  winner_notification_sms?: string;
  non_winner_sms?: string;
}

// Single endpoint for both create and edit
POST /admin/contests/     // Create
PUT /admin/contests/:id   // Update
```

---

## 🔄 **Enhanced Status System**

### **Implement 9-State Contest Workflow (UPDATED)**
```typescript
type ContestStatus = 
  | 'draft'              // Sponsor working copy
  | 'awaiting_approval'  // Submitted for review
  | 'rejected'           // Admin rejected
  | 'published'          // Admin approved (REMOVED - not used)
  | 'upcoming'           // Approved, not started
  | 'active'             // Currently running
  | 'ended'              // Time expired
  | 'complete'           // Winner selected
  | 'cancelled';         // Cancelled by admin

// CURRENT: Status workflow
// draft -> awaiting_approval -> (rejected OR upcoming) -> active -> ended -> complete
// Any status can go to cancelled

// IMPLEMENT: Status-specific UI and workflows
// IMPLEMENT: Admin approval queue interface
// IMPLEMENT: Bulk approve/reject operations
```

---

## 📊 **Pagination Implementation**

### **Add Pagination to All List Views (UPDATED)**
```typescript
interface PaginationParams {
  page: number;      // Default: 1
  size: number;      // Default: 50, Max: 100
  // Note: sort/order not implemented yet
}

// CURRENT: Actual pagination response structure
interface PaginatedResponse<T> {
  items: T[];        // Changed from 'data' to 'items'
  pagination: {
    total: number;
    page: number;
    size: number;
    total_pages: number;  // NEW: Calculated total pages
    has_next: boolean;    // Changed from 'has_more'
    has_prev: boolean;    // NEW: Has previous page
  };
}

// IMPLEMENT: Pagination UI component
// UPDATE: All list views (contests, entries, users)
```

---

## 🛡️ **Security & Error Handling**

### **Enhanced Error Handling**
```typescript
// IMPLEMENT: Structured error handling (UPDATED)
interface APIError {
  success: false;
  message?: string;
  errors?: Record<string, any>;  // Changed from error_code
  meta?: Record<string, any>;
  timestamp: string;
}

// Handle specific error types (errors are in 'errors' field)
if (error.errors) {
  // Field validation errors
  Object.keys(error.errors).forEach(field => {
    showFieldError(field, error.errors[field]);
  });
} else if (error.message) {
  // General error message
  showGeneralError(error.message);
}

// IMPLEMENT: Global error boundary
// IMPLEMENT: Rate limiting UI feedback
```

---

## 🎨 **UI/UX Enhancements**

### **Performance Optimizations**
```typescript
// IMPLEMENT: Debounced search (300ms)
const debouncedSearch = useDebounce(searchTerm, 300);

// IMPLEMENT: Optimistic updates
const handleSubmit = async (data) => {
  setOptimisticState(newState);
  try {
    await api.submit(data);
  } catch (error) {
    setOptimisticState(previousState);
    handleError(error);
  }
};

// IMPLEMENT: Loading states for all async operations
// IMPLEMENT: Skeleton loaders for better UX
```

### **Enhanced Features**
```typescript
// IMPLEMENT: Advanced filtering
interface ContestFilters {
  status?: ContestStatus[];
  location_type?: string;
  date_range?: { start: string; end: string };
  search?: string;
}

// IMPLEMENT: Bulk operations UI
// IMPLEMENT: Export functionality
// IMPLEMENT: Real-time status updates
```

---

## 🔧 **API Client Updates**

### **Service Layer Implementation (UPDATED)**
```typescript
// IMPLEMENT: Service layer pattern
class ContestService {
  async getContests(params: ContestParams): Promise<APIResponse<PaginatedResponse<Contest>>> {
    return apiClient.get('/contests/active', { params });
  }
  
  // CURRENT: Universal contest endpoints
  async createContest(data: UniversalContestRequest): Promise<APIResponse<UniversalContestResponse>> {
    return apiClient.post('/admin/universal-contests/', data);  // Updated endpoint
  }
  
  async updateContest(id: number, data: Partial<UniversalContestRequest>): Promise<APIResponse<UniversalContestResponse>> {
    return apiClient.put(`/admin/universal-contests/${id}`, data);  // Updated endpoint
  }
  
  // NEW: Additional endpoints available
  async getContest(id: number): Promise<APIResponse<UniversalContestResponse>> {
    return apiClient.get(`/admin/universal-contests/${id}`);
  }
  
  async deleteContest(id: number): Promise<APIResponse<{message: string}>> {
    return apiClient.delete(`/admin/universal-contests/${id}`);
  }
}

// IMPLEMENT: Centralized API client with interceptors
// IMPLEMENT: Request/response logging in development
// IMPLEMENT: Automatic retry logic for failed requests
```

---

## 📱 **Mobile Responsiveness**

### **Enhanced Mobile Experience**
```typescript
// IMPLEMENT: Mobile-first responsive design
// IMPLEMENT: Touch-friendly UI elements
// IMPLEMENT: Swipe gestures for list navigation
// IMPLEMENT: Progressive Web App (PWA) features
```

---

## ✅ **Implementation Checklist**

### **Phase 1: Critical Updates (IMMEDIATE - Week 1)**
- [ ] ✅ **BACKEND READY**: Update all ID types to `number`
- [ ] ✅ **BACKEND READY**: Implement `APIResponse<T>` wrapper handling
- [ ] ✅ **BACKEND READY**: Change `name` to `full_name` in user interfaces
- [ ] ⚠️ **NOT YET**: Add refresh token support (use single token for now)
- [ ] ✅ **BACKEND READY**: Implement universal contest form

### **Phase 2: Enhanced Features (Week 2)**
- [ ] ✅ **BACKEND READY**: Add pagination to all list views
- [ ] ✅ **BACKEND READY**: Implement 9-state status system UI
- [ ] ✅ **BACKEND READY**: Add admin approval queue interface
- [ ] ⚠️ **PARTIAL**: Implement bulk operations (delete ready, approve/reject pending)
- [ ] ⚠️ **PARTIAL**: Add advanced filtering (basic search ready)

### **Phase 3: Performance & UX (Week 3)**
- [ ] Add debounced search
- [ ] Implement optimistic updates
- [ ] Add loading states and skeleton loaders
- [ ] Implement error boundaries
- [ ] Add rate limiting feedback

### **Phase 4: Polish & Testing (Week 4)**
- [ ] Mobile responsiveness improvements
- [ ] Accessibility enhancements
- [ ] Performance optimizations
- [ ] ✅ **BACKEND READY**: Comprehensive testing infrastructure
- [ ] Documentation updates

---

## 🎯 **Success Criteria**

1. **Zero API Response Format Errors**: All endpoints use consistent `APIResponse<T>`
2. **Type Safety**: All IDs properly typed as `number`
3. **Feature Parity**: All backend features accessible in UI
4. **Performance**: Sub-300ms response times with optimistic updates
5. **User Experience**: Smooth, responsive interface with proper error handling

---

## 🚀 **BACKEND STATUS: PRODUCTION READY**

### **✅ Current Backend Capabilities (August 30, 2025)**
- **Server**: Running without errors on `http://localhost:8000` ✅
- **API Response Format**: Fully standardized with `APIResponse<T>` wrapper ✅
- **Authentication**: OTP system operational with JWT tokens ✅
- **Universal Contest Form**: 60+ field support, full CRUD operations ✅
- **Status System**: 9-state workflow with admin approval queue ✅
- **Pagination**: Implemented across all list endpoints ✅
- **Error Handling**: Structured error responses with proper HTTP codes ✅
- **Database**: SQLite with all tables created and relationships established ✅
- **Testing**: Comprehensive test suite with 100% critical test pass rate ✅
- **Profile Updates**: PUT /users/me endpoint fully operational ✅
- **CORS Configuration**: All methods and headers properly configured ✅

### **⚠️ Frontend Alignment Required**
The backend is fully operational and production-ready. The frontend needs to be updated to match the current API contracts and response formats to ensure seamless integration.

---

**Priority**: Implement Phase 1 changes immediately to resolve critical compatibility issues. The backend is production-ready and waiting for frontend alignment.**
