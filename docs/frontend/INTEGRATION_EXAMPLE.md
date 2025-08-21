# 🔧 Frontend Integration Example

## 📋 Quick Implementation Guide

### **1. Add Import Button to Admin Contest List**

```tsx
// In your main admin contests view component
// Likely in: src/pages/admin/contests/index.tsx or similar

const AdminContestsPage = () => {
  const [showImportModal, setShowImportModal] = useState(false);
  
  return (
    <div className="admin-contests-page">
      {/* Header with action buttons */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Contests</h1>
        
        <div className="flex gap-3">
          {/* Existing Create Contest button */}
          <Button 
            onClick={() => router.push('/admin/contests/new')}
            className="flex items-center gap-2"
          >
            <Plus size={16} />
            Create Contest
          </Button>
          
          {/* NEW: Import Contest button */}
          <Button 
            variant="outline"
            onClick={() => setShowImportModal(true)}
            className="flex items-center gap-2"
          >
            <Upload size={16} />
            Import Contest
          </Button>
        </div>
      </div>
      
      {/* Your existing contest list */}
      <ContestList contests={contests} />
      
      {/* NEW: Import Modal */}
      <ImportCampaignModal 
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onSuccess={(contestId) => {
          setShowImportModal(false);
          router.push(`/admin/contests/${contestId}`);
        }}
      />
    </div>
  );
};
```

### **2. Simple Import Modal Component**

```tsx
// Create: src/components/admin/ImportCampaignModal.tsx

import { useState } from 'react';
import { Upload, X, CheckCircle, AlertCircle } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'react-hot-toast';

export const ImportCampaignModal = ({ isOpen, onClose, onSuccess }) => {
  const { token } = useAuth();
  const [step, setStep] = useState('upload'); // 'upload' | 'preview' | 'importing'
  const [jsonContent, setJsonContent] = useState('');
  const [campaignData, setCampaignData] = useState(null);
  const [overrides, setOverrides] = useState({
    location: '',
    start_time: '',
    active: false
  });
  
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    if (file.type !== 'application/json') {
      toast.error('Please upload a JSON file');
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target.result;
        const parsed = JSON.parse(content);
        
        // Basic validation
        if (!parsed.name || !parsed.description || !parsed.reward_logic?.winner_reward) {
          toast.error('Invalid campaign JSON: missing required fields');
          return;
        }
        
        setJsonContent(content);
        setCampaignData(parsed);
        setStep('preview');
      } catch (error) {
        toast.error('Invalid JSON format');
      }
    };
    reader.readAsText(file);
  };
  
  const handleImport = async () => {
    setStep('importing');
    
    try {
      const payload = {
        campaign_json: campaignData,
        ...overrides,
        start_time: overrides.start_time || undefined
      };
      
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/admin/contests/import-one-sheet`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success(`Campaign "${campaignData.name}" imported successfully!`);
        onSuccess(result.contest_id);
      } else {
        toast.error(result.message || 'Import failed');
        setStep('preview');
      }
    } catch (error) {
      toast.error('Failed to import campaign');
      setStep('preview');
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold">Import Campaign One-Sheet</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>
        
        <div className="p-6">
          {step === 'upload' && (
            <div className="space-y-4">
              <p className="text-gray-600">Upload a JSON campaign file to create a new contest</p>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-900 mb-2">Upload Campaign JSON</p>
                <p className="text-gray-500 mb-4">Select a .json file to import</p>
                
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileUpload}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>
            </div>
          )}
          
          {step === 'preview' && campaignData && (
            <div className="space-y-6">
              {/* Campaign Preview */}
              <div>
                <h3 className="text-lg font-medium mb-3">Campaign Preview</h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  <div><strong>Name:</strong> {campaignData.name}</div>
                  <div><strong>Description:</strong> {campaignData.description}</div>
                  <div><strong>Duration:</strong> {campaignData.duration_days} day(s)</div>
                  <div><strong>Prize:</strong> {campaignData.reward_logic.winner_reward}</div>
                  {campaignData.day && <div><strong>Day:</strong> {campaignData.day}</div>}
                </div>
              </div>
              
              {/* Override Options */}
              <div>
                <h3 className="text-lg font-medium mb-3">Optional Overrides</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Location
                    </label>
                    <input
                      type="text"
                      value={overrides.location}
                      onChange={(e) => setOverrides(prev => ({ ...prev, location: e.target.value }))}
                      placeholder="e.g., Boulder, CO"
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Time
                    </label>
                    <input
                      type="datetime-local"
                      value={overrides.start_time}
                      onChange={(e) => setOverrides(prev => ({ ...prev, start_time: e.target.value }))}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="active"
                      checked={overrides.active}
                      onChange={(e) => setOverrides(prev => ({ ...prev, active: e.target.checked }))}
                      className="mr-2"
                    />
                    <label htmlFor="active" className="text-sm font-medium text-gray-700">
                      Make contest active immediately
                    </label>
                  </div>
                </div>
              </div>
              
              {/* Actions */}
              <div className="flex justify-end gap-3">
                <Button variant="outline" onClick={() => setStep('upload')}>
                  Back
                </Button>
                <Button onClick={handleImport}>
                  Import Campaign
                </Button>
              </div>
            </div>
          )}
          
          {step === 'importing' && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-lg font-medium">Importing campaign...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
```

### **3. Add to Your Button Components**

```tsx
// If you have a shared Button component, make sure it supports these props:
const Button = ({ variant = "primary", children, onClick, className, ...props }) => {
  const baseClasses = "px-4 py-2 rounded-md font-medium transition-colors";
  const variantClasses = {
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    outline: "border border-gray-300 text-gray-700 hover:bg-gray-50"
  };
  
  return (
    <button 
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
};
```

### **4. Testing with Sample JSON**

```json
{
  "name": "Test Campaign Import",
  "description": "Testing the campaign import functionality",
  "duration_days": 1,
  "reward_logic": {
    "type": "random_winner",
    "winner_reward": "Free coffee"
  },
  "messaging": {
    "initial_sms": "You're entered!",
    "winner_sms": "🎉 You won!"
  }
}
```

## 🚀 Quick Start Checklist

- [ ] Add Import button next to Create Contest button
- [ ] Create ImportCampaignModal component
- [ ] Test file upload and JSON validation
- [ ] Test API integration with backend
- [ ] Test success/error flows
- [ ] Style to match existing admin interface

**The backend is ready and waiting for these API calls!** 🎯
