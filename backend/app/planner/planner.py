"""Structured Research Planner: Translates natural language objectives into executable task sequences."""
from __future__ import annotations
import uuid
import re
from typing import Dict, Any, List
from backend.app.strategy_factory.families import ALLOWED_FAMILIES

class ResearchPlanner:
    def parse_objective(self, raw_prompt: str) -> Dict[str, Any]:
        """Parses natural-language user prompt into target instrument, timeframe, and strategy family."""
        prompt_lower = raw_prompt.lower()
        
        # Detect instruments
        instrument = "XAUUSD"
        if "btcusd" in prompt_lower or "btc" in prompt_lower or "bitcoin" in prompt_lower:
            instrument = "BTCUSD"
        elif "xauusd" in prompt_lower or "gold" in prompt_lower or "xau" in prompt_lower:
            instrument = "XAUUSD"
            
        # Detect timeframe
        timeframe = "M15"
        for tf in ["m1", "m5", "m15", "m30", "h1", "h4", "d1"]:
            if tf in prompt_lower:
                timeframe = tf.upper()
                break

        # Detect target family
        target_family = None
        for fam in ALLOWED_FAMILIES:
            clean_fam = fam.replace("_", " ")
            if clean_fam in prompt_lower or fam in prompt_lower:
                target_family = fam
                break
                
        if not target_family:
            if "rsi" in prompt_lower or "mean reversion" in prompt_lower:
                target_family = "rsi_mean_reversion"
            elif "breakout" in prompt_lower or "channel" in prompt_lower:
                target_family = "breakout"
            elif "crossover" in prompt_lower or "moving average" in prompt_lower or "sma" in prompt_lower:
                target_family = "moving_average_crossover"
            elif "volatility" in prompt_lower or "atr" in prompt_lower:
                target_family = "volatility_filtered"
            else:
                target_family = "momentum"

        return {
            "instrument": instrument,
            "timeframe": timeframe,
            "target_family": target_family,
            "requires_demo_promotion": "demo" in prompt_lower
        }

    def generate_plan(self, objective_id: str, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decomposes parsed research intent into a 5-step structured research task queue."""
        inst = parsed["instrument"]
        tf = parsed["timeframe"]
        fam = parsed["target_family"]
        
        tasks = [
            {
                "task_id": f"task_{uuid.uuid4().hex[:8]}",
                "objective_id": objective_id,
                "task_type": "DATA_PREPARATION",
                "prerequisites": [],
                "required_tools": ["market_data_retrieval", "data_quality_checks"],
                "input_data": {"symbol": inst, "timeframe": tf, "bars": 600},
                "expected_output": "Clean historical dataset with validated OHLCV integrity and regime classification",
                "success_criteria": "Audit report confirms zero duplicate timestamps and valid price continuity",
                "resource_budget": {"max_memory_mb": 128, "timeout_seconds": 15},
                "permission_requirements": ["read_market_data"],
                "retry_policy": {"max_retries": 2, "backoff_seconds": 2},
                "status": "PENDING"
            },
            {
                "task_id": f"task_{uuid.uuid4().hex[:8]}",
                "objective_id": objective_id,
                "task_type": "STRATEGY_GENERATION",
                "prerequisites": ["DATA_PREPARATION"],
                "required_tools": ["strategy_generation", "unit_testing"],
                "input_data": {"family": fam, "instrument": inst, "timeframe": tf},
                "expected_output": "Allowlisted declarative strategy candidate specification with tested parameters",
                "success_criteria": "Strategy passes schema verification and sandbox causality checks",
                "resource_budget": {"max_memory_mb": 64, "timeout_seconds": 10},
                "permission_requirements": ["generate_declarative_spec"],
                "retry_policy": {"max_retries": 1, "backoff_seconds": 1},
                "status": "PENDING"
            },
            {
                "task_id": f"task_{uuid.uuid4().hex[:8]}",
                "objective_id": objective_id,
                "task_type": "BACKTEST_EVALUATION",
                "prerequisites": ["STRATEGY_GENERATION"],
                "required_tools": ["historical_backtesting"],
                "input_data": {"cost_bps": 3.0, "spread_points": 25, "slippage_points": 10},
                "expected_output": "Detailed equity curve, drawdown trajectory, trade log, and Sharpe/Sortino metrics",
                "success_criteria": "Execution accounts for spreads and turnover fees without look-ahead bias",
                "resource_budget": {"max_memory_mb": 128, "timeout_seconds": 20},
                "permission_requirements": ["run_backtest"],
                "retry_policy": {"max_retries": 1, "backoff_seconds": 1},
                "status": "PENDING"
            },
            {
                "task_id": f"task_{uuid.uuid4().hex[:8]}",
                "objective_id": objective_id,
                "task_type": "STATISTICAL_VALIDATION",
                "prerequisites": ["BACKTEST_EVALUATION"],
                "required_tools": ["statistical_validation"],
                "input_data": {"walk_forward_windows": 3, "stress_multiplier": 2.0},
                "expected_output": "Rigorous In-Sample vs Validation vs Out-of-Sample, walk-forward, and regime breakdown report",
                "success_criteria": "Decision to either certify as STATISTICALLY_VALIDATED or REJECT_OR_INCONCLUSIVE",
                "resource_budget": {"max_memory_mb": 256, "timeout_seconds": 30},
                "permission_requirements": ["run_validation"],
                "retry_policy": {"max_retries": 1, "backoff_seconds": 1},
                "status": "PENDING"
            },
            {
                "task_id": f"task_{uuid.uuid4().hex[:8]}",
                "objective_id": objective_id,
                "task_type": "KNOWLEDGE_SYNTHESIS",
                "prerequisites": ["STATISTICAL_VALIDATION"],
                "required_tools": ["reporting"],
                "input_data": {"memory_tier": "EXPERIENCE"},
                "expected_output": "Synthesized lesson, evidence record, and subsequent research recommendation",
                "success_criteria": "Persistent recording in SQLite/Postgres memory with auditable limitations",
                "resource_budget": {"max_memory_mb": 64, "timeout_seconds": 10},
                "permission_requirements": ["write_memory"],
                "retry_policy": {"max_retries": 2, "backoff_seconds": 1},
                "status": "PENDING"
            }
        ]
        return tasks
