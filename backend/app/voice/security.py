"""Voice Security: Passphrase verification, rate limiting, and temporary lockout."""
from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from backend.app.voice.config import voice_settings

class VoiceSecurityManager:
    def __init__(self):
        # In-memory rate limiting and lockout state per session/identifier
        self.failed_attempts: Dict[str, int] = {}
        self.lockout_until: Dict[str, float] = {}

    def is_locked_out(self, session_id: str) -> Tuple[bool, int]:
        """Returns (is_locked, remaining_seconds)."""
        now = time.time()
        lock_time = self.lockout_until.get(session_id, 0)
        if now < lock_time:
            remaining = int(lock_time - now)
            return True, remaining
        return False, 0

    def verify_attempt(self, session_id: str, candidate_passphrase: str) -> Tuple[bool, str]:
        """Verifies candidate passphrase with constant-time comparison, rate limiting, and lockout."""
        if not voice_settings.passphrase_enabled:
            return True, "Passphrase verification disabled by configuration."

        # Check existing lockout
        is_locked, remaining = self.is_locked_out(session_id)
        if is_locked:
            return False, f"Voice security locked out. Too many failed attempts. Try again in {remaining} seconds."

        if not candidate_passphrase or not candidate_passphrase.strip():
            return False, "Passphrase is required."

        is_valid = voice_settings.verify_passphrase(candidate_passphrase)
        if is_valid:
            # Reset failures on success
            self.failed_attempts[session_id] = 0
            return True, "Passphrase verified successfully."

        # Increment failure count
        current_fails = self.failed_attempts.get(session_id, 0) + 1
        self.failed_attempts[session_id] = current_fails

        if current_fails >= voice_settings.max_failed_attempts:
            lockout_expiry = time.time() + voice_settings.lockout_duration_seconds
            self.lockout_until[session_id] = lockout_expiry
            return False, f"Maximum failed attempts exceeded ({current_fails}). Voice security locked out for {voice_settings.lockout_duration_seconds} seconds."

        remaining_tries = voice_settings.max_failed_attempts - current_fails
        return False, f"Invalid passphrase. {remaining_tries} attempt(s) remaining before lockout."

    def reset_lockout(self, session_id: str):
        """Administrative unlock for session."""
        self.failed_attempts[session_id] = 0
        if session_id in self.lockout_until:
            del self.lockout_until[session_id]

voice_security = VoiceSecurityManager()
