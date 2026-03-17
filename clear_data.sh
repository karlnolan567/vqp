#!/bin/bash

# VQP Prototype - Data Reset Script
echo "------------------------------------------------"
echo "🗑️  Clearing VQP Prototype Data..."
echo "------------------------------------------------"

# 1. Kill any running streamlit processes to unlock DB files
pkill -f streamlit || true

# 2. Remove SQLite database files
if [ -f "vqp_prototype.db" ]; then
    rm vqp_prototype.db
    echo "✅ Main database (vqp_prototype.db) removed."
fi

if [ -f "test_vqp.db" ]; then
    rm test_vqp.db
    echo "✅ Test database (test_vqp.db) removed."
fi

# 3. Optional: Re-initialize the database with base signals
# The app.py calls init_db() which recreates the schema and seeds signals.
echo "🔄 Re-initializing clean database structure..."
python3 -c "from models import init_db; init_db()"

echo "------------------------------------------------"
echo "✨ Data reset complete. System is now in a clean state."
echo "------------------------------------------------"
