# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Developer Experience & Tooling
- **Testing Framework**: pytest and pytest-django for modern testing
  - Configured with sensible defaults in `pyproject.toml`
  - pytest-cov for code coverage tracking
  - pytest-xdist for parallel test execution
  - factory-boy and faker for test data generation
  - Common pytest fixtures in `app/conftest.py`

- **Code Quality Tools**:
  - ruff: Fast Python linter (replaces flake8, isort, pylint)
  - black: Opinionated code formatter (100 char line length)
  - isort: Import sorter configured for Django
  - mypy: Static type checker with django-stubs
  - bandit: Security vulnerability scanner

- **Development Automation**:
  - Comprehensive Makefile with 30+ common developer commands
  - Pre-commit hooks for automated code quality checks
  - `.editorconfig` for consistent editor settings across IDEs

- **CI/CD**:
  - GitHub Actions workflow with:
    - Multi-Python version testing (3.11, 3.12, 3.13)
    - PostgreSQL and Redis services
    - Linting and formatting checks
    - Type checking with mypy
    - Security scanning with bandit
    - Docker image building
    - Codecov integration for coverage tracking

- **Documentation**:
  - Enhanced README.md with comprehensive dev tooling instructions
  - CONTRIBUTING.md with contribution guidelines
  - CHANGELOG.md for tracking project changes
  - Inline documentation in configuration files

- **Configuration**:
  - `pyproject.toml` - Central configuration for all Python tools
  - `requirements-dev.txt` - Development dependencies separate from production
  - `.pre-commit-config.yaml` - Pre-commit hook configuration

#### Development Tools
- django-extensions: Additional management commands (shell_plus, runserver_plus)
- django-debug-toolbar: Debug toolbar for development
- ipython: Enhanced Python REPL
- werkzeug: Better debugger for development

### Changed
- Updated README.md with modern setup instructions and tooling documentation
- Reorganized project documentation for better discoverability
- Enhanced .gitignore with tool-specific cache directories

### Developer Experience Improvements
- One-command setup: `make setup`
- Consistent code style enforced automatically
- Pre-commit hooks prevent committing code that fails quality checks
- Comprehensive test infrastructure ready for expansion
- Type hints support with mypy
- Security scanning integrated into CI

## [0.1.0] - 2025-01-XX

### Added
- Initial project structure with 24 Django apps
- Docker and docker-compose configuration
- Basic setup and dev scripts for multiple platforms
- CMS dashboard and public pages
- User authentication and authorization
- PostgreSQL and Redis support
- Celery for background tasks
- Event management system
- Shift scheduling
- POS, merchandise, and inventory modules
- Blog and pages modules
- Social media integration
- Home Assistant automation
- Maps and door access control

---

## Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security vulnerability fixes
