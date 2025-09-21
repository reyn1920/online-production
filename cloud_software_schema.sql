-- Cloud Software Database Schema
-- Simple schema for cloud_software.db

-- Create cloud_software table
CREATE TABLE IF NOT EXISTS cloud_software (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    software_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('voice_generation', 'video_editing', 'thumbnail_creation', 'script_writing', 'background_music', 'training', 'automation', 'bonus_tools')),
    provider TEXT,
    version TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'deprecated')),
    integration_type TEXT CHECK (integration_type IN ('api', 'rpa', 'manual', 'webhook', 'cli')),
    api_endpoint TEXT,
    authentication_method TEXT CHECK (authentication_method IN ('api_key', 'oauth2', 'username_password', 'token', 'none')),
    credentials_stored BOOLEAN DEFAULT FALSE,
    rate_limit_per_hour INTEGER,
    rate_limit_per_day INTEGER,
    current_usage_hour INTEGER DEFAULT 0,
    current_usage_day INTEGER DEFAULT 0,
    last_usage_reset TIMESTAMP,
    configuration JSON,
    capabilities JSON,
    dependencies JSON,
    installation_status TEXT DEFAULT 'not_installed' CHECK (installation_status IN ('not_installed', 'installing', 'installed', 'failed', 'updating')),
    installation_path TEXT,
    license_type TEXT CHECK (license_type IN ('free', 'paid', 'subscription', 'one_time', 'trial')),
    license_expires_at TIMESTAMP,
    subscription_status TEXT CHECK (subscription_status IN ('active', 'expired', 'cancelled', 'trial', 'none')),
    monthly_cost DECIMAL(10,2),
    annual_cost DECIMAL(10,2),
    usage_metrics JSON,
    performance_metrics JSON,
    last_health_check TIMESTAMP,
    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    documentation_url TEXT,
    support_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    notes TEXT,
    metadata JSON
);

-- Create software_usage_logs table
CREATE TABLE IF NOT EXISTS software_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    software_id INTEGER NOT NULL,
    usage_type TEXT NOT NULL,
    operation TEXT,
    input_data JSON,
    output_data JSON,
    execution_time_ms INTEGER,
    status TEXT CHECK (status IN ('success', 'failed', 'timeout', 'cancelled')),
    error_message TEXT,
    cost DECIMAL(10,4),
    user_id TEXT,
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (software_id) REFERENCES cloud_software (id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_cloud_software_name ON cloud_software(software_name);
CREATE INDEX IF NOT EXISTS idx_cloud_software_status ON cloud_software(status);
CREATE INDEX IF NOT EXISTS idx_cloud_software_category ON cloud_software(category);
CREATE INDEX IF NOT EXISTS idx_software_usage_logs_software_id ON software_usage_logs(software_id);
CREATE INDEX IF NOT EXISTS idx_software_usage_logs_timestamp ON software_usage_logs(timestamp);
