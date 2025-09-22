-- ============================================================================
-- TRAE.AI MASTER DATABASE SCHEMA v1.0.0
-- Complete Production-Ready Database Structure
-- ============================================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ============================================================================
-- CORE SYSTEM TABLES
-- ============================================================================

-- Task Queue - Core task management system
CREATE TABLE IF NOT EXISTS task_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    task_type TEXT NOT NULL,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    payload JSON,
    result JSON,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    scheduled_for TIMESTAMP,
    metadata JSON
);

-- API Registry - Track all integrated APIs
CREATE TABLE IF NOT EXISTS api_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT UNIQUE NOT NULL,
    api_type TEXT NOT NULL,
    base_url TEXT,
    version TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated', 'testing')),
    rate_limit_per_minute INTEGER,
    rate_limit_per_day INTEGER,
    cost_per_request DECIMAL(10,6),
    authentication_type TEXT,
    requires_key BOOLEAN DEFAULT 1,
    documentation_url TEXT,
    last_health_check TIMESTAMP,
    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- API Request Logs - Track API usage and performance
CREATE TABLE IF NOT EXISTS api_request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT NOT NULL,
    endpoint TEXT,
    method TEXT DEFAULT 'GET',
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    cost DECIMAL(10,6),
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address TEXT,
    metadata JSON,
    FOREIGN KEY (api_name) REFERENCES api_registry(api_name)
);

-- ============================================================================
-- MONETIZATION TABLES
-- ============================================================================

-- Affiliate Programs - Track affiliate partnerships
CREATE TABLE IF NOT EXISTS affiliate_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id TEXT UNIQUE NOT NULL,
    program_name TEXT NOT NULL,
    company_name TEXT,
    commission_rate DECIMAL(5,2),
    commission_type TEXT CHECK (commission_type IN ('percentage', 'fixed', 'tiered')),
    cookie_duration_days INTEGER,
    minimum_payout DECIMAL(10,2),
    payment_frequency TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending', 'rejected')),
    application_date DATE,
    approval_date DATE,
    affiliate_link TEXT,
    tracking_code TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Affiliate Transactions - Track affiliate earnings
CREATE TABLE IF NOT EXISTS affiliate_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE NOT NULL,
    program_id TEXT NOT NULL,
    transaction_type TEXT CHECK (transaction_type IN ('sale', 'lead', 'click', 'impression')),
    amount DECIMAL(10,2),
    commission DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',
    transaction_date DATE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'paid', 'cancelled')),
    customer_id TEXT,
    order_id TEXT,
    product_name TEXT,
    tracking_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (program_id) REFERENCES affiliate_programs(program_id)
);

-- ============================================================================
-- CONTENT MANAGEMENT TABLES
-- ============================================================================

-- Author Personas - Manage different content personas
CREATE TABLE IF NOT EXISTS author_personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    writing_style TEXT,
    expertise_areas JSON,
    tone TEXT,
    target_audience TEXT,
    bio TEXT,
    avatar_url TEXT,
    social_links JSON,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    metadata JSON
);

-- Hypocrisy Tracker - Track contradictory statements
CREATE TABLE IF NOT EXISTS hypocrisy_tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL,
    subject_type TEXT CHECK (subject_type IN ('politician', 'celebrity', 'organization', 'brand')),
    statement_1 TEXT NOT NULL,
    statement_2 TEXT NOT NULL,
    date_1 DATE,
    date_2 DATE,
    source_1 TEXT,
    source_2 TEXT,
    context_1 TEXT,
    context_2 TEXT,
    contradiction_score INTEGER CHECK (contradiction_score BETWEEN 1 AND 10),
    verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'disputed', 'debunked')),
    impact_score INTEGER CHECK (impact_score BETWEEN 1 AND 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSON,
    metadata JSON
);

-- ============================================================================
-- ANALYTICS TABLES
-- ============================================================================

-- Channels - Track different content channels
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    channel_url TEXT,
    subscriber_count INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    total_videos INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'deleted')),
    created_date DATE,
    last_upload_date DATE,
    category TEXT,
    description TEXT,
    avatar_url TEXT,
    banner_url TEXT,
    country TEXT,
    language TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Video Performance - Track individual video metrics
CREATE TABLE IF NOT EXISTS video_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    channel_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    duration_seconds INTEGER,
    upload_date DATE,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    dislike_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2),
    ctr DECIMAL(5,2), -- Click-through rate
    avg_view_duration_seconds INTEGER,
    revenue DECIMAL(10,2),
    thumbnail_url TEXT,
    tags JSON,
    category TEXT,
    status TEXT DEFAULT 'published' CHECK (status IN ('draft', 'scheduled', 'published', 'private', 'deleted')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
);

-- Video Performance History - Track metrics over time
CREATE TABLE IF NOT EXISTS video_performance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    view_count INTEGER,
    like_count INTEGER,
    dislike_count INTEGER,
    comment_count INTEGER,
    share_count INTEGER,
    revenue DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES video_performance(video_id),
    UNIQUE(video_id, snapshot_date)
);

-- ============================================================================
-- AVATAR SYSTEM TABLES
-- ============================================================================

-- Avatars - Manage virtual personas
CREATE TABLE IF NOT EXISTS avatars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    avatar_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    avatar_type TEXT CHECK (avatar_type IN ('human', 'cartoon', 'abstract', 'brand')),
    gender TEXT,
    age_range TEXT,
    ethnicity TEXT,
    style TEXT,
    personality_traits JSON,
    voice_characteristics JSON,
    visual_assets JSON, -- URLs to images, videos, etc.
    usage_rights TEXT,
    cost_per_use DECIMAL(10,2),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    metadata JSON
);

-- Avatar Usage Log - Track avatar usage
CREATE TABLE IF NOT EXISTS avatar_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usage_id TEXT UNIQUE NOT NULL,
    avatar_id TEXT NOT NULL,
    project_id TEXT,
    usage_type TEXT CHECK (usage_type IN ('video', 'image', 'voice', 'animation')),
    duration_seconds INTEGER,
    cost DECIMAL(10,2),
    quality_settings JSON,
    output_format TEXT,
    file_size_mb DECIMAL(10,2),
    output_url TEXT,
    usage_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (avatar_id) REFERENCES avatars(avatar_id)
);

-- ============================================================================
-- RESEARCH AND EVIDENCE TABLES
-- ============================================================================

-- Evidence - Store research materials and sources
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    source_url TEXT,
    source_type TEXT CHECK (source_type IN ('article', 'video', 'document', 'image', 'audio', 'social_post', 'academic_paper')),
    author TEXT,
    publication_date DATE,
    credibility_score INTEGER CHECK (credibility_score BETWEEN 1 AND 10),
    relevance_score INTEGER CHECK (relevance_score BETWEEN 1 AND 10),
    verification_status TEXT DEFAULT 'unverified' CHECK (verification_status IN ('unverified', 'verified', 'disputed', 'debunked')),
    fact_check_url TEXT,
    bias_rating TEXT,
    topic_tags JSON,
    keywords JSON,
    summary TEXT,
    quality_score INTEGER CHECK (quality_score BETWEEN 1 AND 10),
    usage_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP,
    metadata JSON
);

-- Evidence Citations - Track how evidence is used
CREATE TABLE IF NOT EXISTS evidence_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citation_id TEXT UNIQUE NOT NULL,
    evidence_id TEXT NOT NULL,
    content_id TEXT, -- Reference to content that uses this evidence
    content_type TEXT, -- 'video', 'article', 'post', etc.
    citation_context TEXT,
    citation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_type TEXT CHECK (usage_type IN ('direct_quote', 'paraphrase', 'reference', 'inspiration')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id)
);

-- ============================================================================
-- SYSTEM CONFIGURATION TABLES
-- ============================================================================

-- System Config - Store system-wide settings
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    config_type TEXT DEFAULT 'string' CHECK (config_type IN ('string', 'integer', 'float', 'boolean', 'json')),
    description TEXT,
    category TEXT,
    is_sensitive BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
);

-- Audit Log - Track all system operations
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id TEXT UNIQUE NOT NULL,
    user_id TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    old_values JSON,
    new_values JSON,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    metadata JSON
);

-- ============================================================================
-- PROGRESSIVE SELF-REPAIR SYSTEM
-- ============================================================================

-- Repair Log - Track system repairs and maintenance
CREATE TABLE IF NOT EXISTS repair_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id TEXT UNIQUE NOT NULL,
    component_name TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT,
    repair_action TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    repair_duration_seconds INTEGER,
    success BOOLEAN,
    error_message TEXT,
    automated BOOLEAN DEFAULT 1,
    metadata JSON
);

-- Component Health - Monitor system component health
CREATE TABLE IF NOT EXISTS component_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT UNIQUE NOT NULL,
    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'warning', 'critical', 'unknown')),
    last_check_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptime_percentage DECIMAL(5,2),
    error_count_24h INTEGER DEFAULT 0,
    performance_score INTEGER CHECK (performance_score BETWEEN 0 AND 100),
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    disk_usage_mb INTEGER,
    network_latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- ============================================================================
-- API SUGGESTIONS TABLES
-- ============================================================================

-- API Suggestions - Store API recommendations
CREATE TABLE IF NOT EXISTS api_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id TEXT UNIQUE NOT NULL,
    api_name TEXT NOT NULL,
    api_category TEXT,
    description TEXT,
    use_case TEXT,
    pricing_model TEXT,
    free_tier_limits TEXT,
    documentation_url TEXT,
    popularity_score INTEGER CHECK (popularity_score BETWEEN 1 AND 10),
    reliability_score INTEGER CHECK (reliability_score BETWEEN 1 AND 10),
    ease_of_integration INTEGER CHECK (ease_of_integration BETWEEN 1 AND 10),
    status TEXT DEFAULT 'suggested' CHECK (status IN ('suggested', 'evaluating', 'approved', 'rejected', 'integrated')),
    suggested_by TEXT,
    suggested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evaluated_at TIMESTAMP,
    integration_priority INTEGER DEFAULT 5,
    notes TEXT,
    metadata JSON
);

-- Affiliate Suggestions - Store affiliate program recommendations
CREATE TABLE IF NOT EXISTS affiliate_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id TEXT UNIQUE NOT NULL,
    program_name TEXT NOT NULL,
    company_name TEXT,
    category TEXT,
    commission_rate TEXT,
    description TEXT,
    application_url TEXT,
    requirements TEXT,
    estimated_earnings TEXT,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    relevance_score INTEGER CHECK (relevance_score BETWEEN 1 AND 10),
    status TEXT DEFAULT 'suggested' CHECK (status IN ('suggested', 'researching', 'applied', 'approved', 'rejected')),
    suggested_by TEXT,
    suggested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    researched_at TIMESTAMP,
    applied_at TIMESTAMP,
    priority INTEGER DEFAULT 5,
    notes TEXT,
    metadata JSON
);

-- ============================================================================
-- CREATE ALL INDEXES
-- ============================================================================

-- Task Queue Indexes
CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status);
CREATE INDEX IF NOT EXISTS idx_task_queue_priority ON task_queue(priority);
CREATE INDEX IF NOT EXISTS idx_task_queue_type ON task_queue(task_type);
CREATE INDEX IF NOT EXISTS idx_task_queue_scheduled ON task_queue(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_task_queue_created ON task_queue(created_at);

-- API Registry Indexes
CREATE INDEX IF NOT EXISTS idx_api_registry_status ON api_registry(status);
CREATE INDEX IF NOT EXISTS idx_api_registry_type ON api_registry(api_type);
CREATE INDEX IF NOT EXISTS idx_api_registry_health ON api_registry(health_status);

-- Affiliate Programs Indexes
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_status ON affiliate_programs(status);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_company ON affiliate_programs(company_name);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_rate ON affiliate_programs(commission_rate);

-- API Suggestions Indexes
CREATE INDEX IF NOT EXISTS idx_api_suggestions_status ON api_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_api_suggestions_category ON api_suggestions(api_category);

-- Affiliate Suggestions Indexes
CREATE INDEX IF NOT EXISTS idx_affiliate_suggestions_status ON affiliate_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_affiliate_suggestions_category ON affiliate_suggestions(category);

-- API Request Logs Indexes
CREATE INDEX IF NOT EXISTS idx_api_request_logs_api_name ON api_request_logs(api_name);
CREATE INDEX IF NOT EXISTS idx_api_request_logs_timestamp ON api_request_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_request_logs_status ON api_request_logs(status_code);

-- Author Personas Indexes
CREATE INDEX IF NOT EXISTS idx_author_personas_status ON author_personas(status);
CREATE INDEX IF NOT EXISTS idx_author_personas_usage ON author_personas(usage_count);

-- Hypocrisy Tracker Indexes
CREATE INDEX IF NOT EXISTS idx_hypocrisy_tracker_subject ON hypocrisy_tracker(subject_name);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_tracker_type ON hypocrisy_tracker(subject_type);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_tracker_score ON hypocrisy_tracker(contradiction_score);

-- Channels Indexes
CREATE INDEX IF NOT EXISTS idx_channels_platform ON channels(platform);
CREATE INDEX IF NOT EXISTS idx_channels_status ON channels(status);
CREATE INDEX IF NOT EXISTS idx_channels_subscribers ON channels(subscriber_count);

-- Video Performance Indexes
CREATE INDEX IF NOT EXISTS idx_video_performance_channel ON video_performance(channel_id);
CREATE INDEX IF NOT EXISTS idx_video_performance_upload ON video_performance(upload_date);
CREATE INDEX IF NOT EXISTS idx_video_performance_views ON video_performance(view_count);
CREATE INDEX IF NOT EXISTS idx_video_performance_engagement ON video_performance(engagement_rate);

-- Avatars Indexes
CREATE INDEX IF NOT EXISTS idx_avatars_type ON avatars(avatar_type);
CREATE INDEX IF NOT EXISTS idx_avatars_status ON avatars(status);
CREATE INDEX IF NOT EXISTS idx_avatars_usage ON avatars(usage_count);

-- Evidence Indexes
CREATE INDEX IF NOT EXISTS idx_evidence_source_type ON evidence(source_type);
CREATE INDEX IF NOT EXISTS idx_evidence_credibility ON evidence(credibility_score);
CREATE INDEX IF NOT EXISTS idx_evidence_verification ON evidence(verification_status);
CREATE INDEX IF NOT EXISTS idx_evidence_publication ON evidence(publication_date);

-- System Config Indexes
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);
CREATE INDEX IF NOT EXISTS idx_system_config_sensitive ON system_config(is_sensitive);

-- Audit Log Indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- Component Health Indexes
CREATE INDEX IF NOT EXISTS idx_component_health_status ON component_health(health_status);
CREATE INDEX IF NOT EXISTS idx_component_health_check ON component_health(last_check_at);

-- Repair Log Indexes
CREATE INDEX IF NOT EXISTS idx_repair_log_component ON repair_log(component_name);
CREATE INDEX IF NOT EXISTS idx_repair_log_status ON repair_log(status);
CREATE INDEX IF NOT EXISTS idx_repair_log_severity ON repair_log(severity);

-- ============================================================================
-- INITIAL CONFIGURATION DATA
-- ============================================================================

-- Insert default system configuration
INSERT OR IGNORE INTO system_config (config_key, config_value, config_type, description, category) VALUES
('system_version', '1.0.0', 'string', 'Current system version', 'system'),
('max_task_retries', '3', 'integer', 'Maximum number of task retries', 'tasks'),
('api_rate_limit_buffer', '0.8', 'float', 'Buffer factor for API rate limits', 'api'),
('auto_repair_enabled', 'true', 'boolean', 'Enable automatic system repairs', 'maintenance'),
('log_retention_days', '90', 'integer', 'Number of days to retain logs', 'logging');

-- Insert default API registry entries
INSERT OR IGNORE INTO api_registry (api_name, api_type, base_url, status, requires_key, documentation_url) VALUES
('OpenAI', 'ai', 'https://api.openai.com/v1', 'active', 1, 'https://platform.openai.com/docs'),
('YouTube Data API', 'social', '/api/youtube/v3', 'active', 1, 'https://developers.google.com/youtube/v3'),
('Twitter API', 'social', 'https://api.twitter.com/2', 'active', 1, 'https://developer.twitter.com/en/docs');

-- ============================================================================
-- SCHEMA VALIDATION
-- ============================================================================

-- Count total tables created
SELECT COUNT(*) as total_tables FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';

-- Final status message
SELECT 'TRAE.AI Master Database Schema v1.0.0 successfully created!' as status;
