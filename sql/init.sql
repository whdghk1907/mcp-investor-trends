-- MCP Investor Trends Database Initialization Script

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create investor_trading table
CREATE TABLE IF NOT EXISTS investor_trading (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(6), -- NULL for market-wide data
    market VARCHAR(10) NOT NULL, -- KOSPI, KOSDAQ, ALL
    
    -- Foreign investor trading data
    foreign_buy BIGINT DEFAULT 0,
    foreign_sell BIGINT DEFAULT 0,
    foreign_net BIGINT DEFAULT 0,
    
    -- Institutional investor trading data
    institution_buy BIGINT DEFAULT 0,
    institution_sell BIGINT DEFAULT 0,
    institution_net BIGINT DEFAULT 0,
    
    -- Individual investor trading data
    individual_buy BIGINT DEFAULT 0,
    individual_sell BIGINT DEFAULT 0,
    individual_net BIGINT DEFAULT 0,
    
    -- Program trading data
    program_buy BIGINT DEFAULT 0,
    program_sell BIGINT DEFAULT 0,
    program_net BIGINT DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create unique constraint to prevent duplicate entries
CREATE UNIQUE INDEX IF NOT EXISTS idx_investor_trading_unique 
ON investor_trading (timestamp, COALESCE(stock_code, ''), market);

-- Create hypertable for time-series data
SELECT create_hypertable('investor_trading', 'timestamp', if_not_exists => TRUE);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_investor_trading_timestamp 
ON investor_trading (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_investor_trading_stock_code 
ON investor_trading (stock_code) WHERE stock_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_investor_trading_market 
ON investor_trading (market);

CREATE INDEX IF NOT EXISTS idx_investor_trading_foreign_net 
ON investor_trading (foreign_net DESC);

CREATE INDEX IF NOT EXISTS idx_investor_trading_institution_net 
ON investor_trading (institution_net DESC);

-- Create compression policy for old data (compress data older than 7 days)
SELECT add_compression_policy('investor_trading', INTERVAL '7 days', if_not_exists => TRUE);

-- Create retention policy (keep data for 5 years)
SELECT add_retention_policy('investor_trading', INTERVAL '5 years', if_not_exists => TRUE);

-- Create program_trading table
CREATE TABLE IF NOT EXISTS program_trading (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    market VARCHAR(10) NOT NULL,
    
    -- Program trading data
    program_buy BIGINT DEFAULT 0,
    program_sell BIGINT DEFAULT 0,
    program_net BIGINT DEFAULT 0,
    
    -- Arbitrage trading
    arbitrage_buy BIGINT DEFAULT 0,
    arbitrage_sell BIGINT DEFAULT 0,
    arbitrage_net BIGINT DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create unique constraint for program trading
CREATE UNIQUE INDEX IF NOT EXISTS idx_program_trading_unique 
ON program_trading (timestamp, market);

-- Create hypertable for program trading
SELECT create_hypertable('program_trading', 'timestamp', if_not_exists => TRUE);

-- Create indexes for program trading
CREATE INDEX IF NOT EXISTS idx_program_trading_timestamp 
ON program_trading (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_program_trading_market 
ON program_trading (market);

-- Create stock_info table for metadata
CREATE TABLE IF NOT EXISTS stock_info (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(6) UNIQUE NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL,
    sector VARCHAR(50),
    industry VARCHAR(100),
    market_cap BIGINT,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for stock_info
CREATE INDEX IF NOT EXISTS idx_stock_info_market 
ON stock_info (market);

CREATE INDEX IF NOT EXISTS idx_stock_info_sector 
ON stock_info (sector);

-- Create smart_money_signals table
CREATE TABLE IF NOT EXISTS smart_money_signals (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(6),
    market VARCHAR(10),
    
    signal_type VARCHAR(50) NOT NULL, -- BUY, SELL, NEUTRAL
    intensity NUMERIC(4,2) NOT NULL, -- 1.0 to 10.0
    confidence NUMERIC(4,2) NOT NULL, -- 0.0 to 1.0
    
    foreign_contribution BIGINT DEFAULT 0,
    institution_contribution BIGINT DEFAULT 0,
    total_flow BIGINT DEFAULT 0,
    
    detection_method VARCHAR(50) NOT NULL, -- LARGE_ORDERS, PATTERN_ANALYSIS, etc.
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create hypertable for smart money signals
SELECT create_hypertable('smart_money_signals', 'timestamp', if_not_exists => TRUE);

-- Create indexes for smart money signals
CREATE INDEX IF NOT EXISTS idx_smart_money_signals_timestamp 
ON smart_money_signals (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_smart_money_signals_stock_code 
ON smart_money_signals (stock_code) WHERE stock_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_smart_money_signals_signal_type 
ON smart_money_signals (signal_type);

CREATE INDEX IF NOT EXISTS idx_smart_money_signals_intensity 
ON smart_money_signals (intensity DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_investor_trading_updated_at 
    BEFORE UPDATE ON investor_trading 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_program_trading_updated_at 
    BEFORE UPDATE ON program_trading 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stock_info_updated_at 
    BEFORE UPDATE ON stock_info 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO stock_info (stock_code, stock_name, market, sector) VALUES
('005930', '삼성전자', 'KOSPI', 'Technology'),
('000660', 'SK하이닉스', 'KOSPI', 'Technology'),
('035420', 'NAVER', 'KOSPI', 'Technology'),
('207940', '삼성바이오로직스', 'KOSPI', 'Healthcare'),
('005380', '현대차', 'KOSPI', 'Automotive'),
('035720', '카카오', 'KOSPI', 'Technology'),
('051910', 'LG화학', 'KOSPI', 'Chemical'),
('006400', '삼성SDI', 'KOSPI', 'Technology'),
('028260', '삼성물산', 'KOSPI', 'Construction'),
('012330', '현대모비스', 'KOSPI', 'Automotive')
ON CONFLICT (stock_code) DO NOTHING;

-- Create continuous aggregates for better performance
CREATE MATERIALIZED VIEW IF NOT EXISTS investor_trading_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS time_bucket,
    stock_code,
    market,
    SUM(foreign_buy) AS foreign_buy_sum,
    SUM(foreign_sell) AS foreign_sell_sum,
    SUM(foreign_net) AS foreign_net_sum,
    SUM(institution_buy) AS institution_buy_sum,
    SUM(institution_sell) AS institution_sell_sum,
    SUM(institution_net) AS institution_net_sum,
    SUM(individual_buy) AS individual_buy_sum,
    SUM(individual_sell) AS individual_sell_sum,
    SUM(individual_net) AS individual_net_sum,
    COUNT(*) AS record_count
FROM investor_trading
GROUP BY time_bucket, stock_code, market;

-- Create refresh policy for the materialized view
SELECT add_continuous_aggregate_policy('investor_trading_hourly',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Create daily aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS investor_trading_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', timestamp) AS time_bucket,
    stock_code,
    market,
    SUM(foreign_buy) AS foreign_buy_sum,
    SUM(foreign_sell) AS foreign_sell_sum,
    SUM(foreign_net) AS foreign_net_sum,
    SUM(institution_buy) AS institution_buy_sum,
    SUM(institution_sell) AS institution_sell_sum,
    SUM(institution_net) AS institution_net_sum,
    SUM(individual_buy) AS individual_buy_sum,
    SUM(individual_sell) AS individual_sell_sum,
    SUM(individual_net) AS individual_net_sum,
    COUNT(*) AS record_count
FROM investor_trading
GROUP BY time_bucket, stock_code, market;

-- Create refresh policy for daily aggregates
SELECT add_continuous_aggregate_policy('investor_trading_daily',
    start_offset => INTERVAL '1 week',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Create view for easy market overview
CREATE OR REPLACE VIEW market_overview AS
SELECT 
    timestamp,
    market,
    SUM(foreign_net) AS total_foreign_net,
    SUM(institution_net) AS total_institution_net,
    SUM(individual_net) AS total_individual_net,
    SUM(foreign_net + institution_net) AS smart_money_net,
    COUNT(DISTINCT stock_code) AS active_stocks
FROM investor_trading
WHERE timestamp >= NOW() - INTERVAL '1 day'
GROUP BY timestamp, market
ORDER BY timestamp DESC;

-- Create view for top smart money flows
CREATE OR REPLACE VIEW top_smart_money_flows AS
SELECT 
    stock_code,
    si.stock_name,
    si.market,
    si.sector,
    SUM(foreign_net) AS foreign_net_sum,
    SUM(institution_net) AS institution_net_sum,
    SUM(foreign_net + institution_net) AS smart_money_net_sum,
    COUNT(*) AS record_count
FROM investor_trading it
LEFT JOIN stock_info si ON it.stock_code = si.stock_code
WHERE it.timestamp >= NOW() - INTERVAL '1 day'
    AND it.stock_code IS NOT NULL
GROUP BY it.stock_code, si.stock_name, si.market, si.sector
ORDER BY smart_money_net_sum DESC
LIMIT 50;

-- Create index on the view for better performance
CREATE INDEX IF NOT EXISTS idx_top_smart_money_flows_smart_money_net 
ON investor_trading (stock_code, (foreign_net + institution_net) DESC) 
WHERE stock_code IS NOT NULL;

-- Insert sample trading data for testing
INSERT INTO investor_trading (
    timestamp, stock_code, market, 
    foreign_buy, foreign_sell, foreign_net,
    institution_buy, institution_sell, institution_net,
    individual_buy, individual_sell, individual_net
) VALUES
(NOW() - INTERVAL '1 hour', '005930', 'KOSPI', 1000000000, 800000000, 200000000, 500000000, 600000000, -100000000, 300000000, 400000000, -100000000),
(NOW() - INTERVAL '2 hours', '000660', 'KOSPI', 800000000, 600000000, 200000000, 400000000, 500000000, -100000000, 200000000, 300000000, -100000000),
(NOW() - INTERVAL '3 hours', '035420', 'KOSPI', 600000000, 500000000, 100000000, 300000000, 400000000, -100000000, 150000000, 200000000, -50000000)
ON CONFLICT (timestamp, COALESCE(stock_code, ''), market) DO NOTHING;

-- Create function to generate test data
CREATE OR REPLACE FUNCTION generate_test_data(days_back INT DEFAULT 7)
RETURNS VOID AS $$
DECLARE
    stock_codes VARCHAR[] := ARRAY['005930', '000660', '035420', '207940', '005380'];
    markets VARCHAR[] := ARRAY['KOSPI', 'KOSDAQ'];
    i INT;
    j INT;
    test_timestamp TIMESTAMPTZ;
    stock_code VARCHAR;
    market VARCHAR;
BEGIN
    FOR i IN 1..days_back LOOP
        FOR j IN 1..24 LOOP -- 24 hours per day
            test_timestamp := NOW() - INTERVAL '1 day' * i - INTERVAL '1 hour' * j;
            
            FOREACH stock_code IN ARRAY stock_codes LOOP
                FOREACH market IN ARRAY markets LOOP
                    INSERT INTO investor_trading (
                        timestamp, stock_code, market,
                        foreign_buy, foreign_sell, foreign_net,
                        institution_buy, institution_sell, institution_net,
                        individual_buy, individual_sell, individual_net
                    ) VALUES (
                        test_timestamp, stock_code, market,
                        (random() * 1000000000)::BIGINT, (random() * 800000000)::BIGINT, (random() * 200000000 - 100000000)::BIGINT,
                        (random() * 500000000)::BIGINT, (random() * 600000000)::BIGINT, (random() * 100000000 - 50000000)::BIGINT,
                        (random() * 300000000)::BIGINT, (random() * 400000000)::BIGINT, (random() * 100000000 - 50000000)::BIGINT
                    ) ON CONFLICT DO NOTHING;
                END LOOP;
            END LOOP;
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Uncomment the line below to generate test data
-- SELECT generate_test_data(3);

COMMIT;