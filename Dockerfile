# GoldMind ALA Production Dockerfile
# Single-stage build — frontend/dist/ is pre-built and committed to git
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create required data directories (SQLite will live here)
RUN mkdir -p /app/backend/data /app/data

# Copy application code
COPY backend/ ./backend/
COPY ala/ ./ala/
COPY data/ ./data/
COPY main.py .
COPY start.py .

# Copy pre-built frontend assets (already in git)
COPY frontend/dist/ ./frontend/dist/

# Railway uses $PORT env var (default 8000)
EXPOSE 8000

# Start via Python entrypoint (reads $PORT dynamically)
CMD ["python", "start.py"]
