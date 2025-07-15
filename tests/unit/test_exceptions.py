"""
TDD 테스트: 예외 처리 테스트
"""
import pytest
from src.exceptions import (
    InvestorTrendsException,
    APIException,
    DatabaseException,
    CacheException,
    ValidationException,
    ConfigurationException,
    DataNotFoundException,
    RateLimitException,
    AuthenticationException
)


class TestInvestorTrendsException:
    """기본 예외 클래스 테스트"""
    
    def test_base_exception_creation(self):
        """기본 예외 생성 테스트"""
        exception = InvestorTrendsException("Test error")
        
        assert str(exception) == "Test error"
        assert exception.message == "Test error"
        assert exception.error_code is None
        assert exception.details is None
    
    def test_base_exception_with_details(self):
        """상세 정보가 있는 예외 테스트"""
        details = {"field": "value", "status": "error"}
        exception = InvestorTrendsException(
            message="Test error",
            error_code="TEST_001",
            details=details
        )
        
        assert str(exception) == "Test error"
        assert exception.message == "Test error"
        assert exception.error_code == "TEST_001"
        assert exception.details == details
    
    def test_base_exception_to_dict(self):
        """예외를 딕셔너리로 변환 테스트"""
        details = {"field": "value"}
        exception = InvestorTrendsException(
            message="Test error",
            error_code="TEST_001",
            details=details
        )
        
        expected_dict = {
            "message": "Test error",
            "error_code": "TEST_001",
            "details": details,
            "exception_type": "InvestorTrendsException"
        }
        
        assert exception.to_dict() == expected_dict


class TestAPIException:
    """API 예외 클래스 테스트"""
    
    def test_api_exception_creation(self):
        """API 예외 생성 테스트"""
        exception = APIException("API request failed")
        
        assert str(exception) == "API request failed"
        assert exception.message == "API request failed"
        assert exception.status_code is None
        assert exception.endpoint is None
    
    def test_api_exception_with_status_code(self):
        """상태 코드가 있는 API 예외 테스트"""
        exception = APIException(
            message="API request failed",
            status_code=500,
            endpoint="/api/investor-trading"
        )
        
        assert exception.status_code == 500
        assert exception.endpoint == "/api/investor-trading"
    
    def test_api_exception_is_client_error(self):
        """클라이언트 오류 확인 테스트"""
        client_error = APIException("Bad request", status_code=400)
        server_error = APIException("Internal error", status_code=500)
        
        assert client_error.is_client_error() == True
        assert server_error.is_client_error() == False
    
    def test_api_exception_is_server_error(self):
        """서버 오류 확인 테스트"""
        client_error = APIException("Bad request", status_code=400)
        server_error = APIException("Internal error", status_code=500)
        
        assert client_error.is_server_error() == False
        assert server_error.is_server_error() == True
    
    def test_api_exception_to_dict(self):
        """API 예외를 딕셔너리로 변환 테스트"""
        exception = APIException(
            message="API request failed",
            status_code=500,
            endpoint="/api/investor-trading"
        )
        
        result = exception.to_dict()
        
        assert result["message"] == "API request failed"
        assert result["status_code"] == 500
        assert result["endpoint"] == "/api/investor-trading"
        assert result["exception_type"] == "APIException"


class TestDatabaseException:
    """데이터베이스 예외 클래스 테스트"""
    
    def test_database_exception_creation(self):
        """데이터베이스 예외 생성 테스트"""
        exception = DatabaseException("Database connection failed")
        
        assert str(exception) == "Database connection failed"
        assert exception.query is None
        assert exception.table is None
    
    def test_database_exception_with_query(self):
        """쿼리 정보가 있는 데이터베이스 예외 테스트"""
        exception = DatabaseException(
            message="Query failed",
            query="SELECT * FROM investor_trading",
            table="investor_trading"
        )
        
        assert exception.query == "SELECT * FROM investor_trading"
        assert exception.table == "investor_trading"
    
    def test_database_exception_to_dict(self):
        """데이터베이스 예외를 딕셔너리로 변환 테스트"""
        exception = DatabaseException(
            message="Query failed",
            query="SELECT * FROM investor_trading",
            table="investor_trading"
        )
        
        result = exception.to_dict()
        
        assert result["message"] == "Query failed"
        assert result["query"] == "SELECT * FROM investor_trading"
        assert result["table"] == "investor_trading"
        assert result["exception_type"] == "DatabaseException"


class TestCacheException:
    """캐시 예외 클래스 테스트"""
    
    def test_cache_exception_creation(self):
        """캐시 예외 생성 테스트"""
        exception = CacheException("Cache connection failed")
        
        assert str(exception) == "Cache connection failed"
        assert exception.cache_key is None
        assert exception.operation is None
    
    def test_cache_exception_with_details(self):
        """상세 정보가 있는 캐시 예외 테스트"""
        exception = CacheException(
            message="Cache operation failed",
            cache_key="investor:trading:005930",
            operation="GET"
        )
        
        assert exception.cache_key == "investor:trading:005930"
        assert exception.operation == "GET"
    
    def test_cache_exception_to_dict(self):
        """캐시 예외를 딕셔너리로 변환 테스트"""
        exception = CacheException(
            message="Cache operation failed",
            cache_key="investor:trading:005930",
            operation="GET"
        )
        
        result = exception.to_dict()
        
        assert result["message"] == "Cache operation failed"
        assert result["cache_key"] == "investor:trading:005930"
        assert result["operation"] == "GET"
        assert result["exception_type"] == "CacheException"


class TestValidationException:
    """유효성 검증 예외 클래스 테스트"""
    
    def test_validation_exception_creation(self):
        """유효성 검증 예외 생성 테스트"""
        exception = ValidationException("Invalid parameter")
        
        assert str(exception) == "Invalid parameter"
        assert exception.field is None
        assert exception.value is None
        assert exception.validation_errors == []
    
    def test_validation_exception_with_field(self):
        """필드 정보가 있는 유효성 검증 예외 테스트"""
        exception = ValidationException(
            message="Invalid investor type",
            field="investor_type",
            value="INVALID"
        )
        
        assert exception.field == "investor_type"
        assert exception.value == "INVALID"
    
    def test_validation_exception_with_errors(self):
        """여러 오류가 있는 유효성 검증 예외 테스트"""
        validation_errors = [
            {"field": "investor_type", "error": "Invalid value"},
            {"field": "period", "error": "Invalid period"}
        ]
        
        exception = ValidationException(
            message="Multiple validation errors",
            validation_errors=validation_errors
        )
        
        assert exception.validation_errors == validation_errors
        assert exception.has_multiple_errors() == True
    
    def test_validation_exception_add_error(self):
        """오류 추가 테스트"""
        exception = ValidationException("Validation failed")
        
        exception.add_error("field1", "error1")
        exception.add_error("field2", "error2")
        
        assert len(exception.validation_errors) == 2
        assert exception.validation_errors[0] == {"field": "field1", "error": "error1"}
        assert exception.validation_errors[1] == {"field": "field2", "error": "error2"}
    
    def test_validation_exception_to_dict(self):
        """유효성 검증 예외를 딕셔너리로 변환 테스트"""
        exception = ValidationException(
            message="Invalid investor type",
            field="investor_type",
            value="INVALID"
        )
        
        result = exception.to_dict()
        
        assert result["message"] == "Invalid investor type"
        assert result["field"] == "investor_type"
        assert result["value"] == "INVALID"
        assert result["validation_errors"] == []
        assert result["exception_type"] == "ValidationException"


class TestConfigurationException:
    """설정 예외 클래스 테스트"""
    
    def test_configuration_exception_creation(self):
        """설정 예외 생성 테스트"""
        exception = ConfigurationException("Missing API key")
        
        assert str(exception) == "Missing API key"
        assert exception.config_key is None
        assert exception.config_section is None
    
    def test_configuration_exception_with_details(self):
        """상세 정보가 있는 설정 예외 테스트"""
        exception = ConfigurationException(
            message="Missing API key",
            config_key="KOREA_INVESTMENT_APP_KEY",
            config_section="api"
        )
        
        assert exception.config_key == "KOREA_INVESTMENT_APP_KEY"
        assert exception.config_section == "api"
    
    def test_configuration_exception_to_dict(self):
        """설정 예외를 딕셔너리로 변환 테스트"""
        exception = ConfigurationException(
            message="Missing API key",
            config_key="KOREA_INVESTMENT_APP_KEY",
            config_section="api"
        )
        
        result = exception.to_dict()
        
        assert result["message"] == "Missing API key"
        assert result["config_key"] == "KOREA_INVESTMENT_APP_KEY"
        assert result["config_section"] == "api"
        assert result["exception_type"] == "ConfigurationException"


class TestDataNotFoundException:
    """데이터 미발견 예외 클래스 테스트"""
    
    def test_data_not_found_exception_creation(self):
        """데이터 미발견 예외 생성 테스트"""
        exception = DataNotFoundException("Stock not found")
        
        assert str(exception) == "Stock not found"
        assert exception.resource_type is None
        assert exception.resource_id is None
    
    def test_data_not_found_exception_with_resource(self):
        """리소스 정보가 있는 데이터 미발견 예외 테스트"""
        exception = DataNotFoundException(
            message="Stock not found",
            resource_type="stock",
            resource_id="005930"
        )
        
        assert exception.resource_type == "stock"
        assert exception.resource_id == "005930"
    
    def test_data_not_found_exception_to_dict(self):
        """데이터 미발견 예외를 딕셔너리로 변환 테스트"""
        exception = DataNotFoundException(
            message="Stock not found",
            resource_type="stock",
            resource_id="005930"
        )
        
        result = exception.to_dict()
        
        assert result["message"] == "Stock not found"
        assert result["resource_type"] == "stock"
        assert result["resource_id"] == "005930"
        assert result["exception_type"] == "DataNotFoundException"


class TestRateLimitException:
    """속도 제한 예외 클래스 테스트"""
    
    def test_rate_limit_exception_creation(self):
        """속도 제한 예외 생성 테스트"""
        exception = RateLimitException("Rate limit exceeded")
        
        assert str(exception) == "Rate limit exceeded"
        assert exception.limit is None
        assert exception.reset_time is None
    
    def test_rate_limit_exception_with_details(self):
        """상세 정보가 있는 속도 제한 예외 테스트"""
        exception = RateLimitException(
            message="Rate limit exceeded",
            limit=100,
            reset_time=60
        )
        
        assert exception.limit == 100
        assert exception.reset_time == 60
    
    def test_rate_limit_exception_to_dict(self):
        """속도 제한 예외를 딕셔너리로 변환 테스트"""
        exception = RateLimitException(
            message="Rate limit exceeded",
            limit=100,
            reset_time=60
        )
        
        result = exception.to_dict()
        
        assert result["message"] == "Rate limit exceeded"
        assert result["limit"] == 100
        assert result["reset_time"] == 60
        assert result["exception_type"] == "RateLimitException"


class TestAuthenticationException:
    """인증 예외 클래스 테스트"""
    
    def test_authentication_exception_creation(self):
        """인증 예외 생성 테스트"""
        exception = AuthenticationException("Authentication failed")
        
        assert str(exception) == "Authentication failed"
        assert exception.auth_method is None
        assert exception.user_id is None
    
    def test_authentication_exception_with_details(self):
        """상세 정보가 있는 인증 예외 테스트"""
        exception = AuthenticationException(
            message="Authentication failed",
            auth_method="API_KEY",
            user_id="user123"
        )
        
        assert exception.auth_method == "API_KEY"
        assert exception.user_id == "user123"
    
    def test_authentication_exception_to_dict(self):
        """인증 예외를 딕셔너리로 변환 테스트"""
        exception = AuthenticationException(
            message="Authentication failed",
            auth_method="API_KEY",
            user_id="user123"
        )
        
        result = exception.to_dict()
        
        assert result["message"] == "Authentication failed"
        assert result["auth_method"] == "API_KEY"
        assert result["user_id"] == "user123"
        assert result["exception_type"] == "AuthenticationException"


class TestExceptionInheritance:
    """예외 상속 구조 테스트"""
    
    def test_all_exceptions_inherit_from_base(self):
        """모든 예외가 기본 예외에서 상속되는지 테스트"""
        exceptions = [
            APIException("test"),
            DatabaseException("test"),
            CacheException("test"),
            ValidationException("test"),
            ConfigurationException("test"),
            DataNotFoundException("test"),
            RateLimitException("test"),
            AuthenticationException("test")
        ]
        
        for exception in exceptions:
            assert isinstance(exception, InvestorTrendsException)
            assert isinstance(exception, Exception)
    
    def test_exception_can_be_caught_as_base_type(self):
        """예외를 기본 타입으로 잡을 수 있는지 테스트"""
        with pytest.raises(InvestorTrendsException):
            raise APIException("API error")
        
        with pytest.raises(InvestorTrendsException):
            raise DatabaseException("Database error")
        
        with pytest.raises(InvestorTrendsException):
            raise ValidationException("Validation error")