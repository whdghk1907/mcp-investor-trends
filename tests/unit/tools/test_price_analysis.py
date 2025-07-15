"""
TDD 테스트: 가격 상관관계 분석 도구 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any

from src.tools.price_analysis import PriceAnalysisTool
from src.config import Config
from src.exceptions import APIException, ValidationException


class TestPriceAnalysisTool:
    """가격 상관관계 분석 도구 테스트"""
    
    @pytest.fixture
    def config(self):
        """테스트용 설정"""
        return Config()
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock API 클라이언트"""
        api_client = MagicMock()
        api_client.get_stock_price = AsyncMock()
        api_client.get_investor_trading = AsyncMock()
        return api_client
    
    @pytest.fixture
    def mock_database(self):
        """Mock 데이터베이스"""
        database = MagicMock()
        database.get_price_history = AsyncMock()
        database.get_investor_trading_history = AsyncMock()
        return database
    
    @pytest.fixture
    def mock_cache(self):
        """Mock 캐시"""
        cache = MagicMock()
        cache.get = AsyncMock()
        cache.set = AsyncMock()
        return cache
    
    @pytest.fixture
    def price_analysis_tool(self, config, mock_api_client, mock_database, mock_cache):
        """가격 분석 도구 인스턴스"""
        return PriceAnalysisTool(
            config=config,
            api_client=mock_api_client,
            database=mock_database,
            cache=mock_cache
        )
    
    def test_price_analysis_tool_initialization(self, price_analysis_tool, config):
        """가격 분석 도구 초기화 테스트"""
        assert price_analysis_tool.config == config
        assert price_analysis_tool.api_client is not None
        assert price_analysis_tool.database is not None
        assert price_analysis_tool.cache is not None
        assert price_analysis_tool.logger is not None
    
    @pytest.mark.asyncio
    async def test_calculate_price_correlation(self, price_analysis_tool, mock_api_client, mock_database):
        """가격 상관관계 계산 테스트"""
        # 가격 데이터 모킹
        mock_price_data = [
            {"timestamp": datetime.now() - timedelta(hours=5), "close_price": 78000},
            {"timestamp": datetime.now() - timedelta(hours=4), "close_price": 78500},
            {"timestamp": datetime.now() - timedelta(hours=3), "close_price": 79000},
            {"timestamp": datetime.now() - timedelta(hours=2), "close_price": 79500},
            {"timestamp": datetime.now() - timedelta(hours=1), "close_price": 80000}
        ]
        mock_database.get_price_history.return_value = mock_price_data
        
        # 투자자 거래 데이터 모킹
        mock_trading_data = [
            {"timestamp": datetime.now() - timedelta(hours=5), "foreign_net": 50000000000, "institution_net": 30000000000},
            {"timestamp": datetime.now() - timedelta(hours=4), "foreign_net": 60000000000, "institution_net": 35000000000},
            {"timestamp": datetime.now() - timedelta(hours=3), "foreign_net": 70000000000, "institution_net": 40000000000},
            {"timestamp": datetime.now() - timedelta(hours=2), "foreign_net": 80000000000, "institution_net": 45000000000},
            {"timestamp": datetime.now() - timedelta(hours=1), "foreign_net": 90000000000, "institution_net": 48000000000}
        ]
        mock_database.get_investor_trading_history.return_value = mock_trading_data
        
        # 테스트 실행
        result = await price_analysis_tool.calculate_price_correlation(
            stock_code="005930",
            period="1D"
        )
        
        # 결과 검증
        assert result["success"] == True
        assert "correlation_analysis" in result
        assert "foreign_correlation" in result["correlation_analysis"]
        assert "institution_correlation" in result["correlation_analysis"]
        assert "smart_money_correlation" in result["correlation_analysis"]
        
        # 상관계수 범위 확인 (-1 ~ 1)
        correlations = result["correlation_analysis"]
        assert -1 <= correlations["foreign_correlation"] <= 1
        assert -1 <= correlations["institution_correlation"] <= 1
        assert -1 <= correlations["smart_money_correlation"] <= 1
    
    @pytest.mark.asyncio
    async def test_analyze_price_impact(self, price_analysis_tool):
        """가격 영향도 분석 테스트"""
        # 테스트 데이터
        current_price = 80000
        previous_price = 78000
        trading_data = {
            "foreign_net_buy_amount": 150000000000,
            "institution_net_buy_amount": 80000000000,
            "individual_net_buy_amount": -230000000000
        }
        
        # 테스트 실행
        impact_analysis = price_analysis_tool._analyze_price_impact(
            current_price, previous_price, trading_data
        )
        
        # 결과 검증
        assert "price_change" in impact_analysis
        assert "price_change_percent" in impact_analysis
        assert "impact_intensity" in impact_analysis
        assert "directional_consistency" in impact_analysis
        assert "predicted_direction" in impact_analysis
        
        assert impact_analysis["price_change"] == 2000  # 80000 - 78000
        assert abs(impact_analysis["price_change_percent"] - 2.56) < 0.01  # 약 2.56%
        assert 0 <= impact_analysis["impact_intensity"] <= 10
        assert impact_analysis["directional_consistency"] in ["CONSISTENT", "INCONSISTENT"]
        assert impact_analysis["predicted_direction"] in ["UP", "DOWN", "NEUTRAL"]
    
    @pytest.mark.asyncio
    async def test_calculate_volume_price_relationship(self, price_analysis_tool):
        """거래량-가격 관계 분석 테스트"""
        # 테스트 데이터
        price_data = [78000, 78500, 79000, 79500, 80000]
        volume_data = [1000000, 1200000, 1500000, 1800000, 2000000]
        
        # 테스트 실행
        relationship = price_analysis_tool._calculate_volume_price_relationship(
            price_data, volume_data
        )
        
        # 결과 검증
        assert "volume_price_correlation" in relationship
        assert "trend_confirmation" in relationship
        assert "divergence_signals" in relationship
        
        assert -1 <= relationship["volume_price_correlation"] <= 1
        assert relationship["trend_confirmation"] in ["CONFIRMED", "NOT_CONFIRMED", "WEAK"]
        assert isinstance(relationship["divergence_signals"], list)
    
    @pytest.mark.asyncio
    async def test_predict_price_movement(self, price_analysis_tool):
        """가격 움직임 예측 테스트"""
        # 테스트 데이터
        historical_data = {
            "prices": [78000, 78500, 79000, 79500, 80000],
            "foreign_flows": [50000000000, 60000000000, 70000000000, 80000000000, 90000000000],
            "institution_flows": [30000000000, 35000000000, 40000000000, 45000000000, 48000000000]
        }
        
        current_trading = {
            "foreign_net_buy_amount": 100000000000,
            "institution_net_buy_amount": 50000000000,
            "individual_net_buy_amount": -150000000000
        }
        
        # 테스트 실행
        prediction = price_analysis_tool._predict_price_movement(
            historical_data, current_trading
        )
        
        # 결과 검증
        assert "predicted_direction" in prediction
        assert "confidence_score" in prediction
        assert "support_resistance" in prediction
        assert "momentum_indicator" in prediction
        
        assert prediction["predicted_direction"] in ["BULLISH", "BEARISH", "NEUTRAL"]
        assert 0 <= prediction["confidence_score"] <= 1
        assert prediction["momentum_indicator"] in ["STRONG", "MODERATE", "WEAK"]
    
    @pytest.mark.asyncio
    async def test_analyze_market_timing(self, price_analysis_tool):
        """시장 타이밍 분석 테스트"""
        # 테스트 데이터
        trading_patterns = [
            {"hour": 9, "foreign_net": 50000000000, "price_change": 1.2},
            {"hour": 10, "foreign_net": 30000000000, "price_change": 0.8},
            {"hour": 11, "foreign_net": 70000000000, "price_change": 1.5},
            {"hour": 14, "foreign_net": -20000000000, "price_change": -0.5},
            {"hour": 15, "foreign_net": 40000000000, "price_change": 0.9}
        ]
        
        # 테스트 실행
        timing_analysis = price_analysis_tool._analyze_market_timing(trading_patterns)
        
        # 결과 검증
        assert "optimal_trading_hours" in timing_analysis
        assert "timing_efficiency" in timing_analysis
        assert "pattern_strength" in timing_analysis
        
        assert isinstance(timing_analysis["optimal_trading_hours"], list)
        assert 0 <= timing_analysis["timing_efficiency"] <= 1
        assert timing_analysis["pattern_strength"] in ["STRONG", "MODERATE", "WEAK"]
    
    @pytest.mark.asyncio
    async def test_calculate_smart_money_indicator(self, price_analysis_tool):
        """스마트 머니 지표 계산 테스트"""
        # 테스트 데이터
        price_changes = [1.2, 0.8, 1.5, -0.5, 0.9]  # 가격 변화율
        smart_money_flows = [80000000000, 65000000000, 110000000000, -50000000000, 90000000000]  # 스마트 머니 플로우
        
        # 테스트 실행
        indicator = price_analysis_tool._calculate_smart_money_indicator(
            price_changes, smart_money_flows
        )
        
        # 결과 검증
        assert "smart_money_index" in indicator
        assert "accuracy_rate" in indicator
        assert "signal_strength" in indicator
        assert "market_leadership" in indicator
        
        assert 0 <= indicator["smart_money_index"] <= 100
        assert 0 <= indicator["accuracy_rate"] <= 1
        assert 1 <= indicator["signal_strength"] <= 10
        assert indicator["market_leadership"] in ["LEADING", "LAGGING", "COINCIDENT"]
    
    @pytest.mark.asyncio
    async def test_detect_anomalies(self, price_analysis_tool):
        """이상 패턴 감지 테스트"""
        # 테스트 데이터 (이상한 패턴 포함)
        price_data = [78000, 78500, 79000, 85000, 79500]  # 급등 후 복귀
        trading_data = [
            {"foreign_net": 50000000000, "institution_net": 30000000000},
            {"foreign_net": 60000000000, "institution_net": 35000000000},
            {"foreign_net": 70000000000, "institution_net": 40000000000},
            {"foreign_net": -200000000000, "institution_net": -100000000000},  # 급매도
            {"foreign_net": 80000000000, "institution_net": 45000000000}
        ]
        
        # 테스트 실행
        anomalies = price_analysis_tool._detect_anomalies(price_data, trading_data)
        
        # 결과 검증
        assert "anomaly_detected" in anomalies
        assert "anomaly_type" in anomalies
        assert "anomaly_score" in anomalies
        assert "affected_periods" in anomalies
        
        if anomalies["anomaly_detected"]:
            assert anomalies["anomaly_type"] in ["PRICE_SPIKE", "VOLUME_SPIKE", "FLOW_REVERSAL", "PATTERN_BREAK"]
            assert 0 <= anomalies["anomaly_score"] <= 10
            assert isinstance(anomalies["affected_periods"], list)
    
    @pytest.mark.asyncio
    async def test_error_handling_insufficient_data(self, price_analysis_tool, mock_database):
        """데이터 부족 시 에러 처리 테스트"""
        # 데이터 부족 상황 모킹
        mock_database.get_price_history.return_value = []
        mock_database.get_investor_trading_history.return_value = []
        
        # 테스트 실행
        result = await price_analysis_tool.calculate_price_correlation(
            stock_code="005930",
            period="1D"
        )
        
        # 결과 검증
        assert result["success"] == False
        assert "error" in result
        assert "insufficient data" in result["error"]["message"].lower()
    
    @pytest.mark.asyncio
    async def test_cache_integration(self, price_analysis_tool, mock_cache):
        """캐시 통합 테스트"""
        # 캐시 히트 시나리오
        cached_result = {
            "success": True,
            "cached": True,
            "correlation_analysis": {
                "foreign_correlation": 0.85,
                "institution_correlation": 0.72
            }
        }
        mock_cache.get.return_value = cached_result
        
        # 테스트 실행
        result = await price_analysis_tool.calculate_price_correlation(
            stock_code="005930",
            period="1D"
        )
        
        # 결과 검증
        assert result["cached"] == True
        assert result["correlation_analysis"]["foreign_correlation"] == 0.85
        mock_cache.get.assert_called_once()
    
    def test_correlation_calculation_methods(self, price_analysis_tool):
        """상관계수 계산 메서드 테스트"""
        # 테스트 데이터
        x_data = [1, 2, 3, 4, 5]
        y_data = [2, 4, 6, 8, 10]  # 완전 양의 상관관계
        
        # 피어슨 상관계수 테스트
        pearson_corr = price_analysis_tool._calculate_pearson_correlation(x_data, y_data)
        assert abs(pearson_corr - 1.0) < 0.01  # 거의 1에 가까워야 함
        
        # 스피어만 상관계수 테스트
        spearman_corr = price_analysis_tool._calculate_spearman_correlation(x_data, y_data)
        assert abs(spearman_corr - 1.0) < 0.01  # 거의 1에 가까워야 함
        
        # 음의 상관관계 테스트
        y_negative = [10, 8, 6, 4, 2]
        pearson_neg = price_analysis_tool._calculate_pearson_correlation(x_data, y_negative)
        assert abs(pearson_neg - (-1.0)) < 0.01  # 거의 -1에 가까워야 함
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_report(self, price_analysis_tool, mock_api_client, mock_database):
        """종합 분석 보고서 생성 테스트"""
        # 모든 필요한 데이터 모킹
        mock_database.get_price_history.return_value = [
            {"timestamp": datetime.now(), "close_price": 80000, "volume": 1000000}
        ]
        mock_database.get_investor_trading_history.return_value = [
            {"timestamp": datetime.now(), "foreign_net": 100000000000, "institution_net": 50000000000}
        ]
        
        # 테스트 실행
        result = await price_analysis_tool.generate_comprehensive_analysis(
            stock_code="005930",
            period="1D"
        )
        
        # 결과 검증
        assert result["success"] == True
        assert "correlation_analysis" in result
        assert "price_impact_analysis" in result
        assert "prediction_analysis" in result
        assert "timing_analysis" in result
        assert "anomaly_detection" in result
        assert "smart_money_indicator" in result
        
        # 보고서 요약 확인
        assert "summary" in result
        assert "key_insights" in result["summary"]
        assert "recommendation" in result["summary"]