-- Minimal working schema for TRAE AI system
-- This creates only the essential tables needed for the system to function

-- Task Queue - Core system functionality
CREATE TABLE IF NOT EXISTS task_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    task_data JSON,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    assigned_worker TEXT,
    result JSON
);

-- API Registry - Essential for API orchestrator
CREATE TABLE IF NOT EXISTS api_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT UNIQUE NOT NULL,
    base_url TEXT NOT NULL,
    api_version TEXT,
    authentication_type TEXT CHECK (authentication_type IN ('api_key', 'bearer_token', 'oauth2', 'basic_auth', 'none')),
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_hour INTEGER DEFAULT 3600,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated', 'maintenance')),
    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Request Logs - For monitoring
CREATE TABLE IF NOT EXISTS api_request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms REAL,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_name) REFERENCES api_registry(api_name) ON DELETE CASCADE
);

-- System Configuration
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type TEXT DEFAULT 'string' CHECK (config_type IN ('string', 'integer', 'float', 'boolean', 'json')),
    description TEXT,
    category TEXT DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status, priority DESC);
CREATE INDEX IF NOT EXISTS idx_task_queue_created ON task_queue(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_registry_name ON api_registry(api_name);
CREATE INDEX IF NOT EXISTS idx_api_registry_status ON api_registry(status);
CREATE INDEX IF NOT EXISTS idx_api_logs_api_name ON api_request_logs(api_name);
CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_request_logs(timestamp);

-- Insert default API registry entries
INSERT OR IGNORE INTO api_registry (api_name, base_url, api_version, authentication_type, rate_limit_per_minute, rate_limit_per_hour, status) VALUES
('openai_api', 'https://api.openai.com', 'v1', 'bearer_token', 60, 3000, 'active'),
('youtube_api', 'https://www.googleapis.com/youtube/v3', 'v3', 'api_key', 100, 10000, 'active'),
('twitter_api', 'https://api.twitter.com', '2', 'bearer_token', 300, 15000, 'active');

-- Insert default system configuration
INSERT OR IGNORE INTO system_config (config_key, config_value, config_type, description, category) VALUES
('system_name', 'TRAE AI System', 'string', 'System name', 'general'),
('max_concurrent_tasks', '10', 'integer', 'Maximum concurrent tasks', 'tasks'),
('default_task_timeout', '300', 'integer', 'Default task timeout in seconds', 'tasks'),
('api_rate_limit_buffer', '0.8', 'float', 'Buffer percentage for API rate limits', 'api');

SELECT 'Minimal TRAE AI database schema created successfully!' as status;
