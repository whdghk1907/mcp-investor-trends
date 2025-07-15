"""
TDD 테스트: MCP 서버 클래스 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from src.server import InvestorTrendsMCPServer
from src.config import Config


class TestInvestorTrendsMCPServer:
    """MCP 서버 클래스 테스트"""
    
    @pytest.fixture
    def mock_config(self):
        """테스트용 Config 모킹"""
        config = MagicMock()
        
        # API 설정 모킹
        config.api = MagicMock()
        config.api.korea_investment_key = "test_key"
        config.api.korea_investment_secret = "test_secret"
        config.api.ebest_key = "ebest_key"
        config.api.ebest_secret = "ebest_secret"
        
        # 데이터베이스 설정 모킹
        config.database = MagicMock()
        config.database.url = "postgresql://test"
        
        # 캐시 설정 모킹
        config.cache = MagicMock()
        config.cache.redis_url = "redis://test"
        
        return config
    
    @pytest.fixture
    def server(self, mock_config):
        """테스트용 서버 인스턴스"""
        with patch('src.server.Config', return_value=mock_config):
            server = InvestorTrendsMCPServer()
            return server
    
    def test_server_initialization(self, server):
        """서버 초기화 테스트"""
        assert server is not None
        assert server.config is not None
        assert hasattr(server, 'tools')
        assert hasattr(server, 'logger')
    
    def test_server_has_required_tools(self, server):
        """필수 도구 존재 확인"""
        expected_tools = [
            'get_investor_trading',
            'get_ownership_changes',
            'get_program_trading',
            'get_sector_investor_flow',
            'get_time_based_flow',
            'get_smart_money_tracker',
            'get_investor_sentiment'
        ]
        
        for tool_name in expected_tools:
            assert hasattr(server, tool_name), f"Tool {tool_name} not found"
    
    @pytest.mark.asyncio
    async def test_server_startup(self, server):
        """서버 시작 테스트"""
        with patch.object(server, '_initialize_database') as mock_db_init, \
             patch.object(server, '_initialize_api_clients') as mock_api_init:
            
            await server.startup()
            
            mock_db_init.assert_called_once()
            mock_api_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_server_shutdown(self, server):
        """서버 종료 테스트"""
        with patch.object(server, '_cleanup_database') as mock_db_cleanup, \
             patch.object(server, '_cleanup_api_clients') as mock_api_cleanup:
            
            await server.shutdown()
            
            mock_db_cleanup.assert_called_once()
            mock_api_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_with_valid_params(self, server):
        """유효한 파라미터로 투자자 거래 조회 테스트"""
        # 모킹 설정
        expected_result = {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "scope": "MARKET",
            "investor_data": {
                "foreign": {
                    "buy_amount": 1000000000,
                    "sell_amount": 800000000,
                    "net_amount": 200000000
                }
            }
        }
        
        with patch.object(server, '_fetch_investor_data_basic', return_value=expected_result) as mock_fetch:
            result = await server.get_investor_trading(
                investor_type="FOREIGN",
                period="1D",
                market="KOSPI"
            )
            
            assert result == expected_result
            mock_fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_with_invalid_params(self, server):
        """잘못된 파라미터로 투자자 거래 조회 테스트"""
        result = await server.get_investor_trading(
            investor_type="INVALID",
            period="1D",
            market="KOSPI"
        )
        
        # 에러가 반환되어야 함
        assert result["success"] == False
        assert "error" in result
        assert result["error"]["type"] == "ValueError"
    
    @pytest.mark.asyncio
    async def test_get_program_trading_basic(self, server):
        """기본 프로그램 매매 조회 테스트"""
        expected_result = {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "market": "KOSPI",
            "program_trading": {
                "summary": {
                    "total_buy": 500000000,
                    "total_sell": 400000000,
                    "net_value": 100000000
                }
            }
        }
        
        with patch.object(server, '_fetch_program_data', return_value=expected_result) as mock_fetch:
            result = await server.get_program_trading(market="KOSPI")
            
            assert result == expected_result
            mock_fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_smart_money_tracker_basic(self, server):
        """기본 스마트머니 추적 테스트"""
        expected_result = {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "smart_money_signals": [
                {
                    "stock_code": "005930",
                    "signal_type": "INSTITUTIONAL_ACCUMULATION",
                    "confidence": 8.5
                }
            ],
            "market_smart_money_index": {
                "current_value": 72.5,
                "trend": "INCREASING"
            }
        }
        
        with patch.object(server, '_track_smart_money', return_value=expected_result) as mock_track:
            result = await server.get_smart_money_tracker(
                detection_method="LARGE_ORDERS",
                min_confidence=7.0
            )
            
            assert result == expected_result
            mock_track.assert_called_once()
    
    def test_validate_investor_type_valid(self, server):
        """유효한 투자자 타입 검증"""
        valid_types = ["FOREIGN", "INSTITUTION", "INDIVIDUAL", "ALL"]
        
        for investor_type in valid_types:
            assert server._validate_investor_type(investor_type) == True
    
    def test_validate_investor_type_invalid(self, server):
        """잘못된 투자자 타입 검증"""
        invalid_types = ["INVALID", "UNKNOWN", "", None, 123]
        
        for investor_type in invalid_types:
            assert server._validate_investor_type(investor_type) == False
    
    def test_validate_period_valid(self, server):
        """유효한 기간 검증"""
        valid_periods = ["1D", "5D", "20D", "60D"]
        
        for period in valid_periods:
            assert server._validate_period(period) == True
    
    def test_validate_period_invalid(self, server):
        """잘못된 기간 검증"""
        invalid_periods = ["1H", "1W", "1M", "INVALID", "", None]
        
        for period in invalid_periods:
            assert server._validate_period(period) == False
    
    def test_validate_market_valid(self, server):
        """유효한 시장 검증"""
        valid_markets = ["ALL", "KOSPI", "KOSDAQ"]
        
        for market in valid_markets:
            assert server._validate_market(market) == True
    
    def test_validate_market_invalid(self, server):
        """잘못된 시장 검증"""
        invalid_markets = ["NYSE", "NASDAQ", "INVALID", "", None]
        
        for market in invalid_markets:
            assert server._validate_market(market) == False
    
    @pytest.mark.asyncio
    async def test_error_handling_api_failure(self, server):
        """API 실패 시 에러 처리 테스트"""
        with patch.object(server, '_fetch_investor_data_basic', side_effect=Exception("API Error")):
            
            result = await server.get_investor_trading()
            assert result["success"] == False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_database_failure(self, server):
        """데이터베이스 실패 시 에러 처리 테스트"""
        with patch.object(server, '_initialize_database', side_effect=Exception("DB Error")):
            
            with pytest.raises(Exception, match="DB Error"):
                await server.startup()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self, server):
        """동시 요청 처리 테스트"""
        # 여러 개의 동시 요청 생성
        tasks = []
        
        with patch.object(server, '_fetch_investor_data_basic', return_value={"test": "data"}):
            for i in range(10):
                task = server.get_investor_trading(
                    investor_type="FOREIGN",
                    period="1D"
                )
                tasks.append(task)
            
            # 모든 요청이 성공적으로 완료되는지 확인
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 10
            assert all(result == {"test": "data"} for result in results)
    
    def test_server_tool_registration(self, server):
        """도구 등록 확인 테스트"""
        # 서버가 필요한 도구들을 모두 등록했는지 확인
        required_tools = [
            'get_investor_trading',
            'get_program_trading',
            'get_smart_money_tracker'
        ]
        
        for tool_name in required_tools:
            assert hasattr(server, tool_name)
            # 도구가 호출 가능한지 확인
            tool_method = getattr(server, tool_name)
            assert callable(tool_method)
    
    @pytest.mark.asyncio
    async def test_server_health_check(self, server):
        """서버 헬스 체크 테스트"""
        with patch.object(server, '_check_database_health', return_value=True), \
             patch.object(server, '_check_cache_health', return_value=True), \
             patch.object(server, '_check_api_health', return_value=True):
            
            health_status = await server.health_check()
            
            assert health_status["status"] == "healthy"
            assert health_status["database"] == True
            assert health_status["cache"] == True
            assert health_status["api"] == True
    
    @pytest.mark.asyncio
    async def test_server_health_check_failure(self, server):
        """서버 헬스 체크 실패 테스트"""
        with patch.object(server, '_check_database_health', return_value=False), \
             patch.object(server, '_check_cache_health', return_value=True), \
             patch.object(server, '_check_api_health', return_value=True):
            
            health_status = await server.health_check()
            
            assert health_status["status"] == "unhealthy"
            assert health_status["database"] == False
            assert health_status["cache"] == True
            assert health_status["api"] == True