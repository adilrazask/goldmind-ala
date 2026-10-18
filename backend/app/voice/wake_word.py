"""Optional Wake-Word Background Service & State Manager."""
from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from backend.app.voice.config import voice_settings

class WakeWordService:
    def __init__(self):
        self.is_monitoring: bool = False
        self.last_detection: Optional[str] = None
        self.active_wake_words = voice_settings.wake_words
        self.privacy_mode = {
            "continuous_recording": False,
            "raw_audio_stored": False,
            "privacy_guarantee": "Microphone stream is processed locally in-memory; audio is dropped immediately."
        }

    def start_monitoring(self) -> Dict[str, Any]:
        """Enables wake-word listening with explicit user permission."""
        self.is_monitoring = True
        return {
            "is_monitoring": True,
            "message": "Wake-word background monitoring activated.",
            "wake_words": self.active_wake_words,
            "privacy": self.privacy_mode
        }

    def stop_monitoring(self) -> Dict[str, Any]:
        """Disables microphone listening immediately."""
        self.is_monitoring = False
        return {
            "is_monitoring": False,
            "message": "Wake-word background monitoring disabled."
        }

    def check_audio_stream_chunk(self, transcript_chunk: str) -> Dict[str, Any]:
        """Detects whether incoming transcription chunk contains a configured wake-word."""
        if not self.is_monitoring:
            return {"wake_word_detected": False, "is_monitoring": False}

        clean = transcript_chunk.strip().lower()
        for ww in self.active_wake_words:
            pattern = r"\b" + re.escape(ww) + r"\b"
            if re.search(pattern, clean):
                self.last_detection = datetime.now(timezone.utc).isoformat()
                # Strip wake-word from command payload
                command_remainder = re.sub(pattern, "", clean).strip()
                return {
                    "wake_word_detected": True,
                    "wake_word": ww,
                    "remainder_command": command_remainder,
                    "timestamp": self.last_detection
                }

        return {"wake_word_detected": False, "is_monitoring": True}

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_monitoring": self.is_monitoring,
            "wake_words": self.active_wake_words,
            "last_detection": self.last_detection,
            "privacy": self.privacy_mode
        }

wake_word_service = WakeWordService()
