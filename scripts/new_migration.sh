#!/bin/bash
# Create new migration without deleting database

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/new_migration.sh \"migration message\""
    exit 1
fi

echo "📝 Creating migration: $1"
poetry run alembic revision --autogenerate -m "$1"

echo "⬆️  Applying migration..."
poetry run alembic upgrade head

echo "✅ Migration complete!"
