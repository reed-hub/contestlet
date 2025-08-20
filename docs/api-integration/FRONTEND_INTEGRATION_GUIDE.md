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

## ⚠️ **IMPORTANT UPDATES**

### 🌍 **NEW: Timezone Support**

**Comprehensive timezone handling now available:**

#### 🎯 **Key Changes**
1. **Admin Timezone Preferences**: Admins can set preferred timezone for contest creation
2. **UTC Storage**: All times stored as UTC in database with timezone metadata
3. **Local Display**: Contest times shown in admin's preferred timezone
4. **Automatic Conversion**: Frontend must convert times to/from UTC

#### 🔧 **Implementation Required**
1. **Set Up Timezone Utilities**: Use provided timezone conversion functions
2. **Admin Profile Integration**: Add timezone preferences page
3. **Contest Form Updates**: Convert admin input to UTC before API calls
4. **Display Logic**: Show times in admin's preferred timezone

### 🚨 **SMS Notifications Security Updates**

**Important updates for SMS winner notifications:**

#### 🛑 **Security Changes (Action Required)**
1. **Admin JWT Required**: Legacy admin tokens **NO LONGER WORK** for SMS notifications
   - Must authenticate via OTP to get admin JWT: `POST /auth/request-otp` → `POST /auth/verify-otp`
   - Update admin login flow to use OTP authentication
   
2. **Rate Limiting**: SMS notifications are now rate limited (5 per 5 minutes per admin)
   - Handle `429 Too Many Requests` responses
   - Show appropriate user feedback when rate limited

3. **New Response Format**: SMS notification responses include additional fields
   - `test_mode`, `notification_id`, `twilio_sid` fields added
   - Update response parsing code accordingly

#### ✨ **New Features Available**
- **Test Mode**: Add `test_mode: true` to simulate SMS without sending
- **Audit Trail**: Each SMS gets a `notification_id` for tracking
- **Enhanced Error Handling**: Specific error messages for different failure cases
- **Interaction History**: View complete SMS history per user
- **Multiple SMS Types**: Winners, reminders, and announcements

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

## 🌍 Timezone Handling

### **Overview**
Contestlet uses a timezone-aware system where:
- **All times stored as UTC** in the database
- **Admin interface displays times** in admin's preferred timezone  
- **Contest creation accepts times** in admin's timezone
- **System automatically converts** between timezones

### **Admin Timezone Preferences**

#### **Set Up Admin Timezone Preferences**
```javascript
// Get supported timezones list
async function getSupportedTimezones() {
  const response = await api.request('/admin/profile/timezones');
  return response.timezones; // Array of timezone objects
}

// Set admin timezone preferences
async function setAdminTimezone(timezone, autoDetect = false) {
  const preferences = {
    timezone: timezone,           // e.g., "America/New_York"
    timezone_auto_detect: autoDetect
  };
  
  const response = await adminAPI.request('/admin/profile/timezone', {
    method: 'POST',
    body: JSON.stringify(preferences)
  });
  
  return response;
}

// Get current admin timezone preferences
async function getAdminTimezone() {
  return await adminAPI.request('/admin/profile/timezone');
}
```

#### **Admin Profile Component Example**
```jsx
function AdminTimezoneSettings() {
  const [timezones, setTimezones] = useState([]);
  const [preferences, setPreferences] = useState(null);
  const [selectedTimezone, setSelectedTimezone] = useState('UTC');

  useEffect(() => {
    loadTimezones();
    loadPreferences();
  }, []);

  const loadTimezones = async () => {
    const data = await getSupportedTimezones();
    setTimezones(data);
  };

  const loadPreferences = async () => {
    try {
      const prefs = await getAdminTimezone();
      setPreferences(prefs);
      setSelectedTimezone(prefs.timezone);
    } catch (error) {
      // Admin hasn't set preferences yet
      setPreferences({ timezone: 'UTC', timezone_auto_detect: true });
    }
  };

  const saveTimezone = async () => {
    const updated = await setAdminTimezone(selectedTimezone, false);
    setPreferences(updated);
    showSuccess('Timezone preferences saved!');
  };

  return (
    <div className="timezone-settings">
      <h3>🌍 Timezone Preferences</h3>
      <p>Set your preferred timezone for contest creation and viewing</p>
      
      <div className="timezone-selector">
        <label>Preferred Timezone:</label>
        <select 
          value={selectedTimezone}
          onChange={(e) => setSelectedTimezone(e.target.value)}
        >
          {timezones.map(tz => (
            <option key={tz.timezone} value={tz.timezone}>
              {tz.display_name} ({tz.utc_offset})
            </option>
          ))}
        </select>
      </div>

      <div className="timezone-preview">
        <p><strong>Current time in your timezone:</strong></p>
        <p>{getCurrentTimeInTimezone(selectedTimezone)}</p>
      </div>

      <button onClick={saveTimezone}>Save Timezone Preferences</button>
    </div>
  );
}
```

### **Timezone Conversion Utilities**

#### **Essential Conversion Functions**
```javascript
// Convert datetime-local input to UTC for API
function datetimeLocalToUTC(datetimeLocal, adminTimezone) {
  // datetimeLocal: "2024-01-15T14:30" (from datetime-local input)
  // adminTimezone: "America/New_York" (from admin preferences)
  
  const localDateTime = moment.tz(datetimeLocal, adminTimezone);
  return localDateTime.utc().format('YYYY-MM-DDTHH:mm:ss[Z]');
}

// Convert UTC datetime to admin's timezone for display
function utcToDatetimeLocal(utcDateTime, adminTimezone) {
  // utcDateTime: "2024-01-15T19:30:00Z" (from API)
  // adminTimezone: "America/New_York" (from admin preferences)
  
  const utcMoment = moment.utc(utcDateTime);
  return utcMoment.tz(adminTimezone).format('YYYY-MM-DDTHH:mm');
}

// Get current time in specific timezone
function getCurrentTimeInTimezone(timezone) {
  return moment().tz(timezone).format('MMMM DD, YYYY [at] h:mm A z');
}

// Validate timezone identifier
function isValidTimezone(timezone) {
  const supportedTimezones = [
    'UTC', 'America/New_York', 'America/Chicago', 'America/Denver',
    'America/Los_Angeles', 'America/Phoenix', 'America/Anchorage',
    'Pacific/Honolulu', 'Europe/London', 'Europe/Paris', 'Asia/Tokyo'
    // ... full list from API
  ];
  return supportedTimezones.includes(timezone);
}
```

### **Contest Creation with Timezone Conversion**

#### **Updated Contest Form**
```javascript
async function createContest(formData, adminTimezone) {
  // Convert admin's local times to UTC for API
  const contestData = {
    ...formData,
    start_time: datetimeLocalToUTC(formData.start_time, adminTimezone),
    end_time: datetimeLocalToUTC(formData.end_time, adminTimezone)
  };

  const response = await adminAPI.request('/admin/contests', {
    method: 'POST',
    body: JSON.stringify(contestData)
  });

  return response;
}

// Contest form component
function ContestForm() {
  const [adminTimezone, setAdminTimezone] = useState('UTC');
  const [formData, setFormData] = useState({
    name: '',
    start_time: '',
    end_time: '',
    // ... other fields
  });

  useEffect(() => {
    // Load admin timezone preferences
    loadAdminTimezone();
    // Set default times in admin's timezone
    setDefaultTimes();
  }, []);

  const loadAdminTimezone = async () => {
    try {
      const prefs = await getAdminTimezone();
      setAdminTimezone(prefs.timezone);
    } catch (error) {
      setAdminTimezone('UTC'); // Fallback
    }
  };

  const setDefaultTimes = () => {
    const now = moment().tz(adminTimezone);
    const defaultStart = now.add(1, 'day').startOf('hour');
    const defaultEnd = defaultStart.clone().add(7, 'days');

    setFormData(prev => ({
      ...prev,
      start_time: defaultStart.format('YYYY-MM-DDTHH:mm'),
      end_time: defaultEnd.format('YYYY-MM-DDTHH:mm')
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const contest = await createContest(formData, adminTimezone);
      showSuccess('Contest created successfully!');
      // Redirect or update UI
    } catch (error) {
      showError('Failed to create contest: ' + error.message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="timezone-info">
        🕐 Times will be entered in: <strong>{getTimezoneDisplayName(adminTimezone)}</strong>
        <a href="/admin/profile">Change timezone</a>
      </div>

      <div className="form-group">
        <label>Contest Start Time:</label>
        <input
          type="datetime-local"
          value={formData.start_time}
          onChange={(e) => setFormData({...formData, start_time: e.target.value})}
          required
        />
      </div>

      <div className="form-group">
        <label>Contest End Time:</label>
        <input
          type="datetime-local"
          value={formData.end_time}
          onChange={(e) => setFormData({...formData, end_time: e.target.value})}
          required
        />
      </div>

      {/* ... other form fields */}
      
      <button type="submit">Create Contest</button>
    </form>
  );
}
```

### **Contest Display with Timezone Awareness**

#### **Contest List with Timezone Display**
```javascript
function ContestList() {
  const [contests, setContests] = useState([]);
  const [adminTimezone, setAdminTimezone] = useState('UTC');

  useEffect(() => {
    loadAdminTimezone();
    loadContests();
  }, []);

  const loadContests = async () => {
    const data = await adminAPI.request('/admin/contests');
    setContests(data);
  };

  const formatContestTime = (utcTime) => {
    return utcToDatetimeLocal(utcTime, adminTimezone);
  };

  return (
    <div className="contest-list">
      <h2>Contests (Times in {getTimezoneDisplayName(adminTimezone)})</h2>
      
      {contests.map(contest => (
        <div key={contest.id} className="contest-card">
          <h3>{contest.name}</h3>
          <div className="contest-times">
            <p><strong>Start:</strong> {formatContestTime(contest.start_time)}</p>
            <p><strong>End:</strong> {formatContestTime(contest.end_time)}</p>
            <p><strong>Status:</strong> 
              <span className={`status-${contest.status}`}>
                {contest.status.toUpperCase()}
              </span>
            </p>
          </div>
          
          {/* Show timezone metadata for debugging */}
          {contest.created_timezone && (
            <div className="timezone-metadata">
              <small>Created in: {contest.created_timezone}</small>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

### **Important Implementation Notes**

#### **1. Always Convert to UTC for API Calls**
```javascript
// ❌ Wrong - sending local time to API
const payload = {
  start_time: "2024-01-15T14:30:00"  // Local time, ambiguous
};

// ✅ Correct - convert to UTC first
const payload = {
  start_time: datetimeLocalToUTC("2024-01-15T14:30:00", adminTimezone)
};
```

#### **2. Handle Timezone Changes**
```javascript
// Update display when admin changes timezone
const handleTimezoneChange = async (newTimezone) => {
  await setAdminTimezone(newTimezone);
  setAdminTimezone(newTimezone);
  
  // Refresh contest display with new timezone
  await loadContests();
};
```

#### **3. Provide Clear Timezone Context**
```css
.timezone-info {
  background: #e3f2fd;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 14px;
}

.timezone-info strong {
  color: #1976d2;
}
```

### **Error Handling**

#### **Timezone-Related Errors**
```javascript
const handleTimezoneError = (error) => {
  if (error.message?.includes('Invalid timezone')) {
    return 'Please select a valid timezone from the dropdown';
  }
  
  if (error.message?.includes('timezone preferences')) {
    return 'Could not load timezone preferences. Using UTC as default.';
  }
  
  return 'Timezone operation failed. Please try again.';
};
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

#### View SMS Notification Logs
```javascript
async function getNotificationLogs(contestId = null, notificationType = null, limit = 50) {
  try {
    // Build query parameters
    const params = new URLSearchParams();
    if (contestId) params.append('contest_id', contestId);
    if (notificationType) params.append('notification_type', notificationType);
    if (limit !== 50) params.append('limit', limit);
    
    const queryString = params.toString();
    const endpoint = `/admin/notifications${queryString ? `?${queryString}` : ''}`;
    
    const logs = await adminAPI.request(endpoint);
    
    return {
      success: true,
      logs: logs.map(log => ({
        id: log.id,
        contestId: log.contest_id,
        contestName: log.contest_name,
        userId: log.user_id,
        entryId: log.entry_id,
        message: log.message,
        type: log.notification_type,
        status: log.status, // sent, failed, pending
        twilioSid: log.twilio_sid,
        errorMessage: log.error_message,
        testMode: log.test_mode,
        sentAt: new Date(log.sent_at),
        adminUserId: log.admin_user_id,
        userPhone: log.user_phone, // Masked for privacy
      })),
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

// Usage examples
// Get all notification logs
const allLogs = await getNotificationLogs();

// Get logs for specific contest
const contestLogs = await getNotificationLogs(1);

// Get only winner notifications
const winnerLogs = await getNotificationLogs(null, 'winner');

// Get recent logs for specific contest and type
const recentWinnerLogs = await getNotificationLogs(1, 'winner', 10);

if (allLogs.success) {
  console.log(`Found ${allLogs.logs.length} notification records`);
  allLogs.logs.forEach(log => {
    console.log(`${log.sentAt}: ${log.type} to ${log.userPhone} - ${log.status}`);
  });
}
```

#### SMS Notification Audit Dashboard
```javascript
// Example React component for displaying notification logs
function NotificationLogsDashboard() {
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState({ contestId: '', type: 'all' });
  const [loading, setLoading] = useState(false);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const result = await getNotificationLogs(
        filter.contestId || null,
        filter.type === 'all' ? null : filter.type
      );
      
      if (result.success) {
        setLogs(result.logs);
      } else {
        console.error('Failed to load logs:', result.error);
      }
    } catch (error) {
      console.error('Error loading logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [filter]);

  return (
    <div className="notification-logs">
      <h3>SMS Notification Audit Trail</h3>
      
      {/* Filters */}
      <div className="filters">
        <input
          type="number"
          placeholder="Contest ID (optional)"
          value={filter.contestId}
          onChange={(e) => setFilter({...filter, contestId: e.target.value})}
        />
        <select 
          value={filter.type}
          onChange={(e) => setFilter({...filter, type: e.target.value})}
        >
          <option value="all">All Types</option>
          <option value="winner">Winner Notifications</option>
          <option value="reminder">Reminders</option>
          <option value="general">General</option>
        </select>
        <button onClick={loadLogs}>Refresh</button>
      </div>

      {/* Logs Table */}
      {loading ? (
        <div>Loading...</div>
      ) : (
        <table className="logs-table">
          <thead>
            <tr>
              <th>Sent At</th>
              <th>Contest</th>
              <th>Type</th>
              <th>Recipient</th>
              <th>Status</th>
              <th>Test Mode</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <tr key={log.id} className={`status-${log.status}`}>
                <td>{log.sentAt.toLocaleString()}</td>
                <td>{log.contestName}</td>
                <td>
                  <span className={`badge type-${log.type}`}>
                    {log.type}
                  </span>
                </td>
                <td>{log.userPhone}</td>
                <td>
                  <span className={`badge status-${log.status}`}>
                    {log.status}
                  </span>
                </td>
                <td>{log.testMode ? '🧪 Test' : '📱 Real'}</td>
                <td className="message-cell">
                  <span title={log.message}>
                    {log.message.substring(0, 50)}
                    {log.message.length > 50 ? '...' : ''}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
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
