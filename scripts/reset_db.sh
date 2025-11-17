#!/bin/bash
# Reset database and create fresh migrations
# With default message
# ./scripts/reset_db.sh
#
# With custom message
# ./scripts/reset_db.sh "add department column to warnings"

set -e  # Exit on error

echo "⚠️  WARNING: This will delete the database and all data!"
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Aborted."
    exit 1
fi

echo "🗑️  Removing database..."
rm -f data/weather.db

echo "🗑️  Removing old migrations..."
rm -f alembic/versions/*.py

echo "📝 Creating new migration..."
poetry run alembic revision --autogenerate -m "${1:-initial schema}"

echo "⬆️  Applying migration..."
poetry run alembic upgrade head

echo "✅ Database reset complete!"
