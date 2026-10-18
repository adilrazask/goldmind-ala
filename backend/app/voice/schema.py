"""Structured schemas for GoldMind ALA Voice Command System."""
from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class PermissionLevel(str, Enum):
    LEVEL_1_LOW_RISK = "LEVEL_1_LOW_RISK"             # Read-only market analysis, report reading, status checks
    LEVEL_2_CONTROLLED_RESEARCH = "LEVEL_2_CONTROLLED_RESEARCH" # Generating candidates, backtesting, parameter search
    LEVEL_3_PROTECTED_ACTION = "LEVEL_3_PROTECTED_ACTION"       # Modifying risk limits, live orders, live trading (BLOCKED via voice)

class VoiceCommandIntent(str, Enum):
    # Market Research Intents (Level 1)
    ANALYSE_MARKET = "analyse_market"
    GET_MARKET_STRUCTURE = "get_market_structure"
    CHECK_PRICE_DATA = "check_price_data"
    EXPLAIN_TREND_VOLATILITY = "explain_trend_volatility"
    IDENTIFY_SUPPORT_RESISTANCE = "identify_support_resistance"
    CHECK_INDICATORS = "check_indicators"
    EXPLAIN_MARKET_RISKS = "explain_market_risks"
    COMPARE_MARKETS = "compare_markets"
    GENERATE_MARKET_REPORT = "generate_market_report"

    # Strategy Research Intents (Level 1 & Level 2)
    REVIEW_STRATEGY_RESULTS = "review_strategy_results"
    BACKTEST_STRATEGY = "backtest_strategy"
    COMPARE_BENCHMARK = "compare_benchmark"
    SHOW_MAX_DRAWDOWN = "show_max_drawdown"
    CHECK_TRANSACTION_COSTS = "check_transaction_costs"
    EXPLAIN_POOR_PERFORMANCE = "explain_poor_performance"
    PREPARE_STRATEGY_REPORT = "prepare_strategy_report"

    # System Control Intents (Level 1 & Level 2)
    SHOW_AGENT_STATUS = "show_agent_status"
    CHECK_DATA_CONNECTION = "check_data_connection"
    PAUSE_RESEARCH = "pause_research"
    RESUME_RESEARCH = "resume_research"
    STOP_CURRENT_TASK = "stop_current_task"
    READ_LATEST_REPORT = "read_latest_report"
    SHOW_ACTIVITY_LOG = "show_activity_log"

    # Conversational Follow-up (Contextual)
    CONVERSATIONAL_FOLLOWUP = "conversational_followup"

    # Protected Operations (Level 3 - Strictly Blocked / Prohibited via Voice)
    CHANGE_RISK_LIMITS = "change_risk_limits"
    ENABLE_LIVE_TRADING = "enable_live_trading"
    PLACE_LIVE_ORDER = "place_live_order"
    MODIFY_BROKER_CREDENTIALS = "modify_broker_credentials"

    # Fallback
    UNKNOWN_COMMAND = "unknown_command"

class VoiceCommand(BaseModel):
    agent: str = "goldmind_ala"
    intent: VoiceCommandIntent
    raw_text: str
    symbol: Optional[str] = None
    secondary_symbol: Optional[str] = None
    timeframe: Optional[str] = None
    strategy_family: Optional[str] = None
    mode: str = "research_only"
    permission_level: PermissionLevel = PermissionLevel.LEVEL_1_LOW_RISK
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    is_blocked: bool = False
    blocked_reason: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None

class VoiceResponse(BaseModel):
    command_id: str
    intent: str
    permission_level: str
    status: str # SUCCESS, CONFIRMATION_REQUIRED, BLOCKED, ERROR, NEEDS_CLARIFICATION
    display_text: str
    spoken_summary: str
    data: Dict[str, Any] = Field(default_factory=dict)
    requires_passphrase: bool = False
    timestamp: str

class PassphraseVerificationRequest(BaseModel):
    passphrase: str
    session_id: Optional[str] = "default_session"

class PassphraseConfigUpdate(BaseModel):
    current_passphrase: Optional[str] = None
    new_passphrase: str
    enabled: bool = True
