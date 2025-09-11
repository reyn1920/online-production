-- Migration to add missing columns to affiliate_dashboards table
-- This ensures compatibility with the affiliate credentials API

-- Add is_active column if it doesn't exist
ALTER TABLE affiliate_dashboards ADD COLUMN is_active BOOLEAN DEFAULT 1;

-- Add other missing columns that the API expects
ALTER TABLE affiliate_dashboards ADD COLUMN login_url TEXT;
ALTER TABLE affiliate_dashboards ADD COLUMN username TEXT;
ALTER TABLE affiliate_dashboards ADD COLUMN encrypted_password TEXT;
ALTER TABLE affiliate_dashboards ADD COLUMN login_success_rate REAL DEFAULT 0;
ALTER TABLE affiliate_dashboards ADD COLUMN last_login_attempt TIMESTAMP;
ALTER TABLE affiliate_dashboards ADD COLUMN notes TEXT;
ALTER TABLE affiliate_dashboards ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_affiliate_dashboards_active ON affiliate_dashboards(is_active);
CREATE INDEX IF NOT EXISTS idx_affiliate_dashboards_platform ON affiliate_dashboards(platform_name);