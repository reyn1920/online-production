-- RuntimeHQ MAX Database Schema
-- Initial migration for all required tables

-- System checks table
CREATE TABLE IF NOT EXISTS system_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL,
    details TEXT,
    timestamp TEXT NOT NULL
);

-- Visual proofs table
CREATE TABLE IF NOT EXISTS visual_proofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proof_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT NOT NULL
);

-- Revenue table
CREATE TABLE IF NOT EXISTS revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    source TEXT NOT NULL,
    description TEXT,
    timestamp TEXT NOT NULL
);

-- Job queue table
CREATE TABLE IF NOT EXISTS job_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type TEXT NOT NULL,
    payload TEXT,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    result TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- Channels table
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    config TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- Uploads table
CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    original_name TEXT,
    file_path TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    upload_time TEXT NOT NULL,
    channel_id INTEGER,
    metadata TEXT,
    FOREIGN KEY (channel_id) REFERENCES channels (id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_system_checks_timestamp ON system_checks(timestamp);
CREATE INDEX IF NOT EXISTS idx_visual_proofs_type ON visual_proofs(proof_type);
CREATE INDEX IF NOT EXISTS idx_visual_proofs_created ON visual_proofs(created_at);
CREATE INDEX IF NOT EXISTS idx_revenue_timestamp ON revenue(timestamp);
CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status);
CREATE INDEX IF NOT EXISTS idx_job_queue_priority ON job_queue(priority);
CREATE INDEX IF NOT EXISTS idx_channels_status ON channels(status);
CREATE INDEX IF NOT EXISTS idx_uploads_channel ON uploads(channel_id);