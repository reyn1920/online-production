-- Master Schema for TRAE.AI System Database (right_perspective.db)

-- For managing the asynchronous, resilient task queue
CREATE TABLE IF NOT EXISTS task_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    payload TEXT, -- JSON object with details like topic, etc.
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, failed
    retry_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- For managing the 100+ free APIs and their priorities
CREATE TABLE IF NOT EXISTS api_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL UNIQUE,
    capability TEXT NOT NULL, -- e.g., 'text-generation', 'weather-data', 'image-generation'
    api_url TEXT NOT NULL,
    api_key_name TEXT, -- The name of the secret in secrets.sqlite
    priority INTEGER DEFAULT 10, -- Lower is higher priority
    daily_limit INTEGER,
    is_active BOOLEAN DEFAULT 1,
    notes TEXT,
    -- Enhanced scalable foundation columns
    health_status TEXT DEFAULT 'unknown', -- 'healthy', 'degraded', 'unhealthy', 'unknown'
    last_health_check TIMESTAMP,
    response_time_ms INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0, -- Percentage of successful requests
    usage_count INTEGER DEFAULT 0, -- Total requests made
    daily_usage_count INTEGER DEFAULT 0, -- Requests made today
    last_used TIMESTAMP,
    documentation_url TEXT,
    rate_limit_per_hour INTEGER,
    rate_limit_per_day INTEGER,
    cost_per_request REAL DEFAULT 0.0, -- For paid tiers
    authentication_type TEXT DEFAULT 'api_key', -- 'api_key', 'oauth', 'bearer_token', 'none'
    request_format TEXT DEFAULT 'json', -- 'json', 'xml', 'form_data'
    response_format TEXT DEFAULT 'json', -- 'json', 'xml', 'text'
    supported_methods TEXT DEFAULT 'GET,POST', -- Comma-separated HTTP methods
    error_count INTEGER DEFAULT 0,
    last_error_message TEXT,
    last_error_timestamp TIMESTAMP,
    discovery_source TEXT, -- 'manual', 'research_agent', 'github', 'api_directory'
    validation_status TEXT DEFAULT 'pending', -- 'pending', 'validated', 'rejected'
    tags TEXT, -- Comma-separated tags for categorization
    -- New Command Center columns
    signup_url TEXT, -- Direct link to service registration page
    last_health_status TEXT DEFAULT 'UNKNOWN', -- Real-time status: 'HEALTHY', 'INVALID_KEY', 'ERROR', 'UNKNOWN'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- For managing the AI's writing personas for a human touch
CREATE TABLE IF NOT EXISTS author_personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_name TEXT NOT NULL UNIQUE,
    writing_style_description TEXT NOT NULL,
    target_audience TEXT,
    channel_name TEXT -- Foreign key to channels table
);

-- The "Hypocrisy Engine" database
CREATE TABLE IF NOT EXISTS hypocrisy_tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_category TEXT NOT NULL, -- 'Politician', 'Celebrity', 'Media Outlet'
    topic TEXT NOT NULL,
    statement_A TEXT NOT NULL,
    statement_B TEXT NOT NULL,
    source_url_A TEXT,
    source_url_B TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- For managing and optimizing affiliate programs
CREATE TABLE IF NOT EXISTS affiliate_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_name TEXT NOT NULL,
    product_category TEXT NOT NULL,
    commission_rate REAL,
    conversion_rate REAL DEFAULT 0.0,
    affiliate_link_template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    -- New Command Center columns
    signup_url TEXT, -- Direct link to affiliate program registration page
    last_health_status TEXT DEFAULT 'UNKNOWN', -- Real-time status: 'HEALTHY', 'INVALID_CREDENTIALS', 'ERROR', 'UNKNOWN'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- For the performance feedback loop
CREATE TABLE IF NOT EXISTS video_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL UNIQUE,
    channel_name TEXT NOT NULL,
    topic TEXT,
    views INTEGER,
    likes INTEGER,
    comments INTEGER,
    watch_time_hours REAL,
    ctr REAL, -- Click-through rate
    affiliate_clicks INTEGER,
    last_updated TIMESTAMP
);

-- For configuring channels
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT NOT NULL UNIQUE,
    channel_id_yt TEXT,
    handle_yt TEXT,
    topic TEXT,
    status TEXT DEFAULT 'paused', -- 'active', 'paused'
    notes TEXT
);

-- For managing each channel's cast of avatars
CREATE TABLE IF NOT EXISTS avatars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    avatar_name TEXT NOT NULL,
    is_default BOOLEAN DEFAULT 0,
    base_face_image TEXT NOT NULL,
    vocal_tone TEXT,
    visual_style_prompt TEXT,
    FOREIGN KEY (channel_id) REFERENCES channels (id)
);

-- For storing research and evidence for scripts
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,
    content_type TEXT, -- 'quote', 'statistic', 'fact'
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- For Progressive Self-Repair Protocol - tracking repair attempts and outcomes
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

-- For API Opportunity Finder - storing discovered API suggestions
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
    estimated_daily_limit INTEGER,
    authentication_required BOOLEAN DEFAULT 1,
    cost_tier TEXT DEFAULT 'free', -- 'free', 'freemium', 'paid'
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'added_to_registry'
    reviewed_by TEXT, -- User who reviewed the suggestion
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    added_to_registry_at TIMESTAMP
);

-- For Affiliate Opportunity Finder - storing discovered affiliate program suggestions
CREATE TABLE IF NOT EXISTS affiliate_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_name TEXT NOT NULL,
    product_category TEXT NOT NULL,
    commission_rate REAL,
    signup_url TEXT NOT NULL,
    description TEXT,
    discovery_source TEXT NOT NULL, -- 'affiliate_network', 'company_website', 'research_agent'
    discovery_details TEXT, -- JSON with source-specific metadata
    confidence_score REAL DEFAULT 0.0, -- AI confidence in program quality (0-1)
    validation_notes TEXT, -- LLM analysis of program terms
    estimated_conversion_rate REAL,
    payment_terms TEXT, -- e.g., 'Net 30', 'Weekly', 'Monthly'
    minimum_payout REAL,
    cookie_duration_days INTEGER,
    cost_tier TEXT DEFAULT 'free', -- 'free', 'application_required', 'invite_only'
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'added_to_registry'
    reviewed_by TEXT, -- User who reviewed the suggestion
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    added_to_registry_at TIMESTAMP
);

-- For API Orchestrator - tracking failover and load balancing decisions
CREATE TABLE IF NOT EXISTS api_orchestration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL, -- Unique identifier for the request
    capability_requested TEXT NOT NULL,
    primary_api_id INTEGER, -- First API attempted
    fallback_apis TEXT, -- JSON array of fallback API IDs tried
    successful_api_id INTEGER, -- API that successfully handled the request
    total_attempts INTEGER DEFAULT 1,
    total_response_time_ms INTEGER,
    failure_reasons TEXT, -- JSON array of failure reasons for each attempt
    load_balancing_factor REAL, -- Factor used in load balancing decision
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (primary_api_id) REFERENCES api_registry (id),
    FOREIGN KEY (successful_api_id) REFERENCES api_registry (id)
);

-- For tracking API discovery tasks and Research Agent activities
CREATE TABLE IF NOT EXISTS api_discovery_tasks (
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

-- For storing all generated reports for the Report Center
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