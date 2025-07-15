"""
TDD 테스트: API 클라이언트 간단한 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.api.korea_investment import KoreaInvestmentAPI
from src.exceptions import APIException, AuthenticationException


class TestKoreaInvestmentAPISimple:
    """한국투자증권 API 클라이언트 단순 테스트"""
    
    @pytest.fixture
    def api_client(self):
        """테스트용 API 클라이언트"""
        return KoreaInvestmentAPI(
            app_key="test_app_key",
            app_secret="test_app_secret"
        )
    
    def test_api_client_initialization(self, api_client):
        """API 클라이언트 초기화 테스트"""
        assert api_client.app_key == "test_app_key"
        assert api_client.app_secret == "test_app_secret"
        assert api_client.base_url == "https://openapi.koreainvestment.com:9443"
        assert api_client.access_token is None
        assert api_client.session is None
    
    def test_validate_stock_code_valid(self, api_client):
        """유효한 종목코드 검증 테스트"""
        valid_codes = ["005930", "000660", "035420", "207940"]
        
        for code in valid_codes:
            assert api_client._validate_stock_code(code) == True
    
    def test_validate_stock_code_invalid(self, api_client):
        """잘못된 종목코드 검증 테스트"""
        invalid_codes = ["05930", "0059300", "AAPL", "invalid", "", None]
        
        for code in invalid_codes:
            assert api_client._validate_stock_code(code) == False
    
    def test_validate_market_code_valid(self, api_client):
        """유효한 시장코드 검증 테스트"""
        valid_markets = ["ALL", "KOSPI", "KOSDAQ", "J", "Q"]
        
        for market in valid_markets:
            assert api_client._validate_market_code(market) == True
    
    def test_validate_market_code_invalid(self, api_client):
        """잘못된 시장코드 검증 테스트"""
        invalid_markets = ["NYSE", "NASDAQ", "invalid", "", None]
        
        for market in invalid_markets:
            assert api_client._validate_market_code(market) == False
    
    def test_convert_market_code(self, api_client):
        """시장코드 변환 테스트"""
        assert api_client._convert_market_code("ALL") == "ALL"
        assert api_client._convert_market_code("KOSPI") == "J"
        assert api_client._convert_market_code("KOSDAQ") == "Q"
        assert api_client._convert_market_code("J") == "J"
        assert api_client._convert_market_code("Q") == "Q"
        assert api_client._convert_market_code("UNKNOWN") == "ALL"
    
    def test_get_tr_id_for_endpoint(self, api_client):
        """엔드포인트별 TR ID 반환 테스트"""
        assert api_client._get_tr_id("investor_trading", stock_code="005930") == "FHKST130200000"
        assert api_client._get_tr_id("investor_trading", stock_code=None) == "FHKST130100000"
        assert api_client._get_tr_id("program_trading") == "FHKST130300000"
        assert api_client._get_tr_id("unknown_endpoint") == "FHKST000000000"
    
    def test_should_retry_logic(self, api_client):
        """재시도 로직 테스트"""
        # 재시도 해야 하는 경우
        assert api_client._should_retry(500, 1) == True  # 서버 에러, 첫 번째 재시도
        assert api_client._should_retry(502, 2) == True  # 게이트웨이 에러, 두 번째 재시도
        assert api_client._should_retry(503, 3) == False  # 서비스 불가, 재시도 한도 초과
        
        # 재시도 하지 않는 경우
        assert api_client._should_retry(400, 1) == False  # 클라이언트 에러
        assert api_client._should_retry(401, 1) == False  # 인증 에러
        assert api_client._should_retry(404, 1) == False  # 없는 리소스
    
    def test_format_date_parameter(self, api_client):
        """날짜 파라미터 포맷팅 테스트"""
        from datetime import datetime
        
        test_date = datetime(2024, 1, 10)
        formatted = api_client._format_date(test_date)
        assert formatted == "20240110"
        
        # 문자열 날짜 처리
        formatted_str = api_client._format_date("2024-01-10")
        assert formatted_str == "20240110"
    
    def test_parse_response_data(self, api_client):
        """응답 데이터 파싱 테스트"""
        raw_response = {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다.",
            "output": [
                {
                    "stck_code": "005930",
                    "frgn_ntby_qty": "1000000",
                    "frgn_ntby_tr_pbmn": "78500000000"
                }
            ]
        }
        
        parsed = api_client._parse_investor_trading_response(raw_response)
        
        assert parsed["success"] == True
        assert parsed["message"] == "정상처리 되었습니다."
        assert len(parsed["data"]) == 1
        assert parsed["data"][0]["stock_code"] == "005930"
        assert parsed["data"][0]["foreign_net_buy_qty"] == 1000000
        assert parsed["data"][0]["foreign_net_buy_amount"] == 78500000000
    
    def test_parse_response_data_error(self, api_client):
        """에러 응답 데이터 파싱 테스트"""
        raw_response = {
            "rt_cd": "1",
            "msg_cd": "EGW00123",
            "msg1": "잘못된 요청입니다.",
            "output": []
        }
        
        parsed = api_client._parse_investor_trading_response(raw_response)
        
        assert parsed["success"] == False
        assert parsed["message"] == "잘못된 요청입니다."
        assert parsed["code"] == "EGW00123"
        assert len(parsed["data"]) == 0
    
    def test_parse_response_data_empty_fields(self, api_client):
        """빈 필드가 있는 응답 데이터 파싱 테스트"""
        raw_response = {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다.",
            "output": [
                {
                    "stck_code": "005930",
                    "frgn_ntby_qty": "",
                    "frgn_ntby_tr_pbmn": None
                }
            ]
        }
        
        parsed = api_client._parse_investor_trading_response(raw_response)
        
        assert parsed["success"] == True
        assert len(parsed["data"]) == 1
        assert parsed["data"][0]["stock_code"] == "005930"
        assert parsed["data"][0]["foreign_net_buy_qty"] == 0
        assert parsed["data"][0]["foreign_net_buy_amount"] == 0
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_validation(self, api_client):
        """투자자 거래 조회 파라미터 검증 테스트"""
        api_client.access_token = "test_token"
        
        # 잘못된 종목코드
        with pytest.raises(ValueError, match="Invalid stock code"):
            await api_client.get_investor_trading(stock_code="INVALID")
        
        # 잘못된 시장코드
        with pytest.raises(ValueError, match="Invalid market code"):
            await api_client.get_investor_trading(market="INVALID")
    
    @pytest.mark.asyncio
    async def test_get_program_trading_validation(self, api_client):
        """프로그램 매매 조회 파라미터 검증 테스트"""
        api_client.access_token = "test_token"
        
        # 잘못된 시장코드
        with pytest.raises(ValueError, match="Invalid market code"):
            await api_client.get_program_trading(market="INVALID")
    
    def test_max_retries_setting(self, api_client):
        """최대 재시도 횟수 설정 테스트"""
        assert api_client.max_retries == 3
        assert api_client.retry_delay == 1.0
    
    def test_base_url_setting(self, api_client):
        """기본 URL 설정 테스트"""
        assert api_client.base_url == "https://openapi.koreainvestment.com:9443"
        assert api_client.base_url.startswith("https://")
        assert "openapi.koreainvestment.com" in api_client.base_url