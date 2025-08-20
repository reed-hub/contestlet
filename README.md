# Contestlet Backend API

A FastAPI backend for hosting micro sweepstakes-style contests across the U.S.

## Features

- **🔐 OTP-based Authentication** using phone numbers with Twilio/mock SMS
- **📍 Geolocation Support** for contests with nearby search using Haversine distance
- **🎯 Contest Management** with geofencing capabilities
- **🛡️ Rate Limiting** to prevent OTP abuse
- **📱 Entry System** for users to participate in contests
- **🗄️ SQLAlchemy ORM** with easy PostgreSQL migration
- **🚀 RESTful API** with proper validation and documentation

## 📚 Documentation

### For Frontend Developers
👉 **[Frontend Integration Guide](./docs/api-integration/)** - Complete documentation for integrating with the Contestlet API

**What's included:**
- 📖 Step-by-step integration guide
- 📋 Quick API reference
- 🛠️ Ready-to-use JavaScript SDK
- 🎪 Interactive demo page

### For Backend Developers
Continue reading this README for API details, deployment, and server configuration.

## Project Structure

```
contestlet/
├── app/
│   ├── core/           # Configuration and auth utilities
│   ├── database/       # Database configuration
│   ├── models/         # SQLAlchemy models
│   ├── routers/        # API route handlers
│   ├── schemas/        # Pydantic schemas
│   └── main.py         # FastAPI application
├── docs/               # Documentation
│   └── api-integration/ # Frontend integration guides
├── requirements.txt    # Python dependencies
└── README.md
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment (optional):**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /auth/request-otp` - Request OTP code for phone verification (with rate limiting)
- `POST /auth/verify-otp` - Verify OTP code and get JWT token
- `POST /auth/verify-phone` - Legacy endpoint (deprecated)

### Contests
- `GET /contests/active` - List active contests (with optional location filter)
- `GET /contests/nearby` - Find contests near a location using lat/lng and radius
- `POST /contests/{contest_id}/enter` - Enter a contest

### Entries
- `GET /entries/me` - Get current user's contest entries

### Admin (Bearer Token Required)
- `GET /admin/auth` - Verify admin authentication
- `POST /admin/contests` - Create contest with mandatory official rules
- `GET /admin/contests` - List all contests with admin details
- `PUT /admin/contests/{id}` - Update contest and official rules
- `POST /admin/contests/{id}/select-winner` - Randomly select winner from entries

## Database Models

### User
- `id` (Primary Key)
- `phone` (Unique identifier)
- `created_at`

### Contest
- `id` (Primary Key)
- `name`
- `description`
- `location` (city/state/zip)
- `latitude` (for geolocation)
- `longitude` (for geolocation)
- `start_time`
- `end_time`
- `prize_description`
- `active` (boolean)
- `created_at`

### Entry
- `id` (Primary Key)
- `user_id` (Foreign Key to User)
- `contest_id` (Foreign Key to Contest)
- `created_at`
- `selected` (boolean for winners)

### OTP
- `id` (Primary Key)
- `phone` (phone number)
- `code` (6-digit OTP code)
- `created_at`
- `expires_at`
- `verified` (boolean)
- `attempts` (number of verification attempts)

### OfficialRules
- `id` (Primary Key)
- `contest_id` (Foreign Key to Contest)
- `eligibility_text` (legal eligibility requirements)
- `sponsor_name` (contest sponsor)
- `start_date` / `end_date` (official contest dates)
- `prize_value_usd` (monetary value of prize)
- `terms_url` (optional link to full terms)
- `created_at` / `updated_at`

## Database Migration

The project uses SQLite by default but is designed for easy PostgreSQL migration:

1. Install PostgreSQL dependencies:
   ```bash
   pip install psycopg2-binary
   ```

2. Update `DATABASE_URL` in your environment:
   ```
   DATABASE_URL=postgresql://user:password@localhost/contestlet
   ```

3. The application will automatically use PostgreSQL.

## Development

The project is structured for maintainability:

- **Models**: Database schema definitions
- **Schemas**: Request/response validation
- **Routers**: API endpoint logic
- **Core**: Authentication and configuration
- **Database**: Database setup and utilities

## Authentication & SMS Integration

### OTP Flow
1. User requests OTP via `POST /auth/request-otp` with phone number
2. System generates 6-digit code and sends via SMS (or mock)
3. User verifies OTP via `POST /auth/verify-otp` with phone + code
4. System returns JWT token on successful verification

### SMS Configuration
- **Mock Mode** (default): OTP codes printed to console for testing
- **Twilio Integration**: Set `USE_MOCK_SMS=false` and configure Twilio credentials
- **Rate Limiting**: Max 5 OTP requests per 5-minute window per phone number

### Environment Variables
```env
# SMS Settings
USE_MOCK_SMS=true                    # Set to false for real SMS
TWILIO_ACCOUNT_SID=your_account_sid  # Required for real SMS
TWILIO_AUTH_TOKEN=your_auth_token    # Required for real SMS
TWILIO_PHONE_NUMBER=+1234567890      # Your Twilio phone number

# Rate Limiting
RATE_LIMIT_REQUESTS=5    # Max requests per window
RATE_LIMIT_WINDOW=300    # Window in seconds (5 minutes)

# Admin Settings
ADMIN_TOKEN=your-super-secret-admin-token  # Change in production
```

## Geolocation Features

### Contest Geofencing
- Contests can include latitude/longitude coordinates
- Enables location-based contest discovery and filtering
- Supports radius-based searches using the Haversine formula

### Nearby Contests API
```http
GET /contests/nearby?lat=40.7589&lng=-73.9851&radius=25
```

**Parameters:**
- `lat`: Latitude (-90 to 90)
- `lng`: Longitude (-180 to 180) 
- `radius`: Search radius in miles (default: 25, max: 100)
- `page`: Page number for pagination
- `size`: Results per page

**Response:**
- Returns contests within the specified radius
- Includes `distance_miles` field showing distance from query point
- Results sorted by distance (closest first)
- Standard pagination support

### Distance Calculation
Uses the Haversine formula for great-circle distance calculation:
- Accounts for Earth's curvature
- Returns distances in miles
- Accurate for most use cases under 100 miles

## Admin & Compliance Features

### Legal Compliance
- **Mandatory Official Rules**: All contests require complete legal documentation
- **Required Fields**: Eligibility text, sponsor name, dates, prize value
- **Validation**: Contests cannot be activated without proper compliance data
- **Audit Trail**: Created/updated timestamps for all admin actions

### Contest Management
- **Create**: Full contest creation with integrated official rules
- **Update**: Modify contests and rules with validation
- **List**: Admin view with entry counts and compliance status
- **Winner Selection**: Random selection from eligible entries

### Admin Authentication
```bash
# Admin API requests require Bearer token
curl -H "Authorization: Bearer your-admin-token" \
     http://localhost:8000/admin/contests
```

### Validation Rules
- **No Duplicate Entries**: Users cannot enter the same contest twice
- **Time Validation**: Cannot enter expired contests
- **Winner Selection**: Only possible after contest ends
- **Legal Requirements**: All mandatory fields enforced

## Production Considerations

1. **Security**: Change the SECRET_KEY in production
2. **CORS**: Configure allowed origins properly
3. **Database**: Use PostgreSQL for production
4. **SMS Integration**: Implement real OTP verification
5. **Rate Limiting**: Add rate limiting for phone verification
6. **Monitoring**: Add logging and monitoring
7. **Testing**: Add comprehensive test suite
