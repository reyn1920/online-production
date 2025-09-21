-- TASK COMPLETION DATABASE SCHEMA
-- This database will track EVERY task, issue, and completion status
-- to ensure NOTHING is left incomplete

-- Core tables for task tracking
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
    status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'blocked', 'failed')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    deadline TIMESTAMP,
    estimated_hours REAL,
    actual_hours REAL,
    completion_percentage INTEGER DEFAULT 0 CHECK(completion_percentage >= 0 AND completion_percentage <= 100),
    parent_task_id INTEGER,
    assigned_to TEXT,
    notes TEXT,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
);

-- Files and forbidden vocabulary tracking
CREATE TABLE IF NOT EXISTS files_with_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_type TEXT,
    issue_type TEXT NOT NULL,
    issue_description TEXT,
    severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low')) DEFAULT 'medium',
    status TEXT CHECK(status IN ('identified', 'in_progress', 'fixed', 'ignored')) DEFAULT 'identified',
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fixed_at TIMESTAMP,
    line_numbers TEXT, -- JSON array of line numbers with issues
    forbidden_words TEXT, -- JSON array of forbidden words found
    fix_notes TEXT
);

-- Project components and their status
CREATE TABLE IF NOT EXISTS project_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL, -- 'service', 'module', 'config', 'deployment', etc.
    file_path TEXT,
    description TEXT,
    status TEXT CHECK(status IN ('not_started', 'in_progress', 'completed', 'needs_review', 'failed')) DEFAULT 'not_started',
    health_status TEXT CHECK(health_status IN ('healthy', 'warning', 'critical', 'unknown')) DEFAULT 'unknown',
    last_tested TIMESTAMP,
    test_results TEXT, -- JSON of test results
    dependencies TEXT, -- JSON array of component dependencies
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Deployment and environment tracking
CREATE TABLE IF NOT EXISTS deployments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deployment_name TEXT NOT NULL,
    environment TEXT NOT NULL, -- 'development', 'staging', 'production'
    version TEXT,
    status TEXT CHECK(status IN ('planned', 'in_progress', 'deployed', 'failed', 'rolled_back')) DEFAULT 'planned',
    deployment_type TEXT, -- 'initial', 'update', 'hotfix', 'rollback'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    deployed_by TEXT,
    deployment_notes TEXT,
    rollback_plan TEXT,
    health_check_url TEXT,
    health_status TEXT CHECK(health_status IN ('healthy', 'unhealthy', 'unknown')) DEFAULT 'unknown'
);

-- Configuration and settings tracking
CREATE TABLE IF NOT EXISTS configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name TEXT NOT NULL,
    config_type TEXT NOT NULL, -- 'environment', 'service', 'database', 'security'
    file_path TEXT,
    config_data TEXT, -- JSON configuration data
    is_sensitive BOOLEAN DEFAULT FALSE,
    status TEXT CHECK(status IN ('draft', 'active', 'deprecated', 'needs_update')) DEFAULT 'draft',
    validation_status TEXT CHECK(validation_status IN ('valid', 'invalid', 'not_validated')) DEFAULT 'not_validated',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP
);

-- Error and issue tracking
CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_title TEXT NOT NULL,
    issue_description TEXT,
    issue_type TEXT NOT NULL, -- 'bug', 'security', 'performance', 'deployment', 'configuration'
    severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low')) DEFAULT 'medium',
    status TEXT CHECK(status IN ('open', 'in_progress', 'resolved', 'closed', 'wont_fix')) DEFAULT 'open',
    component_id INTEGER,
    file_path TEXT,
    error_message TEXT,
    stack_trace TEXT,
    reproduction_steps TEXT,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (component_id) REFERENCES project_components(id)
);

-- Task dependencies and relationships
CREATE TABLE IF NOT EXISTS task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    depends_on_task_id INTEGER NOT NULL,
    dependency_type TEXT CHECK(dependency_type IN ('blocks', 'requires', 'related')) DEFAULT 'blocks',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id),
    UNIQUE(task_id, depends_on_task_id)
);

-- Validation and completion checks
CREATE TABLE IF NOT EXISTS completion_validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    validation_type TEXT NOT NULL, -- 'manual', 'automated', 'test', 'review'
    validation_criteria TEXT NOT NULL,
    validation_result TEXT CHECK(validation_result IN ('pass', 'fail', 'pending')) DEFAULT 'pending',
    validated_by TEXT,
    validated_at TIMESTAMP,
    validation_notes TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Progress tracking and metrics
CREATE TABLE IF NOT EXISTS progress_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    component_id INTEGER,
    log_type TEXT NOT NULL, -- 'progress', 'milestone', 'blocker', 'completion'
    message TEXT NOT NULL,
    progress_percentage INTEGER CHECK(progress_percentage >= 0 AND progress_percentage <= 100),
    logged_by TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (component_id) REFERENCES project_components(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category);
CREATE INDEX IF NOT EXISTS idx_files_status ON files_with_issues(status);
CREATE INDEX IF NOT EXISTS idx_files_severity ON files_with_issues(severity);
CREATE INDEX IF NOT EXISTS idx_components_status ON project_components(status);
CREATE INDEX IF NOT EXISTS idx_components_health ON project_components(health_status);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues(severity);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);
CREATE INDEX IF NOT EXISTS idx_deployments_environment ON deployments(environment);

-- Views for common queries
CREATE VIEW IF NOT EXISTS incomplete_tasks AS
SELECT 
    t.*,
    COUNT(d.depends_on_task_id) as dependency_count,
    GROUP_CONCAT(pt.task_name) as parent_tasks
FROM tasks t
LEFT JOIN task_dependencies d ON t.id = d.task_id
LEFT JOIN tasks pt ON t.parent_task_id = pt.id
WHERE t.status NOT IN ('completed')
GROUP BY t.id;

CREATE VIEW IF NOT EXISTS critical_issues AS
SELECT 
    i.*,
    pc.component_name,
    pc.component_type
FROM issues i
LEFT JOIN project_components pc ON i.component_id = pc.id
WHERE i.severity IN ('critical', 'high') 
AND i.status IN ('open', 'in_progress');

CREATE VIEW IF NOT EXISTS files_needing_fixes AS
SELECT 
    f.*,
    COUNT(CASE WHEN f.status = 'identified' THEN 1 END) as open_issues
FROM files_with_issues f
WHERE f.status != 'fixed'
GROUP BY f.file_path;

CREATE VIEW IF NOT EXISTS deployment_status_summary AS
SELECT 
    environment,
    COUNT(*) as total_deployments,
    COUNT(CASE WHEN status = 'deployed' THEN 1 END) as successful_deployments,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_deployments,
    COUNT(CASE WHEN health_status = 'healthy' THEN 1 END) as healthy_deployments
FROM deployments
GROUP BY environment;

-- Triggers to ensure data integrity and automatic updates
CREATE TRIGGER IF NOT EXISTS update_task_timestamps
AFTER UPDATE ON tasks
FOR EACH ROW
WHEN NEW.status != OLD.status
BEGIN
    UPDATE tasks SET 
        started_at = CASE 
            WHEN NEW.status = 'in_progress' AND OLD.status = 'pending' THEN CURRENT_TIMESTAMP
            ELSE OLD.started_at
        END,
        completed_at = CASE 
            WHEN NEW.status = 'completed' THEN CURRENT_TIMESTAMP
            ELSE OLD.completed_at
        END
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_component_timestamp
AFTER UPDATE ON project_components
FOR EACH ROW
BEGIN
    UPDATE project_components SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS validate_task_completion
BEFORE UPDATE ON tasks
FOR EACH ROW
WHEN NEW.status = 'completed' AND NEW.completion_percentage < 100
BEGIN
    SELECT RAISE(ABORT, 'Cannot mark task as completed with less than 100% completion');
END;