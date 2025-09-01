# 🧠 Frontend Summary & API Alignment Report

**Generated**: January 30, 2025  
**Purpose**: Backend team alignment and API integration reference  
**Frontend Version**: Enhanced Contest Status System (Production Ready)

---

## 1. 📱 App Overview

### **Application Purpose**
Contestlet is a comprehensive contest management platform supporting three user types:
- **Users**: Enter contests, view results, manage entries
- **Sponsors**: Create, manage, and monitor their contests
- **Admins**: Approve contests, manage platform, oversee all operations

### **Architecture**
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6 with role-based route protection
- **Styling**: Tailwind CSS with custom components
- **State Management**: React hooks + localStorage (no Redux/Zustand)
- **Build Tool**: Create React App (CRA)

### **Primary Screens & Routes**

#### **Public Routes**
```typescript
/ (LandingPage)                    // Marketing homepage
/enter/:contest_id (ContestAuth)   // Contest entry authentication
/contest/:contest_id/success       // Entry confirmation
/contest/:contest_id/details       // Contest details view
/login, /admin-login (AdminLogin)  // Authentication
```

#### **Authenticated Routes (Role-Based)**
```typescript
// Universal Routes (All Roles)
/dashboard (UnifiedDashboard)      // Role-specific dashboard
/contests (UnifiedContests)        // Contest browsing/management
/contest/:id (ContestEntryPage)    // Contest details/entry
/settings (Settings)               // User settings
/profile/:id/entries (MyEntries)  // User's contest entries

// Creator Routes (Sponsor + Admin)
/contest/create (CreateContest)    // Contest creation
/contest/:id/edit (UpdateContest)  // Contest editing
/sponsor/drafts (DraftManagement)  // Draft contest management

// Admin-Only Routes
/admin/approval (AdminApprovalDashboard)     // Approval overview
/admin/approval-queue (AdminApprovalQueue)   // Contest approval queue
/contests/:id/review (AdminContestReview)    // Individual contest review
/contest/:id/entries (ContestEntries)        // Contest entries management
/notifications (NotificationLogs)            // SMS/notification logs
/admin/debug (AdminApprovalDebug)           // Debug tools
```

---

## 2. 🔄 User Flows

### **User Journey: Contest Entry**
1. **Discovery**: User finds contest via `/` or `/contests`
2. **Entry**: Navigate to `/enter/:contest_id`
3. **Authentication**: Phone + OTP verification via `ContestAuth`
4. **Submission**: Submit entry data (phone, optional fields)
5. **Confirmation**: Redirect to `/contest/:contest_id/success`
6. **Follow-up**: SMS notifications sent automatically

### **Sponsor Journey: Contest Creation**
1. **Authentication**: Login via `/login` (phone + OTP)
2. **Creation**: Navigate to `/contest/create`
3. **Form Completion**: Fill unified contest form (60+ fields)
4. **Draft Management**: Save as draft via `/sponsor/drafts`
5. **Submission**: Submit for admin approval
6. **Monitoring**: Track status via `/dashboard` or `/contests`

### **Admin Journey: Contest Approval**
1. **Queue Review**: Access `/admin/approval-queue`
2. **Individual Review**: Navigate to `/contests/:id/review`
3. **Decision**: Approve/reject with reason/message
4. **Bulk Operations**: Mass approve/reject multiple contests
5. **Monitoring**: Track approval statistics and audit trails

### **Navigation Logic**
- **Role-Based Redirects**: Automatic routing based on user role
- **Authentication Guards**: `RoleBasedRoute` component protects routes
- **Fallback Handling**: Graceful degradation for failed API calls
- **Breadcrumb Navigation**: Contextual navigation in forms/dashboards

---

## 3. 🗂️ State Management

### **Architecture**: React Hooks + localStorage (No Global State Library)

#### **Authentication State**
```typescript
// useUserRole Hook
interface UserInfo {
  id: string;
  phone: string;
  role: 'admin' | 'sponsor' | 'user';
  isAuthenticated: boolean;
  name?: string;
  email?: string;
  sponsor_profile?: any;
}

// Storage Keys
localStorage.access_token          // JWT token
localStorage.contestlet_admin_token // Legacy admin token
localStorage.user_role            // Cached role
localStorage.user_phone           // Cached phone
```

#### **Component-Level State**
- **Contest Lists**: `useState<Contest[]>` in dashboard/list components
- **Form Data**: `useState<ContestFormData>` in creation/edit forms
- **UI State**: Loading, error, filter, sort states per component
- **Toast Messages**: Component-level toast state for user feedback

#### **Data Flow Pattern**
```typescript
Component → API Call → Update Local State → Re-render
```

#### **No Global State Management**
- Each component manages its own data fetching
- Shared data refetched as needed
- Authentication state shared via `useUserRole` hook
- No Redux, Zustand, or Context API for data

---

## 4. 🔌 API Consumption Summary

### **Base Configuration**
```typescript
API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'
Timeout: 10000ms
Authentication: Bearer JWT tokens
Error Handling: Custom ApiError class with RLS error codes
```

### **Authentication Endpoints**

#### **POST /auth/request-otp** (Public)
```typescript
// Request
{ phone: string }

// Response
{ message: string }

// Usage: Phone verification for login
// Triggers: Login form submission, contest entry
// Error Handling: Rate limiting, invalid phone format
```

#### **POST /auth/verify-otp** (Public)
```typescript
// Request
{ phone: string, code: string }

// Response
{ access_token: string, role: string }

// Usage: Complete authentication flow
// Triggers: OTP form submission
// Storage: Saves access_token to localStorage
```

#### **GET /auth/me** (Authenticated)
```typescript
// Response
{ id, phone, role, name, email, sponsor_profile? }

// Usage: Get current user profile
// Triggers: Profile page load, role verification
// Headers: Authorization: Bearer {token}
```

### **Contest Endpoints**

#### **GET /contests/active** (Public)
```typescript
// Response
{ data: Contest[] }

// Usage: Public contest browsing, user dashboard
// Triggers: Landing page, unauthenticated users
// Filters: Only active/upcoming contests
```

#### **GET /admin/contests/** (Admin Only)
```typescript
// Response
{ data: Contest[] }

// Usage: Admin dashboard, all contest management
// Triggers: Admin dashboard load, contest management
// Headers: Authorization required
// Note: Trailing slash required to avoid 307 redirect
```

#### **GET /sponsor/contests/** (Sponsor Only)
```typescript
// Response
{ data: Contest[] }

// Usage: Sponsor dashboard, own contest management
// Triggers: Sponsor dashboard load
// Filters: Only contests created by sponsor
```

#### **GET /contests/:id** (Public)
```typescript
// Response
{ data: Contest }

// Usage: Contest details, entry pages
// Triggers: Contest detail page load
// Public: Available to all users
```

#### **GET /admin/contests/:id** (Admin Only)
```typescript
// Response
{ data: Contest }

// Usage: Admin contest editing, detailed review
// Triggers: Admin edit form load, approval review
// Enhanced: Includes admin-only fields
```

#### **POST /admin/contests/** (Admin/Sponsor)
```typescript
// Request
{
  name: string,
  description: string,
  start_time: string, // ISO 8601 UTC
  end_time: string,   // ISO 8601 UTC
  location?: string,
  latitude?: number,
  longitude?: number,
  prize_description?: string,
  sponsor_profile_id?: string, // Admin only
  contest_type?: 'general' | 'sweepstakes' | 'instant_win',
  entry_method?: 'sms' | 'email' | 'web_form',
  winner_selection_method?: 'random' | 'scheduled' | 'instant',
  minimum_age?: number,
  max_entries_per_person?: number,
  total_entry_limit?: number,
  location_type?: 'united_states' | 'specific_states' | 'radius' | 'custom',
  selected_states?: string[],
  radius_address?: string,
  radius_miles?: number,
  official_rules?: {
    sponsor_name?: string,
    prize_value_usd?: number,
    terms_url?: string,
    eligibility_text?: string
  },
  // SMS Templates
  entry_confirmation_sms?: string,
  winner_notification_sms?: string,
  non_winner_sms?: string
}

// Response
{ data: Contest }

// Usage: Contest creation
// Triggers: Form submission from CreateContest
// Validation: Frontend validates required fields
// Note: Trailing slash required, blob URLs excluded
```

#### **PUT /admin/contests/:id** (Admin/Sponsor)
```typescript
// Request: Same as POST (partial updates supported)
// Response: { data: Contest }

// Usage: Contest editing
// Triggers: Form submission from UpdateContest
// Permissions: Sponsors can edit own, admins can edit all
```

#### **DELETE /contests/:id** (Admin/Sponsor)
```typescript
// Response
{
  success: boolean,
  message: string,
  contest_id: string,
  cleanup_summary: {
    entries_deleted: number,
    notifications_deleted: number,
    dependencies_cleared: number
  }
}

// Usage: Contest deletion
// Triggers: Delete button in contest management
// Permissions: Role-based deletion rights
// Note: Uses unified endpoint, not /admin/contests/:id
```

### **Enhanced Status System Endpoints**

#### **POST /sponsor/workflow/contests/draft** (Sponsor)
```typescript
// Request: Contest data (same as create)
// Response: { data: Contest } with status: 'draft'

// Usage: Save contest as draft
// Triggers: Draft save in contest form
// Workflow: Sponsor draft creation
```

#### **POST /sponsor/workflow/contests/:id/submit** (Sponsor)
```typescript
// Request: { message?: string }
// Response: { data: Contest } with status: 'awaiting_approval'

// Usage: Submit draft for admin approval
// Triggers: Submit button in draft management
// Workflow: Draft → Awaiting Approval
```

#### **GET /admin/approval/queue** (Admin Only)
```typescript
// Query: ?page=1&size=20
// Response
{
  pending_contests: [
    {
      contest_id: string,
      name: string,
      creator_name: string,
      submitted_at: string,
      days_pending: number,
      priority: 'low' | 'medium' | 'high'
    }
  ],
  total_pending: number,
  average_approval_time_days: number,
  oldest_pending_days: number
}

// Usage: Admin approval queue management
// Triggers: Admin approval dashboard load
// Pagination: Supports page/size parameters
```

#### **POST /admin/approval/contests/:id/approve** (Admin Only)
```typescript
// Request
{ approved: boolean, reason?: string }

// Response
{
  contest_id: string,
  old_status: string,
  new_status: string,
  changed_by_user_id: string,
  message: string
}

// Usage: Approve/reject individual contests
// Triggers: Approval/rejection buttons in review
// Workflow: Awaiting Approval → Upcoming/Rejected
```

#### **POST /admin/approval/contests/bulk-approve** (Admin Only)
```typescript
// Request
{ contest_ids: string[], approved: boolean, reason?: string }

// Response: Array of approval results

// Usage: Bulk approve/reject operations
// Triggers: Bulk action buttons in approval queue
// Efficiency: Process multiple contests at once
```

### **Entry Endpoints**

#### **POST /contests/:id/enter** (Authenticated Users)
```typescript
// Request
{
  phone: string,
  additional_data?: any
}

// Response
{
  success: boolean,
  entry_id: string,
  message: string
}

// Usage: Contest entry submission
// Triggers: Entry form submission
// Authentication: Requires valid user token
// SMS: Triggers entry confirmation SMS
```

#### **GET /entries/me** (Authenticated Users)
```typescript
// Response
{ data: Entry[] }

// Usage: User's contest entry history
// Triggers: MyEntries page load
// Filters: Only entries by authenticated user
```

#### **GET /admin/contests/:id/entries** (Admin Only)
```typescript
// Response
{ data: Entry[] }

// Usage: Contest entry management
// Triggers: Admin contest entries view
// Admin: Full entry details and management
```

### **Location Endpoints**

#### **GET /location/states** (Public)
```typescript
// Response
{ data: [{ code: string, name: string }] }

// Usage: State selection in contest forms
// Triggers: Location type selection
// Static: US states list
```

#### **POST /location/geocode** (Authenticated)
```typescript
// Request: { address: string }
// Response: { latitude: number, longitude: number, formatted_address: string }

// Usage: Address to coordinates conversion
// Triggers: Radius-based location setup
// Service: Backend geocoding integration
```

### **Media Endpoints (Cloudinary Integration)**

#### **POST /media/contests/:id/hero** (Authenticated)
```typescript
// Request: FormData with file
// Query: ?media_type=image|video
// Response
{
  secure_url: string,
  public_id: string,
  media_type: string,
  metadata: any
}

// Usage: Contest hero image/video upload
// Triggers: File upload in contest forms
// Integration: Cloudinary CDN optimization
// Limits: 50MB max file size
```

#### **DELETE /media/contests/:id/hero** (Authenticated)
```typescript
// Response: { success: boolean, message: string }

// Usage: Remove contest media
// Triggers: Delete button in media management
// Cleanup: Removes from Cloudinary
```

### **User Management Endpoints**

#### **GET /admin/users** (Admin Only)
```typescript
// Response: { data: User[] }

// Usage: User management, sponsor selection
// Triggers: Admin user management pages
// Admin: Full user list access
```

#### **GET /admin/sponsors** (Admin Only)
```typescript
// Response
{ data: [
  {
    id: string,
    company_name: string,
    contact_name: string,
    is_verified: boolean,
    sponsor_profile: any
  }
] }

// Usage: Sponsor dropdown in contest forms
// Triggers: Admin contest creation/editing
// Fallback: Falls back to /admin/users if unavailable
```

#### **GET /users/me** (Authenticated)
```typescript
// Response: { data: User }

// Usage: Profile management, role verification
// Triggers: Profile page, authentication checks
// Enhanced: Includes sponsor_profile data
```

#### **PUT /users/me** (Authenticated)
```typescript
// Request: User profile data
// Response: { data: User }

// Usage: Profile updates
// Triggers: Settings form submission
// Validation: Backend validates profile data
```

### **Notification Endpoints**

#### **GET /admin/notifications** (Admin Only)
```typescript
// Query: Various filters
// Response: { data: Notification[] }

// Usage: SMS log management
// Triggers: Notification logs page
// Filters: Date range, type, status
```

#### **POST /notifications/sms** (Admin Only)
```typescript
// Request: SMS data
// Response: { success: boolean, message_id: string }

// Usage: Manual SMS sending
// Triggers: Admin SMS tools
// Integration: Twilio backend integration
```

---

## 5. 🔗 Component–Data Mapping

### **Dashboard Components**
- **UnifiedDashboard**: `api.contests.getAll()` (admin), `api.contests.getSponsor()` (sponsor), `api.contests.getActive()` (user)
- **UnifiedContests**: Same as dashboard + filtering/sorting logic
- **AdminApprovalDashboard**: `api.approval.getStatistics()`

### **Contest Management Components**
- **CreateContest/UpdateContest**: Wraps `UnifiedContestForm`
- **UnifiedContestForm**: `api.contests.create()`, `api.contests.update()`, `api.users.getSponsors()`
- **AdminApprovalQueue**: `api.approval.getQueue()`, `api.approval.getStatistics()`
- **AdminContestReview**: `api.contests.getByIdAdmin()`, `api.approval.approveContest()`

### **Entry Components**
- **ContestAuth**: `api.auth.requestOtp()`, `api.auth.verifyOtp()`, `api.entries.submit()`
- **ContestEntryPage**: `api.contests.getById()` (public), contest entry logic
- **MyEntries**: `api.entries.getMine()`
- **ContestEntries**: `api.entries.getContestEntries()` (admin)

### **Media Components**
- **MediaField**: Wraps MediaUpload + URL input
- **MediaUpload**: `POST /media/contests/:id/hero`, `DELETE /media/contests/:id/hero`
- **ResponsiveMedia**: Displays Cloudinary-optimized images

### **Authentication Components**
- **AdminLogin**: `api.auth.requestOtp()`, `api.auth.verifyOtp()`
- **RoleBasedRoute**: Uses `useUserRole()` hook for route protection
- **Settings**: `api.users.getMe()`, `api.users.updateMe()`

### **Shared Data Types**
- **Contest**: Used across all contest-related components
- **User/UserInfo**: Used in authentication and profile components
- **ApiResponse<T>**: Wrapper for all API responses
- **ContestFormData**: Form state for contest creation/editing

---

## 6. 🚨 Assumptions & Gaps

### **Backend Logic Assumptions**

#### **Contest Ownership**
```typescript
// ASSUMPTION: Backend determines contest ownership
// FRONTEND GAP: No explicit ownership checking in UI
// TODO: Implement contest.created_by_user_id validation
const isCreator = true; // Placeholder - should check contest.created_by_user_id === currentUserId
```

#### **Role-Based Sponsor Assignment**
```typescript
// ASSUMPTION: Backend auto-assigns sponsor for sponsor users
// FRONTEND: Sends sponsor_profile_id for admins, ignores for sponsors
// BACKEND EXPECTED: Ignores sponsor_profile_id from sponsors for security
```

#### **Contest Status Transitions**
```typescript
// ASSUMPTION: Backend handles all status transitions automatically
// FRONTEND: Displays status, doesn't validate transition rules
// BACKEND EXPECTED: Enforces draft → awaiting_approval → approved/rejected workflow
```

### **API Response Format Assumptions**
```typescript
// ASSUMPTION: Inconsistent response wrapping
// CURRENT: Some endpoints return { data: T }, others return T directly
// FRONTEND HANDLES: (response as any)?.data || (response as any)?.contests || response || []
```

### **TODO Comments & Placeholders**

#### **Contest Creation**
```typescript
// TODO: Implement geocoding for radius-based contests
latitude: null, // TODO: Implement geocoding
longitude: null

// TODO: File upload integration for contest creation
// Currently: Blob URLs excluded from API payload
```

#### **Entry Management**
```typescript
// TODO: Determine actual ownership from contest.created_by_user_id
// TODO: Backend support for "entered" contest filter
// TODO: Implement entry limit validation
```

#### **Media System**
```typescript
// TODO: Cloudinary integration completion
// TODO: Video upload support
// TODO: Media optimization settings
```

#### **Notification System**
```typescript
// TODO: Real-time notification updates
// TODO: SMS template validation
// TODO: Notification preferences
```

### **Missing Backend Features**
- **Contest Analytics**: Entry counts, conversion rates, performance metrics
- **Advanced Filtering**: Complex contest queries, date ranges, location filters
- **Bulk Operations**: Mass contest updates, batch entry management
- **Audit Logging**: Detailed action logs, change history
- **Caching Strategy**: Contest list caching, user session management

---

## 7. 📋 Schema Expectations

### **User Schema**
```typescript
interface User {
  id: string;                    // Primary key
  phone: string;                 // Unique identifier
  role: 'admin' | 'sponsor' | 'user';
  name?: string;                 // Display name
  email?: string;                // Optional email
  created_at: string;            // ISO 8601
  updated_at: string;            // ISO 8601
  
  // Sponsor-specific (when role === 'sponsor')
  sponsor_profile?: {
    id: string;
    company_name: string;
    contact_name: string;
    is_verified: boolean;
    // Additional sponsor fields...
  };
}
```

### **Contest Schema (Complete - 60+ Fields)**
```typescript
interface Contest {
  // Core Database Fields
  id: string;                    // Primary key
  name: string;                  // Required
  description: string;           // Required
  location?: string;             // Optional location text
  latitude?: number;             // Geocoded coordinates
  longitude?: number;
  start_time: string;            // ISO 8601 UTC - Required
  end_time: string;              // ISO 8601 UTC - Required
  prize_description?: string;
  status: 'draft' | 'awaiting_approval' | 'rejected' | 'upcoming' | 'active' | 'ended' | 'complete' | 'cancelled';
  created_at?: string;           // ISO 8601
  updated_at?: string;           // ISO 8601

  // Enhanced Media System (Cloudinary)
  image_url?: string;            // Public URL
  image_public_id?: string;      // Cloudinary public ID
  media_type?: 'image' | 'video';
  media_metadata?: any;          // JSON metadata
  sponsor_url?: string;          // Sponsor website

  // Role & Permission System
  created_by_user_id?: string;   // Contest creator
  sponsor_profile_id?: string;   // Foreign key to sponsor profiles
  approved_by_user_id?: string;  // Admin who approved

  // Contest Configuration
  contest_type?: 'general' | 'sweepstakes' | 'instant_win';
  entry_method?: 'sms' | 'email' | 'web_form';
  winner_selection_method?: 'random' | 'scheduled' | 'instant';
  minimum_age?: number;          // Default: 18
  max_entries_per_person?: number;
  total_entry_limit?: number;
  consolation_offer?: string;
  geographic_restrictions?: string;
  contest_tags?: string[];       // JSON array
  promotion_channels?: string[]; // JSON array

  // Smart Location System
  location_type?: 'united_states' | 'specific_states' | 'radius' | 'custom';
  selected_states?: string[];    // JSON array of state codes
  radius_address?: string;       // Address for radius targeting
  radius_miles?: number;         // Radius in miles
  radius_latitude?: number;      // Center coordinates
  radius_longitude?: number;

  // Enhanced Status Workflow
  submitted_at?: string;         // When submitted for approval
  approved_at?: string;          // When approved
  rejected_at?: string;          // When rejected
  rejection_reason?: string;     // Admin rejection reason
  approval_message?: string;     // Admin approval message

  // Winner Tracking
  winner_entry_id?: string;
  winner_phone?: string;         // Winner's phone
  winner_selected_at?: string;   // When winner selected
  is_paused?: boolean;

  // SMS Templates (stored separately but accessible)
  entry_confirmation_sms?: string;
  winner_notification_sms?: string;
  non_winner_sms?: string;

  // Backend Computed Fields (Read-Only)
  sponsor_name?: string;         // Computed from sponsor_profile
  location_summary?: string;     // Human-readable location
  entry_count?: number;          // Current entry count
  can_enter?: boolean;           // Whether user can enter
  is_active?: boolean;           // Whether accepting entries
  is_upcoming?: boolean;         // Whether not started
  is_ended?: boolean;            // Whether time expired
  is_complete?: boolean;         // Whether winner selected
  time_until_start?: number;     // Seconds until start
  time_until_end?: number;       // Seconds until end
  duration_days?: number;        // Contest duration
  entry_limit_reached?: boolean; // Whether limit reached
  progress_percentage?: number;   // Progress (0-100)
  status_info?: any;             // Status display info

  // Audit Trail Relationships
  approval_history?: any[];      // ContestApprovalAudit records
  status_audit?: any[];          // ContestStatusAudit records

  // Official Rules (Relationship)
  official_rules?: {
    sponsor_name?: string;
    prize_value_usd?: number;
    terms_url?: string;
    eligibility_text?: string;
    start_date?: string;         // Legal start date
    end_date?: string;           // Legal end date
  };
}
```

### **Entry Schema**
```typescript
interface Entry {
  id: string;                    // Primary key
  contest_id: string;            // Foreign key
  user_id: string;               // Foreign key
  phone: string;                 // Entry phone number
  created_at: string;            // Entry timestamp
  additional_data?: any;         // JSON additional fields
  
  // Computed/Display Fields
  contest?: Contest;             // Populated contest data
  user?: User;                   // Populated user data
}
```

### **Notification Schema**
```typescript
interface Notification {
  id: string;                    // Primary key
  type: 'sms' | 'email';
  recipient: string;             // Phone or email
  message: string;               // Message content
  status: 'pending' | 'sent' | 'failed';
  sent_at?: string;              // When sent
  error_message?: string;        // If failed
  contest_id?: string;           // Related contest
  entry_id?: string;             // Related entry
  
  // Twilio Integration
  twilio_sid?: string;           // Twilio message SID
  twilio_status?: string;        // Twilio delivery status
}
```

### **API Response Wrappers**
```typescript
interface ApiResponse<T> {
  data?: T;                      // Standard wrapper
  contests?: T[];                // Legacy contest arrays
  message?: string;              // Success message
  error?: string;                // Error message
}

interface PaginatedResponse<T> {
  data: T[];                     // Items
  total: number;                 // Total count
  page: number;                  // Current page
  limit: number;                 // Items per page
  hasMore: boolean;              // More pages available
}
```

---

## 8. 🔐 Auth & Permissions

### **Supported Roles**
```typescript
type UserRole = 'admin' | 'sponsor' | 'user';
```

### **Role Capabilities**

#### **User Role**
- **Access**: Public contests, own entries, profile management
- **Restrictions**: Cannot create contests, cannot access admin features
- **Routes**: `/dashboard`, `/contests` (browse only), `/profile/:id/entries`, `/settings`

#### **Sponsor Role**
- **Access**: Create/edit own contests, draft management, entry monitoring
- **Restrictions**: Cannot approve contests, cannot access other sponsors' contests
- **Routes**: All user routes + `/contest/create`, `/contest/:id/edit`, `/sponsor/drafts`
- **Auto-Assignment**: Backend auto-assigns sponsor_profile_id for security

#### **Admin Role**
- **Access**: All platform features, contest approval, user management
- **Restrictions**: None (full platform access)
- **Routes**: All routes including `/admin/*` paths
- **Capabilities**: Approve/reject contests, manage all users, access all data

### **Client-Side Authentication**

#### **JWT Token Storage**
```typescript
// Primary Authentication
localStorage.access_token          // JWT token from /auth/verify-otp

// Legacy Support
localStorage.contestlet_admin_token // Legacy admin token
localStorage.contestlet-admin-token // Alternative key format

// Cached Data
localStorage.user_role            // Cached role for quick access
localStorage.user_phone           // Cached phone for display
```

#### **JWT Token Structure**
```typescript
interface JWTClaims {
  sub: string;                   // User ID
  phone: string;                 // User phone
  role: 'admin' | 'sponsor' | 'user';
  exp: number;                   // Expiration timestamp
  iat?: number;                  // Issued at timestamp
}
```

#### **Token Validation**
```typescript
// Frontend JWT Validation (Security Note: Backend must also validate)
const validateJWTForRLS = (token: string) => {
  // Decode JWT payload
  // Check required claims: sub, phone, role, exp
  // Verify expiration
  // Validate role against allowed values
  // Return validation result
};
```

### **Route Protection**

#### **RoleBasedRoute Component**
```typescript
<RoleBasedRoute allowedRoles={['admin', 'sponsor']}>
  <CreateContest />
</RoleBasedRoute>

// Implementation:
// 1. Check authentication status
// 2. Verify user role against allowedRoles
// 3. Redirect to login if unauthorized
// 4. Render component if authorized
```

#### **API Request Authentication**
```typescript
// Automatic Header Injection
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}

// RLS (Row Level Security) Integration
// - Frontend validates JWT client-side for UX
// - Backend enforces all security server-side
// - Role-based data filtering handled by backend
```

### **Authentication Flow**

#### **Login Process**
1. **Phone Input**: User enters phone number
2. **OTP Request**: `POST /auth/request-otp { phone }`
3. **OTP Verification**: `POST /auth/verify-otp { phone, code }`
4. **Token Storage**: Save `access_token` to localStorage
5. **Role Detection**: Decode JWT to determine role
6. **Redirect**: Navigate to appropriate dashboard

#### **Session Management**
- **Token Expiration**: Automatic logout on JWT expiration
- **Token Refresh**: No automatic refresh (user must re-login)
- **Multi-Device**: Each device maintains separate session
- **Logout**: Clear all localStorage tokens and redirect to home

#### **Permission Checking**
```typescript
// Component-Level Checks
const userRole = getUserRole();
const canEdit = isAdmin() || isSponsor();
const canApprove = isAdmin();

// API-Level Checks
// Backend enforces all permissions
// Frontend shows/hides UI elements based on role
// API returns 403 Forbidden for unauthorized requests
```

---

## 9. 🔌 Miscellaneous

### **Third-Party Integrations**

#### **Cloudinary (Media Management)**
- **Purpose**: Image/video upload, optimization, and CDN delivery
- **Integration**: Direct upload from frontend to backend proxy
- **Endpoints**: `POST /media/contests/:id/hero`, `DELETE /media/contests/:id/hero`
- **Features**: Automatic optimization, multiple formats, responsive delivery
- **Fallback**: URL input mode when Cloudinary not configured
- **Limits**: 50MB max file size, image/video types only

#### **Twilio (SMS Service)**
- **Purpose**: OTP delivery, contest notifications, winner notifications
- **Integration**: Backend-only (frontend triggers via API)
- **Usage**: Entry confirmations, winner notifications, admin alerts
- **Error Handling**: Frontend displays Twilio errors as "SMS service unavailable"
- **Templates**: Customizable SMS templates per contest

#### **Geocoding Service**
- **Purpose**: Address to coordinates conversion for radius-based contests
- **Integration**: Backend service, frontend triggers via `POST /location/geocode`
- **Usage**: Radius contest setup, location validation
- **Fallback**: Manual coordinate entry if geocoding fails

### **Environment Configuration**
```typescript
// Environment Variables
REACT_APP_API_BASE_URL          // Backend API URL
REACT_APP_ENVIRONMENT           // development | staging | production
REACT_APP_DEBUG_MODE            // Enable debug logging

// Build Configurations
Development: http://localhost:8000
Staging: https://staging-api.contestlet.com
Production: https://api.contestlet.com
```

### **Performance Optimizations**

#### **Code Splitting**
- **Route-Based**: Each page component loaded on demand
- **Component-Based**: Large components (forms, dashboards) split
- **Library Splitting**: Vendor libraries separated from app code

#### **Data Fetching**
- **No Caching**: Each component refetches data on mount
- **Optimistic Updates**: Form submissions show immediate feedback
- **Error Boundaries**: Graceful error handling with retry options
- **Loading States**: Comprehensive loading indicators

#### **Image Optimization**
- **Cloudinary Integration**: Automatic format optimization (WebP, AVIF)
- **Responsive Images**: Multiple sizes generated automatically
- **Lazy Loading**: Images loaded as needed
- **Fallback**: Standard image tags when Cloudinary unavailable

### **Offline Support & PWA**
- **Current Status**: No offline support implemented
- **Future Plans**: Contest browsing offline, entry queuing
- **PWA Features**: Not currently implemented
- **Caching Strategy**: No client-side caching (relies on browser cache)

### **Analytics & Monitoring**
- **Error Tracking**: Console logging only (no external service)
- **User Analytics**: No user behavior tracking implemented
- **Performance Monitoring**: No performance metrics collection
- **API Monitoring**: Basic error logging in API client

### **Security Measures**

#### **Client-Side Security**
- **JWT Validation**: Client-side validation for UX (backend enforces security)
- **Input Sanitization**: Basic HTML escaping in forms
- **CORS Handling**: Proper CORS configuration expected from backend
- **XSS Prevention**: React's built-in XSS protection

#### **Data Protection**
- **Token Storage**: localStorage (not secure for sensitive data)
- **Sensitive Data**: No sensitive data stored client-side
- **API Security**: All security enforced server-side
- **Rate Limiting**: Handled by backend, frontend shows rate limit errors

### **Development Tools**

#### **Debug Features**
- **Admin Debug Page**: `/admin/debug` for troubleshooting
- **Console Logging**: Extensive logging in development
- **API Error Details**: Detailed error information in console
- **Token Extraction**: Helper script for token debugging

#### **Testing Strategy**
- **Unit Tests**: Limited (basic component tests)
- **Integration Tests**: Manual testing workflows
- **E2E Tests**: No automated E2E testing
- **API Testing**: Manual testing with browser dev tools

---

## 🎯 Summary for Backend Team

### **Critical Integration Points**

1. **Authentication**: JWT-based with role claims (sub, phone, role, exp)
2. **Contest Management**: 8-state workflow with admin approval system
3. **Media Handling**: Cloudinary integration for optimized delivery
4. **SMS Integration**: Twilio for notifications and OTP delivery
5. **Role-Based Security**: Frontend respects, backend enforces all permissions

### **API Expectations**

1. **Consistent Response Format**: Prefer `{ data: T }` wrapper
2. **Trailing Slash Handling**: `/admin/contests/` (with slash) to avoid redirects
3. **Error Structure**: Structured error responses with codes and messages
4. **Computed Fields**: Backend-calculated fields (location_summary, status_info, etc.)
5. **Pagination Support**: Page/size parameters for large datasets

### **Schema Alignment Priorities**

1. **Contest Schema**: 60+ fields including computed and audit fields
2. **User Profiles**: Sponsor profile relationships and verification status
3. **Entry Management**: Contest-entry relationships and user tracking
4. **Notification System**: SMS templates and delivery tracking
5. **Audit Trails**: Approval history and status change tracking

### **Security Requirements**

1. **JWT Validation**: Server-side validation of all claims
2. **Role-Based Access**: Enforce permissions at API level
3. **Data Filtering**: RLS-style filtering based on user role
4. **Input Validation**: Sanitize and validate all form inputs
5. **Rate Limiting**: Protect against abuse and spam

**Frontend is production-ready and awaiting full backend alignment on these integration points.** 🚀
