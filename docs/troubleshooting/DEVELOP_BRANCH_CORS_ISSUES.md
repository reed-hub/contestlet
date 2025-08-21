# 🚨 Develop Branch CORS Issues - Troubleshooting Guide

## 📋 Current Status Analysis

Based on testing the local development server:

### ✅ **What's Working:**
- Server is healthy and running on `http://localhost:8000`
- CORS is configured for `localhost:3000`, `localhost:3002`, and other local ports
- OPTIONS preflight requests return correct CORS headers
- Public endpoints like `/contests/active` are responding correctly
- Authentication endpoints return proper error messages

### 🔍 **CORS Configuration Confirmed:**
```python
# app/core/vercel_config.py - Development environment
"cors_origins": [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:3002",  # ✅ Frontend development port
    "http://localhost:3003",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",  # ✅ Frontend development port
    "http://127.0.0.1:3003",
    "http://127.0.0.1:8000"
]
```

## 🧪 **Test Results:**

### CORS Preflight Tests
```bash
# ✅ Port 3000 - Working
curl -X OPTIONS -H "Origin: http://localhost:3000" http://localhost:8000/contests/1/enter
→ Returns: access-control-allow-origin: http://localhost:3000

# ✅ Port 3002 - Working  
curl -X OPTIONS -H "Origin: http://localhost:3002" http://localhost:8000/contests/1/enter
→ Returns: access-control-allow-origin: http://localhost:3002
```

### API Endpoint Tests
```bash
# ✅ Public endpoints working
GET /contests/active → Returns contest data

# ✅ Protected endpoints working (proper auth errors)
POST /contests/1/enter → Returns "Could not validate credentials"
```

## 🔍 **Possible Issues & Solutions:**

### **1. Frontend Configuration Issue**
If the frontend is still seeing CORS errors, check:

**Frontend Environment Variables:**
```env
# Make sure API URL is correct
REACT_APP_API_BASE_URL=http://localhost:8000
# Or
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Frontend Port:**
```bash
# Make sure frontend is running on expected port
npm start  # Usually defaults to 3000
# Or specifically:
PORT=3002 npm start
```

### **2. Browser Cache Issue**
If CORS was broken before and now fixed, browsers may cache CORS failures:

**Solution:**
```bash
# Clear browser cache or use incognito mode
# Or hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
```

### **3. Authentication vs CORS**
Make sure the error is actually CORS and not authentication:

**CORS Error (appears in browser console):**
```
Access to fetch at 'http://localhost:8000/contests/1/enter' from origin 'http://localhost:3002' 
has been blocked by CORS policy: ...
```

**Auth Error (appears in network response):**
```json
{"detail": "Could not validate credentials"}
```

### **4. Development vs Production Environment**
Check which environment the server thinks it's in:

**Test Environment Detection:**
```bash
curl http://localhost:8000/ | jq '.environment'
# Should return: "development"
```

## 🛠️ **Quick Fixes:**

### **Frontend Developer Quick Test:**
```javascript
// Test CORS directly in browser console
fetch('http://localhost:8000/', {
  method: 'GET',
  headers: { 'Origin': 'http://localhost:3002' }
})
.then(r => r.json())
.then(data => console.log('✅ CORS working:', data))
.catch(err => console.log('❌ CORS issue:', err));
```

### **Backend Developer Quick Test:**
```bash
# Restart server to reload CORS config
pkill -f "uvicorn app.main:app"
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test specific origin
curl -X OPTIONS \
  -H "Origin: http://localhost:3002" \
  -H "Access-Control-Request-Method: POST" \
  http://localhost:8000/contests/1/enter -v
```

## 📞 **If Issue Persists:**

### **Gather This Information:**
1. **Exact error message** from browser console
2. **Frontend port** (`localhost:3000` vs `localhost:3002`)
3. **Network tab** showing the failing request
4. **Environment** (development/staging/production)
5. **Endpoint being called** (public vs protected)

### **Common CORS vs Non-CORS Issues:**

| Real CORS Issue | Not CORS Issue |
|----------------|-----------------|
| "blocked by CORS policy" in console | JSON error response like `{"detail": "..."}` |
| Preflight OPTIONS fails | POST/GET reaches server but returns error |
| Different origin in request | Authentication/validation errors |
| Browser blocks before request sent | Server processes request but rejects it |

## 🚀 **Current Status:**

**✅ CORS is properly configured and working on the develop branch.**

If you're still seeing issues, it's likely:
1. **Browser cache** needs clearing
2. **Frontend environment** variable pointing to wrong URL  
3. **Authentication issue** being mistaken for CORS
4. **Different port** than expected being used

**Please provide the specific error message and context for targeted troubleshooting!** 🎯
