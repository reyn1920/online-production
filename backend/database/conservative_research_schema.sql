-- Conservative Research Database Schema
-- Comprehensive database design for tracking Democratic hypocrisy, lies, and inaction
-- Author: Trae AI Production System
-- Date: 2025

-- Main table for hypocrisy examples
CREATE TABLE IF NOT EXISTS hypocrisy_examples (
    id TEXT PRIMARY KEY,
    politician TEXT NOT NULL,
    category TEXT NOT NULL, -- 'immigration', 'economy', 'russia_investigation', 'tariffs', 'covid', 'crime', 'election'
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    source_url TEXT NOT NULL,
    date_recorded TEXT, -- When the hypocrisy occurred
    evidence_type TEXT NOT NULL, -- 'speech', 'vote', 'statement', 'tweet', 'interview', 'financial_records'
    contradiction_details TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    tags TEXT NOT NULL, -- JSON array of tags
    verification_status TEXT DEFAULT 'verified' CHECK (verification_status IN ('verified', 'pending', 'disputed')),
    impact_score REAL DEFAULT 0.0, -- 0.0 to 10.0 scale
    media_coverage_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_hypocrisy_politician ON hypocrisy_examples(politician);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_category ON hypocrisy_examples(category);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_severity ON hypocrisy_examples(severity);
CREATE INDEX IF NOT EXISTS idx_hypocrisy_date ON hypocrisy_examples(date_recorded);

-- News articles table for tracking sources
CREATE TABLE IF NOT EXISTS news_articles (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    content TEXT,
    summary TEXT,
    published_date TEXT,
    scraped_at TEXT NOT NULL,
    relevance_score REAL DEFAULT 0.0,
    sentiment_score REAL DEFAULT 0.0, -- -1.0 (negative) to 1.0 (positive)
    keyword_matches TEXT, -- JSON array of matched keywords
    article_type TEXT DEFAULT 'news' CHECK (article_type IN ('news', 'opinion', 'analysis', 'fact_check')),
    political_lean TEXT CHECK (political_lean IN ('left', 'center', 'right', 'unknown'))
);

CREATE INDEX IF NOT EXISTS idx_articles_source ON news_articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_relevance ON news_articles(relevance_score);
CREATE INDEX IF NOT EXISTS idx_articles_date ON news_articles(published_date);

-- Politicians tracking table
CREATE TABLE IF NOT EXISTS politicians (
    name TEXT PRIMARY KEY,
    full_name TEXT,
    party TEXT NOT NULL CHECK (party IN ('Democrat', 'Republican', 'Independent')),
    position TEXT, -- 'President', 'Senator', 'Representative', 'Former President', etc.
    state TEXT,
    district TEXT,
    hypocrisy_count INTEGER DEFAULT 0,
    severity_avg REAL DEFAULT 0.0,
    last_updated TEXT NOT NULL,
    active_status TEXT DEFAULT 'active' CHECK (active_status IN ('active', 'retired', 'deceased')),
    social_media_handles TEXT -- JSON object with Twitter, Facebook, etc.
);

-- Categories table for organizing hypocrisy types
CREATE TABLE IF NOT EXISTS categories (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT,
    parent_category TEXT,
    example_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (parent_category) REFERENCES categories(name)
);

-- Insert default categories
INSERT OR IGNORE INTO categories (name, display_name, description, created_at) VALUES
('immigration', 'Immigration & Border Security', 'Examples related to border security, immigration policy, and enforcement', datetime('now')),
('economy', 'Economy & Trade', 'Examples related to economic policy, tariffs, trade deals, and fiscal policy', datetime('now')),
('russia_investigation', 'Russia Investigation', 'Examples related to Trump-Russia collusion claims, Mueller investigation, and related false narratives', datetime('now')),
('covid', 'COVID-19 Response', 'Examples related to pandemic response, lockdowns, mandates, and policy contradictions', datetime('now')),
('crime', 'Crime & Law Enforcement', 'Examples related to defund police, bail reform, and criminal justice policy', datetime('now')),
('election', 'Election Integrity', 'Examples related to voting laws, election security, and fraud claims', datetime('now')),
('energy', 'Energy Policy', 'Examples related to oil, gas, renewable energy, and climate policy', datetime('now')),
('foreign_policy', 'Foreign Policy', 'Examples related to international relations, military intervention, and diplomacy', datetime('now')),
('healthcare', 'Healthcare', 'Examples related to Obamacare, Medicare, and healthcare policy', datetime('now')),
('taxes', 'Tax Policy', 'Examples related to tax cuts, tax increases, and fiscal responsibility', datetime('now'));

-- Evidence sources table
CREATE TABLE IF NOT EXISTS evidence_sources (
    id TEXT PRIMARY KEY,
    hypocrisy_example_id TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('video', 'audio', 'document', 'tweet', 'article', 'vote_record')),
    source_url TEXT NOT NULL,
    source_title TEXT,
    source_date TEXT,
    description TEXT,
    credibility_score REAL DEFAULT 5.0, -- 1.0 to 10.0 scale
    created_at TEXT NOT NULL,
    FOREIGN KEY (hypocrisy_example_id) REFERENCES hypocrisy_examples(id)
);

-- Media coverage tracking
CREATE TABLE IF NOT EXISTS media_coverage (
    id TEXT PRIMARY KEY,
    hypocrisy_example_id TEXT NOT NULL,
    media_outlet TEXT NOT NULL,
    article_url TEXT NOT NULL,
    headline TEXT,
    coverage_type TEXT CHECK (coverage_type IN ('supportive', 'critical', 'neutral', 'fact_check')),
    published_date TEXT,
    reach_estimate INTEGER, -- Estimated audience reach
    created_at TEXT NOT NULL,
    FOREIGN KEY (hypocrisy_example_id) REFERENCES hypocrisy_examples(id)
);

-- YouTube videos and social media content
CREATE TABLE IF NOT EXISTS social_media_content (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL CHECK (platform IN ('youtube', 'twitter', 'facebook', 'instagram', 'tiktok')),
    content_url TEXT NOT NULL UNIQUE,
    title TEXT,
    description TEXT,
    author TEXT,
    published_date TEXT,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    relevance_score REAL DEFAULT 0.0,
    content_type TEXT CHECK (content_type IN ('video', 'post', 'tweet', 'story')),
    transcript TEXT, -- For videos
    scraped_at TEXT NOT NULL
);

-- Link social media content to hypocrisy examples
CREATE TABLE IF NOT EXISTS content_examples_link (
    content_id TEXT NOT NULL,
    example_id TEXT NOT NULL,
    relevance_type TEXT CHECK (relevance_type IN ('direct_evidence', 'supporting', 'related', 'contradiction')),
    created_at TEXT NOT NULL,
    PRIMARY KEY (content_id, example_id),
    FOREIGN KEY (content_id) REFERENCES social_media_content(id),
    FOREIGN KEY (example_id) REFERENCES hypocrisy_examples(id)
);

-- Fact-checking and verification table
CREATE TABLE IF NOT EXISTS fact_checks (
    id TEXT PRIMARY KEY,
    hypocrisy_example_id TEXT NOT NULL,
    fact_checker TEXT NOT NULL, -- 'PolitiFact', 'FactCheck.org', 'Snopes', etc.
    rating TEXT, -- 'True', 'False', 'Pants on Fire', 'Four Pinocchios', etc.
    fact_check_url TEXT,
    summary TEXT,
    checked_date TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (hypocrisy_example_id) REFERENCES hypocrisy_examples(id)
);

-- Weekly content generation tracking
CREATE TABLE IF NOT EXISTS weekly_content (
    id TEXT PRIMARY KEY,
    week_start_date TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    example_count INTEGER DEFAULT 0,
    categories_covered TEXT, -- JSON array
    generated_at TEXT NOT NULL,
    published_status TEXT DEFAULT 'draft' CHECK (published_status IN ('draft', 'published', 'archived'))
);

-- Link weekly content to specific examples
CREATE TABLE IF NOT EXISTS weekly_content_examples (
    weekly_content_id TEXT NOT NULL,
    hypocrisy_example_id TEXT NOT NULL,
    display_order INTEGER DEFAULT 0,
    PRIMARY KEY (weekly_content_id, hypocrisy_example_id),
    FOREIGN KEY (weekly_content_id) REFERENCES weekly_content(id),
    FOREIGN KEY (hypocrisy_example_id) REFERENCES hypocrisy_examples(id)
);

-- Search and analytics
CREATE TABLE IF NOT EXISTS search_queries (
    id TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_type TEXT CHECK (query_type IN ('politician', 'category', 'keyword', 'date_range')),
    results_count INTEGER DEFAULT 0,
    executed_at TEXT NOT NULL,
    execution_time_ms INTEGER DEFAULT 0
);

-- User engagement tracking (for future web interface)
CREATE TABLE IF NOT EXISTS user_engagement (
    id TEXT PRIMARY KEY,
    example_id TEXT NOT NULL,
    engagement_type TEXT CHECK (engagement_type IN ('view', 'share', 'bookmark', 'comment')),
    user_session TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (example_id) REFERENCES hypocrisy_examples(id)
);

-- Views for common queries
CREATE VIEW IF NOT EXISTS high_impact_examples AS
SELECT 
    he.*,
    p.full_name,
    p.position,
    p.party,
    c.display_name as category_display
FROM hypocrisy_examples he
JOIN politicians p ON he.politician = p.name
JOIN categories c ON he.category = c.name
WHERE he.severity = 'high' AND he.verification_status = 'verified'
ORDER BY he.impact_score DESC, he.date_recorded DESC;

CREATE VIEW IF NOT EXISTS recent_examples AS
SELECT 
    he.*,
    p.full_name,
    p.position,
    c.display_name as category_display
FROM hypocrisy_examples he
JOIN politicians p ON he.politician = p.name
JOIN categories c ON he.category = c.name
WHERE he.created_at >= date('now', '-30 days')
ORDER BY he.created_at DESC;

CREATE VIEW IF NOT EXISTS politician_stats AS
SELECT 
    p.name,
    p.full_name,
    p.position,
    p.party,
    COUNT(he.id) as total_examples,
    COUNT(CASE WHEN he.severity = 'high' THEN 1 END) as high_severity_count,
    COUNT(CASE WHEN he.severity = 'medium' THEN 1 END) as medium_severity_count,
    COUNT(CASE WHEN he.severity = 'low' THEN 1 END) as low_severity_count,
    AVG(he.impact_score) as avg_impact_score,
    MAX(he.date_recorded) as latest_example_date
FROM politicians p
LEFT JOIN hypocrisy_examples he ON p.name = he.politician
GROUP BY p.name, p.full_name, p.position, p.party;

CREATE VIEW IF NOT EXISTS category_stats AS
SELECT 
    c.name,
    c.display_name,
    COUNT(he.id) as total_examples,
    COUNT(CASE WHEN he.severity = 'high' THEN 1 END) as high_severity_count,
    AVG(he.impact_score) as avg_impact_score,
    MAX(he.date_recorded) as latest_example_date
FROM categories c
LEFT JOIN hypocrisy_examples he ON c.name = he.category
GROUP BY c.name, c.display_name;

-- Insert sample politicians
INSERT OR IGNORE INTO politicians (name, full_name, party, position, last_updated) VALUES
('Adam Schiff', 'Adam Bennett Schiff', 'Democrat', 'Representative', datetime('now')),
('Hillary Clinton', 'Hillary Diane Rodham Clinton', 'Democrat', 'Former Secretary of State', datetime('now')),
('Chuck Schumer', 'Charles Ellis Schumer', 'Democrat', 'Senate Majority Leader', datetime('now')),
('Nancy Pelosi', 'Nancy Patricia Pelosi', 'Democrat', 'Former Speaker of the House', datetime('now')),
('Barack Obama', 'Barack Hussein Obama II', 'Democrat', 'Former President', datetime('now')),
('Joe Biden', 'Joseph Robinette Biden Jr.', 'Democrat', 'President', datetime('now')),
('Kamala Harris', 'Kamala Devi Harris', 'Democrat', 'Vice President', datetime('now')),
('Alexandria Ocasio-Cortez', 'Alexandria Ocasio-Cortez', 'Democrat', 'Representative', datetime('now')),
('Maxine Waters', 'Maxine Moore Waters', 'Democrat', 'Representative', datetime('now')),
('Jerry Nadler', 'Jerrold Lewis Nadler', 'Democrat', 'Representative', datetime('now'));

-- Triggers to maintain data consistency
CREATE TRIGGER IF NOT EXISTS update_politician_hypocrisy_count
AFTER INSERT ON hypocrisy_examples
BEGIN
    UPDATE politicians 
    SET hypocrisy_count = hypocrisy_count + 1,
        last_updated = datetime('now')
    WHERE name = NEW.politician;
END;

CREATE TRIGGER IF NOT EXISTS update_category_example_count
AFTER INSERT ON hypocrisy_examples
BEGIN
    UPDATE categories 
    SET example_count = example_count + 1
    WHERE name = NEW.category;
END;

CREATE TRIGGER IF NOT EXISTS update_example_timestamp
AFTER UPDATE ON hypocrisy_examples
BEGIN
    UPDATE hypocrisy_examples 
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- Full-text search setup (if SQLite FTS is available)
-- CREATE VIRTUAL TABLE IF NOT EXISTS hypocrisy_search USING fts5(
--     title, description, contradiction_details, tags,
--     content='hypocrisy_examples',
--     content_rowid='rowid'
-- );

-- Performance optimization indexes
CREATE INDEX IF NOT EXISTS idx_examples_impact_score ON hypocrisy_examples(impact_score DESC);
CREATE INDEX IF NOT EXISTS idx_examples_verification ON hypocrisy_examples(verification_status);
CREATE INDEX IF NOT EXISTS idx_articles_political_lean ON news_articles(political_lean);
CREATE INDEX IF NOT EXISTS idx_social_media_platform ON social_media_content(platform);
CREATE INDEX IF NOT EXISTS idx_social_media_relevance ON social_media_content(relevance_score DESC);

-- Comments for documentation
COMMENT ON TABLE hypocrisy_examples IS 'Main table storing documented examples of Democratic hypocrisy, lies, and inaction';
COMMENT ON TABLE politicians IS 'Tracking table for politicians with their basic information and statistics';
COMMENT ON TABLE categories IS 'Hierarchical categorization system for organizing hypocrisy examples';
COMMENT ON TABLE evidence_sources IS 'Supporting evidence and sources for each hypocrisy example';
COMMENT ON TABLE social_media_content IS 'YouTube videos and social media posts related to conservative research';

-- Sample queries for testing
/*
-- Get all high-severity examples for a specific politician
SELECT * FROM hypocrisy_examples 
WHERE politician = 'Adam Schiff' AND severity = 'high'
ORDER BY date_recorded DESC;

-- Get examples by category with politician info
SELECT he.*, p.full_name, p.position 
FROM hypocrisy_examples he
JOIN politicians p ON he.politician = p.name
WHERE he.category = 'immigration'
ORDER BY he.impact_score DESC;

-- Get weekly content with example count
SELECT wc.*, COUNT(wce.hypocrisy_example_id) as example_count
FROM weekly_content wc
LEFT JOIN weekly_content_examples wce ON wc.id = wce.weekly_content_id
GROUP BY wc.id
ORDER BY wc.week_start_date DESC;

-- Search examples by keyword in title or description
SELECT * FROM hypocrisy_examples
WHERE title LIKE '%border%' OR description LIKE '%border%'
ORDER BY impact_score DESC;
*/