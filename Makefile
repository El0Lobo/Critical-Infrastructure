.PHONY: help setup dev test lint format check ci console manage clean install install-dev migrate makemigrations runserver shell db-reset collectstatic docker-build docker-up docker-down pre-commit

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# NOTE: This Makefile is a convenience wrapper around the bin/ scripts.
# All core functionality is implemented in platform-agnostic Python scripts in bin/
# You can use either approach:
#   - make test    (wrapper, Unix/Mac only)
#   - ./bin/test   (direct, all platforms including Windows)

help: ## Show this help message
	@echo "$(CYAN)╔═══════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║  $(GREEN)El0lobo CMS - Development Commands$(CYAN)            ║$(NC)"
	@echo "$(CYAN)╚═══════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)TIP: All commands delegate to bin/ scripts$(NC)"
	@echo "     Windows users: use 'python bin\<command>' directly"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(CYAN)For full documentation, see: bin/README.md$(NC)"

# Core Development Commands (delegate to bin/)
setup: ## Complete dev setup (venv, deps, migrations, admin)
	./bin/setup

dev: ## Start development server
	./bin/dev

runserver: ## Start Django development server (alias for dev)
	./bin/dev

test: ## Run tests (pytest if available, else Django)
	./bin/test

console: ## Open Django shell (shell_plus if available)
	./bin/console

shell: ## Open Django shell (alias for console)
	./bin/console

manage: ## Run Django management command (usage: make manage ARGS="command")
	./bin/manage $(ARGS)

# Code Quality Commands (delegate to bin/)
lint: ## Run linter (ruff)
	./bin/lint

lint-fix: ## Run linter with auto-fix
	./bin/lint --fix

format: ## Format code with Ruff
	./bin/format

check: ## Run all quality checks (format, lint, types)
	./bin/check

ci: ## Simulate full CI pipeline locally
	./bin/ci

# Testing Variants
test-cov: ## Run tests with HTML coverage report
	./bin/test --cov --cov-report=html
	@python -m webbrowser htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null

test-fast: ## Run tests without coverage
	./bin/test --no-cov

test-parallel: ## Run tests in parallel
	./bin/test -n auto

# Django Management
migrate: ## Run database migrations
	./bin/manage migrate

makemigrations: ## Create new migrations
	./bin/manage makemigrations

create-admin: ## Create development admin user (admin/admin123)
	./bin/manage create_dev_admin

collectstatic: ## Collect static files
	./bin/manage collectstatic --noinput

# Database Operations
db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)WARNING: This will delete your database!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f db.sqlite3; \
		./bin/manage migrate; \
		./bin/manage create_dev_admin; \
		echo "$(GREEN)✓ Database reset complete!$(NC)"; \
	fi

# Pre-commit Hooks
pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

# Installation (Legacy - prefer using bin/setup)
install: ## Install production dependencies only
	pip install -r requirements.txt

install-dev: ## Install development dependencies + hooks
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

# Docker Commands
docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-shell: ## Open shell in Django container
	docker-compose exec web bash

# Cleanup
clean: ## Remove Python cache files and build artifacts
	@echo "$(CYAN)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"
