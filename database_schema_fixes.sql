-- SQL ALTER TABLE commands to fix missing columns in intelligence.db
-- These commands should be run on the intelligence.db database

-- Fix trend_analysis table - add missing columns
ALTER TABLE trend_analysis ADD COLUMN trend_score REAL;
ALTER TABLE trend_analysis ADD COLUMN last_updated DATETIME;

-- Fix intelligence_briefings table - add missing columns
ALTER TABLE intelligence_briefings ADD COLUMN content TEXT;
ALTER TABLE intelligence_briefings ADD COLUMN created_at DATETIME;
ALTER TABLE intelligence_briefings ADD COLUMN priority TEXT;

-- Note: These ALTER TABLE statements will add the missing columns that
-- research_tools.py expects when inserting data into the intelligence database.
-- The trend_analysis table needs trend_score and last_updated columns.
-- The intelligence_briefings table needs content, created_at, and priority columns.

-- Fix api_discovery_tasks table - add missing columns for backend/api_opportunity_finder.py
-- These columns are required by the APIOpportunityFinder class
ALTER TABLE api_discovery_tasks ADD COLUMN task_type TEXT;
ALTER TABLE api_discovery_tasks ADD COLUMN target_capability TEXT;
ALTER TABLE api_discovery_tasks ADD COLUMN search_parameters TEXT;
ALTER TABLE api_discovery_tasks ADD COLUMN capability_gap TEXT;
ALTER TABLE api_discovery_tasks ADD COLUMN search_keywords TEXT;
ALTER TABLE api_discovery_tasks ADD COLUMN target_domains TEXT;
ALTER TABLE api_discovery_tasks ADD COLUMN priority INTEGER DEFAULT 5;
ALTER TABLE api_discovery_tasks ADD COLUMN assigned_agent TEXT;
ALTER TABLE api_discovery_tasks ADD COLUMN progress_notes TEXT;
ALTER TABLE api_discovery_tasks ADD COLUMN apis_found INTEGER DEFAULT 0;
ALTER TABLE api_discovery_tasks ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE api_discovery_tasks ADD COLUMN completed_at TIMESTAMP;

-- Update task_type for existing records if the column was just added
UPDATE api_discovery_tasks SET task_type = 'api_research' WHERE task_type IS NULL;
