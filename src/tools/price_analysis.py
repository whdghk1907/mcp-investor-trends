"""
가격 상관관계 분석 도구
"""
import asyncio
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import math

from ..config import Config
from ..exceptions import APIException, ValidationException, DataNotFoundException


class PriceAnalysisTool:
    """가격 상관관계 분석 도구"""
    
    def __init__(self, config: Config, api_client, database, cache):
        self.config = config
        self.api_client = api_client
        self.database = database
        self.cache = cache
        self.logger = logging.getLogger(__name__)
        
        # 분석 설정
        self.correlation_threshold = 0.7  # 강한 상관관계 기준
        self.anomaly_threshold = 2.5  # 이상 패턴 감지 기준 (표준편차 배수)
        self.min_data_points = 5  # 최소 데이터 포인트
    
    async def calculate_price_correlation(
        self,
        stock_code: str,
        period: str = "1D",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        가격과 투자자 거래의 상관관계 분석
        
        Args:
            stock_code: 종목코드
            period: 분석 기간
            use_cache: 캐시 사용 여부
            
        Returns:
            상관관계 분석 결과
        """
        
        try:
            # 파라미터 검증
            if not self._validate_stock_code(stock_code):
                raise ValidationException(f"Invalid stock code: {stock_code}")
            
            # 캐시 확인
            if use_cache:
                cache_key = f"price_correlation:{stock_code}:{period}"
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    cached_result["cached"] = True
                    return cached_result
            
            # 가격 데이터 조회
            price_data = await self._fetch_price_data(stock_code, period)
            
            # 투자자 거래 데이터 조회
            trading_data = await self._fetch_trading_data(stock_code, period)
            
            # 데이터 충분성 확인
            if len(price_data) < self.min_data_points or len(trading_data) < self.min_data_points:
                raise DataNotFoundException("Insufficient data for correlation analysis")
            
            # 상관관계 분석 수행
            correlation_analysis = self._perform_correlation_analysis(price_data, trading_data)
            
            # 결과 구성
            result = {
                "success": True,
                "stock_code": stock_code,
                "period": period,
                "correlation_analysis": correlation_analysis,
                "data_points": len(price_data),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # 캐시에 저장
            if use_cache:
                ttl = self._get_cache_ttl(period)
                await self.cache.set(cache_key, result, ttl)
            
            return result
            
        except (ValidationException, DataNotFoundException, APIException) as e:
            self.logger.error(f"Error in price correlation analysis: {e}")
            return {
                "success": False,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e)
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Unexpected error in price correlation: {e}")
            return {
                "success": False,
                "error": {
                    "type": "UnexpectedError",
                    "message": "An unexpected error occurred"
                },
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_comprehensive_analysis(
        self,
        stock_code: str,
        period: str = "1D"
    ) -> Dict[str, Any]:
        """종합 가격 분석 보고서 생성"""
        
        try:
            # 기본 상관관계 분석
            correlation_result = await self.calculate_price_correlation(stock_code, period)
            
            if not correlation_result.get("success"):
                return correlation_result
            
            # 추가 분석 수행
            price_data = await self._fetch_price_data(stock_code, period)
            trading_data = await self._fetch_trading_data(stock_code, period)
            
            # 가격 영향도 분석
            price_impact = self._analyze_price_impact_comprehensive(price_data, trading_data)
            
            # 예측 분석
            prediction = self._generate_price_prediction(price_data, trading_data)
            
            # 타이밍 분석
            timing_analysis = self._analyze_optimal_timing(price_data, trading_data)
            
            # 이상 패턴 감지
            anomaly_detection = self._detect_comprehensive_anomalies(price_data, trading_data)
            
            # 스마트 머니 지표
            smart_money_indicator = self._calculate_comprehensive_smart_money_indicator(price_data, trading_data)
            
            # 종합 요약
            summary = self._generate_analysis_summary(
                correlation_result["correlation_analysis"],
                price_impact,
                prediction,
                anomaly_detection
            )
            
            return {
                "success": True,
                "stock_code": stock_code,
                "period": period,
                "correlation_analysis": correlation_result["correlation_analysis"],
                "price_impact_analysis": price_impact,
                "prediction_analysis": prediction,
                "timing_analysis": timing_analysis,
                "anomaly_detection": anomaly_detection,
                "smart_money_indicator": smart_money_indicator,
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            return {
                "success": False,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e)
                },
                "timestamp": datetime.now().isoformat()
            }
    
    async def _fetch_price_data(self, stock_code: str, period: str) -> List[Dict[str, Any]]:
        """가격 데이터 조회"""
        try:
            hours_map = {"1D": 24, "5D": 120, "20D": 480, "60D": 1440}
            hours = hours_map.get(period, 24)
            
            price_data = await self.database.get_price_history(
                stock_code=stock_code,
                hours=hours
            )
            
            return price_data or []
            
        except Exception as e:
            self.logger.error(f"Error fetching price data: {e}")
            raise APIException(f"Failed to fetch price data: {str(e)}")
    
    async def _fetch_trading_data(self, stock_code: str, period: str) -> List[Dict[str, Any]]:
        """투자자 거래 데이터 조회"""
        try:
            hours_map = {"1D": 24, "5D": 120, "20D": 480, "60D": 1440}
            hours = hours_map.get(period, 24)
            
            trading_data = await self.database.get_investor_trading_history(
                stock_code=stock_code,
                hours=hours
            )
            
            return trading_data or []
            
        except Exception as e:
            self.logger.error(f"Error fetching trading data: {e}")
            raise APIException(f"Failed to fetch trading data: {str(e)}")
    
    def _perform_correlation_analysis(
        self, 
        price_data: List[Dict[str, Any]], 
        trading_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """상관관계 분석 수행"""
        
        # 데이터 정렬 및 매칭
        aligned_data = self._align_price_trading_data(price_data, trading_data)
        
        if len(aligned_data) < self.min_data_points:
            return {"error": "Insufficient aligned data points"}
        
        # 가격 변화율 계산
        price_changes = self._calculate_price_changes(aligned_data)
        
        # 투자자별 순매수 금액 추출
        foreign_flows = [data["foreign_net"] for data in aligned_data]
        institution_flows = [data["institution_net"] for data in aligned_data]
        individual_flows = [data.get("individual_net", 0) for data in aligned_data]
        smart_money_flows = [f + i for f, i in zip(foreign_flows, institution_flows)]
        
        # 상관계수 계산
        correlations = {
            "foreign_correlation": self._calculate_pearson_correlation(price_changes, foreign_flows),
            "institution_correlation": self._calculate_pearson_correlation(price_changes, institution_flows),
            "individual_correlation": self._calculate_pearson_correlation(price_changes, individual_flows),
            "smart_money_correlation": self._calculate_pearson_correlation(price_changes, smart_money_flows)
        }
        
        # 상관관계 강도 분석
        correlation_strength = self._analyze_correlation_strength(correlations)
        
        # 시차 분석 (Lead-Lag)
        lead_lag_analysis = self._analyze_lead_lag_relationship(price_changes, smart_money_flows)
        
        return {
            **correlations,
            "correlation_strength": correlation_strength,
            "lead_lag_analysis": lead_lag_analysis,
            "statistical_significance": self._test_statistical_significance(price_changes, smart_money_flows)
        }
    
    def _analyze_price_impact(
        self, 
        current_price: float, 
        previous_price: float, 
        trading_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """가격 영향도 분석"""
        
        price_change = current_price - previous_price
        price_change_percent = (price_change / previous_price * 100) if previous_price != 0 else 0
        
        # 스마트 머니 플로우
        smart_money_flow = (
            trading_data.get("foreign_net_buy_amount", 0) + 
            trading_data.get("institution_net_buy_amount", 0)
        )
        
        # 영향도 강도 계산
        total_flow = abs(smart_money_flow)
        impact_intensity = min(10, total_flow / self.config.analysis.smart_money_threshold * 5)
        
        # 방향성 일치도
        price_direction = "UP" if price_change > 0 else "DOWN" if price_change < 0 else "NEUTRAL"
        flow_direction = "UP" if smart_money_flow > 0 else "DOWN" if smart_money_flow < 0 else "NEUTRAL"
        directional_consistency = "CONSISTENT" if price_direction == flow_direction else "INCONSISTENT"
        
        # 예상 방향
        if abs(smart_money_flow) > self.config.analysis.smart_money_threshold:
            predicted_direction = "UP" if smart_money_flow > 0 else "DOWN"
        else:
            predicted_direction = "NEUTRAL"
        
        return {
            "price_change": price_change,
            "price_change_percent": round(price_change_percent, 2),
            "impact_intensity": round(impact_intensity, 2),
            "directional_consistency": directional_consistency,
            "predicted_direction": predicted_direction,
            "smart_money_flow": smart_money_flow
        }
    
    def _calculate_volume_price_relationship(
        self, 
        price_data: List[float], 
        volume_data: List[float]
    ) -> Dict[str, Any]:
        """거래량-가격 관계 분석"""
        
        if len(price_data) != len(volume_data) or len(price_data) < 2:
            return {"error": "Invalid data for volume-price analysis"}
        
        # 거래량-가격 상관관계
        volume_price_correlation = self._calculate_pearson_correlation(price_data, volume_data)
        
        # 가격 변화와 거래량 변화 분석
        price_changes = [price_data[i] - price_data[i-1] for i in range(1, len(price_data))]
        volume_changes = [volume_data[i] - volume_data[i-1] for i in range(1, len(volume_data))]
        
        # 트렌드 확인
        positive_price_moves = sum(1 for p in price_changes if p > 0)
        positive_volume_moves = sum(1 for v in volume_changes if v > 0)
        
        if len(price_changes) > 0:
            trend_confirmation_rate = min(positive_price_moves, positive_volume_moves) / len(price_changes)
            if trend_confirmation_rate > 0.7:
                trend_confirmation = "CONFIRMED"
            elif trend_confirmation_rate > 0.4:
                trend_confirmation = "WEAK"
            else:
                trend_confirmation = "NOT_CONFIRMED"
        else:
            trend_confirmation = "INSUFFICIENT_DATA"
        
        # 발산 신호 감지
        divergence_signals = []
        for i in range(len(price_changes)):
            if (price_changes[i] > 0 and volume_changes[i] < 0) or (price_changes[i] < 0 and volume_changes[i] > 0):
                divergence_signals.append(i)
        
        return {
            "volume_price_correlation": round(volume_price_correlation, 3),
            "trend_confirmation": trend_confirmation,
            "divergence_signals": divergence_signals,
            "confirmation_rate": round(trend_confirmation_rate, 3) if 'trend_confirmation_rate' in locals() else 0
        }
    
    def _predict_price_movement(
        self, 
        historical_data: Dict[str, List], 
        current_trading: Dict[str, Any]
    ) -> Dict[str, Any]:
        """가격 움직임 예측"""
        
        prices = historical_data.get("prices", [])
        foreign_flows = historical_data.get("foreign_flows", [])
        institution_flows = historical_data.get("institution_flows", [])
        
        if len(prices) < 3:
            return {
                "predicted_direction": "NEUTRAL",
                "confidence_score": 0.0,
                "momentum_indicator": "WEAK"
            }
        
        # 현재 스마트 머니 플로우
        current_smart_money = (
            current_trading.get("foreign_net_buy_amount", 0) + 
            current_trading.get("institution_net_buy_amount", 0)
        )
        
        # 과거 패턴 분석
        smart_money_flows = [f + i for f, i in zip(foreign_flows, institution_flows)]
        price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # 상관관계 기반 예측
        correlation = self._calculate_pearson_correlation(price_changes, smart_money_flows[1:])
        
        # 예측 방향
        if abs(correlation) > 0.5 and abs(current_smart_money) > self.config.analysis.smart_money_threshold:
            if correlation > 0:  # 양의 상관관계
                predicted_direction = "BULLISH" if current_smart_money > 0 else "BEARISH"
            else:  # 음의 상관관계
                predicted_direction = "BEARISH" if current_smart_money > 0 else "BULLISH"
        else:
            predicted_direction = "NEUTRAL"
        
        # 신뢰도 점수
        confidence_score = min(1.0, abs(correlation) * (abs(current_smart_money) / self.config.analysis.smart_money_threshold))
        
        # 모멘텀 지표
        recent_momentum = statistics.mean(price_changes[-3:]) if len(price_changes) >= 3 else 0
        if abs(recent_momentum) > statistics.stdev(price_changes) if len(price_changes) > 1 else 0:
            momentum_indicator = "STRONG"
        elif abs(recent_momentum) > statistics.stdev(price_changes) * 0.5 if len(price_changes) > 1 else 0:
            momentum_indicator = "MODERATE"
        else:
            momentum_indicator = "WEAK"
        
        # 지지/저항 수준
        support_resistance = self._calculate_support_resistance(prices)
        
        return {
            "predicted_direction": predicted_direction,
            "confidence_score": round(confidence_score, 3),
            "support_resistance": support_resistance,
            "momentum_indicator": momentum_indicator,
            "correlation_strength": round(abs(correlation), 3)
        }
    
    def _analyze_market_timing(self, trading_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """시장 타이밍 분석"""
        
        if len(trading_patterns) < 3:
            return {
                "optimal_trading_hours": [],
                "timing_efficiency": 0.0,
                "pattern_strength": "WEAK"
            }
        
        # 시간대별 효율성 계산
        hour_efficiency = {}
        for pattern in trading_patterns:
            hour = pattern.get("hour")
            net_flow = pattern.get("foreign_net", 0)
            price_change = pattern.get("price_change", 0)
            
            if hour is not None:
                # 효율성 = 가격 변화와 플로우의 일치도
                efficiency = abs(price_change) * (1 if net_flow * price_change > 0 else -1)
                if hour in hour_efficiency:
                    hour_efficiency[hour].append(efficiency)
                else:
                    hour_efficiency[hour] = [efficiency]
        
        # 평균 효율성 계산
        avg_efficiency = {}
        for hour, efficiencies in hour_efficiency.items():
            avg_efficiency[hour] = statistics.mean(efficiencies)
        
        # 최적 거래 시간 추출
        sorted_hours = sorted(avg_efficiency.items(), key=lambda x: x[1], reverse=True)
        optimal_hours = [hour for hour, eff in sorted_hours[:3] if eff > 0]
        
        # 전체 타이밍 효율성
        all_efficiencies = [eff for effs in hour_efficiency.values() for eff in effs]
        timing_efficiency = max(0, statistics.mean(all_efficiencies)) if all_efficiencies else 0
        
        # 패턴 강도
        if timing_efficiency > 1.0:
            pattern_strength = "STRONG"
        elif timing_efficiency > 0.5:
            pattern_strength = "MODERATE"
        else:
            pattern_strength = "WEAK"
        
        return {
            "optimal_trading_hours": optimal_hours,
            "timing_efficiency": round(timing_efficiency, 3),
            "pattern_strength": pattern_strength,
            "hour_analysis": {str(k): round(v, 3) for k, v in avg_efficiency.items()}
        }
    
    def _calculate_smart_money_indicator(
        self, 
        price_changes: List[float], 
        smart_money_flows: List[float]
    ) -> Dict[str, Any]:
        """스마트 머니 지표 계산"""
        
        if len(price_changes) != len(smart_money_flows) or len(price_changes) < 3:
            return {
                "smart_money_index": 50,
                "accuracy_rate": 0.0,
                "signal_strength": 1,
                "market_leadership": "COINCIDENT"
            }
        
        # 방향 일치 횟수
        correct_predictions = 0
        total_predictions = 0
        
        for i in range(len(price_changes)):
            if abs(smart_money_flows[i]) > self.config.analysis.smart_money_threshold * 0.1:
                total_predictions += 1
                if (price_changes[i] > 0 and smart_money_flows[i] > 0) or (price_changes[i] < 0 and smart_money_flows[i] < 0):
                    correct_predictions += 1
        
        # 정확도 계산
        accuracy_rate = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        # 스마트 머니 지수 (0-100)
        correlation = abs(self._calculate_pearson_correlation(price_changes, smart_money_flows))
        smart_money_index = correlation * accuracy_rate * 100
        
        # 신호 강도
        avg_flow = statistics.mean([abs(f) for f in smart_money_flows])
        signal_strength = min(10, avg_flow / self.config.analysis.smart_money_threshold * 5)
        
        # 선행/후행 분석
        lead_lag = self._analyze_lead_lag_relationship(price_changes, smart_money_flows)
        if lead_lag.get("smart_money_leads", False):
            market_leadership = "LEADING"
        elif lead_lag.get("price_leads", False):
            market_leadership = "LAGGING"
        else:
            market_leadership = "COINCIDENT"
        
        return {
            "smart_money_index": round(smart_money_index, 2),
            "accuracy_rate": round(accuracy_rate, 3),
            "signal_strength": round(signal_strength, 2),
            "market_leadership": market_leadership,
            "correlation": round(correlation, 3)
        }
    
    def _detect_anomalies(
        self, 
        price_data: List[float], 
        trading_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """이상 패턴 감지"""
        
        if len(price_data) < 5 or len(trading_data) < 5:
            return {
                "anomaly_detected": False,
                "anomaly_type": "NONE",
                "anomaly_score": 0,
                "affected_periods": []
            }
        
        anomalies = []
        
        # 가격 급등/급락 감지
        price_changes = [price_data[i] - price_data[i-1] for i in range(1, len(price_data))]
        price_std = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
        price_mean = statistics.mean(price_changes)
        
        for i, change in enumerate(price_changes):
            if abs(change - price_mean) > self.anomaly_threshold * price_std:
                anomalies.append({
                    "type": "PRICE_SPIKE" if change > 0 else "PRICE_DROP",
                    "period": i + 1,
                    "severity": abs(change - price_mean) / price_std
                })
        
        # 거래량 급증 감지
        flows = [data.get("foreign_net", 0) + data.get("institution_net", 0) for data in trading_data]
        if flows:
            flow_std = statistics.stdev(flows) if len(flows) > 1 else 0
            flow_mean = statistics.mean(flows)
            
            for i, flow in enumerate(flows):
                if abs(flow - flow_mean) > self.anomaly_threshold * flow_std:
                    anomalies.append({
                        "type": "FLOW_SPIKE",
                        "period": i,
                        "severity": abs(flow - flow_mean) / flow_std if flow_std > 0 else 0
                    })
        
        # 패턴 브레이크 감지
        if len(price_changes) >= 3 and len(flows) >= 3:
            recent_correlation = self._calculate_pearson_correlation(price_changes[-3:], flows[-3:])
            overall_correlation = self._calculate_pearson_correlation(price_changes, flows[:len(price_changes)])
            
            if abs(recent_correlation - overall_correlation) > 0.5:
                anomalies.append({
                    "type": "PATTERN_BREAK",
                    "period": len(price_changes) - 1,
                    "severity": abs(recent_correlation - overall_correlation)
                })
        
        # 최고 심각도 이상 패턴
        if anomalies:
            max_anomaly = max(anomalies, key=lambda x: x["severity"])
            return {
                "anomaly_detected": True,
                "anomaly_type": max_anomaly["type"],
                "anomaly_score": round(min(10, max_anomaly["severity"]), 2),
                "affected_periods": [a["period"] for a in anomalies],
                "total_anomalies": len(anomalies)
            }
        else:
            return {
                "anomaly_detected": False,
                "anomaly_type": "NONE",
                "anomaly_score": 0,
                "affected_periods": []
            }
    
    # 헬퍼 메서드들
    def _validate_stock_code(self, stock_code: str) -> bool:
        """종목 코드 검증"""
        return isinstance(stock_code, str) and len(stock_code) == 6 and stock_code.isdigit()
    
    def _calculate_pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """피어슨 상관계수 계산"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        try:
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, y))
            sum_x2 = sum(xi * xi for xi in x)
            sum_y2 = sum(yi * yi for yi in y)
            
            numerator = n * sum_xy - sum_x * sum_y
            denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
            
            return numerator / denominator if denominator != 0 else 0.0
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def _calculate_spearman_correlation(self, x: List[float], y: List[float]) -> float:
        """스피어만 상관계수 계산"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        try:
            # 순위 계산
            def rank(data):
                sorted_data = sorted(enumerate(data), key=lambda x: x[1])
                ranks = [0] * len(data)
                for rank_val, (original_idx, _) in enumerate(sorted_data, 1):
                    ranks[original_idx] = rank_val
                return ranks
            
            rank_x = rank(x)
            rank_y = rank(y)
            
            return self._calculate_pearson_correlation(rank_x, rank_y)
        except Exception:
            return 0.0
    
    def _align_price_trading_data(
        self, 
        price_data: List[Dict[str, Any]], 
        trading_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """가격 데이터와 거래 데이터 시간 정렬"""
        
        # 시간으로 정렬
        price_data.sort(key=lambda x: x.get("timestamp", datetime.min))
        trading_data.sort(key=lambda x: x.get("timestamp", datetime.min))
        
        aligned = []
        
        for trading in trading_data:
            trading_time = trading.get("timestamp")
            if not trading_time:
                continue
            
            # 가장 가까운 시간의 가격 데이터 찾기
            closest_price = None
            min_diff = timedelta.max
            
            for price in price_data:
                price_time = price.get("timestamp")
                if not price_time:
                    continue
                
                time_diff = abs(price_time - trading_time)
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest_price = price
            
            if closest_price and min_diff < timedelta(hours=1):  # 1시간 이내
                aligned.append({
                    "timestamp": trading_time,
                    "price": closest_price.get("close_price", 0),
                    "volume": closest_price.get("volume", 0),
                    "foreign_net": trading.get("foreign_net", 0),
                    "institution_net": trading.get("institution_net", 0),
                    "individual_net": trading.get("individual_net", 0)
                })
        
        return aligned
    
    def _calculate_price_changes(self, aligned_data: List[Dict[str, Any]]) -> List[float]:
        """가격 변화율 계산"""
        if len(aligned_data) < 2:
            return []
        
        price_changes = []
        for i in range(1, len(aligned_data)):
            prev_price = aligned_data[i-1].get("price", 0)
            curr_price = aligned_data[i].get("price", 0)
            
            if prev_price > 0:
                change_percent = (curr_price - prev_price) / prev_price * 100
                price_changes.append(change_percent)
        
        return price_changes
    
    def _analyze_correlation_strength(self, correlations: Dict[str, float]) -> Dict[str, str]:
        """상관관계 강도 분석"""
        strength_map = {}
        
        for key, corr in correlations.items():
            abs_corr = abs(corr)
            if abs_corr >= 0.8:
                strength = "VERY_STRONG"
            elif abs_corr >= 0.6:
                strength = "STRONG"
            elif abs_corr >= 0.4:
                strength = "MODERATE"
            elif abs_corr >= 0.2:
                strength = "WEAK"
            else:
                strength = "VERY_WEAK"
            
            strength_map[key.replace("_correlation", "_strength")] = strength
        
        return strength_map
    
    def _analyze_lead_lag_relationship(
        self, 
        price_changes: List[float], 
        smart_money_flows: List[float]
    ) -> Dict[str, Any]:
        """선행/후행 관계 분석"""
        
        if len(price_changes) < 3 or len(smart_money_flows) < 3:
            return {"smart_money_leads": False, "price_leads": False, "lag_periods": 0}
        
        max_corr = 0
        best_lag = 0
        
        # -2 ~ +2 기간 시차 분석
        for lag in range(-2, 3):
            if lag == 0:
                corr = abs(self._calculate_pearson_correlation(price_changes, smart_money_flows))
            elif lag > 0:  # 스마트 머니가 선행
                if len(smart_money_flows) > lag:
                    corr = abs(self._calculate_pearson_correlation(
                        price_changes[lag:], smart_money_flows[:-lag]
                    ))
                else:
                    continue
            else:  # 가격이 선행
                lag_abs = abs(lag)
                if len(price_changes) > lag_abs:
                    corr = abs(self._calculate_pearson_correlation(
                        price_changes[:-lag_abs], smart_money_flows[lag_abs:]
                    ))
                else:
                    continue
            
            if corr > max_corr:
                max_corr = corr
                best_lag = lag
        
        return {
            "smart_money_leads": best_lag > 0,
            "price_leads": best_lag < 0,
            "lag_periods": abs(best_lag),
            "max_correlation": round(max_corr, 3)
        }
    
    def _test_statistical_significance(
        self, 
        x: List[float], 
        y: List[float], 
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """통계적 유의성 검정"""
        
        correlation = self._calculate_pearson_correlation(x, y)
        n = len(x)
        
        if n < 3:
            return {"significant": False, "p_value": 1.0, "confidence_level": 0.0}
        
        # t-검정
        t_stat = correlation * math.sqrt((n - 2) / (1 - correlation**2)) if abs(correlation) < 1 else float('inf')
        
        # 간단한 p-value 근사 (정확한 계산을 위해서는 scipy 필요)
        if abs(t_stat) > 2.57:  # 99% 신뢰수준
            confidence_level = 0.99
            p_value = 0.01
        elif abs(t_stat) > 1.96:  # 95% 신뢰수준
            confidence_level = 0.95
            p_value = 0.05
        elif abs(t_stat) > 1.64:  # 90% 신뢰수준
            confidence_level = 0.90
            p_value = 0.10
        else:
            confidence_level = 0.0
            p_value = 1.0
        
        return {
            "significant": p_value < alpha,
            "p_value": p_value,
            "confidence_level": confidence_level,
            "t_statistic": round(t_stat, 3)
        }
    
    def _get_cache_ttl(self, period: str) -> int:
        """기간에 따른 캐시 TTL 반환"""
        ttl_map = {
            "1D": self.config.cache.ttl_realtime,
            "5D": self.config.cache.ttl_minute * 5,
            "20D": self.config.cache.ttl_hourly,
            "60D": self.config.cache.ttl_daily
        }
        return ttl_map.get(period, self.config.cache.ttl_realtime)
    
    def _analyze_price_impact_comprehensive(
        self, 
        price_data: List[Dict[str, Any]], 
        trading_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """종합 가격 영향도 분석"""
        
        if len(price_data) < 2 or len(trading_data) < 2:
            return {"error": "Insufficient data for price impact analysis"}
        
        current_price = price_data[-1].get("close_price", 0)
        previous_price = price_data[-2].get("close_price", 0)
        current_trading = trading_data[-1]
        
        return self._analyze_price_impact(current_price, previous_price, current_trading)
    
    def _generate_price_prediction(
        self, 
        price_data: List[Dict[str, Any]], 
        trading_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """가격 예측 생성"""
        
        if len(price_data) < 3 or len(trading_data) < 3:
            return {"error": "Insufficient data for prediction"}
        
        historical_data = {
            "prices": [p.get("close_price", 0) for p in price_data],
            "foreign_flows": [t.get("foreign_net", 0) for t in trading_data],
            "institution_flows": [t.get("institution_net", 0) for t in trading_data]
        }
        
        current_trading = trading_data[-1]
        
        return self._predict_price_movement(historical_data, current_trading)
    
    def _analyze_optimal_timing(
        self, 
        price_data: List[Dict[str, Any]], 
        trading_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """최적 타이밍 분석"""
        
        if len(price_data) < 3 or len(trading_data) < 3:
            return {"error": "Insufficient data for timing analysis"}
        
        # 시간대별 패턴 구성
        patterns = []
        for i, (price, trading) in enumerate(zip(price_data, trading_data)):
            if i > 0:
                prev_price = price_data[i-1].get("close_price", 0)
                curr_price = price.get("close_price", 0)
                price_change = (curr_price - prev_price) / prev_price * 100 if prev_price > 0 else 0
                
                patterns.append({
                    "hour": price.get("timestamp", datetime.now()).hour,
                    "foreign_net": trading.get("foreign_net", 0),
                    "price_change": price_change
                })
        
        return self._analyze_market_timing(patterns)
    
    def _detect_comprehensive_anomalies(
        self, 
        price_data: List[Dict[str, Any]], 
        trading_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """종합 이상 패턴 감지"""
        
        if len(price_data) < 5 or len(trading_data) < 5:
            return {"error": "Insufficient data for anomaly detection"}
        
        prices = [p.get("close_price", 0) for p in price_data]
        
        return self._detect_anomalies(prices, trading_data)
    
    def _calculate_comprehensive_smart_money_indicator(
        self, 
        price_data: List[Dict[str, Any]], 
        trading_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """종합 스마트 머니 지표 계산"""
        
        if len(price_data) < 3 or len(trading_data) < 3:
            return {"error": "Insufficient data for smart money indicator"}
        
        aligned_data = self._align_price_trading_data(price_data, trading_data)
        price_changes = self._calculate_price_changes(aligned_data)
        smart_money_flows = [
            data.get("foreign_net", 0) + data.get("institution_net", 0) 
            for data in aligned_data[1:]  # price_changes와 길이 맞추기
        ]
        
        return self._calculate_smart_money_indicator(price_changes, smart_money_flows)
    
    def _calculate_support_resistance(self, prices: List[float]) -> Dict[str, float]:
        """지지/저항 수준 계산"""
        
        if len(prices) < 5:
            return {"support": 0, "resistance": 0}
        
        # 간단한 지지/저항 계산
        recent_prices = prices[-10:] if len(prices) >= 10 else prices
        support = min(recent_prices)
        resistance = max(recent_prices)
        
        return {
            "support": support,
            "resistance": resistance,
            "current_level": prices[-1] if prices else 0
        }
    
    def _generate_analysis_summary(
        self, 
        correlation_analysis: Dict[str, Any],
        price_impact: Dict[str, Any],
        prediction: Dict[str, Any],
        anomaly_detection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """분석 요약 생성"""
        
        key_insights = []
        
        # 상관관계 인사이트
        smart_money_corr = correlation_analysis.get("smart_money_correlation", 0)
        if abs(smart_money_corr) > 0.7:
            key_insights.append(f"Strong correlation ({smart_money_corr:.2f}) between smart money flow and price movement")
        
        # 가격 영향도 인사이트
        if price_impact.get("directional_consistency") == "CONSISTENT":
            key_insights.append("Price movement aligns with smart money flow direction")
        
        # 예측 인사이트
        prediction_direction = prediction.get("predicted_direction", "NEUTRAL")
        confidence = prediction.get("confidence_score", 0)
        if confidence > 0.7:
            key_insights.append(f"High confidence {prediction_direction.lower()} prediction ({confidence:.1%})")
        
        # 이상 패턴 인사이트
        if anomaly_detection.get("anomaly_detected"):
            anomaly_type = anomaly_detection.get("anomaly_type")
            key_insights.append(f"Anomaly detected: {anomaly_type}")
        
        # 추천사항
        if prediction_direction == "BULLISH" and confidence > 0.6:
            recommendation = "POSITIVE: Strong upward signals detected"
        elif prediction_direction == "BEARISH" and confidence > 0.6:
            recommendation = "NEGATIVE: Strong downward signals detected"
        elif anomaly_detection.get("anomaly_detected"):
            recommendation = "CAUTION: Unusual patterns require careful monitoring"
        else:
            recommendation = "NEUTRAL: Mixed or weak signals"
        
        return {
            "key_insights": key_insights,
            "recommendation": recommendation,
            "overall_sentiment": prediction_direction,
            "confidence_level": confidence,
            "analysis_quality": "HIGH" if len(key_insights) >= 2 else "MODERATE" if len(key_insights) >= 1 else "LOW"
        }