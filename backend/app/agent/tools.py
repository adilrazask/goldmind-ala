"""Bounded Tool Registry: Safe, explicit interfaces preventing arbitrary shell or filesystem calls."""
from __future__ import annotations
import json
from typing import Dict, Any, Callable
from backend.app.market_data.manager import MarketDataManager, DataQualityAudit
from backend.app.strategy_factory.generator import generate_family_candidates, generate_all_candidates
from backend.app.sandbox.validator import static_code_analysis, verify_sandbox_execution
from backend.app.backtesting.engine import BacktestEngine
from backend.app.validation.validator import MultiStageValidator

class BoundedToolRegistry:
    def __init__(self, data_mgr: MarketDataManager, validator: MultiStageValidator):
        self.data_mgr = data_mgr
        self.validator = validator
        self.engine = BacktestEngine()
        self.tools: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "market_data_retrieval": self._tool_market_data,
            "data_quality_checks": self._tool_data_quality,
            "strategy_generation": self._tool_strategy_generation,
            "static_code_analysis": self._tool_static_code_analysis,
            "unit_testing": self._tool_unit_testing,
            "historical_backtesting": self._tool_historical_backtesting,
            "statistical_validation": self._tool_statistical_validation,
            "reporting": self._tool_reporting
        }

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.tools:
            raise PermissionError(f"Tool '{tool_name}' is not in the allowlisted tool registry.")
        # Execute registered function
        return self.tools[tool_name](params)

    def _tool_market_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        symbol = params.get("symbol", "XAUUSD")
        timeframe = params.get("timeframe", "M15")
        bars = int(params.get("bars", 400))
        candles, audit = self.data_mgr.generate_regime_dataset(symbol=symbol, timeframe=timeframe, bars=bars)
        return {"bars_count": len(candles), "audit": audit, "sample_bar": candles[-1]}

    def _tool_data_quality(self, params: Dict[str, Any]) -> Dict[str, Any]:
        candles = params.get("candles", [])
        return DataQualityAudit.audit_candles(candles)

    def _tool_strategy_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        family = params.get("family")
        instrument = params.get("instrument", "XAUUSD")
        timeframe = params.get("timeframe", "M15")
        if family:
            cands = generate_family_candidates(family, instrument, timeframe)
        else:
            cands = generate_all_candidates(instrument, timeframe)
        return {"candidates_generated": len(cands), "sample": cands[0] if cands else None}

    def _tool_static_code_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        valid, errors = static_code_analysis(code)
        return {"valid": valid, "errors": errors}

    def _tool_unit_testing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        spec = params.get("spec", {})
        passed, msg = verify_sandbox_execution(spec)
        return {"passed": passed, "message": msg}

    def _tool_historical_backtesting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        candles = params.get("candles")
        spec = params.get("spec")
        cost_bps = float(params.get("cost_bps", 3.0))
        engine = BacktestEngine(cost_bps=cost_bps)
        res = engine.run_backtest(candles, spec)
        return {
            "total_return": res["total_return"],
            "max_drawdown": res["max_drawdown"],
            "profit_factor": res["profit_factor"],
            "trades_count": res["trades_count"]
        }

    def _tool_statistical_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        candles = params.get("candles")
        spec = params.get("spec")
        cand_id = params.get("candidate_id", "test_cand")
        return self.validator.validate_candidate(candles, spec, cand_id)

    def _tool_reporting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"report_generated": True, "summary": params.get("summary", "")}
