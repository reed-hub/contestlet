"""
Pytest configuration and fixtures for Contestlet API testing
"""
import pytest
import asyncio
import os
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app modules
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("USE_MOCK_SMS", "true")
os.environ.setdefault("RATE_LIMIT_REQUESTS", "100")
os.environ.setdefault("RATE_LIMIT_WINDOW", "3600")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "1440")
os.environ.setdefault("JWT_REFRESH_EXPIRE_MINUTES", "10080")
os.environ.setdefault("ADMIN_PHONES", "+18187958204")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "test-account-sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-auth-token")
os.environ.setdefault("TWILIO_VERIFY_SERVICE_SID", "test-verify-service-sid")
os.environ.setdefault("TWILIO_PHONE_NUMBER", "+15551234567")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    # Import here to avoid circular imports
    from app.database.database import Base
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator:
    """Create a test client with database dependency override"""
    # Import here to avoid circular imports
    from app.main import app
    from app.database.database import get_db
    from fastapi.testclient import TestClient
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Get test settings"""
    # Import here to avoid circular imports
    from app.core.config import get_settings
    return get_settings()


@pytest.fixture
def admin_user_data() -> Dict[str, Any]:
    """Admin user test data"""
    return {
        "phone": "+18187958204",
        "role": "admin",
        "is_verified": True
    }


@pytest.fixture
def sponsor_user_data() -> Dict[str, Any]:
    """Sponsor user test data"""
    return {
        "phone": "+15551234567",
        "role": "sponsor",
        "is_verified": True
    }


@pytest.fixture
def regular_user_data() -> Dict[str, Any]:
    """Regular user test data"""
    return {
        "phone": "+15559876543",
        "role": "user",
        "is_verified": True
    }


@pytest.fixture
def admin_token(admin_user_data: Dict[str, Any]) -> str:
    """Generate admin JWT token for testing"""
    # Import here to avoid circular imports
    from app.core.auth import jwt_manager
    
    return jwt_manager.create_access_token(
        user_id=1,
        phone=admin_user_data["phone"],
        role=admin_user_data["role"]
    )


@pytest.fixture
def sponsor_token(sponsor_user_data: Dict[str, Any]) -> str:
    """Generate sponsor JWT token for testing"""
    # Import here to avoid circular imports
    from app.core.auth import jwt_manager
    
    return jwt_manager.create_access_token(
        user_id=2,
        phone=sponsor_user_data["phone"],
        role=sponsor_user_data["role"]
    )


@pytest.fixture
def user_token(regular_user_data: Dict[str, Any]) -> str:
    """Generate regular user JWT token for testing"""
    # Import here to avoid circular imports
    from app.core.auth import jwt_manager
    
    return jwt_manager.create_access_token(
        user_id=3,
        phone=regular_user_data["phone"],
        role=regular_user_data["role"]
    )


@pytest.fixture
def auth_headers(admin_token: str) -> Dict[str, str]:
    """Authorization headers for admin user"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sponsor_headers(sponsor_token: str) -> Dict[str, str]:
    """Authorization headers for sponsor user"""
    return {"Authorization": f"Bearer {sponsor_token}"}


@pytest.fixture
def user_headers(user_token: str) -> Dict[str, str]:
    """Authorization headers for regular user"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def sample_contest_data() -> Dict[str, Any]:
    """Sample contest data for testing"""
    from datetime import datetime, timedelta
    
    return {
        "name": "Test Contest",
        "description": "A test contest for testing purposes",
        "location": "Test City, TS 12345",
        "start_time": datetime.utcnow() + timedelta(hours=1),
        "end_time": datetime.utcnow() + timedelta(days=7),
        "prize_description": "Test prize worth $100",
        "contest_type": "general",
        "entry_method": "sms",
        "winner_selection_method": "random",
        "minimum_age": 18,
        "max_entries_per_person": 1,
        "total_entry_limit": 100
    }


@pytest.fixture
def sample_entry_data() -> Dict[str, Any]:
    """Sample entry data for testing"""
    return {
        "contest_id": 1,
        "user_id": 3,
        "is_valid": True
    }


# Test utilities
class TestUtils:
    """Utility functions for testing"""
    
    @staticmethod
    def assert_response_structure(response_data: Dict[str, Any], expected_fields: list):
        """Assert response has expected structure"""
        for field in expected_fields:
            assert field in response_data, f"Missing field: {field}"
    
    @staticmethod
    def assert_error_response(response, expected_status: int, expected_error_code: str = None):
        """Assert error response structure"""
        assert response.status_code == expected_status
        if expected_error_code:
            assert "error_code" in response.json()
            assert response.json()["error_code"] == expected_error_code
    
    @staticmethod
    def create_test_user(db: Session, user_data: Dict[str, Any]) -> int:
        """Create a test user and return user ID"""
        from app.models.user import User
        
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    
    @staticmethod
    def create_test_contest(db: Session, contest_data: Dict[str, Any], creator_id: int) -> int:
        """Create a test contest and return contest ID"""
        from app.models.contest import Contest
        
        contest = Contest(**contest_data, created_by_user_id=creator_id)
        db.add(contest)
        db.commit()
        db.refresh(contest)
        return contest.id


@pytest.fixture
def test_utils() -> TestUtils:
    """Test utilities fixture"""
    return TestUtils()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        if "test_unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        elif "test_security" in item.nodeid:
            item.add_marker(pytest.mark.security)
        elif "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)

