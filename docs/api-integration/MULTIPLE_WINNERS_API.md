# 🏆 Multiple Winners API Documentation

## 📋 **Overview**

The Multiple Winners feature allows contests to have 1-50 winners with different prize tiers and comprehensive winner management capabilities. This enhancement maintains full backward compatibility with single-winner contests while providing powerful new functionality for sponsors.

### **Key Features**
- **1-50 Winners**: Configure any number of winners per contest
- **Prize Tiers**: Optional structured prize information for each winner position
- **Winner Management**: Reselect, notify, track claims, and remove winners
- **Backward Compatibility**: Existing single-winner endpoints continue to work
- **Position-Based**: Winners have positions (1st, 2nd, 3rd place, etc.)

---

## 🎯 **Business Use Cases**

### **Example Contest Types**
```json
// Simple multiple winners
{
  "name": "3 Lucky Winners Contest",
  "winner_count": 3,
  "prize_description": "$50 gift cards for all winners"
}

// Tiered prizes
{
  "name": "Grand Prize Contest",
  "winner_count": 3,
  "prize_tiers": {
    "tiers": [
      {"position": 1, "prize": "$100 Gift Card", "description": "First place winner"},
      {"position": 2, "prize": "$50 Gift Card", "description": "Second place winner"},
      {"position": 3, "prize": "$25 Gift Card", "description": "Third place winner"}
    ]
  }
}

// Large giveaway
{
  "name": "Holiday Giveaway",
  "winner_count": 10,
  "prize_description": "Free product samples for 10 winners"
}
```

---

## 🔧 **Database Schema**

### **New Tables**

#### **contest_winners**
```sql
CREATE TABLE contest_winners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER NOT NULL,
    entry_id INTEGER NOT NULL,
    winner_position INTEGER NOT NULL,  -- 1st, 2nd, 3rd place, etc.
    prize_description TEXT,
    selected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notified_at DATETIME DEFAULT NULL,
    claimed_at DATETIME DEFAULT NULL,
    
    FOREIGN KEY (contest_id) REFERENCES contests(id),
    FOREIGN KEY (entry_id) REFERENCES entries(id),
    UNIQUE(contest_id, entry_id),      -- One entry can't win multiple times
    UNIQUE(contest_id, winner_position) -- One position per contest
);
```

### **Enhanced contests Table**
```sql
-- New fields added to existing contests table
ALTER TABLE contests ADD COLUMN winner_count INTEGER DEFAULT 1 NOT NULL;
ALTER TABLE contests ADD COLUMN prize_tiers TEXT DEFAULT NULL; -- JSON as TEXT
```

---

## 🚀 **API Endpoints**

### **1. Multiple Winner Selection**

#### **POST /admin/contests/{contest_id}/select-winners**
Select multiple winners for a contest with optional prize tiers.

**Request Body:**
```json
{
  "winner_count": 3,
  "selection_method": "random",
  "prize_tiers": [
    {"position": 1, "prize": "$100 Gift Card", "description": "First place"},
    {"position": 2, "prize": "$50 Gift Card", "description": "Second place"},
    {"position": 3, "prize": "$25 Gift Card", "description": "Third place"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully selected 3 winners",
  "winners": [
    {
      "id": 1,
      "contest_id": 123,
      "entry_id": 456,
      "winner_position": 1,
      "prize_description": "$100 Gift Card",
      "selected_at": "2024-01-15T10:30:00Z",
      "notified_at": null,
      "claimed_at": null,
      "phone": "+1234567890",
      "is_notified": false,
      "is_claimed": false
    }
    // ... more winners
  ],
  "total_winners": 3,
  "total_entries": 150,
  "selection_method": "random"
}
```

### **2. Winner Management**

#### **GET /admin/contests/{contest_id}/winners**
Get all winners for a contest with their positions and status.

**Response:**
```json
{
  "contest_id": 123,
  "contest_name": "Multi-Winner Contest",
  "winner_count": 3,
  "selected_winners": 2,
  "winners": [
    {
      "id": 1,
      "winner_position": 1,
      "prize_description": "$100 Gift Card",
      "phone": "+1234567890",
      "is_notified": true,
      "is_claimed": false,
      "selected_at": "2024-01-15T10:30:00Z"
    }
    // ... more winners
  ],
  "prize_tiers": {
    "tiers": [
      {"position": 1, "prize": "$100 Gift Card"},
      {"position": 2, "prize": "$50 Gift Card"}
    ]
  }
}
```

#### **POST /admin/contests/{contest_id}/winners/{position}/manage**
Manage individual winners (reselect, notify, mark claimed, remove).

**Request Body:**
```json
{
  "action": "reselect",  // or "notify", "mark_claimed", "remove"
  "custom_message": "Congratulations! You won first place!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Winner at position 1 reselected",
  "winner": {
    "id": 2,
    "winner_position": 1,
    "entry_id": 789,
    "phone": "+1987654321",
    "selected_at": "2024-01-15T11:00:00Z"
  }
}
```

### **3. Winner Notifications**

#### **POST /admin/contests/{contest_id}/winners/notify**
Send notifications to contest winners.

**Request Body:**
```json
{
  "winner_positions": [1, 2],  // null = notify all winners
  "custom_message": "Congratulations! You won {prize_description}!",
  "test_mode": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sent 2 notifications, 0 failed",
  "notifications_sent": 2,
  "failed_notifications": 0,
  "details": [
    {
      "position": 1,
      "phone": "+1234567890",
      "status": "sent",
      "prize": "$100 Gift Card"
    },
    {
      "position": 2,
      "phone": "+1987654321",
      "status": "sent",
      "prize": "$50 Gift Card"
    }
  ]
}
```

### **4. Winner Statistics**

#### **GET /admin/contests/{contest_id}/winners/stats**
Get winner statistics and management overview.

**Response:**
```json
{
  "contest_id": 123,
  "contest_name": "Multi-Winner Contest",
  "winner_count": 3,
  "selected_winners": 3,
  "notified_winners": 2,
  "claimed_winners": 1,
  "notification_rate": 0.67,
  "claim_rate": 0.33,
  "has_prize_tiers": true
}
```

### **5. Legacy Compatibility**

#### **POST /admin/contests/{contest_id}/select-winner**
Legacy single winner selection (maintained for backward compatibility).

**Response:**
```json
{
  "success": true,
  "message": "Winner selected: +1234567890",
  "winner_entry_id": 456,
  "winner_phone": "+1234567890",
  "total_entries": 150
}
```

---

## 📊 **Contest Creation with Multiple Winners**

### **Enhanced Contest Schema**

When creating contests, you can now specify winner configuration:

```json
{
  "name": "Multi-Winner Contest",
  "description": "Contest with multiple winners",
  "start_time": "2024-01-15T00:00:00Z",
  "end_time": "2024-01-22T23:59:59Z",
  "prize_description": "Various prizes for winners",
  
  // Multiple winners configuration
  "winner_count": 5,
  "prize_tiers": {
    "tiers": [
      {"position": 1, "prize": "$500 Grand Prize"},
      {"position": 2, "prize": "$200 Second Prize"},
      {"position": 3, "prize": "$100 Third Prize"},
      {"position": 4, "prize": "$50 Fourth Prize"},
      {"position": 5, "prize": "$25 Fifth Prize"}
    ],
    "total_value": 875,
    "currency": "USD"
  },
  
  // ... other contest fields
}
```

### **Contest Response with Winners**

Contest responses now include winner information:

```json
{
  "id": 123,
  "name": "Multi-Winner Contest",
  
  // Legacy winner fields (for backward compatibility)
  "winner_entry_id": 456,
  "winner_phone": "+1234567890",
  "winner_selected_at": "2024-01-15T10:30:00Z",
  
  // Multiple winners fields
  "winner_count": 5,
  "selected_winners": 3,
  "prize_tiers": {
    "tiers": [
      {"position": 1, "prize": "$500 Grand Prize"},
      {"position": 2, "prize": "$200 Second Prize"}
    ]
  }
}
```

---

## 🔄 **Winner Selection Workflow**

### **1. Contest Setup**
```javascript
// Create contest with multiple winners
const contest = await api.createContest({
  name: "Holiday Giveaway",
  winner_count: 3,
  prize_tiers: {
    tiers: [
      {position: 1, prize: "$100 Gift Card"},
      {position: 2, prize: "$50 Gift Card"},
      {position: 3, prize: "$25 Gift Card"}
    ]
  }
  // ... other fields
});
```

### **2. Winner Selection**
```javascript
// Select multiple winners
const result = await api.selectMultipleWinners(contestId, {
  winner_count: 3,
  selection_method: "random",
  prize_tiers: [
    {position: 1, prize: "$100 Gift Card"},
    {position: 2, prize: "$50 Gift Card"},
    {position: 3, prize: "$25 Gift Card"}
  ]
});

console.log(`Selected ${result.total_winners} winners from ${result.total_entries} entries`);
```

### **3. Winner Management**
```javascript
// Get all winners
const winners = await api.getContestWinners(contestId);

// Reselect first place winner
await api.manageWinner(contestId, 1, {
  action: "reselect"
});

// Notify all winners
await api.notifyWinners(contestId, {
  custom_message: "Congratulations! You won {prize_description}!"
});

// Mark winner as claimed
await api.manageWinner(contestId, 1, {
  action: "mark_claimed"
});
```

---

## 🎯 **Frontend Integration**

### **Contest Creation Form**

```tsx
// Winner count configuration
<div className="form-group">
  <label>Number of Winners</label>
  <input 
    type="number" 
    min="1" 
    max="50" 
    value={winnerCount}
    onChange={(e) => setWinnerCount(parseInt(e.target.value))}
  />
</div>

// Prize tier configuration (optional)
{winnerCount > 1 && (
  <div className="prize-tiers">
    <h3>Prize Tiers (Optional)</h3>
    {Array.from({length: winnerCount}).map((_, i) => (
      <div key={i} className="prize-tier">
        <label>{getOrdinal(i + 1)} Place Prize</label>
        <input 
          placeholder="e.g., $100 Gift Card"
          value={prizeTiers[i]?.prize || ''}
          onChange={(e) => updatePrizeTier(i, e.target.value)}
        />
      </div>
    ))}
  </div>
)}
```

### **Contest Display**

```tsx
// Dynamic winner display
<div className="winner-section">
  <div className="text-center mb-4">
    <div className="text-3xl mb-2">👑</div>
    <div className="text-sm font-sans">
      {contest.winner_count === 1 ? "1 WINNER" : `${contest.winner_count} WINNERS`}
    </div>
  </div>
  
  {/* Show prize tiers or simple description */}
  {contest.prize_tiers ? (
    <div className="prize-tiers">
      {contest.prize_tiers.tiers.map((tier, i) => (
        <div key={i} className="text-center mb-2">
          <span className="font-bold">{getOrdinal(tier.position)} Place:</span> {tier.prize}
        </div>
      ))}
    </div>
  ) : (
    <div className="text-center">
      <span className="font-bold">{contest.prize_description}</span>
    </div>
  )}
</div>
```

### **Admin Winner Management**

```tsx
// Winner management interface
<div className="winner-management">
  <h3>Contest Winners ({selectedWinners}/{winnerCount})</h3>
  
  {!hasWinners && (
    <button 
      onClick={() => selectWinners()}
      className="btn-primary"
    >
      Select {winnerCount} Winners
    </button>
  )}
  
  {winners.map((winner) => (
    <div key={winner.id} className="winner-card">
      <div className="winner-info">
        <span className="position">{getOrdinal(winner.winner_position)} Place</span>
        <span className="phone">{winner.phone}</span>
        <span className="prize">{winner.prize_description}</span>
      </div>
      
      <div className="winner-status">
        <span className={`status ${winner.is_notified ? 'notified' : 'pending'}`}>
          {winner.is_notified ? '✓ Notified' : 'Not Notified'}
        </span>
        <span className={`status ${winner.is_claimed ? 'claimed' : 'unclaimed'}`}>
          {winner.is_claimed ? '✓ Claimed' : 'Unclaimed'}
        </span>
      </div>
      
      <div className="winner-actions">
        <button onClick={() => reselectWinner(winner.winner_position)}>
          Reselect
        </button>
        {!winner.is_notified && (
          <button onClick={() => notifyWinner(winner.winner_position)}>
            Notify
          </button>
        )}
        {!winner.is_claimed && (
          <button onClick={() => markClaimed(winner.winner_position)}>
            Mark Claimed
          </button>
        )}
      </div>
    </div>
  ))}
</div>
```

---

## 🔒 **Business Rules & Validation**

### **Winner Selection Rules**
1. **Contest Status**: Contest must be "ended" to select winners
2. **Entry Requirements**: Must have enough eligible entries for winner count
3. **Unique Winners**: Each entry can only win once per contest
4. **Position Uniqueness**: Each winner position is unique per contest
5. **No Duplicate Selection**: Cannot select winners if already selected (use reselect instead)

### **Prize Tier Validation**
1. **Position Sequence**: Positions must be sequential starting from 1
2. **Count Match**: Number of prize tiers must match winner count (if provided)
3. **Position Uniqueness**: Each position can only appear once

### **Winner Management Rules**
1. **Reselection**: Can reselect any winner position, resets notification/claim status
2. **Notification**: Can notify winners multiple times, tracks latest notification
3. **Claim Tracking**: Can mark winners as claimed, cannot undo claim status
4. **Removal**: Can remove winners, adjusts contest winner count accordingly

---

## 📈 **Migration & Backward Compatibility**

### **Automatic Migration**
- Existing single winners automatically migrated to `contest_winners` table
- Legacy fields (`winner_entry_id`, `winner_phone`, `winner_selected_at`) maintained
- Default `winner_count = 1` for existing contests

### **API Compatibility**
- All existing single-winner endpoints continue to work unchanged
- New multiple-winner endpoints are additive, not breaking changes
- Legacy responses include both old and new winner fields

### **Frontend Compatibility**
- Existing single-winner UI continues to work
- New multiple-winner features are opt-in
- Winner count defaults to 1 for backward compatibility

---

## 🎉 **Success Metrics**

### **Functional Requirements** ✅
- ✅ Sponsors can configure 1-50 winners per contest
- ✅ System randomly selects specified number of winners
- ✅ Each winner gets unique position (no duplicates)
- ✅ Frontend displays winner count dynamically
- ✅ Admin can manage/reselect individual winners
- ✅ Backward compatibility with single-winner contests

### **Technical Requirements** ✅
- ✅ Database constraints prevent duplicate winners
- ✅ API handles concurrent winner selection safely
- ✅ Frontend gracefully handles 1-N winners
- ✅ Migration preserves existing winner data
- ✅ Performance acceptable for contests with 1000+ entries

---

## 🚀 **Next Steps**

### **Phase 2 Enhancements**
- **Manual Winner Selection**: Allow admins to manually pick specific entries
- **Winner Replacement**: Advanced reselection with entry exclusion rules
- **Bulk Operations**: Select/notify/manage multiple winners simultaneously
- **Winner Analytics**: Detailed reporting and winner behavior tracking
- **Advanced Prize Tiers**: Conditional prizes based on entry criteria

### **Integration Points**
- **SMS Templates**: Enhanced templates with winner position variables
- **Email Notifications**: Winner notifications via email
- **Webhook Integration**: Real-time winner selection notifications
- **Export Features**: Winner lists for external prize fulfillment

---

**🏆 The Multiple Winners feature is now production-ready and fully integrated into the Contestlet platform!**
