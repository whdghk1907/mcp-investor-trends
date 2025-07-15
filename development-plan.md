# 🏦 투자자 동향 MCP 서버 개발 계획서

## 1. 프로젝트 개요

### 1.1 목적
한국 주식시장의 투자자별(외국인/기관/개인) 매매 동향을 실시간으로 추적하고 분석하는 MCP 서버 구축

### 1.2 범위
- 투자자별 순매수/매도 동향
- 프로그램 매매 분석
- 투자자별 보유 비중 추적
- 업종별 투자자 동향
- 시간대별 매매 패턴 분석
- 투자 주체별 선호 종목 분석
- 스마트머니 추적

### 1.3 기술 스택
- **언어**: Python 3.11+
- **MCP SDK**: mcp-python
- **API Client**: 한국투자증권 OpenAPI, 이베스트투자증권 xingAPI
- **비동기 처리**: asyncio, aiohttp
- **데이터 분석**: pandas, numpy
- **시계열 분석**: statsmodels
- **캐싱**: Redis + 메모리 캐시
- **데이터베이스**: PostgreSQL + TimescaleDB

## 2. 서버 아키텍처

```
mcp-investor-trends/
├── src/
│   ├── server.py                    # MCP 서버 메인
│   ├── tools/                       # MCP 도구 정의
│   │   ├── __init__.py
│   │   ├── investor_tools.py       # 투자자 동향 도구
│   │   ├── program_tools.py        # 프로그램 매매 도구
│   │   ├── ownership_tools.py      # 보유 비중 도구
│   │   └── analysis_tools.py       # 분석 도구
│   ├── api/
│   │   ├── __init__.py
│   │   ├── korea_investment.py     # 한투 API
│   │   ├── ebest.py                # 이베스트 API
│   │   ├── models.py               # 데이터 모델
│   │   └── constants.py            # 상수 정의
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── investor_analyzer.py    # 투자자 분석
│   │   ├── flow_analyzer.py        # 자금 흐름 분석
│   │   ├── pattern_detector.py     # 패턴 감지
│   │   └── smart_money.py          # 스마트머니 추적
│   ├── utils/
│   │   ├── cache.py                # 캐시 관리
│   │   ├── database.py             # DB 연결
│   │   ├── calculator.py           # 계산 유틸
│   │   └── formatter.py            # 포맷팅
│   ├── config.py                   # 설정 관리
│   └── exceptions.py               # 예외 정의
├── tests/
│   ├── test_tools.py
│   ├── test_analyzer.py
│   └── test_integration.py
├── requirements.txt
├── .env.example
└── README.md
```

## 3. 핵심 기능 명세

### 3.1 제공 도구 (Tools)

#### 1) `get_investor_trading`
```python
@tool
async def get_investor_trading(
    stock_code: Optional[str] = None,
    investor_type: Literal["FOREIGN", "INSTITUTION", "INDIVIDUAL", "ALL"] = "ALL",
    period: Literal["1D", "5D", "20D", "60D"] = "1D",
    market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
    include_details: bool = True
) -> dict:
    """
    투자자별 매매 동향 조회
    
    Parameters:
        stock_code: 특정 종목 코드 (None이면 시장 전체)
        investor_type: 투자자 유형
        period: 조회 기간
        market: 시장 구분
        include_details: 상세 정보 포함 여부
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "scope": "MARKET" or "STOCK",
            "stock_info": {  # stock_code가 있을 때만
                "code": "005930",
                "name": "삼성전자",
                "current_price": 78500,
                "change_rate": 1.55
            },
            "investor_data": {
                "foreign": {
                    "buy_amount": 523456789000,
                    "sell_amount": 234567890000,
                    "net_amount": 288888899000,
                    "buy_volume": 6678900,
                    "sell_volume": 2987650,
                    "net_volume": 3691250,
                    "average_buy_price": 78350,
                    "average_sell_price": 78520,
                    "net_ratio": 55.2,  # 순매수 비율
                    "trend": "ACCUMULATING",  # 매집/분산
                    "intensity": 8.5  # 매매 강도 (1-10)
                },
                "institution": {
                    "buy_amount": 345678900000,
                    "sell_amount": 456789000000,
                    "net_amount": -111110100000,
                    "sub_categories": {  # 기관 세부
                        "investment_trust": 23456789000,
                        "pension_fund": -34567890000,
                        "insurance": 12345678000,
                        "private_fund": -45678900000,
                        "bank": 23456789000,
                        "other": -12345678000
                    }
                },
                "individual": {...},
                "program": {
                    "total_buy": 123456789000,
                    "total_sell": 98765432000,
                    "arbitrage_buy": 45678900000,
                    "arbitrage_sell": 34567890000,
                    "non_arbitrage_buy": 77777889000,
                    "non_arbitrage_sell": 64197542000
                }
            },
            "market_impact": {
                "price_correlation": 0.75,  # 가격과의 상관관계
                "volume_contribution": 23.5,  # 거래량 기여도
                "momentum_score": 7.2
            },
            "historical_comparison": {
                "vs_yesterday": {
                    "foreign_net_change": 156789000000,
                    "institution_net_change": -98765432000
                },
                "vs_week_ago": {...},
                "vs_month_ago": {...}
            }
        }
    """
```

#### 2) `get_ownership_changes`
```python
@tool
async def get_ownership_changes(
    stock_code: str,
    investor_type: Literal["FOREIGN", "INSTITUTION", "ALL"] = "ALL",
    period: Literal["1M", "3M", "6M", "1Y"] = "3M",
    threshold: Optional[float] = 1.0  # 최소 변화율
) -> dict:
    """
    투자자별 보유 비중 변화 추적
    
    Parameters:
        stock_code: 종목 코드
        investor_type: 투자자 유형
        period: 추적 기간
        threshold: 최소 변화율 필터
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "stock_info": {
                "code": "005930",
                "name": "삼성전자",
                "market_cap": 468923450000000
            },
            "ownership_data": {
                "current": {
                    "foreign": {
                        "shares": 3123456789,
                        "percentage": 52.34,
                        "value": 245234567890000
                    },
                    "institution": {
                        "shares": 1234567890,
                        "percentage": 20.67,
                        "value": 96987654321000,
                        "breakdown": {
                            "national_pension": 8.5,
                            "investment_trust": 5.2,
                            "insurance": 3.1,
                            "other": 3.87
                        }
                    },
                    "individual": {
                        "shares": 1598765432,
                        "percentage": 26.78,
                        "value": 125543210987000
                    },
                    "treasury": {
                        "shares": 12345678,
                        "percentage": 0.21
                    }
                },
                "changes": {
                    "foreign": {
                        "shares_change": 234567890,
                        "percentage_change": 2.34,
                        "value_change": 18423456789000,
                        "trend": "INCREASING",
                        "consecutive_days": 15
                    },
                    "institution": {...}
                },
                "historical": [
                    {
                        "date": "2024-01-01",
                        "foreign": 50.0,
                        "institution": 22.5,
                        "individual": 27.3
                    },
                    ...
                ],
                "milestones": [
                    {
                        "date": "2023-11-15",
                        "event": "외국인 지분 50% 돌파",
                        "foreign_ownership": 50.12
                    }
                ]
            },
            "correlation_analysis": {
                "price_vs_foreign_ownership": 0.82,
                "volatility_vs_ownership_change": -0.45,
                "ownership_concentration": 0.73  # 허핀달 지수
            }
        }
    """
```

#### 3) `get_program_trading`
```python
@tool
async def get_program_trading(
    market: Literal["KOSPI", "KOSDAQ", "ALL"] = "ALL",
    program_type: Literal["ALL", "ARBITRAGE", "NON_ARBITRAGE"] = "ALL",
    time_window: Literal["CURRENT", "1H", "TODAY"] = "CURRENT"
) -> dict:
    """
    프로그램 매매 동향 조회
    
    Parameters:
        market: 시장 구분
        program_type: 프로그램 유형
        time_window: 시간 범위
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "market": "ALL",
            "program_trading": {
                "summary": {
                    "total_buy": 234567890000,
                    "total_sell": 198765432000,
                    "net_value": 35802458000,
                    "buy_ratio": 54.1,  # 매수 비중
                    "market_impact": 12.3  # 시장 영향도
                },
                "arbitrage": {
                    "buy": 123456789000,
                    "sell": 98765432000,
                    "net": 24691357000,
                    "basis": 2.5,  # 베이시스
                    "futures_position": "LONG",
                    "intensity": "HIGH"
                },
                "non_arbitrage": {
                    "buy": 111111101000,
                    "sell": 100000000000,
                    "net": 11111101000,
                    "strategy_breakdown": {
                        "index_tracking": 45678900000,
                        "etf_hedging": 34567890000,
                        "portfolio_rebalancing": 30864311000
                    }
                },
                "time_series": [
                    {
                        "time": "09:00",
                        "buy": 23456789000,
                        "sell": 19876543000,
                        "net": 3580246000,
                        "cumulative_net": 3580246000
                    },
                    ...
                ],
                "top_stocks": [
                    {
                        "code": "005930",
                        "name": "삼성전자",
                        "program_buy": 34567890000,
                        "program_sell": 23456789000,
                        "net": 11111101000,
                        "ratio": 15.2  # 전체 프로그램 매매 중 비중
                    },
                    ...
                ],
                "market_indicators": {
                    "program_participation_rate": 18.5,
                    "arbitrage_opportunity": "MODERATE",
                    "market_efficiency": 0.85
                }
            }
        }
    """
```

#### 4) `get_sector_investor_flow`
```python
@tool
async def get_sector_investor_flow(
    sector: Optional[str] = None,
    investor_type: Literal["FOREIGN", "INSTITUTION", "ALL"] = "ALL",
    period: Literal["1D", "5D", "20D"] = "5D",
    top_n: int = 10
) -> dict:
    """
    업종별 투자자 자금 흐름 분석
    
    Parameters:
        sector: 특정 업종 (None이면 전체)
        investor_type: 투자자 유형
        period: 분석 기간
        top_n: 상위 N개 업종
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "period": "5D",
            "sector_flows": [
                {
                    "sector_code": "G2510",
                    "sector_name": "반도체",
                    "foreign": {
                        "net_amount": 1234567890000,
                        "buy_amount": 2345678900000,
                        "sell_amount": 1111111010000,
                        "net_ratio": 52.7,
                        "concentration": 0.75,  # 특정 종목 집중도
                        "top_stocks": [
                            {
                                "code": "005930",
                                "name": "삼성전자",
                                "net_amount": 987654321000,
                                "contribution": 80.0
                            },
                            ...
                        ]
                    },
                    "institution": {...},
                    "momentum": {
                        "score": 8.5,
                        "trend": "STRONG_BUY",
                        "consistency": 0.9  # 일관성
                    },
                    "sector_performance": {
                        "return": 5.67,
                        "vs_market": 3.21,
                        "correlation_with_flow": 0.78
                    }
                },
                ...
            ],
            "rotation_analysis": {
                "from_sectors": [
                    {"name": "은행", "outflow": -234567890000}
                ],
                "to_sectors": [
                    {"name": "반도체", "inflow": 345678900000}
                ],
                "rotation_strength": 7.5,
                "cycle_phase": "EARLY_CYCLE"
            },
            "market_overview": {
                "total_foreign_net": 2345678900000,
                "total_institution_net": -1234567890000,
                "sector_dispersion": 0.34,
                "concentration_risk": "MODERATE"
            }
        }
    """
```

#### 5) `get_time_based_flow`
```python
@tool
async def get_time_based_flow(
    stock_code: Optional[str] = None,
    interval: Literal["1M", "5M", "10M", "30M", "1H"] = "10M",
    session: Literal["ALL", "MORNING", "AFTERNOON"] = "ALL"
) -> dict:
    """
    시간대별 투자자 매매 패턴 분석
    
    Parameters:
        stock_code: 종목 코드 (None이면 시장 전체)
        interval: 시간 간격
        session: 장 시간 구분
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "analysis_scope": "STOCK" or "MARKET",
            "time_flow_data": [
                {
                    "time": "09:00",
                    "foreign": {
                        "buy": 123456789,
                        "sell": 98765432,
                        "net": 24691357,
                        "avg_price": 78450,
                        "intensity": 7.5
                    },
                    "institution": {...},
                    "individual": {...},
                    "price_impact": {
                        "open": 78000,
                        "close": 78500,
                        "change": 0.64,
                        "correlation": 0.82
                    }
                },
                ...
            ],
            "patterns": {
                "foreign": {
                    "typical_entry_time": "09:30-10:00",
                    "typical_exit_time": "14:30-15:00",
                    "morning_bias": "BUY",
                    "afternoon_bias": "NEUTRAL",
                    "consistency_score": 7.8
                },
                "institution": {
                    "batch_trading_times": ["09:00", "13:00", "14:50"],
                    "average_order_size": 234567890,
                    "execution_pattern": "VWAP"
                }
            },
            "anomalies": [
                {
                    "time": "10:30",
                    "type": "UNUSUAL_VOLUME",
                    "investor": "FOREIGN",
                    "magnitude": 345678900,
                    "z_score": 3.2
                }
            ],
            "optimal_trading_windows": {
                "low_impact": ["11:00-11:30", "13:30-14:00"],
                "high_liquidity": ["09:30-10:00", "14:30-15:00"],
                "foreign_active": ["09:30-10:30", "14:00-15:00"]
            }
        }
    """
```

#### 6) `get_smart_money_tracker`
```python
@tool
async def get_smart_money_tracker(
    detection_method: Literal["LARGE_ORDERS", "INSTITUTION_CLUSTER", "FOREIGN_SURGE"] = "LARGE_ORDERS",
    market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
    min_confidence: float = 7.0,
    count: int = 20
) -> dict:
    """
    스마트머니 움직임 추적
    
    Parameters:
        detection_method: 감지 방법
        market: 시장 구분
        min_confidence: 최소 신뢰도
        count: 조회 종목 수
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "smart_money_signals": [
                {
                    "stock_code": "005930",
                    "stock_name": "삼성전자",
                    "signal_type": "INSTITUTIONAL_ACCUMULATION",
                    "confidence": 8.5,
                    "detection_details": {
                        "large_block_trades": 15,
                        "average_block_size": 345678900,
                        "institutional_buyers": ["연기금", "투신", "사모펀드"],
                        "accumulation_period": "5D",
                        "price_impact": "MINIMAL"
                    },
                    "metrics": {
                        "net_buy_amount": 234567890000,
                        "avg_buy_price": 78200,
                        "current_price": 78500,
                        "unrealized_gain": 0.38,
                        "volume_weighted_price": 78350
                    },
                    "technical_context": {
                        "support_level": 77000,
                        "resistance_level": 80000,
                        "trend": "UPWARD",
                        "accumulation_zone": [77500, 78500]
                    },
                    "similar_patterns": [
                        {
                            "date": "2023-06-15",
                            "outcome": "20% gain in 30 days",
                            "similarity_score": 0.85
                        }
                    ]
                },
                ...
            ],
            "market_smart_money_index": {
                "current_value": 72.5,
                "trend": "INCREASING",
                "interpretation": "Smart money accumulating",
                "sector_focus": ["반도체", "2차전지", "바이오"],
                "risk_appetite": "MODERATE"
            },
            "institutional_positioning": {
                "net_exposure": "LONG",
                "leverage_estimate": 1.3,
                "sector_rotation": "TECHNOLOGY",
                "time_horizon": "MEDIUM_TERM"
            }
        }
    """
```

#### 7) `get_investor_sentiment`
```python
@tool
async def get_investor_sentiment(
    period: Literal["REAL_TIME", "1D", "1W", "1M"] = "1D",
    granularity: Literal["OVERALL", "BY_TYPE", "BY_SECTOR"] = "OVERALL"
) -> dict:
    """
    투자자 심리 지표 분석
    
    Parameters:
        period: 분석 기간
        granularity: 분석 세분화 수준
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "sentiment_scores": {
                "overall": {
                    "score": 65.5,  # 0-100
                    "interpretation": "MODERATELY_BULLISH",
                    "change_from_yesterday": 3.2
                },
                "by_investor_type": {
                    "foreign": {
                        "score": 78.5,
                        "trend": "INCREASINGLY_BULLISH",
                        "key_drivers": ["tech_earnings", "weak_dollar"],
                        "consistency": 0.85
                    },
                    "institution": {
                        "score": 58.2,
                        "trend": "NEUTRAL",
                        "concerns": ["valuation", "interest_rates"],
                        "positioning": "DEFENSIVE"
                    },
                    "individual": {
                        "score": 45.3,
                        "trend": "CAUTIOUS",
                        "behavior": "PROFIT_TAKING",
                        "retail_favorites": ["게임", "엔터", "바이오"]
                    }
                },
                "sentiment_drivers": {
                    "positive": [
                        {
                            "factor": "외국인 순매수 지속",
                            "impact": 8.5,
                            "affected_sectors": ["반도체", "전기전자"]
                        }
                    ],
                    "negative": [
                        {
                            "factor": "기관 차익실현",
                            "impact": -5.2,
                            "affected_sectors": ["금융", "건설"]
                        }
                    ]
                },
                "divergence_indicators": {
                    "foreign_vs_domestic": 33.2,  # 괴리도
                    "institution_vs_individual": 12.9,
                    "interpretation": "외국인 주도 시장"
                }
            },
            "market_regime": {
                "current": "RISK_ON",
                "confidence": 0.72,
                "expected_duration": "2-4 weeks",
                "key_risks": ["금리 인상", "중국 경기"]
            },
            "actionable_insights": [
                {
                    "insight": "외국인 매수세 강한 대형 기술주 주목",
                    "confidence": 8.0,
                    "timeframe": "SHORT_TERM"
                },
                {
                    "insight": "기관 순매도 업종 단기 조정 예상",
                    "confidence": 7.2,
                    "timeframe": "IMMEDIATE"
                }
            ]
        }
    """
```

## 4. 분석 엔진 구현

### 4.1 투자자 분석 엔진

```python
# src/analysis/investor_analyzer.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class InvestorProfile:
    """투자자 프로파일"""
    investor_type: str
    behavior_pattern: str
    risk_appetite: str
    typical_holding_period: int
    preferred_sectors: List[str]
    trading_style: str

class InvestorAnalyzer:
    """투자자 행동 분석 엔진"""
    
    def __init__(self):
        self.profiles = self._initialize_profiles()
        self.behavior_models = {}
        
    def _initialize_profiles(self) -> Dict[str, InvestorProfile]:
        """투자자 프로파일 초기화"""
        return {
            "FOREIGN": InvestorProfile(
                investor_type="FOREIGN",
                behavior_pattern="MOMENTUM",
                risk_appetite="MODERATE",
                typical_holding_period=90,
                preferred_sectors=["기술", "소비재"],
                trading_style="TREND_FOLLOWING"
            ),
            "INSTITUTION": InvestorProfile(
                investor_type="INSTITUTION",
                behavior_pattern="VALUE",
                risk_appetite="LOW",
                typical_holding_period=180,
                preferred_sectors=["금융", "산업재"],
                trading_style="CONTRARIAN"
            ),
            "INDIVIDUAL": InvestorProfile(
                investor_type="INDIVIDUAL",
                behavior_pattern="MIXED",
                risk_appetite="HIGH",
                typical_holding_period=30,
                preferred_sectors=["바이오", "게임", "엔터"],
                trading_style="NOISE_TRADING"
            )
        }
    
    async def analyze_investor_behavior(
        self,
        trading_data: pd.DataFrame,
        investor_type: str
    ) -> Dict:
        """투자자 행동 패턴 분석"""
        
        profile = self.profiles.get(investor_type)
        
        analysis = {
            "investor_type": investor_type,
            "profile": profile,
            "behavior_metrics": self._calculate_behavior_metrics(trading_data, investor_type),
            "trading_patterns": self._identify_trading_patterns(trading_data, investor_type),
            "market_timing": self._analyze_market_timing(trading_data, investor_type),
            "sector_preference": self._analyze_sector_preference(trading_data, investor_type),
            "performance_analysis": self._analyze_performance(trading_data, investor_type)
        }
        
        # 이상 행동 감지
        analysis["anomalies"] = self._detect_anomalies(trading_data, investor_type)
        
        # 예측 모델
        analysis["predictions"] = await self._predict_future_behavior(analysis)
        
        return analysis
    
    def _calculate_behavior_metrics(
        self, 
        data: pd.DataFrame, 
        investor_type: str
    ) -> Dict:
        """행동 지표 계산"""
        
        net_trading = data[f'{investor_type.lower()}_net']
        
        return {
            "consistency_score": self._calculate_consistency(net_trading),
            "momentum_following": self._calculate_momentum_following(data, investor_type),
            "contrarian_score": self._calculate_contrarian_score(data, investor_type),
            "herding_index": self._calculate_herding_index(data, investor_type),
            "timing_skill": self._calculate_timing_skill(data, investor_type),
            "concentration_ratio": self._calculate_concentration(data, investor_type)
        }
    
    def _identify_trading_patterns(
        self,
        data: pd.DataFrame,
        investor_type: str
    ) -> List[Dict]:
        """거래 패턴 식별"""
        patterns = []
        
        # 누적 매수/매도 패턴
        accumulation = self._detect_accumulation_pattern(data, investor_type)
        if accumulation:
            patterns.append(accumulation)
        
        # 분산 매도 패턴
        distribution = self._detect_distribution_pattern(data, investor_type)
        if distribution:
            patterns.append(distribution)
        
        # 회전 매매 패턴
        rotation = self._detect_rotation_pattern(data, investor_type)
        if rotation:
            patterns.append(rotation)
        
        # 펌핑 패턴
        pumping = self._detect_pumping_pattern(data, investor_type)
        if pumping:
            patterns.append(pumping)
        
        return patterns
    
    def _detect_accumulation_pattern(
        self,
        data: pd.DataFrame,
        investor_type: str
    ) -> Optional[Dict]:
        """누적 매수 패턴 감지"""
        
        net_buying = data[f'{investor_type.lower()}_net']
        prices = data['close']
        
        # 연속 순매수 일수
        consecutive_buying = (net_buying > 0).astype(int)
        consecutive_count = consecutive_buying.groupby(
            (consecutive_buying != consecutive_buying.shift()).cumsum()
        ).cumsum()
        
        if consecutive_count.iloc[-1] >= 5:  # 5일 이상 연속 매수
            return {
                "pattern": "ACCUMULATION",
                "confidence": min(consecutive_count.iloc[-1] / 10, 1.0) * 100,
                "duration": consecutive_count.iloc[-1],
                "total_amount": net_buying.tail(consecutive_count.iloc[-1]).sum(),
                "average_price": prices.tail(consecutive_count.iloc[-1]).mean(),
                "price_trend": "UP" if prices.iloc[-1] > prices.iloc[-consecutive_count.iloc[-1]] else "DOWN"
            }
        
        return None
    
    def _analyze_market_timing(
        self,
        data: pd.DataFrame,
        investor_type: str
    ) -> Dict:
        """시장 타이밍 분석"""
        
        net_trading = data[f'{investor_type.lower()}_net']
        returns = data['returns']
        
        # 매수/매도 후 수익률
        buy_timing = []
        sell_timing = []
        
        for i in range(len(data) - 20):
            if net_trading.iloc[i] > 0:  # 순매수
                future_return = returns.iloc[i:i+20].sum()
                buy_timing.append(future_return)
            elif net_trading.iloc[i] < 0:  # 순매도
                future_return = returns.iloc[i:i+20].sum()
                sell_timing.append(-future_return)  # 매도 후 하락이 좋은 타이밍
        
        return {
            "buy_timing_score": np.mean(buy_timing) if buy_timing else 0,
            "sell_timing_score": np.mean(sell_timing) if sell_timing else 0,
            "overall_timing_skill": (np.mean(buy_timing) + np.mean(sell_timing)) / 2 if buy_timing and sell_timing else 0,
            "consistency": np.std(buy_timing + sell_timing) if buy_timing or sell_timing else float('inf'),
            "best_timing_examples": self._find_best_timing_examples(data, investor_type)
        }
```

### 4.2 자금 흐름 분석기

```python
# src/analysis/flow_analyzer.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy import stats

class FlowAnalyzer:
    """자금 흐름 분석기"""
    
    def __init__(self):
        self.flow_cache = {}
        self.sector_mappings = self._load_sector_mappings()
        
    async def analyze_money_flow(
        self,
        market_data: pd.DataFrame,
        period: str = "1D"
    ) -> Dict:
        """시장 전체 자금 흐름 분석"""
        
        flow_analysis = {
            "timestamp": datetime.now(),
            "period": period,
            "total_flow": self._calculate_total_flow(market_data),
            "flow_strength": self._calculate_flow_strength(market_data),
            "flow_persistence": self._calculate_flow_persistence(market_data),
            "sector_rotation": self._analyze_sector_rotation(market_data),
            "flow_concentration": self._calculate_flow_concentration(market_data),
            "smart_money_indicator": self._calculate_smart_money_indicator(market_data)
        }
        
        # 자금 흐름 예측
        flow_analysis["flow_forecast"] = await self._forecast_flow(market_data)
        
        return flow_analysis
    
    def _calculate_flow_strength(self, data: pd.DataFrame) -> Dict:
        """자금 흐름 강도 계산"""
        
        foreign_flow = data['foreign_net'].sum()
        institution_flow = data['institution_net'].sum()
        individual_flow = data['individual_net'].sum()
        
        total_flow = abs(foreign_flow) + abs(institution_flow) + abs(individual_flow)
        
        return {
            "absolute_strength": total_flow,
            "directional_strength": foreign_flow + institution_flow,
            "foreign_dominance": abs(foreign_flow) / total_flow if total_flow > 0 else 0,
            "institution_dominance": abs(institution_flow) / total_flow if total_flow > 0 else 0,
            "flow_alignment": self._calculate_alignment(foreign_flow, institution_flow),
            "intensity_score": self._calculate_intensity_score(data)
        }
    
    def _analyze_sector_rotation(self, data: pd.DataFrame) -> Dict:
        """섹터 로테이션 분석"""
        
        sector_flows = {}
        
        for sector in self.sector_mappings:
            sector_data = data[data['sector'] == sector]
            if not sector_data.empty:
                sector_flows[sector] = {
                    "net_flow": sector_data['foreign_net'].sum() + sector_data['institution_net'].sum(),
                    "foreign_flow": sector_data['foreign_net'].sum(),
                    "institution_flow": sector_data['institution_net'].sum(),
                    "momentum": self._calculate_sector_momentum(sector_data),
                    "relative_strength": self._calculate_relative_strength(sector_data, data)
                }
        
        # 로테이션 매트릭스
        rotation_matrix = self._build_rotation_matrix(sector_flows)
        
        return {
            "sector_flows": sector_flows,
            "rotation_matrix": rotation_matrix,
            "from_sectors": self._identify_outflow_sectors(sector_flows),
            "to_sectors": self._identify_inflow_sectors(sector_flows),
            "rotation_intensity": self._calculate_rotation_intensity(sector_flows),
            "cycle_phase": self._identify_cycle_phase(rotation_matrix)
        }
    
    def _calculate_smart_money_indicator(self, data: pd.DataFrame) -> Dict:
        """스마트머니 지표 계산"""
        
        # 대량 거래 감지
        large_trades = self._detect_large_trades(data)
        
        # 기관/외국인 동조화
        synchronization = self._calculate_synchronization(data)
        
        # 가격 영향 최소화 거래
        stealth_accumulation = self._detect_stealth_accumulation(data)
        
        # 종합 스마트머니 점수
        smart_money_score = (
            large_trades['score'] * 0.3 +
            synchronization['score'] * 0.4 +
            stealth_accumulation['score'] * 0.3
        )
        
        return {
            "score": smart_money_score,
            "components": {
                "large_trades": large_trades,
                "synchronization": synchronization,
                "stealth_accumulation": stealth_accumulation
            },
            "interpretation": self._interpret_smart_money_score(smart_money_score),
            "confidence": self._calculate_confidence(data),
            "recent_signals": self._get_recent_smart_money_signals(data)
        }
```

### 4.3 패턴 감지기

```python
# src/analysis/pattern_detector.py
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import numpy as np

class InvestorPatternDetector:
    """투자자 패턴 감지기"""
    
    def __init__(self):
        self.pattern_library = self._build_pattern_library()
        self.ml_models = {}
        
    def detect_patterns(
        self,
        investor_data: pd.DataFrame,
        min_confidence: float = 0.7
    ) -> List[Dict]:
        """투자자 패턴 감지"""
        
        detected_patterns = []
        
        # 기본 패턴 감지
        for pattern_name, pattern_func in self.pattern_library.items():
            result = pattern_func(investor_data)
            if result and result['confidence'] >= min_confidence:
                detected_patterns.append(result)
        
        # ML 기반 이상 패턴 감지
        anomaly_patterns = self._detect_anomaly_patterns(investor_data)
        detected_patterns.extend(anomaly_patterns)
        
        # 패턴 조합 분석
        combined_patterns = self._analyze_pattern_combinations(detected_patterns)
        
        return {
            "individual_patterns": detected_patterns,
            "combined_patterns": combined_patterns,
            "pattern_strength": self._calculate_pattern_strength(detected_patterns),
            "market_implications": self._analyze_implications(detected_patterns)
        }
    
    def _build_pattern_library(self) -> Dict:
        """패턴 라이브러리 구축"""
        return {
            "accumulation": self._detect_accumulation,
            "distribution": self._detect_distribution,
            "pump_and_dump": self._detect_pump_and_dump,
            "stop_hunting": self._detect_stop_hunting,
            "window_dressing": self._detect_window_dressing,
            "front_running": self._detect_front_running,
            "iceberg_orders": self._detect_iceberg_orders
        }
    
    def _detect_pump_and_dump(self, data: pd.DataFrame) -> Optional[Dict]:
        """펌프 앤 덤프 패턴 감지"""
        
        # 단기간 급등 후 대량 매도
        price_surge = data['close'].pct_change(5).iloc[-1]  # 5일 수익률
        recent_volume = data['volume'].iloc[-5:].mean()
        avg_volume = data['volume'].iloc[-30:-5].mean()
        
        # 외국인/기관 매도 확인
        recent_institutional_flow = data['institution_net'].iloc[-3:].sum()
        recent_foreign_flow = data['foreign_net'].iloc[-3:].sum()
        
        if (price_surge > 0.3 and  # 30% 이상 급등
            recent_volume > avg_volume * 3 and  # 거래량 3배 이상
            recent_institutional_flow < 0 and  # 기관 매도
            recent_foreign_flow < 0):  # 외국인 매도
            
            return {
                "pattern": "PUMP_AND_DUMP",
                "confidence": 0.85,
                "stage": "DUMP",
                "price_surge": price_surge,
                "volume_spike": recent_volume / avg_volume,
                "institutional_selling": abs(recent_institutional_flow),
                "risk_level": "EXTREME",
                "recommended_action": "AVOID"
            }
        
        return None
    
    def _detect_anomaly_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """ML 기반 이상 패턴 감지"""
        
        # 특징 추출
        features = self._extract_features(data)
        
        # 정규화
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # DBSCAN 클러스터링
        clustering = DBSCAN(eps=0.5, min_samples=5)
        labels = clustering.fit_predict(features_scaled)
        
        # 이상치 식별 (라벨 -1)
        anomalies = []
        anomaly_indices = np.where(labels == -1)[0]
        
        for idx in anomaly_indices:
            anomaly = self._analyze_anomaly(data.iloc[idx], features[idx])
            if anomaly:
                anomalies.append(anomaly)
        
        return anomalies
```

### 4.4 스마트머니 추적기

```python
# src/analysis/smart_money.py
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

class SmartMoneyTracker:
    """스마트머니 추적 및 분석"""
    
    def __init__(self):
        self.smart_money_criteria = {
            "large_order_threshold": 1000000000,  # 10억원
            "institution_types": ["연기금", "자산운용", "보험", "은행"],
            "foreign_quality_threshold": 0.7
        }
        
    async def track_smart_money(
        self,
        market_data: pd.DataFrame,
        transaction_data: pd.DataFrame
    ) -> Dict:
        """스마트머니 추적"""
        
        # 대형 블록 거래 식별
        block_trades = self._identify_block_trades(transaction_data)
        
        # 기관 투자자 품질 평가
        institutional_quality = self._assess_institutional_quality(transaction_data)
        
        # 외국인 투자자 분류
        foreign_classification = self._classify_foreign_investors(transaction_data)
        
        # 스마트머니 흐름 계산
        smart_money_flow = self._calculate_smart_money_flow(
            block_trades,
            institutional_quality,
            foreign_classification
        )
        
        # 스마트머니 타겟 종목
        target_stocks = self._identify_target_stocks(smart_money_flow)
        
        return {
            "timestamp": datetime.now(),
            "smart_money_flow": smart_money_flow,
            "target_stocks": target_stocks,
            "market_positioning": self._analyze_positioning(smart_money_flow),
            "sector_preferences": self._analyze_sector_preferences(smart_money_flow),
            "timing_analysis": self._analyze_timing(smart_money_flow),
            "follow_recommendations": self._generate_recommendations(target_stocks)
        }
    
    def _identify_block_trades(self, data: pd.DataFrame) -> List[Dict]:
        """블록 거래 식별"""
        
        block_trades = []
        
        for _, trade in data.iterrows():
            if trade['amount'] >= self.smart_money_criteria['large_order_threshold']:
                block_trade = {
                    "timestamp": trade['timestamp'],
                    "stock_code": trade['stock_code'],
                    "amount": trade['amount'],
                    "price": trade['price'],
                    "investor_type": trade['investor_type'],
                    "execution_quality": self._assess_execution_quality(trade),
                    "market_impact": self._calculate_market_impact(trade),
                    "stealth_score": self._calculate_stealth_score(trade)
                }
                block_trades.append(block_trade)
        
        return block_trades
    
    def _assess_institutional_quality(self, data: pd.DataFrame) -> Dict:
        """기관 투자자 품질 평가"""
        
        quality_scores = {}
        
        for inst_type in self.smart_money_criteria['institution_types']:
            inst_data = data[data['institution_subtype'] == inst_type]
            
            if not inst_data.empty:
                quality_scores[inst_type] = {
                    "historical_performance": self._calculate_historical_performance(inst_data),
                    "timing_skill": self._calculate_timing_skill(inst_data),
                    "selection_skill": self._calculate_selection_skill(inst_data),
                    "consistency": self._calculate_consistency(inst_data),
                    "information_ratio": self._calculate_information_ratio(inst_data)
                }
        
        return quality_scores
    
    def _calculate_smart_money_flow(
        self,
        block_trades: List[Dict],
        institutional_quality: Dict,
        foreign_classification: Dict
    ) -> Dict:
        """스마트머니 자금 흐름 계산"""
        
        smart_flow = {
            "total_inflow": 0,
            "total_outflow": 0,
            "net_flow": 0,
            "by_investor_type": {},
            "by_stock": {},
            "quality_weighted_flow": 0
        }
        
        # 블록 거래 기반 흐름
        for trade in block_trades:
            amount = trade['amount'] if trade['amount'] > 0 else 0
            
            # 품질 가중치 적용
            quality_weight = self._get_quality_weight(
                trade['investor_type'],
                institutional_quality,
                foreign_classification
            )
            
            weighted_amount = amount * quality_weight
            
            if trade['amount'] > 0:
                smart_flow['total_inflow'] += weighted_amount
            else:
                smart_flow['total_outflow'] += abs(weighted_amount)
            
            # 종목별 집계
            stock_code = trade['stock_code']
            if stock_code not in smart_flow['by_stock']:
                smart_flow['by_stock'][stock_code] = {
                    'inflow': 0,
                    'outflow': 0,
                    'net': 0,
                    'trades': []
                }
            
            smart_flow['by_stock'][stock_code]['trades'].append(trade)
            
        smart_flow['net_flow'] = smart_flow['total_inflow'] - smart_flow['total_outflow']
        
        return smart_flow
```

## 5. 캐싱 및 성능 최적화

```python
# src/utils/cache.py
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
import redis
import json

class InvestorDataCache:
    """투자자 데이터 전용 캐시"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.memory_cache = {}
        self.cache_ttl = {
            "real_time": 10,  # 10초
            "minute": 60,
            "hourly": 3600,
            "daily": 86400
        }
        
    async def get_investor_data(
        self,
        key: str,
        fetch_func,
        data_type: str = "minute"
    ) -> Any:
        """투자자 데이터 캐시 조회"""
        
        # 1. 메모리 캐시 확인
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if entry['expires'] > datetime.now():
                return entry['data']
        
        # 2. Redis 캐시 확인
        redis_data = await self._get_from_redis(key)
        if redis_data:
            # 메모리 캐시에도 저장
            self.memory_cache[key] = {
                'data': redis_data,
                'expires': datetime.now() + timedelta(seconds=self.cache_ttl[data_type])
            }
            return redis_data
        
        # 3. 데이터 fetch
        data = await fetch_func()
        
        # 4. 캐시 저장
        await self._save_to_cache(key, data, data_type)
        
        return data
    
    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Redis에서 데이터 조회"""
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Redis get error: {e}")
        return None
    
    async def _save_to_cache(self, key: str, data: Any, data_type: str):
        """캐시에 저장"""
        ttl = self.cache_ttl[data_type]
        
        # Redis 저장
        try:
            self.redis.setex(key, ttl, json.dumps(data))
        except Exception as e:
            print(f"Redis set error: {e}")
        
        # 메모리 캐시 저장
        self.memory_cache[key] = {
            'data': data,
            'expires': datetime.now() + timedelta(seconds=ttl)
        }
        
        # 메모리 캐시 크기 관리
        if len(self.memory_cache) > 1000:
            self._evict_old_entries()
    
    def _evict_old_entries(self):
        """오래된 캐시 항목 제거"""
        current_time = datetime.now()
        keys_to_remove = [
            k for k, v in self.memory_cache.items()
            if v['expires'] < current_time
        ]
        for key in keys_to_remove:
            del self.memory_cache[key]
```

## 6. 데이터베이스 스키마

```sql
-- PostgreSQL + TimescaleDB 스키마

-- 투자자 거래 테이블
CREATE TABLE investor_trading (
    timestamp TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    foreign_buy BIGINT,
    foreign_sell BIGINT,
    foreign_net BIGINT,
    institution_buy BIGINT,
    institution_sell BIGINT,
    institution_net BIGINT,
    individual_buy BIGINT,
    individual_sell BIGINT,
    individual_net BIGINT,
    program_buy BIGINT,
    program_sell BIGINT,
    program_net BIGINT,
    PRIMARY KEY (timestamp, stock_code)
);

-- TimescaleDB 하이퍼테이블 변환
SELECT create_hypertable('investor_trading', 'timestamp');

-- 인덱스 생성
CREATE INDEX idx_investor_trading_stock ON investor_trading (stock_code, timestamp DESC);
CREATE INDEX idx_investor_trading_foreign_net ON investor_trading (foreign_net);
CREATE INDEX idx_investor_trading_institution_net ON investor_trading (institution_net);

-- 기관 투자자 세부 테이블
CREATE TABLE institution_detail (
    timestamp TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    institution_type VARCHAR(50) NOT NULL,
    buy_amount BIGINT,
    sell_amount BIGINT,
    net_amount BIGINT,
    PRIMARY KEY (timestamp, stock_code, institution_type)
);

SELECT create_hypertable('institution_detail', 'timestamp');

-- 프로그램 매매 상세 테이블
CREATE TABLE program_trading_detail (
    timestamp TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(10),
    program_type VARCHAR(20) NOT NULL, -- ARBITRAGE, NON_ARBITRAGE
    buy_amount BIGINT,
    sell_amount BIGINT,
    net_amount BIGINT,
    PRIMARY KEY (timestamp, stock_code, program_type)
);

SELECT create_hypertable('program_trading_detail', 'timestamp');

-- 스마트머니 추적 테이블
CREATE TABLE smart_money_signals (
    signal_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    signal_type VARCHAR(50),
    confidence FLOAT,
    amount BIGINT,
    investor_type VARCHAR(20),
    metadata JSONB
);

CREATE INDEX idx_smart_money_timestamp ON smart_money_signals (timestamp DESC);
CREATE INDEX idx_smart_money_stock ON smart_money_signals (stock_code);
CREATE INDEX idx_smart_money_confidence ON smart_money_signals (confidence DESC);
```

## 7. 구현 일정

### Phase 1: 기초 구현 (4일)
- [ ] 프로젝트 구조 설정
- [ ] MCP 서버 기본 구현
- [ ] API 클라이언트 구현 (한투, 이베스트)
- [ ] 기본 투자자 동향 도구 구현

### Phase 2: 핵심 기능 (6일)
- [ ] 7개 주요 도구 구현
- [ ] 투자자 분석 엔진 구현
- [ ] 자금 흐름 분석기 구현
- [ ] 패턴 감지기 구현

### Phase 3: 고급 기능 (5일)
- [ ] 스마트머니 추적기 구현
- [ ] 실시간 데이터 처리
- [ ] 데이터베이스 최적화
- [ ] 캐싱 시스템 구현

### Phase 4: 통합 및 테스트 (3일)
- [ ] 통합 테스트
- [ ] 성능 최적화
- [ ] 문서화
- [ ] 배포 준비

## 8. 테스트 계획

### 8.1 단위 테스트

```python
# tests/test_analyzer.py
import pytest
import pandas as pd
import numpy as np
from src.analysis.investor_analyzer import InvestorAnalyzer
from src.analysis.smart_money import SmartMoneyTracker

class TestInvestorAnalyzer:
    @pytest.fixture
    def sample_trading_data(self):
        """테스트용 거래 데이터"""
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        return pd.DataFrame({
            'timestamp': dates,
            'foreign_buy': np.random.uniform(1e9, 1e10, 30),
            'foreign_sell': np.random.uniform(1e9, 1e10, 30),
            'institution_buy': np.random.uniform(5e8, 5e9, 30),
            'institution_sell': np.random.uniform(5e8, 5e9, 30),
            'individual_buy': np.random.uniform(1e9, 2e9, 30),
            'individual_sell': np.random.uniform(1e9, 2e9, 30),
            'close': np.random.uniform(50000, 60000, 30)
        })
    
    @pytest.mark.asyncio
    async def test_behavior_analysis(self, sample_trading_data):
        """투자자 행동 분석 테스트"""
        analyzer = InvestorAnalyzer()
        
        # 외국인 투자자 분석
        result = await analyzer.analyze_investor_behavior(
            sample_trading_data,
            "FOREIGN"
        )
        
        assert 'behavior_metrics' in result
        assert 'trading_patterns' in result
        assert 'market_timing' in result
        assert result['behavior_metrics']['consistency_score'] >= 0
        
    @pytest.mark.asyncio
    async def test_pattern_detection(self, sample_trading_data):
        """패턴 감지 테스트"""
        analyzer = InvestorAnalyzer()
        
        # 연속 매수 패턴 생성
        sample_trading_data['foreign_net'] = 1000000000  # 10억 순매수
        
        result = await analyzer.analyze_investor_behavior(
            sample_trading_data,
            "FOREIGN"
        )
        
        patterns = result['trading_patterns']
        assert any(p['pattern'] == 'ACCUMULATION' for p in patterns)

@pytest.mark.asyncio
async def test_smart_money_tracking():
    """스마트머니 추적 테스트"""
    tracker = SmartMoneyTracker()
    
    # 테스트 데이터
    market_data = pd.DataFrame({
        'stock_code': ['005930'] * 10,
        'close': np.linspace(70000, 75000, 10),
        'volume': np.random.uniform(1e7, 2e7, 10)
    })
    
    transaction_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=10, freq='H'),
        'stock_code': '005930',
        'amount': [2e9, -5e8, 3e9, -1e9, 5e9, -2e9, 4e9, -3e9, 6e9, -1e9],
        'price': np.linspace(70000, 75000, 10),
        'investor_type': ['FOREIGN'] * 5 + ['INSTITUTION'] * 5,
        'institution_subtype': [None] * 5 + ['연기금'] * 5
    })
    
    result = await tracker.track_smart_money(market_data, transaction_data)
    
    assert 'smart_money_flow' in result
    assert 'target_stocks' in result
    assert result['smart_money_flow']['net_flow'] != 0
```

### 8.2 통합 테스트

```python
# tests/test_integration.py
import pytest
from src.server import InvestorTrendsMCPServer

@pytest.mark.asyncio
async def test_investor_trading_flow():
    """투자자 거래 조회 플로우 테스트"""
    server = InvestorTrendsMCPServer()
    
    # 시장 전체 투자자 동향
    result = await server.get_investor_trading(
        investor_type="ALL",
        period="1D",
        market="KOSPI"
    )
    
    assert 'investor_data' in result
    assert 'foreign' in result['investor_data']
    assert 'institution' in result['investor_data']
    assert 'individual' in result['investor_data']
    
    # 데이터 일관성 확인
    foreign_net = result['investor_data']['foreign']['net_amount']
    institution_net = result['investor_data']['institution']['net_amount']
    individual_net = result['investor_data']['individual']['net_amount']
    
    # 시장 전체의 순매수 합은 0이어야 함
    assert abs(foreign_net + institution_net + individual_net) < 1000000  # 오차 허용

@pytest.mark.asyncio
async def test_smart_money_detection():
    """스마트머니 감지 테스트"""
    server = InvestorTrendsMCPServer()
    
    result = await server.get_smart_money_tracker(
        detection_method="INSTITUTION_CLUSTER",
        market="KOSPI",
        min_confidence=7.0
    )
    
    assert 'smart_money_signals' in result
    assert all(signal['confidence'] >= 7.0 for signal in result['smart_money_signals'])
```

## 9. 배포 및 운영

### 9.1 환경 설정

```bash
# .env 파일
KOREA_INVESTMENT_APP_KEY=your_app_key
KOREA_INVESTMENT_APP_SECRET=your_app_secret
EBEST_APP_KEY=your_ebest_key
EBEST_APP_SECRET=your_ebest_secret
DATABASE_URL=postgresql://user:pass@localhost:5432/investor_trends
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
CACHE_TTL_REALTIME=10
CACHE_TTL_MINUTE=60
SMART_MONEY_THRESHOLD=1000000000
```

### 9.2 Docker 설정

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 실행
CMD ["python", "-m", "src.server"]
```

### 9.3 Docker Compose 설정

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-investor-trends:
    build: .
    container_name: mcp-investor-trends
    environment:
      - KOREA_INVESTMENT_APP_KEY=${KOREA_INVESTMENT_APP_KEY}
      - KOREA_INVESTMENT_APP_SECRET=${KOREA_INVESTMENT_APP_SECRET}
      - EBEST_APP_KEY=${EBEST_APP_KEY}
      - EBEST_APP_SECRET=${EBEST_APP_SECRET}
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/investor_trends
      - REDIS_URL=redis://redis:6379
    ports:
      - "8083:8080"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      
  postgres:
    image: timescale/timescaledb:latest-pg14
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=investor_trends
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  postgres_data:
  redis_data:
```

## 10. 모니터링 및 유지보수

### 10.1 실시간 모니터링

```python
# src/utils/monitoring.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import psutil

@dataclass
class SystemMetrics:
    """시스템 메트릭"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    active_connections: int
    cache_hit_rate: float
    db_query_time: float
    api_response_time: float

class InvestorMonitor:
    """투자자 동향 모니터링"""
    
    def __init__(self):
        self.metrics_buffer = []
        self.alert_thresholds = {
            "flow_anomaly": 3.0,  # 표준편차
            "api_latency": 2000,  # ms
            "cache_hit_rate": 0.6,
            "error_rate": 0.05
        }
        
    async def monitor_system_health(self) -> Dict:
        """시스템 건강 상태 모니터링"""
        
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            active_connections=await self._count_active_connections(),
            cache_hit_rate=await self._get_cache_hit_rate(),
            db_query_time=await self._measure_db_query_time(),
            api_response_time=await self._measure_api_response_time()
        )
        
        self.metrics_buffer.append(metrics)
        
        # 이상 감지
        anomalies = self._detect_anomalies(metrics)
        
        return {
            "current_metrics": metrics,
            "anomalies": anomalies,
            "health_score": self._calculate_health_score(metrics),
            "recommendations": self._generate_recommendations(metrics, anomalies)
        }
    
    async def monitor_investor_flows(self) -> Dict:
        """투자자 자금 흐름 모니터링"""
        
        # 실시간 자금 흐름
        current_flows = await self._get_current_flows()
        
        # 이상 거래 감지
        anomalous_flows = self._detect_flow_anomalies(current_flows)
        
        # 패턴 변화 감지
        pattern_changes = self._detect_pattern_changes(current_flows)
        
        return {
            "timestamp": datetime.now(),
            "current_flows": current_flows,
            "anomalous_flows": anomalous_flows,
            "pattern_changes": pattern_changes,
            "market_sentiment": self._calculate_market_sentiment(current_flows),
            "risk_indicators": self._calculate_risk_indicators(current_flows)
        }
    
    def _detect_flow_anomalies(self, flows: Dict) -> List[Dict]:
        """자금 흐름 이상 감지"""
        anomalies = []
        
        for investor_type, flow_data in flows.items():
            # Z-score 계산
            z_score = self._calculate_z_score(flow_data['net_amount'])
            
            if abs(z_score) > self.alert_thresholds['flow_anomaly']:
                anomalies.append({
                    "investor_type": investor_type,
                    "net_amount": flow_data['net_amount'],
                    "z_score": z_score,
                    "severity": "HIGH" if abs(z_score) > 4 else "MEDIUM",
                    "possible_causes": self._analyze_anomaly_causes(investor_type, flow_data)
                })
        
        return anomalies
    
    async def generate_daily_report(self) -> Dict:
        """일일 리포트 생성"""
        
        # 일일 통계
        daily_stats = await self._calculate_daily_statistics()
        
        # 주요 이벤트
        key_events = await self._identify_key_events()
        
        # 투자자별 성과
        investor_performance = await self._analyze_investor_performance()
        
        # 시장 전망
        market_outlook = await self._generate_market_outlook()
        
        return {
            "report_date": datetime.now().date(),
            "executive_summary": self._generate_executive_summary(daily_stats),
            "daily_statistics": daily_stats,
            "key_events": key_events,
            "investor_performance": investor_performance,
            "market_outlook": market_outlook,
            "action_items": self._generate_action_items(daily_stats, key_events)
        }
```

### 10.2 로그 분석 시스템

```python
# src/utils/log_analyzer.py
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json

class InvestorLogAnalyzer:
    """투자자 동향 로그 분석"""
    
    def __init__(self):
        self.patterns = {
            "large_transaction": re.compile(r"LARGE_TRANSACTION.*amount:(\d+).*investor:(\w+)"),
            "anomaly_detected": re.compile(r"ANOMALY.*type:(\w+).*severity:(\w+)"),
            "api_error": re.compile(r"API_ERROR.*endpoint:(\w+).*code:(\d+)"),
            "smart_money": re.compile(r"SMART_MONEY.*stock:(\w+).*confidence:([\d.]+)")
        }
        
    def analyze_logs(self, log_file: str, time_window: timedelta) -> Dict:
        """로그 분석"""
        
        analysis_result = {
            "time_window": time_window,
            "transaction_analysis": defaultdict(list),
            "anomaly_summary": defaultdict(int),
            "api_health": defaultdict(lambda: {"success": 0, "error": 0}),
            "smart_money_signals": [],
            "performance_metrics": {}
        }
        
        with open(log_file, 'r') as f:
            for line in f:
                self._process_log_line(line, analysis_result)
        
        # 집계 및 요약
        analysis_result["summary"] = self._generate_summary(analysis_result)
        
        return analysis_result
    
    def _process_log_line(self, line: str, result: Dict):
        """개별 로그 라인 처리"""
        
        # 대형 거래 감지
        large_tx_match = self.patterns["large_transaction"].search(line)
        if large_tx_match:
            amount, investor = large_tx_match.groups()
            result["transaction_analysis"][investor].append({
                "amount": int(amount),
                "timestamp": self._extract_timestamp(line)
            })
        
        # 이상 거래 감지
        anomaly_match = self.patterns["anomaly_detected"].search(line)
        if anomaly_match:
            anomaly_type, severity = anomaly_match.groups()
            result["anomaly_summary"][f"{anomaly_type}_{severity}"] += 1
        
        # API 상태
        api_match = self.patterns["api_error"].search(line)
        if api_match:
            endpoint, code = api_match.groups()
            if int(code) >= 400:
                result["api_health"][endpoint]["error"] += 1
            else:
                result["api_health"][endpoint]["success"] += 1
        
        # 스마트머니 신호
        smart_match = self.patterns["smart_money"].search(line)
        if smart_match:
            stock, confidence = smart_match.groups()
            result["smart_money_signals"].append({
                "stock": stock,
                "confidence": float(confidence),
                "timestamp": self._extract_timestamp(line)
            })
    
    def generate_insights(self, analysis_result: Dict) -> List[Dict]:
        """분석 결과에서 인사이트 도출"""
        
        insights = []
        
        # 투자자별 행동 패턴
        for investor, transactions in analysis_result["transaction_analysis"].items():
            if len(transactions) >= 10:
                insights.append({
                    "type": "HIGH_ACTIVITY",
                    "investor": investor,
                    "transaction_count": len(transactions),
                    "total_amount": sum(tx["amount"] for tx in transactions),
                    "interpretation": f"{investor} 투자자의 활발한 거래 감지"
                })
        
        # 이상 거래 패턴
        for anomaly_type, count in analysis_result["anomaly_summary"].items():
            if count > 5:
                insights.append({
                    "type": "FREQUENT_ANOMALY",
                    "anomaly_type": anomaly_type,
                    "count": count,
                    "interpretation": f"{anomaly_type} 유형의 이상 거래 빈발"
                })
        
        # 스마트머니 움직임
        high_confidence_signals = [
            s for s in analysis_result["smart_money_signals"] 
            if s["confidence"] > 8.0
        ]
        if high_confidence_signals:
            insights.append({
                "type": "SMART_MONEY_ACTIVITY",
                "signal_count": len(high_confidence_signals),
                "top_stocks": Counter(s["stock"] for s in high_confidence_signals).most_common(5),
                "interpretation": "스마트머니의 집중 매수 신호 포착"
            })
        
        return insights
```

### 10.3 알림 시스템

```python
# src/utils/alerting.py
from typing import Dict, List
import asyncio
from enum import Enum

class AlertLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class InvestorAlertSystem:
    """투자자 동향 알림 시스템"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self.alert_rules = self._initialize_alert_rules()
        self.alert_history = []
        
    def _initialize_alert_rules(self) -> Dict:
        """알림 규칙 초기화"""
        return {
            "massive_foreign_selling": {
                "condition": lambda data: data.get("foreign_net", 0) < -100000000000,  # -1000억
                "level": AlertLevel.CRITICAL,
                "message": "외국인 대규모 순매도 감지: {amount}억원"
            },
            "institution_accumulation": {
                "condition": lambda data: data.get("institution_net", 0) > 50000000000,  # 500억
                "level": AlertLevel.WARNING,
                "message": "기관 대규모 순매수 감지: {amount}억원"
            },
            "smart_money_signal": {
                "condition": lambda data: data.get("smart_money_confidence", 0) > 8.5,
                "level": AlertLevel.INFO,
                "message": "스마트머니 신호 감지: {stock} (신뢰도: {confidence})"
            },
            "flow_reversal": {
                "condition": lambda data: data.get("flow_reversal", False),
                "level": AlertLevel.WARNING,
                "message": "투자자 매매 방향 전환 감지: {investor_type}"
            }
        }
    
    async def check_alerts(self, market_data: Dict) -> List[Dict]:
        """알림 조건 체크"""
        triggered_alerts = []
        
        for rule_name, rule in self.alert_rules.items():
            if rule["condition"](market_data):
                alert = {
                    "timestamp": datetime.now(),
                    "rule": rule_name,
                    "level": rule["level"],
                    "message": self._format_message(rule["message"], market_data),
                    "data": market_data
                }
                
                triggered_alerts.append(alert)
                await self._send_alert(alert)
        
        # 알림 이력 저장
        self.alert_history.extend(triggered_alerts)
        
        return triggered_alerts
    
    async def _send_alert(self, alert: Dict):
        """알림 전송"""
        if alert["level"] == AlertLevel.CRITICAL:
            # 긴급 알림 (SMS, 전화 등)
            await self._send_critical_alert(alert)
        elif alert["level"] == AlertLevel.WARNING:
            # 경고 알림 (이메일, Slack 등)
            await self._send_warning_alert(alert)
        else:
            # 정보성 알림 (로그, 대시보드 등)
            await self._log_info_alert(alert)
    
    def generate_alert_summary(self, period: timedelta) -> Dict:
        """알림 요약 생성"""
        cutoff_time = datetime.now() - period
        recent_alerts = [
            a for a in self.alert_history 
            if a["timestamp"] > cutoff_time
        ]
        
        summary = {
            "period": period,
            "total_alerts": len(recent_alerts),
            "by_level": Counter(a["level"].value for a in recent_alerts),
            "by_rule": Counter(a["rule"] for a in recent_alerts),
            "critical_alerts": [
                a for a in recent_alerts 
                if a["level"] == AlertLevel.CRITICAL
            ],
            "trends": self._analyze_alert_trends(recent_alerts)
        }
        
        return summary
```

## 11. 보안 고려사항

### 11.1 API 보안
- API 키 암호화 저장 (환경변수 + KMS)
- Rate limiting 구현
- IP 화이트리스트
- API 호출 감사 로그

### 11.2 데이터 보안
- 민감 정보 마스킹
- 데이터베이스 암호화 (at rest)
- SSL/TLS 통신
- 정기적 보안 감사

### 11.3 접근 제어
- Role-based access control (RBAC)
- 도구별 권한 관리
- 세션 관리 및 타임아웃
- 2차 인증 (2FA)

## 12. 성능 최적화 전략

### 12.1 쿼리 최적화
- 적절한 인덱스 설계
- 파티셔닝 전략 (일별/월별)
- 쿼리 실행 계획 분석
- 연결 풀링

### 12.2 캐싱 전략
- 다층 캐싱 (메모리 + Redis)
- 캐시 워밍업
- 캐시 무효화 전략
- TTL 최적화

### 12.3 비동기 처리
- 논블로킹 I/O
- 배치 처리
- 작업 큐 활용
- 병렬 처리

이 계획서를 통해 투자자별 매매 동향을 정확하고 신속하게 분석할 수 있는 MCP 서버를 구축할 수 있습니다.