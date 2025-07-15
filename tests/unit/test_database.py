"""
TDD 테스트: 데이터베이스 연결 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from src.utils.database import DatabaseManager
from src.exceptions import DatabaseException


class TestDatabaseManager:
    """데이터베이스 매니저 테스트"""
    
    @pytest.fixture
    def db_manager(self):
        """테스트용 데이터베이스 매니저"""
        return DatabaseManager(
            database_url="postgresql://test:test@localhost/test_db",
            pool_size=5
        )
    
    def test_database_manager_initialization(self, db_manager):
        """데이터베이스 매니저 초기화 테스트"""
        assert db_manager.database_url == "postgresql://test:test@localhost/test_db"
        assert db_manager.pool_size == 5
        assert db_manager.pool is None
        assert db_manager.logger is not None
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, db_manager):
        """데이터베이스 풀 초기화 성공 테스트"""
        mock_pool = AsyncMock()
        
        with patch('asyncpg.create_pool', return_value=mock_pool) as mock_create_pool:
            await db_manager.initialize()
            
            mock_create_pool.assert_called_once_with(
                "postgresql://test:test@localhost/test_db",
                min_size=5,
                max_size=5,
                command_timeout=60
            )
            assert db_manager.pool == mock_pool
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, db_manager):
        """데이터베이스 풀 초기화 실패 테스트"""
        with patch('asyncpg.create_pool', side_effect=Exception("Connection failed")):
            with pytest.raises(DatabaseException, match="Failed to initialize database pool"):
                await db_manager.initialize()
    
    @pytest.mark.asyncio
    async def test_close_success(self, db_manager):
        """데이터베이스 풀 종료 성공 테스트"""
        mock_pool = AsyncMock()
        db_manager.pool = mock_pool
        
        await db_manager.close()
        
        mock_pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_with_no_pool(self, db_manager):
        """풀이 없는 상태에서 종료 테스트"""
        # pool이 None인 상태에서 close 호출 시 에러가 발생하지 않아야 함
        await db_manager.close()
        # 아무것도 발생하지 않아야 함
    
    @pytest.mark.asyncio
    async def test_get_connection_context_manager(self, db_manager):
        """데이터베이스 연결 컨텍스트 매니저 테스트"""
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager.pool = mock_pool
        
        async with db_manager.get_connection() as conn:
            assert conn == mock_connection
        
        mock_pool.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_insert_investor_trading_success(self, db_manager):
        """투자자 거래 데이터 삽입 성공 테스트"""
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager.pool = mock_pool
        
        test_data = {
            "timestamp": datetime.now(),
            "stock_code": "005930",
            "market": "KOSPI",
            "foreign_buy": 1000000000,
            "foreign_sell": 800000000,
            "foreign_net": 200000000,
            "institution_buy": 500000000,
            "institution_sell": 600000000,
            "institution_net": -100000000,
            "individual_buy": 300000000,
            "individual_sell": 400000000,
            "individual_net": -100000000,
            "program_buy": 100000000,
            "program_sell": 80000000,
            "program_net": 20000000
        }
        
        await db_manager.insert_investor_trading(test_data)
        
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        assert "INSERT INTO investor_trading" in call_args[0][0]
        assert "ON CONFLICT" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_insert_investor_trading_failure(self, db_manager):
        """투자자 거래 데이터 삽입 실패 테스트"""
        mock_connection = AsyncMock()
        mock_connection.execute.side_effect = Exception("Database error")
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager.pool = mock_pool
        
        test_data = {"timestamp": datetime.now()}
        
        with pytest.raises(DatabaseException, match="Failed to insert investor trading data"):
            await db_manager.insert_investor_trading(test_data)
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_history_success(self, db_manager):
        """투자자 거래 이력 조회 성공 테스트"""
        mock_connection = AsyncMock()
        mock_rows = [
            {"timestamp": datetime.now(), "stock_code": "005930", "foreign_net": 1000000000},
            {"timestamp": datetime.now(), "stock_code": "000660", "foreign_net": 500000000}
        ]
        mock_connection.fetch.return_value = mock_rows
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager.pool = mock_pool
        
        result = await db_manager.get_investor_trading_history(
            stock_code="005930",
            market="KOSPI",
            hours=24
        )
        
        assert len(result) == 2
        assert result[0]["stock_code"] == "005930"
        assert result[1]["stock_code"] == "000660"
        
        mock_connection.fetch.assert_called_once()
        call_args = mock_connection.fetch.call_args
        assert "SELECT * FROM investor_trading" in call_args[0][0]
        assert "WHERE" in call_args[0][0]
        assert "ORDER BY timestamp DESC" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_history_with_filters(self, db_manager):
        """필터가 있는 투자자 거래 이력 조회 테스트"""
        mock_connection = AsyncMock()
        mock_connection.fetch.return_value = []
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager.pool = mock_pool
        
        await db_manager.get_investor_trading_history(
            stock_code="005930",
            market="KOSPI",
            hours=24
        )
        
        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        params = call_args[0][1:]
        
        # 쿼리에 필터 조건이 포함되어야 함
        assert "stock_code = $" in query
        assert "market = $" in query
        assert "timestamp >= NOW() - INTERVAL" in query
        
        # 파라미터가 올바르게 전달되어야 함
        assert "005930" in params
        assert "KOSPI" in params
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_history_no_filters(self, db_manager):
        """필터가 없는 투자자 거래 이력 조회 테스트"""
        mock_connection = AsyncMock()
        mock_connection.fetch.return_value = []
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager.pool = mock_pool
        
        await db_manager.get_investor_trading_history(
            stock_code=None,
            market="ALL",
            hours=24
        )
        
        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        
        # stock_code 조건이 없어야 함
        assert "stock_code = $" not in query
        # market 조건이 없어야 함 (ALL인 경우)
        assert "market = $" not in query
    
    @pytest.mark.asyncio
    async def test_batch_insert_investor_trading_success(self, db_manager):
        """배치 투자자 거래 데이터 삽입 성공 테스트"""
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager.pool = mock_pool
        
        test_data = [
            {
                "timestamp": datetime.now(),
                "stock_code": "005930",
                "market": "KOSPI",
                "foreign_buy": 1000000000,
                "foreign_sell": 800000000,
                "foreign_net": 200000000
            },
            {
                "timestamp": datetime.now(),
                "stock_code": "000660",
                "market": "KOSPI",
                "foreign_buy": 500000000,
                "foreign_sell": 600000000,
                "foreign_net": -100000000
            }
        ]
        
        await db_manager.batch_insert_investor_trading(test_data)
        
        # 트랜잭션 시작/종료 확인
        assert mock_connection.execute.call_count == len(test_data)
    
    @pytest.mark.asyncio
    async def test_batch_insert_investor_trading_transaction_rollback(self, db_manager):
        """배치 삽입 시 트랜잭션 롤백 테스트"""
        mock_connection = AsyncMock()
        mock_connection.execute.side_effect = [None, Exception("Database error")]  # 두 번째 실행에서 에러
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager.pool = mock_pool
        
        test_data = [
            {"timestamp": datetime.now(), "stock_code": "005930"},
            {"timestamp": datetime.now(), "stock_code": "000660"}
        ]
        
        with pytest.raises(DatabaseException, match="Failed to batch insert investor trading data"):
            await db_manager.batch_insert_investor_trading(test_data)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, db_manager):
        """데이터베이스 헬스 체크 성공 테스트"""
        mock_connection = AsyncMock()
        mock_connection.fetchval.return_value = 1
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager.pool = mock_pool
        
        result = await db_manager.health_check()
        
        assert result == True
        mock_connection.fetchval.assert_called_once_with("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, db_manager):
        """데이터베이스 헬스 체크 실패 테스트"""
        mock_connection = AsyncMock()
        mock_connection.fetchval.side_effect = Exception("Connection failed")
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager.pool = mock_pool
        
        result = await db_manager.health_check()
        
        assert result == False
    
    @pytest.mark.asyncio
    async def test_health_check_no_pool(self, db_manager):
        """풀이 없는 상태에서 헬스 체크 테스트"""
        # pool이 None인 상태
        result = await db_manager.health_check()
        
        assert result == False
    
    def test_build_query_with_filters(self, db_manager):
        """필터가 있는 쿼리 빌드 테스트"""
        base_query = "SELECT * FROM investor_trading"
        filters = ["stock_code = $1", "market = $2"]
        
        query = db_manager._build_query_with_filters(base_query, filters)
        
        expected = "SELECT * FROM investor_trading WHERE stock_code = $1 AND market = $2"
        assert query == expected
    
    def test_build_query_without_filters(self, db_manager):
        """필터가 없는 쿼리 빌드 테스트"""
        base_query = "SELECT * FROM investor_trading"
        filters = []
        
        query = db_manager._build_query_with_filters(base_query, filters)
        
        assert query == base_query
    
    def test_validate_insert_data_valid(self, db_manager):
        """유효한 삽입 데이터 검증 테스트"""
        valid_data = {
            "timestamp": datetime.now(),
            "stock_code": "005930",
            "market": "KOSPI",
            "foreign_buy": 1000000000,
            "foreign_sell": 800000000,
            "foreign_net": 200000000
        }
        
        assert db_manager._validate_insert_data(valid_data) == True
    
    def test_validate_insert_data_invalid(self, db_manager):
        """잘못된 삽입 데이터 검증 테스트"""
        invalid_data = {
            "timestamp": "invalid_timestamp",
            "stock_code": None,
            "market": "KOSPI"
        }
        
        assert db_manager._validate_insert_data(invalid_data) == False
    
    def test_extract_insert_values(self, db_manager):
        """삽입 데이터에서 값 추출 테스트"""
        data = {
            "timestamp": datetime.now(),
            "stock_code": "005930",
            "market": "KOSPI",
            "foreign_buy": 1000000000,
            "foreign_sell": 800000000,
            "foreign_net": 200000000
        }
        
        values = db_manager._extract_insert_values(data)
        
        assert len(values) == 15  # 15개 필드
        assert values[0] == data["timestamp"]
        assert values[1] == data["stock_code"]
        assert values[2] == data["market"]
        assert values[3] == data["foreign_buy"]
    
    def test_connection_string_parsing(self, db_manager):
        """연결 문자열 파싱 테스트"""
        connection_info = db_manager._parse_connection_string()
        
        assert connection_info["host"] == "localhost"
        assert connection_info["database"] == "test_db"
        assert connection_info["user"] == "test"
        assert connection_info["password"] == "test"