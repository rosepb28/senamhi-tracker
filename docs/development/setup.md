# 🛠️ Development Setup

Quick guide for contributors.

## Setup
```bash
# Clone and install
git clone https://github.com/rosepb28/senamhi-tracker.git
cd senamhi-tracker
poetry install

# Setup database
poetry run alembic upgrade head

# Configure
cp .env.example .env
```

## Running Tests
```bash
# All tests
poetry run pytest -v

# Specific file
poetry run pytest tests/test_warnings.py -v

# With coverage
poetry run pytest --cov=app --cov-report=html
```

**Note:** Tests use SQLite and skip PostGIS-dependent tests when PostgreSQL is configured.

## Code Quality
```bash
# Format and lint (combined)
poetry run ruff check . --fix && poetry run ruff format .

# Or separately
poetry run ruff check . --fix    # Lint and auto-fix
poetry run ruff format .          # Format code

# Pre-commit hooks
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## Database Migrations
```bash
# Create migration
./dev_tools/new_migration.sh "add_new_field"

# Apply
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1

# Reset (⚠️ destructive)
./dev_tools/reset_db.sh
```

## Project Structure
```
app/
├── cli/              # Typer commands
├── scrapers/         # SENAMHI scrapers + shapefiles
├── services/         # Business logic
├── storage/          # Database models + CRUD
├── scheduler/        # Background jobs
└── web/              # Flask web app

config/               # YAML configs
data/                 # SQLite DB + shapefiles
docs/                 # Documentation
scripts/              # Maintenance scripts
tests/                # Test suite
```

## Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feat/amazing-feature`
3. Make changes
4. Run tests: `poetry run pytest -v`
5. Format code: `poetry run ruff format .`
6. Commit: `git commit -m "feat: add amazing feature"`
7. Push: `git push origin feat/amazing-feature`
8. Open Pull Request

### Commit Convention
```
feat: Add new feature
fix: Bug fix
docs: Documentation
test: Add tests
refactor: Code refactoring
chore: Maintenance
```

## Useful Commands
```bash
# Start web server
poetry run senamhi web

# Run scraper
poetry run senamhi scrape --departments LIMA

# Start scheduler
poetry run senamhi daemon start

# View logs
tail -f logs/scheduler.log
```
