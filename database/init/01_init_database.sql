-- TRAE AI Production Database Initialization
-- PostgreSQL 15 - ARM64 Optimized for MacBook Air M1
-- This script creates the complete database schema for all revenue streams

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create custom types
CREATE TYPE user_role AS ENUM ('admin', 'user', 'premium', 'enterprise');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'expired', 'trial');
CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded');
CREATE TYPE content_type AS ENUM ('article', 'video', 'audio', 'image', 'pdf', 'social_post');
CREATE TYPE agent_status AS ENUM ('idle', 'working', 'error', 'maintenance');
CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'cancelled');
CREATE TYPE revenue_stream AS ENUM ('content_generation', 'ai_services', 'subscriptions', 'api_usage', 'consulting', 'marketplace');

-- Users table - Core authentication and user management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role user_role DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    avatar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- User sessions for JWT management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true
);

-- Subscriptions table - Revenue stream management
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_name VARCHAR(100) NOT NULL,
    status subscription_status DEFAULT 'trial',
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    monthly_price DECIMAL(10,2),
    yearly_price DECIMAL(10,2),
    features JSONB DEFAULT '{}',
    usage_limits JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Payments table - Financial transaction tracking
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
    stripe_payment_intent_id VARCHAR(255) UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status payment_status DEFAULT 'pending',
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- AI Agents table - Core AI system management
CREATE TABLE ai_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'content', 'marketing', 'research', 'seo', 'video'
    description TEXT,
    status agent_status DEFAULT 'idle',
    configuration JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE
);

-- Tasks table - AI agent task management
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status task_status DEFAULT 'pending',
    priority INTEGER DEFAULT 5, -- 1-10 scale
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Content table - Generated content management
CREATE TABLE content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    content_type content_type NOT NULL,
    content_text TEXT,
    content_url TEXT,
    file_path TEXT,
    file_size BIGINT,
    mime_type VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    seo_data JSONB DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Revenue tracking table - Comprehensive revenue analytics
CREATE TABLE revenue_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    revenue_stream revenue_stream NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    transaction_id VARCHAR(255),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE
);

-- API usage tracking - For API monetization
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    requests_count INTEGER DEFAULT 1,
    tokens_used INTEGER DEFAULT 0,
    cost DECIMAL(10,4) DEFAULT 0,
    response_time_ms INTEGER,
    status_code INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    date_bucket DATE GENERATED ALWAYS AS (DATE(created_at)) STORED
);

-- SEO reports table - SEO service revenue stream
CREATE TABLE seo_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    report_data JSONB NOT NULL,
    score INTEGER,
    recommendations JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Marketing campaigns - Marketing automation revenue
CREATE TABLE marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'email', 'social', 'video', 'content'
    status VARCHAR(50) DEFAULT 'draft',
    target_audience JSONB DEFAULT '{}',
    content_data JSONB DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    budget DECIMAL(10,2),
    spent DECIMAL(10,2) DEFAULT 0,
    roi DECIMAL(5,2),
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Research data - Research services revenue
CREATE TABLE research_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    research_type VARCHAR(50) NOT NULL,
    sources JSONB DEFAULT '{}',
    findings JSONB DEFAULT '{}',
    confidence_score DECIMAL(3,2),
    cost DECIMAL(10,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System logs - Monitoring and debugging
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(20) NOT NULL, -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    message TEXT NOT NULL,
    component VARCHAR(100),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance optimization (M1 optimized)
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_users_role ON users(role);
CREATE INDEX CONCURRENTLY idx_users_created_at ON users(created_at);

CREATE INDEX CONCURRENTLY idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX CONCURRENTLY idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX CONCURRENTLY idx_user_sessions_token_hash ON user_sessions(token_hash);

CREATE INDEX CONCURRENTLY idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX CONCURRENTLY idx_subscriptions_status ON subscriptions(status);
CREATE INDEX CONCURRENTLY idx_subscriptions_stripe_id ON subscriptions(stripe_subscription_id);

CREATE INDEX CONCURRENTLY idx_payments_user_id ON payments(user_id);
CREATE INDEX CONCURRENTLY idx_payments_status ON payments(status);
CREATE INDEX CONCURRENTLY idx_payments_created_at ON payments(created_at);

CREATE INDEX CONCURRENTLY idx_ai_agents_type ON ai_agents(type);
CREATE INDEX CONCURRENTLY idx_ai_agents_status ON ai_agents(status);

CREATE INDEX CONCURRENTLY idx_tasks_user_id ON tasks(user_id);
CREATE INDEX CONCURRENTLY idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX CONCURRENTLY idx_tasks_status ON tasks(status);
CREATE INDEX CONCURRENTLY idx_tasks_created_at ON tasks(created_at);

CREATE INDEX CONCURRENTLY idx_content_user_id ON content(user_id);
CREATE INDEX CONCURRENTLY idx_content_type ON content(content_type);
CREATE INDEX CONCURRENTLY idx_content_published ON content(is_published);
CREATE INDEX CONCURRENTLY idx_content_created_at ON content(created_at);

CREATE INDEX CONCURRENTLY idx_revenue_user_id ON revenue_tracking(user_id);
CREATE INDEX CONCURRENTLY idx_revenue_stream ON revenue_tracking(revenue_stream);
CREATE INDEX CONCURRENTLY idx_revenue_recorded_at ON revenue_tracking(recorded_at);

CREATE INDEX CONCURRENTLY idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX CONCURRENTLY idx_api_usage_date_bucket ON api_usage(date_bucket);
CREATE INDEX CONCURRENTLY idx_api_usage_endpoint ON api_usage(endpoint);

CREATE INDEX CONCURRENTLY idx_seo_reports_user_id ON seo_reports(user_id);
CREATE INDEX CONCURRENTLY idx_seo_reports_domain ON seo_reports(domain);

CREATE INDEX CONCURRENTLY idx_marketing_campaigns_user_id ON marketing_campaigns(user_id);
CREATE INDEX CONCURRENTLY idx_marketing_campaigns_status ON marketing_campaigns(status);

CREATE INDEX CONCURRENTLY idx_research_data_user_id ON research_data(user_id);
CREATE INDEX CONCURRENTLY idx_research_data_created_at ON research_data(created_at);

CREATE INDEX CONCURRENTLY idx_system_logs_level ON system_logs(level);
CREATE INDEX CONCURRENTLY idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX CONCURRENTLY idx_system_logs_component ON system_logs(component);

-- Full-text search indexes
CREATE INDEX CONCURRENTLY idx_content_text_search ON content USING gin(to_tsvector('english', content_text));
CREATE INDEX CONCURRENTLY idx_tasks_description_search ON tasks USING gin(to_tsvector('english', description));

-- JSONB indexes for metadata queries
CREATE INDEX CONCURRENTLY idx_users_metadata ON users USING gin(metadata);
CREATE INDEX CONCURRENTLY idx_subscriptions_features ON subscriptions USING gin(features);
CREATE INDEX CONCURRENTLY idx_ai_agents_config ON ai_agents USING gin(configuration);
CREATE INDEX CONCURRENTLY idx_content_metadata ON content USING gin(metadata);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_agents_updated_at BEFORE UPDATE ON ai_agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_updated_at BEFORE UPDATE ON content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_seo_reports_updated_at BEFORE UPDATE ON seo_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_marketing_campaigns_updated_at BEFORE UPDATE ON marketing_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for analytics and reporting
CREATE VIEW user_revenue_summary AS
SELECT
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    COALESCE(SUM(rt.amount), 0) as total_revenue,
    COUNT(DISTINCT rt.id) as transaction_count,
    MAX(rt.recorded_at) as last_transaction,
    s.plan_name,
    s.status as subscription_status
FROM users u
LEFT JOIN revenue_tracking rt ON u.id = rt.user_id
LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'active'
GROUP BY u.id, u.email, u.first_name, u.last_name, s.plan_name, s.status;

CREATE VIEW daily_revenue_summary AS
SELECT
    DATE(recorded_at) as revenue_date,
    revenue_stream,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as average_amount
FROM revenue_tracking
GROUP BY DATE(recorded_at), revenue_stream
ORDER BY revenue_date DESC, revenue_stream;

CREATE VIEW agent_performance_summary AS
SELECT
    a.id,
    a.name,
    a.type,
    a.status,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'failed' THEN 1 END) as failed_tasks,
    AVG(EXTRACT(EPOCH FROM (t.completed_at - t.started_at))/60) as avg_completion_time_minutes,
    MAX(t.completed_at) as last_task_completed
FROM ai_agents a
LEFT JOIN tasks t ON a.id = t.agent_id
GROUP BY a.id, a.name, a.type, a.status;

-- Insert default AI agents
INSERT INTO ai_agents (name, type, description, configuration, capabilities) VALUES
('Content Creator', 'content', 'AI agent specialized in creating high-quality written content',
 '{"model": "gpt-4", "max_tokens": 4000, "temperature": 0.7}',
 '{"content_types": ["articles", "blog_posts", "social_media"], "languages": ["en", "es", "fr"]}'),

('Marketing Specialist', 'marketing', 'AI agent for marketing campaign creation and optimization',
 '{"model": "gpt-4", "max_tokens": 3000, "temperature": 0.8}',
 '{"campaign_types": ["email", "social", "video"], "platforms": ["facebook", "instagram", "linkedin"]}'),

('Research Analyst', 'research', 'AI agent for comprehensive research and data analysis',
 '{"model": "gpt-4", "max_tokens": 6000, "temperature": 0.3}',
 '{"research_types": ["market", "competitor", "trend"], "data_sources": ["web", "academic", "news"]}'),

('SEO Optimizer', 'seo', 'AI agent for SEO analysis and optimization',
 '{"model": "gpt-4", "max_tokens": 2000, "temperature": 0.5}',
 '{"seo_types": ["on_page", "technical", "content"], "tools": ["keyword_analysis", "competitor_analysis"]}'),

('Video Producer', 'video', 'AI agent for video content creation and editing',
 '{"model": "gpt-4", "max_tokens": 2000, "temperature": 0.6}',
 '{"video_types": ["promotional", "educational", "social"], "formats": ["mp4", "webm", "mov"]}');

-- Create admin user (password should be changed immediately)
INSERT INTO users (email, password_hash, first_name, last_name, role, email_verified) VALUES
('admin@traeai.com', crypt('admin123', gen_salt('bf')), 'Admin', 'User', 'admin', true);

-- Create sample subscription plans data
INSERT INTO subscriptions (user_id, plan_name, status, monthly_price, yearly_price, features, usage_limits)
SELECT
    u.id,
    'Free Trial',
    'trial',
    0.00,
    0.00,
    '{"content_generation": true, "basic_seo": true, "api_access": false}',
    '{"monthly_content": 10, "api_calls": 100, "storage_gb": 1}'
FROM users u WHERE u.email = 'admin@traeai.com';

-- Performance optimization settings for M1
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Create database-level comments for documentation
COMMENT ON DATABASE traeai_prod IS 'TRAE AI Production Database - ARM64 Optimized for MacBook Air M1';
COMMENT ON TABLE users IS 'Core user authentication and profile management';
COMMENT ON TABLE subscriptions IS 'Subscription and billing management for revenue tracking';
COMMENT ON TABLE ai_agents IS 'AI agent definitions and configurations';
COMMENT ON TABLE tasks IS 'Task queue and execution tracking for AI agents';
COMMENT ON TABLE content IS 'Generated content storage and management';
COMMENT ON TABLE revenue_tracking IS 'Comprehensive revenue analytics across all streams';
COMMENT ON TABLE api_usage IS 'API usage tracking for monetization and rate limiting';

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO traeai;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO traeai;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO traeai;

-- Final optimization
ANALYZE;

-- Success message
SELECT 'TRAE AI Production Database initialized successfully for M1 MacBook Air' as status;
