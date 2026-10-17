from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Objective & Task schemas
class ObjectiveCreate(BaseModel):
    title: str
    raw_prompt: str
    priority: int = 1

class ObjectiveResponse(BaseModel):
    id: str
    title: str
    raw_prompt: str
    status: str
    parsed_intent: Optional[Dict[str, Any]] = None
    priority: int
    created_at: datetime
    updated_at: datetime

class TaskCreate(BaseModel):
    objective_id: Optional[str] = None
    task_type: str
    input_data: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    id: str
    objective_id: Optional[str] = None
    task_type: str
    status: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

# Strategy Schemas
class StrategySpec(BaseModel):
    family: str
    instrument: str = "XAUUSD"
    timeframe: str = "M15"
    parameters: Dict[str, Any]
    side: str = "long_only"
    entry_rules: Optional[List[str]] = None
    exit_rules: Optional[List[str]] = None
    hypothesis: Optional[str] = None

class StrategyCandidateResponse(BaseModel):
    candidate_id: str
    family: str
    instrument: str
    timeframe: str
    hypothesis: Optional[str] = None
    spec_json: Dict[str, Any]
    status: str
    score: Optional[float] = None
    validation_status: str
    approval_state: str
    result_json: Optional[Dict[str, Any]] = None
    created_at: datetime

# Backtest & Validation Schemas
class BacktestRequest(BaseModel):
    candidate_id: str
    dataset_id: Optional[str] = None
    cost_bps: float = 3.0
    spread_points: int = 25
    slippage_points: int = 10

class BacktestReportResponse(BaseModel):
    experiment_id: str
    candidate_id: str
    status: str
    train_return: float
    test_return: float
    test_max_drawdown: float
    test_win_rate: float
    trades_count: int
    profit_factor: float
    sharpe_ratio: float
    decision: str
    lesson: str
    equity_curve: List[Dict[str, Any]]
    drawdown_curve: List[Dict[str, Any]]
    metrics: Dict[str, Any]

class ValidationReportResponse(BaseModel):
    id: str
    candidate_id: str
    in_sample_metrics: Dict[str, Any]
    validation_metrics: Dict[str, Any]
    out_of_sample_metrics: Dict[str, Any]
    walk_forward_metrics: Dict[str, Any]
    regime_breakdown: Dict[str, Any]
    passed_all_gates: bool
    failure_reasons: List[str]

# Memory & Learning Schemas
class InstructionCreate(BaseModel):
    instruction: str
    category: str = "GENERAL"

class DemonstrationCreate(BaseModel):
    title: str
    input_context: Optional[str] = None
    example_decision: str
    explanation: Optional[str] = None
    feedback_label: str = "DESIRABLE"

class LessonFeedback(BaseModel):
    lesson_id: str
    feedback: str # GOOD_RESEARCH, INVALID_CONCLUSION, OVERFITTED, USEFUL_FINDING, POOR_DESIGN, REPEAT_CONDITIONS
    notes: Optional[str] = None

# Risk & Order Schemas
class RiskCheckRequest(BaseModel):
    strategy_id: str
    instrument: str
    side: str
    entry_price: float
    stop_loss: float
    take_profit: float
    account_mode: str = "DEMO"

class RiskDecisionResponse(BaseModel):
    approved: bool
    decision_reason: str
    evaluated_checks: Dict[str, Any]
    calculated_volume: Optional[float] = None

class OrderSubmitRequest(BaseModel):
    strategy_id: str
    symbol: str
    side: str
    risk_percent: float = 0.25
    sl_points: int = 300
    tp_points: int = 600
    account_mode: str = "DEMO"
    confirm_live: Optional[str] = None

class LiveTradingAuthRequest(BaseModel):
    enable: bool
    confirmation_phrase: str
    authorized_by: str
    max_risk_per_trade: float
    daily_loss_limit: float

class KillSwitchRequest(BaseModel):
    active: bool
    reason: str
    actor: str = "OWNER"

class MarketDataHealthResponse(BaseModel):
    provider: str
    symbol: str
    timeframe: str
    total_bars: int
    data_freshness_seconds: int
    missing_candles_count: int
    duplicate_candles_count: int
    invalid_ohlc_count: int
    is_healthy: bool
    last_candle_timestamp: Optional[str] = None
