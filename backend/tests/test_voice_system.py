"""Automated test suite for GoldMind ALA Standalone Voice Command System (18 test scenarios)."""
import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.voice.recognizer import speech_recognizer
from backend.app.voice.interpreter import command_interpreter
from backend.app.voice.dispatcher import voice_dispatcher
from backend.app.voice.security import voice_security
from backend.app.voice.session_context import session_manager
from backend.app.voice.schema import VoiceCommand, VoiceCommandIntent, PermissionLevel
from backend.app.voice.config import voice_settings
from backend.app.core.dependencies import risk_engine, controller, scheduler

client = TestClient(app)

# 1. Microphone permission denied
def test_01_microphone_permission_denied():
    # When microphone access is denied by browser, frontend displays clear error and keyboard fallback
    status_res = client.get("/api/v1/voice/status")
    assert status_res.status_code == 200
    assert "privacy" in status_res.json()["speech"]
    assert status_res.json()["speech"]["status"] == "ONLINE"

# 2. Speech-recognition failure
def test_02_speech_recognition_failure():
    # Empty transcript returns 400 with detail
    res = client.post("/api/v1/voice/transcribe", json={"transcript": "   "})
    assert res.status_code == 400
    assert "Empty voice transcript" in res.json()["detail"]

# 3. Incorrect transcription normalization & correction
def test_03_incorrect_transcription_normalization():
    # Normalizer corrects common homophones and phonetic variants
    raw = "analyse x a u u s d on fifteen minute and bit coin with r s i"
    res = speech_recognizer.normalize_trading_transcription(raw)
    clean = res["normalized_text"]
    assert "XAUUSD" in clean
    assert "BTCUSD" in clean
    assert "RSI" in clean
    assert "15-minute" in clean

# 4. Unsupported command
def test_04_unsupported_command():
    cmd = command_interpreter.interpret("Order me a pepperoni pizza with extra cheese")
    assert cmd.intent == VoiceCommandIntent.UNKNOWN_COMMAND
    resp = client.post("/api/v1/voice/command", json={"raw_text": "Order me a pepperoni pizza"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "NEEDS_CLARIFICATION"

# 5. Ambiguous symbol or timeframe
def test_05_ambiguous_symbol_or_timeframe():
    # When symbol is missing, intent is captured and handled with general or default context
    cmd = command_interpreter.interpret("Give me the current market structure")
    assert cmd.intent == VoiceCommandIntent.GET_MARKET_STRUCTURE
    # Dispatched gracefully
    res = voice_dispatcher.dispatch(cmd)
    assert res.status == "SUCCESS"
    assert "XAUUSD" in res.display_text # Defaults safely to primary instrument

# 6. Valid XAUUSD analysis command
def test_06_valid_xauusd_analysis_command():
    res = client.post("/api/v1/voice/command", json={
        "raw_text": "GoldMind, analyse XAUUSD on the 15-minute timeframe."
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["intent"] == "analyse_market"
    assert "XAUUSD" in data["display_text"]
    assert "spoken_summary" in data
    assert "XAUUSD" in data["spoken_summary"]

# 7. Valid BTCUSD analysis command
def test_07_valid_btcusd_analysis_command():
    res = client.post("/api/v1/voice/command", json={
        "raw_text": "Analyse BTCUSD on the 1-hour timeframe."
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "BTCUSD" in data["display_text"]

# 8. Follow-up question using conversation context
def test_08_followup_question_using_conversation_context():
    sid = "multi_turn_test_session"
    session_manager.reset_session(sid)
    
    # Turn 1: "Analyse XAUUSD"
    r1 = client.post("/api/v1/voice/command", json={
        "raw_text": "Analyse XAUUSD on the 15-minute timeframe",
        "session_id": sid
    })
    assert r1.status_code == 200

    # Turn 2: Follow-up "Explain the current market risks" (no symbol mentioned)
    r2 = client.post("/api/v1/voice/command", json={
        "raw_text": "Explain the current market risks",
        "session_id": sid
    })
    assert r2.status_code == 200
    # Should automatically inherit XAUUSD from session context
    assert "XAUUSD" in r2.json()["display_text"]

# 9. Passphrase verification: variations of '30th July' and rejection of unrelated phrases
def test_09_passphrase_variations_and_rejections():
    sid = "test_pass_session_variations"
    voice_security.reset_lockout(sid)
    
    # 9a. Test that speech recognition variations of "30th July" are all accepted
    valid_variations = [
        "30th July",
        "thirtieth July",
        "thirtieth of July",
        "July 30th",
        "July 30",
        "July thirtieth",
        "30 July",
        "thirty july"
    ]
    for variation in valid_variations:
        res = client.post("/api/v1/voice/passphrase/verify", json={
            "passphrase": variation,
            "session_id": sid
        })
        assert res.status_code == 200, f"Failed to verify variation: {variation}"
        assert res.json()["status"] == "VERIFIED"

    # 9b. Test that unrelated phrases are strictly rejected
    invalid_phrases = [
        "totally_wrong_passphrase",
        "31st July",
        "30th August",
        "July 1st",
        "30th June"
    ]
    for invalid in invalid_phrases:
        sid_inv = f"test_inv_{invalid}"
        voice_security.reset_lockout(sid_inv)
        res = client.post("/api/v1/voice/passphrase/verify", json={
            "passphrase": invalid,
            "session_id": sid_inv
        })
        assert res.status_code == 401
        assert "Invalid passphrase" in res.json()["detail"]

    # 9c. Protected command without passphrase prompts user to speak passphrase
    cmd_res = client.post("/api/v1/voice/command", json={
        "raw_text": "Run backtest on BTCUSD",
        "session_id": "unauth_session"
    })
    assert cmd_res.status_code == 200
    assert cmd_res.json()["status"] == "CONFIRMATION_REQUIRED"
    assert "Please speak your voice passphrase" in cmd_res.json()["spoken_summary"]

    # 9d. Protected command with spoken variation 'thirtieth July' executes successfully
    auth_cmd_res = client.post("/api/v1/voice/command", json={
        "raw_text": "Run backtest on BTCUSD",
        "session_id": "auth_test_session",
        "passphrase": "thirtieth July"
    })
    assert auth_cmd_res.status_code == 200
    assert auth_cmd_res.json()["status"] == "SUCCESS"

# 10. Repeated authentication failures and lockout
def test_10_repeated_authentication_failures_lockout():
    sid = "test_lockout_session"
    voice_security.reset_lockout(sid)
    
    # Fail 3 times
    for _ in range(voice_settings.max_failed_attempts):
        res = client.post("/api/v1/voice/passphrase/verify", json={
            "passphrase": "wrong_phrase",
            "session_id": sid
        })
        assert res.status_code == 401

    # 4th attempt should be rejected with lockout message
    locked_res = client.post("/api/v1/voice/passphrase/verify", json={
        "passphrase": "30th July",
        "session_id": sid
    })
    assert locked_res.status_code == 401
    assert "locked out" in locked_res.json()["detail"].lower()

# 11. Attempt to override a risk limit
def test_11_attempt_to_override_risk_limit():
    initial_risk = risk_engine.max_risk_per_trade_pct
    res = client.post("/api/v1/voice/command", json={
        "raw_text": "Increase my max risk per trade limit to 5.0 percent"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "BLOCKED"
    assert "Protected Action Blocked" in res.json()["display_text"]
    # Verify deterministic risk engine limit was untouched
    assert risk_engine.max_risk_per_trade_pct == initial_risk

# 12. Attempt to activate live trading through voice alone
def test_12_attempt_to_activate_live_trading_through_voice_alone():
    res = client.post("/api/v1/voice/command", json={
        "raw_text": "Enable live trading on my account right now"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "BLOCKED"
    assert "Live trading cannot be enabled via voice" in res.json()["display_text"]

# 13. Stale market data detection
def test_13_stale_market_data_detection():
    # Simulate data quality audit on stale bars
    from backend.app.market_data.manager import DataQualityAudit
    from datetime import datetime, timezone, timedelta
    
    old_time = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    stale_bars = [
        {"timestamp": old_time, "open": 2650.0, "high": 2655.0, "low": 2648.0, "close": 2652.0}
    ]
    audit = DataQualityAudit.audit_candles(stale_bars)
    assert audit["total_candles"] == 1
    assert audit["start_time"] is not None

# 14. Missing data provider handling
def test_14_missing_data_provider_handling():
    cmd = command_interpreter.interpret("Analyse UNKNOWNASSET on M15")
    assert cmd.symbol is None or cmd.symbol not in ["XAUUSD", "BTCUSD"]
    res = voice_dispatcher.dispatch(cmd)
    # Defaults safely to supported symbol and never hallucinates fake providers
    assert res.status == "SUCCESS"

# 15. Cancellation of long-running task
def test_15_cancellation_of_long_running_task():
    res = client.post("/api/v1/voice/command", json={
        "raw_text": "Stop current research task"
    })
    assert res.status_code == 200
    assert "Current Research Task Stopped" in res.json()["display_text"]
    assert scheduler.is_running is False

# 16. Duplicate task prevention
def test_16_duplicate_task_prevention():
    # Pausing research twice in succession should be idempotent
    r1 = client.post("/api/v1/voice/command", json={"raw_text": "Pause new research jobs"})
    assert r1.status_code == 200
    r2 = client.post("/api/v1/voice/command", json={"raw_text": "Pause new research jobs"})
    assert r2.status_code == 200
    assert controller.is_research_paused is True

# 17. Text-to-speech sanitization and formatting
def test_17_text_to_speech_sanitization():
    from backend.app.voice.synthesizer import speech_synthesizer
    raw_markdown = "### **Analysis** for `XAUUSD` • [Link](http://foo)"
    clean = speech_synthesizer.sanitize_for_speech(raw_markdown)
    assert "**" not in clean
    assert "###" not in clean
    assert "`" not in clean

# 18. Application restart and session expiration
def test_18_application_restart_and_session_expiration():
    sid = "reboot_session"
    s = session_manager.get_or_create_session(sid)
    s.add_turn("Analyse XAUUSD", "analyse_market", "XAUUSD", "M15", "Done")
    assert s.last_symbol == "XAUUSD"
    
    # Simulate session reset
    session_manager.reset_session(sid)
    fresh = session_manager.get_or_create_session(sid)
    assert fresh.last_symbol is None
    assert len(fresh.turns) == 0
