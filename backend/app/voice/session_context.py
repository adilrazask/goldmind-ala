"""Session Context & Conversational History Manager."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

class ConversationSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now(timezone.utc)
        self.last_active = self.created_at
        self.last_symbol: Optional[str] = None
        self.last_secondary_symbol: Optional[str] = None
        self.last_timeframe: Optional[str] = None
        self.last_intent: Optional[str] = None
        self.turns: List[Dict[str, Any]] = []

    def add_turn(self, user_text: str, intent: str, symbol: Optional[str], timeframe: Optional[str], response_text: str):
        self.last_active = datetime.now(timezone.utc)
        if symbol:
            if self.last_symbol and self.last_symbol != symbol:
                self.last_secondary_symbol = self.last_symbol
            self.last_symbol = symbol
        if timeframe:
            self.last_timeframe = timeframe
        self.last_intent = intent

        self.turns.append({
            "timestamp": self.last_active.isoformat(),
            "user_text": user_text,
            "intent": intent,
            "symbol": symbol,
            "timeframe": timeframe,
            "response": response_text
        })
        if len(self.turns) > 20:
            self.turns = self.turns[-20:]

    def get_context(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "last_symbol": self.last_symbol,
            "last_secondary_symbol": self.last_secondary_symbol,
            "last_timeframe": self.last_timeframe,
            "last_intent": self.last_intent,
            "turn_count": len(self.turns)
        }

class SessionContextManager:
    def __init__(self):
        self._sessions: Dict[str, ConversationSession] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> ConversationSession:
        sid = session_id or "default_session"
        if sid not in self._sessions:
            self._sessions[sid] = ConversationSession(sid)
        return self._sessions[sid]

    def reset_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

session_manager = SessionContextManager()
