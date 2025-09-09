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