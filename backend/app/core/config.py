import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    PROJECT_NAME: str = "GoldMind ALA"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Storage & DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/ala_database.sqlite3")
    
    # Operating Mode & Security
    DEFAULT_OPERATING_MODE: str = os.getenv("ALA_MODE", "RESEARCH_ONLY") # RESEARCH_ONLY, DEMO, LIVE_DISABLED
    ALLOW_LIVE_TRADING: bool = os.getenv("ALA_ENABLE_LIVE_TRADING", "NO") == "YES_I_ACCEPT_RISK"
    LIVE_CONFIRMATION_PHRASE: str = "I UNDERSTAND REAL MONEY RISK"
    KILL_SWITCH_ACTIVE: bool = False
    
    # Risk limits
    MAX_RISK_PER_TRADE_PCT: float = float(os.getenv("ALA_MAX_RISK_PER_TRADE", "0.25"))
    MAX_DAILY_LOSS_PCT: float = float(os.getenv("ALA_MAX_DAILY_LOSS", "1.0"))
    MAX_OPEN_POSITIONS: int = int(os.getenv("ALA_MAX_OPEN_POSITIONS", "3"))
    MAX_SPREAD_POINTS: int = int(os.getenv("ALA_MAX_SPREAD_POINTS", "35"))
    MAX_SLIPPAGE_POINTS: int = int(os.getenv("ALA_MAX_SLIPPAGE_POINTS", "20"))
    DAILY_START_EQUITY: float = float(os.getenv("ALA_DAILY_START_EQUITY", "10000.0"))
    
    # Model configuration
    USE_OLLAMA: bool = os.getenv("ALA_USE_OLLAMA", "0").lower() in {"1", "true", "yes"}
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    
    # Scheduler & Resource limits
    MAX_CONCURRENT_EXPERIMENTS: int = int(os.getenv("ALA_MAX_CONCURRENT_JOBS", "2"))
    RESEARCH_INTERVAL_SECONDS: int = int(os.getenv("ALA_RESEARCH_INTERVAL", "60"))
    AUTO_RESEARCH_ACTIVE: bool = False

settings = Settings()
