"""
TDD 통합 테스트: 전체 시스템 통합 테스트
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from src.config import Config
from src.server import InvestorTrendsMCPServer
from src.api.korea_investment import KoreaInvestmentAPI
from src.utils.database import DatabaseManager
from src.exceptions import APIException, DatabaseException


class TestSystemIntegration:
    """전체 시스템 통합 테스트"""
    
    @pytest.fixture
    def config(self):
        """테스트용 설정"""
        return Config()
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock API 클라이언트"""
        api_client = MagicMock(spec=KoreaInvestmentAPI)
        api_client.get_investor_trading = AsyncMock()
        api_client.get_program_trading = AsyncMock()
        api_client.close = AsyncMock()
        return api_client
    
    @pytest.fixture
    def mock_database(self):
        """Mock 데이터베이스"""
        db = MagicMock(spec=DatabaseManager)
        db.initialize = AsyncMock()
        db.insert_investor_trading = AsyncMock()
        db.get_investor_trading_history = AsyncMock()
        db.health_check = AsyncMock(return_value=True)
        db.close = AsyncMock()
        return db
    
    @pytest.fixture
    def server(self, config, mock_api_client, mock_database):
        """테스트용 MCP 서버"""
        server = InvestorTrendsMCPServer(config)
        server.api_client = mock_api_client
        server.database = mock_database
        return server
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, server, config):
        """서버 초기화 테스트"""
        assert server.config == config
        assert server.api_client is not None
        assert server.database is not None
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_with_stock_code(self, server, mock_api_client, mock_database):
        """종목 코드가 있는 투자자 거래 데이터 조회 테스트"""
        # API 응답 설정
        mock_api_response = {
            "success": True,
            "data": [
                {
                    "stock_code": "005930",
                    "foreign_net_buy_qty": 1000000,
                    "foreign_net_buy_amount": 78500000000,
                    "institution_net_buy_qty": -500000,
                    "institution_net_buy_amount": -39250000000,
                    "individual_net_buy_qty": -500000,
                    "individual_net_buy_amount": -39250000000
                }
            ]
        }
        mock_api_client.get_investor_trading.return_value = mock_api_response
        
        # 데이터베이스 이력 설정
        mock_db_history = [
            {
                "timestamp": datetime.now(),
                "stock_code": "005930",
                "foreign_net": 78500000000,
                "institution_net": -39250000000,
                "individual_net": -39250000000
            }
        ]
        mock_database.get_investor_trading_history.return_value = mock_db_history
        
        # 서버 메서드 호출
        result = await server.get_investor_trading(
            stock_code="005930",
            investor_type="FOREIGN",
            period="1D",
            market="KOSPI"
        )
        
        # 결과 검증
        assert result["success"] == True
        assert "current_data" in result
        assert "historical_data" in result
        assert "analysis" in result
        assert result["current_data"]["stock_code"] == "005930"
        
        # API 호출 검증
        mock_api_client.get_investor_trading.assert_called_once_with(
            stock_code="005930",
            market="KOSPI"
        )
        
        # 데이터베이스 호출 검증
        mock_database.get_investor_trading_history.assert_called_once_with(
            stock_code="005930",
            market="KOSPI",
            hours=24
        )
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_market_overview(self, server, mock_api_client, mock_database):
        """시장 전체 투자자 거래 개요 조회 테스트"""
        # API 응답 설정
        mock_api_response = {
            "success": True,
            "data": [
                {
                    "market": "KOSPI",
                    "foreign_net_buy_amount": 500000000000,
                    "institution_net_buy_amount": -300000000000,
                    "individual_net_buy_amount": -200000000000
                }
            ]
        }
        mock_api_client.get_investor_trading.return_value = mock_api_response
        
        # 데이터베이스 이력 설정
        mock_db_history = []
        mock_database.get_investor_trading_history.return_value = mock_db_history
        
        # 서버 메서드 호출
        result = await server.get_investor_trading(
            stock_code=None,
            investor_type="ALL",
            period="1D",
            market="KOSPI"
        )
        
        # 결과 검증
        assert result["success"] == True
        assert "market_overview" in result
        assert "analysis" in result
        
        # API 호출 검증
        mock_api_client.get_investor_trading.assert_called_once_with(
            stock_code=None,
            market="KOSPI"
        )
    
    @pytest.mark.asyncio
    async def test_get_program_trading_data(self, server, mock_api_client):
        """프로그램 매매 데이터 조회 테스트"""
        # API 응답 설정
        mock_api_response = {
            "success": True,
            "data": [
                {
                    "market": "KOSPI",
                    "program_buy_amount": 100000000000,
                    "program_sell_amount": 80000000000,
                    "program_net_amount": 20000000000
                }
            ]
        }
        mock_api_client.get_program_trading.return_value = mock_api_response
        
        # 서버 메서드 호출
        result = await server.get_program_trading(
            market="KOSPI",
            period="1D"
        )
        
        # 결과 검증
        assert result["success"] == True
        assert "program_trading" in result
        assert result["program_trading"]["market"] == "KOSPI"
        assert result["program_trading"]["net_amount"] == 20000000000
        
        # API 호출 검증
        mock_api_client.get_program_trading.assert_called_once_with(
            market="KOSPI"
        )
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, server, mock_api_client):
        """API 에러 처리 테스트"""
        # API 에러 설정
        mock_api_client.get_investor_trading.side_effect = APIException("API 서버 에러")
        
        # 서버 메서드 호출
        result = await server.get_investor_trading(
            stock_code="005930",
            investor_type="FOREIGN",
            period="1D",
            market="KOSPI"
        )
        
        # 결과 검증
        assert result["success"] == False
        assert "error" in result
        assert result["error"]["type"] == "APIException"
        assert "API 서버 에러" in result["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, server, mock_database):
        """데이터베이스 에러 처리 테스트"""
        # 데이터베이스 에러 설정
        mock_database.get_investor_trading_history.side_effect = DatabaseException("DB 연결 에러")
        
        # 서버 메서드 호출
        result = await server.get_investor_trading(
            stock_code="005930",
            investor_type="FOREIGN",
            period="1D",
            market="KOSPI"
        )
        
        # 결과 검증
        assert result["success"] == False
        assert "error" in result
        assert result["error"]["type"] == "DatabaseException"
        assert "DB 연결 에러" in result["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_smart_money_analysis(self, server, mock_api_client, mock_database):
        """스마트 머니 분석 테스트"""
        # API 응답 설정 (외국인 대량 매수)
        mock_api_response = {
            "success": True,
            "data": [
                {
                    "stock_code": "005930",
                    "foreign_net_buy_qty": 2000000,
                    "foreign_net_buy_amount": 157000000000,
                    "institution_net_buy_qty": 1000000,
                    "institution_net_buy_amount": 78500000000,
                    "individual_net_buy_qty": -3000000,
                    "individual_net_buy_amount": -235500000000
                }
            ]
        }
        mock_api_client.get_investor_trading.return_value = mock_api_response
        
        # 데이터베이스 이력 설정
        mock_db_history = []
        mock_database.get_investor_trading_history.return_value = mock_db_history
        
        # 서버 메서드 호출
        result = await server.get_investor_trading(
            stock_code="005930",
            investor_type="ALL",
            period="1D",
            market="KOSPI"
        )
        
        # 결과 검증
        assert result["success"] == True
        assert "analysis" in result
        assert "smart_money_signal" in result["analysis"]
        
        # 스마트 머니 신호 확인
        smart_money = result["analysis"]["smart_money_signal"]
        assert smart_money["signal"] in ["BUY", "SELL", "NEUTRAL"]
        assert smart_money["intensity"] >= 1 and smart_money["intensity"] <= 10
    
    @pytest.mark.asyncio
    async def test_data_validation_and_sanitization(self, server):
        """데이터 검증 및 정제 테스트"""
        # 잘못된 파라미터 테스트
        result = await server.get_investor_trading(
            stock_code="INVALID",  # 잘못된 종목코드
            investor_type="FOREIGN",
            period="1D",
            market="KOSPI"
        )
        
        # 결과 검증
        assert result["success"] == False
        assert "error" in result
        assert "validation" in result["error"]["message"].lower()
    
    @pytest.mark.asyncio
    async def test_config_integration(self, server, config):
        """설정 통합 테스트"""
        # 설정 값 확인
        assert server.config.database.url == config.database.url
        assert server.config.api.app_key == config.api.app_key
        assert server.config.cache.redis_url == config.cache.redis_url
        assert server.config.analysis.smart_money_threshold == config.analysis.smart_money_threshold
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, server, mock_api_client, mock_database):
        """동시 요청 처리 테스트"""
        # API 응답 설정
        mock_api_response = {
            "success": True,
            "data": [{"stock_code": "005930", "foreign_net_buy_amount": 1000000000}]
        }
        mock_api_client.get_investor_trading.return_value = mock_api_response
        mock_database.get_investor_trading_history.return_value = []
        
        # 동시 요청 생성
        tasks = []
        for i in range(5):
            task = server.get_investor_trading(
                stock_code="005930",
                investor_type="FOREIGN",
                period="1D",
                market="KOSPI"
            )
            tasks.append(task)
        
        # 동시 실행
        results = await asyncio.gather(*tasks)
        
        # 결과 검증
        assert len(results) == 5
        for result in results:
            assert result["success"] == True
    
    @pytest.mark.asyncio
    async def test_mcp_tool_registry(self, server):
        """MCP 도구 등록 테스트"""
        # 도구 목록 확인
        tools = server.get_available_tools()
        
        # 필수 도구 확인
        tool_names = [tool["name"] for tool in tools]
        assert "get_investor_trading" in tool_names
        assert "get_program_trading" in tool_names
        assert "analyze_smart_money" in tool_names
        assert "get_market_overview" in tool_names
        
        # 도구 스키마 확인
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert "properties" in tool["input_schema"]
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, server, mock_api_client, mock_database):
        """에러 복구 테스트"""
        # 첫 번째 호출에서 에러 발생
        mock_api_client.get_investor_trading.side_effect = [
            APIException("Temporary error"),
            {
                "success": True,
                "data": [{"stock_code": "005930", "foreign_net_buy_amount": 1000000000}]
            }
        ]
        mock_database.get_investor_trading_history.return_value = []
        
        # 첫 번째 호출 (에러 발생)
        result1 = await server.get_investor_trading(
            stock_code="005930",
            investor_type="FOREIGN",
            period="1D",
            market="KOSPI"
        )
        
        # 두 번째 호출 (성공)
        result2 = await server.get_investor_trading(
            stock_code="005930",
            investor_type="FOREIGN",
            period="1D",
            market="KOSPI"
        )
        
        # 결과 검증
        assert result1["success"] == False
        assert result2["success"] == True