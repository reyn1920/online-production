-- TRAE.AI Master Database Schema
-- Production-ready SQLite database schema for right_perspective.db
-- 
-- This schema defines all core tables for the TRAE.AI system including:
-- - Task queue management
-- - API registry and monitoring
-- - Author personas and content management
-- - Hypocrisy tracking and analysis
-- - Affiliate program management
-- - Video performance analytics
-- - Channel management
-- - Avatar system
-- - Evidence collection and storage
--
-- Author: TRAE.AI System
-- Version: 1.0.0
-- Created: 2024

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ============================================================================
-- CORE SYSTEM TABLES
-- ============================================================================

-- Task Queue Management
-- Handles asynchronous task processing and job scheduling
CREATE TABLE IF NOT EXISTS task_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    task_type TEXT NOT NULL,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    payload JSON NOT NULL,
    result JSON,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    assigned_worker TEXT,
    timeout_seconds INTEGER DEFAULT 300,
    dependencies JSON, -- Array of task_ids this task depends on
    metadata JSON
);

-- Indexes for task_queue
CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status);
CREATE INDEX IF NOT EXISTS idx_task_queue_priority ON task_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_task_queue_type ON task_queue(task_type);
CREATE INDEX IF NOT EXISTS idx_task_queue_scheduled ON task_queue(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_task_queue_created ON task_queue(created_at);

-- API Registry and Monitoring
-- Tracks external API endpoints, rate limits, and performance
CREATE TABLE IF NOT EXISTS api_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT UNIQUE NOT NULL,
    base_url TEXT NOT NULL,
    api_version TEXT,
    capability TEXT NOT NULL DEFAULT 'general',
    authentication_type TEXT CHECK (authentication_type IN ('none', 'api_key', 'bearer_token', 'oauth2', 'basic_auth')),
    rate_limit_per_minute INTEGER,
    rate_limit_per_hour INTEGER,
    rate_limit_per_day INTEGER,
    current_usage_minute INTEGER DEFAULT 0,
    current_usage_hour INTEGER DEFAULT 0,
    current_usage_day INTEGER DEFAULT 0,
    last_reset_minute TIMESTAMP,
    last_reset_hour TIMESTAMP,
    last_reset_day TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated', 'maintenance')),
    health_check_url TEXT,
    last_health_check TIMESTAMP,
    health_status TEXT CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    signup_url TEXT,
    last_health_status TEXT DEFAULT 'unknown' CHECK (last_health_status IN ('HEALTHY', 'INVALID_KEY', 'RATE_LIMITED', 'OFFLINE', 'ERROR', 'unknown')),
    is_active BOOLEAN DEFAULT TRUE,
    average_response_time REAL,
    success_rate REAL,
    total_requests INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    allow_automatic_failover BOOLEAN DEFAULT TRUE,
    failover_priority INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 5,
    configuration JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- Indexes for api_registry
CREATE INDEX IF NOT EXISTS idx_api_registry_name ON api_registry(api_name);
CREATE INDEX IF NOT EXISTS idx_api_registry_status ON api_registry(status);
CREATE INDEX IF NOT EXISTS idx_api_registry_health ON api_registry(health_status);
CREATE INDEX IF NOT EXISTS idx_api_registry_capability ON api_registry(capability, priority, status);
CREATE INDEX IF NOT EXISTS idx_api_registry_active ON api_registry(is_active);
CREATE INDEX IF NOT EXISTS idx_api_registry_health_status ON api_registry(last_health_status);

-- Indexes for affiliate_programs
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_active ON affiliate_programs(is_active);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_health_status ON affiliate_programs(last_health_status);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_status ON affiliate_programs(status);

-- Indexes for api_suggestions
CREATE INDEX IF NOT EXISTS idx_api_suggestions_status ON api_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_api_suggestions_category ON api_suggestions(category);

-- Indexes for affiliate_suggestions
CREATE INDEX IF NOT EXISTS idx_affiliate_suggestions_status ON affiliate_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_affiliate_suggestions_category ON affiliate_suggestions(category);

-- API Request Logs
-- Detailed logging of API requests for monitoring and debugging
CREATE TABLE IF NOT EXISTS api_request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id INTEGER NOT NULL,
    request_id TEXT UNIQUE NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    request_headers JSON,
    request_body TEXT,
    response_status INTEGER,
    response_headers JSON,
    response_body TEXT,
    response_time_ms INTEGER,
    error_message TEXT,
    user_agent TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_id) REFERENCES api_registry(id) ON DELETE CASCADE
);

-- Indexes for api_request_logs
CREATE INDEX IF NOT EXISTS idx_api_logs_api_id ON api_request_logs(api_id);
CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_request_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_logs_status ON api_request_logs(response_status);
CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_request_logs(endpoint);

-- ============================================================================
-- CONTENT MANAGEMENT TABLES
-- ============================================================================

-- Author Personas
-- Manages different author personalities and writing styles
CREATE TABLE IF NOT EXISTS author_personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    writing_style JSON NOT NULL, -- Tone, vocabulary, sentence structure preferences
    personality_traits JSON, -- Humor, seriousness, expertise level, etc.
    expertise_areas JSON, -- Array of subject matter expertise
    target_audience TEXT,
    voice_characteristics JSON, -- Formal/informal, technical/accessible, etc.
    content_preferences JSON, -- Preferred content types, formats, lengths
    sample_content TEXT, -- Example content in this persona's style
    usage_guidelines TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    version INTEGER DEFAULT 1,
    parent_persona_id INTEGER, -- For persona variations
    FOREIGN KEY (parent_persona_id) REFERENCES author_personas(id)
);

-- Indexes for author_personas
CREATE INDEX IF NOT EXISTS idx_author_personas_name ON author_personas(persona_name);
CREATE INDEX IF NOT EXISTS idx_author_personas_active ON author_personas(is_active);
CREATE INDEX IF NOT EXISTS idx_author_personas_created ON author_personas(created_at);

-- Hypocrisy Tracker
-- Tracks contradictory statements and positions for analysis
CREATE TABLE IF NOT EXISTS hypocrisy_tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL,
    subject_type TEXT CHECK (subject_type IN ('person', 'organization', 'publication', 'politician', 'celebrity', 'influencer')),
    statement_1 TEXT NOT NULL,
    statement_2 TEXT NOT NULL,
    context_1 TEXT,
    context_2 TEXT,
    date_1 DATE,
    date_2 DATE,
    source_1 TEXT,
    source_2 TEXT,
    contradiction_type TEXT CHECK (contradiction_type IN ('direct', 'contextual', 'temporal', 'value', 'policy_shift', 'audience_based')),
    severity_score INTEGER CHECK (severity_score BETWEEN 1 AND 10),
    confidence_score REAL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'disputed', 'debunked')),
    evidence_links JSON, -- Array of supporting evidence URLs
    tags JSON, -- Categorization tags
    analysis_notes TEXT,
    public_impact_score INTEGER CHECK (public_impact_score BETWEEN 1 AND 10),
    media_coverage_count INTEGER DEFAULT 0,
    social_media_mentions INTEGER DEFAULT 0,
    fact_check_results JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    content_used BOOLEAN DEFAULT FALSE,
    content_used_at TIMESTAMP
);

-- Indexes for hypocrisy_tracker
CREATE INDEX IF NOT EXISTS idx_hypocrisy_subject ON hypocrisy_tracker(subject_name);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_type ON hypocrisy_tracker(subject_type);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_severity ON hypocrisy_tracker(severity_score DESC);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_verification ON hypocrisy_tracker(verification_status);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_created ON hypocrisy_tracker(created_at);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_impact ON hypocrisy_tracker(public_impact_score DESC);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_content_used ON hypocrisy_tracker(content_used);

-- ============================================================================
-- MONETIZATION AND AFFILIATE TABLES
-- ============================================================================

-- Affiliate Programs
-- Manages affiliate marketing programs and tracking
CREATE TABLE IF NOT EXISTS affiliate_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_name TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    program_url TEXT,
    affiliate_id TEXT,
    commission_rate REAL,
    commission_type TEXT CHECK (commission_type IN ('percentage', 'fixed', 'tiered', 'hybrid')),
    cookie_duration_days INTEGER,
    minimum_payout REAL,
    payment_schedule TEXT,
    payment_methods JSON,
    product_categories JSON,
    geographic_restrictions JSON,
    terms_url TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending', 'suspended', 'terminated')),
    application_date DATE,
    approval_date DATE,
    last_payment_date DATE,
    total_earnings REAL DEFAULT 0.0,
    total_clicks INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    conversion_rate REAL DEFAULT 0.0,
    average_order_value REAL DEFAULT 0.0,
    notes TEXT,
    contact_info JSON,
    signup_url TEXT,
    last_health_status TEXT DEFAULT 'unknown' CHECK (last_health_status IN ('HEALTHY', 'INVALID_KEY', 'LOGIN_FAILED', 'SUSPENDED', 'ERROR', 'unknown')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- Indexes for affiliate_programs
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_name ON affiliate_programs(program_name);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_status ON affiliate_programs(status);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_earnings ON affiliate_programs(total_earnings DESC);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_conversion ON affiliate_programs(conversion_rate DESC);

-- Affiliate Transactions
-- Tracks individual affiliate transactions and commissions
CREATE TABLE IF NOT EXISTS affiliate_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,
    transaction_id TEXT UNIQUE NOT NULL,
    click_id TEXT,
    customer_id TEXT,
    order_id TEXT,
    product_id TEXT,
    product_name TEXT,
    order_value REAL NOT NULL,
    commission_amount REAL NOT NULL,
    commission_rate REAL,
    transaction_date TIMESTAMP NOT NULL,
    click_date TIMESTAMP,
    conversion_date TIMESTAMP,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'paid', 'cancelled', 'reversed')),
    payment_date DATE,
    customer_country TEXT,
    referrer_url TEXT,
    landing_page TEXT,
    device_type TEXT,
    browser TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES affiliate_programs(id) ON DELETE CASCADE
);

-- Indexes for affiliate_transactions
CREATE INDEX IF NOT EXISTS idx_affiliate_trans_program ON affiliate_transactions(program_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_trans_date ON affiliate_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_affiliate_trans_status ON affiliate_transactions(status);
CREATE INDEX IF NOT EXISTS idx_affiliate_trans_amount ON affiliate_transactions(commission_amount DESC);

-- ============================================================================
-- VIDEO AND CONTENT PERFORMANCE TABLES
-- ============================================================================

-- Channels
-- Manages different content channels (YouTube, TikTok, etc.)
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('youtube', 'tiktok', 'instagram', 'twitter', 'facebook', 'linkedin', 'twitch', 'podcast')),
    channel_id TEXT, -- Platform-specific channel ID
    channel_url TEXT,
    display_name TEXT,
    description TEXT,
    category TEXT,
    subscriber_count INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    total_videos INTEGER DEFAULT 0,
    average_views REAL DEFAULT 0.0,
    engagement_rate REAL DEFAULT 0.0,
    upload_frequency TEXT, -- daily, weekly, monthly, etc.
    content_strategy TEXT,
    target_demographics JSON,
    monetization_enabled BOOLEAN DEFAULT FALSE,
    monetization_methods JSON, -- ads, sponsorships, merchandise, etc.
    brand_guidelines JSON,
    posting_schedule JSON,
    analytics_access_token TEXT,
    last_sync TIMESTAMP,
    total_revenue REAL DEFAULT 0.0,
    growth_rate REAL DEFAULT 0.0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'terminated')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- Indexes for channels
CREATE INDEX IF NOT EXISTS idx_channels_name ON channels(channel_name);
CREATE INDEX IF NOT EXISTS idx_channels_platform ON channels(platform);
CREATE INDEX IF NOT EXISTS idx_channels_status ON channels(status);
CREATE INDEX IF NOT EXISTS idx_channels_subscribers ON channels(subscriber_count DESC);

-- Video Performance
-- Tracks performance metrics for individual videos/content pieces
CREATE TABLE IF NOT EXISTS video_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    video_id TEXT NOT NULL, -- Platform-specific video ID
    title TEXT NOT NULL,
    description TEXT,
    thumbnail_url TEXT,
    video_url TEXT,
    duration_seconds INTEGER,
    upload_date TIMESTAMP,
    publish_date TIMESTAMP,
    category TEXT,
    tags JSON,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    dislike_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    subscriber_gain INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    average_view_duration REAL DEFAULT 0.0,
    click_through_rate REAL DEFAULT 0.0,
    engagement_rate REAL DEFAULT 0.0,
    revenue REAL DEFAULT 0.0,
    cpm REAL DEFAULT 0.0, -- Cost per mille (thousand views)
    rpm REAL DEFAULT 0.0, -- Revenue per mille
    traffic_sources JSON,
    audience_demographics JSON,
    performance_score REAL DEFAULT 0.0,
    trending_rank INTEGER,
    monetization_status TEXT,
    content_warnings JSON,
    copyright_claims JSON,
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
    UNIQUE(channel_id, video_id)
);

-- Indexes for video_performance
CREATE INDEX IF NOT EXISTS idx_video_perf_channel ON video_performance(channel_id);
CREATE INDEX IF NOT EXISTS idx_video_perf_upload ON video_performance(upload_date);
CREATE INDEX IF NOT EXISTS idx_video_perf_views ON video_performance(view_count DESC);
CREATE INDEX IF NOT EXISTS idx_video_perf_engagement ON video_performance(engagement_rate DESC);
CREATE INDEX IF NOT EXISTS idx_video_perf_revenue ON video_performance(revenue DESC);
CREATE INDEX IF NOT EXISTS idx_video_perf_score ON video_performance(performance_score DESC);

-- Video Performance History
-- Tracks historical performance data for trend analysis
CREATE TABLE IF NOT EXISTS video_performance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_performance_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    dislike_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    revenue REAL DEFAULT 0.0,
    engagement_rate REAL DEFAULT 0.0,
    trending_rank INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_performance_id) REFERENCES video_performance(id) ON DELETE CASCADE,
    UNIQUE(video_performance_id, snapshot_date)
);

-- Indexes for video_performance_history
CREATE INDEX IF NOT EXISTS idx_video_hist_video ON video_performance_history(video_performance_id);
CREATE INDEX IF NOT EXISTS idx_video_hist_date ON video_performance_history(snapshot_date);

-- ============================================================================
-- AVATAR AND IDENTITY MANAGEMENT TABLES
-- ============================================================================

-- Avatars
-- Manages virtual personas and AI-generated identities
CREATE TABLE IF NOT EXISTS avatars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    avatar_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    avatar_type TEXT CHECK (avatar_type IN ('ai_generated', 'stock_photo', 'illustrated', 'animated', 'real_person')),
    gender TEXT CHECK (gender IN ('male', 'female', 'non_binary', 'unspecified')),
    age_range TEXT,
    ethnicity TEXT,
    appearance_description TEXT,
    personality_profile JSON,
    backstory TEXT,
    occupation TEXT,
    interests JSON,
    social_media_profiles JSON,
    voice_characteristics JSON, -- For text-to-speech or voice cloning
    image_urls JSON, -- Array of avatar image URLs
    video_urls JSON, -- Array of avatar video URLs
    animation_data JSON, -- For animated avatars
    usage_rights TEXT,
    license_info TEXT,
    creation_method TEXT,
    creation_parameters JSON, -- AI generation parameters if applicable
    quality_score REAL CHECK (quality_score BETWEEN 0.0 AND 10.0),
    realism_score REAL CHECK (realism_score BETWEEN 0.0 AND 10.0),
    uniqueness_score REAL CHECK (uniqueness_score BETWEEN 0.0 AND 10.0),
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    tags JSON
);

-- Indexes for avatars
CREATE INDEX IF NOT EXISTS idx_avatars_name ON avatars(avatar_name);
CREATE INDEX IF NOT EXISTS idx_avatars_type ON avatars(avatar_type);
CREATE INDEX IF NOT EXISTS idx_avatars_active ON avatars(is_active);
CREATE INDEX IF NOT EXISTS idx_avatars_quality ON avatars(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_avatars_usage ON avatars(usage_count DESC);

-- Avatar Usage Log
-- Tracks when and how avatars are used
CREATE TABLE IF NOT EXISTS avatar_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    avatar_id INTEGER NOT NULL,
    usage_context TEXT NOT NULL, -- video, social_post, article, etc.
    content_id TEXT, -- Reference to the content where avatar was used
    platform TEXT,
    duration_seconds INTEGER, -- For video usage
    engagement_metrics JSON,
    performance_score REAL,
    usage_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    FOREIGN KEY (avatar_id) REFERENCES avatars(id) ON DELETE CASCADE
);

-- Indexes for avatar_usage_log
CREATE INDEX IF NOT EXISTS idx_avatar_usage_avatar ON avatar_usage_log(avatar_id);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_date ON avatar_usage_log(usage_date);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_context ON avatar_usage_log(usage_context);

-- ============================================================================
-- EVIDENCE AND RESEARCH TABLES
-- ============================================================================

-- Evidence
-- Stores research evidence, sources, and supporting materials
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    evidence_type TEXT CHECK (evidence_type IN ('document', 'video', 'audio', 'image', 'webpage', 'social_media', 'news_article', 'academic_paper', 'government_record', 'court_document')),
    source_url TEXT,
    source_name TEXT,
    source_credibility_score REAL CHECK (source_credibility_score BETWEEN 0.0 AND 10.0),
    publication_date DATE,
    access_date DATE,
    author TEXT,
    publisher TEXT,
    content_text TEXT, -- Full text content if available
    content_summary TEXT,
    file_path TEXT, -- Local file storage path
    file_size INTEGER,
    file_hash TEXT, -- For integrity verification
    metadata JSON, -- Additional metadata (EXIF, document properties, etc.)
    tags JSON,
    categories JSON,
    relevance_score REAL CHECK (relevance_score BETWEEN 0.0 AND 10.0),
    verification_status TEXT DEFAULT 'unverified' CHECK (verification_status IN ('unverified', 'verified', 'disputed', 'debunked', 'pending')),
    verification_notes TEXT,
    verified_by TEXT,
    verified_at TIMESTAMP,
    access_restrictions TEXT,
    copyright_info TEXT,
    usage_rights TEXT,
    related_evidence JSON, -- Array of related evidence IDs
    citations_count INTEGER DEFAULT 0,
    quality_score REAL CHECK (quality_score BETWEEN 0.0 AND 10.0),
    bias_assessment JSON,
    fact_check_results JSON,
    archive_urls JSON, -- Wayback Machine, Archive.today, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- Indexes for evidence
CREATE INDEX IF NOT EXISTS idx_evidence_id ON evidence(evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(evidence_type);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source_name);
CREATE INDEX IF NOT EXISTS idx_evidence_date ON evidence(publication_date);
CREATE INDEX IF NOT EXISTS idx_evidence_credibility ON evidence(source_credibility_score DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_relevance ON evidence(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_verification ON evidence(verification_status);
CREATE INDEX IF NOT EXISTS idx_evidence_quality ON evidence(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_created ON evidence(created_at);

-- Evidence Citations
-- Tracks how evidence is cited and used across content
CREATE TABLE IF NOT EXISTS evidence_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id INTEGER NOT NULL,
    citing_content_type TEXT NOT NULL, -- video, article, social_post, etc.
    citing_content_id TEXT NOT NULL,
    citation_context TEXT,
    citation_quote TEXT,
    page_number INTEGER,
    timestamp_seconds INTEGER, -- For video/audio citations
    citation_strength TEXT CHECK (citation_strength IN ('primary', 'secondary', 'supporting', 'contradictory')),
    citation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- Indexes for evidence_citations
CREATE INDEX IF NOT EXISTS idx_evidence_cit_evidence ON evidence_citations(evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_cit_content ON evidence_citations(citing_content_type, citing_content_id);
CREATE INDEX IF NOT EXISTS idx_evidence_cit_date ON evidence_citations(citation_date);

-- ============================================================================
-- SYSTEM CONFIGURATION AND METADATA TABLES
-- ============================================================================

-- System Configuration
-- Stores system-wide configuration settings
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type TEXT DEFAULT 'string' CHECK (config_type IN ('string', 'integer', 'float', 'boolean', 'json')),
    description TEXT,
    category TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    is_readonly BOOLEAN DEFAULT FALSE,
    validation_regex TEXT,
    default_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
);

-- Indexes for system_config
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);

-- Audit Log
-- Comprehensive audit trail for all system operations
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSON,
    new_values JSON,
    changed_fields JSON,
    user_id TEXT,
    session_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context JSON -- Additional context information
);

-- Indexes for audit_log
CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_record ON audit_log(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Update timestamps automatically
CREATE TRIGGER IF NOT EXISTS update_task_queue_timestamp 
    AFTER UPDATE ON task_queue
    BEGIN
        UPDATE task_queue SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_api_registry_timestamp 
    AFTER UPDATE ON api_registry
    BEGIN
        UPDATE api_registry SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_author_personas_timestamp 
    AFTER UPDATE ON author_personas
    BEGIN
        UPDATE author_personas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_hypocrisy_tracker_timestamp 
    AFTER UPDATE ON hypocrisy_tracker
    BEGIN
        UPDATE hypocrisy_tracker SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_affiliate_programs_timestamp 
    AFTER UPDATE ON affiliate_programs
    BEGIN
        UPDATE affiliate_programs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_affiliate_transactions_timestamp 
    AFTER UPDATE ON affiliate_transactions
    BEGIN
        UPDATE affiliate_transactions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_channels_timestamp 
    AFTER UPDATE ON channels
    BEGIN
        UPDATE channels SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_avatars_timestamp 
    AFTER UPDATE ON avatars
    BEGIN
        UPDATE avatars SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_evidence_timestamp 
    AFTER UPDATE ON evidence
    BEGIN
        UPDATE evidence SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_system_config_timestamp 
    AFTER UPDATE ON system_config
    BEGIN
        UPDATE system_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active Tasks View
CREATE VIEW IF NOT EXISTS active_tasks AS
SELECT 
    task_id,
    task_type,
    priority,
    status,
    created_at,
    scheduled_at,
    retry_count,
    max_retries
FROM task_queue 
WHERE status IN ('pending', 'running')
ORDER BY priority DESC, created_at ASC;

-- Channel Performance Summary
CREATE VIEW IF NOT EXISTS channel_performance_summary AS
SELECT 
    c.channel_name,
    c.platform,
    c.subscriber_count,
    COUNT(vp.id) as total_videos,
    AVG(vp.view_count) as avg_views,
    AVG(vp.engagement_rate) as avg_engagement,
    SUM(vp.revenue) as total_revenue,
    MAX(vp.upload_date) as last_upload
FROM channels c
LEFT JOIN video_performance vp ON c.id = vp.channel_id
WHERE c.status = 'active'
GROUP BY c.id, c.channel_name, c.platform, c.subscriber_count;

-- Evidence Quality Summary
CREATE VIEW IF NOT EXISTS evidence_quality_summary AS
SELECT 
    evidence_type,
    verification_status,
    COUNT(*) as count,
    AVG(source_credibility_score) as avg_credibility,
    AVG(quality_score) as avg_quality,
    AVG(relevance_score) as avg_relevance
FROM evidence
GROUP BY evidence_type, verification_status;

-- API Health Dashboard
CREATE VIEW IF NOT EXISTS api_health_dashboard AS
SELECT 
    api_name,
    status,
    health_status,
    success_rate,
    average_response_time,
    current_usage_hour,
    rate_limit_per_hour,
    (CAST(current_usage_hour AS REAL) / NULLIF(rate_limit_per_hour, 0)) * 100 as usage_percentage,
    last_health_check
FROM api_registry
WHERE status = 'active';

-- ============================================================================
-- PROGRESSIVE SELF-REPAIR SYSTEM
-- ============================================================================

-- Repair Log for Progressive Self-Repair Protocol
-- Tracks component failures, repair attempts, and outcomes for intelligent escalation
CREATE TABLE IF NOT EXISTS repair_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    error_message TEXT NOT NULL,
    error_type TEXT,
    repair_tier INTEGER NOT NULL CHECK (repair_tier IN (1, 2, 3)),
    repair_action TEXT NOT NULL,
    repair_outcome TEXT CHECK (repair_outcome IN ('success', 'failure', 'partial')),
    execution_details TEXT,
    error_context JSON,
    repair_duration_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    next_escalation_tier INTEGER,
    failure_count INTEGER DEFAULT 1,
    last_failure_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for repair_log
CREATE INDEX IF NOT EXISTS idx_repair_log_component ON repair_log(component_name);
CREATE INDEX IF NOT EXISTS idx_repair_log_created ON repair_log(created_at);
CREATE INDEX IF NOT EXISTS idx_repair_log_outcome ON repair_log(repair_outcome);
CREATE INDEX IF NOT EXISTS idx_repair_log_tier ON repair_log(repair_tier);

-- Component Health Status
-- Tracks current health status of system components
CREATE TABLE IF NOT EXISTS component_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'healthy' CHECK (status IN ('healthy', 'degraded', 'failing', 'critical')),
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,
    uptime_percentage REAL DEFAULT 100.0,
    last_failure_at TIMESTAMP,
    recovery_time_avg REAL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for component_health
CREATE INDEX IF NOT EXISTS idx_component_health_status ON component_health(status);
CREATE INDEX IF NOT EXISTS idx_component_health_name ON component_health(component_name);

-- ============================================================================
-- INITIAL CONFIGURATION DATA
-- ============================================================================

-- Insert default system configuration
INSERT OR IGNORE INTO system_config (config_key, config_value, config_type, description, category) VALUES
('system_version', '1.0.0', 'string', 'Current system version', 'system'),
('max_task_retries', '3', 'integer', 'Maximum number of task retries', 'tasks'),
('task_timeout_seconds', '300', 'integer', 'Default task timeout in seconds', 'tasks'),
('api_rate_limit_buffer', '0.8', 'float', 'Buffer percentage for API rate limits (0.8 = 80%)', 'api'),
('evidence_auto_archive', 'true', 'boolean', 'Automatically archive evidence URLs', 'evidence'),
('avatar_max_usage_count', '100', 'integer', 'Maximum usage count before avatar retirement', 'avatars'),
('performance_retention_days', '365', 'integer', 'Days to retain performance history', 'analytics'),
('audit_log_retention_days', '1095', 'integer', 'Days to retain audit logs (3 years)', 'system'),
('backup_frequency_hours', '24', 'integer', 'Frequency of automatic backups in hours', 'system'),
('content_quality_threshold', '7.0', 'float', 'Minimum quality score for content approval', 'content');

-- Insert default API registry entries (examples)
INSERT OR IGNORE INTO api_registry (api_name, base_url, api_version, authentication_type, rate_limit_per_minute, rate_limit_per_hour, status) VALUES
('openai_api', 'https://api.openai.com', 'v1', 'bearer_token', 60, 3000, 'active'),
('youtube_api', 'https://www.googleapis.com/youtube/v3', 'v3', 'api_key', 100, 10000, 'active'),
('twitter_api', 'https://api.twitter.com', '2', 'bearer_token', 300, 15000, 'active');

-- ============================================================================
-- SCHEMA VALIDATION AND INTEGRITY CHECKS
-- ============================================================================

-- Verify all tables were created successfully
SELECT 'Schema creation completed. Total tables: ' || COUNT(*) as status 
FROM sqlite_master 
WHERE type = 'table' AND name NOT LIKE 'sqlite_%';

-- Display table summary
SELECT 
    name as table_name,
    CASE 
        WHEN name LIKE '%_log' OR name LIKE '%_history' THEN 'Logging/History'
        WHEN name IN ('task_queue', 'api_registry', 'api_request_logs') THEN 'System Core'
        WHEN name IN ('author_personas', 'hypocrisy_tracker') THEN 'Content Management'
        WHEN name IN ('affiliate_programs', 'affiliate_transactions') THEN 'Monetization'
        WHEN name IN ('channels', 'video_performance', 'video_performance_history', 'performance_metrics') THEN 'Analytics'
        WHEN name IN ('avatars', 'avatar_usage_log') THEN 'Avatar System'
        WHEN name IN ('evidence', 'evidence_citations') THEN 'Research/Evidence'
        WHEN name IN ('system_config', 'audit_log') THEN 'System Configuration'
        ELSE 'Other'
    END as category
FROM sqlite_master 
WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
ORDER BY category, name;

-- Schema version and metadata
CREATE TABLE IF NOT EXISTS schema_metadata (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    checksum TEXT
);

-- ============================================================================
-- AGENT-SPECIFIC TABLES
-- ============================================================================

-- Financial Management Tables
CREATE TABLE IF NOT EXISTS channel_financials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    revenue REAL DEFAULT 0.0,
    expenses REAL DEFAULT 0.0,
    profit REAL DEFAULT 0.0,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resource_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    allocated_amount REAL NOT NULL,
    used_amount REAL DEFAULT 0.0,
    allocation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    forecast_period TEXT NOT NULL,
    predicted_revenue REAL NOT NULL,
    confidence_score REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT DEFAULT 'medium',
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS budget_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    budget_category TEXT NOT NULL,
    allocated_budget REAL NOT NULL,
    spent_amount REAL DEFAULT 0.0,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS allocation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    allocation_type TEXT NOT NULL,
    amount REAL NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_metrics_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS affiliate_payouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    affiliate_id TEXT NOT NULL,
    amount REAL NOT NULL,
    payout_date DATE NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- YouTube Engagement Tables
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    comment_id TEXT UNIQUE NOT NULL,
    author_name TEXT NOT NULL,
    comment_text TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS engagement_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    comment_id TEXT,
    opportunity_type TEXT NOT NULL,
    priority_score REAL NOT NULL,
    suggested_response TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS engagement_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER NOT NULL,
    action_taken TEXT NOT NULL,
    response_text TEXT,
    engagement_metrics JSON,
    success_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES engagement_opportunities(id)
);

CREATE TABLE IF NOT EXISTS topic_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_name TEXT UNIQUE NOT NULL,
    keywords JSON NOT NULL,
    engagement_history JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS engagement_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    engagement_type TEXT NOT NULL,
    engagement_data JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Twitter Engagement Tables
CREATE TABLE IF NOT EXISTS user_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    interaction_type TEXT NOT NULL,
    content TEXT,
    engagement_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topic_engagement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    engagement_count INTEGER DEFAULT 0,
    last_engagement TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT UNIQUE NOT NULL,
    participants JSON,
    messages JSON,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Twitter Promotion Tables
CREATE TABLE IF NOT EXISTS promotion_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name TEXT NOT NULL,
    video_id TEXT NOT NULL,
    hashtags JSON,
    target_audience TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hashtag_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hashtag TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0,
    engagement_rate REAL DEFAULT 0.0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS video_promotions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    promotion_text TEXT NOT NULL,
    scheduled_time TIMESTAMP,
    posted BOOLEAN DEFAULT FALSE,
    engagement_metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Growth and Niche Tables
CREATE TABLE IF NOT EXISTS growth_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    metric_value REAL NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS niche_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_name TEXT NOT NULL,
    opportunity_score REAL NOT NULL,
    market_size REAL,
    competition_level TEXT,
    recommended_action TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS niche_expansions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    current_niche TEXT NOT NULL,
    target_niche TEXT NOT NULL,
    expansion_strategy TEXT,
    success_probability REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channel_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    subscribers INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    engagement_rate REAL DEFAULT 0.0,
    growth_rate REAL DEFAULT 0.0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expansion_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    expansion_type TEXT NOT NULL,
    target_metrics JSON,
    timeline TEXT,
    status TEXT DEFAULT 'planning',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS growth_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    growth_event TEXT NOT NULL,
    impact_metrics JSON,
    event_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content Evolution Tables
CREATE TABLE IF NOT EXISTS format_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    format_type TEXT NOT NULL,
    trend_score REAL NOT NULL,
    popularity_change REAL,
    recommended_adoption BOOLEAN DEFAULT FALSE,
    analysis_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content_adaptations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_content_id TEXT NOT NULL,
    adapted_format TEXT NOT NULL,
    adaptation_strategy TEXT,
    performance_prediction REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS format_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    format_type TEXT NOT NULL,
    performance_metrics JSON,
    audience_response TEXT,
    success_rate REAL,
    evaluation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evolution_experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_name TEXT NOT NULL,
    hypothesis TEXT,
    test_parameters JSON,
    results JSON,
    conclusion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trend_name TEXT NOT NULL,
    trend_data JSON,
    impact_score REAL,
    recommendation TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tool_generation_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    purpose TEXT,
    specifications JSON,
    priority_score REAL,
    status TEXT DEFAULT 'planned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evolution_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    current_value REAL,
    target_value REAL,
    improvement_rate REAL,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS platform_monitoring_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name TEXT NOT NULL,
    monitoring_data JSON,
    alerts JSON,
    status TEXT DEFAULT 'active',
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stealth Automation Tables
CREATE TABLE IF NOT EXISTS stealth_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_name TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,
    credentials_encrypted TEXT,
    proxy_config JSON,
    behavioral_patterns JSON,
    last_activity TIMESTAMP,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS automation_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    session_type TEXT NOT NULL,
    actions_performed JSON,
    success_rate REAL,
    session_start TIMESTAMP,
    session_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES stealth_profiles(id)
);

CREATE TABLE IF NOT EXISTS affiliate_dashboards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name TEXT NOT NULL,
    dashboard_url TEXT,
    login_credentials_encrypted TEXT,
    last_scraped TIMESTAMP,
    scraping_config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payout_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dashboard_id INTEGER NOT NULL,
    payout_amount REAL NOT NULL,
    payout_date DATE NOT NULL,
    payment_method TEXT,
    transaction_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dashboard_id) REFERENCES affiliate_dashboards(id)
);

CREATE TABLE IF NOT EXISTS detection_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    detection_type TEXT NOT NULL,
    severity TEXT DEFAULT 'medium',
    details JSON,
    mitigation_action TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES stealth_profiles(id)
);

-- Creator Collaboration Tables
CREATE TABLE IF NOT EXISTS creator_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_name TEXT NOT NULL,
    platform TEXT NOT NULL,
    follower_count INTEGER,
    engagement_rate REAL,
    niche TEXT,
    contact_info JSON,
    collaboration_history JSON,
    rating REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS outreach_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name TEXT NOT NULL,
    target_creators JSON,
    message_template TEXT,
    campaign_goals TEXT,
    status TEXT DEFAULT 'active',
    success_rate REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collaboration_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    opportunity_type TEXT NOT NULL,
    proposal_details TEXT,
    expected_reach INTEGER,
    estimated_cost REAL,
    status TEXT DEFAULT 'proposed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES creator_profiles(id)
);

CREATE TABLE IF NOT EXISTS outreach_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    messages_sent INTEGER DEFAULT 0,
    responses_received INTEGER DEFAULT 0,
    collaborations_secured INTEGER DEFAULT 0,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES outreach_campaigns(id)
);

-- Strategic Advisor Tables
CREATE TABLE IF NOT EXISTS strategic_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_type TEXT NOT NULL,
    insight_data JSON,
    confidence_score REAL,
    actionable_recommendations JSON,
    impact_assessment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_name TEXT NOT NULL,
    market_size REAL,
    competition_analysis JSON,
    entry_strategy TEXT,
    risk_assessment TEXT,
    potential_roi REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategic_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_title TEXT NOT NULL,
    description TEXT,
    priority_level TEXT DEFAULT 'medium',
    implementation_timeline TEXT,
    expected_outcomes JSON,
    resource_requirements JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quarterly_briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quarter TEXT NOT NULL,
    year INTEGER NOT NULL,
    performance_summary JSON,
    key_achievements JSON,
    challenges_faced JSON,
    next_quarter_goals JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategic_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_category TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    current_value REAL,
    target_value REAL,
    trend_direction TEXT,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Analytics Tables
CREATE TABLE IF NOT EXISTS content_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    engagement_rate REAL DEFAULT 0.0,
    performance_score REAL,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value TEXT,
    feature_impact_score REAL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id TEXT NOT NULL,
    prediction_type TEXT NOT NULL,
    predicted_value REAL,
    confidence_interval JSON,
    model_version TEXT,
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trend_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    frequency INTEGER,
    trend_direction TEXT,
    confidence_score REAL,
    trend_score REAL,
    last_updated DATETIME,
    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    time_window TEXT
);

CREATE TABLE IF NOT EXISTS performance_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_type TEXT NOT NULL,
    insight_data JSON,
    actionable_items JSON,
    priority_score REAL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Research and News Tables
CREATE TABLE IF NOT EXISTS news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    source TEXT,
    url TEXT,
    published_date TIMESTAMP,
    relevance_score REAL,
    keywords JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intelligence_briefings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    summary TEXT,
    key_points TEXT,
    sources TEXT,
    briefing_type TEXT,
    content TEXT,
    priority TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Monitoring Tables
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT,
    component TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS application_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_component TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    metric_value REAL NOT NULL,
    threshold_warning REAL,
    threshold_critical REAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    severity TEXT DEFAULT 'medium',
    message TEXT NOT NULL,
    component TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Error Tracking Tables
CREATE TABLE IF NOT EXISTS error_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    component TEXT,
    severity TEXT DEFAULT 'medium',
    user_context JSON,
    environment TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    alert_data JSON,
    recipients JSON,
    delivery_status TEXT DEFAULT 'pending',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS error_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name TEXT NOT NULL,
    pattern_description TEXT,
    occurrence_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Safe Mode and Environment Tables
CREATE TABLE IF NOT EXISTS environment_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_name TEXT NOT NULL,
    environment_state JSON,
    configuration_backup JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rollback_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rollback_reason TEXT NOT NULL,
    previous_state JSON,
    rollback_actions JSON,
    success BOOLEAN DEFAULT FALSE,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rollback_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    rollback_reason TEXT,
    previous_version TEXT,
    current_version TEXT,
    rollback_data JSON,
    success BOOLEAN DEFAULT FALSE,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance and Rule Enforcement Tables
CREATE TABLE IF NOT EXISTS scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_type TEXT NOT NULL,
    target_path TEXT,
    violations_found INTEGER DEFAULT 0,
    scan_results JSON,
    scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enforcement_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,
    enforcement_action TEXT,
    target_file TEXT,
    action_result TEXT,
    enforced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compliance_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_name TEXT NOT NULL,
    scan_config JSON,
    results JSON,
    compliance_score REAL,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    violation_type TEXT NOT NULL,
    severity TEXT DEFAULT 'medium',
    description TEXT,
    file_path TEXT,
    line_number INTEGER,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enforcement_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    violation_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    action_details JSON,
    success BOOLEAN DEFAULT FALSE,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (violation_id) REFERENCES violations(id)
);

-- API and Integration Tables
CREATE TABLE IF NOT EXISTS api_discovery_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    target_capability TEXT,
    search_parameters TEXT,
    task_name TEXT,
    capability_gap TEXT,
    search_keywords TEXT, -- JSON array of search terms
    target_domains TEXT, -- JSON array of target domains
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending',
    assigned_agent TEXT,
    progress_notes TEXT,
    apis_found INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT NOT NULL,
    api_description TEXT,
    signup_url TEXT,
    category TEXT,
    use_case TEXT,
    integration_complexity TEXT CHECK (integration_complexity IN ('low', 'medium', 'high')) DEFAULT 'medium',
    potential_value REAL DEFAULT 0.0,
    source_url TEXT,
    research_notes TEXT,
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'reviewed', 'added', 'rejected')),
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    suggested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Affiliate Suggestions Table
-- Tracks discovered affiliate program opportunities
CREATE TABLE IF NOT EXISTS affiliate_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_name TEXT NOT NULL,
    company_name TEXT NOT NULL,
    program_description TEXT,
    signup_url TEXT NOT NULL,
    commission_rate TEXT,
    commission_type TEXT,
    cookie_duration TEXT,
    minimum_payout TEXT,
    category TEXT,
    potential_value REAL DEFAULT 0.0,
    integration_complexity TEXT CHECK (integration_complexity IN ('low', 'medium', 'high')) DEFAULT 'medium',
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_url TEXT,
    research_notes TEXT,
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'reviewed', 'added', 'rejected'))
);

CREATE TABLE IF NOT EXISTS api_orchestration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orchestration_id TEXT NOT NULL,
    api_calls JSON,
    execution_time REAL,
    success BOOLEAN DEFAULT FALSE,
    error_details TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_usage_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id INTEGER,
    api_name TEXT NOT NULL,
    endpoint TEXT,
    usage_count INTEGER DEFAULT 1,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time_avg REAL,
    FOREIGN KEY (api_id) REFERENCES api_registry(id) ON DELETE SET NULL
);

-- Cache and Integration Tables
CREATE TABLE IF NOT EXISTS response_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT UNIQUE NOT NULL,
    response_data JSON,
    expiry_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    usage_count INTEGER DEFAULT 1,
    total_tokens INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Secrets Management Table
CREATE TABLE IF NOT EXISTS secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_name TEXT UNIQUE NOT NULL,
    encrypted_value TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Generated Reports Table
CREATE TABLE IF NOT EXISTS generated_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT NOT NULL,
    report_data JSON,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT
);

-- Performance Metrics
-- Tracks system performance and operational metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR AGENT-SPECIFIC TABLES
-- ============================================================================

-- Financial Management Indexes
CREATE INDEX IF NOT EXISTS idx_channel_financials_channel_id ON channel_financials(channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_financials_period ON channel_financials(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_resource_allocations_channel_id ON resource_allocations(channel_id);
CREATE INDEX IF NOT EXISTS idx_financial_alerts_channel_id ON financial_alerts(channel_id);
CREATE INDEX IF NOT EXISTS idx_financial_alerts_resolved ON financial_alerts(resolved);

-- YouTube Engagement Indexes
CREATE INDEX IF NOT EXISTS idx_comments_video_id ON comments(video_id);
CREATE INDEX IF NOT EXISTS idx_comments_comment_id ON comments(comment_id);
CREATE INDEX IF NOT EXISTS idx_engagement_opportunities_video_id ON engagement_opportunities(video_id);
CREATE INDEX IF NOT EXISTS idx_engagement_opportunities_status ON engagement_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_engagement_results_opportunity_id ON engagement_results(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_topic_profiles_topic_name ON topic_profiles(topic_name);

-- Twitter Engagement Indexes
CREATE INDEX IF NOT EXISTS idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_topic_engagement_topic ON topic_engagement(topic);
CREATE INDEX IF NOT EXISTS idx_conversation_cache_conversation_id ON conversation_cache(conversation_id);

-- Twitter Promotion Indexes
CREATE INDEX IF NOT EXISTS idx_promotion_campaigns_video_id ON promotion_campaigns(video_id);
CREATE INDEX IF NOT EXISTS idx_promotion_campaigns_status ON promotion_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_hashtag_performance_hashtag ON hashtag_performance(hashtag);
CREATE INDEX IF NOT EXISTS idx_video_promotions_video_id ON video_promotions(video_id);
CREATE INDEX IF NOT EXISTS idx_video_promotions_posted ON video_promotions(posted);

-- Growth and Niche Indexes
CREATE INDEX IF NOT EXISTS idx_growth_metrics_channel_id ON growth_metrics(channel_id);
CREATE INDEX IF NOT EXISTS idx_growth_metrics_type ON growth_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_niche_opportunities_score ON niche_opportunities(opportunity_score);
CREATE INDEX IF NOT EXISTS idx_channel_metrics_channel_id ON channel_metrics(channel_id);
CREATE INDEX IF NOT EXISTS idx_expansion_plans_channel_id ON expansion_plans(channel_id);
CREATE INDEX IF NOT EXISTS idx_expansion_plans_status ON expansion_plans(status);

-- Content Evolution Indexes
CREATE INDEX IF NOT EXISTS idx_format_trends_format_type ON format_trends(format_type);
CREATE INDEX IF NOT EXISTS idx_format_trends_analysis_date ON format_trends(analysis_date);
CREATE INDEX IF NOT EXISTS idx_content_adaptations_original_id ON content_adaptations(original_content_id);
CREATE INDEX IF NOT EXISTS idx_format_performance_format_type ON format_performance(format_type);
CREATE INDEX IF NOT EXISTS idx_evolution_experiments_name ON evolution_experiments(experiment_name);

-- Stealth Automation Indexes
CREATE INDEX IF NOT EXISTS idx_stealth_profiles_profile_name ON stealth_profiles(profile_name);
CREATE INDEX IF NOT EXISTS idx_stealth_profiles_platform ON stealth_profiles(platform);
CREATE INDEX IF NOT EXISTS idx_stealth_profiles_status ON stealth_profiles(status);
CREATE INDEX IF NOT EXISTS idx_automation_sessions_profile_id ON automation_sessions(profile_id);
CREATE INDEX IF NOT EXISTS idx_detection_events_profile_id ON detection_events(profile_id);
CREATE INDEX IF NOT EXISTS idx_detection_events_resolved ON detection_events(resolved);

-- Creator Collaboration Indexes
CREATE INDEX IF NOT EXISTS idx_creator_profiles_platform ON creator_profiles(platform);
CREATE INDEX IF NOT EXISTS idx_creator_profiles_niche ON creator_profiles(niche);
CREATE INDEX IF NOT EXISTS idx_outreach_campaigns_status ON outreach_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_collaboration_opportunities_creator_id ON collaboration_opportunities(creator_id);
CREATE INDEX IF NOT EXISTS idx_collaboration_opportunities_status ON collaboration_opportunities(status);

-- Strategic Advisor Indexes
CREATE INDEX IF NOT EXISTS idx_strategic_insights_type ON strategic_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_market_opportunities_name ON market_opportunities(opportunity_name);
CREATE INDEX IF NOT EXISTS idx_strategic_recommendations_priority ON strategic_recommendations(priority_level);
CREATE INDEX IF NOT EXISTS idx_quarterly_briefs_quarter_year ON quarterly_briefs(quarter, year);
CREATE INDEX IF NOT EXISTS idx_strategic_metrics_category ON strategic_metrics(metric_category);

-- Performance Analytics Indexes
CREATE INDEX IF NOT EXISTS idx_content_performance_content_id ON content_performance(content_id);
CREATE INDEX IF NOT EXISTS idx_content_performance_platform ON content_performance(platform);
CREATE INDEX IF NOT EXISTS idx_content_features_content_id ON content_features(content_id);
CREATE INDEX IF NOT EXISTS idx_predictions_content_id ON predictions(content_id);
CREATE INDEX IF NOT EXISTS idx_trend_analysis_trend_name ON trend_analysis(trend_name);

-- Research and News Indexes
CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles(source);
CREATE INDEX IF NOT EXISTS idx_news_articles_published_date ON news_articles(published_date);
CREATE INDEX IF NOT EXISTS idx_intelligence_briefings_title ON intelligence_briefings(briefing_title);

-- System Monitoring Indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_component ON system_metrics(component);
CREATE INDEX IF NOT EXISTS idx_application_metrics_component ON application_metrics(app_component);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_resolved ON performance_alerts(resolved);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_severity ON performance_alerts(severity);

-- Error Tracking Indexes
CREATE INDEX IF NOT EXISTS idx_error_events_type ON error_events(error_type);
CREATE INDEX IF NOT EXISTS idx_error_events_component ON error_events(component);
CREATE INDEX IF NOT EXISTS idx_error_events_resolved ON error_events(resolved);
CREATE INDEX IF NOT EXISTS idx_alert_history_type ON alert_history(alert_type);
CREATE INDEX IF NOT EXISTS idx_error_patterns_name ON error_patterns(pattern_name);

-- Safe Mode and Environment Indexes
CREATE INDEX IF NOT EXISTS idx_environment_snapshots_name ON environment_snapshots(snapshot_name);
CREATE INDEX IF NOT EXISTS idx_rollback_history_performed_at ON rollback_history(performed_at);
CREATE INDEX IF NOT EXISTS idx_rollback_log_component ON rollback_log(component_name);

-- Compliance and Rule Enforcement Indexes
CREATE INDEX IF NOT EXISTS idx_scan_results_type ON scan_results(scan_type);
CREATE INDEX IF NOT EXISTS idx_scan_results_timestamp ON scan_results(scan_timestamp);
CREATE INDEX IF NOT EXISTS idx_enforcement_history_rule ON enforcement_history(rule_name);
CREATE INDEX IF NOT EXISTS idx_compliance_scans_name ON compliance_scans(scan_name);
CREATE INDEX IF NOT EXISTS idx_violations_type ON violations(violation_type);
CREATE INDEX IF NOT EXISTS idx_violations_severity ON violations(severity);

-- API and Integration Indexes
CREATE INDEX IF NOT EXISTS idx_api_discovery_tasks_status ON api_discovery_tasks(status);
CREATE INDEX IF NOT EXISTS idx_api_suggestions_name ON api_suggestions(api_name);
CREATE INDEX IF NOT EXISTS idx_api_orchestration_log_id ON api_orchestration_log(orchestration_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_tracking_name ON api_usage_tracking(api_name);

-- Cache and Integration Indexes
CREATE INDEX IF NOT EXISTS idx_response_cache_key ON response_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_response_cache_expiry ON response_cache(expiry_time);
CREATE INDEX IF NOT EXISTS idx_model_usage_name ON model_usage(model_name);

-- Secrets Management Indexes
CREATE INDEX IF NOT EXISTS idx_secrets_key_name ON secrets(key_name);
CREATE INDEX IF NOT EXISTS idx_secrets_expires_at ON secrets(expires_at);

-- Generated Reports Indexes
CREATE INDEX IF NOT EXISTS idx_generated_reports_type ON generated_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_generated_reports_generated_at ON generated_reports(generated_at);

-- Indexes for performance_metrics
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type);

-- ============================================================================
-- CLOUD SOFTWARE INTEGRATION MANAGEMENT
-- ============================================================================

-- Cloud Software Products table - Manage integrated cloud software and tools
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
    configuration JSON, -- Software-specific configuration
    capabilities JSON, -- Array of capabilities this software provides
    dependencies JSON, -- Array of other software this depends on
    installation_status TEXT DEFAULT 'not_installed' CHECK (installation_status IN ('not_installed', 'installing', 'installed', 'failed', 'updating')),
    installation_path TEXT,
    license_type TEXT CHECK (license_type IN ('free', 'paid', 'subscription', 'one_time', 'trial')),
    license_expires_at TIMESTAMP,
    subscription_status TEXT CHECK (subscription_status IN ('active', 'expired', 'cancelled', 'trial', 'none')),
    monthly_cost DECIMAL(10,2),
    annual_cost DECIMAL(10,2),
    usage_metrics JSON, -- Track usage statistics
    performance_metrics JSON, -- Track performance data
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

-- Software Usage Logs table - Track usage of cloud software
CREATE TABLE IF NOT EXISTS software_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    software_id INTEGER NOT NULL,
    usage_type TEXT NOT NULL, -- 'api_call', 'rpa_execution', 'manual_use', 'batch_process'
    operation TEXT, -- Specific operation performed
    input_data JSON, -- Input parameters or data
    output_data JSON, -- Results or output
    execution_time_ms INTEGER,
    status TEXT CHECK (status IN ('success', 'failed', 'timeout', 'cancelled')),
    error_message TEXT,
    cost DECIMAL(10,4), -- Cost for this usage if applicable
    user_id TEXT,
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (software_id) REFERENCES cloud_software(id) ON DELETE CASCADE
);

-- Software Integration Status table - Track integration health and status
CREATE TABLE IF NOT EXISTS software_integration_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    software_id INTEGER NOT NULL,
    check_type TEXT NOT NULL, -- 'health_check', 'auth_test', 'rate_limit_check', 'feature_test'
    status TEXT CHECK (status IN ('pass', 'fail', 'warning', 'skip')),
    message TEXT,
    response_time_ms INTEGER,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checked_by TEXT, -- 'system' or user ID
    details JSON,
    FOREIGN KEY (software_id) REFERENCES cloud_software(id) ON DELETE CASCADE
);

-- Indexes for cloud_software
CREATE INDEX IF NOT EXISTS idx_cloud_software_name ON cloud_software(software_name);
CREATE INDEX IF NOT EXISTS idx_cloud_software_category ON cloud_software(category);
CREATE INDEX IF NOT EXISTS idx_cloud_software_status ON cloud_software(status);
CREATE INDEX IF NOT EXISTS idx_cloud_software_integration_type ON cloud_software(integration_type);
CREATE INDEX IF NOT EXISTS idx_cloud_software_installation ON cloud_software(installation_status);
CREATE INDEX IF NOT EXISTS idx_cloud_software_health ON cloud_software(health_status);

-- Indexes for software_usage_logs
CREATE INDEX IF NOT EXISTS idx_software_usage_software_id ON software_usage_logs(software_id);
CREATE INDEX IF NOT EXISTS idx_software_usage_type ON software_usage_logs(usage_type);
CREATE INDEX IF NOT EXISTS idx_software_usage_timestamp ON software_usage_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_software_usage_status ON software_usage_logs(status);
CREATE INDEX IF NOT EXISTS idx_software_usage_user ON software_usage_logs(user_id);

-- Indexes for software_integration_status
CREATE INDEX IF NOT EXISTS idx_software_integration_software_id ON software_integration_status(software_id);
CREATE INDEX IF NOT EXISTS idx_software_integration_type ON software_integration_status(check_type);
CREATE INDEX IF NOT EXISTS idx_software_integration_status ON software_integration_status(status);
CREATE INDEX IF NOT EXISTS idx_software_integration_checked ON software_integration_status(checked_at);

-- Insert the cloud software products mentioned by the user
INSERT OR REPLACE INTO cloud_software (
    software_name, display_name, category, provider, status, integration_type, 
    authentication_method, capabilities, license_type, created_by, notes
) VALUES 
    ('lingo_blaster', 'Lingo Blaster', 'automation', 'Lingo Blaster Inc', 'active', 'rpa', 'username_password', 
     '["language_processing", "content_translation", "multilingual_support"]', 'subscription', 'system', 'Language processing and translation tool'),
    
    ('captionizer', 'Captionizer', 'video_editing', 'Captionizer Pro', 'active', 'api', 'api_key', 
     '["subtitle_generation", "caption_creation", "video_processing"]', 'subscription', 'system', 'Automated caption and subtitle generation'),
    
    ('thumbnail_blaster', 'Thumbnail Blaster', 'thumbnail_creation', 'Thumbnail Blaster', 'active', 'rpa', 'username_password', 
     '["thumbnail_creation", "image_editing", "template_processing"]', 'subscription', 'system', 'Automated thumbnail creation and editing'),
    
    ('speechelo', 'Speechelo', 'voice_generation', 'Speechelo', 'active', 'rpa', 'username_password', 
     '["text_to_speech", "voice_synthesis", "audio_generation"]', 'one_time', 'system', 'Text-to-speech voice generation software'),
    
    ('voice_generator', 'Voice Generator', 'voice_generation', 'Voice Generator Pro', 'active', 'api', 'api_key', 
     '["voice_synthesis", "custom_voices", "audio_processing"]', 'subscription', 'system', 'Advanced voice generation and synthesis'),
    
    ('background_music', 'Background Music', 'background_music', 'Music Library Pro', 'active', 'api', 'api_key', 
     '["music_library", "royalty_free_music", "audio_mixing"]', 'subscription', 'system', 'Royalty-free background music library'),
    
    ('voiceover_cash_machine', 'Voiceover Cash Machine', 'bonus_tools', 'Voiceover Cash Machine', 'active', 'manual', 'none', 
     '["voiceover_training", "business_strategies", "monetization"]', 'one_time', 'system', 'BONUS: Voiceover business training and strategies'),
    
    ('training', 'Training', 'training', 'Training Academy', 'active', 'manual', 'none', 
     '["video_training", "tutorials", "skill_development"]', 'subscription', 'system', 'Comprehensive training modules and tutorials'),
    
    ('scriptelo', 'Scriptelo', 'script_writing', 'Scriptelo', 'active', 'rpa', 'username_password', 
     '["script_generation", "content_writing", "template_processing"]', 'subscription', 'system', 'Automated script writing and content generation');

-- ============================================================================
-- SOVEREIGN AUDIENCE & GROWTH ENGINE - CRM FOUNDATION
-- ============================================================================

-- Contacts table - Core CRM for audience management
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT GENERATED ALWAYS AS (COALESCE(first_name || ' ' || last_name, first_name, last_name, email)) STORED,
    phone TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'unsubscribed', 'bounced', 'complained', 'pending')),
    source TEXT, -- 'google_form', 'manual', 'import', 'api'
    tags JSON, -- Array of tags for segmentation
    custom_fields JSON, -- Flexible custom data storage
    lead_score INTEGER DEFAULT 0,
    lifecycle_stage TEXT DEFAULT 'subscriber' CHECK (lifecycle_stage IN ('subscriber', 'lead', 'customer', 'evangelist')),
    last_engagement_at TIMESTAMP,
    subscription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unsubscribe_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    timezone TEXT DEFAULT 'UTC',
    language TEXT DEFAULT 'en',
    metadata JSON -- Additional tracking data
);

-- Contact Events table - Track all interactions and behaviors
CREATE TABLE IF NOT EXISTS contact_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    event_type TEXT NOT NULL, -- 'email_sent', 'email_opened', 'email_clicked', 'form_submitted', 'page_visited', 'purchase', 'unsubscribe'
    event_data JSON, -- Flexible event-specific data
    email_campaign_id TEXT, -- Reference to email campaign if applicable
    url TEXT, -- URL clicked or page visited
    user_agent TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    utm_term TEXT,
    metadata JSON,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
);

-- Email Campaigns table - Track email marketing campaigns
CREATE TABLE IF NOT EXISTS email_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    content_html TEXT,
    content_text TEXT,
    sender_name TEXT,
    sender_email TEXT,
    reply_to TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'sending', 'sent', 'paused', 'cancelled')),
    campaign_type TEXT DEFAULT 'broadcast' CHECK (campaign_type IN ('broadcast', 'automation', 'welcome_series', 'nurture')),
    segment_criteria JSON, -- SQL-like criteria for audience segmentation
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    total_recipients INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    unsubscribed_count INTEGER DEFAULT 0,
    bounced_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    tags JSON,
    metadata JSON
);

-- Automation Workflows table - Define marketing automation sequences
CREATE TABLE IF NOT EXISTS automation_workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    trigger_type TEXT NOT NULL, -- 'new_subscriber', 'tag_added', 'event_occurred', 'date_based'
    trigger_criteria JSON, -- Specific trigger conditions
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
    workflow_steps JSON, -- Array of workflow steps and actions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    last_triggered_at TIMESTAMP,
    total_triggered INTEGER DEFAULT 0,
    metadata JSON
);

-- Workflow Executions table - Track individual workflow runs
CREATE TABLE IF NOT EXISTS workflow_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT UNIQUE NOT NULL,
    workflow_id TEXT NOT NULL,
    contact_id INTEGER NOT NULL,
    current_step INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'failed')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    next_action_at TIMESTAMP,
    execution_data JSON, -- Step-specific data and variables
    error_message TEXT,
    metadata JSON,
    FOREIGN KEY (workflow_id) REFERENCES automation_workflows(workflow_id),
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
);

-- Audience Segments table - Define audience segments for targeted campaigns
CREATE TABLE IF NOT EXISTS audience_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    criteria JSON NOT NULL, -- SQL-like criteria for segment definition
    contact_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    segment_type TEXT DEFAULT 'dynamic' CHECK (segment_type IN ('static', 'dynamic')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    last_calculated_at TIMESTAMP,
    tags JSON,
    metadata JSON
);

-- Segment Memberships table - Track which contacts belong to which segments
CREATE TABLE IF NOT EXISTS segment_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id TEXT NOT NULL,
    contact_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by TEXT, -- 'system' for dynamic segments, user ID for manual additions
    metadata JSON,
    FOREIGN KEY (segment_id) REFERENCES audience_segments(segment_id),
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
    UNIQUE(segment_id, contact_id)
);

-- CRM Indexes for optimal performance
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status);
CREATE INDEX IF NOT EXISTS idx_contacts_lifecycle_stage ON contacts(lifecycle_stage);
CREATE INDEX IF NOT EXISTS idx_contacts_last_engagement ON contacts(last_engagement_at);
CREATE INDEX IF NOT EXISTS idx_contacts_subscription_date ON contacts(subscription_date);
CREATE INDEX IF NOT EXISTS idx_contacts_source ON contacts(source);

CREATE INDEX IF NOT EXISTS idx_contact_events_contact_id ON contact_events(contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_events_type ON contact_events(event_type);
CREATE INDEX IF NOT EXISTS idx_contact_events_timestamp ON contact_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_contact_events_campaign_id ON contact_events(email_campaign_id);
CREATE INDEX IF NOT EXISTS idx_contact_events_session ON contact_events(session_id);

CREATE INDEX IF NOT EXISTS idx_email_campaigns_status ON email_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_email_campaigns_type ON email_campaigns(campaign_type);
CREATE INDEX IF NOT EXISTS idx_email_campaigns_scheduled ON email_campaigns(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_email_campaigns_sent ON email_campaigns(sent_at);

CREATE INDEX IF NOT EXISTS idx_automation_workflows_status ON automation_workflows(status);
CREATE INDEX IF NOT EXISTS idx_automation_workflows_trigger ON automation_workflows(trigger_type);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_contact ON workflow_executions(contact_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_next_action ON workflow_executions(next_action_at);

CREATE INDEX IF NOT EXISTS idx_audience_segments_segment_id ON audience_segments(segment_id);
CREATE INDEX IF NOT EXISTS idx_audience_segments_status ON audience_segments(status);
CREATE INDEX IF NOT EXISTS idx_audience_segments_type ON audience_segments(segment_type);
CREATE INDEX IF NOT EXISTS idx_audience_segments_created ON audience_segments(created_at);

CREATE INDEX IF NOT EXISTS idx_segment_memberships_segment ON segment_memberships(segment_id);
CREATE INDEX IF NOT EXISTS idx_segment_memberships_contact ON segment_memberships(contact_id);
CREATE INDEX IF NOT EXISTS idx_segment_memberships_added ON segment_memberships(added_at);

INSERT OR REPLACE INTO schema_metadata (version, description, checksum) 
VALUES ('1.0.0', 'Initial TRAE.AI master database schema', 'sha256:placeholder_checksum');

-- Final status message
SELECT 'TRAE.AI Master Database Schema v1.0.0 successfully created!' as status;