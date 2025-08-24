# 🎯 Multi-Tier Role System - Frontend Integration Guide

## 📋 Overview

This guide provides complete integration instructions for the new multi-tier role system with three user types: **Admin**, **Sponsor**, and **User**. Each role has specific permissions, UI components, and API endpoints.

## 🔐 Authentication Changes

### **Enhanced JWT Token Structure**

The JWT tokens now include role information:

```json
{
  "sub": "123",           // User ID
  "phone": "+1234567890", // Phone number
  "role": "admin",        // NEW: User role (admin, sponsor, user)
  "exp": 1234567890       // Expiration
}
```

### **Token Decoding Example**

```typescript
interface DecodedToken {
  sub: string;
  phone: string;
  role: 'admin' | 'sponsor' | 'user';
  exp: number;
}

function decodeToken(token: string): DecodedToken | null {
  try {
    const decoded = jwt.decode(token) as DecodedToken;
    return decoded;
  } catch (error) {
    console.error('Token decode error:', error);
    return null;
  }
}

// Usage
const token = localStorage.getItem('access_token');
const userInfo = decodeToken(token);
console.log(`User role: ${userInfo?.role}`);
```

## 🎨 Role-Based UI Components

### **Role Detection Hook**

```typescript
// hooks/useUserRole.ts
import { useState, useEffect } from 'react';
import { decodeToken } from '../utils/auth';

export type UserRole = 'admin' | 'sponsor' | 'user';

export interface UserInfo {
  id: string;
  phone: string;
  role: UserRole;
  isAuthenticated: boolean;
}

export function useUserRole(): UserInfo {
  const [userInfo, setUserInfo] = useState<UserInfo>({
    id: '',
    phone: '',
    role: 'user',
    isAuthenticated: false
  });

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      const decoded = decodeToken(token);
      if (decoded) {
        setUserInfo({
          id: decoded.sub,
          phone: decoded.phone,
          role: decoded.role,
          isAuthenticated: true
        });
      }
    }
  }, []);

  return userInfo;
}
```

### **Role-Based Navigation**

```typescript
// components/Navigation.tsx
import React from 'react';
import { useUserRole } from '../hooks/useUserRole';

export function Navigation() {
  const { role, isAuthenticated } = useUserRole();

  if (!isAuthenticated) {
    return <LoginPrompt />;
  }

  return (
    <nav>
      {/* Common navigation items */}
      <NavItem href="/contests">Browse Contests</NavItem>
      
      {/* User-specific items */}
      {role === 'user' && (
        <>
          <NavItem href="/user/profile">My Profile</NavItem>
          <NavItem href="/user/entries">My Entries</NavItem>
          <NavItem href="/user/stats">My Stats</NavItem>
        </>
      )}
      
      {/* Sponsor-specific items */}
      {(role === 'sponsor' || role === 'admin') && (
        <>
          <NavItem href="/sponsor/dashboard">Sponsor Dashboard</NavItem>
          <NavItem href="/sponsor/contests">My Contests</NavItem>
          <NavItem href="/sponsor/profile">Company Profile</NavItem>
          <NavItem href="/sponsor/analytics">Analytics</NavItem>
        </>
      )}
      
      {/* Admin-specific items */}
      {role === 'admin' && (
        <>
          <NavItem href="/admin/dashboard">Admin Dashboard</NavItem>
          <NavItem href="/admin/users">User Management</NavItem>
          <NavItem href="/admin/contests">Contest Management</NavItem>
          <NavItem href="/admin/sponsors">Sponsor Management</NavItem>
        </>
      )}
    </nav>
  );
}
```

### **Role-Based Route Protection**

```typescript
// components/ProtectedRoute.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useUserRole, UserRole } from '../hooks/useUserRole';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles: UserRole[];
  fallbackPath?: string;
}

export function ProtectedRoute({ 
  children, 
  requiredRoles, 
  fallbackPath = '/login' 
}: ProtectedRouteProps) {
  const { role, isAuthenticated } = useUserRole();

  if (!isAuthenticated) {
    return <Navigate to={fallbackPath} replace />;
  }

  if (!requiredRoles.includes(role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
}

// Usage in routing
<Route 
  path="/admin/*" 
  element={
    <ProtectedRoute requiredRoles={['admin']}>
      <AdminDashboard />
    </ProtectedRoute>
  } 
/>

<Route 
  path="/sponsor/*" 
  element={
    <ProtectedRoute requiredRoles={['sponsor', 'admin']}>
      <SponsorDashboard />
    </ProtectedRoute>
  } 
/>
```

## 🔗 API Integration

### **Enhanced API Client**

```typescript
// utils/apiClient.ts
class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('access_token');
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        throw new Error('Authentication required');
      }
      
      if (response.status === 403) {
        throw new Error('Access denied - insufficient permissions');
      }

      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Authentication
  async requestOTP(phone: string) {
    return this.request('/auth/request-otp', {
      method: 'POST',
      body: JSON.stringify({ phone }),
    });
  }

  async verifyOTP(phone: string, code: string) {
    const response = await this.request<{
      access_token: string;
      user_id: number;
      phone: string;
      role: string;
    }>('/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ phone, code }),
    });

    // Store token and update client
    this.token = response.access_token;
    localStorage.setItem('access_token', response.access_token);

    return response;
  }

  // User endpoints
  async getUserProfile() {
    return this.request('/user/profile');
  }

  async getUserEntries() {
    return this.request('/user/entries');
  }

  async getUserStats() {
    return this.request('/user/stats');
  }

  async getAvailableContests() {
    return this.request('/user/contests/available');
  }

  async enterContest(contestId: number) {
    return this.request(`/user/contests/${contestId}/enter`, {
      method: 'POST',
    });
  }

  // Sponsor endpoints
  async getSponsorProfile() {
    return this.request('/sponsor/profile');
  }

  async updateSponsorProfile(data: any) {
    return this.request('/sponsor/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async getSponsorContests() {
    return this.request('/sponsor/contests');
  }

  async createSponsorContest(contestData: any) {
    return this.request('/sponsor/contests', {
      method: 'POST',
      body: JSON.stringify(contestData),
    });
  }

  async getSponsorAnalytics() {
    return this.request('/sponsor/analytics');
  }

  async requestSponsorUpgrade(upgradeData: any) {
    return this.request('/sponsor/upgrade-request', {
      method: 'POST',
      body: JSON.stringify(upgradeData),
    });
  }

  // Admin endpoints
  async getAdminContests() {
    return this.request('/admin/contests');
  }

  async approveContest(contestId: number, action: 'approved' | 'rejected', reason?: string) {
    return this.request(`/admin/contests/${contestId}/approve`, {
      method: 'PUT',
      body: JSON.stringify({ action, reason }),
    });
  }

  async assignUserRole(userId: number, role: string, reason: string) {
    return this.request(`/admin/users/${userId}/assign-role`, {
      method: 'POST',
      body: JSON.stringify({ role, reason }),
    });
  }
}

export const apiClient = new ApiClient(process.env.REACT_APP_API_URL || 'http://localhost:8000');
```

## 🎨 Role-Specific Components

### **User Dashboard**

```typescript
// components/UserDashboard.tsx
import React, { useEffect, useState } from 'react';
import { apiClient } from '../utils/apiClient';

interface UserStats {
  total_entries: number;
  winning_entries: number;
  active_entries: number;
  available_contests: number;
  win_rate: number;
}

export function UserDashboard() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [availableContests, setAvailableContests] = useState([]);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const [statsData, contestsData] = await Promise.all([
        apiClient.getUserStats(),
        apiClient.getAvailableContests()
      ]);
      
      setStats(statsData);
      setAvailableContests(contestsData);
    } catch (error) {
      console.error('Failed to load user data:', error);
    }
  };

  const handleEnterContest = async (contestId: number) => {
    try {
      await apiClient.enterContest(contestId);
      // Refresh data
      loadUserData();
      alert('Successfully entered contest!');
    } catch (error) {
      alert('Failed to enter contest. Please try again.');
    }
  };

  return (
    <div className="user-dashboard">
      <h1>My Dashboard</h1>
      
      {/* User Statistics */}
      {stats && (
        <div className="stats-grid">
          <StatCard title="Total Entries" value={stats.total_entries} />
          <StatCard title="Wins" value={stats.winning_entries} />
          <StatCard title="Active Entries" value={stats.active_entries} />
          <StatCard title="Win Rate" value={`${stats.win_rate}%`} />
        </div>
      )}

      {/* Available Contests */}
      <section>
        <h2>Available Contests</h2>
        <div className="contests-grid">
          {availableContests.map((contest: any) => (
            <ContestCard
              key={contest.id}
              contest={contest}
              onEnter={() => handleEnterContest(contest.id)}
              userHasEntered={contest.user_has_entered}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
```

### **Sponsor Dashboard**

```typescript
// components/SponsorDashboard.tsx
import React, { useEffect, useState } from 'react';
import { apiClient } from '../utils/apiClient';

export function SponsorDashboard() {
  const [profile, setProfile] = useState(null);
  const [contests, setContests] = useState([]);
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    loadSponsorData();
  }, []);

  const loadSponsorData = async () => {
    try {
      const [profileData, contestsData, analyticsData] = await Promise.all([
        apiClient.getSponsorProfile(),
        apiClient.getSponsorContests(),
        apiClient.getSponsorAnalytics()
      ]);
      
      setProfile(profileData);
      setContests(contestsData);
      setAnalytics(analyticsData);
    } catch (error) {
      console.error('Failed to load sponsor data:', error);
    }
  };

  return (
    <div className="sponsor-dashboard">
      <h1>Sponsor Dashboard</h1>
      
      {/* Company Profile Section */}
      <section>
        <h2>Company Profile</h2>
        {profile ? (
          <CompanyProfileCard profile={profile} onUpdate={loadSponsorData} />
        ) : (
          <div>Loading profile...</div>
        )}
      </section>

      {/* Analytics Section */}
      {analytics && (
        <section>
          <h2>Analytics Overview</h2>
          <div className="analytics-grid">
            <StatCard title="Total Contests" value={analytics.total_contests} />
            <StatCard title="Approved" value={analytics.approved_contests} />
            <StatCard title="Pending" value={analytics.pending_contests} />
            <StatCard title="Total Entries" value={analytics.total_entries} />
          </div>
        </section>
      )}

      {/* Contests Management */}
      <section>
        <div className="section-header">
          <h2>My Contests</h2>
          <button 
            className="btn-primary"
            onClick={() => window.location.href = '/sponsor/contests/create'}
          >
            Create New Contest
          </button>
        </div>
        
        <div className="contests-list">
          {contests.map((contest: any) => (
            <SponsorContestCard
              key={contest.id}
              contest={contest}
              onUpdate={loadSponsorData}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
```

### **Role Upgrade Component**

```typescript
// components/RoleUpgradeForm.tsx
import React, { useState } from 'react';
import { apiClient } from '../utils/apiClient';

export function RoleUpgradeForm() {
  const [formData, setFormData] = useState({
    company_name: '',
    website_url: '',
    industry: '',
    description: '',
    verification_document_url: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await apiClient.requestSponsorUpgrade({
        target_role: 'sponsor',
        ...formData
      });

      alert('Sponsor upgrade request submitted! Please wait for admin approval.');
      // Redirect or refresh
      window.location.reload();
    } catch (error) {
      alert('Failed to submit upgrade request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="role-upgrade-form">
      <h2>Upgrade to Sponsor Account</h2>
      <p>Create contests and manage your company profile.</p>

      <div className="form-group">
        <label>Company Name *</label>
        <input
          type="text"
          required
          value={formData.company_name}
          onChange={(e) => setFormData({...formData, company_name: e.target.value})}
        />
      </div>

      <div className="form-group">
        <label>Website URL</label>
        <input
          type="url"
          value={formData.website_url}
          onChange={(e) => setFormData({...formData, website_url: e.target.value})}
        />
      </div>

      <div className="form-group">
        <label>Industry</label>
        <input
          type="text"
          value={formData.industry}
          onChange={(e) => setFormData({...formData, industry: e.target.value})}
        />
      </div>

      <div className="form-group">
        <label>Company Description</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
        />
      </div>

      <button type="submit" disabled={loading} className="btn-primary">
        {loading ? 'Submitting...' : 'Request Sponsor Upgrade'}
      </button>
    </form>
  );
}
```

## 🔄 Migration Strategy

### **Existing User Migration**

```typescript
// utils/userMigration.ts
export async function migrateExistingUsers() {
  // Check if user has role information
  const token = localStorage.getItem('access_token');
  if (!token) return;

  const decoded = decodeToken(token);
  
  // If token doesn't have role, user needs to re-authenticate
  if (!decoded?.role) {
    localStorage.removeItem('access_token');
    window.location.href = '/login?reason=role_update';
    return;
  }

  // Update UI based on new role system
  updateUIForRole(decoded.role);
}

function updateUIForRole(role: string) {
  // Hide/show navigation items
  // Update dashboard components
  // Refresh user permissions
}
```

### **Backward Compatibility**

```typescript
// utils/compatibility.ts
export function isLegacyToken(token: string): boolean {
  const decoded = decodeToken(token);
  return decoded && !decoded.role;
}

export function handleLegacyUser() {
  // Show migration prompt
  // Guide user through role assignment
  // Maintain existing functionality during transition
}
```

## 📱 UI/UX Considerations

### **Role Indicators**

```css
/* Role-based styling */
.user-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.user-badge.admin {
  background: #dc3545;
  color: white;
}

.user-badge.sponsor {
  background: #007bff;
  color: white;
}

.user-badge.user {
  background: #28a745;
  color: white;
}
```

### **Permission States**

```typescript
// components/PermissionGate.tsx
interface PermissionGateProps {
  requiredRoles: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PermissionGate({ 
  requiredRoles, 
  children, 
  fallback = null 
}: PermissionGateProps) {
  const { role } = useUserRole();

  if (!requiredRoles.includes(role)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

// Usage
<PermissionGate 
  requiredRoles={['admin']} 
  fallback={<div>Admin access required</div>}
>
  <AdminOnlyButton />
</PermissionGate>
```

## 🧪 Testing Integration

### **Role-Based Testing**

```typescript
// tests/roleSystem.test.ts
describe('Role System Integration', () => {
  test('Admin can access all features', async () => {
    // Mock admin token
    const adminToken = createMockToken({ role: 'admin' });
    localStorage.setItem('access_token', adminToken);

    render(<App />);
    
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    expect(screen.getByText('User Management')).toBeInTheDocument();
  });

  test('Sponsor can only access sponsor features', async () => {
    const sponsorToken = createMockToken({ role: 'sponsor' });
    localStorage.setItem('access_token', sponsorToken);

    render(<App />);
    
    expect(screen.getByText('Sponsor Dashboard')).toBeInTheDocument();
    expect(screen.queryByText('User Management')).not.toBeInTheDocument();
  });

  test('User upgrade flow works correctly', async () => {
    const userToken = createMockToken({ role: 'user' });
    localStorage.setItem('access_token', userToken);

    render(<RoleUpgradeForm />);
    
    // Fill form and submit
    fireEvent.change(screen.getByLabelText('Company Name'), {
      target: { value: 'Test Company' }
    });
    
    fireEvent.click(screen.getByText('Request Sponsor Upgrade'));
    
    await waitFor(() => {
      expect(mockApiClient.requestSponsorUpgrade).toHaveBeenCalled();
    });
  });
});
```

## 📚 API Reference Summary

### **Authentication Endpoints**
- `POST /auth/request-otp` - Request OTP
- `POST /auth/verify-otp` - Verify OTP (returns role info)

### **User Endpoints**
- `GET /user/profile` - User profile
- `GET /user/contests/available` - Available contests
- `POST /user/contests/{id}/enter` - Enter contest
- `GET /user/entries` - User's entries
- `GET /user/stats` - User statistics

### **Sponsor Endpoints**
- `GET /sponsor/profile` - Sponsor profile
- `PUT /sponsor/profile` - Update profile
- `GET /sponsor/contests` - Sponsor's contests
- `POST /sponsor/contests` - Create contest
- `GET /sponsor/analytics` - Sponsor analytics
- `POST /sponsor/upgrade-request` - Request sponsor role

### **Admin Endpoints**
- `GET /admin/contests` - All contests
- `PUT /admin/contests/{id}/approve` - Approve/reject contest
- `POST /admin/users/{id}/assign-role` - Assign user role

## 🚀 Deployment Checklist

### **Frontend Updates Required**
- [ ] Update authentication flow to handle roles
- [ ] Implement role-based navigation
- [ ] Create role-specific dashboards
- [ ] Add permission gates for UI components
- [ ] Update API client with new endpoints
- [ ] Test all role transitions
- [ ] Implement user migration strategy

### **Environment Configuration**
```env
# Frontend environment variables
REACT_APP_API_URL=https://staging-api.contestlet.com
REACT_APP_ENABLE_ROLE_SYSTEM=true
REACT_APP_DEFAULT_ROLE=user
```

## 🎯 Success Metrics

- **User Engagement**: Role-specific feature usage
- **Conversion Rate**: User → Sponsor upgrades
- **Admin Efficiency**: Contest approval times
- **Security**: Zero unauthorized access incidents
- **Performance**: Role-based page load times

---

**This integration guide provides everything needed to implement the multi-tier role system in your frontend application!** 🌟
