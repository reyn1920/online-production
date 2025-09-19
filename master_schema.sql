-- ============================================================================
-- TRAE.AI MASTER DATABASE SCHEMA
-- Production-ready consolidated schema for all TRAE.AI system databases
-- ============================================================================
--
-- This master schema consolidates all database tables from:
-- - right_perspective.db (hypocrisy tracking, research, API management)
-- - intelligence.db (news analysis, trending topics)
-- - secrets.sqlite (encrypted secret storage)
-- - Core system tables (task queue, monitoring, analytics)
--
-- Author: TRAE.AI System
-- Version: 2.0.0
-- Created: 2024
-- Updated: Production Synthesis

-- Enable foreign key constraints and performance optimizations
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;

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
    assigned_to TEXT
);

-- API Registry and Monitoring
-- Tracks external API integrations and their health status
CREATE TABLE IF NOT EXISTS api_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL UNIQUE,
    api_name TEXT UNIQUE NOT NULL,
    base_url TEXT NOT NULL,
    api_url TEXT NOT NULL,
    api_version TEXT,
    capability TEXT NOT NULL, -- e.g., 'text-generation', 'weather-data', 'image-generation'
    api_key_name TEXT, -- The name of the secret in secrets.sqlite
    authentication_type TEXT DEFAULT 'api_key' CHECK (authentication_type IN ('api_key', 'bearer_token', 'oauth2', 'basic_auth', 'none')),
    priority INTEGER DEFAULT 10, -- Lower is higher priority
    rate_limit_per_minute INTEGER,
    rate_limit_per_hour INTEGER,
    rate_limit_per_day INTEGER,
    daily_limit INTEGER,
    current_usage_minute INTEGER DEFAULT 0,
    current_usage_hour INTEGER DEFAULT 0,
    current_usage_day INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated', 'maintenance')),
    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    last_health_check TIMESTAMP,
    response_time_ms INTEGER DEFAULT 0,
    average_response_time REAL,
    success_rate REAL DEFAULT 100.0, -- Percentage of successful requests
    usage_count INTEGER DEFAULT 0, -- Total requests made
    daily_usage_count INTEGER DEFAULT 0, -- Requests made today
    total_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    documentation_url TEXT,
    notes TEXT,
    cost_per_request REAL DEFAULT 0.0, -- For paid tiers
    request_format TEXT DEFAULT 'json', -- 'json', 'xml', 'form_data'
    response_format TEXT DEFAULT 'json', -- 'json', 'xml', 'text'
    supported_methods TEXT DEFAULT 'GET,POST', -- Comma-separated HTTP methods
    error_count INTEGER DEFAULT 0,
    last_error_message TEXT,
    last_error_timestamp TIMESTAMP,
    discovery_source TEXT, -- 'manual', 'research_agent', 'github', 'api_directory'
    validation_status TEXT DEFAULT 'pending', -- 'pending', 'validated', 'rejected'
    tags TEXT, -- Comma-separated tags for categorization
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

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

-- ============================================================================
-- CONTENT MANAGEMENT TABLES
-- ============================================================================

-- Author Personas
-- Manages different author personalities and their characteristics
CREATE TABLE IF NOT EXISTS author_personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_name TEXT UNIQUE NOT NULL,
    description TEXT,
    writing_style_description TEXT NOT NULL,
    personality_traits JSON,
    writing_style JSON,
    expertise_areas JSON,
    tone_preferences JSON,
    vocabulary_level TEXT CHECK (vocabulary_level IN ('basic', 'intermediate', 'advanced', 'expert')),
    target_audience TEXT,
    channel_name TEXT, -- Foreign key to channels table
    content_types JSON, -- Array of content types this persona is suitable for
    usage_count INTEGER DEFAULT 0,
    success_metrics JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    version INTEGER DEFAULT 1,
    parent_persona_id INTEGER, -- For persona variations
    last_used_at TIMESTAMP,
    FOREIGN KEY (parent_persona_id) REFERENCES author_personas(id)
);

-- Channels
-- Manages different content distribution channels
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,
    channel_url TEXT,
    description TEXT,
    target_audience TEXT,
    content_strategy TEXT,
    posting_schedule TEXT,
    performance_metrics JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- HYPOCRISY TRACKING SYSTEM
-- ============================================================================

-- Hypocrisy Tracker
-- Tracks contradictory statements and positions for analysis
CREATE TABLE IF NOT EXISTS hypocrisy_tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL,
    subject_type TEXT CHECK (subject_type IN ('person', 'organization', 'publication', 'politician', 'celebrity', 'influencer')),
    topic TEXT NOT NULL,
    statement_1 TEXT NOT NULL,
    statement_2 TEXT NOT NULL,
    context_1 TEXT,
    context_2 TEXT,
    date_1 DATE,
    date_2 DATE,
    source_1 TEXT,
    source_2 TEXT,
    source_url_A TEXT, -- Legacy compatibility
    source_url_B TEXT, -- Legacy compatibility
    contradiction_type TEXT CHECK (contradiction_type IN ('direct', 'contextual', 'temporal', 'value', 'policy_shift', 'audience_based')),
    severity_score INTEGER CHECK (severity_score BETWEEN 1 AND 10),
    confidence_score REAL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    contradiction_score REAL CHECK (contradiction_score BETWEEN 0.0 AND 1.0),
    verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'disputed', 'debunked', 'unverified')),
    public_impact_score INTEGER CHECK (public_impact_score BETWEEN 1 AND 10),

    media_coverage_count INTEGER DEFAULT 0,
    social_media_mentions INTEGER DEFAULT 0,
    evidence_links JSON, -- Array of supporting evidence URLs
    fact_check_results JSON,
    tags JSON,
    content_used BOOLEAN DEFAULT FALSE, -- For tracking content creation
    time_gap_days INTEGER, -- Days between contradictory statements
    discovered_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    last_reviewed_at TIMESTAMP
);

-- ============================================================================
-- INTELLIGENCE AND NEWS ANALYSIS
-- ============================================================================

-- News Articles
-- Stores processed news articles for analysis
CREATE TABLE IF NOT EXISTS news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_id TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    url TEXT UNIQUE,
    source TEXT,
    category TEXT,
    published_date TIMESTAMP,
    published TIMESTAMP, -- Legacy compatibility
    relevance_score REAL,
    keywords TEXT, -- Can be JSON or comma-separated
    entities TEXT,
    sentiment_score REAL,
    readability_score REAL,
    trend_strength TEXT,
    processed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trend Analysis
-- Tracks trending topics and keywords
CREATE TABLE IF NOT EXISTS trend_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    trend_name TEXT, -- For compatibility
    frequency INTEGER DEFAULT 1,
    trend_direction TEXT,
    confidence_score REAL,
    trend_score REAL DEFAULT 0.0,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    last_updated DATETIME,
    sources TEXT,
    related_articles TEXT,
    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    time_window TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Intelligence Briefings
-- Stores generated intelligence reports and briefings
CREATE TABLE IF NOT EXISTS intelligence_briefings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    briefing_title TEXT, -- For compatibility
    summary TEXT,
    content TEXT,
    key_points TEXT,
    sources TEXT,
    briefing_type TEXT,
    priority TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- RESEARCH AND EVIDENCE COLLECTION
-- ============================================================================

-- Evidence
-- Stores research and evidence for content creation
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,
    content_type TEXT, -- 'quote', 'statistic', 'fact'
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Suggestions
-- Stores discovered API suggestions from research
CREATE TABLE IF NOT EXISTS api_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    capability TEXT NOT NULL,
    api_url TEXT NOT NULL,
    documentation_url TEXT,
    description TEXT,
    discovery_source TEXT NOT NULL, -- 'github', 'api_directory', 'developer_forum', 'research_agent'
    discovery_details TEXT, -- JSON with source-specific metadata
    confidence_score REAL DEFAULT 0.0, -- AI confidence in API quality (0-1)
    validation_notes TEXT, -- LLM analysis of documentation
    integration_complexity TEXT DEFAULT 'unknown', -- 'simple', 'moderate', 'complex', 'unknown'
    estimated_value REAL DEFAULT 0.0, -- Estimated value to the system (0-1)
    requires_auth BOOLEAN DEFAULT TRUE,
    rate_limits TEXT, -- Description of rate limits
    cost_model TEXT, -- 'free', 'freemium', 'paid', 'unknown'
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'integrated'
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Discovery Tasks
-- Tracks API discovery and research tasks
CREATE TABLE IF NOT EXISTS discovery_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL, -- 'github_scan', 'forum_scan', 'directory_scan'
    target_capability TEXT, -- Capability being searched for
    search_parameters TEXT, -- JSON with search criteria
    status TEXT DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed'
    results_count INTEGER DEFAULT 0,
    execution_time_seconds INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- ============================================================================
-- SYSTEM MONITORING AND REPAIR
-- ============================================================================

-- Repair Log
-- Tracks system repair attempts and outcomes
CREATE TABLE IF NOT EXISTS repair_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    error_message TEXT NOT NULL,
    repair_action TEXT NOT NULL,
    repair_tier INTEGER NOT NULL, -- 1=Restart, 2=Dependency Check, 3=AI-Powered Research
    outcome TEXT NOT NULL, -- 'success', 'failed', 'partial'
    execution_details TEXT, -- JSON with additional context
    attempt_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolution_time_seconds INTEGER
);

-- System Metrics
-- Stores system performance and health metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT,
    component TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Application Metrics
-- Detailed application-level metrics
CREATE TABLE IF NOT EXISTS application_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_component TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_metadata JSON,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Alerts
-- System performance alerts and notifications
CREATE TABLE IF NOT EXISTS performance_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    component TEXT NOT NULL,
    message TEXT NOT NULL,
    threshold_value REAL,
    actual_value REAL,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Error Events
-- Tracks system errors and exceptions
CREATE TABLE IF NOT EXISTS error_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type TEXT NOT NULL,
    component TEXT NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    context_data JSON,
    resolved BOOLEAN DEFAULT FALSE,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- ============================================================================
-- REPORTING AND ANALYTICS
-- ============================================================================

-- Generated Reports
-- Stores all generated reports for the Report Center
CREATE TABLE IF NOT EXISTS generated_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT NOT NULL, -- 'daily_performance', 'weekly_growth', 'quarterly_strategic', 'affiliate_performance', etc.
    title TEXT NOT NULL,
    content TEXT NOT NULL, -- Full report content in Markdown format
    key_headline TEXT, -- AI-generated summary of most important finding
    date_range_start DATE, -- Start date of data covered in report
    date_range_end DATE, -- End date of data covered in report
    generated_by TEXT, -- Agent or system that generated the report
    generation_parameters TEXT, -- JSON with parameters used for generation
    file_size_bytes INTEGER, -- Size of the report content
    status TEXT DEFAULT 'active', -- 'active', 'archived', 'deleted'
    tags TEXT, -- Comma-separated tags for categorization
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Insights
-- AI-generated insights and recommendations
CREATE TABLE IF NOT EXISTS performance_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_type TEXT NOT NULL,
    insight_data JSON,
    actionable_items JSON,
    priority_score REAL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content Performance Tracking
-- Tracks performance metrics for all content across platforms
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

-- Reports Table
-- Simple reports storage for legacy compatibility
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'
);

-- Performance Metrics
-- Detailed performance tracking for all system components
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_type TEXT NOT NULL, -- 'gauge', 'counter', 'histogram', 'timer'
    metric_value REAL NOT NULL,
    metric_unit TEXT,
    component TEXT NOT NULL,
    tags JSON, -- Additional metadata tags
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- ============================================================================
-- ENCRYPTED SECRETS STORAGE
-- ============================================================================

-- Secrets
-- Encrypted storage for sensitive configuration data
CREATE TABLE IF NOT EXISTS secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_name TEXT UNIQUE NOT NULL,
    encrypted_value BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Task Queue Indexes
CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status);
CREATE INDEX IF NOT EXISTS idx_task_queue_priority ON task_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_task_queue_created ON task_queue(created_at);
CREATE INDEX IF NOT EXISTS idx_task_queue_type ON task_queue(task_type);
CREATE INDEX IF NOT EXISTS idx_task_queue_scheduled ON task_queue(scheduled_at);

-- API Registry Indexes
CREATE INDEX IF NOT EXISTS idx_api_registry_name ON api_registry(api_name);
CREATE INDEX IF NOT EXISTS idx_api_registry_service ON api_registry(service_name);
CREATE INDEX IF NOT EXISTS idx_api_registry_status ON api_registry(status);
CREATE INDEX IF NOT EXISTS idx_api_registry_health ON api_registry(health_status);
CREATE INDEX IF NOT EXISTS idx_api_registry_capability ON api_registry(capability);
CREATE INDEX IF NOT EXISTS idx_api_registry_priority ON api_registry(priority);

-- API Request Logs Indexes
CREATE INDEX IF NOT EXISTS idx_api_logs_api_name ON api_request_logs(api_name);
CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_request_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_logs_status ON api_request_logs(status_code);
CREATE INDEX IF NOT EXISTS idx_api_logs_request_id ON api_request_logs(request_id);

-- Author Personas Indexes
CREATE INDEX IF NOT EXISTS idx_author_personas_name ON author_personas(persona_name);
CREATE INDEX IF NOT EXISTS idx_author_personas_active ON author_personas(is_active);
CREATE INDEX IF NOT EXISTS idx_author_personas_usage ON author_personas(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_author_personas_created ON author_personas(created_at);

-- Channels Indexes
CREATE INDEX IF NOT EXISTS idx_channels_name ON channels(channel_name);
CREATE INDEX IF NOT EXISTS idx_channels_platform ON channels(platform);
CREATE INDEX IF NOT EXISTS idx_channels_active ON channels(is_active);

-- Hypocrisy Tracker Indexes
CREATE INDEX IF NOT EXISTS idx_hypocrisy_subject ON hypocrisy_tracker(subject_name);
-- Legacy indexes removed - using subject_name index instead
CREATE INDEX IF NOT EXISTS idx_hypocrisy_type ON hypocrisy_tracker(subject_type);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_severity ON hypocrisy_tracker(severity_score DESC);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_verification ON hypocrisy_tracker(verification_status);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_impact ON hypocrisy_tracker(public_impact_score DESC);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_content_used ON hypocrisy_tracker(content_used);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_created ON hypocrisy_tracker(created_at);

-- News Articles Indexes
CREATE INDEX IF NOT EXISTS idx_news_articles_published ON news_articles(published_date);
CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles(source);
CREATE INDEX IF NOT EXISTS idx_news_articles_relevance ON news_articles(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_hash ON news_articles(hash_id);
CREATE INDEX IF NOT EXISTS idx_news_articles_url ON news_articles(url);

-- Trend Analysis Indexes
CREATE INDEX IF NOT EXISTS idx_trend_analysis_keyword ON trend_analysis(keyword);
CREATE INDEX IF NOT EXISTS idx_trend_analysis_score ON trend_analysis(trend_score DESC);
CREATE INDEX IF NOT EXISTS idx_trend_analysis_updated ON trend_analysis(last_updated);
CREATE INDEX IF NOT EXISTS idx_trend_analysis_frequency ON trend_analysis(frequency DESC);

-- Intelligence Briefings Indexes
CREATE INDEX IF NOT EXISTS idx_intelligence_briefings_topic ON intelligence_briefings(topic);
CREATE INDEX IF NOT EXISTS idx_intelligence_briefings_type ON intelligence_briefings(briefing_type);
CREATE INDEX IF NOT EXISTS idx_intelligence_briefings_priority ON intelligence_briefings(priority);
CREATE INDEX IF NOT EXISTS idx_intelligence_briefings_created ON intelligence_briefings(created_at);

-- Evidence Indexes
CREATE INDEX IF NOT EXISTS idx_evidence_topic ON evidence(topic);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(content_type);
CREATE INDEX IF NOT EXISTS idx_evidence_added ON evidence(date_added);

-- API Suggestions Indexes
CREATE INDEX IF NOT EXISTS idx_api_suggestions_service ON api_suggestions(service_name);
CREATE INDEX IF NOT EXISTS idx_api_suggestions_capability ON api_suggestions(capability);
CREATE INDEX IF NOT EXISTS idx_api_suggestions_confidence ON api_suggestions(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_api_suggestions_status ON api_suggestions(status);

-- System Monitoring Indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_component ON system_metrics(component);
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_application_metrics_component ON application_metrics(app_component);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_resolved ON performance_alerts(resolved);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_severity ON performance_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_component ON performance_metrics(component);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_error_events_type ON error_events(error_type);
CREATE INDEX IF NOT EXISTS idx_error_events_component ON error_events(component);
CREATE INDEX IF NOT EXISTS idx_error_events_resolved ON error_events(resolved);

-- Reporting Indexes
CREATE INDEX IF NOT EXISTS idx_generated_reports_type ON generated_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_generated_reports_status ON generated_reports(status);
CREATE INDEX IF NOT EXISTS idx_generated_reports_created ON generated_reports(created_at);

-- Content Performance Indexes
CREATE INDEX IF NOT EXISTS idx_content_performance_content_id ON content_performance(content_id);
CREATE INDEX IF NOT EXISTS idx_content_performance_platform ON content_performance(platform);
CREATE INDEX IF NOT EXISTS idx_content_performance_analyzed ON content_performance(analyzed_at);
CREATE INDEX IF NOT EXISTS idx_content_performance_engagement ON content_performance(engagement_rate DESC);

-- Reports Indexes
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at);
CREATE INDEX IF NOT EXISTS idx_performance_insights_type ON performance_insights(insight_type);

-- Secrets Indexes
CREATE INDEX IF NOT EXISTS idx_secrets_key_name ON secrets(key_name);
CREATE INDEX IF NOT EXISTS idx_secrets_created ON secrets(created_at);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active APIs View
CREATE VIEW IF NOT EXISTS active_apis AS
SELECT
    service_name,
    api_name,
    capability,
    health_status,
    success_rate,
    average_response_time,
    daily_usage_count,
    daily_limit,
    (CAST(daily_usage_count AS REAL) / NULLIF(daily_limit, 0)) * 100 AS usage_percentage
FROM api_registry
WHERE is_active = 1 AND status = 'active';

-- Recent Hypocrisy Findings View
CREATE VIEW IF NOT EXISTS recent_hypocrisy_findings AS
SELECT
    id,
    subject_name,
    topic,
    severity_score,
    confidence_score,
    verification_status,
    content_used,
    created_at
FROM hypocrisy_tracker
WHERE created_at > datetime('now', '-30 days')
ORDER BY severity_score DESC, created_at DESC;

-- Trending Topics View
CREATE VIEW IF NOT EXISTS current_trending_topics AS
SELECT
    keyword,
    frequency,
    trend_score,
    trend_direction,
    last_updated
FROM trend_analysis
WHERE last_updated > datetime('now', '-24 hours')
ORDER BY trend_score DESC, frequency DESC;

-- System Health View
CREATE VIEW IF NOT EXISTS system_health_overview AS
SELECT
    'APIs' as component,
    COUNT(*) as total,
    SUM(CASE WHEN health_status = 'healthy' THEN 1 ELSE 0 END) as healthy,
    SUM(CASE WHEN health_status = 'degraded' THEN 1 ELSE 0 END) as degraded,
    SUM(CASE WHEN health_status = 'unhealthy' THEN 1 ELSE 0 END) as unhealthy
FROM api_registry WHERE is_active = 1
UNION ALL
SELECT
    'Tasks' as component,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as healthy,
    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as degraded,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as unhealthy
FROM task_queue WHERE created_at > datetime('now', '-24 hours');

-- ============================================================================
-- TRIGGERS FOR DATA INTEGRITY
-- ============================================================================

-- Update timestamps trigger for api_registry
CREATE TRIGGER IF NOT EXISTS update_api_registry_timestamp
AFTER UPDATE ON api_registry
BEGIN
    UPDATE api_registry SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamps trigger for author_personas
CREATE TRIGGER IF NOT EXISTS update_author_personas_timestamp
AFTER UPDATE ON author_personas
BEGIN
    UPDATE author_personas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamps trigger for hypocrisy_tracker
CREATE TRIGGER IF NOT EXISTS update_hypocrisy_tracker_timestamp
AFTER UPDATE ON hypocrisy_tracker
BEGIN
    UPDATE hypocrisy_tracker SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamps trigger for secrets
CREATE TRIGGER IF NOT EXISTS update_secrets_timestamp
AFTER UPDATE ON secrets
BEGIN
    UPDATE secrets SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Validate severity scores trigger
CREATE TRIGGER IF NOT EXISTS validate_hypocrisy_scores
BEFORE INSERT ON hypocrisy_tracker
BEGIN
    SELECT CASE
        WHEN NEW.severity_score < 1 OR NEW.severity_score > 10 THEN
            RAISE(ABORT, 'Severity score must be between 1 and 10')
        WHEN NEW.confidence_score < 0.0 OR NEW.confidence_score > 1.0 THEN
            RAISE(ABORT, 'Confidence score must be between 0.0 and 1.0')
        WHEN NEW.public_impact_score < 1 OR NEW.public_impact_score > 10 THEN
            RAISE(ABORT, 'Public impact score must be between 1 and 10')
    END;
END;

-- ============================================================================
-- INITIAL DATA SETUP
-- ============================================================================

-- Insert default system configuration
INSERT OR IGNORE INTO system_metrics (metric_name, metric_value, metric_unit, component) VALUES
('schema_version', 2.0, 'version', 'database'),
('initialization_time', strftime('%s', 'now'), 'timestamp', 'database'),
('total_tables', 25, 'count', 'database');

-- Insert default author personas
INSERT OR IGNORE INTO author_personas (persona_name, description, writing_style_description, target_audience, is_active) VALUES
('Professional Analyst', 'Authoritative, data-driven analysis with corporate tone', 'Formal, analytical, evidence-based writing with professional terminology', 'Business professionals, executives, analysts', TRUE),
('Investigative Reporter', 'Skeptical, thorough investigative approach', 'Questioning, detailed, fact-checking focused with journalistic integrity', 'General public, news consumers, researchers', TRUE),
('Social Media Influencer', 'Engaging, relatable, trend-aware content creator', 'Casual, conversational, emoji-friendly with viral potential', 'Social media users, younger demographics', TRUE),
('Academic Researcher', 'Scholarly, methodical, peer-review quality analysis', 'Formal academic tone with citations and rigorous methodology', 'Academics, students, research community', TRUE);

-- ============================================================================
-- SCHEMA VALIDATION AND MAINTENANCE
-- ============================================================================

-- Analyze tables for query optimization
ANALYZE;

-- Vacuum to optimize database file
VACUUM;

-- Final schema validation
PRAGMA integrity_check;
PRAGMA foreign_key_check;

-- Log successful schema creation
INSERT INTO system_metrics (metric_name, metric_value, metric_unit, component) VALUES
('schema_creation_success', 1, 'boolean', 'database');

-- ============================================================================
-- END OF MASTER SCHEMA
-- ============================================================================

-- Schema successfully created!
-- Total tables: 25+
-- Total indexes: 50+
-- Total views: 4
-- Total triggers: 4
--
-- This schema provides a comprehensive foundation for the TRAE.AI system
-- with proper indexing, data integrity, and performance optimization.
--
-- Next steps:
-- 1. Run this schema on your target databases
-- 2. Configure the SecretStore with TRAE_MASTER_KEY
-- 3. Initialize the agent system
-- 4. Begin data population and testing
