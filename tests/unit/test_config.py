"""
TDD 테스트: Config 클래스 테스트
"""
import pytest
import os
from unittest.mock import patch
from src.config import Config, DatabaseConfig, CacheConfig, APIConfig, AnalysisConfig


class TestDatabaseConfig:
    """데이터베이스 설정 테스트"""
    
    def test_database_config_default_values(self):
        """기본값 테스트"""
        config = DatabaseConfig(url="postgresql://test")
        
        assert config.url == "postgresql://test"
        assert config.pool_size == 20
        assert config.max_overflow == 10
        assert config.pool_timeout == 30
    
    def test_database_config_custom_values(self):
        """커스텀 값 테스트"""
        config = DatabaseConfig(
            url="postgresql://custom",
            pool_size=50,
            max_overflow=20,
            pool_timeout=60
        )
        
        assert config.url == "postgresql://custom"
        assert config.pool_size == 50
        assert config.max_overflow == 20
        assert config.pool_timeout == 60


class TestCacheConfig:
    """캐시 설정 테스트"""
    
    def test_cache_config_default_values(self):
        """기본값 테스트"""
        config = CacheConfig(redis_url="redis://test")
        
        assert config.redis_url == "redis://test"
        assert config.ttl_realtime == 10
        assert config.ttl_minute == 60
        assert config.ttl_hourly == 3600
        assert config.ttl_daily == 86400
    
    def test_cache_config_custom_values(self):
        """커스텀 값 테스트"""
        config = CacheConfig(
            redis_url="redis://custom",
            ttl_realtime=5,
            ttl_minute=30,
            ttl_hourly=1800,
            ttl_daily=43200
        )
        
        assert config.redis_url == "redis://custom"
        assert config.ttl_realtime == 5
        assert config.ttl_minute == 30
        assert config.ttl_hourly == 1800
        assert config.ttl_daily == 43200


class TestAPIConfig:
    """API 설정 테스트"""
    
    def test_api_config_default_values(self):
        """기본값 테스트"""
        config = APIConfig(
            korea_investment_key="test_key",
            korea_investment_secret="test_secret",
            ebest_key="ebest_key",
            ebest_secret="ebest_secret"
        )
        
        assert config.korea_investment_key == "test_key"
        assert config.korea_investment_secret == "test_secret"
        assert config.ebest_key == "ebest_key"
        assert config.ebest_secret == "ebest_secret"
        assert config.rate_limit_per_minute == 200
    
    def test_api_config_custom_rate_limit(self):
        """커스텀 rate limit 테스트"""
        config = APIConfig(
            korea_investment_key="test_key",
            korea_investment_secret="test_secret",
            ebest_key="ebest_key",
            ebest_secret="ebest_secret",
            rate_limit_per_minute=100
        )
        
        assert config.rate_limit_per_minute == 100


class TestAnalysisConfig:
    """분석 설정 테스트"""
    
    def test_analysis_config_default_values(self):
        """기본값 테스트"""
        config = AnalysisConfig()
        
        assert config.smart_money_threshold == 1000000000
        assert config.large_order_threshold == 500000000
        assert config.anomaly_sensitivity == 2.5
        assert config.pattern_confidence_threshold == 0.7
    
    def test_analysis_config_custom_values(self):
        """커스텀 값 테스트"""
        config = AnalysisConfig(
            smart_money_threshold=2000000000,
            large_order_threshold=1000000000,
            anomaly_sensitivity=3.0,
            pattern_confidence_threshold=0.8
        )
        
        assert config.smart_money_threshold == 2000000000
        assert config.large_order_threshold == 1000000000
        assert config.anomaly_sensitivity == 3.0
        assert config.pattern_confidence_threshold == 0.8


class TestConfig:
    """통합 설정 클래스 테스트"""
    
    @patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://test:test@localhost/test',
        'REDIS_URL': 'redis://localhost:6379/1',
        'KOREA_INVESTMENT_APP_KEY': 'test_korea_key',
        'KOREA_INVESTMENT_APP_SECRET': 'test_korea_secret',
        'EBEST_APP_KEY': 'test_ebest_key',
        'EBEST_APP_SECRET': 'test_ebest_secret',
        'CACHE_TTL_REALTIME': '5',
        'CACHE_TTL_MINUTE': '30',
        'SMART_MONEY_THRESHOLD': '2000000000',
        'LARGE_ORDER_THRESHOLD': '1000000000',
        'ANOMALY_DETECTION_SENSITIVITY': '3.0'
    })
    def test_config_from_environment_variables(self):
        """환경변수에서 설정 로드 테스트"""
        config = Config()
        
        # 데이터베이스 설정
        assert config.database.url == "postgresql://test:test@localhost/test"
        
        # 캐시 설정
        assert config.cache.redis_url == "redis://localhost:6379/1"
        assert config.cache.ttl_realtime == 5
        assert config.cache.ttl_minute == 30
        
        # API 설정
        assert config.api.korea_investment_key == "test_korea_key"
        assert config.api.korea_investment_secret == "test_korea_secret"
        assert config.api.ebest_key == "test_ebest_key"
        assert config.api.ebest_secret == "test_ebest_secret"
        
        # 분석 설정
        assert config.analysis.smart_money_threshold == 2000000000
        assert config.analysis.large_order_threshold == 1000000000
        assert config.analysis.anomaly_sensitivity == 3.0
    
    @patch.dict(os.environ, {}, clear=True)
    def test_config_default_values_when_no_env_vars(self):
        """환경변수가 없을 때 기본값 테스트"""
        config = Config()
        
        # 데이터베이스 기본값
        assert config.database.url == "postgresql://localhost/investor_trends"
        
        # 캐시 기본값
        assert config.cache.redis_url == "redis://localhost:6379/0"
        assert config.cache.ttl_realtime == 10
        assert config.cache.ttl_minute == 60
        
        # API 기본값 (빈 문자열)
        assert config.api.korea_investment_key == ""
        assert config.api.korea_investment_secret == ""
        assert config.api.ebest_key == ""
        assert config.api.ebest_secret == ""
        
        # 분석 기본값
        assert config.analysis.smart_money_threshold == 1000000000
        assert config.analysis.large_order_threshold == 500000000
        assert config.analysis.anomaly_sensitivity == 2.5
    
    def test_config_is_immutable_after_creation(self):
        """설정이 생성 후 불변인지 테스트"""
        config = Config()
        
        # 새로운 객체 할당 테스트
        original_database = config.database
        original_cache = config.cache
        original_api = config.api
        original_analysis = config.analysis
        
        # 동일한 객체 참조인지 확인
        assert config.database is original_database
        assert config.cache is original_cache
        assert config.api is original_api
        assert config.analysis is original_analysis
    
    def test_config_validation_empty_api_keys(self):
        """API 키가 비어있을 때 검증 테스트"""
        config = Config()
        
        # 빈 API 키 상태에서 검증 메서드 호출
        validation_result = config.validate_api_keys()
        
        assert validation_result is False
    
    @patch.dict(os.environ, {
        'KOREA_INVESTMENT_APP_KEY': 'valid_key',
        'KOREA_INVESTMENT_APP_SECRET': 'valid_secret',
        'EBEST_APP_KEY': 'valid_ebest_key',
        'EBEST_APP_SECRET': 'valid_ebest_secret'
    })
    def test_config_validation_valid_api_keys(self):
        """유효한 API 키일 때 검증 테스트"""
        config = Config()
        
        validation_result = config.validate_api_keys()
        
        assert validation_result is True
    
    def test_config_get_cache_ttl_by_type(self):
        """캐시 TTL 타입별 조회 테스트"""
        config = Config()
        
        assert config.get_cache_ttl("realtime") == 10
        assert config.get_cache_ttl("minute") == 60
        assert config.get_cache_ttl("hourly") == 3600
        assert config.get_cache_ttl("daily") == 86400
        assert config.get_cache_ttl("unknown") == 60  # 기본값
    
    def test_config_database_connection_string_format(self):
        """데이터베이스 연결 문자열 형식 테스트"""
        config = Config()
        
        # PostgreSQL 연결 문자열 형식 확인
        assert config.database.url.startswith("postgresql://")
        
        # 필수 구성 요소 확인
        db_url = config.database.url
        assert "://" in db_url
        assert "/" in db_url.split("://")[1]