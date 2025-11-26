# Makefile

.PHONY: scrape scrape-warnings scrape-forecasts logs up down ps shell restart db-shell web build

# Docker Compose base command
COMPOSE = docker compose -f docker-compose.postgres.yml

# ==================== Scraping ====================

# Scrape both forecasts and warnings
scrape:
	$(COMPOSE) exec senamhi-tracker python -m app.main scrape

# Scrape warnings only
scrape-warnings:
	$(COMPOSE) exec senamhi-tracker python -m app.main scrape warnings

# Scrape forecasts only
scrape-forecasts:
	$(COMPOSE) exec senamhi-tracker python -m app.main scrape forecasts

# Force scrape (replace existing data)
scrape-force:
	$(COMPOSE) exec senamhi-tracker python -m app.main scrape --force

# ==================== Services ====================

# Build images without cache
build:
	$(COMPOSE) build --no-cache

# Build and restart services
rebuild: down build up -d

# Start all services
up:
	$(COMPOSE) up -d

# Stop all services
down:
	$(COMPOSE) down

# Stop and remove volumes (WARNING: deletes all data)
clean:
	$(COMPOSE) down -v

# Restart services
restart:
	$(COMPOSE) restart

# Show service status
ps:
	$(COMPOSE) ps

# View logs (follow mode)
logs:
	$(COMPOSE) logs -f senamhi-tracker

# View all logs
logs-all:
	$(COMPOSE) logs -f

# ==================== Shell Access ====================

# Enter app container shell
shell:
	$(COMPOSE) exec senamhi-tracker /bin/bash

# Enter PostgreSQL shell
db-shell:
	$(COMPOSE) exec postgres psql -U senamhi_user -d senamhi

# ==================== Web Dashboard ====================

# Start web dashboard (local)
web:
	poetry run senamhi web

# ==================== Database ====================

# Run migrations
migrate:
	$(COMPOSE) exec senamhi-tracker alembic upgrade head

# Show migration status
migrate-status:
	$(COMPOSE) exec senamhi-tracker alembic current

# Create new migration
migrate-create:
	$(COMPOSE) exec senamhi-tracker alembic revision --autogenerate -m "$(msg)"

# ==================== CLI Commands ====================

# List locations
list-locations:
	$(COMPOSE) exec senamhi-tracker python -m app.main list

# List warnings
list-warnings:
	$(COMPOSE) exec senamhi-tracker python -m app.main warnings list

# Database status
db-status:
	$(COMPOSE) exec senamhi-tracker python -m app.main status

# Scrape runs history
runs:
	$(COMPOSE) exec senamhi-tracker python -m app.main runs

# Scrape warning details
scrape-details:
	$(COMPOSE) exec senamhi-tracker python -m app.main warnings details $(warning)

# ==================== Geospatial ====================

# Download shapefile for warning
geo-download:
	$(COMPOSE) exec senamhi-tracker python -m app.main geo download $(warning)

# Sync shapefile to database
geo-sync:
	$(COMPOSE) exec senamhi-tracker python -m app.main geo sync $(warning)

# List downloaded shapefiles
geo-list:
	$(COMPOSE) exec senamhi-tracker python -m app.main geo list

# ==================== Code Quality ====================

# Format and lint code
lint:
	poetry run ruff check . --fix
	poetry run ruff format .

# Run pre-commit on all files
pre-commit-all:
	poetry run pre-commit run --all-files

# Run both (without recursion)
check: lint pre-commit-all
	@echo "✓ All checks passed!"

# ==================== Help ====================

help:
	@echo "SENAMHI Tracker - Makefile Commands"
	@echo ""
	@echo "Scraping:"
	@echo "  make scrape              - Scrape forecasts and warnings"
	@echo "  make scrape-warnings     - Scrape warnings only"
	@echo "  make scrape-forecasts    - Scrape forecasts only"
	@echo "  make scrape-force        - Force scrape (replace existing)"
	@echo "  make scrape-details warning=421 - Scrape details for warning"
	@echo ""
	@echo "Services:"
	@echo "  make build               - Build images without cache"
	@echo "  make rebuild             - Stop, rebuild, and restart services"
	@echo "  make up                  - Start Docker services"
	@echo "  make down                - Stop Docker services"
	@echo "  make clean               - Stop and remove volumes (deletes data)"
	@echo "  make restart             - Restart services"
	@echo "  make ps                  - Show service status"
	@echo "  make logs                - View app logs (follow)"
	@echo "  make logs-all            - View all service logs"
	@echo ""
	@echo "Shell Access:"
	@echo "  make shell               - Enter app container"
	@echo "  make db-shell            - Enter PostgreSQL shell"
	@echo ""
	@echo "Database:"
	@echo "  make migrate             - Run migrations"
	@echo "  make migrate-status      - Show migration status"
	@echo "  make migrate-create msg='description' - Create new migration"
	@echo ""
	@echo "CLI:"
	@echo "  make list-locations      - List all locations"
	@echo "  make list-warnings       - List warnings"
	@echo "  make db-status           - Show database status"
	@echo "  make runs                - Show scrape runs history"
	@echo ""
	@echo "Geospatial:"
	@echo "  make geo-download warning=420  - Download shapefile"
	@echo "  make geo-sync warning=420      - Sync shapefile to DB"
	@echo "  make geo-list            - List downloaded shapefiles"
	@echo ""
	@echo "Web:"
	@echo "  make web                 - Start web dashboard (local)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                - Format and lint code"
	@echo "  make pre-commit-all      - Run pre-commit on all files"
	@echo "  make check               - Run all code quality checks"
	@echo ""============================================="
