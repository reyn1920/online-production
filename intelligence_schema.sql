-- Intelligence Database Schema
-- Simple schema for intelligence.db

-- Create trend_analysis table
CREATE TABLE IF NOT EXISTS trend_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trend_name TEXT NOT NULL,
    trend_score REAL,
    last_updated DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create intelligence_briefings table
CREATE TABLE IF NOT EXISTS intelligence_briefings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    briefing_title TEXT NOT NULL,
    content TEXT,
    created_at DATETIME,
    priority TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create api_discovery_tasks table
CREATE TABLE IF NOT EXISTS api_discovery_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT,
    task_type TEXT,
    target_capability TEXT,
    search_parameters TEXT,
    capability_gap TEXT,
    search_keywords TEXT,
    target_domains TEXT,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending',
    assigned_agent TEXT,
    progress_notes TEXT,
    apis_found INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_api_discovery_tasks_status ON api_discovery_tasks(status);
CREATE INDEX IF NOT EXISTS idx_api_discovery_tasks_priority ON api_discovery_tasks(priority);
