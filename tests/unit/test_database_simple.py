"""
TDD 테스트: 데이터베이스 단순 테스트
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.utils.database import DatabaseManager


class TestDatabaseManagerSimple:
    """데이터베이스 매니저 단순 테스트"""
    
    @pytest.fixture
    def db_manager(self):
        """테스트용 데이터베이스 매니저"""
        return DatabaseManager(
            database_url="postgresql://test:test@localhost/test_db",
            pool_size=5
        )
    
    def test_database_manager_initialization(self, db_manager):
        """데이터베이스 매니저 초기화 테스트"""
        assert db_manager.database_url == "postgresql://test:test@localhost/test_db"
        assert db_manager.pool_size == 5
        assert db_manager.pool is None
        assert db_manager.logger is not None
    
    def test_validate_insert_data_valid(self, db_manager):
        """유효한 삽입 데이터 검증 테스트"""
        valid_data = {
            "timestamp": datetime.now(),
            "stock_code": "005930",
            "market": "KOSPI",
            "foreign_buy": 1000000000,
            "foreign_sell": 800000000,
            "foreign_net": 200000000
        }
        
        assert db_manager._validate_insert_data(valid_data) == True
    
    def test_validate_insert_data_missing_required_fields(self, db_manager):
        """필수 필드가 누락된 데이터 검증 테스트"""
        invalid_data = {
            "stock_code": "005930",
            "foreign_buy": 1000000000
        }
        
        assert db_manager._validate_insert_data(invalid_data) == False
    
    def test_validate_insert_data_invalid_timestamp(self, db_manager):
        """잘못된 타임스탬프 데이터 검증 테스트"""
        invalid_data = {
            "timestamp": "invalid_timestamp",
            "market": "KOSPI"
        }
        
        assert db_manager._validate_insert_data(invalid_data) == False
    
    def test_validate_insert_data_invalid_market(self, db_manager):
        """잘못된 시장 코드 데이터 검증 테스트"""
        invalid_data = {
            "timestamp": datetime.now(),
            "market": ""  # 빈 문자열
        }
        
        assert db_manager._validate_insert_data(invalid_data) == False
    
    def test_validate_insert_data_invalid_stock_code(self, db_manager):
        """잘못된 종목 코드 데이터 검증 테스트"""
        invalid_data = {
            "timestamp": datetime.now(),
            "market": "KOSPI",
            "stock_code": "05930"  # 5자리 (6자리여야 함)
        }
        
        assert db_manager._validate_insert_data(invalid_data) == False
    
    def test_validate_insert_data_none_stock_code(self, db_manager):
        """종목 코드가 None인 경우 검증 테스트"""
        valid_data = {
            "timestamp": datetime.now(),
            "market": "KOSPI",
            "stock_code": None  # None은 허용됨
        }
        
        assert db_manager._validate_insert_data(valid_data) == True
    
    def test_extract_insert_values(self, db_manager):
        """삽입 데이터에서 값 추출 테스트"""
        data = {
            "timestamp": datetime.now(),
            "stock_code": "005930",
            "market": "KOSPI",
            "foreign_buy": 1000000000,
            "foreign_sell": 800000000,
            "foreign_net": 200000000,
            "institution_buy": 500000000,
            "institution_sell": 600000000,
            "institution_net": -100000000,
            "individual_buy": 300000000,
            "individual_sell": 400000000,
            "individual_net": -100000000,
            "program_buy": 100000000,
            "program_sell": 80000000,
            "program_net": 20000000
        }
        
        values = db_manager._extract_insert_values(data)
        
        assert len(values) == 15  # 15개 필드
        assert values[0] == data["timestamp"]
        assert values[1] == data["stock_code"]
        assert values[2] == data["market"]
        assert values[3] == data["foreign_buy"]
        assert values[4] == data["foreign_sell"]
        assert values[5] == data["foreign_net"]
        assert values[6] == data["institution_buy"]
        assert values[7] == data["institution_sell"]
        assert values[8] == data["institution_net"]
        assert values[9] == data["individual_buy"]
        assert values[10] == data["individual_sell"]
        assert values[11] == data["individual_net"]
        assert values[12] == data["program_buy"]
        assert values[13] == data["program_sell"]
        assert values[14] == data["program_net"]
    
    def test_extract_insert_values_missing_fields(self, db_manager):
        """필드가 누락된 경우 기본값 설정 테스트"""
        data = {
            "timestamp": datetime.now(),
            "stock_code": "005930",
            "market": "KOSPI"
            # 다른 필드들은 누락
        }
        
        values = db_manager._extract_insert_values(data)
        
        assert len(values) == 15
        assert values[0] == data["timestamp"]
        assert values[1] == data["stock_code"]
        assert values[2] == data["market"]
        # 누락된 필드들은 기본값 0
        assert values[3] == 0  # foreign_buy
        assert values[4] == 0  # foreign_sell
        assert values[5] == 0  # foreign_net
        assert values[14] == 0  # program_net
    
    def test_build_query_with_filters(self, db_manager):
        """필터가 있는 쿼리 빌드 테스트"""
        base_query = "SELECT * FROM investor_trading"
        filters = ["stock_code = $1", "market = $2", "timestamp >= $3"]
        
        query = db_manager._build_query_with_filters(base_query, filters)
        
        expected = "SELECT * FROM investor_trading WHERE stock_code = $1 AND market = $2 AND timestamp >= $3"
        assert query == expected
    
    def test_build_query_without_filters(self, db_manager):
        """필터가 없는 쿼리 빌드 테스트"""
        base_query = "SELECT * FROM investor_trading"
        filters = []
        
        query = db_manager._build_query_with_filters(base_query, filters)
        
        assert query == base_query
    
    def test_build_query_with_single_filter(self, db_manager):
        """단일 필터 쿼리 빌드 테스트"""
        base_query = "SELECT * FROM investor_trading"
        filters = ["stock_code = $1"]
        
        query = db_manager._build_query_with_filters(base_query, filters)
        
        expected = "SELECT * FROM investor_trading WHERE stock_code = $1"
        assert query == expected
    
    def test_parse_connection_string(self, db_manager):
        """연결 문자열 파싱 테스트"""
        connection_info = db_manager._parse_connection_string()
        
        assert connection_info["host"] == "localhost"
        assert connection_info["database"] == "test_db"
        assert connection_info["user"] == "test"
        assert connection_info["password"] == "test"
        assert connection_info["port"] == "5432"
    
    def test_parse_connection_string_with_port(self):
        """포트가 있는 연결 문자열 파싱 테스트"""
        db_manager = DatabaseManager("postgresql://user:pass@host:5433/mydb")
        connection_info = db_manager._parse_connection_string()
        
        assert connection_info["host"] == "host"
        assert connection_info["database"] == "mydb"
        assert connection_info["user"] == "user"
        assert connection_info["password"] == "pass"
        assert connection_info["port"] == "5433"
    
    def test_parse_connection_string_minimal(self):
        """최소한의 연결 문자열 파싱 테스트"""
        db_manager = DatabaseManager("postgresql://localhost/mydb")
        connection_info = db_manager._parse_connection_string()
        
        assert connection_info["host"] == "localhost"
        assert connection_info["database"] == "mydb"
        assert connection_info["user"] == ""
        assert connection_info["password"] == ""
        assert connection_info["port"] == "5432"
    
    def test_database_url_validation(self, db_manager):
        """데이터베이스 URL 유효성 검증"""
        assert db_manager.database_url.startswith("postgresql://")
        assert "localhost" in db_manager.database_url
        assert "test_db" in db_manager.database_url
    
    def test_pool_size_setting(self, db_manager):
        """풀 사이즈 설정 테스트"""
        assert db_manager.pool_size == 5
        
        # 다른 풀 사이즈로 초기화
        db_manager2 = DatabaseManager("postgresql://localhost/test", pool_size=10)
        assert db_manager2.pool_size == 10
    
    def test_logger_initialization(self, db_manager):
        """로거 초기화 테스트"""
        assert db_manager.logger is not None
        assert db_manager.logger.name == "src.utils.database"
    
    def test_pool_initial_state(self, db_manager):
        """풀 초기 상태 테스트"""
        assert db_manager.pool is None
        
        # initialize 호출 전까지는 None 상태여야 함
        assert db_manager.pool is None
    
    def test_extract_insert_values_data_types(self, db_manager):
        """삽입 값 데이터 타입 테스트"""
        now = datetime.now()
        data = {
            "timestamp": now,
            "stock_code": "005930",
            "market": "KOSPI",
            "foreign_buy": 1000000000,
            "foreign_sell": 800000000,
            "foreign_net": 200000000
        }
        
        values = db_manager._extract_insert_values(data)
        
        # 타입 확인
        assert isinstance(values[0], datetime)
        assert isinstance(values[1], str)
        assert isinstance(values[2], str)
        assert isinstance(values[3], int)
        assert isinstance(values[4], int)
        assert isinstance(values[5], int)
    
    def test_validate_insert_data_with_all_fields(self, db_manager):
        """모든 필드가 있는 데이터 검증 테스트"""
        complete_data = {
            "timestamp": datetime.now(),
            "stock_code": "005930",
            "market": "KOSPI",
            "foreign_buy": 1000000000,
            "foreign_sell": 800000000,
            "foreign_net": 200000000,
            "institution_buy": 500000000,
            "institution_sell": 600000000,
            "institution_net": -100000000,
            "individual_buy": 300000000,
            "individual_sell": 400000000,
            "individual_net": -100000000,
            "program_buy": 100000000,
            "program_sell": 80000000,
            "program_net": 20000000
        }
        
        assert db_manager._validate_insert_data(complete_data) == True