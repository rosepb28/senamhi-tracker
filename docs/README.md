# 📚 SENAMHI Tracker Documentation

Complete documentation for Peru weather monitoring system.

## 🚀 Quick Start

**Local Development:**

```bash
git clone https://github.com/rosepb28/senamhi-tracker.git
cd senamhi-tracker
poetry install
poetry run alembic upgrade head
poetry run senamhi scrape --departments LIMA
poetry run senamhi web
```

**Docker (PostgreSQL + PostGIS):**

```bash
make up              # Start services
make scrape          # Scrape data
make logs            # View logs
make down            # Stop services
```

See [Setup Guide](SETUP.md) for detailed instructions.

## 📖 Documentation

### Getting Started

- **[Setup Guide](SETUP.md)** - Installation and Makefile commands
- **[API Reference](API.md)** - REST API endpoints

### Development

- **[Development Guide](DEVELOPMENT.md)** - Contributing and testing

### Detailed Guides

- **[Configuration](archive/configuration.md)** - Environment variables
- **[Installation](archive/installation.md)** - Detailed setup options
- **[CLI Commands](archive/usage/cli.md)** - Complete command reference
- **[Web Dashboard](archive/usage/web.md)** - Web interface guide
- **[Scheduler](archive/usage/scheduler.md)** - Automated scraping
- **[Geospatial Features](archive/features/geospatial.md)** - PostGIS and maps
- **[Troubleshooting](archive/troubleshooting.md)** - Common issues

## 🛠️ Makefile Commands

```bash
# Services
make up              # Start Docker services
make down            # Stop services
make restart         # Restart services
make ps              # Show status

# Scraping
make scrape          # Scrape forecasts and warnings
make scrape-warnings # Scrape warnings only

# Database
make migrate         # Run migrations
make db-shell        # PostgreSQL shell

# Development
make shell           # Enter app container
make rebuild         # Rebuild containers
make check           # Run linting and formatting
```

See [Setup Guide](SETUP.md) for complete command list.

## 🎯 Common Workflows

**Daily monitoring:**

```bash
make scrape-warnings
poetry run senamhi warnings active
poetry run senamhi web
```

**Geospatial setup:**

```bash
poetry run senamhi geo download 421
poetry run senamhi geo sync 421
```

**Development:**

```bash
make check                    # Format and lint
poetry run pytest -v          # Run tests
poetry run senamhi web        # Start dashboard
```

## 📊 Project Structure

```text
senamhi-tracker/
├── app/                 # Application code
│   ├── cli/            # CLI commands
│   ├── scrapers/       # Data scrapers
│   ├── services/       # Business logic
│   ├── storage/        # Database models
│   ├── scheduler/      # Background jobs
│   └── web/            # Flask web app
├── config/             # YAML configurations
├── docs/               # Documentation
├── tests/              # Test suite
├── Makefile            # Docker shortcuts
└── docker-compose.postgres.yml
```

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/rosepb28/senamhi-tracker/issues)
- **Docs:** [archive/troubleshooting.md](archive/troubleshooting.md)
