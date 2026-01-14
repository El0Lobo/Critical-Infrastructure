# Development Scripts

Platform-agnostic development scripts for this Django project. These scripts work identically on Windows, Linux, and macOS.

## Quick Start

### Initial Setup

Run this once to set up your development environment:

**Unix/Linux/macOS:**
```bash
./bin/setup
```

**Windows (Command Prompt):**
```cmd
python bin\setup
```

**Windows (PowerShell):**
```powershell
python bin\setup
```

This will:
- Create a Python virtual environment (`.venv/`)
- Install all dependencies from `requirements.txt`
- Run database migrations
- Create a development admin user (username: `admin`, password: `admin123`)
- Set up your `.env` file (if `.env.sample` exists)

### Update After Pulling Changes

Run this after pulling changes from git:

**Unix/Linux/macOS:**
```bash
./bin/update
```

**Windows:**
```cmd
python bin\update
```

This will pull the latest changes, update dependencies (if needed), and run migrations.

### Start Development Server

**Unix/Linux/macOS:**
```bash
./bin/dev
```

**Windows:**
```cmd
python bin\dev
```

Server will be available at: http://127.0.0.1:8000/

You can pass arguments to customize the server:
```bash
./bin/dev 0.0.0.0:8080  # Run on different host/port
```

## Available Scripts

### `bin/setup`
Complete project setup - virtual environment, dependencies, migrations, and admin user.

**Usage:**
```bash
./bin/setup              # Unix
python bin\setup         # Windows
```

**What it does:**
- Creates Python virtual environment (`.venv/`)
- Checks if venv is in sync and rebuilds if needed
- Installs all dependencies from `requirements.txt` and `requirements-dev.txt`
- Sets up `.env` file from `.env.sample`
- Runs database migrations
- Creates development admin user (`admin`/`admin123`)

### `bin/update`
Update an existing installation after pulling changes from git.

**Usage:**
```bash
./bin/update             # Unix
python bin\update        # Windows
```

**What it does:**
- Pulls latest changes from your current git branch
- Detects if `requirements.txt` changed and updates dependencies
- Runs database migrations

**Perfect for:**
- After pulling changes from teammates
- Syncing with upstream changes
- Updating your local dev environment

**Note:** This only updates dependencies if requirements files have changed, making it much faster than re-running setup.

### `bin/dev`
Start the Django development server.

**Usage:**
```bash
./bin/dev                # Unix - default (127.0.0.1:8000)
./bin/dev 0.0.0.0:8080  # Unix - custom host/port

python bin\dev           # Windows - default
python bin\dev 8080      # Windows - custom port
```

### `bin/test`
Run Django tests.

**Usage:**
```bash
./bin/test               # Unix - run all tests
./bin/test myapp         # Unix - test specific app
./bin/test --keepdb      # Unix - keep test database

python bin\test          # Windows - run all tests
python bin\test myapp    # Windows - test specific app
```

**Common test options:**
- `--keepdb` - Preserve test database between runs (faster)
- `--parallel` - Run tests in parallel
- `--failfast` - Stop on first failure
- `--verbosity=2` - More detailed output

### `bin/console`
Launch Django shell (auto-detects and uses `shell_plus` if `django-extensions` is installed).

**Usage:**
```bash
./bin/console            # Unix
python bin\console       # Windows
```

### `bin/manage`
Run any Django management command.

**Usage:**
```bash
./bin/manage <command> [args]         # Unix
python bin\manage <command> [args]    # Windows
```

**Examples:**
```bash
./bin/manage migrate
./bin/manage createsuperuser
./bin/manage collectstatic
./bin/manage makemigrations
./bin/manage showmigrations
./bin/manage check
```

### `bin/lint`
Check code quality with ruff (fast modern linter).

**Usage:**
```bash
./bin/lint               # Unix - check for issues
./bin/lint --fix         # Unix - auto-fix safe issues

python bin\lint          # Windows - check for issues
python bin\lint --fix    # Windows - auto-fix safe issues
```

### `bin/format`
Format code with black and ruff (import sorting).

**Usage:**
```bash
./bin/format            # Unix - format all code
python bin\format       # Windows - format all code
```

This command runs:
1. `black` - Code formatter
2. `ruff` - Import sorting and auto-fixes

### `bin/check`
Run all code quality checks (format, lint, type-check).

**Usage:**
```bash
./bin/check             # Unix - run all checks
python bin\check        # Windows - run all checks
```

This command runs:
1. **ruff format** - Check code formatting
2. **ruff check** - Check code quality
3. **mypy** - Check type hints (non-blocking)

Perfect for running before commits!

### `bin/ci`
Simulate the full CI pipeline locally.

**Usage:**
```bash
./bin/ci                # Unix - run full CI checks
python bin\ci           # Windows - run full CI checks
```

This command runs the same checks as GitHub Actions:
1. Code formatting (ruff format)
2. Linting (ruff check)
3. Type checking (mypy)
4. Security scan (bandit)
5. Tests (pytest)

Great for catching issues before pushing!

### `bin/reset`
Nuclear option - completely reset the project to a fresh state.

**Usage:**
```bash
./bin/reset             # Unix - reset everything
python bin\reset        # Windows - reset everything
```

**What it does:**
1. Removes the database (`db.sqlite3`)
2. Removes the virtual environment (`.venv`)
3. Removes environment config (`.env`)
4. Runs `bin/setup` to create everything fresh
5. Runs `bin/ci` to verify everything works

**Warning:** This is destructive! It will ask for confirmation before proceeding.

**Perfect for:**
- Starting completely fresh
- Fixing broken environments
- Testing the setup process
- Recovering from migration issues

## Platform Notes

### Unix/Linux/macOS
All scripts have the executable bit set (`chmod +x`) and include proper shebangs, so you can run them directly:
```bash
./bin/setup
./bin/dev
./bin/test
```

### Windows
Scripts can be run using Python:
```cmd
python bin\setup
python bin\dev
python bin\test
```

Or directly (if `.py` files are associated with Python):
```cmd
bin\setup
bin\dev
bin\test
```

## Features

✓ **Platform Detection** - Automatically detects Windows, Linux, or macOS
✓ **Modern TUI** - Beautiful terminal UI powered by Rich library
✓ **Battle-Tested Libraries** - Uses `rich` for gorgeous output and formatting
✓ **Demoscene-Ready** - ASCII art headers and colorful effects
✓ **Error Handling** - Clear error messages with visual indicators
✓ **Virtual Environment** - Automatic venv detection and management
✓ **No Activation Needed** - Scripts use the venv Python directly
✓ **Executable on Unix** - Pre-chmod'd for convenience
✓ **Code Quality Tools** - Built-in linting, formatting, and type checking
✓ **CI Simulation** - Run the full GitHub Actions pipeline locally
✓ **Django Best Practices** - Follows official Django recommendations
✓ **Easy Reset** - Nuclear option to start completely fresh

## Troubleshooting

### Virtual environment not found
If you see "Virtual environment not found", run:
```bash
./bin/setup
```

### Permission denied (Unix)
If scripts aren't executable:
```bash
chmod +x bin/*
```

### Python not found (Windows)
Ensure Python 3.8+ is installed and in your PATH. Try:
```cmd
python --version
```

### Module not found errors
Run setup again to install dependencies:
```bash
./bin/setup
```

## Development Credentials

After running `bin/setup`, you can log in with:
- **Username:** `admin`
- **Password:** `admin123`

**Important:** Change these credentials in production!

## Requirements

- Python 3.8 or higher
- Git (for cloning the repository)
- Internet connection (for installing dependencies)

## Architecture

All scripts are written in Python for maximum portability. They:
1. Detect the current platform (Windows/Unix)
2. Locate the virtual environment's Python executable
3. Run Django management commands using the venv Python
4. Provide colored, formatted output for better UX

No shell activation is needed - scripts directly invoke the virtual environment's Python interpreter.
