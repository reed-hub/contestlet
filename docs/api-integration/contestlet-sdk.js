/**
 * Contestlet API SDK
 * Easy-to-use JavaScript SDK for integrating with the Contestlet API
 * 
 * Usage:
 *   const contestlet = new ContestletSDK('http://localhost:8000');
 *   await contestlet.auth.requestOTP('5551234567');
 *   await contestlet.auth.verifyOTP('5551234567', '123456');
 *   const contests = await contestlet.contests.getActive();
 */

class ContestletSDK {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.token = this._getStoredToken();
    
    // Initialize modules
    this.auth = new AuthModule(this);
    this.contests = new ContestsModule(this);
    this.entries = new EntriesModule(this);
    this.admin = new AdminModule(this);
  }

  // Core request method
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

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ContestletAPIError(response.status, response.statusText, errorData);
      }
      
      return await response.json();
    } catch (error) {
      if (error instanceof ContestletAPIError) {
        throw error;
      }
      throw new ContestletAPIError(0, 'Network Error', { message: error.message });
    }
  }

  // Token management
  setToken(token) {
    this.token = token;
    localStorage.setItem('contestlet_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('contestlet_token');
  }

  _getStoredToken() {
    return localStorage.getItem('contestlet_token');
  }

  isAuthenticated() {
    return !!this.token;
  }
}

// Custom error class
class ContestletAPIError extends Error {
  constructor(status, statusText, data = {}) {
    super(data.detail || data.message || statusText);
    this.name = 'ContestletAPIError';
    this.status = status;
    this.statusText = statusText;
    this.data = data;
  }
}

// Authentication module (Twilio Verify API)
class AuthModule {
  constructor(sdk) {
    this.sdk = sdk;
  }

  /**
   * Request OTP via Twilio Verify API
   * @param {string} phoneNumber - US phone number (various formats accepted)
   * @returns {Promise<{success: boolean, message: string, retryAfter: number|null}>}
   */
  async requestOTP(phoneNumber) {
    try {
      const normalizedPhone = this._normalizePhone(phoneNumber);
      const response = await this.sdk.request('/auth/request-otp', {
        method: 'POST',
        body: JSON.stringify({ phone: normalizedPhone }),
      });
      
      return {
        success: true,
        message: response.message,
        retryAfter: response.retry_after,
      };
    } catch (error) {
      if (error.status === 429) {
        return {
          success: false,
          message: 'Too many requests. Please wait before requesting another code.',
          retryAfter: 300, // Default retry time
          rateLimited: true,
        };
      }
      throw error;
    }
  }

  /**
   * Verify OTP code via Twilio Verify API
   * @param {string} phoneNumber - Same phone number used for request
   * @param {string} otpCode - 6-digit code from SMS (or 123456 in development)
   * @returns {Promise<{success: boolean, token?: string, userId?: number, message: string}>}
   */
  async verifyOTP(phoneNumber, otpCode) {
    const normalizedPhone = this._normalizePhone(phoneNumber);
    const normalizedCode = this._normalizeOTP(otpCode);
    
    const response = await this.sdk.request('/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ 
        phone: normalizedPhone, 
        code: normalizedCode 
      }),
    });
    
    if (response.success) {
      this.sdk.setToken(response.access_token);
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
  }

  async legacyVerifyPhone(phoneNumber) {
    const normalizedPhone = this._normalizePhone(phoneNumber);
    const response = await this.sdk.request('/auth/verify-phone', {
      method: 'POST',
      body: JSON.stringify({ phone: normalizedPhone }),
    });
    
    this.sdk.setToken(response.access_token);
    return {
      token: response.access_token,
      userId: response.user_id,
    };
  }

  logout() {
    this.sdk.clearToken();
  }

  _normalizePhone(phone) {
    const cleaned = phone.replace(/\D/g, '');
    
    if (cleaned.length === 10) {
      return cleaned;
    } else if (cleaned.length === 11 && cleaned.startsWith('1')) {
      return cleaned.substring(1);
    }
    
    throw new Error('Invalid phone number format. Please use 10-digit US phone number.');
  }

  _normalizeOTP(code) {
    const cleaned = code.replace(/\D/g, '');
    if (cleaned.length !== 6) {
      throw new Error('OTP code must be 6 digits');
    }
    return cleaned;
  }

  /**
   * Get current user information from JWT token
   * @returns {Promise<{userId: number, phone: string, role: string, authenticated: boolean}>}
   */
  async getCurrentUser() {
    return await this.sdk.request('/auth/me');
  }

  /**
   * Check if current user has admin role
   * @returns {Promise<boolean>}
   */
  async isAdmin() {
    try {
      const userInfo = await this.getCurrentUser();
      return userInfo.role === 'admin';
    } catch (error) {
      return false;
    }
  }
}

// Contests module
class ContestsModule {
  constructor(sdk) {
    this.sdk = sdk;
  }

  async getActive(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.location) params.append('location', filters.location);
    if (filters.page) params.append('page', filters.page);
    if (filters.size) params.append('size', filters.size);
    
    const queryString = params.toString();
    const endpoint = `/contests/active${queryString ? `?${queryString}` : ''}`;
    
    return await this.sdk.request(endpoint);
  }

  async getNearby(latitude, longitude, radius = 25, filters = {}) {
    if (!this._isValidCoordinate(latitude, longitude)) {
      throw new Error('Invalid coordinates. Latitude must be -90 to 90, longitude must be -180 to 180.');
    }
    
    const params = new URLSearchParams({
      lat: latitude,
      lng: longitude,
      radius: radius,
      ...(filters.page && { page: filters.page }),
      ...(filters.size && { size: filters.size }),
    });
    
    return await this.sdk.request(`/contests/nearby?${params}`);
  }

  async enter(contestId) {
    if (!this.sdk.isAuthenticated()) {
      throw new Error('Authentication required to enter contests');
    }
    
    return await this.sdk.request(`/contests/${contestId}/enter`, {
      method: 'POST',
    });
  }

  _isValidCoordinate(lat, lng) {
    return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
  }
}

// Entries module
class EntriesModule {
  constructor(sdk) {
    this.sdk = sdk;
  }

  async getMine() {
    if (!this.sdk.isAuthenticated()) {
      throw new Error('Authentication required to view entries');
    }
    
    return await this.sdk.request('/entries/me');
  }
}

// Admin module
class AdminModule {
  constructor(sdk) {
    this.sdk = sdk;
  }

  setAdminToken(adminToken) {
    this.adminToken = adminToken;
  }

  /**
   * Authenticate admin using OTP and set admin token
   * @param {string} adminPhone - Admin phone number
   * @param {string} otpCode - OTP code from SMS
   * @returns {Promise<{success: boolean, phone?: string, userId?: number, error?: string}>}
   */
  async authenticateWithOTP(adminPhone, otpCode) {
    try {
      // Verify OTP and get JWT token
      const verifyResult = await this.sdk.auth.verifyOTP(adminPhone, otpCode);
      
      if (!verifyResult.success) {
        return {
          success: false,
          error: verifyResult.message || 'OTP verification failed',
        };
      }

      // Set the token for future admin requests
      this.setAdminToken(verifyResult.token);
      this.sdk.setToken(verifyResult.token);

      // Check if user has admin role
      const userInfo = await this.sdk.auth.getCurrentUser();
      
      if (userInfo.role !== 'admin') {
        return {
          success: false,
          error: 'User does not have admin privileges',
        };
      }

      return {
        success: true,
        phone: userInfo.phone,
        userId: userInfo.userId,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  }

  async _adminRequest(endpoint, options = {}) {
    if (!this.adminToken) {
      throw new Error('Admin token required for admin operations');
    }
    
    return await this.sdk.request(endpoint, {
      ...options,
      headers: {
        Authorization: `Bearer ${this.adminToken}`,
        ...options.headers,
      },
    });
  }

  async checkAuth() {
    return await this._adminRequest('/admin/auth');
  }

  async createContest(contestData) {
    return await this._adminRequest('/admin/contests', {
      method: 'POST',
      body: JSON.stringify(contestData),
    });
  }

  async getContests() {
    return await this._adminRequest('/admin/contests');
  }

  async updateContest(contestId, updateData) {
    return await this._adminRequest(`/admin/contests/${contestId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async getContestEntries(contestId) {
    return await this._adminRequest(`/admin/contests/${contestId}/entries`);
  }

  async selectWinner(contestId) {
    return await this._adminRequest(`/admin/contests/${contestId}/select-winner`, {
      method: 'POST',
    });
  }

  /**
   * Notify contest winner via SMS
   * @param {number} contestId - Contest ID
   * @param {number} entryId - Winner's entry ID  
   * @param {string} message - Custom SMS message to send
   * @param {boolean} [testMode=false] - If true, simulate SMS without sending
   * @returns {Promise<Object>} SMS notification result with enhanced fields
   */
  async notifyWinner(contestId, entryId, message, testMode = false) {
    return await this._adminRequest(`/admin/contests/${contestId}/notify-winner`, {
      method: 'POST',
      body: JSON.stringify({
        entry_id: entryId,
        message: message,
        test_mode: testMode  // ✨ NEW: Test mode support
      }),
    });
  }

  /**
   * Select winner and optionally notify via SMS
   * @param {number} contestId - Contest ID
   * @param {string} [smsMessage] - Optional SMS message. If provided, winner will be notified
   * @param {boolean} [testMode=false] - If true, simulate SMS without sending
   * @returns {Promise<Object>} Combined result of winner selection and optional SMS
   */
  async selectAndNotifyWinner(contestId, smsMessage = null, testMode = false) {
    try {
      // Step 1: Select winner
      const winnerResult = await this.selectWinner(contestId);
      
      if (!winnerResult.success) {
        return {
          success: false,
          stage: 'winner_selection',
          error: winnerResult.message,
        };
      }

      // Step 2: Send SMS if message provided
      let smsResult = null;
      if (smsMessage) {
        smsResult = await this.notifyWinner(
          contestId, 
          winnerResult.winner_entry_id, 
          smsMessage,
          testMode  // ✨ NEW: Pass test mode to SMS notification
        );
      }

      return {
        success: true,
        winnerSelected: true,
        smsNotified: smsResult ? smsResult.success : false,
        winnerEntryId: winnerResult.winner_entry_id,
        winnerPhone: winnerResult.winner_user_phone,
        totalEntries: winnerResult.total_entries,
        smsStatus: smsResult ? smsResult.sms_status : null,
        smsResult: smsResult,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  }
}

// Utility functions
const ContestletUtils = {
  // Phone number formatter for display
  formatPhoneNumber(phone) {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    }
    return phone;
  },

  // Distance formatter
  formatDistance(miles) {
    if (miles < 1) {
      return `${(miles * 5280).toFixed(0)} ft`;
    }
    return `${miles.toFixed(1)} mi`;
  },

  // Date formatter
  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
  },

  // Time formatter
  formatDateTime(dateString) {
    return new Date(dateString).toLocaleString();
  },

  // Contest status checker
  getContestStatus(contest) {
    const now = new Date();
    const start = new Date(contest.start_time);
    const end = new Date(contest.end_time);
    
    if (now < start) return 'upcoming';
    if (now > end) return 'ended';
    return 'active';
  },

  // Error message helper
  getErrorMessage(error) {
    if (error instanceof ContestletAPIError) {
      switch (error.status) {
        case 400: return 'Invalid request. Please check your input.';
        case 401: return 'Session expired. Please log in again.';
        case 403: return 'Access denied.';
        case 404: return 'Not found.';
        case 409: return 'You have already performed this action.';
        case 429: return 'Too many requests. Please wait before trying again.';
        case 500: return 'Server error. Please try again later.';
        default: return error.message || 'An unexpected error occurred.';
      }
    }
    return error.message || 'An unexpected error occurred.';
  },
};

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
  // Node.js
  module.exports = { ContestletSDK, ContestletAPIError, ContestletUtils };
} else if (typeof define === 'function' && define.amd) {
  // AMD
  define(() => ({ ContestletSDK, ContestletAPIError, ContestletUtils }));
} else {
  // Browser global
  window.ContestletSDK = ContestletSDK;
  window.ContestletAPIError = ContestletAPIError;
  window.ContestletUtils = ContestletUtils;
}

// Example usage with Twilio Verify:
/*
// Initialize SDK
const contestlet = new ContestletSDK('http://localhost:8000');

// Twilio Verify authentication flow
try {
  // Step 1: Request OTP (sends SMS via Twilio)
  const otpResult = await contestlet.auth.requestOTP('18187958204');
  if (otpResult.success) {
    console.log('SMS sent via Twilio:', otpResult.message);
    
    // Step 2: Verify OTP (user enters code from SMS)
    // In development: Use 123456 
    // In production: Use actual code from SMS
    const authResult = await contestlet.auth.verifyOTP('18187958204', '123456');
    if (authResult.success) {
      console.log('Authenticated via Twilio Verify!', authResult.userId);
      // User now has JWT token and can access protected endpoints
    } else {
      console.log('Verification failed:', authResult.message);
    }
  } else if (otpResult.rateLimited) {
    console.log('Rate limited. Please wait before requesting another code.');
  }
} catch (error) {
  console.error('Twilio auth error:', ContestletUtils.getErrorMessage(error));
}

// Get contests
try {
  const activeContests = await contestlet.contests.getActive({ page: 1, size: 10 });
  const nearbyContests = await contestlet.contests.getNearby(37.7749, -122.4194, 25);
  
  // Enter a contest
  await contestlet.contests.enter(1);
  
  // View user's entries
  const myEntries = await contestlet.entries.getMine();
} catch (error) {
  console.error('Contest error:', ContestletUtils.getErrorMessage(error));
}

// Admin operations (OTP-based authentication)
try {
  // Step 1: Request OTP for admin phone
  await contestlet.auth.requestOTP('18187958204'); // Admin phone
  
  // Step 2: Authenticate with OTP to get admin JWT
  const adminAuth = await contestlet.admin.authenticateWithOTP('18187958204', '123456');
  if (adminAuth.success) {
    console.log('Admin authenticated:', adminAuth.phone);
    
    // Step 3: Admin operations now available
    const allContests = await contestlet.admin.getContests();
    const contestEntries = await contestlet.admin.getContestEntries(1);
    
    // Step 4: Winner selection and SMS notification
    const winnerResult = await contestlet.admin.selectWinner(1);
    if (winnerResult.success) {
      console.log('Winner selected:', winnerResult.winner_entry_id);
      
      // Send SMS notification to winner
      const smsResult = await contestlet.admin.notifyWinner(
        1, 
        winnerResult.winner_entry_id,
        "🎉 Congratulations! You've won our amazing contest! We'll contact you soon with prize details."
      );
      
      if (smsResult.success) {
        console.log('SMS sent to winner:', smsResult.winner_phone);
      }
    }
    
    // Alternative: Select winner and notify in one call
    const combinedResult = await contestlet.admin.selectAndNotifyWinner(
      2, 
      "🎊 You're our lucky winner! Check your email for next steps."
    );
    console.log('Winner selected and notified:', combinedResult.smsNotified);
    
    // Check current user info and role
    const userInfo = await contestlet.auth.getCurrentUser();
    console.log('Current user role:', userInfo.role); // "admin"
    
    const isAdmin = await contestlet.auth.isAdmin();
    console.log('Is admin:', isAdmin); // true
  } else {
    console.error('Admin auth failed:', adminAuth.error);
  }
} catch (error) {
  console.error('Admin error:', ContestletUtils.getErrorMessage(error));
}

// Legacy admin token (deprecated)
// admin.setAdminToken('your-admin-token');

try {
  const contests = await admin.getContests();
  const entries = await admin.getContestEntries(1);  // Get entries for contest 1
  const winner = await admin.selectWinner(1);
} catch (error) {
  console.error('Admin error:', ContestletUtils.getErrorMessage(error));
}
*/
