#!/usr/bin/env bash
# Exit immediately if any command fails
set -e

echo "=== 1. Installing Python Dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== 2. Building React Frontend Production Assets ==="
cd frontend
npm install
npm run build
cd ..

echo "=== 3. Initializing GoldMind ALA Database ==="
python -c "from backend.app.database.session import init_db; init_db()"

echo "=== Build Complete! Unified Fullstack Application Ready ==="
