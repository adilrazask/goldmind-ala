"""End-to-End Verification of GoldMind ALA Autonomous Lifecycle."""
from __future__ import annotations
import sys
import json
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.database.session import init_db, SessionLocal
from backend.app.agent.controller import AgentController
from backend.app.brokers.simulated import SimulatedBroker
from backend.app.risk.engine import CentralRiskEngine
from backend.app.execution.order_manager import OrderLifecycleManager
from backend.app.models.entities import AgentObjective, AgentTask, ExperimentRun, ValidationResult, Lesson, BrokerOrder, BrokerPosition

def run_verification():
    print("=" * 70)
    print("GOLDMIND ALA: END-TO-END VERIFICATION RUN")
    print("=" * 70)
    
    init_db()
    controller = AgentController()
    
    # 1. Objective Entry
    prompt = "Research XAUUSD M15 breakout strategies, evaluate transaction costs, and validate out-of-sample robustness."
    print(f"\n[1] Entering Research Objective: '{prompt}'")
    obj_info = controller.create_objective(prompt, title="Autonomous XAUUSD Breakout Investigation")
    obj_id = obj_info["objective_id"]
    print(f" -> Objective created: ID={obj_id}, Tasks planned={obj_info['tasks_count']}")
    print(f" -> Parsed Intent: {json.dumps(obj_info['parsed_intent'])}")
    
    # 2 & 3. Planning & Task Execution Sequence
    print("\n[2] Executing Decomposed Task Sequence autonomously:")
    for step_num in range(1, 6):
        task_res = controller.run_next_task(obj_id)
        assert task_res is not None, f"Expected task at step {step_num}"
        print(f"   Task {step_num}/5 [{task_res['task_type']}]: Status={task_res['status']}")
        for event in task_res.get("events", []):
            print(f"     • {event}")
            
    # Verify DB persistence of experiment and validation
    db = SessionLocal()
    try:
        exp = db.query(ExperimentRun).order_by(ExperimentRun.created_at.desc()).first()
        val = db.query(ValidationResult).order_by(ValidationResult.created_at.desc()).first()
        lesson = db.query(Lesson).order_by(Lesson.created_at.desc()).first()
        
        print("\n[3] Research Evidence & Empirical Synthesis:")
        print(f" -> Backtest Total Return: {exp.test_return:.2%}, Max DD: {exp.test_max_drawdown:.2%}, Trades: {exp.trades_count}")
        print(f" -> Multi-Stage Validation Decision: {val.decision} (Passed All: {val.passed_all_gates})")
        print(f" -> Recorded Lesson: ID={lesson.id}")
        print(f"    Observation: {lesson.observation}")
        print(f"    Evidence: {lesson.evidence}")
        print(f"    Confidence: {lesson.confidence:.0%}, Status: {lesson.verification_status}")
    finally:
        db.close()
        
    # 4. Restricted Demo Trade Lifecycle & Broker Reconciliation
    print("\n[4] Restricted Demo Trade Lifecycle with Central Risk Gate:")
    broker = SimulatedBroker()
    risk = CentralRiskEngine()
    order_mgr = OrderLifecycleManager(broker, risk)
    
    print(" -> Submitting Risk-Gated Order on XAUUSD...")
    ok, msg, order_res = order_mgr.submit_managed_order(
        strategy_id="STRAT_VALIDATED_BREAKOUT",
        strategy_approval_state="DEMO_APPROVED",
        symbol="XAUUSD",
        side="BUY",
        entry_price=2650.0,
        stop_loss=2645.0,
        take_profit=2665.0,
        account_mode="DEMO"
    )
    assert ok is True, f"Order failed: {msg}"
    print(f" -> Order Status: {order_res['state']}, Ticket: #{order_res['ticket']}, Sized Volume: {order_res['volume']} lots")
    
    # Verify open positions
    open_pos = broker.get_positions("XAUUSD")
    print(f" -> Broker Open Positions count: {len(open_pos)}")
    assert len(open_pos) == 1
    
    # Simulate market move and close position
    ticket = open_pos[0]["ticket"]
    broker.update_tick_price("XAUUSD", 2658.0) # Price gained $8
    print(f" -> Simulating market tick to 2658.0: Unrealized P&L = ${broker.get_positions('XAUUSD')[0]['unrealized_profit']:.2f}")
    
    print(f" -> Closing Position #{ticket} on signal...")
    close_ok = broker.close_position(ticket)
    assert close_ok is True
    
    # Reconcile state
    rec = order_mgr.reconcile_state()
    print(f" -> State Reconciliation: Reconciled={rec['reconciled']}, Broker Open={rec['broker_open_positions']}")
    print(f" -> Post-Trade Account Equity: ${broker.get_account_info()['equity']:.2f}")
    
    # 5. Live Trading Security Assertion
    print("\n[5] Air-Gapped Live Trading Security Verification:")
    live_ok, live_msg, _ = order_mgr.submit_managed_order(
        strategy_id="STRAT_UNAPPROVED",
        strategy_approval_state="RESEARCH_ONLY",
        symbol="XAUUSD",
        side="BUY",
        entry_price=2650.0,
        stop_loss=2645.0,
        take_profit=2665.0,
        account_mode="LIVE"
    )
    print(f" -> Unapproved live order rejected as expected: '{live_msg}'")
    assert live_ok is False
    
    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY.")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
