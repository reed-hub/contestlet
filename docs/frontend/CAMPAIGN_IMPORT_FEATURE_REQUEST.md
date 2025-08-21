# 📋 Frontend Feature Request: Campaign Import from JSON

## 🎯 Overview
Add a campaign import feature that allows admins to import predefined campaign one-sheets (JSON files) directly into the contest management system via a new "Import Contest" button.

## 🎨 UI/UX Requirements

### **Main Admin View Changes**
- **Location**: Next to the existing "Create Contest" button
- **Button**: Add "Import Contest" button with upload icon
- **Layout**: 
  ```
  [Create Contest] [Import Contest]
  ```

### **Import Flow Design**

#### **Step 1: Import Button & Modal**
```jsx
// Main admin view button
<Button 
  variant="outline" 
  onClick={openImportModal}
  className="flex items-center gap-2"
>
  <Upload size={16} />
  Import Contest
</Button>
```

#### **Step 2: Import Modal UI**
Create a modal/dialog with the following sections:

**Modal Header:**
- Title: "Import Campaign One-Sheet"
- Subtitle: "Upload a JSON campaign file to create a new contest"

**Modal Body:**
1. **File Upload Area**
   - Drag & drop zone for JSON files
   - File picker button
   - File type validation (`.json` only)
   - File size limit display

2. **JSON Preview Section**
   - Code editor/textarea showing uploaded JSON
   - Syntax highlighting (optional)
   - Validation status indicator

3. **Override Options**
   - Location input field (optional override)
   - Start time picker (optional override)
   - Admin user ID field (auto-populated from auth)

**Modal Footer:**
- Cancel button
- Import button (disabled until valid JSON loaded)

#### **Step 3: Success/Error Handling**
- **Success**: Show success toast + redirect to contest view
- **Validation Errors**: Show inline error messages
- **API Errors**: Show error modal with details

## 🔌 API Integration

### **Endpoint**
```
POST /admin/contests/import-one-sheet
Authorization: Bearer {admin_token}
```

### **Request Payload**
```typescript
interface CampaignImportRequest {
  campaign_json: {
    name: string;
    description: string;
    day?: string;
    duration_days: number;
    entry_type?: string;
    reward_logic: {
      type: string;
      winner_reward: string;
      consolation_offer?: string;
    };
    messaging?: {
      initial_sms?: string;
      winner_sms?: string;
      non_winner_sms?: string;
      reminder_sms?: string;
    };
    promotion_channels?: string[];
    activation_hooks?: string[];
    // Additional fields allowed
  };
  location?: string;           // Optional override
  start_time?: string;         // Optional override (ISO format)
  admin_user_id?: string;      // Optional override
  latitude?: number;           // Optional override
  longitude?: number;          // Optional override
}
```

### **Response Handling**
```typescript
interface CampaignImportResponse {
  success: boolean;
  contest_id?: number;
  message: string;
  warnings?: string[];
  fields_mapped?: Record<string, string>;
  fields_stored_in_metadata?: string[];
}
```

## 📱 Component Implementation Guide

### **1. Import Button Component**
```tsx
// Add to main admin contest list view
const ImportContestButton = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  return (
    <>
      <Button 
        variant="outline"
        onClick={() => setIsModalOpen(true)}
        className="flex items-center gap-2"
      >
        <Upload size={16} />
        Import Contest
      </Button>
      
      <ImportCampaignModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};
```

### **2. Import Modal Component**
```tsx
const ImportCampaignModal = ({ isOpen, onClose }) => {
  const [jsonFile, setJsonFile] = useState(null);
  const [jsonContent, setJsonContent] = useState('');
  const [overrides, setOverrides] = useState({
    location: '',
    start_time: ''
  });
  const [isImporting, setIsImporting] = useState(false);
  
  const handleFileUpload = (file) => {
    // Validate JSON file
    // Parse and display content
    // Enable import button
  };
  
  const handleImport = async () => {
    try {
      setIsImporting(true);
      
      const payload = {
        campaign_json: JSON.parse(jsonContent),
        ...overrides
      };
      
      const response = await fetch('/admin/contests/import-one-sheet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success(`Contest "${result.contest_id}" imported successfully!`);
        router.push(`/admin/contests/${result.contest_id}`);
        onClose();
      } else {
        toast.error(result.message);
      }
    } catch (error) {
      toast.error('Failed to import campaign');
    } finally {
      setIsImporting(false);
    }
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      {/* Modal implementation */}
    </Modal>
  );
};
```

## 📄 Sample Campaign JSON

Provide this example in the UI for testing:

```json
{
  "name": "Margarita Monday Mystery",
  "description": "Each Monday, one lucky SMS subscriber wins a margarita + taco combo. Others get smaller perks.",
  "day": "Monday",
  "duration_days": 1,
  "entry_type": "SMS opt-in",
  "reward_logic": {
    "type": "random_winner",
    "winner_reward": "Free margarita + taco",
    "consolation_offer": "$2 off margaritas"
  },
  "messaging": {
    "initial_sms": "You're in! Margarita Monday winner announced tonight 🍹",
    "winner_sms": "🎉 You won Margarita Monday! Come in for your free drink + taco.",
    "non_winner_sms": "No win this week—but enjoy $2 off margaritas tonight 🍹"
  },
  "promotion_channels": [
    "in-store signage",
    "Instagram",
    "SMS reminder"
  ],
  "activation_hooks": [
    "show_sms_for_offer",
    "winner_announcement_in_IG_story"
  ]
}
```

## ✅ Validation Requirements

### **Frontend Validation**
1. **File Type**: Only `.json` files allowed
2. **File Size**: Max 1MB
3. **JSON Syntax**: Valid JSON format
4. **Required Fields**: 
   - `name` (non-empty string)
   - `description` (non-empty string)
   - `duration_days` (positive integer)
   - `reward_logic.winner_reward` (non-empty string)

### **Error Messages**
- **Invalid File**: "Please upload a valid JSON file"
- **Missing Required Fields**: "Campaign must include name, description, and reward logic"
- **Invalid JSON**: "Invalid JSON format. Please check syntax."
- **API Error**: Display backend error message

## 🎨 Design Specifications

### **Button Styling**
- **Position**: Right of "Create Contest" button
- **Icon**: Upload/import icon (lucide-react: `Upload`)
- **Variant**: Outline button to differentiate from primary action
- **Responsive**: Stack vertically on mobile

### **Modal Styling**
- **Size**: Large modal (md:max-w-2xl)
- **Sections**: Clear visual separation between upload, preview, and options
- **File Drop Zone**: Dashed border, hover effects
- **JSON Preview**: Monospace font, max height with scroll

### **States**
- **Loading**: Show spinner during import
- **Success**: Green checkmark + success message
- **Error**: Red error styling + clear error message

## 🧪 Testing Scenarios

1. **Happy Path**: Upload valid JSON → see preview → import successfully
2. **Invalid JSON**: Upload invalid file → see error message
3. **Missing Fields**: Upload incomplete campaign → see validation errors
4. **API Error**: Network error → see error handling
5. **Large File**: Upload large JSON → see file size error

## 🚀 Implementation Priority

### **Phase 1** (MVP)
- [x] Import button next to Create Contest
- [x] Basic file upload modal
- [x] JSON validation and preview
- [x] API integration
- [x] Success/error handling

### **Phase 2** (Enhancements)
- [ ] Drag & drop file upload
- [ ] JSON syntax highlighting
- [ ] Campaign preview before import
- [ ] Import history/log

## 📚 Dependencies

### **Required Packages**
```json
{
  "react-dropzone": "^14.2.3",     // File upload
  "@monaco-editor/react": "^4.6.0", // JSON editor (optional)
  "react-hot-toast": "^2.4.1"      // Toast notifications
}
```

### **API Requirements**
- Backend endpoint: `POST /admin/contests/import-one-sheet`
- Admin authentication token
- CORS configured for local development

## 🎯 Success Criteria

✅ **User can click "Import Contest" button**  
✅ **User can upload and validate JSON campaign file**  
✅ **User can see preview of campaign data**  
✅ **User can override location, start time, and active status**  
✅ **User receives clear feedback on success/failure**  
✅ **Imported contest appears in contest list**  
✅ **All campaign metadata preserved and accessible**

---

**🚀 Ready for Implementation!** 

This feature will enable rapid contest creation from predefined campaign templates, significantly improving admin workflow efficiency.
