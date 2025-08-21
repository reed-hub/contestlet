# 🎯 Contest Form Support Implementation Plan

## 📋 Form Field Analysis & Implementation Strategy

### ✅ **ALREADY SUPPORTED (Ready to Use)**
- Contest Name ✅
- Description ✅  
- Location ✅
- Prize Description ✅
- Prize Value (USD) ✅
- Eligibility Requirements ✅
- Start Date/Time ✅
- End Date/Time ✅
- Sponsor Name ✅
- Terms & Conditions URL ✅

### 🔧 **PHASE 1: Essential Backend Extensions (Immediate)**

#### **1.1 Database Schema Updates**
```sql
-- Add to contests table
ALTER TABLE contests ADD COLUMN contest_type VARCHAR(50) DEFAULT 'general';
ALTER TABLE contests ADD COLUMN entry_method VARCHAR(50) DEFAULT 'sms';
ALTER TABLE contests ADD COLUMN winner_selection_method VARCHAR(50) DEFAULT 'random';
ALTER TABLE contests ADD COLUMN minimum_age INTEGER DEFAULT 18;
ALTER TABLE contests ADD COLUMN max_entries_per_person INTEGER NULL;
ALTER TABLE contests ADD COLUMN total_entry_limit INTEGER NULL;
ALTER TABLE contests ADD COLUMN consolation_offer TEXT NULL;
ALTER TABLE contests ADD COLUMN geographic_restrictions TEXT NULL;
ALTER TABLE contests ADD COLUMN contest_tags JSON NULL;
ALTER TABLE contests ADD COLUMN promotion_channels JSON NULL;
```

#### **1.2 Schema Validation (app/schemas/admin.py)**
```python
class AdminContestCreate(ContestBase):
    # ... existing fields ...
    
    # Advanced configuration
    contest_type: Optional[str] = Field("general", description="Contest type")
    entry_method: Optional[str] = Field("sms", description="Entry method")
    winner_selection_method: Optional[str] = Field("random", description="Winner selection")
    minimum_age: Optional[int] = Field(18, ge=13, le=100, description="Minimum age")
    max_entries_per_person: Optional[int] = Field(None, ge=1, description="Max entries per person")
    total_entry_limit: Optional[int] = Field(None, ge=1, description="Total entry limit")
    consolation_offer: Optional[str] = Field(None, description="Consolation prize/offer")
    geographic_restrictions: Optional[str] = Field(None, description="Geographic restrictions")
    contest_tags: Optional[List[str]] = Field(None, description="Contest tags")
    promotion_channels: Optional[List[str]] = Field(None, description="Promotion channels")
```

#### **1.3 Business Logic Updates (app/routers/contests.py)**
```python
def validate_contest_entry(contest, user, db):
    # Age validation
    if contest.minimum_age and contest.minimum_age > 18:
        # Add age validation logic when user profiles support birth_date
        pass
    
    # Entry limit per person
    if contest.max_entries_per_person:
        user_entry_count = db.query(Entry).filter(
            Entry.contest_id == contest.id,
            Entry.user_id == user.id
        ).count()
        
        if user_entry_count >= contest.max_entries_per_person:
            raise HTTPException(400, f"Maximum {contest.max_entries_per_person} entries allowed")
    
    # Total entry limit
    if contest.total_entry_limit:
        total_entries = db.query(Entry).filter(Entry.contest_id == contest.id).count()
        if total_entries >= contest.total_entry_limit:
            raise HTTPException(400, "Contest entry limit reached")
```

### 🔧 **PHASE 2: SMS Templates System (Short-term)**

#### **2.1 New SMS Templates Model**
```python
# app/models/sms_template.py
class SMSTemplate(Base):
    __tablename__ = "sms_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    template_type = Column(String(50), nullable=False)  # entry_confirmation, winner, non_winner
    message_content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    contest = relationship("Contest", back_populates="sms_templates")
```

#### **2.2 Template Schema**
```python
# app/schemas/sms_template.py
class SMSTemplateCreate(BaseModel):
    template_type: str = Field(..., description="Template type")
    message_content: str = Field(..., description="SMS message content")

class SMSTemplateDict(BaseModel):
    entry_confirmation: Optional[str] = Field(None, description="Entry confirmation SMS")
    winner_notification: Optional[str] = Field(None, description="Winner SMS")
    non_winner: Optional[str] = Field(None, description="Non-winner SMS")
```

#### **2.3 Template Integration**
```python
# Add to AdminContestCreate
sms_templates: Optional[SMSTemplateDict] = Field(None, description="SMS message templates")
```

### 🔧 **PHASE 3: Form Field Mapping (Complete Implementation)**

#### **3.1 Frontend to Backend Field Mapping**

| Frontend Field | Backend Field | Type | Default |
|----------------|---------------|------|---------|
| Contest Type dropdown | `contest_type` | String | "general" |
| Entry Method dropdown | `entry_method` | String | "sms" |
| Winner Selection dropdown | `winner_selection_method` | String | "random" |
| Minimum Age input | `minimum_age` | Integer | 18 |
| Max Entries Per Person | `max_entries_per_person` | Integer/NULL | NULL (unlimited) |
| Total Entry Limit | `total_entry_limit` | Integer/NULL | NULL (unlimited) |
| Consolation Prize/Offer | `consolation_offer` | Text | NULL |
| Geographic Restrictions | `geographic_restrictions` | Text | NULL |
| Contest Tags | `contest_tags` | JSON Array | NULL |
| Promotion Channels checkboxes | `promotion_channels` | JSON Array | NULL |
| Entry Confirmation SMS | `sms_templates.entry_confirmation` | Text | NULL |
| Winner Notification SMS | `sms_templates.winner_notification` | Text | NULL |
| Non-Winner SMS | `sms_templates.non_winner` | Text | NULL |

#### **3.2 API Endpoint Updates**
```python
# app/routers/admin.py - Update create_contest
@router.post("/contests", response_model=AdminContestResponse)
async def create_contest(contest_data: AdminContestCreate, ...):
    # Extract SMS templates
    sms_templates = contest_data.sms_templates
    contest_dict = contest_data.dict(exclude={'official_rules', 'sms_templates'})
    
    # Create contest with all new fields
    contest = Contest(**contest_dict)
    db.add(contest)
    db.flush()
    
    # Create SMS templates if provided
    if sms_templates:
        for template_type, content in sms_templates.dict(exclude_unset=True).items():
            if content:
                template = SMSTemplate(
                    contest_id=contest.id,
                    template_type=template_type,
                    message_content=content
                )
                db.add(template)
    
    # ... rest of creation logic
```

## 🚀 **Implementation Timeline**

### **Week 1: Phase 1 (Essential Fields)**
- [ ] Add database columns
- [ ] Update schemas with validation
- [ ] Implement entry limit business logic
- [ ] Test basic form submission

### **Week 2: Phase 2 (SMS Templates)**
- [ ] Create SMS template model
- [ ] Add template schemas
- [ ] Integrate with contest creation
- [ ] Test template functionality

### **Week 3: Phase 3 (Complete Integration)**
- [ ] Full field mapping implementation
- [ ] Frontend-backend integration testing
- [ ] Edge case validation
- [ ] Production deployment

## 🧪 **Testing Strategy**

### **Form Submission Tests**
```bash
# Test with all fields
curl -X POST http://localhost:8000/admin/contests \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Contest",
    "description": "Full form test",
    "contest_type": "general",
    "entry_method": "sms",
    "winner_selection_method": "random",
    "minimum_age": 21,
    "max_entries_per_person": 5,
    "consolation_offer": "10% discount",
    "contest_tags": ["summer", "promo"],
    "promotion_channels": ["instagram", "email"],
    "sms_templates": {
      "entry_confirmation": "Thanks for entering!",
      "winner_notification": "You won!",
      "non_winner": "Thanks for playing!"
    },
    "official_rules": { ... }
  }'
```

## 📊 **Success Metrics**

### **Phase 1 Complete ✅**
- All form fields accepted by backend
- No validation errors on submission
- Entry limits enforced correctly

### **Phase 2 Complete ✅**
- SMS templates stored and retrievable
- Templates used in notification system
- Template variables working

### **Phase 3 Complete ✅**
- 100% form field support
- Full frontend-backend integration
- Production-ready contest creation

## 🎯 **Priority Order**

1. **🔥 Critical**: Minimum age, entry limits (legal/business requirements)
2. **🚀 High**: Contest type, consolation offers (marketing features)
3. **📋 Medium**: Geographic restrictions, promotion channels (analytics)
4. **🎨 Nice-to-have**: Advanced SMS templates, contest tags (enhancement)

**This plan ensures complete form support within 3 weeks with incremental deployments.** 🚀
