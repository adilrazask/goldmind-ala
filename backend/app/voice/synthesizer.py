"""Text-to-Speech & Spoken Summary Synthesizer."""
from __future__ import annotations
from typing import Dict, Any, Optional

class SpeechSynthesizerService:
    def __init__(self):
        self.disclaimer = "Simulated results are not evidence of future market profitability."

    def build_spoken_summary(self, intent: str, title: str, key_facts: str, symbol: Optional[str] = None) -> str:
        """Formats a concise, clear spoken summary avoiding overly long technical data."""
        prefix = f"GoldMind {title}."
        if symbol:
            prefix = f"GoldMind analysis for {symbol}."
            
        summary = f"{prefix} {key_facts.strip()} Full details are displayed on your terminal."
        return summary

    def sanitize_for_speech(self, text: str) -> str:
        """Removes markdown symbols, URLs, and code blocks for crisp speech synthesis."""
        clean = text.replace("**", "").replace("*", "").replace("`", "")
        clean = clean.replace("###", "").replace("##", "").replace("#", "")
        clean = clean.replace("•", "").replace("---", "")
        return " ".join(clean.split())

speech_synthesizer = SpeechSynthesizerService()
