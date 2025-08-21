# 🔧 Missing Backend Fields for Contest Creation

## 📋 Analysis Summary

The frontend contest creation form includes several advanced fields that are **not currently supported** by the backend API. Here's what needs to be implemented:

## ❌ **Missing Backend Fields:**

### **1. Contest Configuration**
```python
# app/models/contest.py - ADD THESE FIELDS:
class Contest(Base):
    # ... existing fields ...
    
    # Contest type and method
    contest_type: str = Column(String(50), default="general")  # general, sweepstakes, instant_win
    entry_method: str = Column(String(50), default="sms")      # sms, email, web_form
    winner_selection_method: str = Column(String(50), default="random")  # random, scheduled, instant
    
    # Entry limitations
    minimum_age: int = Column(Integer, default=18)
    max_entries_per_person: Optional[int] = Column(Integer, nullable=True)  # NULL = unlimited
    total_entry_limit: Optional[int] = Column(Integer, nullable=True)       # NULL = unlimited
    
    # Additional prize info
    consolation_offer: Optional[str] = Column(Text, nullable=True)
    
    # Geographic and targeting
    geographic_restrictions: Optional[str] = Column(Text, nullable=True)
    contest_tags: Optional[str] = Column(Text, nullable=True)  # JSON array of tags
    
    # Marketing
    promotion_channels: Optional[str] = Column(Text, nullable=True)  # JSON array
```

### **2. SMS Message Templates**
```python
# app/models/sms_template.py - NEW MODEL:
class SMSTemplate(Base):
    __tablename__ = "sms_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    template_type = Column(String(50), nullable=False)  # entry_confirmation, winner, non_winner
    message_content = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)  # Available template variables
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Relationship
    contest = relationship("Contest", back_populates="sms_templates")
```

### **3. Schema Updates**
```python
# app/schemas/admin.py - ADD TO AdminContestCreate:
class AdminContestCreate(ContestBase):
    # ... existing fields ...
    
    # Contest configuration
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
    
    # SMS templates
    sms_templates: Optional[Dict[str, str]] = Field(None, description="SMS message templates")
```

## 🚀 **Quick Implementation Strategy:**

### **Phase 1: Essential Fields (High Priority)**
1. **Minimum Age** - Required for legal compliance
2. **Max Entries Per Person** - Common business requirement  
3. **Consolation Offer** - Marketing feature
4. **Contest Tags** - Organization and filtering

### **Phase 2: Advanced Features (Medium Priority)**
5. **Winner Selection Method** - Currently only random
6. **Entry Method** - Currently only SMS
7. **Geographic Restrictions** - Compliance feature
8. **Promotion Channels** - Marketing analytics

### **Phase 3: Templates (Lower Priority)**
9. **SMS Message Templates** - Customization feature
10. **Contest Type** - Advanced categorization

## 🔧 **Immediate Action Items:**

### **1. Database Migration**
```sql
-- Add essential fields to contests table
ALTER TABLE contests ADD COLUMN minimum_age INTEGER DEFAULT 18;
ALTER TABLE contests ADD COLUMN max_entries_per_person INTEGER;
ALTER TABLE contests ADD COLUMN consolation_offer TEXT;
ALTER TABLE contests ADD COLUMN contest_tags TEXT;  -- JSON array
```

### **2. Schema Validation**
```python
# app/schemas/admin.py
@validator('minimum_age')
def validate_minimum_age(cls, v):
    if v < 13:  # COPPA compliance
        raise ValueError('Minimum age cannot be less than 13')
    return v

@validator('max_entries_per_person')  
def validate_max_entries(cls, v):
    if v is not None and v < 1:
        raise ValueError('Max entries must be at least 1')
    return v
```

### **3. Business Logic Updates**
```python
# app/routers/contests.py - UPDATE entry validation:
def validate_contest_entry(contest, user, db):
    # Check minimum age (if user has birthday field)
    if hasattr(user, 'birth_date') and contest.minimum_age:
        age = calculate_age(user.birth_date)
        if age < contest.minimum_age:
            raise HTTPException(400, f"Must be at least {contest.minimum_age} years old")
    
    # Check max entries per person
    if contest.max_entries_per_person:
        user_entries = db.query(Entry).filter(
            Entry.contest_id == contest.id,
            Entry.user_id == user.id
        ).count()
        
        if user_entries >= contest.max_entries_per_person:
            raise HTTPException(400, f"Maximum {contest.max_entries_per_person} entries per person")
```

## 🎯 **Current Form Support Status:**

| Form Section | Backend Support | Action Needed |
|-------------|----------------|---------------|
| **Basic Info** | ✅ 100% Complete | None |
| **Prize & Rules** | ✅ 100% Complete | None |
| **Date/Time** | ✅ 100% Complete | None |
| **Advanced Options** | ❌ 20% Complete | Implement missing fields |
| **SMS Templates** | ❌ 0% Complete | Build template system |

## 📞 **Recommendation:**

**Implement Phase 1 fields immediately** to support the frontend form. The current backend will **reject** the advanced form fields, causing creation failures.

**Priority Order:**
1. 🔥 **Minimum Age** (legal requirement)
2. 🔥 **Max Entries** (business logic)
3. 🔥 **Consolation Offer** (marketing feature)  
4. 📋 **Contest Tags** (organization)
5. 📋 **Remaining fields** (nice-to-have)

**The frontend form is more advanced than the current backend supports!** 🚨
