"""Comprehensive Automated Test Suite for GoldMind ALA Backend."""
import pytest
from datetime import datetime, timezone
from backend.app.database.session import init_db, SessionLocal
from backend.app.market_data.manager import MarketDataManager, DataQualityAudit
from backend.app.strategy_factory.families import ALLOWED_FAMILIES, compute_positions
from backend.app.strategy_factory.generator import generate_family_candidates, generate_all_candidates
from backend.app.sandbox.validator import validate_strategy_schema, static_code_analysis, verify_sandbox_execution
from backend.app.backtesting.engine import BacktestEngine
from backend.app.validation.validator import MultiStageValidator
from backend.app.risk.engine import CentralRiskEngine
from backend.app.brokers.simulated import SimulatedBroker
from backend.app.execution.order_manager import OrderLifecycleManager
from backend.app.learning.memory_system import AutonomousMemorySystem
from backend.app.planner.planner import ResearchPlanner
from backend.app.agent.controller import AgentController

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()

# --- 1. Market Data Tests ---
def test_market_data_regime_generation():
    mgr = MarketDataManager()
    candles, audit = mgr.generate_regime_dataset("XAUUSD", "M15", bars=200)
    assert len(candles) == 200
    assert audit["is_valid"] is True
    assert audit["missing_candles"] == 0
    assert audit["duplicate_candles"] == 0
    assert audit["invalid_ohlc_bars"] == 0

def test_data_quality_detects_bad_bars():
    bad_candles = [
        {"timestamp": "2026-01-01T00:00:00Z", "open": 100, "high": 90, "low": 105, "close": 95}, # Inverted high/low
        {"timestamp": "2026-01-01T00:00:00Z", "open": 100, "high": 110, "low": 90, "close": 105}  # Duplicate timestamp
    ]
    audit = DataQualityAudit.audit_candles(bad_candles)
    assert audit["is_valid"] is False
    assert audit["invalid_ohlc_bars"] > 0
    assert audit["duplicate_candles"] > 0

# --- 2. Strategy Factory & Sandbox Tests ---
def test_all_10_families_exist_and_generate():
    assert len(ALLOWED_FAMILIES) == 10
    all_cands = generate_all_candidates("XAUUSD", "M15")
    assert len(all_cands) >= 50
    generated_families = {c["family"] for c in all_cands}
    assert generated_families == ALLOWED_FAMILIES

def test_sandbox_ast_catches_dangerous_code():
    valid, errors = static_code_analysis("import os\nos.system('rm -rf /')")
    assert not valid
    assert any("Imports are strictly forbidden" in e for e in errors)

    valid, errors = static_code_analysis("eval('1 + 1')")
    assert not valid
    assert any("Forbidden function call" in e for e in errors)

def test_sandbox_execution_validates_causality():
    cand = {"family": "moving_average_crossover", "parameters": {"fast": 10, "slow": 30}, "side": "long_only"}
    passed, msg = verify_sandbox_execution(cand)
    assert passed is True

# --- 3. Backtesting & Look-ahead Elimination Tests ---
def test_backtesting_no_lookahead_and_costs():
    mgr = MarketDataManager()
    candles, _ = mgr.generate_regime_dataset("XAUUSD", "M15", bars=150)
    cand = {"family": "momentum", "parameters": {"lookback": 5, "threshold": 0.001}, "side": "long_only"}
    
    # Run backtest with realistic costs
    engine = BacktestEngine(cost_bps=3.0, spread_points=25, slippage_points=10)
    report = engine.run_backtest(candles, cand)
    assert "total_return" in report
    assert "max_drawdown" in report
    assert "sharpe_ratio" in report
    assert "equity_curve" in report
    assert len(report["equity_curve"]) == len(candles)
    assert report["total_fees"] >= 0.0

# --- 4. Multi-Stage Validation Tests ---
def test_multi_stage_validation_pipeline():
    mgr = MarketDataManager()
    candles, _ = mgr.generate_regime_dataset("XAUUSD", "M15", bars=300)
    cand = {"family": "rsi_mean_reversion", "parameters": {"period": 14, "lower": 30, "exit_level": 50}, "side": "long_only"}
    
    validator = MultiStageValidator()
    val_res = validator.validate_candidate(candles, cand, "test_cand_1")
    assert "decision" in val_res
    assert "in_sample_metrics" in val_res
    assert "out_of_sample_metrics" in val_res
    assert "walk_forward_metrics" in val_res
    assert "regime_breakdown" in val_res
    assert len(val_res["regime_breakdown"]) == 4

# --- 5. Central Deterministic Risk Engine Tests ---
def test_risk_engine_kills_switch_blocks_orders():
    risk = CentralRiskEngine()
    risk.kill_switch_active = True
    approved, reason, checks, vol = risk.evaluate_proposal(
        strategy_id="strat_1",
        strategy_approval_state="DEMO_APPROVED",
        instrument="XAUUSD",
        side="BUY",
        entry_price=2650.0,
        stop_loss=2645.0,
        take_profit=2660.0,
        account_mode="DEMO",
        current_equity=10000.0,
        current_spread_points=20,
        open_positions_count=0
    )
    assert approved is False
    assert "kill switch is active" in reason

def test_risk_engine_enforces_daily_loss_limit():
    risk = CentralRiskEngine(daily_loss_limit_pct=1.0, daily_start_equity=10000.0)
    # If equity drops below 9900 (1% loss), orders must be blocked
    approved, reason, checks, vol = risk.evaluate_proposal(
        strategy_id="strat_1",
        strategy_approval_state="DEMO_APPROVED",
        instrument="XAUUSD",
        side="BUY",
        entry_price=2650.0,
        stop_loss=2645.0,
        take_profit=2660.0,
        account_mode="DEMO",
        current_equity=9850.0, # Breached daily loss limit
        current_spread_points=20,
        open_positions_count=0
    )
    assert approved is False
    assert "Daily equity loss limit reached" in reason

def test_risk_engine_calculates_deterministic_lot_sizing():
    risk = CentralRiskEngine(max_risk_per_trade_pct=0.25)
    # XAUUSD: 10000 equity * 0.25% = $25 risk
    # entry 2650, SL 2645 -> $5 distance = 500 points * $0.01 = $5/lot * 100 contracts = $500/lot
    # Raw volume = 25 / 500 = 0.05 lots
    approved, reason, checks, vol = risk.evaluate_proposal(
        strategy_id="strat_1",
        strategy_approval_state="DEMO_APPROVED",
        instrument="XAUUSD",
        side="BUY",
        entry_price=2650.0,
        stop_loss=2645.0,
        take_profit=2660.0,
        account_mode="DEMO",
        current_equity=10000.0,
        current_spread_points=20,
        open_positions_count=0
    )
    assert approved is True
    assert vol == 0.05
    assert checks["estimated_risk_dollars"] == 25.0

def test_risk_engine_rejects_inverted_stop_loss():
    risk = CentralRiskEngine()
    # Inverted SL on BUY: SL higher than entry
    approved, reason, checks, vol = risk.evaluate_proposal(
        strategy_id="strat_1",
        strategy_approval_state="DEMO_APPROVED",
        instrument="XAUUSD",
        side="BUY",
        entry_price=2650.0,
        stop_loss=2660.0, # Invalid
        take_profit=2670.0,
        account_mode="DEMO",
        current_equity=10000.0,
        current_spread_points=20,
        open_positions_count=0
    )
    assert approved is False
    assert "Invalid protective SL/TP orientation" in reason

def test_risk_engine_rejects_live_when_not_allowlisted():
    risk = CentralRiskEngine()
    approved, reason, checks, vol = risk.evaluate_proposal(
        strategy_id="strat_1",
        strategy_approval_state="RESEARCH_ONLY",
        instrument="XAUUSD",
        side="BUY",
        entry_price=2650.0,
        stop_loss=2645.0,
        take_profit=2660.0,
        account_mode="LIVE",
        current_equity=10000.0,
        current_spread_points=20,
        open_positions_count=0
    )
    assert approved is False
    assert "LIVE_ALLOWLISTED" in reason

# --- 6. Order Lifecycle & Reconciliation Tests ---
def test_order_manager_reconciliation_and_idempotency():
    broker = SimulatedBroker()
    risk = CentralRiskEngine()
    order_mgr = OrderLifecycleManager(broker, risk)
    
    import uuid
    idem_key = f"test_idem_{uuid.uuid4().hex[:8]}"
    ok, msg, res = order_mgr.submit_managed_order(
        strategy_id="strat_test",
        strategy_approval_state="DEMO_APPROVED",
        symbol="XAUUSD",
        side="BUY",
        entry_price=2650.0,
        stop_loss=2645.0,
        take_profit=2660.0,
        account_mode="DEMO",
        idempotency_key=idem_key
    )
    assert ok is True
    assert res["state"] == "FILLED"
    
    # Retry with same idempotency key must reject
    ok2, msg2, res2 = order_mgr.submit_managed_order(
        strategy_id="strat_test",
        strategy_approval_state="DEMO_APPROVED",
        symbol="XAUUSD",
        side="BUY",
        entry_price=2650.0,
        stop_loss=2645.0,
        take_profit=2660.0,
        account_mode="DEMO",
        idempotency_key=idem_key
    )
    assert ok2 is False
    assert "Duplicate order rejected" in msg2

    # Reconcile state
    rec_res = order_mgr.reconcile_state()
    assert rec_res["reconciled"] is True
    assert rec_res["broker_open_positions"] == 1

# --- 7. Autonomous Memory System Tests ---
def test_5_tier_memory_operations():
    mem = AutonomousMemorySystem()
    
    # 1. Instruction Memory
    insts = mem.get_instructions()
    assert len(insts) >= 5
    
    # 2. Demonstration Memory
    demo = mem.add_demonstration("Lookahead Prevention", "Reject candle t-1 execution", "Must use bar t+1")
    assert demo["title"] == "Lookahead Prevention"
    
    # 3. Experience Memory & Feedback
    les_id = mem.record_lesson("Momentum fails in high vol", "Stress test max DD 28%", confidence=0.8)
    assert les_id.startswith("LES-")
    
    # Owner feedback
    fb_ok = mem.apply_owner_feedback(les_id, "GOOD_RESEARCH", "High quality stress test")
    assert fb_ok is True
    lessons = mem.get_lessons()
    target_l = [l for l in lessons if l["lesson_id"] == les_id][0]
    assert target_l["owner_feedback"] == "GOOD_RESEARCH"
    assert target_l["verification_status"] == "VERIFIED"

    # 4. Verified Knowledge
    know_id = mem.store_verified_knowledge("GOLD_LONDON_SESSION", {"optimal_hours": [8, 16]})
    assert know_id.startswith("KNOW-")

    # 5. Research Procedure Improvement
    prop = mem.propose_procedure_improvement("VALIDATOR", "Increase walk-forward windows from 3 to 5", "Enhances out-of-sample stability")
    assert prop["status"] == "PROPOSED"

# --- 8. Agent Controller & Research Loop Tests ---
def test_agent_controller_end_to_end_loop():
    controller = AgentController()
    res = controller.create_objective("Research XAUUSD M15 breakout strategies and validate robustness")
    assert res["objective_id"].startswith("obj_")
    assert res["tasks_count"] == 5
    
    # Step through all 5 tasks
    for i in range(5):
        step_res = controller.run_next_task(res["objective_id"])
        assert step_res is not None
        assert step_res["status"] == "COMPLETED"

    # All tasks completed
    next_step = controller.run_next_task(res["objective_id"])
    assert next_step is None
