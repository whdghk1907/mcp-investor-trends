"""
투자자 동향 MCP 서버 예외 처리 클래스
"""
from typing import Optional, Dict, Any, List


class InvestorTrendsException(Exception):
    """투자자 동향 서버 기본 예외 클래스"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        return {
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "exception_type": self.__class__.__name__
        }


class APIException(InvestorTrendsException):
    """API 관련 예외"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.status_code = status_code
        self.endpoint = endpoint
    
    def is_client_error(self) -> bool:
        """클라이언트 오류인지 확인 (4xx)"""
        return self.status_code is not None and 400 <= self.status_code < 500
    
    def is_server_error(self) -> bool:
        """서버 오류인지 확인 (5xx)"""
        return self.status_code is not None and 500 <= self.status_code < 600
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        result = super().to_dict()
        result.update({
            "status_code": self.status_code,
            "endpoint": self.endpoint
        })
        return result


class DatabaseException(InvestorTrendsException):
    """데이터베이스 관련 예외"""
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        table: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.query = query
        self.table = table
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        result = super().to_dict()
        result.update({
            "query": self.query,
            "table": self.table
        })
        return result


class CacheException(InvestorTrendsException):
    """캐시 관련 예외"""
    
    def __init__(
        self,
        message: str,
        cache_key: Optional[str] = None,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.cache_key = cache_key
        self.operation = operation
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        result = super().to_dict()
        result.update({
            "cache_key": self.cache_key,
            "operation": self.operation
        })
        return result


class ValidationException(InvestorTrendsException):
    """유효성 검증 예외"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        validation_errors: Optional[List[Dict[str, str]]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.field = field
        self.value = value
        self.validation_errors = validation_errors or []
    
    def add_error(self, field: str, error: str):
        """유효성 검증 오류 추가"""
        self.validation_errors.append({
            "field": field,
            "error": error
        })
    
    def has_multiple_errors(self) -> bool:
        """여러 오류가 있는지 확인"""
        return len(self.validation_errors) > 1
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        result = super().to_dict()
        result.update({
            "field": self.field,
            "value": self.value,
            "validation_errors": self.validation_errors
        })
        return result


class ConfigurationException(InvestorTrendsException):
    """설정 관련 예외"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_section: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.config_key = config_key
        self.config_section = config_section
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        result = super().to_dict()
        result.update({
            "config_key": self.config_key,
            "config_section": self.config_section
        })
        return result


class DataNotFoundException(InvestorTrendsException):
    """데이터 미발견 예외"""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.resource_type = resource_type
        self.resource_id = resource_id
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        result = super().to_dict()
        result.update({
            "resource_type": self.resource_type,
            "resource_id": self.resource_id
        })
        return result


class RateLimitException(InvestorTrendsException):
    """속도 제한 예외"""
    
    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        reset_time: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.limit = limit
        self.reset_time = reset_time
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        result = super().to_dict()
        result.update({
            "limit": self.limit,
            "reset_time": self.reset_time
        })
        return result


class AuthenticationException(InvestorTrendsException):
    """인증 예외"""
    
    def __init__(
        self,
        message: str,
        auth_method: Optional[str] = None,
        user_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.auth_method = auth_method
        self.user_id = user_id
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        result = super().to_dict()
        result.update({
            "auth_method": self.auth_method,
            "user_id": self.user_id
        })
        return result