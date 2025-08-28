# 🗺️ Geocoding Integration Guide

**Complete frontend integration guide for the new geocoding endpoint that enables radius-based contest targeting.**

---

## 🎯 **Overview**

The `/location/geocode` endpoint converts addresses to coordinates, enabling radius-based contest targeting. This guide provides everything you need to integrate address verification into your contest creation forms.

### **✅ What's Available**
- 🌍 **Address to Coordinates**: Convert any US address to lat/lng coordinates
- 🆓 **Free Service**: Uses OpenStreetMap Nominatim (no API key required)
- 🔒 **Admin Authentication**: Secure endpoint for contest creators only
- ⚡ **Fast Response**: Typically under 2 seconds for most addresses
- 🛡️ **Error Handling**: Comprehensive validation and error responses

---

## 🚀 **Quick Start**

### **1. Basic Geocoding Request**

```javascript
const geocodeAddress = async (address, adminToken) => {
  try {
    const response = await fetch('/location/geocode', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminToken}`
      },
      body: JSON.stringify({ address })
    });

    const result = await response.json();
    
    if (result.success) {
      return {
        success: true,
        latitude: result.coordinates.latitude,
        longitude: result.coordinates.longitude,
        formattedAddress: result.formatted_address
      };
    } else {
      return {
        success: false,
        error: result.error_message
      };
    }
  } catch (error) {
    return {
      success: false,
      error: 'Network error occurred'
    };
  }
};
```

### **2. Usage in Contest Form**

```javascript
// Example usage in contest creation
const handleAddressGeocode = async () => {
  const address = "1600 Amphitheatre Parkway, Mountain View, CA";
  const result = await geocodeAddress(address, userToken);
  
  if (result.success) {
    // Update contest form with coordinates
    setContestData(prev => ({
      ...prev,
      radius_address: result.formattedAddress,
      radius_latitude: result.latitude,
      radius_longitude: result.longitude
    }));
  } else {
    // Show error to user
    setError(result.error);
  }
};
```

---

## 📋 **API Reference**

### **Endpoint Details**
- **URL**: `POST /location/geocode`
- **Authentication**: Admin JWT required
- **Content-Type**: `application/json`

### **Request Format**
```json
{
  "address": "123 Main St, San Francisco, CA 94102"
}
```

### **Success Response (200)**
```json
{
  "success": true,
  "coordinates": {
    "latitude": 37.7915756,
    "longitude": -122.3944622
  },
  "formatted_address": "123, Main Street, Transbay, South of Market, San Francisco, California, 94105, United States"
}
```

### **Error Responses**

**Address Not Found (200 with success: false)**
```json
{
  "success": false,
  "error_message": "Address not found"
}
```

**Invalid Input (422)**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "address"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

**Authentication Required (401)**
```json
{
  "detail": "Authentication required"
}
```

**Admin Access Required (403)**
```json
{
  "detail": "Invalid admin credentials. Admin access required."
}
```

---

## 🎨 **React Components**

### **Address Geocoding Component**

```tsx
import React, { useState } from 'react';
import { MapPin, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

interface AddressGeocoderProps {
  onGeocode: (result: GeocodingResult) => void;
  adminToken: string;
  initialAddress?: string;
}

interface GeocodingResult {
  success: boolean;
  latitude?: number;
  longitude?: number;
  formattedAddress?: string;
  error?: string;
}

export const AddressGeocoder: React.FC<AddressGeocoderProps> = ({
  onGeocode,
  adminToken,
  initialAddress = ''
}) => {
  const [address, setAddress] = useState(initialAddress);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GeocodingResult | null>(null);

  const handleGeocode = async () => {
    if (!address.trim()) {
      setResult({ success: false, error: 'Please enter an address' });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('/location/geocode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`
        },
        body: JSON.stringify({ address: address.trim() })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      const geocodingResult: GeocodingResult = {
        success: data.success,
        latitude: data.coordinates?.latitude,
        longitude: data.coordinates?.longitude,
        formattedAddress: data.formatted_address,
        error: data.error_message
      };

      setResult(geocodingResult);
      onGeocode(geocodingResult);

    } catch (error) {
      const errorResult: GeocodingResult = {
        success: false,
        error: error instanceof Error ? error.message : 'Geocoding failed'
      };
      setResult(errorResult);
      onGeocode(errorResult);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleGeocode();
    }
  };

  return (
    <div className="space-y-4">
      {/* Address Input */}
      <div className="flex space-x-2">
        <div className="flex-1">
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter address (e.g., 123 Main St, San Francisco, CA)"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </div>
        <button
          onClick={handleGeocode}
          disabled={loading || !address.trim()}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {loading ? (
            <Loader2 className="animate-spin" size={16} />
          ) : (
            <MapPin size={16} />
          )}
          <span>{loading ? 'Geocoding...' : 'Find Location'}</span>
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className={`p-3 rounded-md ${
          result.success 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          {result.success ? (
            <div className="flex items-start space-x-2">
              <CheckCircle className="text-green-500 mt-0.5" size={16} />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-800">
                  Location Found
                </p>
                <p className="text-sm text-green-700 mt-1">
                  {result.formattedAddress}
                </p>
                <p className="text-xs text-green-600 mt-1">
                  Coordinates: {result.latitude?.toFixed(6)}, {result.longitude?.toFixed(6)}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-start space-x-2">
              <AlertCircle className="text-red-500 mt-0.5" size={16} />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800">
                  Geocoding Failed
                </p>
                <p className="text-sm text-red-700 mt-1">
                  {result.error}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Help Text */}
      <p className="text-xs text-gray-500">
        Enter a complete US address including street, city, and state for best results.
      </p>
    </div>
  );
};
```

### **Contest Form Integration**

```tsx
import React, { useState } from 'react';
import { AddressGeocoder } from './AddressGeocoder';

export const ContestLocationForm = ({ adminToken, onLocationUpdate }) => {
  const [locationType, setLocationType] = useState('united_states');
  const [radiusData, setRadiusData] = useState({
    address: '',
    miles: 50,
    latitude: null,
    longitude: null
  });

  const handleGeocodingResult = (result) => {
    if (result.success) {
      const updatedData = {
        ...radiusData,
        address: result.formattedAddress,
        latitude: result.latitude,
        longitude: result.longitude
      };
      setRadiusData(updatedData);
      
      // Update parent component
      onLocationUpdate({
        location_type: 'radius',
        radius_address: result.formattedAddress,
        radius_miles: radiusData.miles,
        radius_coordinates: {
          latitude: result.latitude,
          longitude: result.longitude
        }
      });
    }
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-medium">Contest Location Targeting</h3>
      
      {/* Location Type Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">
          Target Audience
        </label>
        
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="radio"
              name="locationType"
              value="united_states"
              checked={locationType === 'united_states'}
              onChange={(e) => setLocationType(e.target.value)}
              className="mr-2"
            />
            <span>All United States residents</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="radio"
              name="locationType"
              value="radius"
              checked={locationType === 'radius'}
              onChange={(e) => setLocationType(e.target.value)}
              className="mr-2"
            />
            <span>Within specific radius of address</span>
          </label>
        </div>
      </div>

      {/* Radius Configuration */}
      {locationType === 'radius' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium">Radius-Based Targeting</h4>
          
          {/* Address Geocoding */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Center Address
            </label>
            <AddressGeocoder
              onGeocode={handleGeocodingResult}
              adminToken={adminToken}
              initialAddress={radiusData.address}
            />
          </div>

          {/* Radius Distance */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Radius (miles)
            </label>
            <select
              value={radiusData.miles}
              onChange={(e) => {
                const miles = parseInt(e.target.value);
                setRadiusData(prev => ({ ...prev, miles }));
                if (radiusData.latitude && radiusData.longitude) {
                  onLocationUpdate({
                    location_type: 'radius',
                    radius_address: radiusData.address,
                    radius_miles: miles,
                    radius_coordinates: {
                      latitude: radiusData.latitude,
                      longitude: radiusData.longitude
                    }
                  });
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value={10}>10 miles</option>
              <option value={25}>25 miles</option>
              <option value={50}>50 miles</option>
              <option value={100}>100 miles</option>
              <option value={250}>250 miles</option>
              <option value={500}>500 miles</option>
            </select>
          </div>

          {/* Preview */}
          {radiusData.latitude && radiusData.longitude && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm text-blue-800">
                <strong>Target Area:</strong> Within {radiusData.miles} miles of {radiusData.address}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

### **Custom Hook for Geocoding**

```tsx
import { useState, useCallback } from 'react';

interface UseGeocodingOptions {
  adminToken: string;
}

interface GeocodingResult {
  success: boolean;
  latitude?: number;
  longitude?: number;
  formattedAddress?: string;
  error?: string;
}

export const useGeocoding = ({ adminToken }: UseGeocodingOptions) => {
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<GeocodingResult | null>(null);

  const geocodeAddress = useCallback(async (address: string): Promise<GeocodingResult> => {
    if (!address.trim()) {
      const result = { success: false, error: 'Address is required' };
      setLastResult(result);
      return result;
    }

    setLoading(true);

    try {
      const response = await fetch('/location/geocode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`
        },
        body: JSON.stringify({ address: address.trim() })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      const result: GeocodingResult = {
        success: data.success,
        latitude: data.coordinates?.latitude,
        longitude: data.coordinates?.longitude,
        formattedAddress: data.formatted_address,
        error: data.error_message
      };

      setLastResult(result);
      return result;

    } catch (error) {
      const result: GeocodingResult = {
        success: false,
        error: error instanceof Error ? error.message : 'Geocoding failed'
      };
      setLastResult(result);
      return result;
    } finally {
      setLoading(false);
    }
  }, [adminToken]);

  const clearResult = useCallback(() => {
    setLastResult(null);
  }, []);

  return {
    geocodeAddress,
    loading,
    lastResult,
    clearResult
  };
};
```

---

## 🎯 **Integration Examples**

### **1. Simple Address Lookup**

```javascript
// Basic usage
const result = await fetch('/location/geocode', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${adminToken}`
  },
  body: JSON.stringify({
    address: "1600 Amphitheatre Parkway, Mountain View, CA"
  })
});

const data = await result.json();
console.log('Coordinates:', data.coordinates);
// Output: { latitude: 37.4224857, longitude: -122.0855846 }
```

### **2. Form Validation with Geocoding**

```javascript
const validateAndGeocodeAddress = async (formData) => {
  if (formData.location_type !== 'radius') {
    return { valid: true };
  }

  if (!formData.radius_address) {
    return { valid: false, error: 'Address is required for radius targeting' };
  }

  const geocodingResult = await geocodeAddress(formData.radius_address, adminToken);
  
  if (!geocodingResult.success) {
    return { 
      valid: false, 
      error: `Invalid address: ${geocodingResult.error}` 
    };
  }

  // Update form with geocoded coordinates
  return {
    valid: true,
    updatedData: {
      ...formData,
      radius_address: geocodingResult.formattedAddress,
      radius_latitude: geocodingResult.latitude,
      radius_longitude: geocodingResult.longitude
    }
  };
};
```

### **3. Batch Address Processing**

```javascript
const geocodeMultipleAddresses = async (addresses, adminToken) => {
  const results = [];
  
  for (const address of addresses) {
    try {
      const result = await geocodeAddress(address, adminToken);
      results.push({ address, ...result });
      
      // Rate limiting: wait 1 second between requests
      await new Promise(resolve => setTimeout(resolve, 1000));
    } catch (error) {
      results.push({ 
        address, 
        success: false, 
        error: error.message 
      });
    }
  }
  
  return results;
};
```

### **4. Auto-complete with Geocoding**

```javascript
const AddressAutocomplete = ({ onAddressSelect, adminToken }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [selectedAddress, setSelectedAddress] = useState('');

  const handleAddressConfirm = async () => {
    if (!selectedAddress) return;

    const result = await geocodeAddress(selectedAddress, adminToken);
    if (result.success) {
      onAddressSelect({
        address: result.formattedAddress,
        latitude: result.latitude,
        longitude: result.longitude
      });
    }
  };

  return (
    <div>
      <input
        type="text"
        value={selectedAddress}
        onChange={(e) => setSelectedAddress(e.target.value)}
        placeholder="Enter address..."
      />
      <button onClick={handleAddressConfirm}>
        Confirm Address
      </button>
    </div>
  );
};
```

---

## 🔒 **Error Handling**

### **Comprehensive Error Handler**

```javascript
const handleGeocodingError = (error, response) => {
  // Network errors
  if (!response) {
    return {
      type: 'network',
      message: 'Unable to connect to geocoding service',
      userMessage: 'Please check your internet connection and try again.'
    };
  }

  // HTTP status errors
  switch (response.status) {
    case 401:
      return {
        type: 'auth',
        message: 'Authentication required',
        userMessage: 'Please log in to use address lookup.'
      };
    
    case 403:
      return {
        type: 'permission',
        message: 'Admin access required',
        userMessage: 'You need admin permissions to use address lookup.'
      };
    
    case 422:
      return {
        type: 'validation',
        message: 'Invalid address format',
        userMessage: 'Please enter a valid address.'
      };
    
    case 408:
      return {
        type: 'timeout',
        message: 'Geocoding service timeout',
        userMessage: 'The address lookup is taking too long. Please try again.'
      };
    
    case 503:
      return {
        type: 'service',
        message: 'Geocoding service unavailable',
        userMessage: 'Address lookup is temporarily unavailable. Please try again later.'
      };
    
    default:
      return {
        type: 'unknown',
        message: `HTTP ${response.status}: ${response.statusText}`,
        userMessage: 'An unexpected error occurred. Please try again.'
      };
  }
};
```

### **User-Friendly Error Messages**

```javascript
const showGeocodingError = (error) => {
  const errorMap = {
    'Address not found': 'We couldn\'t find that address. Please try a more specific address with street, city, and state.',
    'Geocoding service timed out': 'Address lookup is taking longer than expected. Please try again.',
    'Authentication required': 'Please log in to use address verification.',
    'Invalid admin credentials': 'You need admin permissions to verify addresses.',
    'Geocoding service is temporarily unavailable': 'Address verification is temporarily down. Please try again in a few minutes.'
  };

  return errorMap[error] || 'Unable to verify address. Please check the address and try again.';
};
```

---

## 🧪 **Testing**

### **Unit Tests**

```javascript
// Test geocoding function
describe('geocodeAddress', () => {
  test('should return coordinates for valid address', async () => {
    const mockResponse = {
      success: true,
      coordinates: { latitude: 37.7749, longitude: -122.4194 },
      formatted_address: 'San Francisco, CA, USA'
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse)
    });

    const result = await geocodeAddress('San Francisco, CA', 'mock-token');
    
    expect(result.success).toBe(true);
    expect(result.latitude).toBe(37.7749);
    expect(result.longitude).toBe(-122.4194);
  });

  test('should handle address not found', async () => {
    const mockResponse = {
      success: false,
      error_message: 'Address not found'
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse)
    });

    const result = await geocodeAddress('invalid address', 'mock-token');
    
    expect(result.success).toBe(false);
    expect(result.error).toBe('Address not found');
  });
});
```

### **Integration Tests**

```javascript
// Test complete form flow
test('contest form with radius targeting', async () => {
  render(<ContestForm adminToken="mock-token" />);
  
  // Select radius targeting
  fireEvent.click(screen.getByLabelText(/radius/i));
  
  // Enter address
  const addressInput = screen.getByPlaceholderText(/enter address/i);
  fireEvent.change(addressInput, { 
    target: { value: '1600 Amphitheatre Parkway, Mountain View, CA' } 
  });
  
  // Click geocode button
  fireEvent.click(screen.getByText(/find location/i));
  
  // Wait for geocoding result
  await waitFor(() => {
    expect(screen.getByText(/location found/i)).toBeInTheDocument();
  });
  
  // Verify coordinates are set
  expect(screen.getByText(/37.422/)).toBeInTheDocument();
});
```

---

## 🌍 **Best Practices**

### **1. Address Input Guidelines**
- **Encourage complete addresses**: "123 Main St, San Francisco, CA 94102"
- **Provide examples**: Show format in placeholder text
- **Validate before geocoding**: Check for minimum required components
- **Handle partial matches**: Show formatted address for confirmation

### **2. User Experience**
- **Loading states**: Show spinner during geocoding requests
- **Immediate feedback**: Display results or errors quickly
- **Address confirmation**: Let users confirm the formatted address
- **Retry options**: Allow users to try different address formats

### **3. Performance Optimization**
- **Debounce requests**: Wait for user to stop typing
- **Cache results**: Store geocoded addresses locally
- **Rate limiting**: Respect service limits (1 request per second)
- **Fallback handling**: Graceful degradation when service is unavailable

### **4. Security Considerations**
- **Token validation**: Ensure admin token is valid before requests
- **Input sanitization**: Clean address input before sending
- **Error message filtering**: Don't expose sensitive error details
- **HTTPS only**: Always use secure connections

---

## 📚 **Additional Resources**

### **Related Endpoints**
- `GET /location/states` - Get list of US states for state-specific targeting
- `POST /location/validate` - Validate complete location configuration
- `POST /location/check-eligibility` - Check if user is eligible for contest

### **Documentation Links**
- [API Quick Reference](../api-integration/API_QUICK_REFERENCE.md#location--geocoding)
- [Complete API Integration Guide](../api-integration/FRONTEND_INTEGRATION_GUIDE.md)
- [Contest Form Support Guide](../backend/COMPLETE_FORM_SUPPORT_SUMMARY.md)

### **Example Addresses for Testing**
```javascript
const testAddresses = [
  "1600 Amphitheatre Parkway, Mountain View, CA",      // Google HQ
  "1 Apple Park Way, Cupertino, CA",                   // Apple Park
  "350 5th Ave, New York, NY 10118",                   // Empire State Building
  "1600 Pennsylvania Avenue NW, Washington, DC 20500", // White House
  "123 Main St, San Francisco, CA 94102"               // Generic address
];
```

---

## 🎉 **Ready to Integrate!**

Your geocoding integration is now complete with:

✅ **Production-ready components**  
✅ **Comprehensive error handling**  
✅ **TypeScript support**  
✅ **Testing examples**  
✅ **Best practices guide**  
✅ **Real-world usage patterns**

**The geocoding endpoint is live and ready for immediate integration into your contest creation forms! 🚀**

Start with the `AddressGeocoder` component and customize it to match your design system.
