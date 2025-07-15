"""
투자자 매매 동향 분석 도구
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import statistics
import hashlib

from ..config import Config
from ..exceptions import APIException, ValidationException, DataNotFoundException


class InvestorTradingTool:
    """투자자 매매 동향 분석 도구"""
    
    def __init__(self, config: Config, api_client, database, cache):
        self.config = config
        self.api_client = api_client
        self.database = database
        self.cache = cache
        self.logger = logging.getLogger(__name__)
        
        # 분석 설정
        self.intensity_thresholds = {
            "low": 1000000000,      # 10억
            "medium": 5000000000,   # 50억  
            "high": 10000000000,    # 100억
            "very_high": 50000000000  # 500억
        }
        
        self.trend_sensitivity = 0.1  # 10% 변화율 기준
    
    async def get_investor_trading(
        self,
        stock_code: Optional[str] = None,
        investor_type: str = "ALL",
        period: str = "1D",
        market: str = "ALL",
        include_analysis: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        투자자 매매 동향 조회 및 분석
        
        Args:
            stock_code: 종목코드 (None이면 시장 전체)
            investor_type: 투자자 타입 (FOREIGN, INSTITUTION, INDIVIDUAL, ALL)
            period: 분석 기간 (1D, 5D, 20D, 60D, ALL)
            market: 시장 (KOSPI, KOSDAQ, ALL)
            include_analysis: 분석 결과 포함 여부
            use_cache: 캐시 사용 여부
            
        Returns:
            분석 결과 딕셔너리
        """
        
        try:
            # 파라미터 검증
            self._validate_parameters(stock_code, investor_type, period, market)
            
            # 캐시 확인
            if use_cache:
                cached_result = await self._get_from_cache(stock_code, investor_type, period, market)
                if cached_result:
                    self.logger.info(f"Cache hit for {stock_code or 'market'} investor trading")
                    return cached_result
            
            # 다중 기간 분석 처리
            if period == "ALL":
                return await self._get_multi_period_analysis(
                    stock_code, investor_type, market, include_analysis
                )
            
            # 현재 데이터 조회
            current_data = await self._fetch_current_data(stock_code, market)
            
            # 과거 데이터 조회
            historical_data = await self._fetch_historical_data(stock_code, market, period)
            
            # 결과 구성
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "stock_code": stock_code,
                "market": market,
                "period": period,
                "investor_type": investor_type
            }
            
            if stock_code:
                # 개별 종목 분석
                result.update(await self._analyze_stock_trading(
                    stock_code, current_data, historical_data, investor_type, include_analysis
                ))
            else:
                # 시장 전체 분석
                result.update(await self._analyze_market_trading(
                    current_data, historical_data, market, investor_type, include_analysis
                ))
            
            # 캐시에 저장
            if use_cache:
                await self._save_to_cache(result, stock_code, investor_type, period, market)
            
            return result
            
        except (ValidationException, APIException, DataNotFoundException) as e:
            self.logger.error(f"Error in get_investor_trading: {e}")
            return {
                "success": False,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e)
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Unexpected error in get_investor_trading: {e}")
            return {
                "success": False,
                "error": {
                    "type": "UnexpectedError",
                    "message": "An unexpected error occurred"
                },
                "timestamp": datetime.now().isoformat()
            }
    
    async def _fetch_current_data(self, stock_code: Optional[str], market: str) -> Dict[str, Any]:
        """현재 투자자 거래 데이터 조회"""
        try:
            api_result = await self.api_client.get_investor_trading(
                stock_code=stock_code,
                market=market
            )
            
            if not api_result.get("success", False):
                raise APIException("Failed to fetch current trading data")
            
            return api_result.get("data", [{}])[0] if api_result.get("data") else {}
            
        except Exception as e:
            self.logger.error(f"Error fetching current data: {e}")
            raise APIException(f"Failed to fetch current data: {str(e)}")
    
    async def _fetch_historical_data(
        self, 
        stock_code: Optional[str], 
        market: str, 
        period: str
    ) -> List[Dict[str, Any]]:
        """과거 투자자 거래 데이터 조회"""
        try:
            # 기간을 시간으로 변환
            hours_map = {"1D": 24, "5D": 120, "20D": 480, "60D": 1440}
            hours = hours_map.get(period, 24)
            
            historical_data = await self.database.get_investor_trading_history(
                stock_code=stock_code,
                market=market,
                hours=hours
            )
            
            return historical_data or []
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data: {e}")
            return []
    
    async def _analyze_stock_trading(
        self,
        stock_code: str,
        current_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        investor_type: str,
        include_analysis: bool
    ) -> Dict[str, Any]:
        """개별 종목 투자자 거래 분석"""
        
        result = {
            "current_data": current_data,
            "historical_data": historical_data
        }
        
        if include_analysis and current_data:
            analysis = {}
            
            # 트렌드 분석
            analysis["trend_analysis"] = self._calculate_trend_analysis(current_data, historical_data)
            
            # 강도 점수
            analysis["intensity_score"] = self._calculate_intensity_score(current_data)
            
            # 시장 영향도
            analysis["market_impact"] = self._calculate_market_impact(current_data)
            
            # 스마트 머니 신호
            analysis["smart_money_signal"] = self._analyze_smart_money_signals(current_data, historical_data)
            
            # 투자자 타입별 필터링
            if investor_type != "ALL":
                analysis = self._filter_analysis_by_investor_type(analysis, investor_type)
            
            result["analysis"] = analysis
        
        return result
    
    async def _analyze_market_trading(
        self,
        current_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        market: str,
        investor_type: str,
        include_analysis: bool
    ) -> Dict[str, Any]:
        """시장 전체 투자자 거래 분석"""
        
        # 시장 개요 생성
        market_overview = self._generate_market_overview(current_data)
        
        result = {
            "market_overview": market_overview,
            "historical_data": historical_data
        }
        
        if include_analysis and current_data:
            analysis = {}
            
            # 시장 트렌드 분석
            analysis["market_trend"] = self._calculate_market_trend(current_data, historical_data)
            
            # 시장 심리 분석
            analysis["market_sentiment"] = self._calculate_market_sentiment(current_data)
            
            # 투자자 그룹 분석
            analysis["investor_group_analysis"] = self._analyze_investor_groups(current_data, historical_data)
            
            result["analysis"] = analysis
        
        return result
    
    def _calculate_trend_analysis(
        self, 
        current_data: Dict[str, Any], 
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """트렌드 분석 계산"""
        
        if not historical_data:
            return {
                "trend_direction": "NEUTRAL",
                "trend_strength": 1,
                "consistency_score": 0,
                "momentum_score": 1
            }
        
        # 현재 스마트 머니 플로우
        current_smart_money = (
            current_data.get("foreign_net_buy_amount", 0) + 
            current_data.get("institution_net_buy_amount", 0)
        )
        
        # 과거 스마트 머니 플로우 추출
        historical_flows = []
        for data in historical_data[-10:]:  # 최근 10개 데이터포인트
            flow = data.get("foreign_net", 0) + data.get("institution_net", 0)
            historical_flows.append(flow)
        
        if not historical_flows:
            return {
                "trend_direction": "NEUTRAL",
                "trend_strength": 1,
                "consistency_score": 0,
                "momentum_score": 1
            }
        
        # 트렌드 방향 계산
        trend_direction = self._determine_trend_direction(historical_flows, current_smart_money)
        
        # 트렌드 강도 계산 (1-10)
        trend_strength = self._calculate_trend_strength(historical_flows, current_smart_money)
        
        # 일관성 점수 (0-1)
        consistency_score = self._calculate_consistency_score(historical_flows)
        
        # 모멘텀 점수 (1-10)
        momentum_score = self._calculate_momentum_score(historical_flows, current_smart_money)
        
        return {
            "trend_direction": trend_direction,
            "trend_strength": min(10, max(1, trend_strength)),
            "consistency_score": min(1, max(0, consistency_score)),
            "momentum_score": min(10, max(1, momentum_score))
        }
    
    def _calculate_intensity_score(self, trading_data: Dict[str, Any]) -> Dict[str, Any]:
        """거래 강도 점수 계산"""
        
        foreign_net = abs(trading_data.get("foreign_net_buy_amount", 0))
        institution_net = abs(trading_data.get("institution_net_buy_amount", 0))
        individual_net = abs(trading_data.get("individual_net_buy_amount", 0))
        program_net = abs(trading_data.get("program_net_buy_amount", 0))
        
        total_activity = foreign_net + institution_net + individual_net + program_net
        smart_money_activity = foreign_net + institution_net
        
        # 전체 강도 (1-10)
        overall_intensity = self._calculate_intensity_level(total_activity)
        
        # 투자자별 강도
        foreign_intensity = self._calculate_intensity_level(foreign_net)
        institution_intensity = self._calculate_intensity_level(institution_net)
        
        # 스마트 머니 강도
        smart_money_intensity = self._calculate_intensity_level(smart_money_activity)
        
        return {
            "overall_intensity": overall_intensity,
            "foreign_intensity": foreign_intensity,
            "institution_intensity": institution_intensity,
            "smart_money_intensity": max(1, smart_money_intensity),
            "total_activity_amount": total_activity,
            "smart_money_activity_amount": smart_money_activity
        }
    
    def _calculate_market_impact(self, trading_data: Dict[str, Any], market: str = "ALL") -> Dict[str, Any]:
        """시장 영향도 계산"""
        
        foreign_net = trading_data.get("foreign_net_buy_amount", 0)
        institution_net = trading_data.get("institution_net_buy_amount", 0)
        individual_net = trading_data.get("individual_net_buy_amount", 0)
        
        smart_money_net = foreign_net + institution_net
        total_net_activity = abs(foreign_net) + abs(institution_net) + abs(individual_net)
        
        # 영향도 점수 (0-10)
        if total_net_activity == 0:
            impact_score = 0
        else:
            impact_score = min(10, abs(smart_money_net) / self.intensity_thresholds["low"] * 2)
        
        # 지배력 요소
        if total_net_activity > 0:
            dominance_factor = abs(smart_money_net) / total_net_activity
        else:
            dominance_factor = 0
        
        # 압력 지표
        if smart_money_net > self.config.analysis.smart_money_threshold:
            pressure_indicator = "BUYING_PRESSURE"
        elif smart_money_net < -self.config.analysis.smart_money_threshold:
            pressure_indicator = "SELLING_PRESSURE"
        else:
            pressure_indicator = "BALANCED"
        
        # 시장 심리
        if smart_money_net > 0:
            market_sentiment = "BULLISH"
        elif smart_money_net < 0:
            market_sentiment = "BEARISH"
        else:
            market_sentiment = "NEUTRAL"
        
        return {
            "impact_score": round(impact_score, 2),
            "dominance_factor": round(dominance_factor, 3),
            "pressure_indicator": pressure_indicator,
            "market_sentiment": market_sentiment,
            "smart_money_net_flow": smart_money_net,
            "total_activity": total_net_activity
        }
    
    def _analyze_smart_money_signals(
        self, 
        current_data: Dict[str, Any], 
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """스마트 머니 신호 분석"""
        
        current_foreign = current_data.get("foreign_net_buy_amount", 0)
        current_institution = current_data.get("institution_net_buy_amount", 0)
        current_smart_money = current_foreign + current_institution
        
        # 과거 스마트 머니 플로우
        historical_smart_money = []
        for data in historical_data[-5:]:  # 최근 5개 데이터
            flow = data.get("foreign_net", 0) + data.get("institution_net", 0)
            historical_smart_money.append(flow)
        
        # 신호 방향
        if current_smart_money > self.config.analysis.smart_money_threshold:
            signal_direction = "BUY"
        elif current_smart_money < -self.config.analysis.smart_money_threshold:
            signal_direction = "SELL"
        else:
            signal_direction = "NEUTRAL"
        
        # 신호 강도 (1-10)
        signal_strength = min(10, max(1, abs(current_smart_money) / self.intensity_thresholds["low"] * 2))
        
        # 신뢰도 계산 (0-1)
        confidence_level = self._calculate_signal_confidence(current_smart_money, historical_smart_money)
        
        return {
            "signal_direction": signal_direction,
            "signal_strength": round(signal_strength, 2),
            "confidence_level": round(confidence_level, 3),
            "foreign_flow": current_foreign,
            "institutional_flow": current_institution,
            "total_smart_money_flow": current_smart_money
        }
    
    def _generate_market_overview(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """시장 개요 생성"""
        
        foreign_net = current_data.get("foreign_net_buy_amount", 0)
        institution_net = current_data.get("institution_net_buy_amount", 0)
        individual_net = current_data.get("individual_net_buy_amount", 0)
        program_net = current_data.get("program_net_buy_amount", 0)
        
        smart_money_net = foreign_net + institution_net
        total_activity = abs(foreign_net) + abs(institution_net) + abs(individual_net) + abs(program_net)
        
        return {
            "total_foreign_net": foreign_net,
            "total_institution_net": institution_net,
            "total_individual_net": individual_net,
            "total_program_net": program_net,
            "smart_money_net": smart_money_net,
            "total_activity_volume": total_activity,
            "foreign_ratio": round(abs(foreign_net) / total_activity * 100, 2) if total_activity > 0 else 0,
            "institution_ratio": round(abs(institution_net) / total_activity * 100, 2) if total_activity > 0 else 0,
            "individual_ratio": round(abs(individual_net) / total_activity * 100, 2) if total_activity > 0 else 0
        }
    
    # 헬퍼 메서드들
    def _validate_parameters(self, stock_code: Optional[str], investor_type: str, period: str, market: str):
        """파라미터 검증"""
        if stock_code and not self._validate_stock_code(stock_code):
            raise ValidationException(f"Invalid stock code: {stock_code}")
        
        if not self._validate_investor_type(investor_type):
            raise ValidationException(f"Invalid investor type: {investor_type}")
        
        if not self._validate_period(period):
            raise ValidationException(f"Invalid period: {period}")
        
        if not self._validate_market(market):
            raise ValidationException(f"Invalid market: {market}")
    
    def _validate_stock_code(self, stock_code: Optional[str]) -> bool:
        """종목코드 검증"""
        if stock_code is None:
            return True
        return isinstance(stock_code, str) and len(stock_code) == 6 and stock_code.isdigit()
    
    def _validate_investor_type(self, investor_type: str) -> bool:
        """투자자 타입 검증"""
        valid_types = ["FOREIGN", "INSTITUTION", "INDIVIDUAL", "PROGRAM", "ALL"]
        return investor_type in valid_types
    
    def _validate_period(self, period: str) -> bool:
        """기간 검증"""
        valid_periods = ["1D", "5D", "20D", "60D", "ALL"]
        return period in valid_periods
    
    def _validate_market(self, market: str) -> bool:
        """시장 검증"""
        valid_markets = ["KOSPI", "KOSDAQ", "ALL"]
        return market in valid_markets
    
    def _determine_trend_direction(self, historical_flows: List[float], current_flow: float) -> str:
        """트렌드 방향 결정"""
        if len(historical_flows) < 3:
            return "NEUTRAL"
        
        # 최근 3개 데이터와 현재 데이터 비교
        recent_flows = historical_flows[-3:] + [current_flow]
        
        increasing = 0
        decreasing = 0
        
        for i in range(1, len(recent_flows)):
            if recent_flows[i] > recent_flows[i-1]:
                increasing += 1
            elif recent_flows[i] < recent_flows[i-1]:
                decreasing += 1
        
        if increasing > decreasing:
            return "ACCUMULATING"
        elif decreasing > increasing:
            return "DISTRIBUTING"
        else:
            return "NEUTRAL"
    
    def _calculate_trend_strength(self, historical_flows: List[float], current_flow: float) -> float:
        """트렌드 강도 계산"""
        if not historical_flows:
            return 1.0
        
        # 변화율 계산
        avg_historical = statistics.mean(historical_flows)
        if avg_historical == 0:
            return 1.0
        
        change_rate = abs(current_flow - avg_historical) / abs(avg_historical)
        return min(10.0, change_rate * 10)
    
    def _calculate_consistency_score(self, historical_flows: List[float]) -> float:
        """일관성 점수 계산"""
        if len(historical_flows) < 2:
            return 0.0
        
        # 방향 일관성 계산
        direction_changes = 0
        for i in range(1, len(historical_flows)):
            if (historical_flows[i] > 0) != (historical_flows[i-1] > 0):
                direction_changes += 1
        
        consistency = 1.0 - (direction_changes / (len(historical_flows) - 1))
        return max(0.0, consistency)
    
    def _calculate_momentum_score(self, historical_flows: List[float], current_flow: float) -> float:
        """모멘텀 점수 계산"""
        if len(historical_flows) < 2:
            return 1.0
        
        # 가속도 계산
        recent_trend = historical_flows[-1] - historical_flows[-2] if len(historical_flows) >= 2 else 0
        current_acceleration = current_flow - historical_flows[-1]
        
        if recent_trend == 0:
            return 1.0
        
        momentum = abs(current_acceleration / recent_trend) if recent_trend != 0 else 1.0
        return min(10.0, max(1.0, momentum))
    
    def _calculate_intensity_level(self, amount: float) -> int:
        """거래량에 따른 강도 레벨 계산"""
        abs_amount = abs(amount)
        
        if abs_amount >= self.intensity_thresholds["very_high"]:
            return 10
        elif abs_amount >= self.intensity_thresholds["high"]:
            return 8
        elif abs_amount >= self.intensity_thresholds["medium"]:
            return 6
        elif abs_amount >= self.intensity_thresholds["low"]:
            return 4
        else:
            return max(1, int(abs_amount / self.intensity_thresholds["low"] * 4))
    
    def _calculate_signal_confidence(self, current_flow: float, historical_flows: List[float]) -> float:
        """신호 신뢰도 계산"""
        if not historical_flows:
            return 0.5
        
        # 일관성 기반 신뢰도
        same_direction_count = 0
        for flow in historical_flows:
            if (flow > 0) == (current_flow > 0):
                same_direction_count += 1
        
        direction_confidence = same_direction_count / len(historical_flows)
        
        # 크기 기반 신뢰도
        avg_magnitude = statistics.mean([abs(flow) for flow in historical_flows])
        magnitude_confidence = min(1.0, abs(current_flow) / max(avg_magnitude, 1))
        
        # 종합 신뢰도
        overall_confidence = (direction_confidence * 0.6 + magnitude_confidence * 0.4)
        return min(1.0, max(0.0, overall_confidence))
    
    def _generate_cache_key(
        self, 
        stock_code: Optional[str], 
        investor_type: str, 
        period: str, 
        market: str
    ) -> str:
        """캐시 키 생성"""
        stock_part = stock_code or "ALL"
        return f"investor_trading:{stock_part}:{investor_type}:{period}:{market}"
    
    async def _get_from_cache(
        self, 
        stock_code: Optional[str], 
        investor_type: str, 
        period: str, 
        market: str
    ) -> Optional[Dict[str, Any]]:
        """캐시에서 데이터 조회"""
        try:
            cache_key = self._generate_cache_key(stock_code, investor_type, period, market)
            cached_data = await self.cache.get(cache_key)
            
            if cached_data:
                cached_data["cached"] = True
                return cached_data
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Cache get error: {e}")
            return None
    
    async def _save_to_cache(
        self, 
        data: Dict[str, Any], 
        stock_code: Optional[str], 
        investor_type: str, 
        period: str, 
        market: str
    ) -> None:
        """캐시에 데이터 저장"""
        try:
            cache_key = self._generate_cache_key(stock_code, investor_type, period, market)
            
            # 기간에 따른 TTL 설정
            ttl_map = {
                "1D": self.config.cache.ttl_realtime,
                "5D": self.config.cache.ttl_minute,
                "20D": self.config.cache.ttl_hourly,
                "60D": self.config.cache.ttl_daily
            }
            ttl = ttl_map.get(period, self.config.cache.ttl_realtime)
            
            await self.cache.set(cache_key, data, ttl)
            
        except Exception as e:
            self.logger.warning(f"Cache set error: {e}")
    
    async def _get_multi_period_analysis(
        self, 
        stock_code: Optional[str], 
        investor_type: str, 
        market: str, 
        include_analysis: bool
    ) -> Dict[str, Any]:
        """다중 기간 분석"""
        periods = ["1D", "5D", "20D", "60D"]
        multi_period_results = {}
        
        # 각 기간별 분석을 병렬로 실행
        tasks = []
        for period in periods:
            task = self.get_investor_trading(
                stock_code=stock_code,
                investor_type=investor_type,
                period=period,
                market=market,
                include_analysis=include_analysis,
                use_cache=True
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error in {periods[i]} analysis: {result}")
                continue
            
            if result.get("success"):
                multi_period_results[periods[i]] = {
                    "trend_analysis": result.get("analysis", {}).get("trend_analysis"),
                    "intensity_score": result.get("analysis", {}).get("intensity_score"),
                    "market_impact": result.get("analysis", {}).get("market_impact")
                }
        
        return {
            "success": True,
            "stock_code": stock_code,
            "market": market,
            "investor_type": investor_type,
            "multi_period_analysis": multi_period_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _filter_analysis_by_investor_type(self, analysis: Dict[str, Any], investor_type: str) -> Dict[str, Any]:
        """투자자 타입별 분석 필터링"""
        # 전체 분석에서 특정 투자자 타입 관련 정보만 추출
        if investor_type == "FOREIGN":
            # 외국인 관련 분석만 필터링
            filtered_analysis = {
                "trend_analysis": analysis.get("trend_analysis", {}),
                "intensity_score": {
                    "foreign_intensity": analysis.get("intensity_score", {}).get("foreign_intensity", 0)
                },
                "smart_money_signal": {
                    key: value for key, value in analysis.get("smart_money_signal", {}).items()
                    if "foreign" in key.lower()
                }
            }
        elif investor_type == "INSTITUTION":
            # 기관 관련 분석만 필터링
            filtered_analysis = {
                "trend_analysis": analysis.get("trend_analysis", {}),
                "intensity_score": {
                    "institution_intensity": analysis.get("intensity_score", {}).get("institution_intensity", 0)
                },
                "smart_money_signal": {
                    key: value for key, value in analysis.get("smart_money_signal", {}).items()
                    if "institution" in key.lower()
                }
            }
        else:
            # 기본적으로는 전체 분석 반환
            filtered_analysis = analysis
        
        return filtered_analysis
    
    def _calculate_market_trend(self, current_data: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """시장 트렌드 분석"""
        # 시장 전체의 스마트 머니 트렌드 분석
        return self._calculate_trend_analysis(current_data, historical_data)
    
    def _calculate_market_sentiment(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """시장 심리 분석"""
        foreign_net = current_data.get("foreign_net_buy_amount", 0)
        institution_net = current_data.get("institution_net_buy_amount", 0)
        individual_net = current_data.get("individual_net_buy_amount", 0)
        
        smart_money_flow = foreign_net + institution_net
        total_flow = abs(foreign_net) + abs(institution_net) + abs(individual_net)
        
        # 심리 지수 계산
        if total_flow == 0:
            sentiment_score = 50  # 중립
        else:
            sentiment_score = 50 + (smart_money_flow / total_flow * 50)
        
        # 심리 상태 판정
        if sentiment_score >= 70:
            sentiment_state = "VERY_BULLISH"
        elif sentiment_score >= 55:
            sentiment_state = "BULLISH"
        elif sentiment_score >= 45:
            sentiment_state = "NEUTRAL"
        elif sentiment_score >= 30:
            sentiment_state = "BEARISH"
        else:
            sentiment_state = "VERY_BEARISH"
        
        return {
            "sentiment_score": round(sentiment_score, 2),
            "sentiment_state": sentiment_state,
            "smart_money_dominance": round(abs(smart_money_flow) / max(total_flow, 1) * 100, 2)
        }
    
    def _analyze_investor_groups(self, current_data: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """투자자 그룹 분석"""
        foreign_net = current_data.get("foreign_net_buy_amount", 0)
        institution_net = current_data.get("institution_net_buy_amount", 0)
        individual_net = current_data.get("individual_net_buy_amount", 0)
        
        # 각 그룹의 활동성 분석
        groups = {
            "foreign": {"current_flow": foreign_net, "intensity": self._calculate_intensity_level(foreign_net)},
            "institution": {"current_flow": institution_net, "intensity": self._calculate_intensity_level(institution_net)},
            "individual": {"current_flow": individual_net, "intensity": self._calculate_intensity_level(individual_net)}
        }
        
        # 가장 활발한 그룹 식별
        most_active = max(groups.keys(), key=lambda x: abs(groups[x]["current_flow"]))
        
        # 그룹 간 상관관계 분석
        correlation = self._calculate_group_correlation(current_data, historical_data)
        
        return {
            "group_activities": groups,
            "most_active_group": most_active,
            "group_correlation": correlation,
            "smart_money_alignment": "ALIGNED" if foreign_net * institution_net >= 0 else "DIVERGENT"
        }
    
    def _calculate_group_correlation(self, current_data: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """투자자 그룹 간 상관관계 계산"""
        if len(historical_data) < 3:
            return {"correlation_strength": "INSUFFICIENT_DATA"}
        
        # 과거 데이터에서 각 그룹의 플로우 추출
        foreign_flows = [data.get("foreign_net", 0) for data in historical_data[-10:]]
        institution_flows = [data.get("institution_net", 0) for data in historical_data[-10:]]
        individual_flows = [data.get("individual_net", 0) for data in historical_data[-10:]]
        
        # 간단한 상관관계 계산 (방향성 기준)
        foreign_institution_agreement = sum(
            1 for i in range(len(foreign_flows)) 
            if (foreign_flows[i] > 0) == (institution_flows[i] > 0)
        ) / len(foreign_flows)
        
        return {
            "foreign_institution_correlation": round(foreign_institution_agreement, 3),
            "correlation_strength": "HIGH" if foreign_institution_agreement > 0.7 else "MEDIUM" if foreign_institution_agreement > 0.4 else "LOW"
        }