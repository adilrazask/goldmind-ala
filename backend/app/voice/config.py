"""Configuration and security settings for the GoldMind ALA Voice Command System."""
from __future__ import annotations
import os
import hashlib
import secrets
from pathlib import Path

VOICE_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
VOICE_DATA_DIR.mkdir(parents=True, exist_ok=True)

class VoiceSettings:
    def __init__(self):
        # Default secure passphrase: "GoldMind secure command"
        default_phrase = os.getenv("ALA_VOICE_PASSPHRASE", "GoldMind secure command")
        self.salt = os.getenv("ALA_VOICE_SALT", secrets.token_hex(16))
        self.passphrase_hash = self.hash_passphrase(default_phrase, self.salt)
        self.passphrase_enabled = os.getenv("ALA_VOICE_PASSPHRASE_ENABLED", "true").lower() in ("true", "1", "yes")
        
        # Security & Lockout
        self.max_failed_attempts = int(os.getenv("ALA_VOICE_MAX_FAILURES", "3"))
        self.lockout_duration_seconds = int(os.getenv("ALA_VOICE_LOCKOUT_SEC", "300"))
        
        # Wake word
        self.wake_words = ["hey goldmind", "goldmind", "ok goldmind"]
        self.wake_word_enabled = False
        
        # Speech config
        self.default_language = os.getenv("ALA_VOICE_LANG", "en-US")
        self.speech_rate = float(os.getenv("ALA_VOICE_SPEECH_RATE", "1.0"))
        self.speech_voice = os.getenv("ALA_VOICE_SPEECH_VOICE", "default")
        
        # Allowlisted Trading Domain Entities
        self.supported_symbols = ["XAUUSD", "BTCUSD"]
        self.supported_timeframes = {
            "m1": "M1", "1m": "M1", "1 minute": "M1", "1-minute": "M1",
            "m5": "M5", "5m": "M5", "5 minute": "M5", "5-minute": "M5",
            "m15": "M15", "15m": "M15", "15 minute": "M15", "15-minute": "M15",
            "m30": "M30", "30m": "M30", "30 minute": "M30", "30-minute": "M30",
            "h1": "H1", "1h": "H1", "1 hour": "H1", "1-hour": "H1", "hourly": "H1",
            "h4": "H4", "4h": "H4", "4 hour": "H4", "4-hour": "H4",
            "d1": "D1", "1d": "D1", "daily": "D1", "1 day": "D1"
        }
        self.default_timeframe = "M15"

    def hash_passphrase(self, passphrase: str, salt: str) -> str:
        """Derives a secure PBKDF2 HMAC-SHA256 hash for the voice passphrase."""
        return hashlib.pbkdf2_hmac(
            "sha256",
            passphrase.strip().lower().encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100000
        ).hex()

    def verify_passphrase(self, candidate: str) -> bool:
        """Constant-time verification of voice passphrase."""
        candidate_hash = self.hash_passphrase(candidate, self.salt)
        return secrets.compare_digest(candidate_hash, self.passphrase_hash)

    def update_passphrase(self, new_phrase: str) -> None:
        """Updates the passphrase with a fresh random salt."""
        self.salt = secrets.token_hex(16)
        self.passphrase_hash = self.hash_passphrase(new_phrase, self.salt)

voice_settings = VoiceSettings()
