"""Production Entrypoint for GoldMind ALA on Cloud Platforms (Railway, Render, Fly.io)."""
import os
import sys
from pathlib import Path

# Ensure required storage directories exist before DB initialization
root_dir = Path(__file__).resolve().parent
(root_dir / "backend" / "data").mkdir(parents=True, exist_ok=True)
(root_dir / "data").mkdir(parents=True, exist_ok=True)

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"==================================================", flush=True)
    print(f" GoldMind ALA Production Engine Starting...", flush=True)
    print(f" Binding: 0.0.0.0:{port}", flush=True)
    print(f" Healthcheck Endpoint: http://0.0.0.0:{port}/health", flush=True)
    print(f"==================================================", flush=True)
    
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, log_level="info")
