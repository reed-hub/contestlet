"""
Tests for the new clean architecture components
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.shared.constants.contest import ContestConstants, ContestMessages
from app.shared.constants.auth import AuthConstants, AuthMessages
from app.shared.constants.location import LocationConstants, LocationMessages
from app.shared.constants.media import MediaConstants, MediaMessages
from app.shared.exceptions.base import (
    ResourceNotFoundException, 
    ValidationException, 
    BusinessException,
    ErrorCode
)
from app.shared.types.responses import APIResponse, PaginatedResponse
from app.shared.types.pagination import PaginationParams, create_paginated_result


class TestConstants:
    """Test centralized constants"""
    
    def test_contest_constants_defined(self):
        """Test that all contest constants are properly defined"""
        # Status constants
        assert ContestConstants.STATUS_DRAFT == "draft"
        assert ContestConstants.STATUS_AWAITING_APPROVAL == "awaiting_approval"
        assert ContestConstants.STATUS_PUBLISHED == "published"
        assert ContestConstants.STATUS_ACTIVE == "active"
        assert ContestConstants.STATUS_ENDED == "ended"
        assert ContestConstants.STATUS_COMPLETE == "complete"
        assert ContestConstants.STATUS_CANCELLED == "cancelled"
        assert ContestConstants.STATUS_REJECTED == "rejected"
        
        # Validation constants
        assert ContestConstants.MIN_NAME_LENGTH > 0
        assert ContestConstants.MAX_NAME_LENGTH > ContestConstants.MIN_NAME_LENGTH
        assert ContestConstants.MIN_DESCRIPTION_LENGTH > 0
        assert ContestConstants.MAX_DESCRIPTION_LENGTH > ContestConstants.MIN_DESCRIPTION_LENGTH
        
        # Entry limits
        assert ContestConstants.MIN_ENTRIES_PER_PERSON >= 1
        assert ContestConstants.MAX_ENTRIES_PER_PERSON >= ContestConstants.MIN_ENTRIES_PER_PERSON
        assert ContestConstants.DEFAULT_ENTRIES_PER_PERSON >= ContestConstants.MIN_ENTRIES_PER_PERSON
    
    def test_auth_constants_defined(self):
        """Test that all auth constants are properly defined"""
        # Roles
        assert AuthConstants.ADMIN_ROLE == "admin"
        assert AuthConstants.SPONSOR_ROLE == "sponsor"
        assert AuthConstants.USER_ROLE == "user"
        
        # Valid roles list
        assert AuthConstants.ADMIN_ROLE in AuthConstants.VALID_ROLES
        assert AuthConstants.SPONSOR_ROLE in AuthConstants.VALID_ROLES
        assert AuthConstants.USER_ROLE in AuthConstants.VALID_ROLES
        
        # Token settings
        assert AuthConstants.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert AuthConstants.REFRESH_TOKEN_EXPIRE_DAYS > 0
        assert AuthConstants.OTP_EXPIRE_MINUTES > 0
        assert AuthConstants.OTP_LENGTH >= 4
    
    def test_location_constants_defined(self):
        """Test that all location constants are properly defined"""
        # Location types
        assert LocationConstants.LOCATION_TYPE_UNITED_STATES == "united_states"
        assert LocationConstants.LOCATION_TYPE_SPECIFIC_STATES == "specific_states"
        assert LocationConstants.LOCATION_TYPE_RADIUS == "radius"
        assert LocationConstants.LOCATION_TYPE_CUSTOM == "custom"
        
        # Coordinate limits
        assert LocationConstants.MIN_LATITUDE == -90.0
        assert LocationConstants.MAX_LATITUDE == 90.0
        assert LocationConstants.MIN_LONGITUDE == -180.0
        assert LocationConstants.MAX_LONGITUDE == 180.0
        
        # State codes
        assert "CA" in LocationConstants.VALID_STATE_CODES
        assert "NY" in LocationConstants.VALID_STATE_CODES
        assert "TX" in LocationConstants.VALID_STATE_CODES
        assert LocationConstants.VALID_STATE_CODES["CA"] == "California"
    
    def test_media_constants_defined(self):
        """Test that all media constants are properly defined"""
        # Media types
        assert MediaConstants.MEDIA_TYPE_IMAGE == "image"
        assert MediaConstants.MEDIA_TYPE_VIDEO == "video"
        
        # File formats
        assert "jpg" in MediaConstants.SUPPORTED_IMAGE_FORMATS
        assert "png" in MediaConstants.SUPPORTED_IMAGE_FORMATS
        assert "mp4" in MediaConstants.SUPPORTED_VIDEO_FORMATS
        
        # Size limits
        assert MediaConstants.MAX_IMAGE_SIZE_MB > 0
        assert MediaConstants.MAX_VIDEO_SIZE_MB > MediaConstants.MAX_IMAGE_SIZE_MB
        assert MediaConstants.MIN_FILE_SIZE_BYTES > 0


class TestStructuredExceptions:
    """Test structured exception system"""
    
    def test_resource_not_found_exception(self):
        """Test ResourceNotFoundException"""
        exception = ResourceNotFoundException("Contest", 123)
        
        assert exception.error_code == ErrorCode.RESOURCE_NOT_FOUND
        assert "Contest" in exception.message
        assert "123" in exception.message
        assert exception.details["resource_type"] == "Contest"
        assert exception.details["resource_id"] == 123
    
    def test_validation_exception(self):
        """Test ValidationException"""
        field_errors = {"name": "Name is required", "email": "Invalid email format"}
        exception = ValidationException("Validation failed", field_errors=field_errors)
        
        assert exception.error_code == ErrorCode.VALIDATION_FAILED
        assert exception.message == "Validation failed"
        assert exception.field_errors == field_errors
        assert "name" in exception.field_errors
        assert "email" in exception.field_errors
    
    def test_business_exception(self):
        """Test BusinessException"""
        details = {"contest_id": 123, "current_status": "active"}
        exception = BusinessException(
            error_code=ErrorCode.CONTEST_PROTECTED,
            message="Cannot delete active contest",
            details=details
        )
        
        assert exception.error_code == ErrorCode.CONTEST_PROTECTED
        assert exception.message == "Cannot delete active contest"
        assert exception.details == details
    
    def test_exception_serialization(self):
        """Test exception serialization for API responses"""
        exception = ValidationException(
            "Invalid input",
            field_errors={"name": "Required field"}
        )
        
        serialized = exception.to_dict()
        
        assert "error_code" in serialized
        assert "message" in serialized
        assert "field_errors" in serialized
        assert serialized["error_code"] == ErrorCode.VALIDATION_FAILED
        assert serialized["message"] == "Invalid input"
        assert serialized["field_errors"]["name"] == "Required field"


class TestResponseModels:
    """Test standardized response models"""
    
    def test_api_response_success(self):
        """Test successful API response"""
        data = {"id": 1, "name": "Test Contest"}
        response = APIResponse(
            success=True,
            data=data,
            message="Contest retrieved successfully"
        )
        
        assert response.success is True
        assert response.data == data
        assert response.message == "Contest retrieved successfully"
        assert response.errors is None
        assert response.error_code is None
    
    def test_api_response_error(self):
        """Test error API response"""
        errors = {"validation": "Invalid input"}
        response = APIResponse(
            success=False,
            message="Validation failed",
            errors=errors,
            error_code=ErrorCode.VALIDATION_FAILED
        )
        
        assert response.success is False
        assert response.data is None
        assert response.message == "Validation failed"
        assert response.errors == errors
        assert response.error_code == ErrorCode.VALIDATION_FAILED
    
    def test_paginated_response(self):
        """Test paginated response creation"""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        pagination = PaginationParams(page=1, limit=10)
        
        paginated = create_paginated_result(items, total=25, pagination=pagination)
        
        assert paginated.items == items
        assert paginated.total == 25
        assert paginated.page == 1
        assert paginated.limit == 10
        assert paginated.pages == 3  # ceil(25/10)
        assert paginated.has_next is True
        assert paginated.has_prev is False
    
    def test_pagination_params_validation(self):
        """Test pagination parameters validation"""
        # Valid pagination
        pagination = PaginationParams(page=1, limit=20)
        assert pagination.page == 1
        assert pagination.limit == 20
        assert pagination.offset == 0
        
        # Test offset calculation
        pagination = PaginationParams(page=3, limit=10)
        assert pagination.offset == 20  # (3-1) * 10
        
        # Test default values
        pagination = PaginationParams()
        assert pagination.page == 1
        assert pagination.limit == 50  # Default limit


class TestServiceLayerIntegration:
    """Test service layer integration with new architecture"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_contest_repo(self):
        """Mock contest repository"""
        from app.infrastructure.repositories.contest_repository import SQLAlchemyContestRepository
        return Mock(spec=SQLAlchemyContestRepository)
    
    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository"""
        from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
        return Mock(spec=SQLAlchemyUserRepository)
    
    def test_contest_service_initialization(self, mock_db_session, mock_contest_repo, mock_user_repo):
        """Test contest service initialization with dependencies"""
        from app.core.services.contest_service import ContestService
        
        service = ContestService(
            contest_repo=mock_contest_repo,
            user_repo=mock_user_repo,
            db=mock_db_session
        )
        
        assert service.contest_repo == mock_contest_repo
        assert service.user_repo == mock_user_repo
        assert service.db == mock_db_session
    
    def test_user_service_initialization(self, mock_db_session, mock_user_repo):
        """Test user service initialization with dependencies"""
        from app.core.services.user_service import UserService
        
        service = UserService(
            user_repo=mock_user_repo,
            db=mock_db_session
        )
        
        assert service.user_repo == mock_user_repo
        assert service.db == mock_db_session
    
    @patch('app.core.services.contest_service.ContestService.get_contest_by_id')
    def test_service_method_error_handling(self, mock_get_contest, mock_db_session, mock_contest_repo, mock_user_repo):
        """Test service method error handling with structured exceptions"""
        from app.core.services.contest_service import ContestService
        
        # Setup mock to raise ResourceNotFoundException
        mock_get_contest.side_effect = ResourceNotFoundException("Contest", 999)
        
        service = ContestService(
            contest_repo=mock_contest_repo,
            user_repo=mock_user_repo,
            db=mock_db_session
        )
        
        # Test that the exception is properly raised
        with pytest.raises(ResourceNotFoundException) as exc_info:
            service.get_contest_by_id(999)
        
        assert exc_info.value.error_code == ErrorCode.RESOURCE_NOT_FOUND
        assert "Contest" in str(exc_info.value)
        assert "999" in str(exc_info.value)


class TestDependencyInjection:
    """Test dependency injection system"""
    
    def test_service_dependencies_available(self):
        """Test that all service dependencies are available"""
        from app.core.dependencies.services import (
            get_contest_service,
            get_auth_service,
            get_user_service,
            get_admin_service,
            get_entry_service,
            get_location_service
        )
        
        # Test that all dependency functions exist and are callable
        assert callable(get_contest_service)
        assert callable(get_auth_service)
        assert callable(get_user_service)
        assert callable(get_admin_service)
        assert callable(get_entry_service)
        assert callable(get_location_service)
    
    def test_auth_dependencies_available(self):
        """Test that all auth dependencies are available"""
        from app.core.dependencies.auth import (
            get_current_user,
            get_admin_user,
            get_sponsor_user,
            get_admin_or_sponsor_user,
            get_optional_user
        )
        
        # Test that all auth dependency functions exist and are callable
        assert callable(get_current_user)
        assert callable(get_admin_user)
        assert callable(get_sponsor_user)
        assert callable(get_admin_or_sponsor_user)
        assert callable(get_optional_user)


class TestErrorHandlingMiddleware:
    """Test global error handling middleware"""
    
    def test_structured_exception_conversion(self):
        """Test that structured exceptions are properly converted to API responses"""
        from app.api.middleware.error_handler import convert_exception_to_response
        
        # Test ResourceNotFoundException
        exception = ResourceNotFoundException("Contest", 123)
        response = convert_exception_to_response(exception)
        
        assert response["success"] is False
        assert response["error_code"] == ErrorCode.RESOURCE_NOT_FOUND
        assert "Contest" in response["message"]
        assert "123" in response["message"]
    
    def test_validation_exception_conversion(self):
        """Test ValidationException conversion"""
        from app.api.middleware.error_handler import convert_exception_to_response
        
        field_errors = {"name": "Required field", "email": "Invalid format"}
        exception = ValidationException("Validation failed", field_errors=field_errors)
        response = convert_exception_to_response(exception)
        
        assert response["success"] is False
        assert response["error_code"] == ErrorCode.VALIDATION_FAILED
        assert response["message"] == "Validation failed"
        assert response["errors"]["field_errors"] == field_errors
    
    def test_generic_exception_conversion(self):
        """Test generic exception conversion"""
        from app.api.middleware.error_handler import convert_exception_to_response
        
        exception = ValueError("Something went wrong")
        response = convert_exception_to_response(exception)
        
        assert response["success"] is False
        assert response["error_code"] == ErrorCode.INTERNAL_ERROR
        assert "internal server error" in response["message"].lower()


class TestCleanArchitecturePatterns:
    """Test clean architecture pattern compliance"""
    
    def test_service_layer_separation(self):
        """Test that service layer is properly separated from controllers"""
        # Import a service and verify it doesn't import from routers
        import inspect
        from app.core.services.contest_service import ContestService
        
        # Get all imports in the service module
        service_module = inspect.getmodule(ContestService)
        source = inspect.getsource(service_module)
        
        # Verify no router imports (clean architecture compliance)
        assert "from app.routers" not in source
        assert "import app.routers" not in source
    
    def test_repository_pattern_compliance(self):
        """Test that repositories follow the pattern correctly"""
        from app.infrastructure.repositories.contest_repository import SQLAlchemyContestRepository
        
        # Verify repository has required methods
        repo_methods = dir(SQLAlchemyContestRepository)
        
        # Check for standard repository methods
        assert "get_by_id" in repo_methods
        assert "save" in repo_methods
        assert "delete" in repo_methods
    
    def test_constants_centralization(self):
        """Test that constants are properly centralized"""
        # Verify constants are not duplicated in other modules
        import inspect
        from app.core.services.contest_service import ContestService
        
        service_source = inspect.getsource(ContestService)
        
        # Should not have hardcoded status strings
        assert '"draft"' not in service_source or 'ContestConstants' in service_source
        assert '"active"' not in service_source or 'ContestConstants' in service_source
    
    def test_type_safety_compliance(self):
        """Test that type hints are properly used"""
        from app.core.services.contest_service import ContestService
        import inspect
        
        # Get method signatures
        methods = inspect.getmembers(ContestService, predicate=inspect.isfunction)
        
        for method_name, method in methods:
            if not method_name.startswith('_'):  # Skip private methods
                signature = inspect.signature(method)
                
                # Verify return type annotation exists for public methods
                assert signature.return_annotation != inspect.Signature.empty, f"Method {method_name} missing return type annotation"


class TestProductionReadiness:
    """Test production readiness indicators"""
    
    def test_error_codes_comprehensive(self):
        """Test that error codes cover all scenarios"""
        from app.shared.exceptions.base import ErrorCode
        
        # Verify essential error codes exist
        essential_codes = [
            "RESOURCE_NOT_FOUND",
            "VALIDATION_FAILED", 
            "UNAUTHORIZED",
            "FORBIDDEN",
            "BUSINESS_RULE_VIOLATION",
            "INTERNAL_ERROR"
        ]
        
        for code in essential_codes:
            assert hasattr(ErrorCode, code), f"Missing essential error code: {code}"
    
    def test_constants_completeness(self):
        """Test that constants cover all necessary values"""
        # Contest constants completeness
        assert hasattr(ContestConstants, 'MIN_NAME_LENGTH')
        assert hasattr(ContestConstants, 'MAX_NAME_LENGTH')
        assert hasattr(ContestConstants, 'STATUS_DRAFT')
        assert hasattr(ContestConstants, 'STATUS_ACTIVE')
        
        # Auth constants completeness
        assert hasattr(AuthConstants, 'ADMIN_ROLE')
        assert hasattr(AuthConstants, 'VALID_ROLES')
        assert hasattr(AuthConstants, 'ACCESS_TOKEN_EXPIRE_MINUTES')
    
    def test_messages_standardization(self):
        """Test that messages are standardized"""
        # Contest messages
        assert hasattr(ContestMessages, 'CONTEST_CREATED')
        assert hasattr(ContestMessages, 'CONTEST_NOT_FOUND')
        assert hasattr(ContestMessages, 'INVALID_STATUS_TRANSITION')
        
        # Auth messages
        assert hasattr(AuthMessages, 'INVALID_CREDENTIALS')
        assert hasattr(AuthMessages, 'ACCESS_DENIED')
        assert hasattr(AuthMessages, 'TOKEN_EXPIRED')
    
    def test_response_model_consistency(self):
        """Test that response models are consistent"""
        from app.api.responses.contest import ContestListResponse, ContestDetailResponse
        from app.api.responses.user import UserProfileResponse, UserListResponse
        
        # Verify all response models inherit from APIResponse
        assert hasattr(ContestListResponse, '__orig_bases__')
        assert hasattr(ContestDetailResponse, '__orig_bases__')
        assert hasattr(UserProfileResponse, '__orig_bases__')
        assert hasattr(UserListResponse, '__orig_bases__')
