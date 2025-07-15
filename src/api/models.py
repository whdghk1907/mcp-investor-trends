"""
투자자 동향 데이터 모델 정의
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List, Any
import re


@dataclass
class InvestorData:
    """투자자 데이터 모델"""
    buy_amount: int
    sell_amount: int
    net_amount: int
    buy_volume: int
    sell_volume: int
    net_volume: int
    average_buy_price: float
    average_sell_price: float
    net_ratio: float
    trend: str  # ACCUMULATING, DISTRIBUTING, NEUTRAL
    intensity: float  # 1-10
    
    def __post_init__(self):
        """초기화 후 유효성 검증"""
        if not self.is_valid_trend():
            raise ValueError(f"Invalid trend: {self.trend}")
        if not self.is_valid_intensity():
            raise ValueError(f"Intensity must be between 1 and 10: {self.intensity}")
    
    def is_valid(self) -> bool:
        """데이터 유효성 검증"""
        return (
            self.buy_amount >= 0 and
            self.sell_amount >= 0 and
            self.buy_volume >= 0 and
            self.sell_volume >= 0 and
            self.is_valid_trend() and
            self.is_valid_intensity()
        )
    
    def is_valid_trend(self) -> bool:
        """트렌드 유효성 검증"""
        valid_trends = ["ACCUMULATING", "DISTRIBUTING", "NEUTRAL"]
        return self.trend in valid_trends
    
    def is_valid_intensity(self) -> bool:
        """강도 유효성 검증"""
        return 1.0 <= self.intensity <= 10.0
    
    def get_net_amount(self) -> int:
        """순매수 금액 반환"""
        return self.net_amount
    
    def get_trading_intensity(self) -> float:
        """거래 강도 반환"""
        return self.intensity
    
    def is_accumulating(self) -> bool:
        """매집 중인지 확인"""
        return self.trend == "ACCUMULATING"
    
    def is_distributing(self) -> bool:
        """분산 중인지 확인"""
        return self.trend == "DISTRIBUTING"


@dataclass
class StockInfo:
    """종목 정보 모델"""
    code: str
    name: str
    current_price: int
    change_rate: float
    market_cap: Optional[int] = None
    sector: Optional[str] = None
    
    def __post_init__(self):
        """초기화 후 유효성 검증"""
        if not self.is_valid_code():
            raise ValueError(f"Invalid stock code: {self.code}")
    
    def is_valid(self) -> bool:
        """종목 정보 유효성 검증"""
        return (
            self.is_valid_code() and
            self.current_price > 0 and
            len(self.name) > 0
        )
    
    def is_valid_code(self) -> bool:
        """종목 코드 유효성 검증 (6자리 숫자)"""
        return bool(re.match(r'^\d{6}$', self.code))
    
    def get_market_cap_in_trillion(self) -> float:
        """시가총액을 조 단위로 반환"""
        if self.market_cap is None:
            return 0.0
        return round(self.market_cap / 1_000_000_000_000, 1)
    
    def get_market_cap_in_billion(self) -> float:
        """시가총액을 억 단위로 반환"""
        if self.market_cap is None:
            return 0.0
        return round(self.market_cap / 100_000_000, 1)
    
    def is_positive_change(self) -> bool:
        """상승 중인지 확인"""
        return self.change_rate > 0
    
    def is_negative_change(self) -> bool:
        """하락 중인지 확인"""
        return self.change_rate < 0


@dataclass
class InvestorTradingData:
    """투자자 매매 데이터 종합 모델"""
    timestamp: datetime
    scope: str  # MARKET, STOCK
    stock_info: Optional[StockInfo]
    foreign: InvestorData
    institution: InvestorData
    individual: InvestorData
    program: Dict[str, Any]
    market_impact: Dict[str, float]
    
    def is_valid(self) -> bool:
        """데이터 유효성 검증"""
        return (
            self.scope in ["MARKET", "STOCK"] and
            self.foreign.is_valid() and
            self.institution.is_valid() and
            self.individual.is_valid() and
            (self.stock_info is None or self.stock_info.is_valid())
        )
    
    def get_total_net_amount(self) -> int:
        """전체 순매수 금액 (균형 확인용)"""
        return (
            self.foreign.net_amount + 
            self.institution.net_amount + 
            self.individual.net_amount
        )
    
    def get_dominant_investor(self) -> str:
        """지배적인 투자자 유형 반환"""
        net_amounts = {
            "FOREIGN": abs(self.foreign.net_amount),
            "INSTITUTION": abs(self.institution.net_amount),
            "INDIVIDUAL": abs(self.individual.net_amount)
        }
        return max(net_amounts, key=net_amounts.get)
    
    def has_market_impact(self) -> bool:
        """시장 영향이 있는지 확인"""
        return self.market_impact.get("correlation", 0) > 0.5


@dataclass
class SmartMoneySignal:
    """스마트머니 신호 모델"""
    stock_code: str
    stock_name: str
    signal_type: str
    confidence: float
    detection_details: Dict[str, Any]
    metrics: Dict[str, Any]
    technical_context: Dict[str, Any]
    timestamp: datetime
    
    def __post_init__(self):
        """초기화 후 유효성 검증"""
        if not self.is_valid_confidence():
            raise ValueError(f"Confidence must be between 0 and 10: {self.confidence}")
    
    def is_valid(self) -> bool:
        """신호 유효성 검증"""
        return (
            len(self.stock_code) == 6 and
            len(self.stock_name) > 0 and
            self.is_valid_confidence() and
            isinstance(self.detection_details, dict) and
            isinstance(self.metrics, dict) and
            isinstance(self.technical_context, dict)
        )
    
    def is_valid_confidence(self) -> bool:
        """신뢰도 유효성 검증"""
        return 0.0 <= self.confidence <= 10.0
    
    def is_high_confidence(self) -> bool:
        """높은 신뢰도인지 확인"""
        return self.confidence >= 8.0
    
    def is_low_confidence(self) -> bool:
        """낮은 신뢰도인지 확인"""
        return self.confidence < 5.0
    
    def get_signal_strength(self) -> str:
        """신호 강도 반환"""
        if self.confidence >= 8.0:
            return "HIGH"
        elif self.confidence >= 6.0:
            return "MEDIUM"
        else:
            return "LOW"


@dataclass
class ProgramTradingData:
    """프로그램 매매 데이터 모델"""
    timestamp: datetime
    market: str
    total_buy: int
    total_sell: int
    net_value: int
    arbitrage_data: Dict[str, Any]
    non_arbitrage_data: Dict[str, Any]
    market_indicators: Dict[str, float]
    
    def is_valid(self) -> bool:
        """데이터 유효성 검증"""
        return (
            self.market in ["KOSPI", "KOSDAQ", "ALL"] and
            self.total_buy >= 0 and
            self.total_sell >= 0 and
            isinstance(self.arbitrage_data, dict) and
            isinstance(self.non_arbitrage_data, dict) and
            isinstance(self.market_indicators, dict)
        )
    
    def get_buy_ratio(self) -> float:
        """매수 비율 계산"""
        total_trading = self.total_buy + self.total_sell
        if total_trading == 0:
            return 50.0
        return round((self.total_buy / total_trading) * 100, 1)
    
    def get_net_value(self) -> int:
        """순매수 금액 반환"""
        return self.net_value
    
    def is_net_buying(self) -> bool:
        """순매수인지 확인"""
        return self.net_value > 0
    
    def is_net_selling(self) -> bool:
        """순매도인지 확인"""
        return self.net_value < 0
    
    def get_trading_intensity(self) -> str:
        """거래 강도 분류"""
        total_trading = self.total_buy + self.total_sell
        
        if total_trading < 100_000_000:  # 1억 미만
            return "LOW"
        elif total_trading < 1_000_000_000:  # 10억 미만
            return "MEDIUM"
        else:
            return "HIGH"