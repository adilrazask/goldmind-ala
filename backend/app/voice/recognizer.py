"""Speech Recognition & Trading Terminology Normalization."""
from __future__ import annotations
import re
from typing import Dict, Any, List, Optional, Tuple

# Trading Terminology Canonical Mappings & Homophones
TRADING_SYNONYMS = {
    # Symbols
    r"\b(xau\s*usd|x\s*a\s*u\s*u\s*s\s*d|gold\s*spot|gold)\b": "XAUUSD",
    r"\b(btc\s*usd|b\s*t\s*c\s*u\s*s\s*d|bit\s*coin|crypto)\b": "BTCUSD",
    r"\b(eur\s*usd|e\s*u\s*r\s*u\s*s\s*d|euro)\b": "EURUSD",
    
    # Indicators
    r"\b(r\s*s\s*i|relative\s*strength\s*index)\b": "RSI",
    r"\b(e\s*m\s*a|exponential\s*moving\s*average)\b": "EMA",
    r"\b(s\s*m\s*a|simple\s*moving\s*average)\b": "SMA",
    r"\b(a\s*t\s*r|average\s*true\s*range)\b": "ATR",
    r"\b(v\s*w\s*a\s*p|volume\s*weighted\s*average\s*price)\b": "VWAP",
    r"\b(bollinger\s*bands?|b\s*bands?)\b": "Bollinger Bands",
    r"\b(m\s*a\s*c\s*d|moving\s*average\s*convergence\s*divergence)\b": "MACD",
    
    # Order terms
    r"\b(stop\s*loss|s\s*l|stoploss)\b": "stop-loss",
    r"\b(take\s*profit|t\s*p|takeprofit)\b": "take-profit",
    r"\b(draw\s*down|drawdown|max\s*dd)\b": "drawdown",
    r"\b(back\s*test|backtest|back-test)\b": "backtest",
    r"\b(walk\s*forward|walkforward)\b": "walk-forward",
    r"\b(out\s*of\s*sample|o\s*o\s*s)\b": "out-of-sample",
    r"\b(in\s*sample|i\s*s)\b": "in-sample",
    
    # Timeframes
    r"\b(1\s*minute|one\s*minute|m\s*1|1\s*m)\b": "1-minute",
    r"\b(5\s*minutes?|five\s*minutes?|m\s*5|5\s*m)\b": "5-minute",
    r"\b(15\s*minutes?|fifteen\s*minutes?|m\s*15|15\s*m)\b": "15-minute",
    r"\b(30\s*minutes?|thirty\s*minutes?|m\s*30|30\s*m)\b": "30-minute",
    r"\b(1\s*hour|one\s*hour|h\s*1|1\s*h|hourly)\b": "1-hour",
    r"\b(4\s*hours?|four\s*hours?|h\s*4|4\s*h)\b": "4-hour",
    r"\b(1\s*day|one\s*day|daily|d\s*1|1\s*d)\b": "daily"
}

# Hindi Trading Terms (optional bilingual recognition)
HINDI_PHONETIC_MAPPINGS = {
    r"\b(gold|sona|sone)\b": "XAUUSD",
    r"\b(bitcoin|crypto)\b": "BTCUSD",
    r"\b(visheshan|jaanch|analysis|dekho)\b": "analyse",
    r"\b(kya\s*chal\s*raha\s*hai|status|haal)\b": "show status",
    r"\b(rok\s*do|ruk\s*jao|pause)\b": "pause",
    r"\b(shuru\s*karo|chalu\s*karo|resume)\b": "resume"
}

class SpeechRecognizerService:
    def __init__(self):
        self.privacy_policy = {
            "mode": "LOCAL_PREFERRED",
            "browser_engine": "Web Speech API (Chrome/Safari/Edge native, zero 3rd-party audio upload)",
            "server_processing": "Strictly text normalization and structured intent extraction",
            "audio_retention": "No continuous recording or raw audio is persisted to disk."
        }

    def normalize_trading_transcription(self, raw_transcript: str) -> Dict[str, Any]:
        """Cleans transcription errors, normalizes trading terminology, and detects recognized entities."""
        if not raw_transcript or not raw_transcript.strip():
            return {
                "original_text": "",
                "normalized_text": "",
                "detected_entities": {},
                "is_empty": True
            }

        text = raw_transcript.strip()
        detected_entities = {
            "symbols": [],
            "indicators": [],
            "timeframes": [],
            "concepts": []
        }

        # Apply Hindi phonetic maps if present
        for pattern, replacement in HINDI_PHONETIC_MAPPINGS.items():
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Apply Trading terms normalization
        for pattern, replacement in TRADING_SYNONYMS.items():
            if re.search(pattern, text, re.IGNORECASE):
                # Record entity
                if replacement in ["XAUUSD", "BTCUSD", "EURUSD"]:
                    if replacement not in detected_entities["symbols"]:
                        detected_entities["symbols"].append(replacement)
                elif replacement in ["RSI", "EMA", "SMA", "ATR", "VWAP", "Bollinger Bands", "MACD"]:
                    if replacement not in detected_entities["indicators"]:
                        detected_entities["indicators"].append(replacement)
                elif "minute" in replacement or "hour" in replacement or "daily" in replacement:
                    if replacement not in detected_entities["timeframes"]:
                        detected_entities["timeframes"].append(replacement)
                else:
                    if replacement not in detected_entities["concepts"]:
                        detected_entities["concepts"].append(replacement)

                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return {
            "original_text": raw_transcript,
            "normalized_text": text.strip(),
            "detected_entities": detected_entities,
            "is_empty": False
        }

    def get_service_status(self) -> Dict[str, Any]:
        return {
            "status": "ONLINE",
            "default_language": "en-US",
            "supported_languages": ["en-US", "en-GB", "hi-IN"],
            "privacy": self.privacy_policy,
            "trading_terminology_vocab_size": len(TRADING_SYNONYMS)
        }

speech_recognizer = SpeechRecognizerService()
