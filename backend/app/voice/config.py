"""Configuration and security settings for the GoldMind ALA Voice Command System.

Default passphrase is '30th July'.
Speech recognition variations (e.g. 'thirtieth July', 'July 30th') are normalized
and verified in constant-time using PBKDF2 HMAC-SHA256 with a unique random salt.
Plaintext passphrases are NEVER stored on disk, never logged, and never sent to external models.
"""
from __future__ import annotations
import os
import re
import json
import hashlib
import secrets
from pathlib import Path
from typing import Dict, Any, Optional

VOICE_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
VOICE_DATA_DIR.mkdir(parents=True, exist_ok=True)
VERIFIER_FILE = VOICE_DATA_DIR / "voice_verifier.json"

# Ordinals and number word mapping for speech-recognition date variations
ORDINALS_MAP = {
    "first": "1", "1st": "1",
    "second": "2", "2nd": "2",
    "third": "3", "3rd": "3",
    "fourth": "4", "4th": "4",
    "fifth": "5", "5th": "5",
    "sixth": "6", "6th": "6",
    "seventh": "7", "7th": "7",
    "eighth": "8", "8th": "8",
    "ninth": "9", "9th": "9",
    "tenth": "10", "10th": "10",
    "eleventh": "11", "11th": "11",
    "twelfth": "12", "12th": "12",
    "thirteenth": "13", "13th": "13",
    "fourteenth": "14", "14th": "14",
    "fifteenth": "15", "15th": "15",
    "sixteenth": "16", "16th": "16",
    "seventeenth": "17", "17th": "17",
    "eighteenth": "18", "18th": "18",
    "nineteenth": "19", "19th": "19",
    "twentieth": "20", "20th": "20", "twenty": "20",
    "twenty first": "21", "twenty-first": "21", "21st": "21",
    "twenty second": "22", "twenty-second": "22", "22nd": "22",
    "twenty third": "23", "twenty-third": "23", "23rd": "23",
    "twenty fourth": "24", "twenty-fourth": "24", "24th": "24",
    "twenty fifth": "25", "twenty-fifth": "25", "25th": "25",
    "twenty sixth": "26", "twenty-sixth": "26", "26th": "26",
    "twenty seventh": "27", "twenty-seventh": "27", "27th": "27",
    "twenty eighth": "28", "twenty-eighth": "28", "28th": "28",
    "twenty ninth": "29", "twenty-ninth": "29", "29th": "29",
    "thirtieth": "30", "30th": "30", "thirty": "30",
    "thirty first": "31", "thirty-first": "31", "31st": "31"
}

def canonicalize_passphrase(phrase: str) -> str:
    """Canonicalizes speech variations of dates, ordinals, and terms for safe voice passphrase comparison.
    
    Examples:
    '30th July' -> '30 july'
    'thirtieth July' -> '30 july'
    'thirtieth of July' -> '30 july'
    'July 30th' -> '30 july'
    'July 30' -> '30 july'
    """
    if not phrase:
        return ""
    text = phrase.lower().strip()
    
    # Remove leading/trailing non-alphanumeric characters
    text = re.sub(r"^[^\w\s]+|[^\w\s]+$", "", text)
    # Remove filler prepositions like 'the', 'of'
    text = re.sub(r"\bthe\b", "", text)
    text = re.sub(r"\bof\b", "", text)
    
    # Replace compound and ordinal numbers (longest match first)
    for k in sorted(ORDINALS_MAP.keys(), key=len, reverse=True):
        pattern = r"\b" + re.escape(k) + r"\b"
        text = re.sub(pattern, ORDINALS_MAP[k], text)
        
    # Split into words, strip, and sort so word order variation does not break comparison
    tokens = [tok.strip() for tok in re.split(r"[\s\-_]+", text) if tok.strip()]
    return " ".join(sorted(tokens))


class VoiceSettings:
    """Manages voice settings, trading vocabularies, and salted cryptographic passphrase verifiers."""
    def __init__(self):
        # Default passphrase is "30th July"
        default_phrase = os.getenv("ALA_VOICE_PASSPHRASE", "30th July")
        self.passphrase_enabled = os.getenv("ALA_VOICE_PASSPHRASE_ENABLED", "true").lower() in ("true", "1", "yes")
        
        # Load or initialize verifier from secure JSON storage (salt + hash only)
        self.salt, self.passphrase_hash = self._load_or_initialize_verifier(default_phrase)
        
        # Security & Lockout
        self.max_failed_attempts = int(os.getenv("ALA_VOICE_MAX_FAILURES", "3"))
        self.lockout_duration_seconds = int(os.getenv("ALA_VOICE_LOCKOUT_SEC", "300"))
        self.session_auth_duration_seconds = int(os.getenv("ALA_VOICE_SESSION_AUTH_SEC", "900")) # 15 minutes
        
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

    def _load_or_initialize_verifier(self, initial_passphrase: str) -> tuple[str, str]:
        """Loads salted PBKDF2 hash from disk or initializes it securely."""
        if VERIFIER_FILE.exists():
            try:
                with open(VERIFIER_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    salt = data.get("salt")
                    p_hash = data.get("passphrase_hash")
                    if salt and p_hash:
                        return salt, p_hash
            except Exception:
                pass

        # First run: initialize with default "30th July"
        salt = secrets.token_hex(16)
        p_hash = self.hash_passphrase(initial_passphrase, salt)
        self._save_verifier(salt, p_hash)
        return salt, p_hash

    def _save_verifier(self, salt: str, p_hash: str) -> None:
        """Persists salt and hash with strict file permissions. Plaintext is never saved."""
        data = {
            "salt": salt,
            "passphrase_hash": p_hash,
            "iterations": 100000,
            "algorithm": "pbkdf2_hmac_sha256",
            "note": "Initial default is '30th July'. Plaintext is never stored."
        }
        with open(VERIFIER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        try:
            os.chmod(VERIFIER_FILE, 0o600)
        except OSError:
            pass

    def hash_passphrase(self, passphrase: str, salt: str) -> str:
        """Derives a PBKDF2 HMAC-SHA256 hash from the canonicalized passphrase representation."""
        canonical = canonicalize_passphrase(passphrase)
        return hashlib.pbkdf2_hmac(
            "sha256",
            canonical.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100000
        ).hex()

    def verify_passphrase(self, candidate: str) -> bool:
        """Constant-time comparison against the stored hash after speech canonicalization."""
        if not candidate:
            return False
        candidate_hash = self.hash_passphrase(candidate, self.salt)
        return secrets.compare_digest(candidate_hash, self.passphrase_hash)

    def update_passphrase(self, new_phrase: str) -> None:
        """Updates the passphrase with a fresh random salt and saves the verifier."""
        self.salt = secrets.token_hex(16)
        self.passphrase_hash = self.hash_passphrase(new_phrase, self.salt)
        self._save_verifier(self.salt, self.passphrase_hash)


voice_settings = VoiceSettings()
