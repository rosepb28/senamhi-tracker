#!/bin/bash

# Clean downloaded shapefiles from data/shapefiles/
# Usage: ./dev_tools/clean_shapefiles.sh [--dry-run]

set -e

SHAPEFILES_DIR="data/shapefiles"
DRY_RUN=false

# Parse arguments
if [ "$1" = "--dry-run" ]; then
    DRY_RUN=true
fi

# Check if directory exists
if [ ! -d "$SHAPEFILES_DIR" ]; then
    echo "❌ Directory $SHAPEFILES_DIR does not exist"
    exit 1
fi

# Count files
ZIP_COUNT=$(find "$SHAPEFILES_DIR" -name "*.zip" 2>/dev/null | wc -l)
DIR_COUNT=$(find "$SHAPEFILES_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
TOTAL=$((ZIP_COUNT + DIR_COUNT))

if [ $TOTAL -eq 0 ]; then
    echo "✅ No shapefiles to clean"
    exit 0
fi

echo "📊 Found in $SHAPEFILES_DIR:"
echo "   - ZIP files: $ZIP_COUNT"
echo "   - Directories: $DIR_COUNT"
echo "   - Total items: $TOTAL"

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "🔍 DRY RUN - Would delete:"
    find "$SHAPEFILES_DIR" -mindepth 1 -maxdepth 1 -type f -name "*.zip" -o -type d
    echo ""
    echo "Run without --dry-run to actually delete"
    exit 0
fi

# Confirm deletion
echo ""
read -p "⚠️  Delete all shapefiles? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

# Delete files
echo "🗑️  Deleting shapefiles..."
find "$SHAPEFILES_DIR" -mindepth 1 -maxdepth 1 \( -type f -name "*.zip" -o -type d \) -exec rm -rf {} +

echo "✅ Cleaned $TOTAL item(s) from $SHAPEFILES_DIR"
