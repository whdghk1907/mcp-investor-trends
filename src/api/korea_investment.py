"""
한국투자증권 OpenAPI 클라이언트
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

from ..exceptions import APIException, AuthenticationException, RateLimitException


class KoreaInvestmentAPI:
    """한국투자증권 API 클라이언트"""
    
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        self.session = None
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        await self._get_access_token()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
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
        
        try:
            async with self.session.post(url, json=data) as response:
                result = await response.json()
                
                if "access_token" in result:
                    self.access_token = result["access_token"]
                else:
                    raise AuthenticationException(
                        "Failed to get access token",
                        auth_method="CLIENT_CREDENTIALS",
                        details=result
                    )
        except aiohttp.ClientError as e:
            raise AuthenticationException(
                f"Failed to get access token: {str(e)}",
                auth_method="CLIENT_CREDENTIALS"
            )
    
    async def get_investor_trading(
        self, 
        stock_code: Optional[str] = None,
        market: str = "ALL"
    ) -> Dict[str, Any]:
        """투자자별 매매 동향 조회"""
        
        # 파라미터 검증
        if stock_code and not self._validate_stock_code(stock_code):
            raise ValueError(f"Invalid stock code: {stock_code}")
        
        if not self._validate_market_code(market):
            raise ValueError(f"Invalid market code: {market}")
        
        # 헤더 설정
        headers = {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": self._get_tr_id("investor_trading", stock_code=stock_code),
            "content-type": "application/json"
        }
        
        # 파라미터 설정
        params = {}
        if stock_code:
            params["fid_cond_mrkt_div_code"] = "J"
            params["fid_input_iscd"] = stock_code
        else:
            params["fid_cond_mrkt_div_code"] = self._convert_market_code(market)
            
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/investor-trading"
        
        return await self._make_request("GET", url, headers=headers, params=params)
    
    async def get_program_trading(self, market: str = "ALL") -> Dict[str, Any]:
        """프로그램 매매 동향 조회"""
        
        if not self._validate_market_code(market):
            raise ValueError(f"Invalid market code: {market}")
        
        headers = {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": self._get_tr_id("program_trading"),
            "content-type": "application/json"
        }
        
        params = {
            "fid_cond_mrkt_div_code": self._convert_market_code(market),
            "fid_input_date_1": self._format_date(datetime.now())
        }
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/program-trading"
        
        return await self._make_request("GET", url, headers=headers, params=params)
    
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """HTTP 요청 실행"""
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self.session.request(
                    method, url, headers=headers, params=params, json=data
                ) as response:
                    
                    response_data = await response.json()
                    
                    # 성공 응답 처리
                    if response.status == 200:
                        return response_data
                    
                    # 속도 제한 에러
                    elif response.status == 429:
                        raise RateLimitException(
                            "Rate limit exceeded",
                            status_code=response.status,
                            endpoint=url
                        )
                    
                    # 인증 에러
                    elif response.status == 401:
                        raise AuthenticationException(
                            "Authentication failed",
                            auth_method="BEARER_TOKEN",
                            details=response_data
                        )
                    
                    # 기타 클라이언트/서버 에러
                    else:
                        if self._should_retry(response.status, attempt):
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        else:
                            raise APIException(
                                "API request failed",
                                status_code=response.status,
                                endpoint=url,
                                details=response_data
                            )
            
            except aiohttp.ClientConnectionError as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise APIException(
                        f"Connection failed: {str(e)}",
                        endpoint=url
                    )
            
            except asyncio.TimeoutError as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise APIException(
                        f"Request timeout: {str(e)}",
                        endpoint=url
                    )
    
    def _validate_stock_code(self, stock_code: str) -> bool:
        """종목코드 유효성 검증"""
        if not stock_code:
            return False
        return bool(re.match(r'^\d{6}$', stock_code))
    
    def _validate_market_code(self, market_code: str) -> bool:
        """시장코드 유효성 검증"""
        valid_markets = ["ALL", "KOSPI", "KOSDAQ", "J", "Q"]
        return market_code in valid_markets
    
    def _convert_market_code(self, market: str) -> str:
        """시장코드 변환"""
        conversion_map = {
            "ALL": "ALL",
            "KOSPI": "J",
            "KOSDAQ": "Q",
            "J": "J",
            "Q": "Q"
        }
        return conversion_map.get(market, "ALL")
    
    def _get_tr_id(self, endpoint: str, **kwargs) -> str:
        """엔드포인트별 TR ID 반환"""
        tr_id_map = {
            "investor_trading": {
                "with_stock": "FHKST130200000",
                "without_stock": "FHKST130100000"
            },
            "program_trading": "FHKST130300000"
        }
        
        if endpoint == "investor_trading":
            stock_code = kwargs.get("stock_code")
            if stock_code:
                return tr_id_map[endpoint]["with_stock"]
            else:
                return tr_id_map[endpoint]["without_stock"]
        
        return tr_id_map.get(endpoint, "FHKST000000000")
    
    def _should_retry(self, status_code: int, attempt: int) -> bool:
        """재시도 여부 판단"""
        # 재시도 가능한 상태 코드 (5xx 서버 에러)
        retryable_codes = [500, 502, 503, 504]
        
        # 재시도 한도 확인
        if attempt >= self.max_retries:
            return False
        
        # 서버 에러인 경우만 재시도
        return status_code in retryable_codes
    
    def _format_date(self, date: Any) -> str:
        """날짜 포맷팅"""
        if isinstance(date, datetime):
            return date.strftime("%Y%m%d")
        elif isinstance(date, str):
            # "2024-01-10" 형식을 "20240110" 형식으로 변환
            return date.replace("-", "")
        else:
            return str(date)
    
    def _parse_investor_trading_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """투자자 거래 응답 파싱"""
        rt_cd = response.get("rt_cd", "1")
        msg_cd = response.get("msg_cd", "")
        msg1 = response.get("msg1", "")
        
        parsed_response = {
            "success": rt_cd == "0",
            "message": msg1,
            "code": msg_cd,
            "data": []
        }
        
        if rt_cd == "0" and "output" in response:
            output_data = response["output"]
            
            for item in output_data:
                parsed_item = {
                    "stock_code": item.get("stck_code", ""),
                    "stock_name": item.get("stck_name", ""),
                    "business_date": item.get("stck_bsop_date", ""),
                    "foreign_net_buy_qty": int(item.get("frgn_ntby_qty", "0") or "0"),
                    "foreign_net_buy_amount": int(item.get("frgn_ntby_tr_pbmn", "0") or "0"),
                    "foreign_ownership_ratio": float(item.get("hts_frgn_ehrt", "0") or "0"),
                    "institution_net_buy_qty": int(item.get("inst_ntby_qty", "0") or "0"),
                    "institution_net_buy_amount": int(item.get("inst_ntby_tr_pbmn", "0") or "0"),
                    "individual_net_buy_qty": int(item.get("indv_ntby_qty", "0") or "0"),
                    "individual_net_buy_amount": int(item.get("indv_ntby_tr_pbmn", "0") or "0")
                }
                parsed_response["data"].append(parsed_item)
        
        return parsed_response