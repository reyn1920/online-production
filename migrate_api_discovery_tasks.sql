-- Migration script to update api_discovery_tasks table schema
-- This script handles the transition from the old schema to the new comprehensive schema
-- Run this on any existing databases that have the old api_discovery_tasks structure

-- First, create a backup of the existing table
CREATE TABLE IF NOT EXISTS api_discovery_tasks_backup AS
SELECT * FROM api_discovery_tasks;

-- Drop the existing table
DROP TABLE IF EXISTS api_discovery_tasks;

-- Create the new table with the updated schema
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

-- Migrate data from backup table to new table
-- Map old columns to new columns where possible
INSERT INTO api_discovery_tasks (
    id, task_name, task_type, status, created_at
)
SELECT
    id,
    task_name,
    'api_research' as task_type, -- Default task_type for migrated records
    status,
    created_at
FROM api_discovery_tasks_backup
WHERE EXISTS (SELECT 1 FROM api_discovery_tasks_backup);

-- Clean up backup table (optional - comment out if you want to keep the backup)
-- DROP TABLE api_discovery_tasks_backup;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_api_discovery_tasks_status
ON api_discovery_tasks(status, priority DESC);

CREATE INDEX IF NOT EXISTS idx_api_discovery_tasks_created_at
ON api_discovery_tasks(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_api_discovery_tasks_assigned_agent
ON api_discovery_tasks(assigned_agent, status);
