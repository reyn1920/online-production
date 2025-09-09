-- API & Affiliate Command Center Schema Updates
-- This migration adds the required columns and tables for the Command Center functionality

-- Add missing columns to api_registry table
ALTER TABLE api_registry ADD COLUMN signup_url TEXT;
ALTER TABLE api_registry ADD COLUMN last_health_status TEXT DEFAULT 'unknown' CHECK (last_health_status IN ('HEALTHY', 'INVALID_KEY', 'RATE_LIMITED', 'OFFLINE', 'ERROR', 'unknown'));
ALTER TABLE api_registry ADD COLUMN is_active BOOLEAN DEFAULT TRUE;

-- Add missing columns to affiliate_programs table
ALTER TABLE affiliate_programs ADD COLUMN signup_url TEXT;
ALTER TABLE affiliate_programs ADD COLUMN last_health_status TEXT DEFAULT 'unknown' CHECK (last_health_status IN ('HEALTHY', 'INVALID_KEY', 'LOGIN_FAILED', 'SUSPENDED', 'ERROR', 'unknown'));
ALTER TABLE affiliate_programs ADD COLUMN is_active BOOLEAN DEFAULT TRUE;

-- Create affiliate_suggestions table (similar to api_suggestions)
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

-- Update existing api_suggestions table to match Command Center requirements
ALTER TABLE api_suggestions ADD COLUMN signup_url TEXT;
ALTER TABLE api_suggestions ADD COLUMN category TEXT;
ALTER TABLE api_suggestions ADD COLUMN source_url TEXT;
ALTER TABLE api_suggestions ADD COLUMN research_notes TEXT;
ALTER TABLE api_suggestions ADD COLUMN status TEXT DEFAULT 'new' CHECK (status IN ('new', 'reviewed', 'added', 'rejected'));
ALTER TABLE api_suggestions ADD COLUMN discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_api_registry_active ON api_registry(is_active);
CREATE INDEX IF NOT EXISTS idx_api_registry_health_status ON api_registry(last_health_status);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_active ON affiliate_programs(is_active);
CREATE INDEX IF NOT EXISTS idx_affiliate_programs_health_status ON affiliate_programs(last_health_status);
CREATE INDEX IF NOT EXISTS idx_affiliate_suggestions_status ON affiliate_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_affiliate_suggestions_category ON affiliate_suggestions(category);
CREATE INDEX IF NOT EXISTS idx_api_suggestions_status ON api_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_api_suggestions_category ON api_suggestions(category);

-- Update triggers to handle new columns
DROP TRIGGER IF EXISTS update_api_registry_timestamp;
CREATE TRIGGER update_api_registry_timestamp
AFTER UPDATE ON api_registry
FOR EACH ROW
BEGIN
    UPDATE api_registry SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS update_affiliate_programs_timestamp;
CREATE TRIGGER update_affiliate_programs_timestamp
AFTER UPDATE ON affiliate_programs
FOR EACH ROW
BEGIN
    UPDATE affiliate_programs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Create trigger for affiliate_suggestions
CREATE TRIGGER IF NOT EXISTS update_affiliate_suggestions_timestamp
AFTER UPDATE ON affiliate_suggestions
FOR EACH ROW
BEGIN
    UPDATE affiliate_suggestions SET discovered_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Insert some sample data for testing
INSERT OR IGNORE INTO api_suggestions (api_name, api_description, signup_url, category, use_case, integration_complexity, potential_value, status) VALUES
('OpenWeatherMap', 'Free weather data API with 1000 calls/day', 'https://openweathermap.org/api', 'Weather', 'Weather information for content personalization', 'low', 8.5, 'new'),
('JSONPlaceholder', 'Free fake REST API for testing and prototyping', 'https://jsonplaceholder.typicode.com/', 'Development', 'Testing and development placeholder data', 'low', 6.0, 'new'),
('REST Countries', 'Free API for country information', 'https://restcountries.com/', 'Geography', 'Country data for location-based content', 'low', 7.0, 'new');

INSERT OR IGNORE INTO affiliate_suggestions (program_name, company_name, program_description, signup_url, commission_rate, commission_type, category, potential_value, integration_complexity, status) VALUES
('Amazon Associates', 'Amazon', 'Earn up to 10% advertising fees from qualifying purchases', 'https://affiliate-program.amazon.com/', '1-10%', 'percentage', 'E-commerce', 9.5, 'medium', 'new'),
('ShareASale', 'ShareASale Network', 'Access to 4000+ merchant affiliate programs', 'https://www.shareasale.com/shareasale.cfm?call=signup', 'Varies', 'percentage', 'Network', 8.5, 'medium', 'new'),
('ClickBank', 'ClickBank', 'Digital products with high commission rates', 'https://accounts.clickbank.com/signup/', '10-75%', 'percentage', 'Digital Products', 8.0, 'medium', 'new');

-- Add comments for documentation
COMMENT ON COLUMN api_registry.signup_url IS 'Direct URL to sign up for the API service';
COMMENT ON COLUMN api_registry.last_health_status IS 'Last known health status from automated checks';
COMMENT ON COLUMN api_registry.is_active IS 'Whether this API is currently active for use';
COMMENT ON COLUMN affiliate_programs.signup_url IS 'Direct URL to sign up for the affiliate program';
COMMENT ON COLUMN affiliate_programs.last_health_status IS 'Last known health status from automated checks';
COMMENT ON COLUMN affiliate_programs.is_active IS 'Whether this affiliate program is currently active';