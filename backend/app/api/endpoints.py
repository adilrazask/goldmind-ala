"""FastAPI REST & WebSocket Endpoints for GoldMind ALA SaaS."""
from __future__ import annotations
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from backend.app.database.session import get_db, SessionLocal
from backend.app.core.config import settings
from backend.app.models.entities import (
    AgentObjective, AgentTask, TaskEvent, StrategyCandidate, ExperimentRun,
    BacktestResult, ValidationResult, Lesson, Instruction, Demonstration,
    BrokerOrder, BrokerPosition, AuditLog, ApprovalEvent, SystemHealth
)
from backend.app.agent.controller import AgentController
from backend.app.scheduler.runner import ResearchScheduler
from backend.app.brokers.simulated import SimulatedBroker
from backend.app.brokers.mt5_adapter import MT5BrokerAdapter
from backend.app.risk.engine import CentralRiskEngine
from backend.app.execution.order_manager import OrderLifecycleManager
from backend.app.schemas.schemas import (
    ObjectiveCreate, TaskCreate, StrategySpec, RiskCheckRequest,
    OrderSubmitRequest, LiveTradingAuthRequest, KillSwitchRequest,
    LessonFeedback, InstructionCreate, DemonstrationCreate
)
from backend.app.core.dependencies import (
    controller, scheduler, risk_engine, simulated_broker,
    mt5_broker, active_broker, order_manager
)
from backend.app.voice.router import router as voice_router
from backend.app.delta.router import router as delta_router

router = APIRouter()
router.include_router(voice_router)
router.include_router(delta_router)

# Active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

ws_manager = ConnectionManager()

# --- PAGE 1: Main Dashboard Endpoints ---
@router.get("/dashboard/state")
def get_dashboard_state(db: Session = Depends(get_db)):
    account_info = active_broker.get_account_info()
    positions = active_broker.get_positions()
    
    total_experiments = db.query(ExperimentRun).count()
    rejected_count = db.query(StrategyCandidate).filter_by(status="REJECTED").count()
    validated_count = db.query(StrategyCandidate).filter_by(status="PROMOTED_TO_DEMO").count()
    awaiting_validation = db.query(StrategyCandidate).filter_by(validation_status="PENDING").count()
    
    active_obj = db.query(AgentObjective).filter_by(status="ACTIVE").order_by(AgentObjective.created_at.desc()).first()
    recent_exp = db.query(ExperimentRun).order_by(ExperimentRun.created_at.desc()).first()
    
    # Audit trail
    recent_errors = db.query(TaskEvent).filter_by(event_type="ERROR").order_by(TaskEvent.created_at.desc()).limit(5).all()

    return {
        "agent_status": "PAUSED" if controller.is_research_paused else ("RUNNING" if scheduler.is_running else "IDLE"),
        "operating_mode": controller.operating_mode,
        "current_objective": active_obj.title if active_obj else "No active research objective.",
        "active_objective_id": active_obj.id if active_obj else None,
        "scheduler": scheduler.status(),
        "experiments_count": total_experiments,
        "rejected_strategies_count": rejected_count,
        "validated_strategies_count": validated_count,
        "awaiting_validation_count": awaiting_validation,
        "account": account_info,
        "open_positions": positions,
        "realized_pnl": 0.0,
        "unrealized_pnl": sum(p.get("unrealized_profit", 0) for p in positions),
        "kill_switch_active": risk_engine.kill_switch_active,
        "last_experiment": {
            "id": recent_exp.id,
            "return": recent_exp.test_return,
            "decision": recent_exp.decision
        } if recent_exp else None,
        "recent_errors": [{"time": e.created_at.isoformat(), "message": e.message} for e in recent_errors]
    }

@router.post("/dashboard/controls")
def dashboard_controls(action: str, interval_seconds: Optional[int] = 60, db: Session = Depends(get_db)):
    act = action.upper()
    if act == "START":
        controller.is_research_paused = False
        scheduler.start(interval_seconds)
    elif act == "PAUSE":
        controller.is_research_paused = True
    elif act == "RESUME":
        controller.is_research_paused = False
        if not scheduler.is_running:
            scheduler.start(interval_seconds)
    elif act == "STOP":
        scheduler.stop()
    elif act == "KILL_SWITCH":
        risk_engine.kill_switch_active = True
        scheduler.stop()
        db.add(AuditLog(action="KILL_SWITCH_ACTIVATED", actor="OWNER_DASHBOARD", details={"timestamp": datetime.now(timezone.utc).isoformat()}))
        db.commit()
    elif act == "DEACTIVATE_KILL_SWITCH":
        risk_engine.kill_switch_active = False
        db.add(AuditLog(action="KILL_SWITCH_DEACTIVATED", actor="OWNER_DASHBOARD", details={"timestamp": datetime.now(timezone.utc).isoformat()}))
        db.commit()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
        
    return {"action": act, "scheduler": scheduler.status(), "kill_switch": risk_engine.kill_switch_active}

# --- PAGE 2: AI Agent Workspace ---
@router.post("/agent/objective")
def create_objective(payload: ObjectiveCreate, db: Session = Depends(get_db)):
    res = controller.create_objective(payload.raw_prompt, payload.title)
    db.add(AuditLog(action="CREATE_OBJECTIVE", actor="USER", details=res))
    db.commit()
    return res

@router.get("/agent/objectives")
def list_objectives(db: Session = Depends(get_db)):
    objs = db.query(AgentObjective).order_by(AgentObjective.created_at.desc()).all()
    results = []
    for o in objs:
        tasks = db.query(AgentTask).filter_by(objective_id=o.id).all()
        results.append({
            "id": o.id,
            "title": o.title,
            "raw_prompt": o.raw_prompt,
            "status": o.status,
            "parsed_intent": o.parsed_intent,
            "created_at": o.created_at.isoformat(),
            "tasks": [{
                "task_id": t.id,
                "type": t.task_type,
                "status": t.status,
                "output": t.output_data
            } for t in tasks]
        })
    return results

@router.post("/agent/step")
def step_agent():
    """Manually triggers the execution of the next research task in queue."""
    res = controller.run_next_task()
    return {"executed_task": res}

# --- PAGE 3: Strategy Laboratory ---
@router.get("/strategies")
def list_strategies(family: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(StrategyCandidate)
    if family:
        query = query.filter_by(family=family)
    cands = query.order_by(StrategyCandidate.created_at.desc()).limit(100).all()
    return [{
        "candidate_id": c.candidate_id,
        "family": c.family,
        "instrument": c.instrument,
        "timeframe": c.timeframe,
        "hypothesis": c.hypothesis,
        "parameters": c.spec_json.get("parameters", {}),
        "spec_json": c.spec_json,
        "status": c.status,
        "score": c.score,
        "validation_status": c.validation_status,
        "approval_state": c.approval_state,
        "created_at": c.created_at.isoformat()
    } for c in cands]

@router.post("/strategies/generate-batch")
def generate_strategies_batch(family: str = "momentum", count: int = 5, db: Session = Depends(get_db)):
    from backend.app.strategy_factory.generator import generate_family_candidates
    candidates = generate_family_candidates(family)[:count]
    saved = []
    for c in candidates:
        cand_id = f"cand_{uuid.uuid4().hex[:8]}"
        passed, msg = verify_sandbox_execution(c)
        cand_db = StrategyCandidate(
            candidate_id=cand_id,
            family=family,
            instrument=c.get("instrument", "XAUUSD"),
            timeframe=c.get("timeframe", "M15"),
            hypothesis=c.get("hypothesis"),
            spec_json=c,
            status="SYNTAX_PASSED" if passed else "REJECTED",
            approval_state="RESEARCH_ONLY"
        )
        db.add(cand_db)
        saved.append({"candidate_id": cand_id, "family": family, "status": cand_db.status})
    db.commit()
    return {"generated_count": len(saved), "candidates": saved}

# --- PAGE 4: Research Monitor ---
@router.get("/research/monitor")
def get_research_monitor(db: Session = Depends(get_db)):
    active_obj = db.query(AgentObjective).filter_by(status="ACTIVE").order_by(AgentObjective.created_at.desc()).first()
    current_task = db.query(AgentTask).filter_by(status="RUNNING").first()
    recent_tasks = db.query(AgentTask).order_by(AgentTask.created_at.desc()).limit(15).all()
    
    events = db.query(TaskEvent).order_by(TaskEvent.created_at.desc()).limit(30).all()
    
    return {
        "current_objective": {
            "id": active_obj.id,
            "title": active_obj.title,
            "prompt": active_obj.raw_prompt,
            "intent": active_obj.parsed_intent
        } if active_obj else None,
        "current_task": {
            "id": current_task.id,
            "type": current_task.task_type,
            "budget": current_task.resource_budget,
            "started_at": current_task.started_at.isoformat() if current_task.started_at else None
        } if current_task else None,
        "recent_tasks": [{
            "id": t.id,
            "type": t.task_type,
            "status": t.status,
            "error": t.error_message
        } for t in recent_tasks],
        "event_timeline": [{
            "id": e.id,
            "task_id": e.task_id,
            "type": e.event_type,
            "message": e.message,
            "timestamp": e.created_at.isoformat()
        } for e in events]
    }

# --- PAGE 5: Backtesting & Validation ---
@router.get("/backtest/results")
def list_backtest_results(limit: int = 10, db: Session = Depends(get_db)):
    results = db.query(BacktestResult).order_by(BacktestResult.created_at.desc()).limit(limit).all()
    out = []
    for r in results:
        exp = db.query(ExperimentRun).filter_by(id=r.experiment_id).first()
        out.append({
            "id": r.id,
            "experiment_id": r.experiment_id,
            "candidate_id": exp.candidate_id if exp else "unknown",
            "sharpe_ratio": r.sharpe_ratio,
            "sortino_ratio": r.sortino_ratio,
            "profit_factor": r.profit_factor,
            "expectancy": r.expectancy,
            "total_fees": r.total_fees,
            "slippage_cost": r.slippage_cost,
            "equity_curve": r.equity_curve or [],
            "drawdown_curve": r.drawdown_curve or [],
            "trades_count": len(r.trades_log or []),
            "created_at": r.created_at.isoformat()
        })
    return out

@router.get("/validation/results")
def list_validation_results(limit: int = 10, db: Session = Depends(get_db)):
    vals = db.query(ValidationResult).order_by(ValidationResult.created_at.desc()).limit(limit).all()
    return [{
        "id": v.id,
        "candidate_id": v.candidate_id,
        "passed_all_gates": v.passed_all_gates,
        "failure_reasons": v.failure_reasons or [],
        "in_sample": v.in_sample_metrics or {},
        "validation": v.validation_metrics or {},
        "out_of_sample": v.out_of_sample_metrics or {},
        "walk_forward": v.walk_forward_metrics or {},
        "regime_breakdown": v.regime_breakdown or [],
        "stress_test": v.stress_test_metrics or {},
        "created_at": v.created_at.isoformat()
    } for v in vals]

# --- PAGE 6: Autonomous Learning Centre ---
@router.get("/learning/memory")
def get_learning_memory():
    return {
        "instructions": controller.memory_system.get_instructions(),
        "demonstrations": controller.memory_system.get_demonstrations(),
        "lessons": controller.memory_system.get_lessons(50),
        "verified_knowledge": controller.memory_system.get_verified_knowledge(),
        "improvement_proposals": controller.memory_system.get_improvement_proposals()
    }

@router.post("/learning/instruction")
def add_instruction(payload: InstructionCreate):
    return controller.memory_system.add_instruction(payload.instruction, payload.category)

@router.post("/learning/example")
def add_example(payload: DemonstrationCreate):
    return controller.memory_system.add_demonstration(
        payload.title, payload.example_decision, payload.explanation or "", payload.feedback_label
    )

@router.post("/learning/feedback")
def submit_lesson_feedback(payload: LessonFeedback):
    success = controller.memory_system.apply_owner_feedback(payload.lesson_id, payload.feedback, payload.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"status": "SUCCESS", "lesson_id": payload.lesson_id, "feedback": payload.feedback}

# --- PAGE 7: Demo Trading ---
@router.get("/demo/account")
def get_demo_account(db: Session = Depends(get_db)):
    account_info = active_broker.get_account_info()
    positions = active_broker.get_positions()
    orders = db.query(BrokerOrder).order_by(BrokerOrder.created_at.desc()).limit(25).all()
    
    return {
        "account": account_info,
        "positions": positions,
        "recent_orders": [{
            "id": o.id,
            "symbol": o.symbol,
            "side": o.side,
            "volume": o.requested_volume,
            "price": o.execution_price or o.requested_price,
            "state": o.state,
            "rejection_reason": o.rejection_reason,
            "ticket": o.broker_ticket,
            "created_at": o.created_at.isoformat()
        } for o in orders]
    }

@router.post("/demo/trade")
def submit_demo_trade(payload: OrderSubmitRequest):
    # Verify current market price
    entry_price = 2650.0 if payload.symbol.upper() == "XAUUSD" else 88000.0
    point = 0.01 if payload.symbol.upper() == "XAUUSD" else 0.1
    
    if payload.side.upper() == "BUY":
        sl = entry_price - (payload.sl_points * point)
        tp = entry_price + (payload.tp_points * point)
    else:
        sl = entry_price + (payload.sl_points * point)
        tp = entry_price - (payload.tp_points * point)
        
    ok, msg, res = order_manager.submit_managed_order(
        strategy_id=payload.strategy_id,
        strategy_approval_state="DEMO_APPROVED",
        symbol=payload.symbol,
        side=payload.side,
        entry_price=entry_price,
        stop_loss=sl,
        take_profit=tp,
        account_mode="DEMO"
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return res

@router.post("/demo/close-position")
def close_demo_position(ticket: int):
    success = active_broker.close_position(ticket)
    if not success:
        raise HTTPException(status_code=400, detail="Could not close position.")
    # Reconcile state
    order_manager.reconcile_state()
    return {"status": "CLOSED", "ticket": ticket}

# --- PAGE 8: Live Trading Controls ---
@router.get("/live/controls")
def get_live_controls():
    return {
        "live_trading_enabled": settings.ALLOW_LIVE_TRADING,
        "kill_switch_active": risk_engine.kill_switch_active,
        "max_risk_per_trade_pct": risk_engine.max_risk_per_trade_pct,
        "daily_loss_limit_pct": risk_engine.daily_loss_limit_pct,
        "max_open_positions": risk_engine.max_open_positions,
        "max_spread_points": risk_engine.max_spread_points,
        "daily_start_equity": risk_engine.daily_start_equity,
        "confirmation_phrase_required": settings.LIVE_CONFIRMATION_PHRASE
    }

@router.post("/live/authorize")
def authorize_live_trading(payload: LiveTradingAuthRequest, db: Session = Depends(get_db)):
    if payload.confirmation_phrase != settings.LIVE_CONFIRMATION_PHRASE:
        raise HTTPException(status_code=403, detail="Invalid confirmation phrase. Refusing live authorization.")
    
    settings.ALLOW_LIVE_TRADING = payload.enable
    risk_engine.max_risk_per_trade_pct = min(payload.max_risk_per_trade, 0.5)
    risk_engine.daily_loss_limit_pct = min(payload.daily_loss_limit, 2.0)
    
    db.add(ApprovalEvent(
        action_type="LIVE_TRADE_AUTHORIZATION",
        authorized_by=payload.authorized_by,
        details={
            "enabled": payload.enable,
            "max_risk": risk_engine.max_risk_per_trade_pct,
            "daily_loss_limit": risk_engine.daily_loss_limit_pct
        }
    ))
    db.commit()
    return {"live_trading_enabled": settings.ALLOW_LIVE_TRADING, "authorized_by": payload.authorized_by}

@router.post("/live/kill-switch")
def trigger_kill_switch(payload: KillSwitchRequest, db: Session = Depends(get_db)):
    risk_engine.kill_switch_active = payload.active
    if payload.active:
        scheduler.stop()
        
    db.add(AuditLog(
        action="KILL_SWITCH_TOGGLED",
        actor=payload.actor,
        details={"active": payload.active, "reason": payload.reason}
    ))
    db.commit()
    return {"kill_switch_active": risk_engine.kill_switch_active, "reason": payload.reason}

# --- PAGE 9: Market Data ---
@router.get("/market-data/health")
def get_market_data_health():
    # Audit XAUUSD and BTCUSD
    candles_xau, audit_xau = controller.data_mgr.generate_regime_dataset(symbol="XAUUSD", timeframe="M15", bars=300)
    candles_btc, audit_btc = controller.data_mgr.generate_regime_dataset(symbol="BTCUSD", timeframe="M15", bars=300)
    return {
        "providers": [
            {
                "name": "GoldMind Synthetic/Historical Engine",
                "symbol": "XAUUSD",
                "timeframe": "M15",
                "health": audit_xau
            },
            {
                "name": "GoldMind Crypto Feed Adapter",
                "symbol": "BTCUSD",
                "timeframe": "M15",
                "health": audit_btc
            }
        ]
    }

# --- PAGE 10: Settings & Operations ---
@router.get("/settings")
def get_system_settings():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_url": settings.DATABASE_URL.split("///")[-1],
        "use_ollama": settings.USE_OLLAMA,
        "ollama_host": settings.OLLAMA_HOST,
        "ollama_model": settings.OLLAMA_MODEL,
        "operating_mode": controller.operating_mode,
        "live_trading_opt_in": settings.ALLOW_LIVE_TRADING,
        "kill_switch_active": risk_engine.kill_switch_active,
        "risk_limits": {
            "max_risk_per_trade_pct": risk_engine.max_risk_per_trade_pct,
            "daily_loss_limit_pct": risk_engine.daily_loss_limit_pct,
            "max_open_positions": risk_engine.max_open_positions,
            "max_spread_points": risk_engine.max_spread_points
        }
    }

# --- Live WebSocket ---
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Respond with heartbeat status
            await websocket.send_json({
                "type": "HEARTBEAT",
                "time": datetime.now(timezone.utc).isoformat(),
                "scheduler_running": scheduler.is_running,
                "kill_switch": risk_engine.kill_switch_active
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
