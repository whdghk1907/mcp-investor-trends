"""
TDD 테스트: API 클라이언트 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from datetime import datetime
from src.api.korea_investment import KoreaInvestmentAPI
from src.exceptions import APIException, AuthenticationException, RateLimitException


class TestKoreaInvestmentAPI:
    """한국투자증권 API 클라이언트 테스트"""
    
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
    
    @pytest.mark.asyncio
    async def test_context_manager_entry(self, api_client):
        """컨텍스트 매니저 진입 테스트"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            with patch.object(api_client, '_get_access_token') as mock_get_token:
                mock_get_token.return_value = None
                
                result = await api_client.__aenter__()
                
                assert result == api_client
                mock_session_class.assert_called_once()
                mock_get_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_exit(self, api_client):
        """컨텍스트 매니저 종료 테스트"""
        mock_session = AsyncMock()
        api_client.session = mock_session
        
        await api_client.__aexit__(None, None, None)
        
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_access_token_success(self, api_client):
        """액세스 토큰 발급 성공 테스트"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        api_client.session = mock_session
        
        await api_client._get_access_token()
        
        assert api_client.access_token == "test_access_token"
        mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, api_client):
        """액세스 토큰 발급 실패 테스트"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "error": "invalid_client",
            "error_description": "Invalid client credentials"
        }
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        api_client.session = mock_session
        
        with pytest.raises(AuthenticationException, match="Failed to get access token"):
            await api_client._get_access_token()
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_market_data(self, api_client):
        """시장 전체 투자자 거래 데이터 조회 테스트"""
        api_client.access_token = "test_token"
        
        mock_response_data = {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다.",
            "output": [
                {
                    "stck_bsop_date": "20240110",
                    "stck_code": "",
                    "data_rank": "1",
                    "hts_frgn_ehrt": "55.2",
                    "frgn_ntby_qty": "1000000",
                    "frgn_ntby_tr_pbmn": "78500000000"
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        api_client.session = mock_session
        
        result = await api_client.get_investor_trading(market="KOSPI")
        
        assert result == mock_response_data
        mock_session.get.assert_called_once()
        
        # 헤더 검증
        call_args = mock_session.get.call_args
        headers = call_args[1]['headers']
        assert headers['authorization'] == "Bearer test_token"
        assert headers['appkey'] == "test_app_key"
        assert headers['appsecret'] == "test_app_secret"
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_stock_data(self, api_client):
        """특정 종목 투자자 거래 데이터 조회 테스트"""
        api_client.access_token = "test_token"
        
        mock_response_data = {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "output": [
                {
                    "stck_bsop_date": "20240110",
                    "stck_code": "005930",
                    "stck_name": "삼성전자",
                    "frgn_ntby_qty": "500000",
                    "frgn_ntby_tr_pbmn": "39250000000"
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        api_client.session = mock_session
        
        result = await api_client.get_investor_trading(stock_code="005930")
        
        assert result == mock_response_data
        
        # 파라미터 검증
        call_args = mock_session.get.call_args
        params = call_args[1]['params']
        assert params['fid_input_iscd'] == "005930"
        assert params['fid_cond_mrkt_div_code'] == "J"
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_api_error(self, api_client):
        """API 에러 응답 테스트"""
        api_client.access_token = "test_token"
        
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json.return_value = {
            "rt_cd": "1",
            "msg_cd": "EGW00123",
            "msg1": "잘못된 요청입니다."
        }
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        api_client.session = mock_session
        
        with pytest.raises(APIException, match="API request failed"):
            await api_client.get_investor_trading()
    
    @pytest.mark.asyncio
    async def test_get_investor_trading_rate_limit(self, api_client):
        """API 속도 제한 테스트"""
        api_client.access_token = "test_token"
        
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.json.return_value = {
            "rt_cd": "1",
            "msg_cd": "EGW00124",
            "msg1": "API 호출 한도를 초과했습니다."
        }
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        api_client.session = mock_session
        
        with pytest.raises(RateLimitException, match="Rate limit exceeded"):
            await api_client.get_investor_trading()
    
    @pytest.mark.asyncio
    async def test_get_program_trading_success(self, api_client):
        """프로그램 매매 데이터 조회 성공 테스트"""
        api_client.access_token = "test_token"
        
        mock_response_data = {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "output": [
                {
                    "stck_bsop_date": "20240110",
                    "prg_buy_qty": "1000000",
                    "prg_seln_qty": "800000",
                    "prg_ntby_qty": "200000"
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        api_client.session = mock_session
        
        result = await api_client.get_program_trading(market="KOSPI")
        
        assert result == mock_response_data
        mock_session.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_request_retry_on_temporary_failure(self, api_client):
        """일시적 실패 시 재시도 테스트"""
        api_client.access_token = "test_token"
        
        # 첫 번째 호출은 실패, 두 번째 호출은 성공
        mock_response_fail = AsyncMock()
        mock_response_fail.status = 500
        mock_response_fail.json.return_value = {"error": "Internal server error"}
        
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.json.return_value = {"rt_cd": "0", "output": []}
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.side_effect = [
            mock_response_fail,
            mock_response_success
        ]
        api_client.session = mock_session
        
        with patch.object(api_client, '_should_retry', return_value=True):
            result = await api_client.get_investor_trading()
            
            assert result == {"rt_cd": "0", "output": []}
            assert mock_session.get.call_count == 2
    
    @pytest.mark.asyncio
    async def test_request_headers_validation(self, api_client):
        """요청 헤더 검증 테스트"""
        api_client.access_token = "test_token"
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"rt_cd": "0", "output": []}
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        api_client.session = mock_session
        
        await api_client.get_investor_trading()
        
        call_args = mock_session.get.call_args
        headers = call_args[1]['headers']
        
        # 필수 헤더 검증
        assert 'authorization' in headers
        assert 'appkey' in headers
        assert 'appsecret' in headers
        assert 'tr_id' in headers
        assert 'content-type' in headers
        
        # 헤더 값 검증
        assert headers['authorization'] == "Bearer test_token"
        assert headers['appkey'] == "test_app_key"
        assert headers['appsecret'] == "test_app_secret"
        assert headers['content-type'] == "application/json"
    
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
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, api_client):
        """연결 에러 처리 테스트"""
        api_client.access_token = "test_token"
        
        mock_session = AsyncMock()
        mock_session.get.side_effect = aiohttp.ClientConnectionError("Connection failed")
        api_client.session = mock_session
        
        with pytest.raises(APIException, match="Connection failed"):
            await api_client.get_investor_trading()
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, api_client):
        """타임아웃 에러 처리 테스트"""
        api_client.access_token = "test_token"
        
        mock_session = AsyncMock()
        mock_session.get.side_effect = aiohttp.ClientTimeout("Request timeout")
        api_client.session = mock_session
        
        with pytest.raises(APIException, match="Request timeout"):
            await api_client.get_investor_trading()
    
    def test_format_date_parameter(self, api_client):
        """날짜 파라미터 포맷팅 테스트"""
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