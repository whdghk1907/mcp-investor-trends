"""
데이터베이스 연결 및 관리 클래스
"""
import asyncpg
import asyncio
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from urllib.parse import urlparse

from ..exceptions import DatabaseException


class DatabaseManager:
    """데이터베이스 매니저"""
    
    def __init__(self, database_url: str, pool_size: int = 20):
        self.database_url = database_url
        self.pool_size = pool_size
        self.pool = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """데이터베이스 풀 초기화"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.pool_size,
                max_size=self.pool_size,
                command_timeout=60
            )
            self.logger.info("Database pool initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            raise DatabaseException(
                "Failed to initialize database pool",
                details={"error": str(e), "database_url": self.database_url}
            )
    
    async def close(self):
        """데이터베이스 풀 종료"""
        if self.pool:
            await self.pool.close()
            self.logger.info("Database pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        if not self.pool:
            raise DatabaseException("Database pool not initialized")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def insert_investor_trading(self, data: Dict[str, Any]) -> None:
        """투자자 거래 데이터 삽입"""
        if not self._validate_insert_data(data):
            raise DatabaseException("Invalid insert data", details={"data": data})
        
        query = """
        INSERT INTO investor_trading (
            timestamp, stock_code, market,
            foreign_buy, foreign_sell, foreign_net,
            institution_buy, institution_sell, institution_net,
            individual_buy, individual_sell, individual_net,
            program_buy, program_sell, program_net
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
        )
        ON CONFLICT (timestamp, COALESCE(stock_code, ''), market) 
        DO UPDATE SET
            foreign_buy = EXCLUDED.foreign_buy,
            foreign_sell = EXCLUDED.foreign_sell,
            foreign_net = EXCLUDED.foreign_net,
            institution_buy = EXCLUDED.institution_buy,
            institution_sell = EXCLUDED.institution_sell,
            institution_net = EXCLUDED.institution_net,
            individual_buy = EXCLUDED.individual_buy,
            individual_sell = EXCLUDED.individual_sell,
            individual_net = EXCLUDED.individual_net,
            program_buy = EXCLUDED.program_buy,
            program_sell = EXCLUDED.program_sell,
            program_net = EXCLUDED.program_net,
            updated_at = NOW()
        """
        
        try:
            async with self.get_connection() as conn:
                values = self._extract_insert_values(data)
                await conn.execute(query, *values)
        except Exception as e:
            self.logger.error(f"Failed to insert investor trading data: {e}")
            raise DatabaseException(
                "Failed to insert investor trading data",
                table="investor_trading",
                details={"error": str(e), "data": data}
            )
    
    async def batch_insert_investor_trading(self, data_list: List[Dict[str, Any]]) -> None:
        """배치 투자자 거래 데이터 삽입"""
        if not data_list:
            return
        
        query = """
        INSERT INTO investor_trading (
            timestamp, stock_code, market,
            foreign_buy, foreign_sell, foreign_net,
            institution_buy, institution_sell, institution_net,
            individual_buy, individual_sell, individual_net,
            program_buy, program_sell, program_net
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
        )
        ON CONFLICT (timestamp, COALESCE(stock_code, ''), market) 
        DO UPDATE SET
            foreign_buy = EXCLUDED.foreign_buy,
            foreign_sell = EXCLUDED.foreign_sell,
            foreign_net = EXCLUDED.foreign_net,
            institution_buy = EXCLUDED.institution_buy,
            institution_sell = EXCLUDED.institution_sell,
            institution_net = EXCLUDED.institution_net,
            individual_buy = EXCLUDED.individual_buy,
            individual_sell = EXCLUDED.individual_sell,
            individual_net = EXCLUDED.individual_net,
            program_buy = EXCLUDED.program_buy,
            program_sell = EXCLUDED.program_sell,
            program_net = EXCLUDED.program_net,
            updated_at = NOW()
        """
        
        try:
            async with self.get_connection() as conn:
                for data in data_list:
                    if not self._validate_insert_data(data):
                        raise DatabaseException(
                            "Invalid insert data in batch",
                            details={"data": data}
                        )
                    
                    values = self._extract_insert_values(data)
                    await conn.execute(query, *values)
        except Exception as e:
            self.logger.error(f"Failed to batch insert investor trading data: {e}")
            raise DatabaseException(
                "Failed to batch insert investor trading data",
                table="investor_trading",
                details={"error": str(e), "batch_size": len(data_list)}
            )
    
    async def get_investor_trading_history(
        self,
        stock_code: Optional[str] = None,
        market: str = "ALL",
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """투자자 거래 이력 조회"""
        
        base_query = "SELECT * FROM investor_trading"
        where_conditions = [f"timestamp >= NOW() - INTERVAL '{hours} hours'"]
        params = []
        
        if stock_code:
            where_conditions.append(f"stock_code = ${len(params) + 1}")
            params.append(stock_code)
            
        if market != "ALL":
            where_conditions.append(f"market = ${len(params) + 1}")
            params.append(market)
        
        query = self._build_query_with_filters(base_query, where_conditions)
        query += " ORDER BY timestamp DESC LIMIT 1000"
        
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get investor trading history: {e}")
            raise DatabaseException(
                "Failed to get investor trading history",
                table="investor_trading",
                query=query,
                details={"error": str(e)}
            )
    
    async def health_check(self) -> bool:
        """데이터베이스 헬스 체크"""
        if not self.pool:
            return False
        
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False
    
    def _validate_insert_data(self, data: Dict[str, Any]) -> bool:
        """삽입 데이터 유효성 검증"""
        required_fields = ["timestamp", "market"]
        
        for field in required_fields:
            if field not in data:
                return False
        
        # 타임스탬프 유효성 검증
        if not isinstance(data["timestamp"], datetime):
            return False
        
        # 시장 코드 유효성 검증
        if not isinstance(data["market"], str) or len(data["market"]) == 0:
            return False
        
        # 종목 코드 유효성 검증 (선택사항)
        if "stock_code" in data and data["stock_code"] is not None:
            if not isinstance(data["stock_code"], str) or len(data["stock_code"]) != 6:
                return False
        
        return True
    
    def _extract_insert_values(self, data: Dict[str, Any]) -> List[Any]:
        """삽입 데이터에서 값 추출"""
        return [
            data.get("timestamp"),
            data.get("stock_code"),
            data.get("market"),
            data.get("foreign_buy", 0),
            data.get("foreign_sell", 0),
            data.get("foreign_net", 0),
            data.get("institution_buy", 0),
            data.get("institution_sell", 0),
            data.get("institution_net", 0),
            data.get("individual_buy", 0),
            data.get("individual_sell", 0),
            data.get("individual_net", 0),
            data.get("program_buy", 0),
            data.get("program_sell", 0),
            data.get("program_net", 0)
        ]
    
    def _build_query_with_filters(self, base_query: str, filters: List[str]) -> str:
        """필터가 있는 쿼리 빌드"""
        if not filters:
            return base_query
        
        return f"{base_query} WHERE {' AND '.join(filters)}"
    
    def _parse_connection_string(self) -> Dict[str, str]:
        """연결 문자열 파싱"""
        parsed = urlparse(self.database_url)
        
        return {
            "host": parsed.hostname or "localhost",
            "port": str(parsed.port) if parsed.port else "5432",
            "database": parsed.path.lstrip("/") if parsed.path else "",
            "user": parsed.username or "",
            "password": parsed.password or ""
        }