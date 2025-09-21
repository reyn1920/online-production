-- ============================================================================
-- TRAE.AI Master Database Schema
-- Version: 1.0.0
-- Description: Comprehensive database schema for TRAE.AI system
-- ============================================================================

-- ============================================================================
-- CORE SYSTEM TABLES
-- ============================================================================

-- Task Queue Management
-- Handles asynchronous task processing and job scheduling
CREATE TABLE IF NOT EXISTS task_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    task_type TEXT NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    payload JSON,
    result JSON,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_by TEXT,
    assigned_to TEXT
);

-- Indexes for task_queue
CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status);
CREATE INDEX IF NOT EXISTS idx_task_queue_priority ON task_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_task_queue_created ON task_queue(created_at);
CREATE INDEX IF NOT EXISTS idx_task_queue_scheduled ON task_queue(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_task_queue_type ON task_queue(task_type);

-- API Registry and Monitoring
-- Tracks external API integrations and their health status
CREATE TABLE IF NOT EXISTS api_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT UNIQUE NOT NULL,
    base_url TEXT NOT NULL,
    api_version TEXT,
    authentication_type TEXT CHECK (authentication_type IN ('api_key', 'bearer_token', 'oauth2', 'basic_auth', 'none')),
    rate_limit_per_minute INTEGER,
    rate_limit_per_hour INTEGER,
    rate_limit_per_day INTEGER,
    current_usage_minute INTEGER DEFAULT 0,
    current_usage_hour INTEGER DEFAULT 0,
    current_usage_day INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated', 'maintenance')),
    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    last_health_check TIMESTAMP,
    success_rate REAL DEFAULT 100.0,
    average_response_time REAL,
    total_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Indexes for api_registry
CREATE INDEX IF NOT EXISTS idx_api_registry_name ON api_registry(api_name);
CREATE INDEX IF NOT EXISTS idx_api_registry_status ON api_registry(status);
CREATE INDEX IF NOT EXISTS idx_api_registry_health ON api_registry(health_status);

-- API Request Logs
-- Detailed logging of all API requests for monitoring and debugging
CREATE TABLE IF NOT EXISTS api_request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    request_id TEXT,
    status_code INTEGER,
    response_time_ms REAL,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address TEXT,
    request_headers JSON,
    response_headers JSON,
    FOREIGN KEY (api_name) REFERENCES api_registry(api_name) ON DELETE CASCADE
);

-- Indexes for api_request_logs
CREATE INDEX IF NOT EXISTS idx_api_logs_api_name ON api_request_logs(api_name);
CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_request_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_logs_status ON api_request_logs(status_code);
CREATE INDEX IF NOT EXISTS idx_api_logs_request_id ON api_request_logs(request_id);

-- ============================================================================
-- CONTENT MANAGEMENT TABLES
-- ============================================================================

-- Author Personas
-- Manages different author personalities and their characteristics
CREATE TABLE IF NOT EXISTS author_personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_name TEXT UNIQUE NOT NULL,
    description TEXT,
    personality_traits JSON,
    writing_style JSON,
    expertise_areas JSON,
    tone_preferences JSON,
    vocabulary_level TEXT CHECK (vocabulary_level IN ('basic', 'intermediate', 'advanced', 'expert')),
    target_audience TEXT,
    content_types JSON, -- Array of content types this persona is suitable for
    usage_count INTEGER DEFAULT 0,
    success_metrics JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    last_used_at TIMESTAMP
);

-- Indexes for author_personas
CREATE INDEX IF NOT EXISTS idx_author_personas_name ON author_personas(persona_name);
CREATE INDEX IF NOT EXISTS idx_author_personas_active ON author_personas(is_active);
CREATE INDEX IF NOT EXISTS idx_author_personas_usage ON author_personas(usage_count DESC);

-- Hypocrisy Tracker
-- Tracks contradictory statements and positions for consistency analysis
CREATE TABLE IF NOT EXISTS hypocrisy_tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL, -- Person, organization, or brand being tracked
    subject_type TEXT CHECK (subject_type IN ('person', 'organization', 'publication', 'politician', 'celebrity', 'influencer')),
    statement_1 TEXT NOT NULL,
    statement_2 TEXT NOT NULL,
    contradiction_type TEXT CHECK (contradiction_type IN ('direct', 'contextual', 'temporal', 'value', 'policy_shift', 'audience_based')),
    severity_score INTEGER CHECK (severity_score BETWEEN 1 AND 10),
    context_1 TEXT,
    context_2 TEXT,
    date_1 DATE,
    date_2 DATE,
    source_1 TEXT,
    source_2 TEXT,
    evidence_links JSON,
    verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'disputed', 'debunked')),
    public_impact_score INTEGER CHECK (public_impact_score BETWEEN 1 AND 10),
    media_coverage_count INTEGER DEFAULT 0,
    social_media_mentions INTEGER DEFAULT 0,
    fact_check_results JSON,
    tags JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    last_reviewed_at TIMESTAMP
);

-- Indexes for hypocrisy_tracker
CREATE INDEX IF NOT EXISTS idx_hypocrisy_subject ON hypocrisy_tracker(subject_name);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_type ON hypocrisy_tracker(subject_type);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_severity ON hypocrisy_tracker(severity_score DESC);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_verification ON hypocrisy_tracker(verification_status);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_interest ON hypocrisy_tracker(public_interest_score DESC);

-- ============================================================================
-- MONETIZATION AND AFFILIATE TABLES
-- ============================================================================

-- Affiliate Programs
-- Manages affiliate marketing programs and their details
CREATE TABLE IF NOT EXISTS affiliate_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_name TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    program_url TEXT,
    commission_structure JSON, -- Details about commission rates, tiers, etc.
    cookie_duration_days INTEGER,
    minimum_payout REAL,
    payment_frequency TEXT,
    payment_methods JSON,
    product_categories JSON,
    geographic_restrictions JSON,
    promotional_materials JSON,
    tracking_method TEXT,
    affiliate_id TEXT,
    api_integration JSON,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending', 'suspended', 'terminated')),
    performance_metrics JSON,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    joined_date DATE,
    last_payment_date DATE
);

-- Indexes for affiliate_programs
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_name ON affiliate_programs(program_name);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_company ON affiliate_programs(company_name);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_status ON affiliate_programs(status);

-- Affiliate Transactions
-- Tracks individual affiliate transactions and commissions
CREATE TABLE IF NOT EXISTS affiliate_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,
    transaction_id TEXT UNIQUE,
    order_id TEXT,
    customer_id TEXT,
    product_name TEXT,
    product_category TEXT,
    sale_amount REAL NOT NULL,
    commission_rate REAL NOT NULL,
    commission_amount REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    transaction_date TIMESTAMP NOT NULL,
    conversion_date TIMESTAMP,
    click_date TIMESTAMP,
    referral_source TEXT,
    customer_type TEXT CHECK (customer_type IN ('new', 'returning')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled', 'paid')),
    payment_date DATE,
    payment_reference TEXT,
    notes TEXT,
    metadata JSON,
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
-- Manages different content channels and platforms
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('youtube', 'tiktok', 'instagram', 'twitter', 'linkedin', 'facebook', 'twitch', 'podcast', 'blog', 'newsletter')),
    channel_url TEXT,
    channel_id_external TEXT, -- Platform-specific channel ID
    description TEXT,
    category TEXT,
    subscriber_count INTEGER DEFAULT 0,
    follower_count INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    total_videos INTEGER DEFAULT 0,
    creation_date DATE,
    verification_status BOOLEAN DEFAULT FALSE,
    monetization_enabled BOOLEAN DEFAULT FALSE,
    content_strategy JSON,
    posting_schedule JSON,
    target_demographics JSON,
    performance_goals JSON,
    branding_guidelines JSON,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'archived')),
    api_credentials JSON, -- Encrypted API keys for platform integration
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    managed_by TEXT
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
    video_id_external TEXT NOT NULL, -- Platform-specific video ID
    title TEXT NOT NULL,
    description TEXT,
    thumbnail_url TEXT,
    video_url TEXT,
    duration_seconds INTEGER,
    upload_date TIMESTAMP,
    publish_date TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    dislike_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    engagement_rate REAL, -- Calculated engagement percentage
    watch_time_minutes REAL,
    average_view_duration REAL,
    click_through_rate REAL,
    subscriber_gain INTEGER DEFAULT 0,
    revenue REAL DEFAULT 0.0,
    cpm REAL, -- Cost per mille (thousand views)
    rpm REAL, -- Revenue per mille
    tags JSON,
    categories JSON,
    content_type TEXT,
    video_quality TEXT,
    language TEXT,
    captions_available BOOLEAN DEFAULT FALSE,
    age_restriction BOOLEAN DEFAULT FALSE,
    monetization_status TEXT,
    copyright_claims JSON,
    performance_tier TEXT CHECK (performance_tier IN ('viral', 'high', 'medium', 'low', 'poor')),
    trending_status BOOLEAN DEFAULT FALSE,
    peak_concurrent_viewers INTEGER,
    demographics JSON,
    traffic_sources JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
);

-- Indexes for video_performance
CREATE INDEX IF NOT EXISTS idx_video_perf_channel ON video_performance(channel_id);
CREATE INDEX IF NOT EXISTS idx_video_perf_upload ON video_performance(upload_date);
CREATE INDEX IF NOT EXISTS idx_video_perf_views ON video_performance(view_count DESC);
CREATE INDEX IF NOT EXISTS idx_video_perf_engagement ON video_performance(engagement_rate DESC);
CREATE INDEX IF NOT EXISTS idx_video_perf_revenue ON video_performance(revenue DESC);
CREATE INDEX IF NOT EXISTS idx_video_perf_tier ON video_performance(performance_tier);

-- Video Performance History
-- Tracks historical performance data for trend analysis
CREATE TABLE IF NOT EXISTS video_performance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_performance_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    share_count INTEGER,
    subscriber_gain INTEGER,
    revenue REAL,
    watch_time_minutes REAL,
    engagement_rate REAL,
    ranking_position INTEGER,
    trending_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_performance_id) REFERENCES video_performance(id) ON DELETE CASCADE
);

-- Indexes for video_performance_history
CREATE INDEX IF NOT EXISTS idx_video_hist_video ON video_performance_history(video_performance_id);
CREATE INDEX IF NOT EXISTS idx_video_hist_date ON video_performance_history(snapshot_date);

-- ============================================================================
-- AVATAR AND IDENTITY MANAGEMENT TABLES
-- ============================================================================

-- Avatars
-- Manages AI-generated avatars and their characteristics
CREATE TABLE IF NOT EXISTS avatars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    avatar_name TEXT UNIQUE NOT NULL,
    avatar_type TEXT CHECK (avatar_type IN ('realistic', 'cartoon', 'abstract', 'brand_mascot', 'professional')),
    gender TEXT CHECK (gender IN ('male', 'female', 'non_binary', 'unspecified')),
    age_range TEXT CHECK (age_range IN ('child', 'teen', 'young_adult', 'adult', 'middle_aged', 'senior')),
    ethnicity TEXT,
    physical_description JSON,
    personality_traits JSON,
    voice_characteristics JSON,
    clothing_style JSON,
    background_story TEXT,
    profession TEXT,
    interests JSON,
    social_media_presence JSON,
    content_specialization JSON,
    usage_guidelines TEXT,
    brand_alignment JSON,
    generation_parameters JSON, -- AI model parameters used to create avatar
    image_assets JSON, -- URLs or paths to avatar images
    video_assets JSON, -- URLs or paths to avatar videos
    voice_assets JSON, -- URLs or paths to voice samples
    usage_count INTEGER DEFAULT 0,
    performance_metrics JSON,
    audience_reception JSON,
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    copyright_info TEXT,
    licensing_terms TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    last_used_at TIMESTAMP
);

-- Indexes for avatars
CREATE INDEX IF NOT EXISTS idx_avatars_name ON avatars(avatar_name);
CREATE INDEX IF NOT EXISTS idx_avatars_type ON avatars(avatar_type);
CREATE INDEX IF NOT EXISTS idx_avatars_active ON avatars(is_active);
CREATE INDEX IF NOT EXISTS idx_avatars_usage ON avatars(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_avatars_public ON avatars(is_public);

-- Avatar Usage Log
-- Tracks when and how avatars are used across different content
CREATE TABLE IF NOT EXISTS avatar_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    avatar_id INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    content_id TEXT,
    platform TEXT,
    usage_context TEXT,
    duration_seconds INTEGER,
    performance_metrics JSON,
    audience_feedback JSON,
    usage_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    FOREIGN KEY (avatar_id) REFERENCES avatars(id) ON DELETE CASCADE
);

-- Indexes for avatar_usage_log
CREATE INDEX IF NOT EXISTS idx_avatar_usage_avatar ON avatar_usage_log(avatar_id);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_date ON avatar_usage_log(usage_date);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_content ON avatar_usage_log(content_type);

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
    evidence_type TEXT CHECK (evidence_type IN ('document', 'video', 'audio', 'image', 'website', 'social_media', 'news_article', 'academic_paper', 'government_record', 'legal_document', 'interview', 'testimony', 'data_analysis', 'survey', 'experiment')),
    source_name TEXT NOT NULL,
    source_url TEXT,
    source_type TEXT CHECK (source_type IN ('primary', 'secondary', 'tertiary')),
    author TEXT,
    publication_date DATE,
    access_date DATE,
    language TEXT DEFAULT 'en',
    content_text TEXT,
    content_summary TEXT,
    keywords JSON,
    topics JSON,
    geographic_relevance JSON,
    time_period_start DATE,
    time_period_end DATE,
    source_credibility_score REAL CHECK (source_credibility_score BETWEEN 0.0 AND 10.0),
    bias_indicators JSON,
    methodology_notes TEXT,
    sample_size INTEGER,
    confidence_level REAL,
    statistical_significance REAL,
    peer_reviewed BOOLEAN DEFAULT FALSE,
    replication_studies JSON,
    contradictory_evidence JSON,
    supporting_evidence JSON,
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

-- Indexes for performance_metrics
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type);

INSERT OR REPLACE INTO schema_metadata (version, description, checksum)
VALUES ('1.0.0', 'Initial TRAE.AI master database schema', 'sha256:placeholder_checksum');

-- Final status message
SELECT 'TRAE.AI Master Database Schema v1.0.0 successfully created!' as status;
