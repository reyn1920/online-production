PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topic TEXT NOT NULL,
  started_at_utc TEXT NOT NULL,
  ended_at_utc TEXT,
  source_count INTEGER DEFAULT 0,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  title TEXT,
  domain TEXT,
  url TEXT UNIQUE,
  publisher TEXT,
  content_type TEXT,
  first_seen_utc TEXT,
  last_modified TEXT,
  accessed_utc TEXT,
  why_consulted TEXT,
  relevance INTEGER,
  credibility_notes TEXT,
  redirect_of TEXT,
  status TEXT,
  created_at_utc TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_sources_run ON sources(run_id);
CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain);
CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url);
CREATE INDEX IF NOT EXISTS idx_runs_topic ON runs(topic);
