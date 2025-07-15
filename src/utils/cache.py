"""
캐시 매니저 클래스
"""
import asyncio
import json
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

from ..config import Config
from ..exceptions import CacheException


class CacheManager:
    """캐시 매니저"""
    
    def __init__(self, config: Config):
        self.config = config
        self.redis_client = None
        self.logger = logging.getLogger(__name__)
        self._local_cache = {}  # 폴백용 로컬 캐시
        
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis not available, using local cache")
    
    async def initialize(self):
        """캐시 초기화"""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    self.config.cache.redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                
                # 연결 테스트
                await self.redis_client.ping()
                self.logger.info("Redis cache initialized successfully")
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize Redis cache: {e}")
                self.redis_client = None
        else:
            self.logger.info("Using local cache (Redis not available)")
    
    async def close(self):
        """캐시 연결 종료"""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Redis cache connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        try:
            if self.redis_client:
                # Redis에서 조회
                data = await self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # 로컬 캐시에서 조회
                cache_item = self._local_cache.get(key)
                if cache_item and cache_item["expires_at"] > datetime.now():
                    return cache_item["data"]
                elif cache_item:
                    # 만료된 항목 제거
                    del self._local_cache[key]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """캐시에 데이터 저장"""
        try:
            serialized_value = json.dumps(value, default=str)
            
            if self.redis_client:
                # Redis에 저장
                await self.redis_client.setex(key, ttl, serialized_value)
            else:
                # 로컬 캐시에 저장
                expires_at = datetime.now() + timedelta(seconds=ttl)
                self._local_cache[key] = {
                    "data": value,
                    "expires_at": expires_at
                }
                
                # 로컬 캐시 크기 제한 (1000개)
                if len(self._local_cache) > 1000:
                    # 가장 오래된 항목 제거
                    oldest_key = min(
                        self._local_cache.keys(),
                        key=lambda k: self._local_cache[k]["expires_at"]
                    )
                    del self._local_cache[oldest_key]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        try:
            if self.redis_client:
                # Redis에서 삭제
                result = await self.redis_client.delete(key)
                return result > 0
            else:
                # 로컬 캐시에서 삭제
                if key in self._local_cache:
                    del self._local_cache[key]
                    return True
                return False
                
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """캐시 키 존재 여부 확인"""
        try:
            if self.redis_client:
                return await self.redis_client.exists(key) > 0
            else:
                cache_item = self._local_cache.get(key)
                return cache_item is not None and cache_item["expires_at"] > datetime.now()
                
        except Exception as e:
            self.logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """패턴에 맞는 캐시 키들 삭제"""
        try:
            deleted_count = 0
            
            if self.redis_client:
                # Redis에서 패턴 매칭으로 삭제
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted_count = await self.redis_client.delete(*keys)
            else:
                # 로컬 캐시에서 패턴 매칭으로 삭제
                import fnmatch
                keys_to_delete = [
                    key for key in self._local_cache.keys()
                    if fnmatch.fnmatch(key, pattern)
                ]
                for key in keys_to_delete:
                    del self._local_cache[key]
                deleted_count = len(keys_to_delete)
            
            self.logger.info(f"Cleared {deleted_count} cache keys matching pattern: {pattern}")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    async def increment(self, key: str, amount: int = 1, ttl: int = 300) -> int:
        """카운터 증가"""
        try:
            if self.redis_client:
                # Redis 카운터
                pipe = self.redis_client.pipeline()
                pipe.incr(key, amount)
                pipe.expire(key, ttl)
                results = await pipe.execute()
                return results[0]
            else:
                # 로컬 캐시 카운터
                cache_item = self._local_cache.get(key)
                if cache_item and cache_item["expires_at"] > datetime.now():
                    new_value = cache_item["data"] + amount
                else:
                    new_value = amount
                
                expires_at = datetime.now() + timedelta(seconds=ttl)
                self._local_cache[key] = {
                    "data": new_value,
                    "expires_at": expires_at
                }
                return new_value
                
        except Exception as e:
            self.logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    async def health_check(self) -> bool:
        """캐시 헬스 체크"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            else:
                # 로컬 캐시는 항상 건강
                return True
                
        except Exception as e:
            self.logger.error(f"Cache health check failed: {e}")
            return False
    
    def get_cache_info(self) -> dict:
        """캐시 정보 반환"""
        info = {
            "cache_type": "redis" if self.redis_client else "local",
            "redis_available": REDIS_AVAILABLE,
            "local_cache_size": len(self._local_cache)
        }
        
        if self.redis_client:
            info["redis_url"] = self.config.cache.redis_url
        
        return info
    
    async def _cleanup_expired_local_cache(self):
        """만료된 로컬 캐시 항목 정리"""
        if not self._local_cache:
            return
        
        try:
            now = datetime.now()
            expired_keys = [
                key for key, item in self._local_cache.items()
                if item["expires_at"] <= now
            ]
            
            for key in expired_keys:
                del self._local_cache[key]
            
            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache items")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up expired cache: {e}")


class MockCacheManager:
    """테스트용 Mock 캐시 매니저"""
    
    def __init__(self):
        self._cache = {}
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        pass
    
    async def close(self):
        pass
    
    async def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        self._cache[key] = value
        return True
    
    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        return key in self._cache
    
    async def clear_pattern(self, pattern: str) -> int:
        import fnmatch
        keys_to_delete = [
            key for key in self._cache.keys()
            if fnmatch.fnmatch(key, pattern)
        ]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)
    
    async def increment(self, key: str, amount: int = 1, ttl: int = 300) -> int:
        current = self._cache.get(key, 0)
        new_value = current + amount
        self._cache[key] = new_value
        return new_value
    
    async def health_check(self) -> bool:
        return True
    
    def get_cache_info(self) -> dict:
        return {
            "cache_type": "mock",
            "cache_size": len(self._cache)
        }