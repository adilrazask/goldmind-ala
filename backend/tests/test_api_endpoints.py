"""Integration tests for GoldMind ALA FastAPI REST Endpoints."""
import pytest
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["project"] == "GoldMind ALA"

def test_dashboard_state_endpoint():
    response = client.get("/api/v1/dashboard/state")
    assert response.status_code == 200
    data = response.json()
    assert "agent_status" in data
    assert "operating_mode" in data
    assert "account" in data
    assert "kill_switch_active" in data

def test_agent_objective_and_tasks_flow():
    # 1. Post new objective
    obj_payload = {
        "title": "API Test Research XAUUSD M15",
        "raw_prompt": "Research XAUUSD M15 breakout strategies and validate robustness",
        "priority": 1
    }
    response = client.post("/api/v1/agent/objective", json=obj_payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "objective_id" in res_data
    assert res_data["tasks_count"] == 5

    # 2. Trigger step
    step_res = client.post("/api/v1/agent/step")
    assert step_res.status_code == 200
    task_out = step_res.json()["executed_task"]
    assert task_out is not None
    assert task_out["status"] == "COMPLETED"

def test_strategy_lab_endpoints():
    response = client.get("/api/v1/strategies")
    assert response.status_code == 200
    strategies = response.json()
    assert isinstance(strategies, list)

def test_learning_memory_endpoint():
    response = client.get("/api/v1/learning/memory")
    assert response.status_code == 200
    mem_data = response.json()
    assert "instructions" in mem_data
    assert "demonstrations" in mem_data
    assert "lessons" in mem_data
    assert "verified_knowledge" in mem_data
    assert "improvement_proposals" in mem_data

def test_demo_trading_endpoints():
    response = client.get("/api/v1/demo/account")
    assert response.status_code == 200
    data = response.json()
    assert "account" in data
    assert "positions" in data

def test_live_controls_and_kill_switch():
    # Live controls
    res = client.get("/api/v1/live/controls")
    assert res.status_code == 200
    ctrls = res.json()
    assert ctrls["live_trading_enabled"] is False

    # Bad auth phrase must be rejected
    bad_auth = client.post("/api/v1/live/authorize", json={
        "enable": True,
        "confirmation_phrase": "WRONG_PHRASE",
        "authorized_by": "TestUser",
        "max_risk_per_trade": 0.25,
        "daily_loss_limit": 1.0
    })
    assert bad_auth.status_code == 403

    # Toggle kill switch
    ks_res = client.post("/api/v1/live/kill-switch", json={
        "active": True,
        "reason": "Test emergency pause",
        "actor": "API_TEST"
    })
    assert ks_res.status_code == 200
    assert ks_res.json()["kill_switch_active"] is True

    # Untoggle kill switch
    ks_res2 = client.post("/api/v1/live/kill-switch", json={
        "active": False,
        "reason": "Resume operational testing",
        "actor": "API_TEST"
    })
    assert ks_res2.status_code == 200
    assert ks_res2.json()["kill_switch_active"] is False

def test_market_data_health():
    res = client.get("/api/v1/market-data/health")
    assert res.status_code == 200
    providers = res.json()["providers"]
    assert len(providers) >= 2
    assert any(p["symbol"] == "XAUUSD" for p in providers)
    assert any(p["symbol"] == "BTCUSD" for p in providers)

def test_spa_static_serving():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "GoldMind ALA" in res.text

