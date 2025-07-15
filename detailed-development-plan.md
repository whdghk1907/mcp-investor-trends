# 🏦 투자자 동향 MCP 서버 상세 개발계획서

## 📋 프로젝트 개요

### 목표
한국 주식시장의 투자자별(외국인/기관/개인) 매매 동향을 실시간으로 추적하고 분석하는 고성능 MCP 서버 구축

### 핵심 가치 제안
- **실시간 분석**: 투자자별 매매 동향 실시간 모니터링
- **스마트머니 추적**: 고도화된 알고리즘으로 스마트머니 흐름 감지
- **패턴 인식**: ML 기반 투자자 행동 패턴 분석
- **액션 인사이트**: 실행 가능한 투자 시그널 제공

---

## 🎯 Phase 1: 기반 구조 설정 (4일)

### Day 1: 프로젝트 초기화 및 환경 설정

#### 1.1 개발 환경 구성
```bash
# 프로젝트 구조 생성
mkdir -p src/{tools,api,analysis,utils}
mkdir -p tests/{unit,integration}
mkdir -p docs/{api,deployment}
mkdir -p config/{dev,prod}
```

#### 1.2 의존성 설정
**requirements.txt 핵심 라이브러리**
```
# MCP 기본
mcp>=0.1.0

# 비동기 처리
asyncio>=3.4.3
aiohttp>=3.8.0
uvloop>=0.17.0

# 데이터 처리
pandas>=2.0.0
numpy>=1.24.0
pytz>=2023.3

# 시계열 분석
statsmodels>=0.14.0
scikit-learn>=1.3.0

# 데이터베이스
asyncpg>=0.28.0
redis>=4.5.0

# API 클라이언트
requests>=2.31.0
websocket-client>=1.6.0

# 로깅 및 모니터링
structlog>=23.1.0
prometheus-client>=0.17.0

# 보안
cryptography>=41.0.0
python-jose>=3.3.0
```

#### 1.3 환경 변수 구성
**.env.example**
```
# API 설정
KOREA_INVESTMENT_APP_KEY=your_app_key
KOREA_INVESTMENT_APP_SECRET=your_app_secret
EBEST_APP_KEY=your_ebest_key
EBEST_APP_SECRET=your_ebest_secret

# 데이터베이스
DATABASE_URL=postgresql://user:pass@localhost:5432/investor_trends
REDIS_URL=redis://localhost:6379/0

# 캐싱 설정
CACHE_TTL_REALTIME=10
CACHE_TTL_MINUTE=60
CACHE_TTL_HOURLY=3600
CACHE_TTL_DAILY=86400

# 분석 설정
SMART_MONEY_THRESHOLD=1000000000
LARGE_ORDER_THRESHOLD=500000000
ANOMALY_DETECTION_SENSITIVITY=2.5

# 로깅
LOG_LEVEL=INFO
LOG_FORMAT=json

# 보안
SECRET_KEY=your_secret_key
TOKEN_EXPIRE_HOURS=24
```

### Day 2: 기본 MCP 서버 구조 구현

#### 2.1 MCP 서버 메인 클래스
**src/server.py**
```python
import asyncio
from typing import Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent

from .tools.investor_tools import InvestorTools
from .tools.program_tools import ProgramTools
from .tools.ownership_tools import OwnershipTools
from .tools.analysis_tools import AnalysisTools
from .config import Config
from .utils.logger import setup_logger

class InvestorTrendsMCPServer:
    def __init__(self):
        self.server = Server("investor-trends")
        self.config = Config()
        self.logger = setup_logger()
        
        # 도구 인스턴스 초기화
        self.investor_tools = InvestorTools(self.config)
        self.program_tools = ProgramTools(self.config)
        self.ownership_tools = OwnershipTools(self.config)
        self.analysis_tools = AnalysisTools(self.config)
        
        self._register_tools()
        self._setup_handlers()
    
    def _register_tools(self):
        """MCP 도구 등록"""
        tools = [
            # 투자자 매매 동향
            Tool(
                name="get_investor_trading",
                description="투자자별 매매 동향 조회",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stock_code": {"type": "string", "description": "종목 코드"},
                        "investor_type": {
                            "type": "string", 
                            "enum": ["FOREIGN", "INSTITUTION", "INDIVIDUAL", "ALL"],
                            "default": "ALL"
                        },
                        "period": {
                            "type": "string",
                            "enum": ["1D", "5D", "20D", "60D"],
                            "default": "1D"
                        },
                        "market": {
                            "type": "string",
                            "enum": ["ALL", "KOSPI", "KOSDAQ"],
                            "default": "ALL"
                        }
                    }
                }
            ),
            # 프로그램 매매
            Tool(
                name="get_program_trading",
                description="프로그램 매매 동향 조회",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "market": {
                            "type": "string",
                            "enum": ["KOSPI", "KOSDAQ", "ALL"],
                            "default": "ALL"
                        },
                        "program_type": {
                            "type": "string",
                            "enum": ["ALL", "ARBITRAGE", "NON_ARBITRAGE"],
                            "default": "ALL"
                        }
                    }
                }
            ),
            # 스마트머니 추적
            Tool(
                name="get_smart_money_tracker",
                description="스마트머니 움직임 추적",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "detection_method": {
                            "type": "string",
                            "enum": ["LARGE_ORDERS", "INSTITUTION_CLUSTER", "FOREIGN_SURGE"],
                            "default": "LARGE_ORDERS"
                        },
                        "min_confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 10,
                            "default": 7.0
                        }
                    }
                }
            )
        ]
        
        for tool in tools:
            self.server.register_tool(tool)
    
    async def run(self):
        """서버 실행"""
        await self.server.run()

if __name__ == "__main__":
    server = InvestorTrendsMCPServer()
    asyncio.run(server.run())
```

#### 2.2 설정 관리
**src/config.py**
```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    url: str
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30

@dataclass
class CacheConfig:
    redis_url: str
    ttl_realtime: int = 10
    ttl_minute: int = 60
    ttl_hourly: int = 3600
    ttl_daily: int = 86400

@dataclass
class APIConfig:
    korea_investment_key: str
    korea_investment_secret: str
    ebest_key: str
    ebest_secret: str
    rate_limit_per_minute: int = 200

@dataclass
class AnalysisConfig:
    smart_money_threshold: int = 1000000000
    large_order_threshold: int = 500000000
    anomaly_sensitivity: float = 2.5
    pattern_confidence_threshold: float = 0.7

class Config:
    def __init__(self):
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "postgresql://localhost/investor_trends")
        )
        
        self.cache = CacheConfig(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            ttl_realtime=int(os.getenv("CACHE_TTL_REALTIME", "10")),
            ttl_minute=int(os.getenv("CACHE_TTL_MINUTE", "60")),
            ttl_hourly=int(os.getenv("CACHE_TTL_HOURLY", "3600")),
            ttl_daily=int(os.getenv("CACHE_TTL_DAILY", "86400"))
        )
        
        self.api = APIConfig(
            korea_investment_key=os.getenv("KOREA_INVESTMENT_APP_KEY", ""),
            korea_investment_secret=os.getenv("KOREA_INVESTMENT_APP_SECRET", ""),
            ebest_key=os.getenv("EBEST_APP_KEY", ""),
            ebest_secret=os.getenv("EBEST_APP_SECRET", "")
        )
        
        self.analysis = AnalysisConfig(
            smart_money_threshold=int(os.getenv("SMART_MONEY_THRESHOLD", "1000000000")),
            large_order_threshold=int(os.getenv("LARGE_ORDER_THRESHOLD", "500000000")),
            anomaly_sensitivity=float(os.getenv("ANOMALY_DETECTION_SENSITIVITY", "2.5"))
        )
```

### Day 3: API 클라이언트 기본 구현

#### 3.1 한국투자증권 API 클라이언트
**src/api/korea_investment.py**
```python
import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import hmac
import base64

class KoreaInvestmentAPI:
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self._get_access_token()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _get_access_token(self):
        """액세스 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        async with self.session.post(url, json=data) as response:
            result = await response.json()
            self.access_token = result.get("access_token")
    
    async def get_investor_trading(
        self, 
        stock_code: Optional[str] = None,
        market: str = "ALL"
    ) -> Dict:
        """투자자별 매매 동향 조회"""
        
        headers = {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST130200000" if stock_code else "FHKST130100000"
        }
        
        params = {}
        if stock_code:
            params["fid_cond_mrkt_div_code"] = "J"
            params["fid_input_iscd"] = stock_code
        else:
            params["fid_cond_mrkt_div_code"] = market
            
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/investor-trading"
        
        async with self.session.get(url, headers=headers, params=params) as response:
            return await response.json()
    
    async def get_program_trading(self, market: str = "ALL") -> Dict:
        """프로그램 매매 동향 조회"""
        
        headers = {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST130300000"
        }
        
        params = {
            "fid_cond_mrkt_div_code": market,
            "fid_input_date_1": datetime.now().strftime("%Y%m%d")
        }
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/program-trading"
        
        async with self.session.get(url, headers=headers, params=params) as response:
            return await response.json()
```

#### 3.2 데이터 모델 정의
**src/api/models.py**
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
from decimal import Decimal

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

@dataclass
class StockInfo:
    """종목 정보 모델"""
    code: str
    name: str
    current_price: int
    change_rate: float
    market_cap: Optional[int] = None
    sector: Optional[str] = None

@dataclass
class InvestorTradingData:
    """투자자 매매 데이터 종합 모델"""
    timestamp: datetime
    scope: str  # MARKET, STOCK
    stock_info: Optional[StockInfo]
    foreign: InvestorData
    institution: InvestorData
    individual: InvestorData
    program: Dict
    market_impact: Dict
    
@dataclass
class SmartMoneySignal:
    """스마트머니 신호 모델"""
    stock_code: str
    stock_name: str
    signal_type: str
    confidence: float
    detection_details: Dict
    metrics: Dict
    technical_context: Dict
    timestamp: datetime

@dataclass
class ProgramTradingData:
    """프로그램 매매 데이터 모델"""
    timestamp: datetime
    market: str
    total_buy: int
    total_sell: int
    net_value: int
    arbitrage_data: Dict
    non_arbitrage_data: Dict
    market_indicators: Dict
```

### Day 4: 데이터베이스 설계 및 기본 연결

#### 4.1 데이터베이스 스키마 구현
**database/schema.sql**
```sql
-- 투자자 거래 데이터 테이블
CREATE TABLE investor_trading (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(10),
    market VARCHAR(10) NOT NULL,
    
    -- 외국인 데이터
    foreign_buy BIGINT DEFAULT 0,
    foreign_sell BIGINT DEFAULT 0,
    foreign_net BIGINT DEFAULT 0,
    foreign_buy_volume BIGINT DEFAULT 0,
    foreign_sell_volume BIGINT DEFAULT 0,
    
    -- 기관 데이터
    institution_buy BIGINT DEFAULT 0,
    institution_sell BIGINT DEFAULT 0,
    institution_net BIGINT DEFAULT 0,
    institution_buy_volume BIGINT DEFAULT 0,
    institution_sell_volume BIGINT DEFAULT 0,
    
    -- 개인 데이터
    individual_buy BIGINT DEFAULT 0,
    individual_sell BIGINT DEFAULT 0,
    individual_net BIGINT DEFAULT 0,
    individual_buy_volume BIGINT DEFAULT 0,
    individual_sell_volume BIGINT DEFAULT 0,
    
    -- 프로그램 데이터
    program_buy BIGINT DEFAULT 0,
    program_sell BIGINT DEFAULT 0,
    program_net BIGINT DEFAULT 0,
    
    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- TimescaleDB 하이퍼테이블 생성
SELECT create_hypertable('investor_trading', 'timestamp', if_not_exists => TRUE);

-- 인덱스 생성
CREATE INDEX idx_investor_trading_stock_time ON investor_trading (stock_code, timestamp DESC);
CREATE INDEX idx_investor_trading_market_time ON investor_trading (market, timestamp DESC);
CREATE INDEX idx_investor_trading_foreign_net ON investor_trading (foreign_net);
CREATE INDEX idx_investor_trading_institution_net ON investor_trading (institution_net);

-- 기관 투자자 세부 데이터
CREATE TABLE institution_detail (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(10),
    institution_type VARCHAR(50) NOT NULL,
    buy_amount BIGINT DEFAULT 0,
    sell_amount BIGINT DEFAULT 0,
    net_amount BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('institution_detail', 'timestamp', if_not_exists => TRUE);

-- 스마트머니 신호 테이블
CREATE TABLE smart_money_signals (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    signal_type VARCHAR(50) NOT NULL,
    confidence DECIMAL(3,1) NOT NULL,
    amount BIGINT,
    investor_type VARCHAR(20),
    detection_method VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_smart_money_timestamp ON smart_money_signals (timestamp DESC);
CREATE INDEX idx_smart_money_stock ON smart_money_signals (stock_code);
CREATE INDEX idx_smart_money_confidence ON smart_money_signals (confidence DESC);
```

#### 4.2 데이터베이스 연결 클래스
**src/utils/database.py**
```python
import asyncpg
import asyncio
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import logging

class DatabaseManager:
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
                min_size=5,
                max_size=self.pool_size,
                command_timeout=60
            )
            self.logger.info("Database pool initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """데이터베이스 풀 종료"""
        if self.pool:
            await self.pool.close()
    
    @asynccontextmanager
    async def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        async with self.pool.acquire() as connection:
            yield connection
    
    async def insert_investor_trading(self, data: Dict) -> None:
        """투자자 거래 데이터 삽입"""
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
        
        async with self.get_connection() as conn:
            await conn.execute(query, *data.values())
    
    async def get_investor_trading_history(
        self,
        stock_code: Optional[str] = None,
        market: str = "ALL",
        hours: int = 24
    ) -> List[Dict]:
        """투자자 거래 이력 조회"""
        
        where_conditions = ["timestamp >= NOW() - INTERVAL '%s hours'" % hours]
        params = []
        
        if stock_code:
            where_conditions.append("stock_code = $%d" % (len(params) + 1))
            params.append(stock_code)
            
        if market != "ALL":
            where_conditions.append("market = $%d" % (len(params) + 1))
            params.append(market)
        
        query = f"""
        SELECT * FROM investor_trading
        WHERE {' AND '.join(where_conditions)}
        ORDER BY timestamp DESC
        LIMIT 1000
        """
        
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
```

---

## 🚀 Phase 2: 핵심 기능 구현 (6일)

### Day 5-6: 투자자 매매 동향 도구 구현

#### 5.1 투자자 매매 도구 핵심 로직
**src/tools/investor_tools.py**
```python
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ..api.korea_investment import KoreaInvestmentAPI
from ..api.models import InvestorTradingData, InvestorData, StockInfo
from ..utils.database import DatabaseManager
from ..utils.cache import CacheManager
from ..utils.calculator import TradingCalculator

class InvestorTools:
    def __init__(self, config):
        self.config = config
        self.db_manager = DatabaseManager(config.database.url)
        self.cache_manager = CacheManager(config.cache.redis_url)
        self.calculator = TradingCalculator()
        
    async def get_investor_trading(
        self,
        stock_code: Optional[str] = None,
        investor_type: str = "ALL",
        period: str = "1D",
        market: str = "ALL",
        include_details: bool = True
    ) -> Dict:
        """투자자별 매매 동향 조회"""
        
        # 캐시 키 생성
        cache_key = f"investor:trading:{stock_code or 'market'}:{investor_type}:{period}:{market}"
        
        # 캐시 확인
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # 1. API에서 실시간 데이터 조회
            api_data = await self._fetch_api_data(stock_code, market)
            
            # 2. 히스토리컬 데이터 조회
            historical_data = await self._fetch_historical_data(stock_code, market, period)
            
            # 3. 데이터 통합 및 분석
            result = await self._analyze_investor_data(
                api_data, historical_data, investor_type, include_details
            )
            
            # 4. 캐시 저장
            await self.cache_manager.set(
                cache_key, 
                result, 
                ttl=self.config.cache.ttl_minute
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in get_investor_trading: {e}")
            raise
    
    async def _fetch_api_data(self, stock_code: Optional[str], market: str) -> Dict:
        """API에서 실시간 데이터 조회"""
        
        async with KoreaInvestmentAPI(
            self.config.api.korea_investment_key,
            self.config.api.korea_investment_secret
        ) as api:
            if stock_code:
                return await api.get_investor_trading(stock_code=stock_code)
            else:
                return await api.get_investor_trading(market=market)
    
    async def _fetch_historical_data(
        self, 
        stock_code: Optional[str], 
        market: str, 
        period: str
    ) -> List[Dict]:
        """히스토리컬 데이터 조회"""
        
        # 기간별 시간 설정
        period_hours = {
            "1D": 24,
            "5D": 120,
            "20D": 480,
            "60D": 1440
        }
        
        hours = period_hours.get(period, 24)
        
        return await self.db_manager.get_investor_trading_history(
            stock_code=stock_code,
            market=market,
            hours=hours
        )
    
    async def _analyze_investor_data(
        self,
        api_data: Dict,
        historical_data: List[Dict],
        investor_type: str,
        include_details: bool
    ) -> Dict:
        """투자자 데이터 분석"""
        
        # DataFrame 변환
        df = pd.DataFrame(historical_data) if historical_data else pd.DataFrame()
        
        # 분석 결과 구조
        result = {
            "timestamp": datetime.now().isoformat(),
            "scope": "STOCK" if api_data.get("stock_code") else "MARKET",
            "investor_data": {},
            "market_impact": {},
            "historical_comparison": {}
        }
        
        # 종목 정보 (개별 종목인 경우)
        if result["scope"] == "STOCK":
            result["stock_info"] = self._extract_stock_info(api_data)
        
        # 투자자별 데이터 분석
        investors = ["foreign", "institution", "individual"] if investor_type == "ALL" else [investor_type.lower()]
        
        for investor in investors:
            result["investor_data"][investor] = await self._analyze_single_investor(
                api_data, df, investor, include_details
            )
        
        # 프로그램 매매 데이터
        if "program" in api_data:
            result["investor_data"]["program"] = self._extract_program_data(api_data)
        
        # 시장 영향도 분석
        if include_details:
            result["market_impact"] = self._calculate_market_impact(api_data, df)
            result["historical_comparison"] = self._compare_with_history(api_data, df)
        
        return result
    
    async def _analyze_single_investor(
        self,
        api_data: Dict,
        df: pd.DataFrame,
        investor: str,
        include_details: bool
    ) -> Dict:
        """개별 투자자 분석"""
        
        # 현재 데이터 추출
        current_data = self._extract_current_investor_data(api_data, investor)
        
        # 기본 메트릭 계산
        result = {
            "buy_amount": current_data.get("buy_amount", 0),
            "sell_amount": current_data.get("sell_amount", 0),
            "net_amount": current_data.get("net_amount", 0),
            "buy_volume": current_data.get("buy_volume", 0),
            "sell_volume": current_data.get("sell_volume", 0),
            "net_volume": current_data.get("net_volume", 0),
            "average_buy_price": self.calculator.safe_divide(
                current_data.get("buy_amount", 0),
                current_data.get("buy_volume", 0)
            ),
            "average_sell_price": self.calculator.safe_divide(
                current_data.get("sell_amount", 0),
                current_data.get("sell_volume", 0)
            )
        }
        
        # 추가 분석 (히스토리 데이터가 있는 경우)
        if include_details and not df.empty:
            result.update({
                "net_ratio": self._calculate_net_ratio(current_data),
                "trend": self._determine_trend(df, investor),
                "intensity": self._calculate_intensity(df, investor),
                "consistency": self._calculate_consistency(df, investor),
                "momentum": self._calculate_momentum(df, investor)
            })
            
            # 기관 투자자 세부 분석
            if investor == "institution":
                result["sub_categories"] = await self._analyze_institution_subcategories(api_data)
        
        return result
    
    def _calculate_net_ratio(self, data: Dict) -> float:
        """순매수 비율 계산"""
        buy_amount = data.get("buy_amount", 0)
        sell_amount = data.get("sell_amount", 0)
        total_amount = buy_amount + sell_amount
        
        if total_amount == 0:
            return 0.0
        
        return (buy_amount / total_amount) * 100
    
    def _determine_trend(self, df: pd.DataFrame, investor: str) -> str:
        """투자자 트렌드 판정"""
        if df.empty or len(df) < 5:
            return "NEUTRAL"
        
        recent_net = df[f"{investor}_net"].tail(5)
        
        # 연속 순매수/순매도 확인
        consecutive_buy = (recent_net > 0).all()
        consecutive_sell = (recent_net < 0).all()
        
        if consecutive_buy:
            return "ACCUMULATING"
        elif consecutive_sell:
            return "DISTRIBUTING"
        else:
            # 트렌드 기울기로 판정
            slope = np.polyfit(range(len(recent_net)), recent_net, 1)[0]
            if slope > 0:
                return "ACCUMULATING"
            elif slope < 0:
                return "DISTRIBUTING"
            else:
                return "NEUTRAL"
    
    def _calculate_intensity(self, df: pd.DataFrame, investor: str) -> float:
        """매매 강도 계산 (1-10 스케일)"""
        if df.empty:
            return 5.0
        
        # 거래량 기준 강도 계산
        recent_volume = df[f"{investor}_buy_volume"].tail(5).sum() + df[f"{investor}_sell_volume"].tail(5).sum()
        avg_volume = (df[f"{investor}_buy_volume"].mean() + df[f"{investor}_sell_volume"].mean()) * 5
        
        if avg_volume == 0:
            return 5.0
        
        intensity_ratio = recent_volume / avg_volume
        
        # 1-10 스케일로 정규화
        return min(10.0, max(1.0, intensity_ratio * 5))
    
    def _calculate_market_impact(self, api_data: Dict, df: pd.DataFrame) -> Dict:
        """시장 영향도 분석"""
        
        if df.empty or len(df) < 2:
            return {
                "price_correlation": 0.0,
                "volume_contribution": 0.0,
                "momentum_score": 0.0
            }
        
        # 가격 상관관계 (외국인 순매수와 가격 변동)
        foreign_net = df["foreign_net"]
        price_changes = df["close"].pct_change() if "close" in df.columns else pd.Series([0] * len(df))
        
        price_correlation = foreign_net.corr(price_changes) if len(foreign_net) > 1 else 0.0
        
        # 거래량 기여도
        total_volume = df["foreign_buy_volume"].sum() + df["foreign_sell_volume"].sum()
        market_volume = df["total_volume"].sum() if "total_volume" in df.columns else total_volume * 3
        volume_contribution = (total_volume / market_volume * 100) if market_volume > 0 else 0.0
        
        # 모멘텀 점수
        momentum_score = self._calculate_momentum_score(df)
        
        return {
            "price_correlation": round(price_correlation, 2),
            "volume_contribution": round(volume_contribution, 1),
            "momentum_score": round(momentum_score, 1)
        }
```

### Day 7-8: 프로그램 매매 및 보유비중 도구

#### 7.1 프로그램 매매 도구
**src/tools/program_tools.py**
```python
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

class ProgramTools:
    def __init__(self, config):
        self.config = config
        self.api_clients = self._initialize_api_clients()
        
    async def get_program_trading(
        self,
        market: str = "ALL",
        program_type: str = "ALL",
        time_window: str = "CURRENT"
    ) -> Dict:
        """프로그램 매매 동향 조회"""
        
        cache_key = f"program:trading:{market}:{program_type}:{time_window}"
        
        # 캐시 확인
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # API 데이터 조회
            api_data = await self._fetch_program_data(market, time_window)
            
            # 데이터 분석 및 가공
            result = await self._analyze_program_data(api_data, program_type, time_window)
            
            # 캐시 저장
            await self.cache_manager.set(cache_key, result, ttl=30)  # 30초 캐시
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in get_program_trading: {e}")
            raise
    
    async def _analyze_program_data(
        self,
        api_data: Dict,
        program_type: str,
        time_window: str
    ) -> Dict:
        """프로그램 매매 데이터 분석"""
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "market": api_data.get("market", "ALL"),
            "program_trading": {
                "summary": self._calculate_program_summary(api_data),
                "arbitrage": self._extract_arbitrage_data(api_data),
                "non_arbitrage": self._extract_non_arbitrage_data(api_data),
                "time_series": self._build_time_series(api_data, time_window),
                "top_stocks": self._identify_top_program_stocks(api_data),
                "market_indicators": self._calculate_market_indicators(api_data)
            }
        }
        
        return result
    
    def _calculate_program_summary(self, data: Dict) -> Dict:
        """프로그램 매매 요약 계산"""
        
        total_buy = data.get("total_program_buy", 0)
        total_sell = data.get("total_program_sell", 0)
        net_value = total_buy - total_sell
        
        total_trading = total_buy + total_sell
        buy_ratio = (total_buy / total_trading * 100) if total_trading > 0 else 50.0
        
        # 시장 영향도 계산
        market_volume = data.get("total_market_volume", total_trading * 5)  # 추정
        market_impact = (total_trading / market_volume * 100) if market_volume > 0 else 0.0
        
        return {
            "total_buy": total_buy,
            "total_sell": total_sell,
            "net_value": net_value,
            "buy_ratio": round(buy_ratio, 1),
            "market_impact": round(market_impact, 1)
        }
    
    def _extract_arbitrage_data(self, data: Dict) -> Dict:
        """차익거래 데이터 추출"""
        
        arb_buy = data.get("arbitrage_buy", 0)
        arb_sell = data.get("arbitrage_sell", 0)
        
        # 베이시스 계산 (선물-현물 가격차)
        basis = data.get("futures_basis", 0)
        
        # 선물 포지션 추정
        futures_position = "LONG" if arb_buy > arb_sell else "SHORT" if arb_sell > arb_buy else "NEUTRAL"
        
        # 차익거래 강도
        arb_volume = arb_buy + arb_sell
        intensity = "HIGH" if arb_volume > 1e11 else "MEDIUM" if arb_volume > 5e10 else "LOW"
        
        return {
            "buy": arb_buy,
            "sell": arb_sell,
            "net": arb_buy - arb_sell,
            "basis": round(basis, 1),
            "futures_position": futures_position,
            "intensity": intensity
        }
```

#### 7.2 보유비중 추적 도구
**src/tools/ownership_tools.py**
```python
class OwnershipTools:
    def __init__(self, config):
        self.config = config
        
    async def get_ownership_changes(
        self,
        stock_code: str,
        investor_type: str = "ALL",
        period: str = "3M",
        threshold: float = 1.0
    ) -> Dict:
        """투자자별 보유 비중 변화 추적"""
        
        cache_key = f"ownership:{stock_code}:{investor_type}:{period}"
        
        try:
            # 보유비중 데이터 조회
            ownership_data = await self._fetch_ownership_data(stock_code, period)
            
            # 변화 분석
            result = await self._analyze_ownership_changes(
                ownership_data, stock_code, investor_type, threshold
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in get_ownership_changes: {e}")
            raise
    
    async def _analyze_ownership_changes(
        self,
        ownership_data: List[Dict],
        stock_code: str,
        investor_type: str,
        threshold: float
    ) -> Dict:
        """보유비중 변화 분석"""
        
        if not ownership_data:
            return {"error": "No ownership data available"}
        
        # 최신 데이터
        latest = ownership_data[0]
        
        # 변화 계산
        changes = self._calculate_ownership_changes(ownership_data, threshold)
        
        # 히스토리컬 데이터 구성
        historical = self._build_ownership_history(ownership_data)
        
        # 마일스톤 이벤트 식별
        milestones = self._identify_ownership_milestones(ownership_data)
        
        # 상관관계 분석
        correlation = self._analyze_ownership_correlation(ownership_data, stock_code)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "stock_info": {
                "code": stock_code,
                "name": latest.get("stock_name", ""),
                "market_cap": latest.get("market_cap", 0)
            },
            "ownership_data": {
                "current": self._extract_current_ownership(latest),
                "changes": changes,
                "historical": historical,
                "milestones": milestones
            },
            "correlation_analysis": correlation
        }
        
        return result
    
    def _calculate_ownership_changes(self, data: List[Dict], threshold: float) -> Dict:
        """보유비중 변화 계산"""
        
        if len(data) < 2:
            return {}
        
        latest = data[0]
        previous = data[-1]  # 가장 오래된 데이터
        
        changes = {}
        
        for investor_type in ["foreign", "institution", "individual"]:
            current_pct = latest.get(f"{investor_type}_ownership_pct", 0)
            previous_pct = previous.get(f"{investor_type}_ownership_pct", 0)
            
            pct_change = current_pct - previous_pct
            
            if abs(pct_change) >= threshold:
                # 연속일 계산
                consecutive_days = self._calculate_consecutive_days(data, investor_type)
                
                changes[investor_type] = {
                    "shares_change": latest.get(f"{investor_type}_shares", 0) - previous.get(f"{investor_type}_shares", 0),
                    "percentage_change": round(pct_change, 2),
                    "value_change": self._calculate_value_change(latest, previous, investor_type),
                    "trend": "INCREASING" if pct_change > 0 else "DECREASING",
                    "consecutive_days": consecutive_days
                }
        
        return changes
```

### Day 9-10: 스마트머니 추적 및 분석 엔진

#### 9.1 스마트머니 추적기 핵심 구현
**src/analysis/smart_money.py**
```python
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

class SmartMoneyTracker:
    def __init__(self, config):
        self.config = config
        self.smart_money_threshold = config.analysis.smart_money_threshold
        self.large_order_threshold = config.analysis.large_order_threshold
        
    async def track_smart_money(
        self,
        detection_method: str = "LARGE_ORDERS",
        market: str = "ALL",
        min_confidence: float = 7.0,
        count: int = 20
    ) -> Dict:
        """스마트머니 추적"""
        
        try:
            # 1. 원시 데이터 수집
            raw_data = await self._collect_raw_data(market)
            
            # 2. 감지 방법별 분석
            signals = await self._detect_smart_money_signals(
                raw_data, detection_method, min_confidence
            )
            
            # 3. 시장 스마트머니 지수 계산
            market_index = self._calculate_market_smart_money_index(signals)
            
            # 4. 기관 포지셔닝 분석
            institutional_positioning = self._analyze_institutional_positioning(raw_data)
            
            # 5. 결과 구성
            result = {
                "timestamp": datetime.now().isoformat(),
                "smart_money_signals": signals[:count],
                "market_smart_money_index": market_index,
                "institutional_positioning": institutional_positioning,
                "detection_method": detection_method,
                "total_signals_found": len(signals)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in track_smart_money: {e}")
            raise
    
    async def _detect_smart_money_signals(
        self,
        raw_data: Dict,
        detection_method: str,
        min_confidence: float
    ) -> List[Dict]:
        """스마트머니 신호 감지"""
        
        signals = []
        
        if detection_method == "LARGE_ORDERS":
            signals.extend(await self._detect_large_block_orders(raw_data))
        elif detection_method == "INSTITUTION_CLUSTER":
            signals.extend(await self._detect_institutional_clustering(raw_data))
        elif detection_method == "FOREIGN_SURGE":
            signals.extend(await self._detect_foreign_surge_patterns(raw_data))
        else:
            # 모든 방법 적용
            signals.extend(await self._detect_large_block_orders(raw_data))
            signals.extend(await self._detect_institutional_clustering(raw_data))
            signals.extend(await self._detect_foreign_surge_patterns(raw_data))
        
        # 신뢰도 필터링 및 정렬
        filtered_signals = [s for s in signals if s["confidence"] >= min_confidence]
        return sorted(filtered_signals, key=lambda x: x["confidence"], reverse=True)
    
    async def _detect_large_block_orders(self, data: Dict) -> List[Dict]:
        """대형 블록 주문 감지"""
        
        signals = []
        
        for stock_code, stock_data in data.items():
            if not isinstance(stock_data, dict):
                continue
                
            # 대형 거래 식별
            large_trades = self._identify_large_trades(stock_data)
            
            if len(large_trades) >= 3:  # 최소 3건 이상의 대형 거래
                
                # 신뢰도 계산
                confidence = self._calculate_block_trade_confidence(large_trades, stock_data)
                
                if confidence >= 5.0:  # 최소 신뢰도
                    
                    signal = {
                        "stock_code": stock_code,
                        "stock_name": stock_data.get("name", ""),
                        "signal_type": "LARGE_BLOCK_ACCUMULATION",
                        "confidence": confidence,
                        "detection_details": {
                            "large_block_trades": len(large_trades),
                            "average_block_size": np.mean([t["amount"] for t in large_trades]),
                            "institutional_buyers": self._identify_institutional_buyers(large_trades),
                            "accumulation_period": self._calculate_accumulation_period(large_trades),
                            "price_impact": self._calculate_price_impact(large_trades, stock_data)
                        },
                        "metrics": self._calculate_block_trade_metrics(large_trades, stock_data),
                        "technical_context": self._get_technical_context(stock_data),
                        "similar_patterns": await self._find_similar_patterns(stock_code, large_trades)
                    }
                    
                    signals.append(signal)
        
        return signals
    
    def _calculate_block_trade_confidence(self, large_trades: List[Dict], stock_data: Dict) -> float:
        """블록 거래 신뢰도 계산"""
        
        # 기본 점수
        base_score = 5.0
        
        # 거래 건수 가산점
        trade_count_bonus = min(len(large_trades) * 0.5, 3.0)
        
        # 평균 거래 규모 가산점
        avg_size = np.mean([t["amount"] for t in large_trades])
        size_bonus = min((avg_size / self.large_order_threshold - 1) * 2, 2.0)
        
        # 가격 영향 최소화 가산점 (스텔스 축적)
        price_impact = self._calculate_price_impact(large_trades, stock_data)
        stealth_bonus = max(0, 2.0 - price_impact) if price_impact < 2.0 else 0
        
        # 기관 투자자 다양성 가산점
        institutional_types = set([t.get("investor_type") for t in large_trades])
        diversity_bonus = min(len(institutional_types) * 0.3, 1.0)
        
        # 시간 집중도 가산점
        time_concentration = self._calculate_time_concentration(large_trades)
        timing_bonus = min(time_concentration * 0.5, 1.0)
        
        total_confidence = (
            base_score + 
            trade_count_bonus + 
            size_bonus + 
            stealth_bonus + 
            diversity_bonus + 
            timing_bonus
        )
        
        return min(total_confidence, 10.0)
    
    async def _detect_institutional_clustering(self, data: Dict) -> List[Dict]:
        """기관 투자자 클러스터링 감지"""
        
        signals = []
        
        # 기관 투자자별 매매 패턴 분석
        institutional_patterns = self._analyze_institutional_patterns(data)
        
        # 클러스터링 분석
        clusters = self._perform_institutional_clustering(institutional_patterns)
        
        for cluster in clusters:
            if cluster["signal_strength"] >= 7.0:
                
                signal = {
                    "stock_code": cluster["primary_stock"],
                    "stock_name": data.get(cluster["primary_stock"], {}).get("name", ""),
                    "signal_type": "INSTITUTIONAL_CLUSTERING",
                    "confidence": cluster["signal_strength"],
                    "detection_details": {
                        "participating_institutions": cluster["institutions"],
                        "cluster_size": len(cluster["stocks"]),
                        "coordination_score": cluster["coordination_score"],
                        "time_synchronization": cluster["time_sync"],
                        "sector_focus": cluster["sector_focus"]
                    },
                    "metrics": cluster["metrics"],
                    "technical_context": self._get_technical_context(
                        data.get(cluster["primary_stock"], {})
                    )
                }
                
                signals.append(signal)
        
        return signals
    
    def _analyze_institutional_patterns(self, data: Dict) -> Dict:
        """기관 투자자 패턴 분석"""
        
        patterns = {}
        
        for stock_code, stock_data in data.items():
            if not isinstance(stock_data, dict):
                continue
            
            # 기관별 거래 패턴 추출
            institutional_data = stock_data.get("institutional_trades", [])
            
            if institutional_data:
                patterns[stock_code] = {
                    "pension_fund_pattern": self._extract_investor_pattern(institutional_data, "pension_fund"),
                    "investment_trust_pattern": self._extract_investor_pattern(institutional_data, "investment_trust"),
                    "insurance_pattern": self._extract_investor_pattern(institutional_data, "insurance"),
                    "bank_pattern": self._extract_investor_pattern(institutional_data, "bank"),
                    "coordination_indicators": self._calculate_coordination_indicators(institutional_data)
                }
        
        return patterns
    
    def _perform_institutional_clustering(self, patterns: Dict) -> List[Dict]:
        """기관 투자자 클러스터링 수행"""
        
        if not patterns:
            return []
        
        # 특징 벡터 생성
        features = []
        stock_codes = []
        
        for stock_code, pattern in patterns.items():
            feature_vector = self._create_feature_vector(pattern)
            features.append(feature_vector)
            stock_codes.append(stock_code)
        
        if len(features) < 3:
            return []
        
        # 정규화
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # DBSCAN 클러스터링
        clustering = DBSCAN(eps=0.5, min_samples=2)
        labels = clustering.fit_predict(features_scaled)
        
        # 클러스터 분석
        clusters = []
        unique_labels = set(labels)
        
        for label in unique_labels:
            if label == -1:  # 노이즈 제외
                continue
                
            cluster_indices = [i for i, l in enumerate(labels) if l == label]
            cluster_stocks = [stock_codes[i] for i in cluster_indices]
            
            cluster_analysis = self._analyze_cluster(
                cluster_stocks, 
                {stock: patterns[stock] for stock in cluster_stocks}
            )
            
            if cluster_analysis["signal_strength"] >= 6.0:
                clusters.append(cluster_analysis)
        
        return sorted(clusters, key=lambda x: x["signal_strength"], reverse=True)
    
    def _calculate_market_smart_money_index(self, signals: List[Dict]) -> Dict:
        """시장 스마트머니 지수 계산"""
        
        if not signals:
            return {
                "current_value": 50.0,
                "trend": "NEUTRAL",
                "interpretation": "No significant smart money activity",
                "sector_focus": [],
                "risk_appetite": "NEUTRAL"
            }
        
        # 신뢰도 가중 평균
        weighted_confidence = np.average(
            [s["confidence"] for s in signals],
            weights=[s["confidence"] for s in signals]
        )
        
        # 시장 지수 계산 (0-100)
        market_index = min(weighted_confidence * 10, 100)
        
        # 트렌드 분석
        recent_signals = [s for s in signals if self._is_recent_signal(s)]
        trend = self._determine_market_trend(recent_signals)
        
        # 섹터 집중도 분석
        sector_focus = self._analyze_sector_concentration(signals)
        
        # 위험 선호도 분석
        risk_appetite = self._analyze_risk_appetite(signals)
        
        return {
            "current_value": round(market_index, 1),
            "trend": trend,
            "interpretation": self._interpret_market_index(market_index),
            "sector_focus": sector_focus[:5],  # 상위 5개 섹터
            "risk_appetite": risk_appetite
        }
```

---

## ⚡ Phase 3: 고급 기능 및 최적화 (5일)

### Day 11-12: 실시간 데이터 처리 및 분석 엔진

#### 11.1 실시간 데이터 스트리밍
**src/utils/realtime_processor.py**
```python
import asyncio
import websockets
import json
from typing import Dict, List, Callable, Optional
from datetime import datetime
import aioredis
from dataclasses import dataclass

@dataclass
class StreamingData:
    timestamp: datetime
    stock_code: str
    data_type: str  # TRADE, QUOTE, ORDER
    data: Dict

class RealTimeProcessor:
    def __init__(self, config):
        self.config = config
        self.subscribers = {}
        self.processing_queue = asyncio.Queue(maxsize=10000)
        self.redis_client = None
        self.running = False
        
    async def start(self):
        """실시간 처리 시작"""
        self.redis_client = await aioredis.from_url(self.config.cache.redis_url)
        self.running = True
        
        # 처리 태스크들 시작
        await asyncio.gather(
            self._websocket_listener(),
            self._data_processor(),
            self._anomaly_detector(),
            self._signal_generator()
        )
    
    async def _websocket_listener(self):
        """웹소켓 데이터 수신"""
        
        while self.running:
            try:
                async with websockets.connect(
                    "wss://api.example.com/realtime",
                    extra_headers={"Authorization": f"Bearer {self.access_token}"}
                ) as websocket:
                    
                    # 구독 설정
                    subscribe_msg = {
                        "action": "subscribe",
                        "channels": ["investor_trading", "program_trading", "large_orders"]
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    
                    async for message in websocket:
                        data = json.loads(message)
                        stream_data = StreamingData(
                            timestamp=datetime.now(),
                            stock_code=data.get("stock_code", ""),
                            data_type=data.get("type", "UNKNOWN"),
                            data=data
                        )
                        
                        await self.processing_queue.put(stream_data)
                        
            except Exception as e:
                self.logger.error(f"WebSocket connection error: {e}")
                await asyncio.sleep(5)  # 재연결 대기
    
    async def _data_processor(self):
        """데이터 처리 워커"""
        
        while self.running:
            try:
                # 배치 처리를 위해 여러 데이터 수집
                batch = []
                timeout = 0.1  # 100ms 대기
                
                try:
                    # 첫 번째 데이터 대기
                    first_data = await asyncio.wait_for(
                        self.processing_queue.get(), 
                        timeout=timeout
                    )
                    batch.append(first_data)
                    
                    # 추가 데이터 수집 (논블로킹)
                    while len(batch) < 100:  # 최대 100개까지 배치
                        try:
                            data = self.processing_queue.get_nowait()
                            batch.append(data)
                        except asyncio.QueueEmpty:
                            break
                            
                except asyncio.TimeoutError:
                    continue
                
                if batch:
                    await self._process_batch(batch)
                    
            except Exception as e:
                self.logger.error(f"Data processing error: {e}")
    
    async def _process_batch(self, batch: List[StreamingData]):
        """배치 데이터 처리"""
        
        # 타입별로 그룹화
        grouped_data = {}
        for data in batch:
            data_type = data.data_type
            if data_type not in grouped_data:
                grouped_data[data_type] = []
            grouped_data[data_type].append(data)
        
        # 타입별 처리
        for data_type, data_list in grouped_data.items():
            if data_type == "INVESTOR_TRADE":
                await self._process_investor_trades(data_list)
            elif data_type == "PROGRAM_TRADE":
                await self._process_program_trades(data_list)
            elif data_type == "LARGE_ORDER":
                await self._process_large_orders(data_list)
    
    async def _process_investor_trades(self, trades: List[StreamingData]):
        """투자자 거래 데이터 처리"""
        
        # 데이터베이스 저장을 위한 배치 준비
        db_records = []
        
        for trade in trades:
            data = trade.data
            
            record = {
                "timestamp": trade.timestamp,
                "stock_code": trade.stock_code,
                "foreign_buy": data.get("foreign_buy", 0),
                "foreign_sell": data.get("foreign_sell", 0),
                "institution_buy": data.get("institution_buy", 0),
                "institution_sell": data.get("institution_sell", 0),
                "individual_buy": data.get("individual_buy", 0),
                "individual_sell": data.get("individual_sell", 0)
            }
            
            db_records.append(record)
            
            # 실시간 분석
            await self._analyze_trade_real_time(trade)
        
        # 배치 저장
        if db_records:
            await self.db_manager.batch_insert_investor_trading(db_records)
    
    async def _analyze_trade_real_time(self, trade: StreamingData):
        """실시간 거래 분석"""
        
        data = trade.data
        
        # 이상 거래 감지
        anomalies = await self._detect_trade_anomalies(trade)
        
        if anomalies:
            # 알림 발송
            for anomaly in anomalies:
                await self._send_real_time_alert(anomaly)
        
        # 패턴 업데이트
        await self._update_patterns_real_time(trade)
        
        # 스마트머니 신호 체크
        smart_money_signals = await self._check_smart_money_signals(trade)
        
        if smart_money_signals:
            # Redis에 신호 저장
            await self._cache_smart_money_signals(smart_money_signals)
    
    async def _anomaly_detector(self):
        """이상 거래 감지 엔진"""
        
        while self.running:
            try:
                # 최근 데이터 수집
                recent_data = await self._get_recent_trading_data()
                
                # 통계적 이상 감지
                statistical_anomalies = self._detect_statistical_anomalies(recent_data)
                
                # 패턴 기반 이상 감지
                pattern_anomalies = self._detect_pattern_anomalies(recent_data)
                
                # ML 기반 이상 감지
                ml_anomalies = await self._detect_ml_anomalies(recent_data)
                
                # 모든 이상 거래 통합
                all_anomalies = statistical_anomalies + pattern_anomalies + ml_anomalies
                
                # 중요도 정렬 및 처리
                sorted_anomalies = sorted(all_anomalies, key=lambda x: x["severity"], reverse=True)
                
                for anomaly in sorted_anomalies[:10]:  # 상위 10개만 처리
                    await self._handle_anomaly(anomaly)
                
                await asyncio.sleep(30)  # 30초마다 검사
                
            except Exception as e:
                self.logger.error(f"Anomaly detection error: {e}")
                await asyncio.sleep(60)
```

#### 11.2 ML 기반 패턴 감지
**src/analysis/ml_detector.py**
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib
from typing import Dict, List, Tuple, Optional

class MLPatternDetector:
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.scalers = {}
        self.feature_extractors = {}
        
    async def initialize_models(self):
        """ML 모델 초기화"""
        
        # 이상 거래 감지 모델
        self.models["anomaly"] = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=200
        )
        
        # 패턴 클러스터링 모델
        self.models["clustering"] = DBSCAN(
            eps=0.5,
            min_samples=5
        )
        
        # 스케일러 초기화
        self.scalers["trading"] = StandardScaler()
        self.scalers["price"] = StandardScaler()
        
        # 기존 모델 로드 시도
        await self._load_pretrained_models()
        
    async def _load_pretrained_models(self):
        """사전 훈련된 모델 로드"""
        
        try:
            self.models["anomaly"] = joblib.load("models/anomaly_detector.pkl")
            self.scalers["trading"] = joblib.load("models/trading_scaler.pkl")
            self.logger.info("Pre-trained models loaded successfully")
        except FileNotFoundError:
            self.logger.info("No pre-trained models found, using fresh models")
    
    async def detect_anomalies(self, trading_data: pd.DataFrame) -> List[Dict]:
        """ML 기반 이상 거래 감지"""
        
        if trading_data.empty or len(trading_data) < 10:
            return []
        
        # 특징 추출
        features = self._extract_trading_features(trading_data)
        
        if features.empty:
            return []
        
        # 데이터 정규화
        features_scaled = self.scalers["trading"].fit_transform(features)
        
        # 이상 감지
        anomaly_scores = self.models["anomaly"].decision_function(features_scaled)
        anomaly_labels = self.models["anomaly"].predict(features_scaled)
        
        # 이상 거래 식별
        anomalies = []
        anomaly_indices = np.where(anomaly_labels == -1)[0]
        
        for idx in anomaly_indices:
            anomaly_data = trading_data.iloc[idx]
            
            anomaly = {
                "timestamp": anomaly_data["timestamp"],
                "stock_code": anomaly_data.get("stock_code", "MARKET"),
                "anomaly_type": self._classify_anomaly_type(features.iloc[idx]),
                "severity": self._calculate_anomaly_severity(anomaly_scores[idx]),
                "details": {
                    "anomaly_score": float(anomaly_scores[idx]),
                    "feature_contributions": self._analyze_feature_contributions(features.iloc[idx]),
                    "trading_metrics": {
                        "foreign_net": int(anomaly_data.get("foreign_net", 0)),
                        "institution_net": int(anomaly_data.get("institution_net", 0)),
                        "volume_spike": self._calculate_volume_spike(anomaly_data)
                    }
                },
                "confidence": self._calculate_anomaly_confidence(anomaly_scores[idx])
            }
            
            anomalies.append(anomaly)
        
        return sorted(anomalies, key=lambda x: x["severity"], reverse=True)
    
    def _extract_trading_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """거래 데이터에서 특징 추출"""
        
        features = pd.DataFrame()
        
        # 기본 거래 특징
        features["foreign_net_ratio"] = data["foreign_net"] / (data["foreign_buy"] + data["foreign_sell"] + 1)
        features["institution_net_ratio"] = data["institution_net"] / (data["institution_buy"] + data["institution_sell"] + 1)
        features["individual_net_ratio"] = data["individual_net"] / (data["individual_buy"] + data["individual_sell"] + 1)
        
        # 거래량 특징
        features["total_volume"] = data["foreign_buy_volume"] + data["foreign_sell_volume"] + \
                                 data["institution_buy_volume"] + data["institution_sell_volume"] + \
                                 data["individual_buy_volume"] + data["individual_sell_volume"]
        
        # 이동평균 기반 특징 (롤링 윈도우)
        window = min(20, len(data))
        if window > 1:
            features["foreign_net_ma"] = data["foreign_net"].rolling(window).mean()
            features["volume_ma"] = features["total_volume"].rolling(window).mean()
            
            # 이동평균 대비 편차
            features["foreign_net_deviation"] = (data["foreign_net"] - features["foreign_net_ma"]) / (features["foreign_net_ma"].abs() + 1)
            features["volume_deviation"] = (features["total_volume"] - features["volume_ma"]) / (features["volume_ma"] + 1)
        
        # 변화율 특징
        features["foreign_net_change"] = data["foreign_net"].pct_change().fillna(0)
        features["institution_net_change"] = data["institution_net"].pct_change().fillna(0)
        
        # 상호작용 특징
        features["foreign_institution_alignment"] = np.sign(data["foreign_net"]) * np.sign(data["institution_net"])
        features["smart_money_flow"] = (data["foreign_net"] + data["institution_net"]) / (features["total_volume"] + 1)
        
        # 시간 기반 특징
        if "timestamp" in data.columns:
            data["hour"] = pd.to_datetime(data["timestamp"]).dt.hour
            features["is_opening"] = (data["hour"] == 9).astype(int)
            features["is_closing"] = (data["hour"] >= 14).astype(int)
        
        # NaN 값 처리
        features = features.fillna(0)
        
        return features
    
    def _classify_anomaly_type(self, feature_row: pd.Series) -> str:
        """이상 거래 유형 분류"""
        
        # 외국인 대량 거래
        if abs(feature_row.get("foreign_net_deviation", 0)) > 3:
            return "FOREIGN_MASSIVE_TRADE"
        
        # 기관 이상 거래
        elif abs(feature_row.get("institution_net_change", 0)) > 5:
            return "INSTITUTION_UNUSUAL_ACTIVITY"
        
        # 거래량 급증
        elif feature_row.get("volume_deviation", 0) > 3:
            return "VOLUME_SPIKE"
        
        # 스마트머니 동조화
        elif feature_row.get("foreign_institution_alignment", 0) == 1 and \
             abs(feature_row.get("smart_money_flow", 0)) > 2:
            return "SMART_MONEY_COORDINATION"
        
        # 시간대 이상 거래
        elif feature_row.get("is_closing", 0) == 1 and \
             abs(feature_row.get("foreign_net_ratio", 0)) > 0.8:
            return "END_OF_DAY_MANIPULATION"
        
        else:
            return "UNKNOWN_PATTERN"
    
    def _calculate_anomaly_severity(self, anomaly_score: float) -> float:
        """이상 거래 심각도 계산 (0-10 스케일)"""
        
        # Isolation Forest의 점수는 음수 (더 음수일수록 이상)
        normalized_score = abs(anomaly_score)
        
        # 0-10 스케일로 변환
        severity = min(10.0, max(0.0, normalized_score * 20))
        
        return round(severity, 1)
    
    async def detect_pattern_clusters(self, trading_data: pd.DataFrame) -> List[Dict]:
        """패턴 클러스터 감지"""
        
        if trading_data.empty or len(trading_data) < 10:
            return []
        
        # 특징 추출
        features = self._extract_pattern_features(trading_data)
        
        if features.empty:
            return []
        
        # 정규화
        features_scaled = self.scalers["trading"].fit_transform(features)
        
        # 클러스터링
        cluster_labels = self.models["clustering"].fit_predict(features_scaled)
        
        # 클러스터 분석
        clusters = []
        unique_labels = set(cluster_labels)
        
        for label in unique_labels:
            if label == -1:  # 노이즈 제외
                continue
            
            cluster_indices = np.where(cluster_labels == label)[0]
            cluster_data = trading_data.iloc[cluster_indices]
            
            cluster_analysis = self._analyze_cluster_pattern(cluster_data, features.iloc[cluster_indices])
            
            if cluster_analysis["significance"] >= 7.0:
                clusters.append(cluster_analysis)
        
        return sorted(clusters, key=lambda x: x["significance"], reverse=True)
```

### Day 13-14: 캐싱 시스템 및 성능 최적화

#### 13.1 고성능 캐싱 시스템
**src/utils/advanced_cache.py**
```python
import asyncio
import pickle
import zlib
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
import aioredis
from dataclasses import dataclass
import hashlib

@dataclass
class CacheConfig:
    ttl: int
    compress: bool = False
    serialize_method: str = "pickle"  # pickle, json
    invalidation_strategy: str = "ttl"  # ttl, lru, dependency

class AdvancedCacheManager:
    def __init__(self, redis_url: str, default_ttl: int = 300):
        self.redis_url = redis_url
        self.redis_client = None
        self.default_ttl = default_ttl
        self.memory_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "redis_hits": 0
        }
        self.dependency_graph = {}  # 캐시 의존성 그래프
        
    async def initialize(self):
        """캐시 관리자 초기화"""
        self.redis_client = await aioredis.from_url(self.redis_url)
        
        # 정리 태스크 시작
        asyncio.create_task(self._cleanup_task())
        asyncio.create_task(self._stats_reporting_task())
    
    async def get(
        self,
        key: str,
        fetch_func: Optional[Callable] = None,
        config: Optional[CacheConfig] = None
    ) -> Any:
        """다층 캐시에서 데이터 조회"""
        
        start_time = datetime.now()
        
        try:
            # 1. 메모리 캐시 확인
            memory_result = self._get_from_memory(key)
            if memory_result is not None:
                self.cache_stats["hits"] += 1
                self.cache_stats["memory_hits"] += 1
                return memory_result
            
            # 2. Redis 캐시 확인
            redis_result = await self._get_from_redis(key, config)
            if redis_result is not None:
                # 메모리 캐시에도 저장
                self._save_to_memory(key, redis_result, config)
                self.cache_stats["hits"] += 1
                self.cache_stats["redis_hits"] += 1
                return redis_result
            
            # 3. 캐시 미스 - 데이터 fetch
            if fetch_func:
                self.cache_stats["misses"] += 1
                data = await fetch_func() if asyncio.iscoroutinefunction(fetch_func) else fetch_func()
                
                # 캐시에 저장
                await self.set(key, data, config)
                return data
            
            return None
            
        finally:
            # 성능 메트릭 기록
            duration = (datetime.now() - start_time).total_seconds()
            await self._record_performance_metric(key, duration)
    
    async def set(
        self,
        key: str,
        value: Any,
        config: Optional[CacheConfig] = None
    ):
        """캐시에 데이터 저장"""
        
        if config is None:
            config = CacheConfig(ttl=self.default_ttl)
        
        # 메모리 캐시에 저장
        self._save_to_memory(key, value, config)
        
        # Redis에 저장
        await self._save_to_redis(key, value, config)
        
        # 의존성 업데이트
        await self._update_dependencies(key, value)
    
    async def invalidate(self, pattern: str = None, keys: List[str] = None):
        """캐시 무효화"""
        
        if keys:
            # 특정 키들 무효화
            for key in keys:
                await self._invalidate_key(key)
        elif pattern:
            # 패턴 매칭으로 무효화
            await self._invalidate_pattern(pattern)
    
    async def invalidate_dependencies(self, changed_key: str):
        """의존성 기반 캐시 무효화"""
        
        dependent_keys = self.dependency_graph.get(changed_key, [])
        
        for dep_key in dependent_keys:
            await self._invalidate_key(dep_key)
            # 재귀적으로 의존성 무효화
            await self.invalidate_dependencies(dep_key)
    
    def _get_from_memory(self, key: str) -> Any:
        """메모리 캐시에서 조회"""
        
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            
            # TTL 확인
            if entry["expires"] > datetime.now():
                return entry["data"]
            else:
                # 만료된 데이터 제거
                del self.memory_cache[key]
        
        return None
    
    def _save_to_memory(self, key: str, value: Any, config: CacheConfig):
        """메모리 캐시에 저장"""
        
        expires = datetime.now() + timedelta(seconds=config.ttl)
        
        self.memory_cache[key] = {
            "data": value,
            "expires": expires,
            "created": datetime.now()
        }
        
        # 메모리 캐시 크기 관리
        if len(self.memory_cache) > 10000:  # 최대 10,000개 항목
            self._evict_memory_cache()
    
    async def _get_from_redis(self, key: str, config: Optional[CacheConfig]) -> Any:
        """Redis에서 조회"""
        
        try:
            raw_data = await self.redis_client.get(key)
            if raw_data:
                return self._deserialize(raw_data, config)
        except Exception as e:
            self.logger.error(f"Redis get error for key {key}: {e}")
        
        return None
    
    async def _save_to_redis(self, key: str, value: Any, config: CacheConfig):
        """Redis에 저장"""
        
        try:
            serialized = self._serialize(value, config)
            await self.redis_client.setex(key, config.ttl, serialized)
        except Exception as e:
            self.logger.error(f"Redis set error for key {key}: {e}")
    
    def _serialize(self, value: Any, config: CacheConfig) -> bytes:
        """데이터 직렬화"""
        
        if config.serialize_method == "pickle":
            data = pickle.dumps(value)
        else:  # JSON
            import json
            data = json.dumps(value).encode()
        
        if config.compress:
            data = zlib.compress(data)
        
        return data
    
    def _deserialize(self, data: bytes, config: Optional[CacheConfig]) -> Any:
        """데이터 역직렬화"""
        
        if config and config.compress:
            data = zlib.decompress(data)
        
        if config and config.serialize_method == "json":
            import json
            return json.loads(data.decode())
        else:  # pickle (기본값)
            return pickle.loads(data)
    
    async def _cleanup_task(self):
        """주기적 캐시 정리"""
        
        while True:
            try:
                # 메모리 캐시 정리
                self._cleanup_memory_cache()
                
                # Redis 메트릭 정리
                await self._cleanup_redis_metrics()
                
                await asyncio.sleep(300)  # 5분마다 정리
                
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)
    
    def _cleanup_memory_cache(self):
        """만료된 메모리 캐시 정리"""
        
        current_time = datetime.now()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry["expires"] < current_time
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
    
    async def get_cache_statistics(self) -> Dict:
        """캐시 통계 조회"""
        
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        # Redis 메모리 사용량
        redis_info = await self.redis_client.info("memory")
        
        return {
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "memory_cache_size": len(self.memory_cache),
            "redis_memory_usage": redis_info.get("used_memory_human", "N/A"),
            "cache_distribution": {
                "memory_hits": self.cache_stats["memory_hits"],
                "redis_hits": self.cache_stats["redis_hits"],
                "misses": self.cache_stats["misses"]
            }
        }
```

#### 13.2 쿼리 최적화 및 인덱싱
**database/optimization.sql**
```sql
-- 성능 최적화를 위한 추가 인덱스

-- 1. 투자자별 시계열 조회 최적화
CREATE INDEX CONCURRENTLY idx_investor_trading_foreign_time 
ON investor_trading (foreign_net, timestamp DESC) 
WHERE foreign_net != 0;

CREATE INDEX CONCURRENTLY idx_investor_trading_institution_time 
ON investor_trading (institution_net, timestamp DESC) 
WHERE institution_net != 0;

-- 2. 종목별 투자자 동향 최적화
CREATE INDEX CONCURRENTLY idx_investor_trading_stock_investor 
ON investor_trading (stock_code, timestamp DESC, foreign_net, institution_net);

-- 3. 대용량 집계 쿼리 최적화
CREATE INDEX CONCURRENTLY idx_investor_trading_market_time_partial 
ON investor_trading (market, timestamp DESC) 
WHERE stock_code IS NULL;

-- 4. 스마트머니 신호 조회 최적화
CREATE INDEX CONCURRENTLY idx_smart_money_composite 
ON smart_money_signals (confidence DESC, timestamp DESC, stock_code);

-- 5. 기관 투자자 세부 분석용 인덱스
CREATE INDEX CONCURRENTLY idx_institution_detail_composite 
ON institution_detail (stock_code, institution_type, timestamp DESC);

-- 6. 실시간 조회용 부분 인덱스
CREATE INDEX CONCURRENTLY idx_investor_trading_recent 
ON investor_trading (timestamp DESC, stock_code) 
WHERE timestamp >= NOW() - INTERVAL '24 hours';

-- 7. 프로그램 매매 분석용 인덱스
CREATE INDEX CONCURRENTLY idx_program_trading_time_type 
ON program_trading_detail (timestamp DESC, program_type, stock_code);

-- 집계 성능을 위한 materialized view
CREATE MATERIALIZED VIEW mv_daily_investor_summary AS
SELECT 
    DATE(timestamp) as trade_date,
    stock_code,
    market,
    SUM(foreign_buy) as daily_foreign_buy,
    SUM(foreign_sell) as daily_foreign_sell,
    SUM(foreign_net) as daily_foreign_net,
    SUM(institution_buy) as daily_institution_buy,
    SUM(institution_sell) as daily_institution_sell,
    SUM(institution_net) as daily_institution_net,
    COUNT(*) as record_count
FROM investor_trading
WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(timestamp), stock_code, market;

-- materialized view 인덱스
CREATE UNIQUE INDEX idx_mv_daily_summary_primary 
ON mv_daily_investor_summary (trade_date, COALESCE(stock_code, ''), market);

-- 자동 갱신을 위한 함수
CREATE OR REPLACE FUNCTION refresh_daily_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_investor_summary;
END;
$$ LANGUAGE plpgsql;

-- 일별 자동 갱신 (cron job 필요)
-- 0 1 * * * psql -d investor_trends -c "SELECT refresh_daily_summary();"

-- 쿼리 성능 모니터링 뷰
CREATE VIEW v_slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
WHERE mean_time > 100  -- 100ms 이상 쿼리
ORDER BY mean_time DESC;

-- 인덱스 사용률 모니터링
CREATE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    CASE 
        WHEN idx_scan = 0 THEN 'Unused'
        WHEN idx_scan < 10 THEN 'Low Usage'
        ELSE 'Active'
    END as usage_status
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Day 15: 통합 테스트 및 배포 준비

#### 15.1 통합 테스트 스위트
**tests/integration/test_full_workflow.py**
```python
import pytest
import asyncio
from datetime import datetime, timedelta
import pandas as pd

from src.server import InvestorTrendsMCPServer
from src.utils.database import DatabaseManager
from src.utils.advanced_cache import AdvancedCacheManager

class TestFullWorkflow:
    @pytest.fixture(scope="class")
    async def server(self):
        """테스트용 서버 인스턴스"""
        server = InvestorTrendsMCPServer()
        await server.initialize()
        yield server
        await server.cleanup()
    
    @pytest.mark.asyncio
    async def test_complete_investor_analysis_workflow(self, server):
        """완전한 투자자 분석 워크플로우 테스트"""
        
        # 1. 기본 투자자 동향 조회
        basic_result = await server.get_investor_trading(
            investor_type="ALL",
            period="1D",
            market="KOSPI"
        )
        
        assert "investor_data" in basic_result
        assert "foreign" in basic_result["investor_data"]
        assert "institution" in basic_result["investor_data"]
        assert "individual" in basic_result["investor_data"]
        
        # 2. 특정 종목 분석
        stock_result = await server.get_investor_trading(
            stock_code="005930",  # 삼성전자
            investor_type="FOREIGN",
            period="5D",
            include_details=True
        )
        
        assert stock_result["scope"] == "STOCK"
        assert "stock_info" in stock_result
        assert stock_result["stock_info"]["code"] == "005930"
        
        # 3. 프로그램 매매 분석
        program_result = await server.get_program_trading(
            market="KOSPI",
            program_type="ALL"
        )
        
        assert "program_trading" in program_result
        assert "summary" in program_result["program_trading"]
        assert "arbitrage" in program_result["program_trading"]
        
        # 4. 스마트머니 추적
        smart_money_result = await server.get_smart_money_tracker(
            detection_method="LARGE_ORDERS",
            min_confidence=7.0
        )
        
        assert "smart_money_signals" in smart_money_result
        assert "market_smart_money_index" in smart_money_result
        
        # 5. 데이터 일관성 검증
        await self._verify_data_consistency(basic_result, stock_result, program_result)
    
    async def _verify_data_consistency(self, basic_result, stock_result, program_result):
        """데이터 일관성 검증"""
        
        # 투자자별 순매수 합계는 0에 가까워야 함 (시장 전체)
        if basic_result["scope"] == "MARKET":
            foreign_net = basic_result["investor_data"]["foreign"]["net_amount"]
            institution_net = basic_result["investor_data"]["institution"]["net_amount"]
            individual_net = basic_result["investor_data"]["individual"]["net_amount"]
            
            total_net = foreign_net + institution_net + individual_net
            # 오차 허용 (1억원)
            assert abs(total_net) < 100000000, f"Market balance inconsistent: {total_net}"
        
        # 프로그램 매매 데이터 검증
        program_summary = program_result["program_trading"]["summary"]
        assert program_summary["total_buy"] >= 0
        assert program_summary["total_sell"] >= 0
        assert 0 <= program_summary["buy_ratio"] <= 100
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, server):
        """부하 상황에서의 성능 테스트"""
        
        # 동시 요청 시뮬레이션
        tasks = []
        
        for i in range(50):  # 50개 동시 요청
            if i % 3 == 0:
                task = server.get_investor_trading()
            elif i % 3 == 1:
                task = server.get_program_trading()
            else:
                task = server.get_smart_money_tracker()
            
            tasks.append(task)
        
        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        # 성능 검증
        duration = (end_time - start_time).total_seconds()
        assert duration < 30, f"Performance too slow: {duration}s for 50 requests"
        
        # 에러율 검증
        errors = [r for r in results if isinstance(r, Exception)]
        error_rate = len(errors) / len(results)
        assert error_rate < 0.1, f"Error rate too high: {error_rate * 100}%"
    
    @pytest.mark.asyncio
    async def test_cache_effectiveness(self, server):
        """캐시 효과성 테스트"""
        
        # 첫 번째 요청 (캐시 미스)
        start_time = datetime.now()
        result1 = await server.get_investor_trading(stock_code="005930")
        first_duration = (datetime.now() - start_time).total_seconds()
        
        # 두 번째 요청 (캐시 히트)
        start_time = datetime.now()
        result2 = await server.get_investor_trading(stock_code="005930")
        second_duration = (datetime.now() - start_time).total_seconds()
        
        # 캐시 효과 검증
        assert second_duration < first_duration * 0.5, "Cache not effective"
        assert result1 == result2, "Cached result inconsistent"
        
        # 캐시 통계 확인
        cache_stats = await server.cache_manager.get_cache_statistics()
        assert cache_stats["hit_rate"] > 0, "No cache hits recorded"
    
    @pytest.mark.asyncio
    async def test_database_performance(self, server):
        """데이터베이스 성능 테스트"""
        
        db_manager = server.db_manager
        
        # 대량 데이터 삽입 테스트
        test_data = []
        for i in range(1000):
            test_data.append({
                "timestamp": datetime.now() - timedelta(minutes=i),
                "stock_code": f"00{i % 100:04d}",
                "market": "KOSPI",
                "foreign_buy": i * 1000000,
                "foreign_sell": i * 900000,
                "foreign_net": i * 100000,
                "institution_buy": i * 800000,
                "institution_sell": i * 850000,
                "institution_net": -i * 50000,
                "individual_buy": i * 700000,
                "individual_sell": i * 750000,
                "individual_net": -i * 50000,
                "program_buy": i * 200000,
                "program_sell": i * 180000,
                "program_net": i * 20000
            })
        
        start_time = datetime.now()
        await db_manager.batch_insert_investor_trading(test_data)
        insert_duration = (datetime.now() - start_time).total_seconds()
        
        # 성능 기준: 1000건 삽입이 5초 이내
        assert insert_duration < 5.0, f"Insert too slow: {insert_duration}s"
        
        # 조회 성능 테스트
        start_time = datetime.now()
        result = await db_manager.get_investor_trading_history(
            market="KOSPI",
            hours=24
        )
        query_duration = (datetime.now() - start_time).total_seconds()
        
        # 성능 기준: 24시간 데이터 조회가 2초 이내
        assert query_duration < 2.0, f"Query too slow: {query_duration}s"
        assert len(result) > 0, "No data returned"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, server):
        """에러 처리 및 복구 테스트"""
        
        # 잘못된 파라미터 테스트
        with pytest.raises(ValueError):
            await server.get_investor_trading(
                stock_code="INVALID",
                investor_type="UNKNOWN"
            )
        
        # API 타임아웃 시뮬레이션
        # (실제로는 mock을 사용하여 시뮬레이션)
        
        # 데이터베이스 연결 실패 시뮬레이션
        # (실제로는 mock을 사용하여 시뮬레이션)
        
        # 서버가 정상적으로 복구되는지 확인
        recovery_result = await server.get_investor_trading()
        assert recovery_result is not None, "Server failed to recover"
```

#### 15.2 배포 스크립트
**deploy/deploy.sh**
```bash
#!/bin/bash

set -e

echo "🚀 Starting MCP Investor Trends Server Deployment"

# 환경 변수 확인
if [ -z "$DEPLOYMENT_ENV" ]; then
    echo "❌ DEPLOYMENT_ENV not set (dev/staging/prod)"
    exit 1
fi

# 설정 파일 로드
source "config/${DEPLOYMENT_ENV}.env"

echo "📝 Deploying to environment: $DEPLOYMENT_ENV"

# 1. 의존성 확인
echo "🔍 Checking dependencies..."
python --version
pip --version
docker --version
docker-compose --version

# 2. 코드 품질 검사
echo "🧹 Running code quality checks..."
python -m flake8 src/ --max-line-length=100
python -m mypy src/ --ignore-missing-imports
python -m black src/ --check

# 3. 테스트 실행
echo "🧪 Running tests..."
python -m pytest tests/ -v --cov=src --cov-report=html

# 4. 보안 검사
echo "🔒 Running security checks..."
python -m bandit -r src/ -f json -o security-report.json

# 5. 데이터베이스 마이그레이션 (staging/prod만)
if [ "$DEPLOYMENT_ENV" != "dev" ]; then
    echo "🗄️ Running database migrations..."
    python scripts/migrate_database.py --env=$DEPLOYMENT_ENV
fi

# 6. Docker 이미지 빌드
echo "🏗️ Building Docker image..."
docker build -t mcp-investor-trends:$DEPLOYMENT_ENV .

# 7. 이미지 최적화 확인
echo "📊 Checking image size..."
docker images mcp-investor-trends:$DEPLOYMENT_ENV --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# 8. 환경별 배포
if [ "$DEPLOYMENT_ENV" = "dev" ]; then
    echo "🏃‍♂️ Starting development environment..."
    docker-compose -f docker-compose.dev.yml up -d
    
elif [ "$DEPLOYMENT_ENV" = "staging" ]; then
    echo "🎭 Deploying to staging..."
    docker-compose -f docker-compose.staging.yml up -d
    
    # 헬스 체크
    echo "❤️ Running health checks..."
    sleep 30
    python scripts/health_check.py --env=staging
    
elif [ "$DEPLOYMENT_ENV" = "prod" ]; then
    echo "🚀 Deploying to production..."
    
    # 블루-그린 배포
    python scripts/blue_green_deploy.py
    
    # 트래픽 전환 전 최종 검증
    echo "✅ Running production validation..."
    python scripts/production_validation.py
    
    # 모니터링 알림 활성화
    python scripts/enable_monitoring.py
fi

# 9. 배포 후 검증
echo "🔍 Post-deployment verification..."
sleep 10

# API 엔드포인트 테스트
curl -f http://localhost:8080/health || {
    echo "❌ Health check failed"
    exit 1
}

# MCP 서버 연결 테스트
python scripts/test_mcp_connection.py

echo "✅ Deployment completed successfully!"

# 10. 슬랙 알림 (선택사항)
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ MCP Investor Trends deployed to $DEPLOYMENT_ENV successfully\"}" \
        $SLACK_WEBHOOK_URL
fi

echo "📊 Deployment summary:"
echo "Environment: $DEPLOYMENT_ENV"
echo "Version: $(git rev-parse --short HEAD)"
echo "Timestamp: $(date)"
echo "Image: mcp-investor-trends:$DEPLOYMENT_ENV"
```

이제 상세한 개발계획이 완성되었습니다. 다음 단계로 세부 작업 항목과 일정을 수립하겠습니다.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "기존 계획문서 분석 및 개발 범위 정의", "status": "completed", "priority": "high"}, {"id": "2", "content": "단계별 구체적 개발계획 작성", "status": "completed", "priority": "high"}, {"id": "3", "content": "각 단계별 세부 작업 항목 및 일정 수립", "status": "in_progress", "priority": "high"}, {"id": "4", "content": "기술적 의존성 및 위험요소 분석", "status": "pending", "priority": "medium"}]