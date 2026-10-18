# Multi-stage production build for GoldMind ALA
# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Production Runtime
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create required data directories
RUN mkdir -p /app/backend/data /app/data

# Copy application source
COPY backend/ ./backend/
COPY ala/ ./ala/
COPY data/ ./data/
COPY main.py .
COPY start.py .

# Copy built frontend assets from builder
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Informational expose
EXPOSE 8000

# Start via production python entrypoint (handles dynamic $PORT without shell escaping bugs)
CMD ["python", "start.py"]
