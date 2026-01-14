# Critical Infrastructure

**Everything you need to run your place. No bullshit.**

Critical Infrastructure is a venue management system for collectives and other folk who actually work and run venues. Public website, event calendar, staff scheduling, point of sale, inventory tracking, and internal comms - all in one Django app.
Built by people who know that running a space means you mostly don't know where most of your stuff is and that keeping records across teams is a nightmare.

This fixes that.

---

## Install (Local Dev)

1) Copy the environment file:
```bash
cp .env.example .env
```

2) Run setup (creates venv, installs deps, migrates):
```bash
./bin/setup
```

3) Start the dev server:
```bash
./bin/dev
```

Open **http://127.0.0.1:8000** — log in with `admin` / `admin123` (dev only)

> **Windows?** `python bin\setup` and `python bin\dev`

---

## Run Modes

- **Development**: `./bin/dev` (Django runserver, dev defaults)
- **Production-like**: Docker Compose (Gunicorn, Postgres, Redis)

The mode is controlled by `DJANGO_ENV` in `.env` (`development`, `staging`, `production`).

---

## Deploy (Docker Compose)

1) Copy and edit environment:
```bash
cp .env.example .env
```

Set at least:
```env
DJANGO_ENV=production
DJANGO_DEBUG=False
SECRET_KEY=change-this
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgres://postgres:postgres@db:5432/postgres
REDIS_URL=redis://redis:6379/0
```

2) Build and start services:
```bash
docker compose up -d --build
```

3) Run migrations and collect static files:
```bash
docker compose exec web ./bin/manage migrate
docker compose exec web ./bin/manage collectstatic --noinput
```

4) Create a production admin user:
```bash
docker compose exec web ./bin/manage createsuperuser
```

**Optional (Caddy HTTPS):**
```bash
docker compose --profile live up -d --build
```
Set `DOMAIN` and `ACME_EMAIL` in `.env` for TLS.

---

## What's Inside

### Public-Facing
- **Event calendar** — recurring events, one-offs, the whole deal
- **Customizable themes** — make it yours
- **Page builder** — CMS that doesn't suck
- **Artist profiles** — bands, DJs, whoever

### Staff Tools
- **Shift scheduling** — templates, assignments, the boring stuff automated
- **Point of sale** — multi-payment, discounts, actually usable
- **Inventory** — bar stock, merch, know what you have
- **Internal comms** — messages, email, all in one place
- **Asset manager** — photos, videos, documents organized
- **Venue maps** — floorplans for when people ask "where's the bathroom?"

### Tech That Works
- **Django 5.2** — because it's 2025 and PHP is dead
- **PostgreSQL or SQLite** — your call
- **HTMX** — dynamic UI without webpack hell
- **REST API** — Django REST Framework
- **Background jobs** — Celery + Redis for the slow stuff

---

## Daily Commands

```bash
./bin/dev              # Start the server
./bin/update           # Pull changes, update dependencies, run migrations
./bin/test             # Run tests
./bin/console          # Django shell (shell_plus if you have it)
./bin/manage migrate   # Migrations
```

### Before Committing
```bash
./bin/format           # Auto-format (black + ruff)
./bin/check            # Lint, types, the works
```

### Before Pushing
```bash
./bin/ci               # Full CI suite locally—catch it before GitHub does
```

---

## Structure

```
app/
├── events/      # Events, recurring stuff, tickets
├── shifts/      # Staff scheduling
├── pos/         # Point of sale
├── menu/        # Food and drinks
├── merch/       # Merch catalog
├── inventory/   # Stock tracking
├── bands/       # Artists/performers
├── comms/       # Messaging + email
├── assets/      # File manager
├── pages/       # CMS pages
├── cms/         # Dashboard
├── users/       # Profiles, perms
└── setup/       # Settings
```

---

## Config

Critical Infrastructure uses environment variables. Copy `.env.example` to `.env`:

```env
DJANGO_ENV=[development|staging|production]
DJANGO_DEBUG=True
SECRET_KEY=change-this-in-production
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Docs

- **[Development Guide](DEVELOPMENT.md)** — Testing, code quality, deep dives
- **[Architecture](ARCHITECTURE.md)** — How it's built
- **[Contributing](CONTRIBUTING.md)** — Join in
- **[Security](SECURITY_AUDIT_REPORT.md)** — Don't get hacked
- **[Coding Conventions](CODING_CONVENTIONS.md)** — Code style
- **[bin/ Scripts](bin/README.md)** — Tool docs

---

## Requirements

- **Python 3.11+** (3.11, 3.12, 3.13 all work)
- **Git**
- **Docker** (optional, for PostgreSQL)

---

## Platform Notes

Scripts work everywhere. Same commands, same results.

**Unix/Mac:**
```bash
./bin/setup
./bin/dev
```

**Windows:**
```cmd
python bin\setup
python bin\dev
```

---

## Help

- `./bin/manage --help` — Django commands
- `make help` — Quick ref (Unix/Mac)

## License

[Your license here]
