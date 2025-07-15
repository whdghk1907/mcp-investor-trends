"""
TDD 테스트: 데이터 모델 테스트
"""
import pytest
from datetime import datetime
from decimal import Decimal
from src.api.models import (
    InvestorData, StockInfo, InvestorTradingData, 
    SmartMoneySignal, ProgramTradingData
)


class TestInvestorData:
    """투자자 데이터 모델 테스트"""
    
    def test_investor_data_creation(self):
        """투자자 데이터 생성 테스트"""
        data = InvestorData(
            buy_amount=1000000000,
            sell_amount=800000000,
            net_amount=200000000,
            buy_volume=100000,
            sell_volume=80000,
            net_volume=20000,
            average_buy_price=10000.0,
            average_sell_price=10000.0,
            net_ratio=55.5,
            trend="ACCUMULATING",
            intensity=7.5
        )
        
        assert data.buy_amount == 1000000000
        assert data.sell_amount == 800000000
        assert data.net_amount == 200000000
        assert data.buy_volume == 100000
        assert data.sell_volume == 80000
        assert data.net_volume == 20000
        assert data.average_buy_price == 10000.0
        assert data.average_sell_price == 10000.0
        assert data.net_ratio == 55.5
        assert data.trend == "ACCUMULATING"
        assert data.intensity == 7.5
    
    def test_investor_data_validation(self):
        """투자자 데이터 유효성 검증 테스트"""
        data = InvestorData(
            buy_amount=1000000000,
            sell_amount=800000000,
            net_amount=200000000,
            buy_volume=100000,
            sell_volume=80000,
            net_volume=20000,
            average_buy_price=10000.0,
            average_sell_price=10000.0,
            net_ratio=55.5,
            trend="ACCUMULATING",
            intensity=7.5
        )
        
        assert data.is_valid()
        assert data.get_net_amount() == 200000000
        assert data.get_trading_intensity() == 7.5
        assert data.is_accumulating() == True
        assert data.is_distributing() == False
    
    def test_investor_data_trend_validation(self):
        """투자자 데이터 트렌드 검증 테스트"""
        valid_trends = ["ACCUMULATING", "DISTRIBUTING", "NEUTRAL"]
        
        for trend in valid_trends:
            data = InvestorData(
                buy_amount=1000000000,
                sell_amount=800000000,
                net_amount=200000000,
                buy_volume=100000,
                sell_volume=80000,
                net_volume=20000,
                average_buy_price=10000.0,
                average_sell_price=10000.0,
                net_ratio=55.5,
                trend=trend,
                intensity=7.5
            )
            assert data.is_valid_trend()
    
    def test_investor_data_invalid_trend(self):
        """잘못된 트렌드 테스트"""
        with pytest.raises(ValueError, match="Invalid trend"):
            InvestorData(
                buy_amount=1000000000,
                sell_amount=800000000,
                net_amount=200000000,
                buy_volume=100000,
                sell_volume=80000,
                net_volume=20000,
                average_buy_price=10000.0,
                average_sell_price=10000.0,
                net_ratio=55.5,
                trend="INVALID_TREND",
                intensity=7.5
            )
    
    def test_investor_data_intensity_range(self):
        """투자자 데이터 강도 범위 테스트"""
        # 유효한 강도 범위 (1-10)
        valid_data = InvestorData(
            buy_amount=1000000000,
            sell_amount=800000000,
            net_amount=200000000,
            buy_volume=100000,
            sell_volume=80000,
            net_volume=20000,
            average_buy_price=10000.0,
            average_sell_price=10000.0,
            net_ratio=55.5,
            trend="ACCUMULATING",
            intensity=5.0
        )
        assert valid_data.is_valid_intensity()
        
        # 잘못된 강도 범위
        with pytest.raises(ValueError, match="Intensity must be between 1 and 10"):
            InvestorData(
                buy_amount=1000000000,
                sell_amount=800000000,
                net_amount=200000000,
                buy_volume=100000,
                sell_volume=80000,
                net_volume=20000,
                average_buy_price=10000.0,
                average_sell_price=10000.0,
                net_ratio=55.5,
                trend="ACCUMULATING",
                intensity=15.0  # 잘못된 범위
            )


class TestStockInfo:
    """종목 정보 모델 테스트"""
    
    def test_stock_info_creation(self):
        """종목 정보 생성 테스트"""
        stock = StockInfo(
            code="005930",
            name="삼성전자",
            current_price=78500,
            change_rate=1.55,
            market_cap=468923450000000,
            sector="기술"
        )
        
        assert stock.code == "005930"
        assert stock.name == "삼성전자"
        assert stock.current_price == 78500
        assert stock.change_rate == 1.55
        assert stock.market_cap == 468923450000000
        assert stock.sector == "기술"
    
    def test_stock_info_validation(self):
        """종목 정보 유효성 검증"""
        stock = StockInfo(
            code="005930",
            name="삼성전자",
            current_price=78500,
            change_rate=1.55
        )
        
        assert stock.is_valid()
        assert stock.get_market_cap_in_trillion() == 0.0  # None인 경우
        assert stock.is_positive_change() == True
        assert stock.is_negative_change() == False
    
    def test_stock_info_invalid_code(self):
        """잘못된 종목코드 테스트"""
        with pytest.raises(ValueError, match="Invalid stock code"):
            StockInfo(
                code="INVALID",
                name="삼성전자",
                current_price=78500,
                change_rate=1.55
            )
    
    def test_stock_info_market_cap_conversion(self):
        """시가총액 변환 테스트"""
        stock = StockInfo(
            code="005930",
            name="삼성전자",
            current_price=78500,
            change_rate=1.55,
            market_cap=468923450000000
        )
        
        # 조 단위 변환
        assert stock.get_market_cap_in_trillion() == 468.9
        
        # 억 단위 변환
        assert stock.get_market_cap_in_billion() == 4689234.5


class TestInvestorTradingData:
    """투자자 매매 데이터 모델 테스트"""
    
    def test_investor_trading_data_creation(self):
        """투자자 매매 데이터 생성 테스트"""
        stock_info = StockInfo(
            code="005930",
            name="삼성전자",
            current_price=78500,
            change_rate=1.55
        )
        
        foreign_data = InvestorData(
            buy_amount=1000000000,
            sell_amount=800000000,
            net_amount=200000000,
            buy_volume=100000,
            sell_volume=80000,
            net_volume=20000,
            average_buy_price=10000.0,
            average_sell_price=10000.0,
            net_ratio=55.5,
            trend="ACCUMULATING",
            intensity=7.5
        )
        
        institution_data = InvestorData(
            buy_amount=500000000,
            sell_amount=600000000,
            net_amount=-100000000,
            buy_volume=50000,
            sell_volume=60000,
            net_volume=-10000,
            average_buy_price=10000.0,
            average_sell_price=10000.0,
            net_ratio=45.5,
            trend="DISTRIBUTING",
            intensity=6.0
        )
        
        individual_data = InvestorData(
            buy_amount=300000000,
            sell_amount=400000000,
            net_amount=-100000000,
            buy_volume=30000,
            sell_volume=40000,
            net_volume=-10000,
            average_buy_price=10000.0,
            average_sell_price=10000.0,
            net_ratio=42.9,
            trend="DISTRIBUTING",
            intensity=5.0
        )
        
        trading_data = InvestorTradingData(
            timestamp=datetime.now(),
            scope="STOCK",
            stock_info=stock_info,
            foreign=foreign_data,
            institution=institution_data,
            individual=individual_data,
            program={"buy": 100000000, "sell": 80000000},
            market_impact={"correlation": 0.75}
        )
        
        assert trading_data.scope == "STOCK"
        assert trading_data.stock_info.code == "005930"
        assert trading_data.foreign.net_amount == 200000000
        assert trading_data.institution.net_amount == -100000000
        assert trading_data.individual.net_amount == -100000000
    
    def test_investor_trading_data_validation(self):
        """투자자 매매 데이터 유효성 검증"""
        stock_info = StockInfo(
            code="005930",
            name="삼성전자",
            current_price=78500,
            change_rate=1.55
        )
        
        foreign_data = InvestorData(
            buy_amount=1000000000,
            sell_amount=800000000,
            net_amount=200000000,
            buy_volume=100000,
            sell_volume=80000,
            net_volume=20000,
            average_buy_price=10000.0,
            average_sell_price=10000.0,
            net_ratio=55.5,
            trend="ACCUMULATING",
            intensity=7.5
        )
        
        institution_data = InvestorData(
            buy_amount=500000000,
            sell_amount=600000000,
            net_amount=-100000000,
            buy_volume=50000,
            sell_volume=60000,
            net_volume=-10000,
            average_buy_price=10000.0,
            average_sell_price=10000.0,
            net_ratio=45.5,
            trend="DISTRIBUTING",
            intensity=6.0
        )
        
        individual_data = InvestorData(
            buy_amount=300000000,
            sell_amount=400000000,
            net_amount=-100000000,
            buy_volume=30000,
            sell_volume=40000,
            net_volume=-10000,
            average_buy_price=10000.0,
            average_sell_price=10000.0,
            net_ratio=42.9,
            trend="DISTRIBUTING",
            intensity=5.0
        )
        
        trading_data = InvestorTradingData(
            timestamp=datetime.now(),
            scope="STOCK",
            stock_info=stock_info,
            foreign=foreign_data,
            institution=institution_data,
            individual=individual_data,
            program={"buy": 100000000, "sell": 80000000},
            market_impact={"correlation": 0.75}
        )
        
        assert trading_data.is_valid()
        assert trading_data.get_total_net_amount() == 0  # 균형 확인
        assert trading_data.get_dominant_investor() == "FOREIGN"
        assert trading_data.has_market_impact() == True


class TestSmartMoneySignal:
    """스마트머니 신호 모델 테스트"""
    
    def test_smart_money_signal_creation(self):
        """스마트머니 신호 생성 테스트"""
        signal = SmartMoneySignal(
            stock_code="005930",
            stock_name="삼성전자",
            signal_type="INSTITUTIONAL_ACCUMULATION",
            confidence=8.5,
            detection_details={"method": "large_orders"},
            metrics={"amount": 1000000000},
            technical_context={"support": 77000},
            timestamp=datetime.now()
        )
        
        assert signal.stock_code == "005930"
        assert signal.stock_name == "삼성전자"
        assert signal.signal_type == "INSTITUTIONAL_ACCUMULATION"
        assert signal.confidence == 8.5
        assert signal.detection_details == {"method": "large_orders"}
        assert signal.metrics == {"amount": 1000000000}
        assert signal.technical_context == {"support": 77000}
    
    def test_smart_money_signal_validation(self):
        """스마트머니 신호 유효성 검증"""
        signal = SmartMoneySignal(
            stock_code="005930",
            stock_name="삼성전자",
            signal_type="INSTITUTIONAL_ACCUMULATION",
            confidence=8.5,
            detection_details={"method": "large_orders"},
            metrics={"amount": 1000000000},
            technical_context={"support": 77000},
            timestamp=datetime.now()
        )
        
        assert signal.is_valid()
        assert signal.is_high_confidence() == True
        assert signal.is_low_confidence() == False
        assert signal.get_signal_strength() == "HIGH"
    
    def test_smart_money_signal_confidence_validation(self):
        """스마트머니 신호 신뢰도 검증"""
        # 유효한 신뢰도 범위 (0-10)
        valid_signal = SmartMoneySignal(
            stock_code="005930",
            stock_name="삼성전자",
            signal_type="INSTITUTIONAL_ACCUMULATION",
            confidence=8.5,
            detection_details={},
            metrics={},
            technical_context={},
            timestamp=datetime.now()
        )
        assert valid_signal.is_valid_confidence()
        
        # 잘못된 신뢰도 범위
        with pytest.raises(ValueError, match="Confidence must be between 0 and 10"):
            SmartMoneySignal(
                stock_code="005930",
                stock_name="삼성전자",
                signal_type="INSTITUTIONAL_ACCUMULATION",
                confidence=15.0,  # 잘못된 범위
                detection_details={},
                metrics={},
                technical_context={},
                timestamp=datetime.now()
            )


class TestProgramTradingData:
    """프로그램 매매 데이터 모델 테스트"""
    
    def test_program_trading_data_creation(self):
        """프로그램 매매 데이터 생성 테스트"""
        program_data = ProgramTradingData(
            timestamp=datetime.now(),
            market="KOSPI",
            total_buy=500000000,
            total_sell=400000000,
            net_value=100000000,
            arbitrage_data={"buy": 200000000, "sell": 180000000},
            non_arbitrage_data={"buy": 300000000, "sell": 220000000},
            market_indicators={"participation_rate": 15.5}
        )
        
        assert program_data.market == "KOSPI"
        assert program_data.total_buy == 500000000
        assert program_data.total_sell == 400000000
        assert program_data.net_value == 100000000
        assert program_data.arbitrage_data == {"buy": 200000000, "sell": 180000000}
        assert program_data.non_arbitrage_data == {"buy": 300000000, "sell": 220000000}
        assert program_data.market_indicators == {"participation_rate": 15.5}
    
    def test_program_trading_data_validation(self):
        """프로그램 매매 데이터 유효성 검증"""
        program_data = ProgramTradingData(
            timestamp=datetime.now(),
            market="KOSPI",
            total_buy=500000000,
            total_sell=400000000,
            net_value=100000000,
            arbitrage_data={"buy": 200000000, "sell": 180000000},
            non_arbitrage_data={"buy": 300000000, "sell": 220000000},
            market_indicators={"participation_rate": 15.5}
        )
        
        assert program_data.is_valid()
        assert program_data.get_buy_ratio() == 55.6  # 500/(500+400)*100
        assert program_data.is_net_buying() == True
        assert program_data.is_net_selling() == False
        assert program_data.get_trading_intensity() == "MEDIUM"
    
    def test_program_trading_data_calculations(self):
        """프로그램 매매 데이터 계산 테스트"""
        program_data = ProgramTradingData(
            timestamp=datetime.now(),
            market="KOSPI",
            total_buy=500000000,
            total_sell=400000000,
            net_value=100000000,
            arbitrage_data={"buy": 200000000, "sell": 180000000},
            non_arbitrage_data={"buy": 300000000, "sell": 220000000},
            market_indicators={"participation_rate": 15.5}
        )
        
        # 매수 비율 계산 (소수점 1자리까지)
        expected_buy_ratio = round(500000000 / (500000000 + 400000000) * 100, 1)
        assert program_data.get_buy_ratio() == expected_buy_ratio
        
        # 순매수 금액 확인
        assert program_data.get_net_value() == 100000000
        
        # 거래 강도 분류
        assert program_data.get_trading_intensity() in ["LOW", "MEDIUM", "HIGH"]