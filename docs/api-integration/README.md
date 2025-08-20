# 📚 API Integration Documentation

Welcome to the Contestlet API integration documentation! This directory contains everything you need to integrate your frontend application with the Contestlet API.

## 📋 Documentation Files

### 📖 [Frontend Integration Guide](./FRONTEND_INTEGRATION_GUIDE.md)
**The complete integration guide** - Your main resource for implementing Contestlet API integration.

**What's included:**
- 🚀 Quick start setup
- 🔐 Complete Twilio Verify authentication flow
- 📱 SMS-based OTP verification examples
- 🛡️ OTP-based admin authentication
- 📍 All API endpoints with examples
- ⚠️ Comprehensive error handling
- 💻 React, Vue.js, and vanilla JavaScript examples
- 🔒 Security best practices
- 🧪 Testing and development guidance

### 📋 [API Quick Reference](./API_QUICK_REFERENCE.md)
**Compact reference card** - Perfect for developers who need quick endpoint lookups.

**What's included:**
- 🔗 All endpoints with request/response examples
- 📱 Phone number formatting rules
- 📊 HTTP status codes
- 🔑 Authentication requirements
- 📍 Geolocation parameter ranges

### 🛠️ [JavaScript SDK](./contestlet-sdk.js)
**Drop-in SDK** - Ready-to-use JavaScript library for easy API integration.

**Features:**
- 🎯 Simple, intuitive API
- 🔐 Built-in token management with Twilio Verify
- 📱 Automated phone number validation
- ⚠️ Comprehensive error handling
- 🌍 Geolocation utilities
- 🛡️ Admin operations support
- 📧 **NEW**: SMS notification management with audit logging
- 📊 **NEW**: Comprehensive notification logs API
- 🌍 **NEW**: Full timezone support with admin preferences
- ⏰ **NEW**: UTC storage with local timezone display
- 📦 Compatible with React, Vue, Angular, and vanilla JS

### 🎪 [Interactive Demo](./demo.html)
**Live demo page** - See the API in action with a working example.

**Features:**
- 🔐 Twilio Verify authentication flow demonstration
- 📱 SMS OTP verification (real and mock modes)
- 🛡️ OTP-based admin authentication demo
- 🎯 Contest browsing and entry
- 📍 Geolocation-based contest search
- 👤 User entry management
- 🔧 Admin operations interface
- 🚨 **NEW**: Enhanced SMS winner notifications with security
- 🧪 **NEW**: Test mode for SMS simulation
- 📊 **NEW**: SMS notification audit trail with filtering
- 🌍 **NEW**: Timezone-aware contest creation and display
- ⏰ **NEW**: Admin timezone preference management
- 📋 Real-time API response logging

---

## 🚀 Quick Start

### 1. **Start with the Integration Guide**
Read the [Frontend Integration Guide](./FRONTEND_INTEGRATION_GUIDE.md) for comprehensive setup instructions.

### 2. **Use the JavaScript SDK**
```html
<script src="docs/api-integration/contestlet-sdk.js"></script>
<script>
const contestlet = new ContestletSDK('http://localhost:8000');
</script>
```

### 3. **Try the Demo**
Open `demo.html` in your browser to see a working example:
```bash
# Serve the demo locally
python3 -m http.server 8080
# Then visit: http://localhost:8080/docs/api-integration/demo.html
```

### 4. **Quick Reference**
Keep the [API Quick Reference](./API_QUICK_REFERENCE.md) handy for endpoint lookups.

---

## 🔧 Development Workflow

### Prerequisites
- Contestlet API running on `http://localhost:8000`
- Modern web browser with JavaScript enabled
- Basic knowledge of REST APIs and JavaScript

### Integration Steps
1. **Authentication Setup**
   - Implement OTP request/verification flow
   - Set up token storage and management
   - Configure admin phone numbers for admin access
   - Handle authentication errors

2. **Contest Features**
   - Load and display active contests
   - Implement geolocation-based search
   - Add contest entry functionality
   - Show user's contest entries

3. **Error Handling**
   - Implement comprehensive error catching
   - Add user-friendly error messages
   - Handle rate limiting scenarios

4. **Testing**
   - Test with the interactive demo
   - Verify all endpoints work correctly
   - Test error scenarios

---

## 📚 Additional Resources

### API Documentation
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/

### Timezone Documentation
- **📍 [Comprehensive Timezone Guide](../TIMEZONE_GUIDE.md)**: Complete guide to timezone handling, best practices, and troubleshooting
- **🌍 Timezone Support**: UTC storage with admin timezone preferences
- **⏰ Contest Creation**: Timezone-aware contest scheduling

### Code Examples
The integration guide includes complete examples for:
- ⚛️ React with hooks
- 🟢 Vue.js with Pinia
- 📦 Vanilla JavaScript
- 🎯 TypeScript definitions

### Support
- Check the main [README](../../README.md) for API details
- Review server logs for debugging
- Use the demo page to test API responses

---

## 🎯 Next Steps

1. **Read the Integration Guide** - Get familiar with the authentication flow and API structure
2. **Download the SDK** - Use `contestlet-sdk.js` for easy integration
3. **Try the Demo** - See everything working together in `demo.html`
4. **Build Your App** - Use the examples and patterns from the documentation

Happy coding! 🚀
