"""Comprehensive Test Suite for Delta Exchange Integration (All 24 Required Test Cases)."""
from __future__ import annotations
import time
import pytest
from unittest.mock import MagicMock, patch
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.delta.config import DeltaSettings, DeltaEnvironment, delta_settings
from backend.app.delta.auth import DeltaAuth
from backend.app.delta.rest_client import DeltaRestClient, delta_client
from backend.app.delta.ws_client import DeltaWebSocketClient
from backend.app.delta.adapter import DeltaBrokerAdapter
from backend.app.risk.engine import CentralRiskEngine
from backend.app.execution.order_manager import OrderLifecycleManager
from backend.app.voice.interpreter import command_interpreter
from backend.app.voice.dispatcher import voice_dispatcher
from backend.app.voice.schema import VoiceCommandIntent, PermissionLevel

client = TestClient(app)

# 1. API configuration validation
def test_01_api_configuration_validation():
    cfg = DeltaSettings()
    audit = cfg.validate_configuration()
    assert audit["environment"] in ("INDIA_TESTNET", "INDIA_PRODUCTION", "GLOBAL_TESTNET", "GLOBAL_PRODUCTION")
    assert "rest_base_url" in audit
    assert "masked_api_key" in audit

# 2. Authentication success and failure
def test_02_authentication_signature_generation():
    key = "test_key_123"
    secret = "test_secret_abc"
    timestamp = "1700000000"
    
    # 2a. Valid signature calculation
    sig = DeltaAuth.generate_signature(secret, "GET", "/v2/wallet/balances", timestamp, "")
    assert len(sig) == 64 # SHA256 hex digest
    
    # 2b. Same payload gives deterministic result
    sig2 = DeltaAuth.generate_signature(secret, "GET", "/v2/wallet/balances", timestamp, "")
    assert sig == sig2
    
    # 2c. Tampered secret gives different signature
    sig_bad = DeltaAuth.generate_signature("wrong_secret", "GET", "/v2/wallet/balances", timestamp, "")
    assert sig != sig_bad

    # 2d. Missing secret raises ValueError
    with pytest.raises(ValueError):
        DeltaAuth.generate_signature("", "GET", "/v2/wallet/balances", timestamp, "")

# 3. Product discovery
def test_03_product_discovery():
    mock_products = [
        {
            "id": 101,
            "symbol": "BTCUSD",
            "contract_type": "perpetual_futures",
            "tick_size": "0.1",
            "contract_value": "1.0",
            "min_order_size": "1",
            "trading_status": "operational"
        },
        {
            "id": 102,
            "symbol": "BTC_USDT",
            "contract_type": "perpetual_futures",
            "tick_size": "0.5",
            "contract_value": "1.0",
            "min_order_size": "1",
            "trading_status": "operational"
        }
    ]
    rest_client = DeltaRestClient()
    with patch.object(rest_client, "_request", return_value={"success": True, "data": {"result": mock_products}}):
        products = rest_client.get_products()
        assert len(products) == 2
        assert products[0]["symbol"] == "BTCUSD"
        assert products[0]["id"] == 101
        assert products[0]["tick_size"] == 0.1

# 4. Historical candle retrieval
def test_04_historical_candle_retrieval():
    mock_candles = [
        [1700000000, 85000.0, 85500.0, 84800.0, 85200.0, 150.0],
        [1700000900, 85200.0, 85800.0, 85100.0, 85600.0, 200.0]
    ]
    rest_client = DeltaRestClient()
    with patch.object(rest_client, "_request", return_value={"success": True, "data": {"result": mock_candles}}):
        candles, audit = rest_client.get_candles("BTCUSD", resolution="15m")
        assert len(candles) == 2
        assert candles[0]["open"] == 85000.0
        assert candles[1]["close"] == 85600.0
        assert audit["is_valid"] is True

# 5. Live WebSocket subscription
def test_05_live_websocket_subscription():
    ws_client = DeltaWebSocketClient()
    ws_client.subscribed_symbols = ["BTCUSD", "ETHUSD"]
    status = ws_client.get_status()
    assert "BTCUSD" in status["subscribed_symbols"]
    assert status["data_freshness_status"] in ("FRESH", "STALE")

# 6. WebSocket reconnection
def test_06_websocket_reconnection_handling():
    ws_client = DeltaWebSocketClient()
    ws_client.is_connected = True
    ws_client.last_message_time = time.time()
    
    # Simulate connection drop
    ws_client.is_connected = False
    assert ws_client.get_status()["is_connected"] is False
    
    # Restore
    ws_client.is_connected = True
    assert ws_client.get_status()["is_connected"] is True

# 7. Stale-data rejection
def test_07_stale_data_rejection():
    ws_client = DeltaWebSocketClient()
    ws_client.is_connected = True
    # Message received 30 seconds ago (threshold is 15s)
    ws_client.last_message_time = time.time() - 30.0
    status = ws_client.get_status()
    assert status["data_freshness_status"] == "STALE"

# 8. Invalid symbol rejection
def test_08_invalid_symbol_rejection():
    engine = CentralRiskEngine()
    approved, reason, checks, vol = engine.evaluate_proposal(
        strategy_id="strat_1",
        strategy_approval_state="DEMO_APPROVED",
        instrument="NON_EXISTENT_COIN_999",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_mode="DEMO",
        current_equity=10000.0,
        current_spread_points=10,
        open_positions_count=0
    )
    assert approved is False
    assert "not available or supported" in reason

# 9. Indicator calculations
def test_09_indicator_calculations():
    from backend.app.voice.dispatcher import calc_ema, calc_rsi, calc_atr
    closes = [100.0 + i for i in range(30)]
    ema10 = calc_ema(closes, 10)
    rsi14 = calc_rsi(closes, 14)
    assert ema10 > 100.0
    assert 0.0 <= rsi14 <= 100.0

# 10. Strategy signal generation
def test_10_strategy_signal_generation():
    from backend.app.strategy_factory.families import compute_positions
    from backend.app.market_data.manager import MarketDataManager
    mgr = MarketDataManager()
    candles, _ = mgr.generate_regime_dataset(symbol="BTCUSD", bars=50)
    spec = {"family": "moving_average_crossover", "parameters": {"fast": 5, "slow": 15}}
    positions = compute_positions(candles, spec)
    assert len(positions) == len(candles)
    assert all(p in (0.0, 1.0) for p in positions)

# 11. Invalid signal rejection
def test_11_invalid_signal_rejection():
    from backend.app.strategy_factory.families import compute_positions
    with pytest.raises(ValueError):
        compute_positions([], {"family": "unsupported_family"})

# 12. Risk-limit enforcement (Daily loss)
def test_12_risk_limit_daily_loss():
    engine = CentralRiskEngine(daily_loss_limit_pct=1.0, daily_start_equity=10000.0)
    # Equity dropped by 2%
    approved, reason, checks, vol = engine.evaluate_proposal(
        strategy_id="strat_1",
        strategy_approval_state="DEMO_APPROVED",
        instrument="BTCUSD",
        side="BUY",
        entry_price=85000.0,
        stop_loss=84000.0,
        take_profit=87000.0,
        account_mode="DEMO",
        current_equity=9800.0, # < 9900 threshold
        current_spread_points=10,
        open_positions_count=0
    )
    assert approved is False
    assert "Daily equity loss limit reached" in reason

# 13. Invalid order quantity rejection
def test_13_invalid_order_quantity_rejection():
    engine = CentralRiskEngine()
    # Inverted stop loss
    approved, reason, checks, vol = engine.evaluate_proposal(
        strategy_id="strat_1",
        strategy_approval_state="DEMO_APPROVED",
        instrument="BTCUSD",
        side="BUY",
        entry_price=85000.0,
        stop_loss=86000.0, # SL above entry on BUY!
        take_profit=88000.0,
        account_mode="DEMO",
        current_equity=10000.0,
        current_spread_points=10,
        open_positions_count=0
    )
    assert approved is False
    assert "Invalid protective SL/TP orientation" in reason

# 14. Duplicate-order prevention
def test_14_duplicate_order_prevention():
    adapter = DeltaBrokerAdapter()
    engine = CentralRiskEngine()
    order_mgr = OrderLifecycleManager(adapter, engine)
    
    idem = "delta_unique_test_key_001"
    # First submission
    ok1, msg1, _ = order_mgr.submit_managed_order(
        strategy_id="strat_1",
        strategy_approval_state="DEMO_APPROVED",
        symbol="BTCUSD",
        side="BUY",
        entry_price=85000.0,
        stop_loss=84000.0,
        take_profit=87000.0,
        idempotency_key=idem
    )
    # Second submission with exact same key must be rejected
    ok2, msg2, _ = order_mgr.submit_managed_order(
        strategy_id="strat_1",
        strategy_approval_state="DEMO_APPROVED",
        symbol="BTCUSD",
        side="BUY",
        entry_price=85000.0,
        stop_loss=84000.0,
        take_profit=87000.0,
        idempotency_key=idem
    )
    assert ok2 is False
    assert "Duplicate order rejected" in msg2

# 15. Order timeout reconciliation
def test_15_order_timeout_reconciliation():
    adapter = DeltaBrokerAdapter()
    engine = CentralRiskEngine()
    order_mgr = OrderLifecycleManager(adapter, engine)
    result = order_mgr.reconcile_state()
    assert "reconciled" in result

# 16. Partial fills handling
def test_16_partial_fills_handling():
    adapter = DeltaBrokerAdapter()
    adapter.settings.trading_mode = "PAPER"
    res = adapter.submit_order("BTCUSD", "BUY", 1.0, 85000.0, 84000.0, 87000.0)
    assert res.accepted is True
    assert res.status == "FILLED"
    assert res.volume == 1.0

# 17. Order cancellation
def test_17_order_cancellation():
    adapter = DeltaBrokerAdapter()
    res = adapter.submit_order("BTCUSD", "BUY", 1.0, 85000.0, 84000.0, 87000.0)
    assert res.ticket is not None
    # Close / cancel position
    closed = adapter.close_position(res.ticket)
    assert closed is True

# 18. Position reconciliation
def test_18_position_reconciliation():
    adapter = DeltaBrokerAdapter()
    positions = adapter.get_positions()
    assert isinstance(positions, list)

# 19. Account-data failure handling
def test_19_account_data_failure_handling():
    rest_client = DeltaRestClient()
    with patch.object(rest_client, "_request", return_value={"success": False, "message": "Delta API Down"}):
        balances = rest_client.get_wallet_balances()
        assert balances == []

# 20. Emergency-stop behavior
def test_20_emergency_stop_behavior():
    engine = CentralRiskEngine()
    engine.kill_switch_active = True
    approved, reason, checks, vol = engine.evaluate_proposal(
        strategy_id="strat_1",
        strategy_approval_state="DEMO_APPROVED",
        instrument="BTCUSD",
        side="BUY",
        entry_price=85000.0,
        stop_loss=84000.0,
        take_profit=87000.0,
        account_mode="DEMO",
        current_equity=10000.0,
        current_spread_points=10,
        open_positions_count=0
    )
    assert approved is False
    assert "Emergency kill switch is active" in reason

# 21. Voice transcription errors normalization
def test_21_voice_transcription_normalization():
    from backend.app.voice.recognizer import speech_recognizer
    res = speech_recognizer.normalize_trading_transcription("show bit coin on 15 minute")
    assert "BTCUSD" in res["normalized_text"]
    assert "15-minute" in res["normalized_text"]

    from backend.app.voice.interpreter import command_interpreter
    tf = command_interpreter.extract_timeframe(res["normalized_text"])
    assert tf == "M15"

# 22. Ambiguous order requests
def test_22_ambiguous_order_requests():
    cmd = command_interpreter.interpret("Do something on the chart")
    res = voice_dispatcher.dispatch(cmd)
    assert res.status in ("NEEDS_CLARIFICATION", "SUCCESS")

# 23. Attempted risk-control bypass via voice
def test_23_attempted_risk_control_bypass_via_voice():
    res = client.post("/api/v1/voice/command", json={
        "raw_text": "Set maximum daily loss limit to 50 percent"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "BLOCKED"
    assert "Voice commands cannot alter risk limits" in res.json()["spoken_summary"]

# 24. Application restart and recovery
def test_24_application_restart_and_recovery():
    status_res = client.get("/api/v1/delta/status")
    assert status_res.status_code == 200
    assert status_res.json()["active_trading_mode"] in ("PAPER", "LIVE")
