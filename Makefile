# TRAE.AI Production Makefile
# Convenient commands for managing the complete AI-powered platform

# Go-Live Configuration
PYTHON = python3
VENV = venv
VENV_PYTHON = $(VENV)/bin/python
VENV_PIP = $(VENV)/bin/pip
VENV_FLASK = $(VENV)/bin/flask
PORT ?= 8000

.PHONY: help install build start stop restart logs status clean test deploy backup restore go-live no-launch fix-syntax venv-clean deps-install

# Default target
help:
	@echo "🚀 TRAE.AI Production Management"
	@echo "================================"
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make install     - Install all dependencies and setup environment"
	@echo "  make setup-env   - Copy .env.example to .env for configuration"
	@echo ""
	@echo "🏗️  Build & Deploy:"
	@echo "  make build       - Build all Docker images"
	@echo "  make start       - Start all services with Docker Compose"
	@echo "  make stop        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make deploy      - Deploy to production"
	@echo ""
	@echo "📊 Monitoring & Logs:"
	@echo "  make logs        - View logs from all services"
	@echo "  make status      - Check status of all services"
	@echo "  make health      - Run health checks"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test        - Run all tests"
	@echo "  make test-unit   - Run unit tests only"
	@echo "  make test-e2e    - Run end-to-end tests"
	@echo "  make lint        - Run code linting"
	@echo "  make lint-fix    - Auto-fix lint issues"
	@echo "  make security    - Run security scans"
	@echo "  make dev         - Auto-lint + test watch mode"
	@echo "  make dev-fast    - Bare-metal test watch mode"
	@echo "  make ci          - Run full CI pipeline (lint + tests + security)"
	@echo ""
	@echo "🗄️  Database & Backup:"
	@echo "  make db-init     - Initialize database with schema"
	@echo "  make db-migrate  - Run database migrations"
	@echo "  make backup      - Create system backup"
	@echo "  make restore     - Restore from backup"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean       - Clean up containers and images"
	@echo "  make clean-all   - Deep clean (remove volumes too)"
	@echo "  make update      - Update all dependencies"
	@echo ""
	@echo "🚀 Go-Live Commands:"
	@echo "  make go-live     - Run full go-live prep + launch (Flask server)"
	@echo "  make no-launch   - Run go-live prep but skip app launch"
	@echo "  make fix-syntax  - Fix Python syntax issues only"
	@echo "  make venv-clean  - Remove venv and __pycache__"
	@echo "  make deps-install - Install requirements (M1 optimized)"
	@echo ""

# Setup & Installation
install: setup-env
	@echo "📦 Installing TRAE.AI dependencies..."
	@if [ ! -d "venv" ]; then python3 -m venv venv; fi
	@. venv/bin/activate && pip install --upgrade pip
	@. venv/bin/activate && pip install -r requirements.txt
	@if [ -f "content-agent/requirements.txt" ]; then . venv/bin/activate && pip install -r content-agent/requirements.txt; fi
	@if [ -f "marketing-agent/requirements.txt" ]; then . venv/bin/activate && pip install -r marketing-agent/requirements.txt; fi
	@if [ -f "monetization-bundle/requirements.txt" ]; then . venv/bin/activate && pip install -r monetization-bundle/requirements.txt; fi
	@if [ -f "analytics-dashboard/requirements.txt" ]; then . venv/bin/activate && pip install -r analytics-dashboard/requirements.txt; fi
	@echo "✅ Installation complete!"

setup-env:
	@if [ ! -f ".env" ]; then \
		echo "📝 Creating .env file from template..."; \
		cp .env.example .env; \
		echo "⚠️  Please edit .env file with your API keys and configuration"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Build & Deploy
build:
	@echo "🏗️  Building TRAE.AI Docker images..."
	docker-compose build --parallel
	@echo "✅ Build complete!"

start: setup-env
	@echo "🚀 Starting TRAE.AI platform..."
	docker-compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@make status
	@echo ""
	@echo "🎉 TRAE.AI is running!"
	@echo "📊 Dashboard: http://localhost"
	@echo "📚 API Docs: http://localhost/api/content/docs"

stop:
	@echo "🛑 Stopping TRAE.AI platform..."
	docker-compose down
	@echo "✅ All services stopped"

restart: stop start

deploy: build
	@echo "🚀 Deploying TRAE.AI to production..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ Production deployment complete!"

# Monitoring & Logs
logs:
	@echo "📋 Viewing TRAE.AI logs..."
	docker-compose logs -f --tail=100

logs-service:
	@echo "📋 Viewing logs for $(SERVICE)..."
	docker-compose logs -f --tail=100 $(SERVICE)

status:
	@echo "📊 TRAE.AI Service Status:"
	@echo "========================="
	docker-compose ps
	@echo ""
	@echo "🔍 Health Checks:"
	@curl -s http://localhost/health || echo "❌ Main service not responding"
	@curl -s http://localhost/api/content/health || echo "❌ Content Agent not responding"
	@curl -s http://localhost/api/marketing/health || echo "❌ Marketing Agent not responding"
	@curl -s http://localhost/api/monetization/health || echo "❌ Monetization Bundle not responding"
	@curl -s http://localhost/api/analytics/health || echo "❌ Analytics Dashboard not responding"

health:
	@echo "🏥 Running comprehensive health checks..."
	@python tests/health_check.py

# Testing & Quality
test: test-unit test-e2e

test-unit:
	@echo "🧪 Running unit tests..."
	@. venv/bin/activate && python -m pytest tests/unit/ -v

test-e2e:
	@echo "🎬 Running end-to-end tests..."
	@. venv/bin/activate && python tests/test_final_verification.py

test-integration:
	@echo "🔗 Running integration tests..."
	@. venv/bin/activate && python -m pytest tests/integration/ -v

lint:
	@echo "🔍 Running code linting..."
	@. venv/bin/activate && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@. venv/bin/activate && black --check .
	@. venv/bin/activate && isort --check-only .

lint-fix:
	@echo "🔧 Auto-fixing lint issues..."
	@. venv/bin/activate && black .
	@. venv/bin/activate && isort .

security:
	@echo "🔒 Running security scans..."
	@. venv/bin/activate && bandit -r . -f json -o security-report.json || true
	@. venv/bin/activate && safety check

# Development workflow targets
dev: lint-fix
	@echo "🛠️  Starting development mode with auto-lint + test watch..."
	@. venv/bin/activate && python -m pytest tests/ -v --tb=short -x --lf
	@echo "🔄 Watching for changes... (Press Ctrl+C to stop)"
	@. venv/bin/activate && python -m pytest tests/ -v --tb=short -x --lf -f

dev-fast:
	@echo "⚡ Starting bare-metal test watch..."
	@echo "🔄 Watching for changes... (Press Ctrl+C to stop)"
	@. venv/bin/activate && python -m pytest tests/ -v --tb=short -x --lf -f --no-cov

# CI target - runs the same pipeline as GitHub Actions
ci:
	@echo "🚀 Running CI pipeline (lint + tests on multiple Python versions)..."
	@echo "📋 This matches the GitHub Actions workflow for pre-push confidence"
	@echo ""
	@echo "🔍 Step 1: Linting..."
	@make lint
	@echo ""
	@echo "🧪 Step 2: Running full test suite..."
	@make test
	@echo ""
	@echo "🔒 Step 3: Security checks..."
	@make security
	@echo ""
	@echo "✅ CI pipeline completed successfully! Ready for push."

# Database & Backup
db-init:
	@echo "🗄️  Initializing TRAE.AI database..."
	docker-compose exec postgres psql -U traeai -d traeai -f /docker-entrypoint-initdb.d/init-db.sql
	@echo "✅ Database initialized!"

db-migrate:
	@echo "🔄 Running database migrations..."
	@. venv/bin/activate && alembic upgrade head

db-backup:
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U traeai traeai > backups/db-backup-$(shell date +%Y%m%d-%H%M%S).sql
	@echo "✅ Database backup created in backups/"

db-restore:
	@echo "🔄 Restoring database from backup..."
	@if [ -z "$(BACKUP_FILE)" ]; then echo "❌ Please specify BACKUP_FILE=path/to/backup.sql"; exit 1; fi
	docker-compose exec -T postgres psql -U traeai -d traeai < $(BACKUP_FILE)
	@echo "✅ Database restored from $(BACKUP_FILE)"

backup: db-backup
	@echo "📦 Creating full system backup..."
	@mkdir -p backups/$(shell date +%Y%m%d-%H%M%S)
	@cp -r uploads/ backups/$(shell date +%Y%m%d-%H%M%S)/uploads/ 2>/dev/null || true
	@cp -r media/ backups/$(shell date +%Y%m%d-%H%M%S)/media/ 2>/dev/null || true
	@cp .env backups/$(shell date +%Y%m%d-%H%M%S)/.env 2>/dev/null || true
	@echo "✅ Full backup created in backups/"

restore:
	@echo "🔄 Restoring system from backup..."
	@if [ -z "$(BACKUP_DIR)" ]; then echo "❌ Please specify BACKUP_DIR=path/to/backup/directory"; exit 1; fi
	@if [ -d "$(BACKUP_DIR)/uploads" ]; then cp -r $(BACKUP_DIR)/uploads/ ./; fi
	@if [ -d "$(BACKUP_DIR)/media" ]; then cp -r $(BACKUP_DIR)/media/ ./; fi
	@echo "✅ System restored from $(BACKUP_DIR)"

# Maintenance
clean:
	@echo "🧹 Cleaning up Docker containers and images..."
	docker-compose down --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup complete!"

clean-all:
	@echo "🧹 Deep cleaning (removing volumes too)..."
	docker-compose down -v --remove-orphans
	docker system prune -af
	docker volume prune -f
	@echo "✅ Deep cleanup complete!"

update:
	@echo "🔄 Updating TRAE.AI dependencies..."
	@. venv/bin/activate && pip install --upgrade pip
	@. venv/bin/activate && pip install -r requirements.txt --upgrade
	docker-compose pull
	@echo "✅ Update complete!"

# Development helpers
dev-setup: install
	@echo "🛠️  Setting up development environment..."
	@. venv/bin/activate && pip install pytest black flake8 isort bandit safety
	@echo "✅ Development environment ready!"

dev-start:
	@echo "🛠️  Starting development servers..."
	@echo "Starting Content Agent on port 8001..."
	@. venv/bin/activate && cd content-agent && python main.py &
	@echo "Starting Marketing Agent on port 8002..."
	@. venv/bin/activate && cd marketing-agent && python main.py &
	@echo "Starting Monetization Bundle on port 8003..."
	@. venv/bin/activate && cd monetization-bundle && python main.py &
	@echo "Starting Analytics Dashboard on port 8004..."
	@. venv/bin/activate && cd analytics-dashboard && python main.py &
	@echo "✅ All development servers started!"

dev-stop:
	@echo "🛑 Stopping development servers..."
	@pkill -f "python main.py" || true
	@echo "✅ Development servers stopped!"

# Quick actions
quick-start: setup-env start

quick-test: test-unit

quick-deploy: build deploy

# Monitoring shortcuts
tail-content:
	@make logs-service SERVICE=content-agent

tail-marketing:
	@make logs-service SERVICE=marketing-agent

tail-monetization:
	@make logs-service SERVICE=monetization-bundle

tail-analytics:
	@make logs-service SERVICE=analytics-dashboard

tail-nginx:
	@make logs-service SERVICE=nginx

tail-db:
	@make logs-service SERVICE=postgres

# Performance monitoring
stats:
	@echo "📊 TRAE.AI Performance Stats:"
	@echo "============================="
	docker stats --no-stream

resources:
	@echo "💾 System Resource Usage:"
	@echo "========================="
	@df -h
	@echo ""
	@free -h
	@echo ""
	@docker system df

# Security helpers
scan-secrets:
	@echo "🔍 Scanning for secrets in codebase..."
	@git secrets --scan || echo "No git-secrets installed"

check-ports:
	@echo "🔍 Checking open ports..."
	@netstat -tlnp | grep -E ':(80|8001|8002|8003|8004|5432|6379|5672)'

# Documentation
docs:
	@echo "📚 Opening TRAE.AI documentation..."
	@open http://localhost/api/content/docs || echo "Please visit http://localhost/api/content/docs"

api-docs:
	@echo "📚 API Documentation URLs:"
	@echo "Content Agent: http://localhost/api/content/docs"
	@echo "Marketing Agent: http://localhost/api/marketing/docs"
	@echo "Monetization Bundle: http://localhost/api/monetization/docs"
	@echo "Analytics Dashboard: http://localhost/api/analytics/docs"

# Version info
version:
	@echo "🏷️  TRAE.AI Version Information:"
	@echo "================================"
	@echo "Platform: TRAE.AI v1.0.0"
	@echo "Docker: $(shell docker --version)"
	@echo "Docker Compose: $(shell docker-compose --version)"
	@echo "Python: $(shell python3 --version)"
	@echo "Node.js: $(shell node --version 2>/dev/null || echo 'Not installed')"
	@echo "Git: $(shell git --version)"

# Emergency procedures
emergency-stop:
	@echo "🚨 EMERGENCY STOP - Shutting down all TRAE.AI services immediately!"
	docker-compose kill
	docker-compose down --remove-orphans
	@echo "✅ Emergency shutdown complete!"

emergency-restart: emergency-stop
	@echo "🚨 EMERGENCY RESTART - Restarting TRAE.AI platform..."
	@sleep 5
	@make start

# System info
info:
	@echo "ℹ️  TRAE.AI System Information:"
	@echo "==============================="
	@echo "Project: TRAE.AI - AI-Powered Content & Marketing Platform"
	@echo "Services: Content Agent, Marketing Agent, Monetization Bundle, Analytics Dashboard"
	@echo "Database: PostgreSQL with Redis cache"
	@echo "Message Queue: RabbitMQ"
	@echo "Load Balancer: Nginx"
	@echo "Container Runtime: Docker with Docker Compose"
	@echo ""
	@echo "📁 Directory Structure:"
	@echo "  content-agent/     - AI content generation service"
	@echo "  marketing-agent/   - Marketing automation service"
	@echo "  monetization-bundle/ - Revenue optimization service"
	@echo "  analytics-dashboard/ - Business intelligence service"
	@echo "  nginx/            - Load balancer configuration"
	@echo "  tests/            - Test suites and verification"
	@echo ""
	@echo "🌐 Access Points:"
	@echo "  Main Dashboard: http://localhost"
	@echo "  API Documentation: http://localhost/api/*/docs"
	@echo "  Health Checks: http://localhost/health"

welcome:
	@echo ""
	@echo "🚀 Welcome to TRAE.AI!"
	@echo "======================"
	@echo ""
	@echo "The Ultimate AI-Powered Content & Marketing Automation Platform"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make install    # Install dependencies"
	@echo "  2. make setup-env  # Configure environment"
	@echo "  3. make start      # Launch the platform"
	@echo ""
	@echo "Go-Live Quick Start:"
	@echo "  1. make go-live    # Full production preparation + launch"
	@echo "  2. make no-launch  # Prepare for production without launching"
	@echo ""
	@echo "For help: make help"
	@echo ""
	@echo "Transform your ideas into revenue-generating content automatically! 🎯"
	@echo ""

# Go-Live Commands
go-live:
	@echo "🚀 Running full go-live preparation..."
	@$(PYTHON) fix_python_syntax.py --go-live --port $(PORT)

no-launch:
	@echo "🚀 Running go-live preparation without launch..."
	@$(PYTHON) fix_python_syntax.py --go-live --no-launch

fix-syntax:
	@echo "🔧 Fixing Python syntax issues..."
	@$(PYTHON) fix_python_syntax.py .

venv-clean:
	@echo "🧹 Cleaning virtualenv and caches..."
	@rm -rf $(VENV)
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

deps-install:
	@echo "📦 Installing dependencies..."
	@if [ -f requirements-m1.txt ]; then \
		echo "Installing Apple Silicon optimized dependencies..."; \
		$(VENV_PIP) install -U pip setuptools wheel; \
		$(VENV_PIP) install -r requirements-m1.txt; \
	else \
		echo "Installing requirements.txt..."; \
		$(VENV_PIP) install -U pip setuptools wheel; \
		$(VENV_PIP) install -r requirements.txt; \
	fi
