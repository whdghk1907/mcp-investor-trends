"""
투자자 동향 MCP 서버 메인 클래스
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import Config
from .api.korea_investment import KoreaInvestmentAPI
from .utils.database import DatabaseManager
from .utils.cache import CacheManager
from .tools.investor_tools import InvestorTradingTool
from .exceptions import APIException, DatabaseException, ValidationException


class InvestorTrendsMCPServer:
    """투자자 동향 MCP 서버"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = self._setup_logger()
        self.tools = {}
        self.database = None
        self.api_client = None
        self.cache = None
        self.investor_tool = None
        
        # 초기화
        self._register_tools()
    
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _register_tools(self):
        """MCP 도구 등록"""
        self.tools = {
            'get_investor_trading': self.get_investor_trading,
            'get_ownership_changes': self.get_ownership_changes,
            'get_program_trading': self.get_program_trading,
            'get_sector_investor_flow': self.get_sector_investor_flow,
            'get_time_based_flow': self.get_time_based_flow,
            'get_smart_money_tracker': self.get_smart_money_tracker,
            'get_investor_sentiment': self.get_investor_sentiment
        }
    
    async def startup(self):
        """서버 시작"""
        self.logger.info("Starting MCP Investor Trends Server...")
        
        await self._initialize_database()
        await self._initialize_cache()
        await self._initialize_api_clients()
        await self._initialize_tools()
        
        self.logger.info("Server started successfully")
    
    async def shutdown(self):
        """서버 종료"""
        self.logger.info("Shutting down MCP Investor Trends Server...")
        
        await self._cleanup_database()
        await self._cleanup_cache()
        await self._cleanup_api_clients()
        
        self.logger.info("Server shutdown complete")
    
    async def _initialize_database(self):
        """데이터베이스 초기화"""
        try:
            self.database = DatabaseManager(
                database_url=self.config.database.url,
                pool_size=self.config.database.pool_size
            )
            await self.database.initialize()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _initialize_cache(self):
        """캐시 초기화"""
        try:
            self.cache = CacheManager(self.config)
            await self.cache.initialize()
            self.logger.info("Cache initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize cache: {e}")
            raise
    
    async def _initialize_api_clients(self):
        """API 클라이언트 초기화"""
        try:
            self.api_client = KoreaInvestmentAPI(
                app_key=self.config.api.app_key,
                app_secret=self.config.api.app_secret
            )
            await self.api_client.initialize()
            self.logger.info("API client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize API client: {e}")
            raise
    
    async def _initialize_tools(self):
        """도구 초기화"""
        try:
            self.investor_tool = InvestorTradingTool(
                config=self.config,
                api_client=self.api_client,
                database=self.database,
                cache=self.cache
            )
            self.logger.info("Tools initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize tools: {e}")
            raise
    
    async def _cleanup_database(self):
        """데이터베이스 정리"""
        if self.database:
            await self.database.close()
            self.logger.info("Database closed successfully")
    
    async def _cleanup_cache(self):
        """캐시 정리"""
        if self.cache:
            await self.cache.close()
            self.logger.info("Cache closed successfully")
    
    async def _cleanup_api_clients(self):
        """API 클라이언트 정리"""
        if self.api_client:
            await self.api_client.close()
            self.logger.info("API client closed successfully")
    
    # MCP 도구 구현
    async def get_investor_trading(
        self,
        stock_code: Optional[str] = None,
        investor_type: str = "ALL",
        period: str = "1D",
        market: str = "ALL",
        include_analysis: bool = True
    ) -> Dict[str, Any]:
        """투자자별 매매 동향 조회 (고급 분석 포함)"""
        
        if self.investor_tool:
            # 새로운 고급 도구 사용
            return await self.investor_tool.get_investor_trading(
                stock_code=stock_code,
                investor_type=investor_type,
                period=period,
                market=market,
                include_analysis=include_analysis,
                use_cache=True
            )
        else:
            # 폴백: 기존 기본 구현
            try:
                # 파라미터 검증
                if not self._validate_investor_type(investor_type):
                    raise ValueError(f"Invalid investor_type: {investor_type}")
                
                if not self._validate_period(period):
                    raise ValueError(f"Invalid period: {period}")
                
                if not self._validate_market(market):
                    raise ValueError(f"Invalid market: {market}")
                
                # 데이터 조회 (기본 구현)
                return await self._fetch_investor_data_basic(
                    stock_code=stock_code,
                    investor_type=investor_type,
                    period=period,
                    market=market,
                    include_analysis=include_analysis
                )
            
            except Exception as e:
                self.logger.error(f"Error in basic get_investor_trading: {e}")
                return {
                    "success": False,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e)
                    },
                    "timestamp": datetime.now().isoformat()
                }
    
    async def get_ownership_changes(
        self,
        stock_code: str,
        investor_type: str = "ALL",
        period: str = "3M",
        threshold: float = 1.0
    ) -> Dict[str, Any]:
        """투자자별 보유 비중 변화 추적"""
        # 구현 예정
        return {}
    
    async def get_program_trading(
        self,
        market: str = "ALL",
        program_type: str = "ALL",
        time_window: str = "CURRENT"
    ) -> Dict[str, Any]:
        """프로그램 매매 동향 조회"""
        return await self._fetch_program_data(
            market=market,
            program_type=program_type,
            time_window=time_window
        )
    
    async def get_sector_investor_flow(
        self,
        sector: Optional[str] = None,
        investor_type: str = "ALL",
        period: str = "5D",
        top_n: int = 10
    ) -> Dict[str, Any]:
        """업종별 투자자 자금 흐름 분석"""
        # 구현 예정
        return {}
    
    async def get_time_based_flow(
        self,
        stock_code: Optional[str] = None,
        interval: str = "10M",
        session: str = "ALL"
    ) -> Dict[str, Any]:
        """시간대별 투자자 매매 패턴 분석"""
        # 구현 예정
        return {}
    
    async def get_smart_money_tracker(
        self,
        detection_method: str = "LARGE_ORDERS",
        market: str = "ALL",
        min_confidence: float = 7.0,
        count: int = 20
    ) -> Dict[str, Any]:
        """스마트머니 움직임 추적"""
        return await self._track_smart_money(
            detection_method=detection_method,
            market=market,
            min_confidence=min_confidence,
            count=count
        )
    
    async def get_investor_sentiment(
        self,
        period: str = "1D",
        granularity: str = "OVERALL"
    ) -> Dict[str, Any]:
        """투자자 심리 지표 분석"""
        # 구현 예정
        return {}
    
    # 헬퍼 메서드들
    def _validate_investor_type(self, investor_type: str) -> bool:
        """투자자 타입 검증"""
        valid_types = ["FOREIGN", "INSTITUTION", "INDIVIDUAL", "ALL"]
        return investor_type in valid_types
    
    def _validate_period(self, period: str) -> bool:
        """기간 검증"""
        valid_periods = ["1D", "5D", "20D", "60D"]
        return period in valid_periods
    
    def _validate_market(self, market: str) -> bool:
        """시장 검증"""
        valid_markets = ["ALL", "KOSPI", "KOSDAQ"]
        return market in valid_markets
    
    def _validate_stock_code(self, stock_code: Optional[str]) -> bool:
        """종목 코드 검증"""
        if stock_code is None:
            return True
        return isinstance(stock_code, str) and len(stock_code) == 6 and stock_code.isdigit()
    
    async def _fetch_investor_data_basic(
        self,
        stock_code: Optional[str] = None,
        investor_type: str = "ALL",
        period: str = "1D",
        market: str = "ALL",
        include_analysis: bool = True
    ) -> Dict[str, Any]:
        """투자자 데이터 조회 (기본 구현)"""
        try:
            # API를 통해 현재 투자자 거래 데이터 조회
            current_data = await self.api_client.get_investor_trading(
                stock_code=stock_code,
                market=market
            )
            
            # 데이터베이스에서 이력 데이터 조회
            hours_map = {"1D": 24, "5D": 120, "20D": 480, "60D": 1440}
            hours = hours_map.get(period, 24)
            
            historical_data = await self.database.get_investor_trading_history(
                stock_code=stock_code,
                market=market,
                hours=hours
            )
            
            # 기본 분석
            analysis = self._analyze_smart_money_signals(current_data, historical_data) if include_analysis else {}
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "stock_code": stock_code,
                "market": market,
                "period": period,
                "investor_type": investor_type,
                "current_data": current_data.get("data", [{}])[0] if current_data.get("data") else {},
                "historical_data": historical_data,
                "analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching basic investor data: {e}")
            raise
    
    async def _fetch_program_data(
        self,
        market: str = "ALL",
        program_type: str = "ALL",
        time_window: str = "CURRENT"
    ) -> Dict[str, Any]:
        """프로그램 매매 데이터 조회 (구현 예정)"""
        # 임시 구현
        return {
            "timestamp": datetime.now().isoformat(),
            "market": market,
            "program_trading": {
                "summary": {
                    "total_buy": 500000000,
                    "total_sell": 400000000,
                    "net_value": 100000000
                }
            }
        }
    
    async def _track_smart_money(
        self,
        detection_method: str = "LARGE_ORDERS",
        market: str = "ALL",
        min_confidence: float = 7.0,
        count: int = 20
    ) -> Dict[str, Any]:
        """스마트머니 추적 (구현 예정)"""
        # 임시 구현
        return {
            "timestamp": datetime.now().isoformat(),
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
    
    async def health_check(self) -> Dict[str, Any]:
        """서버 헬스 체크"""
        database_healthy = await self._check_database_health()
        cache_healthy = await self._check_cache_health()
        api_healthy = await self._check_api_health()
        
        overall_healthy = database_healthy and cache_healthy and api_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "database": database_healthy,
            "cache": cache_healthy,
            "api": api_healthy,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _check_database_health(self) -> bool:
        """데이터베이스 헬스 체크"""
        try:
            if self.database:
                return await self.database.health_check()
            return False
        except Exception:
            return False
    
    async def _check_cache_health(self) -> bool:
        """캐시 헬스 체크"""
        try:
            if self.cache:
                return await self.cache.health_check()
            return True  # 캐시가 없어도 정상
        except Exception:
            return False
    
    async def _check_api_health(self) -> bool:
        """API 헬스 체크"""
        try:
            if self.api_client:
                # 간단한 API 호출로 헬스 체크 (향후 구현)
                return True
            return False
        except Exception:
            return False
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 반환"""
        return [
            {
                "name": "get_investor_trading",
                "description": "투자자별 매매 동향 조회",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "stock_code": {"type": "string", "description": "종목코드 (6자리)"},
                        "investor_type": {"type": "string", "enum": ["FOREIGN", "INSTITUTION", "INDIVIDUAL", "ALL"]},
                        "period": {"type": "string", "enum": ["1D", "5D", "20D", "60D"]},
                        "market": {"type": "string", "enum": ["ALL", "KOSPI", "KOSDAQ"]}
                    }
                }
            },
            {
                "name": "get_program_trading",
                "description": "프로그램 매매 동향 조회",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "market": {"type": "string", "enum": ["ALL", "KOSPI", "KOSDAQ"]},
                        "period": {"type": "string", "enum": ["1D", "5D", "20D"]}
                    }
                }
            },
            {
                "name": "analyze_smart_money",
                "description": "스마트 머니 분석",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "stock_code": {"type": "string", "description": "종목코드 (6자리)"},
                        "detection_method": {"type": "string", "enum": ["LARGE_ORDERS", "PATTERN_ANALYSIS"]},
                        "min_confidence": {"type": "number", "minimum": 1, "maximum": 10}
                    }
                }
            },
            {
                "name": "get_market_overview",
                "description": "시장 전체 투자자 동향 개요",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "market": {"type": "string", "enum": ["ALL", "KOSPI", "KOSDAQ"]},
                        "period": {"type": "string", "enum": ["1D", "5D", "20D"]}
                    }
                }
            }
        ]
    
    def _analyze_smart_money_signals(self, current_data: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """스마트 머니 신호 분석"""
        try:
            # 현재 데이터에서 투자자별 순매수 금액 추출
            foreign_net = current_data.get("foreign_net_buy_amount", 0)
            institution_net = current_data.get("institution_net_buy_amount", 0)
            individual_net = current_data.get("individual_net_buy_amount", 0)
            
            # 스마트 머니 신호 계산
            smart_money_net = foreign_net + institution_net
            total_volume = abs(foreign_net) + abs(institution_net) + abs(individual_net)
            
            # 신호 강도 계산 (1-10)
            if total_volume > 0:
                intensity = min(10, max(1, abs(smart_money_net) / total_volume * 10))
            else:
                intensity = 1
            
            # 신호 방향 결정
            if smart_money_net > self.config.analysis.smart_money_threshold:
                signal = "BUY"
            elif smart_money_net < -self.config.analysis.smart_money_threshold:
                signal = "SELL"
            else:
                signal = "NEUTRAL"
            
            return {
                "smart_money_signal": {
                    "signal": signal,
                    "intensity": round(intensity, 2),
                    "foreign_contribution": foreign_net,
                    "institution_contribution": institution_net,
                    "total_smart_money_flow": smart_money_net
                },
                "trend_analysis": self._analyze_trend(historical_data),
                "market_sentiment": self._calculate_market_sentiment(current_data)
            }
        except Exception as e:
            self.logger.error(f"Error in smart money analysis: {e}")
            return {
                "smart_money_signal": {
                    "signal": "NEUTRAL",
                    "intensity": 1,
                    "error": "Analysis failed"
                }
            }
    
    def _analyze_trend(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """트렌드 분석"""
        if len(historical_data) < 2:
            return {"trend": "INSUFFICIENT_DATA", "confidence": 0}
        
        # 최근 데이터의 외국인 + 기관 순매수 추세 분석
        recent_flows = []
        for data in historical_data[-5:]:  # 최근 5개 데이터포인트
            foreign_net = data.get("foreign_net", 0)
            institution_net = data.get("institution_net", 0)
            recent_flows.append(foreign_net + institution_net)
        
        if len(recent_flows) >= 3:
            increasing = sum(1 for i in range(1, len(recent_flows)) if recent_flows[i] > recent_flows[i-1])
            decreasing = sum(1 for i in range(1, len(recent_flows)) if recent_flows[i] < recent_flows[i-1])
            
            if increasing > decreasing:
                return {"trend": "ACCUMULATING", "confidence": increasing / (len(recent_flows) - 1)}
            elif decreasing > increasing:
                return {"trend": "DISTRIBUTING", "confidence": decreasing / (len(recent_flows) - 1)}
        
        return {"trend": "NEUTRAL", "confidence": 0.5}
    
    def _calculate_market_sentiment(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """시장 심리 계산"""
        foreign_net = current_data.get("foreign_net_buy_amount", 0)
        institution_net = current_data.get("institution_net_buy_amount", 0)
        individual_net = current_data.get("individual_net_buy_amount", 0)
        
        # 투자자 그룹별 거래 비중 계산
        total_activity = abs(foreign_net) + abs(institution_net) + abs(individual_net)
        
        if total_activity == 0:
            return {"sentiment": "NEUTRAL", "dominant_group": "NONE"}
        
        # 가장 활발한 투자자 그룹 식별
        groups = {
            "FOREIGN": abs(foreign_net),
            "INSTITUTION": abs(institution_net),
            "INDIVIDUAL": abs(individual_net)
        }
        
        dominant_group = max(groups, key=groups.get)
        
        # 전체적인 시장 심리 판단
        if foreign_net + institution_net > 0:
            sentiment = "POSITIVE"
        elif foreign_net + institution_net < 0:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"
        
        return {
            "sentiment": sentiment,
            "dominant_group": dominant_group,
            "activity_distribution": {
                "foreign_ratio": round(abs(foreign_net) / total_activity * 100, 2),
                "institution_ratio": round(abs(institution_net) / total_activity * 100, 2),
                "individual_ratio": round(abs(individual_net) / total_activity * 100, 2)
            }
        }