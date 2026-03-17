#!/bin/bash

# VQP Prototype - Full System Reset Script
echo "------------------------------------------------"
echo "💥 Performing Nuclear Reset of VQP Prototype..."
echo "------------------------------------------------"

# 1. Terminate active processes
echo "🛑 Stopping active processes..."
pkill -f streamlit || true
pkill -f python3 || true

# 2. Remove all database files
echo "🗑️  Removing all SQLite databases..."
rm -f *.db
echo "✅ Databases cleared."

# 3. Clean up Python cache
echo "🧹 Cleaning Python bytecode and cache..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
echo "✅ Cache cleared."

# 4. Re-initialize the core database structure
echo "🔄 Re-initializing base signals (S001-S008)..."
python3 -c "from models import init_db; init_db()"
echo "✅ Base signals seeded."

echo "------------------------------------------------"
echo "✨ System is now in a pristine state."
echo "------------------------------------------------"
