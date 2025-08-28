# 🎨 Cloudinary Media Integration Guide

**Complete frontend integration guide for Cloudinary-powered contest hero images and videos.**

---

## 🎯 **Overview**

The Contestlet API now includes a complete Cloudinary media management system for contest hero images and videos. This guide provides everything you need to integrate media upload, display, and management features into your frontend application.

### **✅ What's Included**
- 🖼️ **Image & Video Support**: JPEG, PNG, WebP, GIF, MP4, MOV, AVI
- 🔄 **Auto-Optimization**: WebP/AVIF conversion, compression, responsive sizing
- 📱 **Multi-Size URLs**: Thumbnail, medium, large, extra-large for responsive design
- 🔒 **Secure Uploads**: Admin and sponsor permissions with ownership validation
- 🌍 **Environment Separation**: Proper folder organization per environment
- 📊 **Fallback Support**: Graceful handling of existing content

---

## 🚀 **Quick Start**

### **1. Check Service Health**

```javascript
// Verify Cloudinary is configured
const healthResponse = await fetch('/media/health');
const health = await healthResponse.json();

if (health.cloudinary_configured) {
  console.log('✅ Cloudinary ready for uploads');
} else {
  console.log('⚠️ Cloudinary not configured - uploads disabled');
}
```

### **2. Upload Contest Hero Media**

```javascript
// Upload image or video
const uploadMedia = async (contestId, file, mediaType = 'image') => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`/media/contests/${contestId}/hero?media_type=${mediaType}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`
    },
    body: formData
  });
  
  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }
  
  return await response.json();
};
```

### **3. Get Optimized URLs**

```javascript
// Get responsive image URLs
const getMediaUrls = async (contestId) => {
  const response = await fetch(`/media/contests/${contestId}/hero/urls`);
  const data = await response.json();
  
  return {
    hasMedia: data.has_media,
    fallbackUrl: data.fallback_url,
    urls: data.urls // { thumbnail, medium, large, extra_large }
  };
};
```

---

## 📋 **API Endpoints**

### **🔐 Authenticated Endpoints**

#### **Upload Hero Media**
```http
POST /media/contests/{contest_id}/hero?media_type={type}
Authorization: Bearer {token}
Content-Type: multipart/form-data

Body: FormData with 'file' field
```

**Parameters:**
- `contest_id`: Contest ID (integer)
- `media_type`: "image" or "video" (query parameter)
- `file`: Media file (form data)

**Response:**
```json
{
  "contest_id": 123,
  "public_id": "contestlet-develop/contests/123/hero",
  "secure_url": "https://res.cloudinary.com/...",
  "media_type": "image",
  "metadata": {
    "width": 1080,
    "height": 1080,
    "format": "jpg",
    "bytes": 245760
  }
}
```

#### **Delete Hero Media**
```http
DELETE /media/contests/{contest_id}/hero
Authorization: Bearer {token}
```

**Response:**
```json
{
  "contest_id": 123,
  "deleted": true,
  "public_id": "contestlet-develop/contests/123/hero"
}
```

### **🌍 Public Endpoints**

#### **Get Optimized URLs**
```http
GET /media/contests/{contest_id}/hero/urls
```

**Response:**
```json
{
  "contest_id": 123,
  "has_media": true,
  "fallback_url": "https://example.com/fallback.jpg",
  "urls": {
    "thumbnail": "https://res.cloudinary.com/.../c_fill,w_150,h_150/...",
    "medium": "https://res.cloudinary.com/.../c_fill,w_400,h_400/...",
    "large": "https://res.cloudinary.com/.../c_fill,w_800,h_800/...",
    "extra_large": "https://res.cloudinary.com/.../c_fill,w_1200,h_1200/..."
  }
}
```

#### **Service Health Check**
```http
GET /media/health
```

**Response:**
```json
{
  "service": "media",
  "status": "healthy",
  "cloudinary_configured": true,
  "environment": "development",
  "base_folder": "contestlet-develop"
}
```

---

## 🎨 **React Components**

### **Media Upload Component**

```tsx
import React, { useState, useRef } from 'react';
import { Upload, X, Image, Video, Loader2 } from 'lucide-react';

interface MediaUploadProps {
  contestId: number;
  currentMediaUrl?: string;
  onUploadSuccess: (data: any) => void;
  onUploadError: (error: string) => void;
}

export const MediaUpload: React.FC<MediaUploadProps> = ({
  contestId,
  currentMediaUrl,
  onUploadSuccess,
  onUploadError
}) => {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (file: File) => {
    if (!file) return;

    // Validate file type
    const isImage = file.type.startsWith('image/');
    const isVideo = file.type.startsWith('video/');
    
    if (!isImage && !isVideo) {
      onUploadError('Please select an image or video file');
      return;
    }

    // Validate file size (50MB limit)
    if (file.size > 50 * 1024 * 1024) {
      onUploadError('File size must be less than 50MB');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const mediaType = isImage ? 'image' : 'video';
      const response = await fetch(`/media/contests/${contestId}/hero?media_type=${mediaType}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const data = await response.json();
      onUploadSuccess(data);
    } catch (error) {
      onUploadError(error.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  return (
    <div className="space-y-4">
      {/* Current Media Preview */}
      {currentMediaUrl && (
        <div className="relative">
          <img 
            src={currentMediaUrl} 
            alt="Contest hero" 
            className="w-full h-48 object-cover rounded-lg"
          />
          <button
            onClick={() => {/* Handle delete */}}
            className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Upload Area */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300'}
          ${uploading ? 'opacity-50 pointer-events-none' : 'cursor-pointer hover:border-gray-400'}
        `}
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,video/*"
          onChange={handleFileInputChange}
          className="hidden"
        />

        {uploading ? (
          <div className="flex flex-col items-center space-y-2">
            <Loader2 className="animate-spin" size={32} />
            <p>Uploading...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-2">
            <Upload size={32} className="text-gray-400" />
            <p className="text-lg font-medium">Drop files here or click to upload</p>
            <p className="text-sm text-gray-500">
              Supports images (JPEG, PNG, WebP, GIF) and videos (MP4, MOV, AVI)
            </p>
            <p className="text-xs text-gray-400">Maximum file size: 50MB</p>
          </div>
        )}
      </div>

      {/* File Type Icons */}
      <div className="flex justify-center space-x-4 text-sm text-gray-500">
        <div className="flex items-center space-x-1">
          <Image size={16} />
          <span>Images</span>
        </div>
        <div className="flex items-center space-x-1">
          <Video size={16} />
          <span>Videos</span>
        </div>
      </div>
    </div>
  );
};
```

### **Responsive Media Display Component**

```tsx
import React, { useState, useEffect } from 'react';

interface ResponsiveMediaProps {
  contestId: number;
  className?: string;
  sizes?: 'thumbnail' | 'medium' | 'large' | 'extra_large';
  fallbackUrl?: string;
}

export const ResponsiveMedia: React.FC<ResponsiveMediaProps> = ({
  contestId,
  className = '',
  sizes = 'medium',
  fallbackUrl
}) => {
  const [mediaData, setMediaData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMediaUrls = async () => {
      try {
        const response = await fetch(`/media/contests/${contestId}/hero/urls`);
        if (!response.ok) {
          throw new Error('Failed to fetch media URLs');
        }
        const data = await response.json();
        setMediaData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMediaUrls();
  }, [contestId]);

  if (loading) {
    return (
      <div className={`bg-gray-200 animate-pulse ${className}`}>
        <div className="w-full h-full flex items-center justify-center">
          <div className="text-gray-400">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-gray-100 ${className}`}>
        <div className="w-full h-full flex items-center justify-center">
          <div className="text-gray-500">Failed to load media</div>
        </div>
      </div>
    );
  }

  // Use Cloudinary optimized URL if available, otherwise fallback
  const imageUrl = mediaData?.has_media 
    ? mediaData.urls[sizes]
    : (mediaData?.fallback_url || fallbackUrl);

  if (!imageUrl) {
    return (
      <div className={`bg-gray-100 ${className}`}>
        <div className="w-full h-full flex items-center justify-center">
          <div className="text-gray-500">No media available</div>
        </div>
      </div>
    );
  }

  return (
    <img
      src={imageUrl}
      alt="Contest hero media"
      className={className}
      loading="lazy"
    />
  );
};
```

### **Media Management Hook**

```tsx
import { useState, useCallback } from 'react';

export const useMediaManagement = (contestId: number) => {
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const uploadMedia = useCallback(async (file: File, mediaType: 'image' | 'video') => {
    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`/media/contests/${contestId}/hero?media_type=${mediaType}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      return await response.json();
    } finally {
      setUploading(false);
    }
  }, [contestId]);

  const deleteMedia = useCallback(async () => {
    setDeleting(true);
    
    try {
      const response = await fetch(`/media/contests/${contestId}/hero`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Delete failed');
      }

      return await response.json();
    } finally {
      setDeleting(false);
    }
  }, [contestId]);

  const getMediaUrls = useCallback(async () => {
    const response = await fetch(`/media/contests/${contestId}/hero/urls`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch media URLs');
    }

    return await response.json();
  }, [contestId]);

  return {
    uploadMedia,
    deleteMedia,
    getMediaUrls,
    uploading,
    deleting
  };
};
```

---

## 🎯 **Integration Examples**

### **Contest Creation Form**

```tsx
import React, { useState } from 'react';
import { MediaUpload } from './MediaUpload';

export const ContestForm = () => {
  const [contestData, setContestData] = useState({
    name: '',
    description: '',
    // ... other fields
  });
  const [mediaData, setMediaData] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Create contest first
    const contestResponse = await fetch('/admin/contests', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify(contestData)
    });

    const contest = await contestResponse.json();
    
    // If media was uploaded, it's already associated with the contest
    // Navigate to contest details or show success message
    console.log('Contest created with media:', contest);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic contest fields */}
      <div>
        <label>Contest Name</label>
        <input
          type="text"
          value={contestData.name}
          onChange={(e) => setContestData({...contestData, name: e.target.value})}
        />
      </div>

      {/* Media upload section */}
      <div>
        <label className="block text-sm font-medium mb-2">Hero Image/Video</label>
        <MediaUpload
          contestId={contest?.id} // Pass contest ID after creation
          onUploadSuccess={(data) => {
            setMediaData(data);
            // Optionally update contestData.image_url with data.secure_url
          }}
          onUploadError={(error) => {
            console.error('Upload error:', error);
          }}
        />
      </div>

      <button type="submit">Create Contest</button>
    </form>
  );
};
```

### **Contest Card with Responsive Media**

```tsx
import React from 'react';
import { ResponsiveMedia } from './ResponsiveMedia';

export const ContestCard = ({ contest }) => {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Hero media */}
      <ResponsiveMedia
        contestId={contest.id}
        sizes="medium"
        className="w-full h-48 object-cover"
        fallbackUrl={contest.image_url}
      />
      
      {/* Contest details */}
      <div className="p-4">
        <h3 className="text-lg font-semibold">{contest.name}</h3>
        <p className="text-gray-600 mt-2">{contest.description}</p>
        
        <div className="mt-4 flex justify-between items-center">
          <span className="text-sm text-gray-500">
            Ends: {new Date(contest.end_time).toLocaleDateString()}
          </span>
          <button className="bg-blue-500 text-white px-4 py-2 rounded">
            Enter Contest
          </button>
        </div>
      </div>
    </div>
  );
};
```

### **Admin Contest Management**

```tsx
import React, { useState } from 'react';
import { useMediaManagement } from './useMediaManagement';

export const AdminContestEdit = ({ contest }) => {
  const { uploadMedia, deleteMedia, uploading, deleting } = useMediaManagement(contest.id);
  const [mediaUrls, setMediaUrls] = useState(null);

  const handleMediaUpload = async (file, mediaType) => {
    try {
      const result = await uploadMedia(file, mediaType);
      // Refresh media URLs
      const urls = await getMediaUrls();
      setMediaUrls(urls);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handleMediaDelete = async () => {
    try {
      await deleteMedia();
      setMediaUrls(null);
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  return (
    <div className="space-y-6">
      <h2>Edit Contest: {contest.name}</h2>
      
      {/* Media management section */}
      <div className="border rounded-lg p-4">
        <h3 className="text-lg font-medium mb-4">Hero Media</h3>
        
        {mediaUrls?.has_media ? (
          <div className="space-y-4">
            <img 
              src={mediaUrls.urls.large} 
              alt="Contest hero" 
              className="w-full max-w-md h-64 object-cover rounded"
            />
            <button
              onClick={handleMediaDelete}
              disabled={deleting}
              className="bg-red-500 text-white px-4 py-2 rounded disabled:opacity-50"
            >
              {deleting ? 'Deleting...' : 'Delete Media'}
            </button>
          </div>
        ) : (
          <MediaUpload
            contestId={contest.id}
            onUploadSuccess={handleMediaUpload}
            onUploadError={(error) => console.error(error)}
          />
        )}
      </div>
      
      {/* Other contest editing fields */}
    </div>
  );
};
```

---

## 🔒 **Security & Permissions**

### **Access Control**
- **Admins**: Can upload/delete media for any contest
- **Sponsors**: Can upload/delete media for their own contests only
- **Users**: Cannot upload/delete media (read-only access to URLs)

### **File Validation**
- **Supported Types**: Images (JPEG, PNG, WebP, GIF), Videos (MP4, MOV, AVI)
- **Size Limit**: 50MB maximum
- **Aspect Ratio**: 1:1 (1080x1080) recommended for consistency

### **Error Handling**
```javascript
// Handle common upload errors
const handleUploadError = (error) => {
  switch (error.code) {
    case 'FILE_TOO_LARGE':
      return 'File size must be less than 50MB';
    case 'INVALID_FILE_TYPE':
      return 'Please select an image or video file';
    case 'UNAUTHORIZED':
      return 'You do not have permission to upload media';
    case 'CONTEST_NOT_FOUND':
      return 'Contest not found';
    default:
      return error.message || 'Upload failed';
  }
};
```

---

## 🌍 **Environment Configuration**

### **Development**
```javascript
const API_BASE_URL = 'http://localhost:8000';
const CLOUDINARY_FOLDER = 'contestlet-develop';
```

### **Staging**
```javascript
const API_BASE_URL = 'https://contestlet-git-staging.vercel.app';
const CLOUDINARY_FOLDER = 'contestlet-staging';
```

### **Production**
```javascript
const API_BASE_URL = 'https://contestlet.vercel.app';
const CLOUDINARY_FOLDER = 'contestlet-production';
```

---

## 🧪 **Testing**

### **Unit Tests**
```javascript
// Test media upload hook
import { renderHook, act } from '@testing-library/react-hooks';
import { useMediaManagement } from './useMediaManagement';

test('should upload media successfully', async () => {
  const { result } = renderHook(() => useMediaManagement(123));
  
  const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
  
  await act(async () => {
    const response = await result.current.uploadMedia(mockFile, 'image');
    expect(response.contest_id).toBe(123);
  });
});
```

### **Integration Tests**
```javascript
// Test complete upload flow
test('should handle complete media upload flow', async () => {
  render(<MediaUpload contestId={123} onUploadSuccess={mockSuccess} />);
  
  const fileInput = screen.getByRole('button');
  const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
  
  await user.upload(fileInput, file);
  
  expect(mockSuccess).toHaveBeenCalledWith(
    expect.objectContaining({
      contest_id: 123,
      media_type: 'image'
    })
  );
});
```

---

## 📚 **Additional Resources**

### **API Documentation**
- **Interactive Docs**: https://contestlet.vercel.app/docs
- **API Reference**: [API_QUICK_REFERENCE.md](../api-integration/API_QUICK_REFERENCE.md)

### **Cloudinary Documentation**
- **Image Transformations**: https://cloudinary.com/documentation/image_transformations
- **Video Transformations**: https://cloudinary.com/documentation/video_manipulation_and_delivery
- **Responsive Images**: https://cloudinary.com/documentation/responsive_images

### **Best Practices**
- Use responsive image URLs for different screen sizes
- Implement proper loading states and error handling
- Cache media URLs to reduce API calls
- Use lazy loading for better performance
- Provide fallback content for missing media

---

## 🎉 **Ready to Go!**

Your Cloudinary media integration is now complete and ready for production use. The system provides:

✅ **Seamless Upload Experience**  
✅ **Automatic Optimization**  
✅ **Responsive Image Delivery**  
✅ **Secure Access Control**  
✅ **Environment Separation**  
✅ **Fallback Support**

**Happy coding! 🚀**
