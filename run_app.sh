#!/usr/bin/env bash
# GoldMind ALA — High-Performance Startup Script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================="
echo "        GOLDMIND ALA — AUTONOMOUS LEARNING AGENT & QUANT LAB    "
echo "================================================================="

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# Ensure frontend build exists
if [ ! -d "frontend/dist" ]; then
    echo "Building frontend production assets..."
    (cd frontend && npm install && npm run build)
fi

PORT="${1:-8000}"
HOST="127.0.0.1"

echo "Checking port $PORT..."
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "Notice: Port $PORT is currently in use by another process."
    PORT="8888"
    echo "Switching to alternative port: http://$HOST:$PORT"
fi

echo "Starting unified GoldMind ALA Server on http://$HOST:$PORT ..."
echo "Serving React 19 Quant Terminal + FastAPI REST API + SQLite Database"
echo "================================================================="

PYTHONPATH=. .venv/bin/python3 main.py server --host "$HOST" --port "$PORT"
