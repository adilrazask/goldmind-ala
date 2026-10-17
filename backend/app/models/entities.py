import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

# 1. agent_configurations
class AgentConfiguration(Base):
    __tablename__ = "agent_configurations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(JSON, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

# 2. agent_objectives
class AgentObjective(Base):
    __tablename__ = "agent_objectives"
    id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=False)
    raw_prompt = Column(Text, nullable=False)
    status = Column(String(50), default="ACTIVE", index=True) # ACTIVE, PAUSED, COMPLETED, CANCELLED
    parsed_intent = Column(JSON, nullable=True)
    priority = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tasks = relationship("AgentTask", back_populates="objective", cascade="all, delete-orphan")

# 3. agent_tasks
class AgentTask(Base):
    __tablename__ = "agent_tasks"
    id = Column(String(50), primary_key=True)
    objective_id = Column(String(50), ForeignKey("agent_objectives.id"), nullable=True, index=True)
    task_type = Column(String(50), nullable=False, index=True) # DATA_FETCH, STRATEGY_GEN, BACKTEST, VALIDATE, DEMO_MONITOR, LEARN
    status = Column(String(50), default="PENDING", index=True) # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    resource_budget = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    objective = relationship("AgentObjective", back_populates="tasks")
    events = relationship("TaskEvent", back_populates="task", cascade="all, delete-orphan")

# 4. task_events
class TaskEvent(Base):
    __tablename__ = "task_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), ForeignKey("agent_tasks.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    task = relationship("AgentTask", back_populates="events")

# 5. instructions
class Instruction(Base):
    __tablename__ = "instructions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    instruction = Column(Text, nullable=False)
    category = Column(String(50), default="GENERAL") # GENERAL, SAFETY, RISK, RESEARCH
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 6. demonstrations
class Demonstration(Base):
    __tablename__ = "demonstrations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    input_context = Column(Text, nullable=True)
    example_decision = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    feedback_label = Column(String(50), default="DESIRABLE") # DESIRABLE, UNDESIRABLE
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 7. memory_records
class MemoryRecord(Base):
    __tablename__ = "memory_records"
    id = Column(String(50), primary_key=True)
    category = Column(String(50), nullable=False, index=True) # INSTRUCTION, DEMONSTRATION, EXPERIENCE, VERIFIED_KNOWLEDGE, RESEARCH_IMPROVEMENT
    key = Column(String(100), nullable=False, index=True)
    value_json = Column(JSON, nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

# 8. research_procedures
class ResearchProcedure(Base):
    __tablename__ = "research_procedures"
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    active_version_id = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 9. research_procedure_versions
class ResearchProcedureVersion(Base):
    __tablename__ = "research_procedure_versions"
    id = Column(String(50), primary_key=True)
    procedure_id = Column(String(50), ForeignKey("research_procedures.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    definition_json = Column(JSON, nullable=False)
    change_rationale = Column(Text, nullable=True)
    benchmark_metrics = Column(JSON, nullable=True)
    promoted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 10. strategy_definitions
class StrategyDefinition(Base):
    __tablename__ = "strategy_definitions"
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    family = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    versions = relationship("StrategyVersion", back_populates="definition", cascade="all, delete-orphan")

# 11. strategy_versions
class StrategyVersion(Base):
    __tablename__ = "strategy_versions"
    id = Column(String(50), primary_key=True)
    strategy_id = Column(String(50), ForeignKey("strategy_definitions.id"), nullable=False, index=True)
    version = Column(Integer, default=1)
    spec_json = Column(JSON, nullable=False)
    code_body = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    definition = relationship("StrategyDefinition", back_populates="versions")

# 12. strategy_candidates
class StrategyCandidate(Base):
    __tablename__ = "strategy_candidates"
    candidate_id = Column(String(50), primary_key=True)
    family = Column(String(50), nullable=False, index=True)
    instrument = Column(String(20), default="XAUUSD", index=True)
    timeframe = Column(String(10), default="M15", index=True)
    hypothesis = Column(Text, nullable=True)
    spec_json = Column(JSON, nullable=False)
    status = Column(String(50), default="GENERATED", index=True) # GENERATED, SYNTAX_PASSED, BACKTESTED, VALIDATED, REJECTED, PROMOTED_TO_DEMO
    score = Column(Float, nullable=True)
    validation_status = Column(String(50), default="PENDING")
    approval_state = Column(String(50), default="RESEARCH_ONLY") # RESEARCH_ONLY, DEMO_APPROVED, LIVE_ALLOWLISTED
    result_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 13. market_data_sources
class MarketDataSource(Base):
    __tablename__ = "market_data_sources"
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(String(50), nullable=False) # CSV, MT5, SYNTHETIC, PUBLIC_API
    config_json = Column(JSON, nullable=True)
    is_healthy = Column(Boolean, default=True)
    last_check_at = Column(DateTime(timezone=True), default=utcnow)

# 14. datasets
class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String(50), primary_key=True)
    source_id = Column(String(50), ForeignKey("market_data_sources.id"), nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    bar_count = Column(Integer, default=0)
    data_quality_report = Column(JSON, nullable=True)
    file_path = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 15. experiment_runs
class ExperimentRun(Base):
    __tablename__ = "experiment_runs"
    id = Column(String(50), primary_key=True)
    task_id = Column(String(50), ForeignKey("agent_tasks.id"), nullable=True)
    candidate_id = Column(String(50), ForeignKey("strategy_candidates.candidate_id"), nullable=False, index=True)
    dataset_id = Column(String(50), ForeignKey("datasets.id"), nullable=True)
    status = Column(String(50), default="RUNNING") # RUNNING, COMPLETED, FAILED
    train_return = Column(Float, nullable=True)
    test_return = Column(Float, nullable=True)
    test_max_drawdown = Column(Float, nullable=True)
    test_win_rate = Column(Float, nullable=True)
    trades_count = Column(Integer, default=0)
    decision = Column(String(50), nullable=True)
    lesson = Column(Text, nullable=True)
    full_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 16. backtest_results
class BacktestResult(Base):
    __tablename__ = "backtest_results"
    id = Column(String(50), primary_key=True)
    experiment_id = Column(String(50), ForeignKey("experiment_runs.id"), nullable=False, index=True)
    equity_curve = Column(JSON, nullable=True)
    drawdown_curve = Column(JSON, nullable=True)
    trades_log = Column(JSON, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    expectancy = Column(Float, nullable=True)
    turnover = Column(Float, nullable=True)
    total_fees = Column(Float, nullable=True)
    slippage_cost = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 17. validation_results
class ValidationResult(Base):
    __tablename__ = "validation_results"
    id = Column(String(50), primary_key=True)
    candidate_id = Column(String(50), ForeignKey("strategy_candidates.candidate_id"), nullable=False, index=True)
    in_sample_metrics = Column(JSON, nullable=True)
    validation_metrics = Column(JSON, nullable=True)
    out_of_sample_metrics = Column(JSON, nullable=True)
    walk_forward_metrics = Column(JSON, nullable=True)
    regime_breakdown = Column(JSON, nullable=True)
    stress_test_metrics = Column(JSON, nullable=True)
    passed_all_gates = Column(Boolean, default=False)
    decision = Column(String(50), default="REJECTED_OR_INCONCLUSIVE")
    failure_reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 18. demo_experiments
class DemoExperiment(Base):
    __tablename__ = "demo_experiments"
    id = Column(String(50), primary_key=True)
    candidate_id = Column(String(50), ForeignKey("strategy_candidates.candidate_id"), nullable=False)
    broker_account_id = Column(String(50), ForeignKey("broker_accounts.id"), nullable=True)
    status = Column(String(50), default="ACTIVE") # ACTIVE, PAUSED, STOPPED
    initial_equity = Column(Float, default=10000.0)
    current_equity = Column(Float, default=10000.0)
    max_drawdown = Column(Float, default=0.0)
    trades_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 19. trade_proposals
class TradeProposal(Base):
    __tablename__ = "trade_proposals"
    id = Column(String(50), primary_key=True)
    strategy_id = Column(String(50), nullable=False)
    instrument = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False) # BUY, SELL
    suggested_entry = Column(Float, nullable=False)
    suggested_sl = Column(Float, nullable=False)
    suggested_tp = Column(Float, nullable=False)
    proposed_volume = Column(Float, nullable=False)
    rationale = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 20. risk_decisions
class RiskDecision(Base):
    __tablename__ = "risk_decisions"
    id = Column(String(50), primary_key=True)
    proposal_id = Column(String(50), ForeignKey("trade_proposals.id"), nullable=False)
    approved = Column(Boolean, nullable=False)
    decision_reason = Column(String(255), nullable=False)
    evaluated_checks = Column(JSON, nullable=False)
    adjusted_volume = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 21. broker_accounts
class BrokerAccount(Base):
    __tablename__ = "broker_accounts"
    id = Column(String(50), primary_key=True)
    broker_name = Column(String(50), nullable=False)
    account_number = Column(String(50), nullable=False)
    account_mode = Column(String(20), nullable=False) # DEMO, REAL
    currency = Column(String(10), default="USD")
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    margin = Column(Float, default=0.0)
    free_margin = Column(Float, default=0.0)
    is_connected = Column(Boolean, default=False)
    last_synced_at = Column(DateTime(timezone=True), default=utcnow)

# 22. broker_orders
class BrokerOrder(Base):
    __tablename__ = "broker_orders"
    id = Column(String(50), primary_key=True)
    idempotency_key = Column(String(100), unique=True, index=True)
    strategy_id = Column(String(50), nullable=True)
    account_mode = Column(String(20), nullable=False) # DEMO, LIVE
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False) # BUY, SELL
    requested_volume = Column(Float, nullable=False)
    filled_volume = Column(Float, default=0.0)
    requested_price = Column(Float, nullable=True)
    execution_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    broker_ticket = Column(Integer, nullable=True, index=True)
    state = Column(String(50), default="CREATED", index=True) # CREATED, VALIDATED, SUBMITTED, ACKNOWLEDGED, PARTIALLY_FILLED, FILLED, REJECTED, CANCELLED, EXPIRED, UNKNOWN
    rejection_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

# 23. broker_positions
class BrokerPosition(Base):
    __tablename__ = "broker_positions"
    id = Column(String(50), primary_key=True)
    ticket = Column(Integer, unique=True, nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    volume = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    unrealized_profit = Column(Float, default=0.0)
    magic_number = Column(Integer, default=610181)
    is_closed = Column(Boolean, default=False)
    opened_at = Column(DateTime(timezone=True), default=utcnow)
    closed_at = Column(DateTime(timezone=True), nullable=True)

# 24. broker_events
class BrokerEvent(Base):
    __tablename__ = "broker_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 25. trade_reviews
class TradeReview(Base):
    __tablename__ = "trade_reviews"
    id = Column(String(50), primary_key=True)
    position_ticket = Column(Integer, nullable=False, index=True)
    strategy_id = Column(String(50), nullable=True)
    realized_pnl = Column(Float, nullable=False)
    slippage = Column(Float, default=0.0)
    mfe = Column(Float, nullable=True) # Max favorable excursion
    mae = Column(Float, nullable=True) # Max adverse excursion
    rule_adherence = Column(Boolean, default=True)
    thesis_supported = Column(Boolean, default=False)
    observations = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 26. lessons
class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(String(50), primary_key=True)
    source_experiment_id = Column(String(50), nullable=True, index=True)
    observation = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    confidence = Column(Float, default=0.8)
    applicable_conditions = Column(String(255), nullable=True)
    verification_status = Column(String(50), default="UNVERIFIED") # UNVERIFIED, VERIFIED, REFUTED
    owner_feedback = Column(String(50), nullable=True) # GOOD_RESEARCH, INVALID_CONCLUSION, OVERFITTED, USEFUL
    owner_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 27. improvement_proposals
class ImprovementProposal(Base):
    __tablename__ = "improvement_proposals"
    id = Column(String(50), primary_key=True)
    target_component = Column(String(100), nullable=False) # PLANNER, STRATEGY_FACTORY, VALIDATION_GATE
    proposed_change = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    test_suite_result = Column(JSON, nullable=True)
    status = Column(String(50), default="PROPOSED") # PROPOSED, ACCEPTED, REJECTED
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 28. approval_events
class ApprovalEvent(Base):
    __tablename__ = "approval_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String(50), nullable=False) # LIVE_TRADE_ENABLE, LIMIT_CHANGE, STRATEGY_ALLOWLIST
    authorized_by = Column(String(100), nullable=False)
    details = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 29. audit_logs
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(100), nullable=False, index=True)
    actor = Column(String(50), default="SYSTEM")
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

# 30. system_health
class SystemHealth(Base):
    __tablename__ = "system_health"
    id = Column(Integer, primary_key=True, autoincrement=True)
    component = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False) # OK, WARN, ERROR
    details = Column(JSON, nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), default=utcnow)
