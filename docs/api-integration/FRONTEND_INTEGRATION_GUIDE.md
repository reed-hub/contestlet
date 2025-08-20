# 🔗 Contestlet API - Frontend Integration Guide

This guide provides everything you need to integrate a frontend application with the Contestlet API.

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Authentication Flow](#authentication-flow)
- [API Endpoints](#api-endpoints)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)
- [Security Best Practices](#security-best-practices)
- [Testing & Development](#testing--development)

---

## ⚠️ **BREAKING CHANGES - SMS Notifications**

**Important updates for SMS winner notifications:**

### 🛑 **Security Changes (Action Required)**
1. **Admin JWT Required**: Legacy admin tokens **NO LONGER WORK** for SMS notifications
   - Must authenticate via OTP to get admin JWT: `POST /auth/request-otp` → `POST /auth/verify-otp`
   - Update admin login flow to use OTP authentication
   
2. **Rate Limiting**: SMS notifications are now rate limited (5 per 5 minutes per admin)
   - Handle `429 Too Many Requests` responses
   - Show appropriate user feedback when rate limited

3. **New Response Format**: SMS notification responses include additional fields
   - `test_mode`, `notification_id`, `twilio_sid` fields added
   - Update response parsing code accordingly

### ✨ **New Features Available**
- **Test Mode**: Add `test_mode: true` to simulate SMS without sending
- **Audit Trail**: Each SMS gets a `notification_id` for tracking
- **Enhanced Error Handling**: Specific error messages for different failure cases

---

## 🚀 Quick Start

### Base Configuration
```javascript
const API_BASE_URL = 'http://localhost:8000';  // Development
// const API_BASE_URL = 'https://your-domain.com';  // Production

const apiConfig = {
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds
};
```

### Basic API Client Setup
```javascript
class ContestletAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('contestlet_token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('contestlet_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('contestlet_token');
  }
}

const api = new ContestletAPI();
```

---

## 🔐 Authentication Flow (Twilio Verify API)

### 1. Phone Number Verification (OTP)

The authentication system uses **Twilio Verify API** for secure SMS-based verification.

#### Step 1: Request OTP
```javascript
async function requestOTP(phoneNumber) {
  try {
    // Format phone number (API accepts various US formats)
    const cleanPhone = phoneNumber.replace(/\D/g, ''); // Remove non-digits
    const formattedPhone = cleanPhone.length === 10 ? cleanPhone : cleanPhone;
    
    const response = await api.request('/auth/request-otp', {
      method: 'POST',
      body: JSON.stringify({ phone: formattedPhone }),
    });
    
    return {
      success: true,
      message: response.message,
      retryAfter: response.retry_after,
    };
  } catch (error) {
    // Handle rate limiting
    if (error.message.includes('429')) {
      return {
        success: false,
        error: 'Too many requests. Please wait before requesting another code.',
        rateLimited: true,
      };
    }
    
    return {
      success: false,
      error: error.message,
    };
  }
}

// Usage with real phone number
const result = await requestOTP('18187958204'); // US phone number
if (result.success) {
  console.log('OTP sent successfully via Twilio');
  // Show OTP input form
  // In development: Use code 123456
  // In production: User receives real SMS
} else {
  console.error('Failed to send OTP:', result.error);
  if (result.rateLimited) {
    // Show rate limiting message with retry timer
  }
}
```

#### Step 2: Verify OTP
```javascript
async function verifyOTP(phoneNumber, otpCode) {
  try {
    // Clean and validate inputs
    const cleanPhone = phoneNumber.replace(/\D/g, '');
    const cleanCode = otpCode.replace(/\D/g, '');
    
    if (cleanCode.length !== 6) {
      return {
        success: false,
        message: 'OTP code must be 6 digits',
      };
    }
    
    const response = await api.request('/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ 
        phone: cleanPhone, 
        code: cleanCode 
      }),
    });
    
    if (response.success) {
      api.setToken(response.access_token);
      return {
        success: true,
        token: response.access_token,
        userId: response.user_id,
        message: response.message,
      };
    } else {
      return {
        success: false,
        message: response.message,
      };
    }
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

// Usage with Twilio Verify
const result = await verifyOTP('18187958204', '123456'); // Use 123456 in development
if (result.success) {
  console.log('User authenticated via Twilio Verify:', result.userId);
  // User is now authenticated with JWT token
  // Redirect to dashboard or main app
} else {
  console.error('Twilio verification failed:', result.message);
  // Common error messages:
  // - "Invalid verification code"
  // - "Verification code has expired. Please request a new one."
  // - "Too many verification attempts. Please wait before trying again."
}
```

### 📱 Development vs Production

```javascript
// Development mode (USE_MOCK_SMS=true)
const devResult = await requestOTP('18187958204');
// Always use code: 123456

// Production mode (USE_MOCK_SMS=false)  
const prodResult = await requestOTP('18187958204');
// User receives real SMS with random 6-digit code
```

### 2. Token Management
```javascript
// Check if user is authenticated
function isAuthenticated() {
  return !!api.token;
}

// Auto-refresh token (implement based on your needs)
function setupTokenRefresh() {
  // JWT tokens expire after 24 hours by default
  // Implement refresh logic or re-authentication
}

// Logout
function logout() {
  api.clearToken();
  // Redirect to login page
  window.location.href = '/login';
}
```

---

## 📍 API Endpoints

### Contest Management

#### Get Active Contests
```javascript
async function getActiveContests(filters = {}) {
  const params = new URLSearchParams();
  
  if (filters.location) params.append('location', filters.location);
  if (filters.page) params.append('page', filters.page);
  if (filters.size) params.append('size', filters.size);
  
  const queryString = params.toString();
  const endpoint = `/contests/active${queryString ? `?${queryString}` : ''}`;
  
  return await api.request(endpoint);
}

// Usage
const contests = await getActiveContests({ 
  location: 'San Francisco', 
  page: 1, 
  size: 10 
});
```

#### Find Nearby Contests
```javascript
async function getNearbyContests(latitude, longitude, radius = 25) {
  const params = new URLSearchParams({
    lat: latitude,
    lng: longitude,
    radius: radius,
  });
  
  return await api.request(`/contests/nearby?${params}`);
}

// Usage with Geolocation API
function findNearbyContests() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(async (position) => {
      const { latitude, longitude } = position.coords;
      const contests = await getNearbyContests(latitude, longitude, 25);
      displayContests(contests.contests);
    });
  }
}
```

#### Enter a Contest
```javascript
async function enterContest(contestId) {
  try {
    const response = await api.request(`/contests/${contestId}/enter`, {
      method: 'POST',
    });
    
    return {
      success: true,
      entry: response,
    };
  } catch (error) {
    // Handle specific error cases
    if (error.message.includes('409')) {
      return {
        success: false,
        error: 'already_entered',
        message: 'You have already entered this contest',
      };
    } else if (error.message.includes('400')) {
      return {
        success: false,
        error: 'contest_expired',
        message: 'This contest has expired',
      };
    }
    
    return {
      success: false,
      error: 'unknown',
      message: error.message,
    };
  }
}
```

#### Get User's Entries
```javascript
async function getUserEntries() {
  return await api.request('/entries/me');
}

// Usage
const userEntries = await getUserEntries();
console.log(`User has entered ${userEntries.length} contests`);
```

### Admin Operations

For admin users managing contests and viewing entries, additional endpoints are available that require admin authentication.

#### Admin Authentication Setup

##### Option 1: OTP-Based Admin Authentication (Recommended)
```javascript
// Admin authentication using OTP
async function authenticateAdmin(adminPhone, otpCode) {
  try {
    // Step 1: Request OTP (if needed)
    const otpResponse = await fetch('http://localhost:8000/auth/request-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: adminPhone }),
    });

    // Step 2: Verify OTP and get admin JWT
    const verifyResponse = await fetch('http://localhost:8000/auth/verify-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: adminPhone, code: otpCode }),
    });

    const result = await verifyResponse.json();
    
    if (result.success) {
      // Check if user has admin role
      const userInfo = await fetch('http://localhost:8000/auth/me', {
        headers: { 'Authorization': `Bearer ${result.access_token}` },
      });
      const userData = await userInfo.json();
      
      if (userData.role === 'admin') {
        return {
          success: true,
          adminToken: result.access_token,
          userId: result.user_id,
          phone: userData.phone,
        };
      } else {
        throw new Error('User does not have admin privileges');
      }
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

// Usage example
const adminAuth = await authenticateAdmin('18187958204', '123456');
if (adminAuth.success) {
  console.log('Admin authenticated:', adminAuth.phone);
  // Use adminAuth.adminToken for admin API calls
}
```

##### Option 2: Legacy Admin Token (Deprecated)
```javascript
const adminToken = 'contestlet-admin-super-secret-token-change-in-production';
```

#### Admin API Client
```javascript
// Set up admin API client
class AdminAPI {
  constructor(baseURL = 'http://localhost:8000', adminToken) {
    this.baseURL = baseURL;
    this.adminToken = adminToken;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.adminToken}`,
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`Admin API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }
}

// Initialize admin client with OTP-based token
const adminAPI = new AdminAPI('http://localhost:8000', adminAuth.adminToken);
```

#### View Contest Entries
```javascript
async function getContestEntries(contestId) {
  try {
    const entries = await adminAPI.request(`/admin/contests/${contestId}/entries`);
    
    return {
      success: true,
      entries: entries,
      count: entries.length,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

// Usage
const result = await getContestEntries(1);
if (result.success) {
  console.log(`Found ${result.count} entries for contest`);
  result.entries.forEach(entry => {
    console.log(`Entry ${entry.id}: User ${entry.user_id} (${entry.phone_number})`);
  });
} else {
  console.error('Failed to get entries:', result.error);
}
```

#### Create Contest
```javascript
async function createContest(contestData) {
  const fullContestData = {
    name: contestData.name,
    description: contestData.description,
    location: contestData.location,
    latitude: contestData.latitude,
    longitude: contestData.longitude,
    start_time: contestData.start_time,
    end_time: contestData.end_time,
    prize_description: contestData.prize_description,
    active: contestData.active,
    official_rules: {
      eligibility_text: "Must be 18+ and US resident",
      sponsor_name: "Your Company",
      start_date: contestData.start_time,
      end_date: contestData.end_time,
      prize_value_usd: contestData.prize_value,
      terms_url: "https://yoursite.com/terms"
    }
  };

  return await adminAPI.request('/admin/contests', {
    method: 'POST',
    body: JSON.stringify(fullContestData),
  });
}

// Usage
const newContest = await createContest({
  name: "Summer Giveaway",
  description: "Win amazing prizes this summer!",
  location: "San Francisco, CA",
  latitude: 37.7749,
  longitude: -122.4194,
  start_time: "2025-08-20T10:00:00",
  end_time: "2025-08-27T10:00:00",
  prize_description: "$1000 Cash Prize",
  prize_value: 1000.0,
  active: true
});
```

#### Select Contest Winner
```javascript
async function selectWinner(contestId) {
  try {
    const result = await adminAPI.request(`/admin/contests/${contestId}/select-winner`, {
      method: 'POST',
    });
    
    return {
      success: result.success,
      message: result.message,
      winnerEntryId: result.winner_entry_id,
      winnerPhone: result.winner_user_phone,
      totalEntries: result.total_entries,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

// Usage
const winnerResult = await selectWinner(1);
if (winnerResult.success) {
  console.log(`Winner selected! Entry ID: ${winnerResult.winnerEntryId}`);
  console.log(`Winner phone: ${winnerResult.winnerPhone}`);
} else {
  console.error('Winner selection failed:', winnerResult.error);
}
```

#### Notify Winner via SMS
```javascript
async function notifyWinner(contestId, entryId, customMessage, testMode = false) {
  try {
    const notificationData = {
      entry_id: entryId,
      message: customMessage || "🎉 Congratulations! You're the winner! We'll contact you soon with details about claiming your prize.",
      test_mode: testMode  // ✨ NEW: Set to true for testing without sending real SMS
    };

    const result = await adminAPI.request(`/admin/contests/${contestId}/notify-winner`, {
      method: 'POST',
      body: JSON.stringify(notificationData),
    });
    
    return {
      success: result.success,
      message: result.message,
      entryId: result.entry_id,
      contestId: result.contest_id,
      winnerPhone: result.winner_phone, // Masked for privacy
      smsStatus: result.sms_status,
      testMode: result.test_mode,        // ✨ NEW: Indicates if this was a test
      notificationId: result.notification_id, // ✨ NEW: Database ID for audit trail
      twilioSid: result.twilio_sid,      // ✨ NEW: Twilio message ID (if real SMS)
      sentAt: result.notification_sent_at,
    };
  } catch (error) {
    // ⚠️ IMPORTANT: Handle new error cases
    if (error.status === 429) {
      return {
        success: false,
        error: "Rate limited: Too many SMS notifications. Please wait.",
        rateLimited: true,
      };
    } else if (error.status === 403 && error.message?.includes('JWT')) {
      return {
        success: false,
        error: "Admin JWT required. Please re-authenticate via OTP.",
        authenticationRequired: true,
      };
    } else {
      return {
        success: false,
        error: error.message,
      };
    }
  }
}

// Usage examples
const smsResult = await notifyWinner(
  1, 
  12, 
  "🎊 Amazing news! You've won our Summer Contest! Check your email for prize details."
);

if (smsResult.success) {
  console.log(`SMS sent to winner: ${smsResult.winnerPhone}`);
  console.log(`SMS status: ${smsResult.smsStatus}`);
} else {
  console.error('Failed to send SMS:', smsResult.error);
}

// Combined workflow: Select winner and notify
async function selectAndNotifyWinner(contestId, customMessage) {
  const winnerResult = await selectWinner(contestId);
  
  if (winnerResult.success) {
    const smsResult = await notifyWinner(
      contestId, 
      winnerResult.winnerEntryId, 
      customMessage
    );
    
    return {
      winnerSelected: true,
      smsNotified: smsResult.success,
      winnerEntryId: winnerResult.winnerEntryId,
      winnerPhone: smsResult.winnerPhone,
      smsStatus: smsResult.smsStatus,
    };
  }
  
  return {
    winnerSelected: false,
    error: winnerResult.error,
  };
}
```

---

## ⚠️ Error Handling

### Comprehensive Error Handler
```javascript
function handleAPIError(error, context = '') {
  console.error(`API Error in ${context}:`, error);
  
  // Parse error message for status codes
  const statusMatch = error.message.match(/(\d{3})/);
  const status = statusMatch ? parseInt(statusMatch[1]) : null;
  
  switch (status) {
    case 400:
      return 'Invalid request. Please check your input.';
    case 401:
      api.clearToken();
      window.location.href = '/login';
      return 'Session expired. Please log in again.';
    case 403:
      return 'Access denied. You do not have permission.';
    case 404:
      return 'Resource not found.';
    case 409:
      return 'Conflict. You may have already performed this action.';
    case 429:
      return 'Too many requests. Please wait before trying again.';
    case 500:
      return 'Server error. Please try again later.';
    default:
      return 'An unexpected error occurred. Please try again.';
  }
}

// Usage in components
try {
  const result = await enterContest(contestId);
} catch (error) {
  const userMessage = handleAPIError(error, 'contest entry');
  showErrorMessage(userMessage);
}
```

### Rate Limiting Handling
```javascript
async function requestOTPWithRetry(phoneNumber, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestOTP(phoneNumber);
    } catch (error) {
      if (error.message.includes('429')) {
        const retryAfter = extractRetryAfter(error) || 60;
        if (attempt < maxRetries) {
          console.log(`Rate limited. Retrying in ${retryAfter} seconds...`);
          await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
          continue;
        }
      }
      throw error;
    }
  }
}
```

---

## 💻 Code Examples

### React Integration Example

#### Authentication Hook
```javascript
// hooks/useAuth.js
import { useState, useEffect, createContext, useContext } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('contestlet_token');
    if (token) {
      api.setToken(token);
      // Optionally verify token validity
      setUser({ token }); // Add user data as needed
    }
    setLoading(false);
  }, []);

  const login = async (phone, otp) => {
    const result = await verifyOTP(phone, otp);
    if (result.success) {
      setUser({ 
        token: result.token, 
        userId: result.userId 
      });
      return true;
    }
    return false;
  };

  const logout = () => {
    api.clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

#### Contest List Component
```javascript
// components/ContestList.jsx
import { useState, useEffect } from 'react';

function ContestList() {
  const [contests, setContests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadContests();
  }, []);

  const loadContests = async () => {
    try {
      setLoading(true);
      const response = await getActiveContests();
      setContests(response.contests);
    } catch (err) {
      setError(handleAPIError(err, 'loading contests'));
    } finally {
      setLoading(false);
    }
  };

  const handleEnterContest = async (contestId) => {
    try {
      const result = await enterContest(contestId);
      if (result.success) {
        alert('Successfully entered contest!');
        // Update UI or reload contests
      } else {
        alert(result.message);
      }
    } catch (err) {
      alert(handleAPIError(err, 'entering contest'));
    }
  };

  if (loading) return <div>Loading contests...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="contest-list">
      {contests.map(contest => (
        <div key={contest.id} className="contest-card">
          <h3>{contest.name}</h3>
          <p>{contest.description}</p>
          <p>Prize: {contest.prize_description}</p>
          {contest.distance_miles && (
            <p>{contest.distance_miles} miles away</p>
          )}
          <button onClick={() => handleEnterContest(contest.id)}>
            Enter Contest
          </button>
        </div>
      ))}
    </div>
  );
}
```

### Vue.js Integration Example
```javascript
// stores/contestStore.js (Pinia)
import { defineStore } from 'pinia';

export const useContestStore = defineStore('contest', {
  state: () => ({
    contests: [],
    userEntries: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchActiveContests(filters = {}) {
      this.loading = true;
      try {
        const response = await getActiveContests(filters);
        this.contests = response.contests;
      } catch (error) {
        this.error = handleAPIError(error, 'fetching contests');
      } finally {
        this.loading = false;
      }
    },

    async enterContest(contestId) {
      try {
        const result = await enterContest(contestId);
        if (result.success) {
          await this.fetchUserEntries(); // Refresh entries
          return true;
        }
        return false;
      } catch (error) {
        this.error = handleAPIError(error, 'entering contest');
        return false;
      }
    },

    async fetchUserEntries() {
      try {
        this.userEntries = await getUserEntries();
      } catch (error) {
        this.error = handleAPIError(error, 'fetching user entries');
      }
    },
  },
});
```

---

## 🔒 Security Best Practices

### Token Security
```javascript
// 1. Secure token storage (consider using secure HTTP-only cookies for production)
class SecureTokenManager {
  static setToken(token) {
    // For development
    localStorage.setItem('contestlet_token', token);
    
    // For production - consider using secure cookies
    // document.cookie = `contestlet_token=${token}; secure; httpOnly; sameSite=strict`;
  }

  static getToken() {
    return localStorage.getItem('contestlet_token');
  }

  static clearToken() {
    localStorage.removeItem('contestlet_token');
  }
}

// 2. Request interceptor for automatic token attachment
api.request = async function(endpoint, options = {}) {
  const token = SecureTokenManager.getToken();
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  // Add CSRF protection if needed
  // config.headers['X-CSRF-Token'] = getCSRFToken();

  const response = await fetch(`${this.baseURL}${endpoint}`, config);
  
  // Handle token expiration
  if (response.status === 401) {
    SecureTokenManager.clearToken();
    window.location.href = '/login';
  }
  
  return response;
};
```

### Input Validation
```javascript
// Phone number validation
function validatePhoneNumber(phone) {
  // Remove all non-digit characters
  const cleaned = phone.replace(/\D/g, '');
  
  // Check if it's a valid US phone number
  if (cleaned.length === 10) {
    return `1${cleaned}`; // Add country code
  } else if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return cleaned;
  }
  
  throw new Error('Invalid phone number format');
}

// OTP code validation
function validateOTPCode(code) {
  const cleaned = code.replace(/\D/g, '');
  if (cleaned.length !== 6) {
    throw new Error('OTP code must be 6 digits');
  }
  return cleaned;
}
```

---

## 🧪 Testing & Development

### Development Setup
```javascript
// config/development.js
export const developmentConfig = {
  API_BASE_URL: 'http://localhost:8000',
  MOCK_SMS: true, // Will show OTP codes in console
  DEBUG_MODE: true,
};

// Mock OTP for development
if (developmentConfig.MOCK_SMS) {
  window.mockOTP = '123456'; // Use this code for development
}
```

### API Testing Utility
```javascript
// utils/apiTester.js
export class APITester {
  static async testEndpoints() {
    console.log('🧪 Testing Contestlet API endpoints...');
    
    try {
      // Test health check
      const health = await api.request('/');
      console.log('✅ Health check:', health.status);
      
      // Test active contests
      const contests = await getActiveContests();
      console.log('✅ Active contests:', contests.total);
      
      // Test OTP request (development only)
      if (developmentConfig.MOCK_SMS) {
        const otpResult = await requestOTP('5551234567');
        console.log('✅ OTP request:', otpResult.success);
      }
      
      console.log('🎉 All API tests passed!');
    } catch (error) {
      console.error('❌ API test failed:', error);
    }
  }
}

// Run tests in development
if (developmentConfig.DEBUG_MODE) {
  APITester.testEndpoints();
}
```

### Error Monitoring
```javascript
// utils/errorMonitoring.js
export function setupErrorMonitoring() {
  // Log API errors for debugging
  const originalRequest = api.request;
  api.request = async function(...args) {
    try {
      return await originalRequest.apply(this, args);
    } catch (error) {
      // Log to console in development
      if (developmentConfig.DEBUG_MODE) {
        console.group('🔥 API Error');
        console.error('Endpoint:', args[0]);
        console.error('Error:', error);
        console.groupEnd();
      }
      
      // Send to monitoring service in production
      // sendToMonitoring({ endpoint: args[0], error: error.message });
      
      throw error;
    }
  };
}
```

---

## 📚 Additional Resources

### Environment Variables
```bash
# Frontend .env file
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
REACT_APP_DEBUG_MODE=true
```

### TypeScript Definitions
```typescript
// types/api.ts
export interface Contest {
  id: number;
  name: string;
  description?: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  start_time: string;
  end_time: string;
  prize_description?: string;
  active: boolean;
  created_at: string;
  distance_miles?: number;
}

export interface ContestListResponse {
  contests: Contest[];
  total: number;
  page: number;
  size: number;
}

export interface OTPVerificationResponse {
  success: boolean;
  message: string;
  access_token?: string;
  token_type: string;
  user_id?: number;
}

export interface AdminEntryResponse {
  id: number;
  contest_id: number;
  user_id: number;
  phone_number: string;
  created_at: string;
  selected: boolean;
}
```

### API Documentation Links
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/

---

## 🎯 Quick Checklist

### ✅ Frontend Integration Checklist
- [ ] Set up API client with base URL and headers
- [ ] Implement phone number validation
- [ ] Create OTP request/verification flow
- [ ] Set up token storage and management
- [ ] Implement contest listing and search
- [ ] Add contest entry functionality
- [ ] Handle all error cases appropriately
- [ ] Add loading states and user feedback
- [ ] Test with rate limiting scenarios
- [ ] Implement logout functionality
- [ ] Add geolocation for nearby contests
- [ ] Set up error monitoring

### 🚀 Ready for Production
Once you've implemented the above checklist, your frontend will be fully integrated with the Contestlet API and ready for users to start discovering and entering contests!

For questions or additional support, refer to the API documentation at `/docs` or check the server logs for detailed error information.
