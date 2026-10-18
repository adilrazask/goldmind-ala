"""Voice Command API Endpoints."""
from __future__ import annotations
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.app.voice.recognizer import speech_recognizer
from backend.app.voice.interpreter import command_interpreter
from backend.app.voice.dispatcher import voice_dispatcher
from backend.app.voice.session_context import session_manager
from backend.app.voice.security import voice_security
from backend.app.voice.wake_word import wake_word_service
from backend.app.voice.config import voice_settings
from backend.app.voice.schema import (
    VoiceCommand, VoiceResponse, PassphraseVerificationRequest,
    PassphraseConfigUpdate, PermissionLevel
)

router = APIRouter(prefix="/voice", tags=["Voice Command System"])

class TranscribeRequest(BaseModel):
    transcript: str
    language: Optional[str] = "en-US"

class CommandExecutionRequest(BaseModel):
    raw_text: str
    passphrase: Optional[str] = None
    session_id: Optional[str] = "default_session"

class WakeWordToggleRequest(BaseModel):
    enable: bool

class WakeWordDetectRequest(BaseModel):
    transcript_chunk: str

@router.get("/status")
def get_voice_status():
    """Returns speech recognition service status, supported languages, and privacy disclosures."""
    speech_stat = speech_recognizer.get_service_status()
    wake_stat = wake_word_service.get_status()
    return {
        "speech": speech_stat,
        "wake_word": wake_stat,
        "passphrase_enabled": voice_settings.passphrase_enabled,
        "supported_symbols": voice_settings.supported_symbols,
        "supported_timeframes": list(set(voice_settings.supported_timeframes.values()))
    }

@router.post("/transcribe")
def normalize_transcription(payload: TranscribeRequest):
    """Cleans speech-to-text transcript, resolves trading terms, and identifies entities."""
    if not payload.transcript or not payload.transcript.strip():
        raise HTTPException(status_code=400, detail="Empty voice transcript received.")
    
    result = speech_recognizer.normalize_trading_transcription(payload.transcript)
    return result

@router.post("/command", response_model=VoiceResponse)
def execute_voice_command(payload: CommandExecutionRequest):
    """Interprets and executes a voice command with session context and security checks."""
    raw_text = payload.raw_text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Command text cannot be empty.")

    sid = payload.session_id or "default_session"
    session = session_manager.get_or_create_session(sid)
    session_ctx = session.get_context()

    # 1. Normalize trading terms
    norm_res = speech_recognizer.normalize_trading_transcription(raw_text)
    clean_text = norm_res["normalized_text"]

    # 2. Interpret command & determine permission level
    cmd: VoiceCommand = command_interpreter.interpret(clean_text, session_context=session_ctx)

    # 3. Check for Passphrase if required for Level 2 Controlled Research
    if cmd.permission_level == PermissionLevel.LEVEL_2_CONTROLLED_RESEARCH and voice_settings.passphrase_enabled:
        if not payload.passphrase:
            return VoiceResponse(
                command_id=f"vcmd_{sid[:6]}",
                intent=cmd.intent.value,
                permission_level=cmd.permission_level.value,
                status="CONFIRMATION_REQUIRED",
                display_text=(
                    f"### 🔐 Passphrase Required\n\n"
                    f"Action **{cmd.intent.value}** is classified as Controlled Research. "
                    f"Please provide your voice passphrase to execute."
                ),
                spoken_summary="This research action requires voice passphrase verification.",
                data={"requires_passphrase": True},
                requires_passphrase=True,
                timestamp=""
            )

        # Verify passphrase
        valid, msg = voice_security.verify_attempt(sid, payload.passphrase)
        if not valid:
            raise HTTPException(status_code=401, detail=msg)

    # 4. Dispatch to actual GoldMind ALA functions
    response: VoiceResponse = voice_dispatcher.dispatch(cmd)

    # 5. Record conversational turn
    session.add_turn(
        user_text=raw_text,
        intent=cmd.intent.value,
        symbol=cmd.symbol,
        timeframe=cmd.timeframe,
        response_text=response.spoken_summary
    )

    return response

@router.post("/passphrase/verify")
def verify_voice_passphrase(payload: PassphraseVerificationRequest):
    """Verifies passphrase with rate limiting and temporary lockout."""
    sid = payload.session_id or "default_session"
    valid, msg = voice_security.verify_attempt(sid, payload.passphrase)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)
    return {"status": "VERIFIED", "message": msg}

@router.post("/passphrase/update")
def update_voice_passphrase(payload: PassphraseConfigUpdate):
    """Updates passphrase or security settings."""
    if voice_settings.passphrase_enabled and payload.current_passphrase:
        valid, msg = voice_security.verify_attempt("admin", payload.current_passphrase)
        if not valid:
            raise HTTPException(status_code=401, detail="Current passphrase incorrect.")

    voice_settings.update_passphrase(payload.new_passphrase)
    voice_settings.passphrase_enabled = payload.enabled
    return {"status": "SUCCESS", "message": "Voice passphrase updated successfully."}

@router.get("/wake-word/status")
def get_wake_word_status():
    return wake_word_service.get_status()

@router.post("/wake-word/toggle")
def toggle_wake_word(payload: WakeWordToggleRequest):
    if payload.enable:
        return wake_word_service.start_monitoring()
    return wake_word_service.stop_monitoring()

@router.post("/wake-word/detect")
def detect_wake_word(payload: WakeWordDetectRequest):
    return wake_word_service.check_audio_stream_chunk(payload.transcript_chunk)
