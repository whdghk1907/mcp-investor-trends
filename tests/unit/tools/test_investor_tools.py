"""
TDD 테스트: 투자자 매매 도구 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any

from src.tools.investor_tools import InvestorTradingTool
from src.config import Config
from src.exceptions import APIException, ValidationException


class TestInvestorTradingTool:
    """투자자 매매 도구 테스트"""
    
    @pytest.fixture
    def config(self):
        """테스트용 설정"""
        return Config()
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock API 클라이언트"""
        api_client = MagicMock()
        api_client.get_investor_trading = AsyncMock()
        return api_client
    
    @pytest.fixture
    def mock_database(self):
        """Mock 데이터베이스"""
        database = MagicMock()
        database.get_investor_trading_history = AsyncMock()
        database.insert_investor_trading = AsyncMock()
        return database
    
    @pytest.fixture
    def mock_cache(self):
        """Mock 캐시"""
        cache = MagicMock()
        cache.get = AsyncMock()
        cache.set = AsyncMock()
        return cache
    
    @pytest.fixture
    def investor_tool(self, config, mock_api_client, mock_database, mock_cache):
        """투자자 도구 인스턴스"""
        return InvestorTradingTool(
            config=config,
            api_client=mock_api_client,
            database=mock_database,
            cache=mock_cache
        )
    
    def test_investor_tool_initialization(self, investor_tool, config):
        """투자자 도구 초기화 테스트"""
        assert investor_tool.config == config
        assert investor_tool.api_client is not None
        assert investor_tool.database is not None
        assert investor_tool.cache is not None
        assert investor_tool.logger is not None
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_single_stock(self, investor_tool, mock_api_client, mock_database, mock_cache):
        """단일 종목 투자자 거래 조회 테스트"""
        # 캐시 미스
        mock_cache.get.return_value = None
        
        # API 응답 모킹
        mock_api_response = {
            "success": True,
            "data": [{
                "stock_code": "005930",
                "foreign_net_buy_amount": 100000000000,
                "institution_net_buy_amount": 50000000000,
                "individual_net_buy_amount": -150000000000,
                "program_net_buy_amount": 10000000000,
                "timestamp": datetime.now().isoformat()
            }]
        }
        mock_api_client.get_investor_trading.return_value = mock_api_response
        
        # 데이터베이스 이력 모킹
        mock_history = [
            {
                "timestamp": datetime.now() - timedelta(hours=1),
                "foreign_net": 80000000000,
                "institution_net": 40000000000,
                "individual_net": -120000000000
            }
        ]
        mock_database.get_investor_trading_history.return_value = mock_history
        
        # 테스트 실행
        result = await investor_tool.get_investor_trading(
            stock_code="005930",
            investor_type="ALL",
            period="1D",
            include_analysis=True
        )
        
        # 결과 검증
        assert result["success"] == True
        assert result["stock_code"] == "005930"
        assert "current_data" in result
        assert "historical_data" in result
        assert "analysis" in result
        
        # 분석 결과 검증
        analysis = result["analysis"]
        assert "trend_analysis" in analysis
        assert "intensity_score" in analysis
        assert "market_impact" in analysis
        assert "smart_money_signal" in analysis
        
        # API 호출 검증
        mock_api_client.get_investor_trading.assert_called_once()
        mock_database.get_investor_trading_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_market_overview(self, investor_tool, mock_api_client, mock_database, mock_cache):
        """시장 전체 투자자 거래 개요 조회 테스트"""
        # 캐시 미스
        mock_cache.get.return_value = None
        
        # API 응답 모킹
        mock_api_response = {
            "success": True,
            "data": [{
                "market": "KOSPI",
                "foreign_net_buy_amount": 500000000000,
                "institution_net_buy_amount": -200000000000,
                "individual_net_buy_amount": -300000000000,
                "program_net_buy_amount": 50000000000
            }]
        }
        mock_api_client.get_investor_trading.return_value = mock_api_response
        mock_database.get_investor_trading_history.return_value = []
        
        # 테스트 실행
        result = await investor_tool.get_investor_trading(
            stock_code=None,
            investor_type="ALL",
            period="1D",
            market="KOSPI"
        )
        
        # 결과 검증
        assert result["success"] == True
        assert result["market"] == "KOSPI"
        assert "market_overview" in result
        assert "analysis" in result
        
        # 시장 개요 검증
        overview = result["market_overview"]
        assert overview["total_foreign_net"] == 500000000000
        assert overview["total_institution_net"] == -200000000000
        assert overview["total_individual_net"] == -300000000000
        assert overview["smart_money_net"] == 300000000000  # foreign + institution
    
    @pytest.mark.asyncio
    async def test_calculate_trend_analysis(self, investor_tool):
        """트렌드 분석 계산 테스트"""
        # 테스트 데이터
        current_data = {
            "foreign_net_buy_amount": 100000000000,
            "institution_net_buy_amount": 50000000000,
            "individual_net_buy_amount": -150000000000
        }
        
        historical_data = [
            {"timestamp": datetime.now() - timedelta(hours=5), "foreign_net": 50000000000, "institution_net": 30000000000},
            {"timestamp": datetime.now() - timedelta(hours=4), "foreign_net": 60000000000, "institution_net": 35000000000},
            {"timestamp": datetime.now() - timedelta(hours=3), "foreign_net": 70000000000, "institution_net": 40000000000},
            {"timestamp": datetime.now() - timedelta(hours=2), "foreign_net": 80000000000, "institution_net": 45000000000},
            {"timestamp": datetime.now() - timedelta(hours=1), "foreign_net": 90000000000, "institution_net": 48000000000}
        ]
        
        # 테스트 실행
        trend_analysis = investor_tool._calculate_trend_analysis(current_data, historical_data)
        
        # 결과 검증
        assert "trend_direction" in trend_analysis
        assert "trend_strength" in trend_analysis
        assert "consistency_score" in trend_analysis
        assert "momentum_score" in trend_analysis
        
        assert trend_analysis["trend_direction"] in ["ACCUMULATING", "DISTRIBUTING", "NEUTRAL"]
        assert 0 <= trend_analysis["trend_strength"] <= 10
        assert 0 <= trend_analysis["consistency_score"] <= 1
        assert 0 <= trend_analysis["momentum_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_calculate_intensity_score(self, investor_tool):
        """거래 강도 점수 계산 테스트"""
        # 테스트 데이터
        trading_data = {
            "foreign_net_buy_amount": 100000000000,
            "institution_net_buy_amount": 80000000000,
            "individual_net_buy_amount": -180000000000,
            "program_net_buy_amount": 20000000000
        }
        
        # 테스트 실행
        intensity_score = investor_tool._calculate_intensity_score(trading_data)
        
        # 결과 검증
        assert "overall_intensity" in intensity_score
        assert "foreign_intensity" in intensity_score
        assert "institution_intensity" in intensity_score
        assert "smart_money_intensity" in intensity_score
        
        assert 1 <= intensity_score["overall_intensity"] <= 10
        assert 0 <= intensity_score["foreign_intensity"] <= 10
        assert 0 <= intensity_score["institution_intensity"] <= 10
        assert 1 <= intensity_score["smart_money_intensity"] <= 10
    
    @pytest.mark.asyncio
    async def test_calculate_market_impact(self, investor_tool):
        """시장 영향도 계산 테스트"""
        # 테스트 데이터
        trading_data = {
            "foreign_net_buy_amount": 200000000000,
            "institution_net_buy_amount": 100000000000,
            "individual_net_buy_amount": -300000000000
        }
        
        # 테스트 실행
        market_impact = investor_tool._calculate_market_impact(trading_data, market="KOSPI")
        
        # 결과 검증
        assert "impact_score" in market_impact
        assert "dominance_factor" in market_impact
        assert "pressure_indicator" in market_impact
        assert "market_sentiment" in market_impact
        
        assert 0 <= market_impact["impact_score"] <= 10
        assert market_impact["market_sentiment"] in ["BULLISH", "BEARISH", "NEUTRAL"]
        assert market_impact["pressure_indicator"] in ["BUYING_PRESSURE", "SELLING_PRESSURE", "BALANCED"]
    
    @pytest.mark.asyncio
    async def test_analyze_smart_money_signals(self, investor_tool):
        """스마트 머니 신호 분석 테스트"""
        # 테스트 데이터
        current_data = {
            "foreign_net_buy_amount": 150000000000,
            "institution_net_buy_amount": 80000000000,
            "individual_net_buy_amount": -230000000000
        }
        
        historical_data = [
            {"foreign_net": 100000000000, "institution_net": 60000000000},
            {"foreign_net": 120000000000, "institution_net": 70000000000},
            {"foreign_net": 140000000000, "institution_net": 75000000000}
        ]
        
        # 테스트 실행
        smart_money_signals = investor_tool._analyze_smart_money_signals(current_data, historical_data)
        
        # 결과 검증
        assert "signal_strength" in smart_money_signals
        assert "signal_direction" in smart_money_signals
        assert "confidence_level" in smart_money_signals
        assert "institutional_flow" in smart_money_signals
        assert "foreign_flow" in smart_money_signals
        
        assert smart_money_signals["signal_direction"] in ["BUY", "SELL", "NEUTRAL"]
        assert 1 <= smart_money_signals["signal_strength"] <= 10
        assert 0 <= smart_money_signals["confidence_level"] <= 1
    
    @pytest.mark.asyncio
    async def test_cache_integration(self, investor_tool, mock_cache, mock_api_client, mock_database):
        """캐시 통합 테스트"""
        # 캐시 미스 시나리오 - None 반환
        mock_cache.get.return_value = None
        
        # API 응답 모킹
        mock_api_response = {
            "success": True,
            "data": [{
                "stock_code": "005930",
                "foreign_net_buy_amount": 100000000000,
                "institution_net_buy_amount": 50000000000,
                "individual_net_buy_amount": -150000000000,
                "timestamp": datetime.now().isoformat()
            }]
        }
        mock_api_client.get_investor_trading.return_value = mock_api_response
        mock_database.get_investor_trading_history.return_value = []
        
        # 테스트 실행
        result = await investor_tool.get_investor_trading(
            stock_code="005930",
            investor_type="ALL",
            period="1D"
        )
        
        # 결과 검증
        cache_key = "investor_trading:005930:ALL:1D:ALL"
        mock_cache.get.assert_called_once_with(cache_key)
        mock_cache.set.assert_called_once()
        assert result["success"] == True
        assert result["stock_code"] == "005930"
    
    @pytest.mark.asyncio
    async def test_error_handling_api_failure(self, investor_tool, mock_api_client, mock_cache):
        """API 실패 에러 처리 테스트"""
        # 캐시 미스
        mock_cache.get.return_value = None
        
        # API 에러 설정
        mock_api_client.get_investor_trading.side_effect = APIException("API 서버 장애")
        
        # 테스트 실행
        result = await investor_tool.get_investor_trading(
            stock_code="005930",
            investor_type="ALL",
            period="1D"
        )
        
        # 결과 검증
        assert result["success"] == False
        assert "error" in result
        assert result["error"]["type"] == "APIException"
        assert "API 서버 장애" in result["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_error_handling_validation_failure(self, investor_tool):
        """검증 실패 에러 처리 테스트"""
        # 잘못된 파라미터로 테스트
        result = await investor_tool.get_investor_trading(
            stock_code="INVALID",  # 잘못된 종목코드
            investor_type="UNKNOWN",  # 잘못된 투자자 타입
            period="INVALID"  # 잘못된 기간
        )
        
        # 결과 검증
        assert result["success"] == False
        assert "error" in result
        assert result["error"]["type"] == "ValidationException"
    
    @pytest.mark.asyncio
    async def test_multi_period_analysis(self, investor_tool, mock_api_client, mock_database, mock_cache):
        """다중 기간 분석 테스트"""
        # 캐시 미스
        mock_cache.get.return_value = None
        
        # API 응답 모킹
        mock_api_client.get_investor_trading.return_value = {
            "success": True,
            "data": [{"foreign_net_buy_amount": 100000000000}]
        }
        
        # 각 기간별 데이터베이스 응답 모킹
        periods = ["1D", "5D", "20D", "60D"]
        for period in periods:
            mock_database.get_investor_trading_history.return_value = [
                {"timestamp": datetime.now(), "foreign_net": 50000000000}
            ]
        
        # 테스트 실행
        result = await investor_tool.get_investor_trading(
            stock_code="005930",
            investor_type="ALL",
            period="ALL",  # 모든 기간 분석
            include_analysis=True
        )
        
        # 결과 검증
        assert result["success"] == True
        assert "multi_period_analysis" in result
        
        multi_period = result["multi_period_analysis"]
        for period in periods:
            assert period in multi_period
            if multi_period[period]:  # None이 아닌 경우만 검증
                assert "trend_analysis" in multi_period[period] or "intensity_score" in multi_period[period]
    
    def test_validate_parameters(self, investor_tool):
        """파라미터 검증 테스트"""
        # 유효한 파라미터
        assert investor_tool._validate_stock_code("005930") == True
        assert investor_tool._validate_stock_code(None) == True  # None 허용
        assert investor_tool._validate_investor_type("FOREIGN") == True
        assert investor_tool._validate_period("1D") == True
        assert investor_tool._validate_market("KOSPI") == True
        
        # 잘못된 파라미터
        assert investor_tool._validate_stock_code("INVALID") == False
        assert investor_tool._validate_investor_type("UNKNOWN") == False
        assert investor_tool._validate_period("INVALID") == False
        assert investor_tool._validate_market("UNKNOWN") == False
    
    @pytest.mark.asyncio
    async def test_generate_cache_key(self, investor_tool):
        """캐시 키 생성 테스트"""
        # 테스트 실행
        cache_key = investor_tool._generate_cache_key(
            stock_code="005930",
            investor_type="FOREIGN",
            period="1D",
            market="KOSPI"
        )
        
        # 결과 검증
        expected_key = "investor_trading:005930:FOREIGN:1D:KOSPI"
        assert cache_key == expected_key
        
        # None 값 처리 테스트
        cache_key_none = investor_tool._generate_cache_key(
            stock_code=None,
            investor_type="ALL",
            period="5D",
            market="ALL"
        )
        
        expected_key_none = "investor_trading:ALL:ALL:5D:ALL"
        assert cache_key_none == expected_key_none
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, investor_tool, mock_api_client, mock_database, mock_cache):
        """동시 요청 처리 테스트"""
        import asyncio
        
        # 캐시 미스
        mock_cache.get.return_value = None
        
        # API 응답 모킹
        mock_api_client.get_investor_trading.return_value = {
            "success": True,
            "data": [{"foreign_net_buy_amount": 100000000000}]
        }
        mock_database.get_investor_trading_history.return_value = []
        
        # 동시 요청 생성
        tasks = []
        stock_codes = ["005930", "000660", "035420"]
        
        for stock_code in stock_codes:
            task = investor_tool.get_investor_trading(
                stock_code=stock_code,
                investor_type="ALL",
                period="1D"
            )
            tasks.append(task)
        
        # 동시 실행
        results = await asyncio.gather(*tasks)
        
        # 결과 검증
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["success"] == True
            assert result["stock_code"] == stock_codes[i]