"""
투자자 동향 MCP 서버 설정 관리
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    url: str
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30


@dataclass
class CacheConfig:
    """캐시 설정"""
    redis_url: str
    ttl_realtime: int = 10
    ttl_minute: int = 60
    ttl_hourly: int = 3600
    ttl_daily: int = 86400


@dataclass
class APIConfig:
    """API 설정"""
    korea_investment_key: str
    korea_investment_secret: str
    ebest_key: str
    ebest_secret: str
    rate_limit_per_minute: int = 200
    
    @property
    def app_key(self) -> str:
        """앱 키 (korea_investment_key의 별칭)"""
        return self.korea_investment_key
    
    @property
    def app_secret(self) -> str:
        """앱 시크릿 (korea_investment_secret의 별칭)"""
        return self.korea_investment_secret


@dataclass
class AnalysisConfig:
    """분석 설정"""
    smart_money_threshold: int = 1000000000
    large_order_threshold: int = 500000000
    anomaly_sensitivity: float = 2.5
    pattern_confidence_threshold: float = 0.7


class Config:
    """통합 설정 클래스"""
    
    def __init__(self):
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "postgresql://localhost/investor_trends")
        )
        
        self.cache = CacheConfig(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            ttl_realtime=int(os.getenv("CACHE_TTL_REALTIME", "10")),
            ttl_minute=int(os.getenv("CACHE_TTL_MINUTE", "60")),
            ttl_hourly=int(os.getenv("CACHE_TTL_HOURLY", "3600")),
            ttl_daily=int(os.getenv("CACHE_TTL_DAILY", "86400"))
        )
        
        self.api = APIConfig(
            korea_investment_key=os.getenv("KOREA_INVESTMENT_APP_KEY", ""),
            korea_investment_secret=os.getenv("KOREA_INVESTMENT_APP_SECRET", ""),
            ebest_key=os.getenv("EBEST_APP_KEY", ""),
            ebest_secret=os.getenv("EBEST_APP_SECRET", "")
        )
        
        self.analysis = AnalysisConfig(
            smart_money_threshold=int(os.getenv("SMART_MONEY_THRESHOLD", "1000000000")),
            large_order_threshold=int(os.getenv("LARGE_ORDER_THRESHOLD", "500000000")),
            anomaly_sensitivity=float(os.getenv("ANOMALY_DETECTION_SENSITIVITY", "2.5"))
        )
    
    def validate_api_keys(self) -> bool:
        """API 키 유효성 검사"""
        return bool(
            self.api.korea_investment_key and 
            self.api.korea_investment_secret and
            self.api.ebest_key and 
            self.api.ebest_secret
        )
    
    def get_cache_ttl(self, cache_type: str) -> int:
        """캐시 타입별 TTL 반환"""
        ttl_map = {
            "realtime": self.cache.ttl_realtime,
            "minute": self.cache.ttl_minute,
            "hourly": self.cache.ttl_hourly,
            "daily": self.cache.ttl_daily
        }
        return ttl_map.get(cache_type, self.cache.ttl_minute)  # 기본값