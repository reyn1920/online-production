-- TRAE.AI Database Initialization Script
-- This script creates all necessary tables for the complete TRAE.AI system

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE content_type AS ENUM ('text', 'image', 'video', 'audio', 'blog_post', 'social_post', 'email', 'ebook', 'script');
CREATE TYPE content_status AS ENUM ('draft', 'processing', 'ready', 'published', 'failed', 'archived');
CREATE TYPE campaign_type AS ENUM ('brand_awareness', 'lead_generation', 'sales', 'engagement', 'traffic', 'conversion');
CREATE TYPE campaign_status AS ENUM ('draft', 'active', 'paused', 'completed', 'cancelled');
CREATE TYPE revenue_stream_type AS ENUM ('affiliate', 'product_sales', 'subscription', 'advertising', 'sponsorship', 'course', 'membership', 'print_on_demand', 'consulting', 'licensing');
CREATE TYPE transaction_status AS ENUM ('pending', 'completed', 'failed', 'refunded', 'cancelled');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'expired', 'paused', 'trial');
CREATE TYPE alert_type AS ENUM ('revenue_drop', 'growth_decline', 'system_error', 'campaign_performance', 'content_performance');
CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE data_source_type AS ENUM ('api', 'database', 'file', 'webhook', 'manual');
CREATE TYPE visualization_type AS ENUM ('line_chart', 'bar_chart', 'pie_chart', 'scatter_plot', 'heatmap', 'table', 'metric_card');

-- =============================================================================
-- CONTENT AGENT TABLES
-- =============================================================================

-- Content items table
CREATE TABLE content_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content_type content_type NOT NULL,
    status content_status DEFAULT 'draft',
    content_text TEXT,
    content_data JSONB, -- Store structured content data
    metadata JSONB, -- Store additional metadata
    file_path VARCHAR(1000),
    file_size BIGINT,
    duration INTEGER, -- For video/audio content in seconds
    thumbnail_path VARCHAR(1000),
    tags TEXT[],
    target_audience VARCHAR(200),
    seo_keywords TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100),
    ai_model_used VARCHAR(100),
    generation_prompt TEXT,
    quality_score DECIMAL(3,2), -- 0.00 to 1.00
    engagement_score DECIMAL(3,2), -- 0.00 to 1.00
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0
);

-- Content templates table
CREATE TABLE content_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    content_type content_type NOT NULL,
    template_data JSONB NOT NULL, -- Store template structure
    variables JSONB, -- Store template variables
    category VARCHAR(100),
    tags TEXT[],
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Content generation jobs table
CREATE TABLE content_generation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_item_id UUID REFERENCES content_items(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- 'text', 'image', 'video', 'audio', 'tts'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    input_data JSONB NOT NULL,
    output_data JSONB,
    error_message TEXT,
    ai_model VARCHAR(100),
    processing_time INTEGER, -- in seconds
    cost DECIMAL(10,4), -- API cost
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Content publishing schedule table
CREATE TABLE content_schedule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_item_id UUID REFERENCES content_items(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL, -- 'youtube', 'twitter', 'facebook', 'instagram', etc.
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'published', 'failed', 'cancelled'
    platform_post_id VARCHAR(200), -- ID from the platform after publishing
    platform_url VARCHAR(500), -- URL of the published content
    publish_data JSONB, -- Platform-specific publishing data
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- MARKETING AGENT TABLES
-- =============================================================================

-- Marketing campaigns table
CREATE TABLE marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    campaign_type campaign_type NOT NULL,
    status campaign_status DEFAULT 'draft',
    channels TEXT[] NOT NULL, -- ['social_media', 'email', 'content', 'paid_ads']
    target_audience TEXT,
    budget DECIMAL(12,2),
    spent_budget DECIMAL(12,2) DEFAULT 0,
    start_date DATE,
    end_date DATE,
    duration_days INTEGER,
    objectives TEXT[],
    kpis JSONB, -- Key Performance Indicators
    settings JSONB, -- Campaign-specific settings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Campaign content association table
CREATE TABLE campaign_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES marketing_campaigns(id) ON DELETE CASCADE,
    content_item_id UUID REFERENCES content_items(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    scheduled_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending',
    performance_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Social media posts table
CREATE TABLE social_media_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES marketing_campaigns(id) ON DELETE SET NULL,
    content_item_id UUID REFERENCES content_items(id) ON DELETE SET NULL,
    platform VARCHAR(50) NOT NULL,
    post_text TEXT,
    media_urls TEXT[],
    hashtags TEXT[],
    mentions TEXT[],
    scheduled_time TIMESTAMP WITH TIME ZONE,
    published_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'draft',
    platform_post_id VARCHAR(200),
    platform_url VARCHAR(500),
    engagement_data JSONB, -- likes, shares, comments, etc.
    reach INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Email campaigns table
CREATE TABLE email_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    marketing_campaign_id UUID REFERENCES marketing_campaigns(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    content_html TEXT,
    content_text TEXT,
    sender_name VARCHAR(100),
    sender_email VARCHAR(200),
    recipient_list_id VARCHAR(100), -- External list ID (Mailchimp, SendGrid)
    scheduled_time TIMESTAMP WITH TIME ZONE,
    sent_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'draft',
    recipients_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    bounced_count INTEGER DEFAULT 0,
    unsubscribed_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Lead management table
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(200) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    company VARCHAR(200),
    job_title VARCHAR(100),
    source VARCHAR(100), -- 'website', 'social_media', 'email', 'referral'
    campaign_id UUID REFERENCES marketing_campaigns(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'new', -- 'new', 'contacted', 'qualified', 'converted', 'lost'
    score INTEGER DEFAULT 0, -- Lead scoring
    tags TEXT[],
    notes TEXT,
    custom_fields JSONB,
    last_activity TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- MONETIZATION BUNDLE TABLES
-- =============================================================================

-- Revenue streams table
CREATE TABLE revenue_streams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    stream_type revenue_stream_type NOT NULL,
    platform VARCHAR(100), -- 'gumroad', 'stripe', 'youtube', 'amazon', etc.
    platform_id VARCHAR(200), -- External platform identifier
    is_active BOOLEAN DEFAULT true,
    commission_rate DECIMAL(5,4), -- For affiliate streams
    base_price DECIMAL(12,2), -- For product/subscription streams
    currency VARCHAR(3) DEFAULT 'USD',
    settings JSONB, -- Stream-specific settings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    revenue_stream_id UUID REFERENCES revenue_streams(id) ON DELETE SET NULL,
    transaction_id VARCHAR(200) NOT NULL, -- External transaction ID
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    fee DECIMAL(12,2) DEFAULT 0, -- Platform fees
    net_amount DECIMAL(12,2) NOT NULL, -- Amount after fees
    status transaction_status DEFAULT 'pending',
    customer_email VARCHAR(200),
    customer_name VARCHAR(200),
    product_name VARCHAR(200),
    product_id VARCHAR(200),
    platform VARCHAR(100),
    platform_data JSONB, -- Platform-specific transaction data
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    revenue_stream_id UUID REFERENCES revenue_streams(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    product_type VARCHAR(50), -- 'ebook', 'course', 'software', 'merchandise'
    sku VARCHAR(100),
    platform_product_id VARCHAR(200), -- External platform product ID
    is_active BOOLEAN DEFAULT true,
    inventory_count INTEGER,
    digital_file_path VARCHAR(500),
    download_limit INTEGER,
    tags TEXT[],
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Affiliate links table
CREATE TABLE affiliate_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    revenue_stream_id UUID REFERENCES revenue_streams(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    original_url VARCHAR(1000) NOT NULL,
    affiliate_url VARCHAR(1000) NOT NULL,
    short_url VARCHAR(200), -- Shortened version
    platform VARCHAR(100), -- 'amazon', 'clickbank', 'commission_junction'
    commission_rate DECIMAL(5,4),
    click_count INTEGER DEFAULT 0,
    conversion_count INTEGER DEFAULT 0,
    total_earnings DECIMAL(12,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    revenue_stream_id UUID REFERENCES revenue_streams(id) ON DELETE CASCADE,
    customer_email VARCHAR(200) NOT NULL,
    customer_name VARCHAR(200),
    plan_name VARCHAR(200) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    billing_cycle VARCHAR(20), -- 'monthly', 'yearly', 'weekly'
    status subscription_status DEFAULT 'active',
    platform_subscription_id VARCHAR(200), -- External subscription ID
    platform VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE,
    next_billing_date DATE,
    trial_end_date DATE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ANALYTICS DASHBOARD TABLES
-- =============================================================================

-- Dashboards table
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    layout JSONB NOT NULL, -- Dashboard layout configuration
    is_public BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false,
    tags TEXT[],
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data sources table
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    source_type data_source_type NOT NULL,
    connection_config JSONB NOT NULL, -- Connection configuration
    refresh_interval INTEGER DEFAULT 3600, -- Refresh interval in seconds
    last_refresh TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Metric definitions table
CREATE TABLE metric_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    data_source_id UUID REFERENCES data_sources(id) ON DELETE CASCADE,
    query_config JSONB NOT NULL, -- Query/calculation configuration
    unit VARCHAR(50), -- 'currency', 'percentage', 'count', 'time'
    format_config JSONB, -- Formatting configuration
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Reports table
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    report_type VARCHAR(50), -- 'revenue', 'content', 'marketing', 'custom'
    config JSONB NOT NULL, -- Report configuration
    schedule JSONB, -- Scheduling configuration
    recipients TEXT[], -- Email recipients
    is_active BOOLEAN DEFAULT true,
    last_generated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    alert_type alert_type NOT NULL,
    severity alert_severity DEFAULT 'medium',
    condition_config JSONB NOT NULL, -- Alert condition configuration
    notification_config JSONB, -- Notification settings
    is_active BOOLEAN DEFAULT true,
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alert instances table (for tracking alert occurrences)
CREATE TABLE alert_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id UUID REFERENCES alerts(id) ON DELETE CASCADE,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message TEXT NOT NULL,
    data JSONB, -- Alert-specific data
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(100)
);

-- =============================================================================
-- SYSTEM TABLES
-- =============================================================================

-- System metrics table (for tracking overall system performance)
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(50),
    tags JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API usage tracking table
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service VARCHAR(100) NOT NULL, -- 'openai', 'elevenlabs', 'stability', etc.
    endpoint VARCHAR(200),
    request_count INTEGER DEFAULT 1,
    tokens_used INTEGER DEFAULT 0,
    cost DECIMAL(10,4) DEFAULT 0,
    date DATE NOT NULL,
    hour INTEGER, -- 0-23 for hourly tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User sessions table (for tracking user activity)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(200) NOT NULL UNIQUE,
    user_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Content items indexes
CREATE INDEX idx_content_items_type ON content_items(content_type);
CREATE INDEX idx_content_items_status ON content_items(status);
CREATE INDEX idx_content_items_created_at ON content_items(created_at);
CREATE INDEX idx_content_items_published_at ON content_items(published_at);
CREATE INDEX idx_content_items_tags ON content_items USING GIN(tags);

-- Marketing campaigns indexes
CREATE INDEX idx_campaigns_type ON marketing_campaigns(campaign_type);
CREATE INDEX idx_campaigns_status ON marketing_campaigns(status);
CREATE INDEX idx_campaigns_dates ON marketing_campaigns(start_date, end_date);

-- Transactions indexes
CREATE INDEX idx_transactions_revenue_stream ON transactions(revenue_stream_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_amount ON transactions(amount);

-- System metrics indexes
CREATE INDEX idx_system_metrics_name_time ON system_metrics(metric_name, recorded_at);
CREATE INDEX idx_api_usage_service_date ON api_usage(service, date);

-- Social media posts indexes
CREATE INDEX idx_social_posts_platform ON social_media_posts(platform);
CREATE INDEX idx_social_posts_published ON social_media_posts(published_time);
CREATE INDEX idx_social_posts_campaign ON social_media_posts(campaign_id);

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_content_items_updated_at BEFORE UPDATE ON content_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_content_templates_updated_at BEFORE UPDATE ON content_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_marketing_campaigns_updated_at BEFORE UPDATE ON marketing_campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_social_media_posts_updated_at BEFORE UPDATE ON social_media_posts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_email_campaigns_updated_at BEFORE UPDATE ON email_campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_revenue_streams_updated_at BEFORE UPDATE ON revenue_streams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_affiliate_links_updated_at BEFORE UPDATE ON affiliate_links FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_dashboards_updated_at BEFORE UPDATE ON dashboards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON data_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_metric_definitions_updated_at BEFORE UPDATE ON metric_definitions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INITIAL DATA SEEDING
-- =============================================================================

-- Insert default content templates
INSERT INTO content_templates (name, description, content_type, template_data, category) VALUES
('YouTube Video Script', 'Template for creating engaging YouTube video scripts', 'script', '{"structure": ["hook", "introduction", "main_content", "call_to_action", "outro"], "variables": ["topic", "target_audience", "duration"]}', 'video'),
('Blog Post Template', 'Standard blog post template with SEO optimization', 'blog_post', '{"structure": ["title", "introduction", "main_sections", "conclusion", "cta"], "variables": ["topic", "keywords", "word_count"]}', 'content'),
('Social Media Post', 'Engaging social media post template', 'social_post', '{"structure": ["hook", "content", "hashtags", "cta"], "variables": ["platform", "topic", "tone"]}', 'social'),
('Email Newsletter', 'Professional email newsletter template', 'email', '{"structure": ["subject", "greeting", "main_content", "cta", "signature"], "variables": ["audience", "topic", "offer"]}', 'email');

-- Insert default revenue streams
INSERT INTO revenue_streams (name, description, stream_type, platform, is_active) VALUES
('YouTube Ad Revenue', 'Revenue from YouTube monetization', 'advertising', 'youtube', true),
('Affiliate Marketing', 'Commission from affiliate product sales', 'affiliate', 'various', true),
('Digital Products', 'Sales from digital products and courses', 'product_sales', 'gumroad', true),
('Membership Subscriptions', 'Monthly recurring revenue from memberships', 'subscription', 'patreon', true),
('Consulting Services', 'Revenue from consulting and coaching', 'consulting', 'direct', true);

-- Insert default dashboards
INSERT INTO dashboards (name, description, layout, is_default) VALUES
('Revenue Overview', 'Main dashboard showing revenue metrics and trends', '{"widgets": [{"type": "revenue_chart", "position": {"x": 0, "y": 0, "w": 6, "h": 4}}, {"type": "revenue_metrics", "position": {"x": 6, "y": 0, "w": 6, "h": 4}}]}', true),
('Content Performance', 'Dashboard tracking content creation and engagement', '{"widgets": [{"type": "content_metrics", "position": {"x": 0, "y": 0, "w": 12, "h": 6}}]}', false),
('Marketing Analytics', 'Campaign performance and marketing metrics', '{"widgets": [{"type": "campaign_performance", "position": {"x": 0, "y": 0, "w": 8, "h": 6}}, {"type": "social_metrics", "position": {"x": 8, "y": 0, "w": 4, "h": 6}}]}', false);

-- Insert default alerts
INSERT INTO alerts (name, description, alert_type, severity, condition_config, is_active) VALUES
('Revenue Drop Alert', 'Alert when daily revenue drops below threshold', 'revenue_drop', 'high', '{"threshold": 100, "period": "daily", "comparison": "previous_period"}', true),
('Low Content Performance', 'Alert when content engagement is below average', 'content_performance', 'medium', '{"metric": "engagement_rate", "threshold": 0.02, "period": "weekly"}', true),
('Campaign Budget Alert', 'Alert when campaign spending exceeds budget', 'campaign_performance', 'high', '{"metric": "budget_utilization", "threshold": 0.9}', true);

-- Create initial system metrics
INSERT INTO system_metrics (metric_name, metric_value, metric_unit) VALUES
('total_content_items', 0, 'count'),
('total_revenue', 0, 'currency'),
('active_campaigns', 0, 'count'),
('total_subscribers', 0, 'count'),
('api_requests_today', 0, 'count');

COMMIT;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trae_ai_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trae_ai_user;
-- GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO trae_ai_user;
