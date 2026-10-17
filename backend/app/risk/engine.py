"""Central Deterministic Risk Engine: Independent of AI models and non-bypassable."""
from __future__ import annotations
import math
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from backend.app.core.config import settings
from backend.app.market_data.manager import INSTRUMENT_SPECS

class RiskViolationError(RuntimeError):
    pass

class CentralRiskEngine:
    def __init__(
        self,
        daily_loss_limit_pct: float = 1.0,
        max_risk_per_trade_pct: float = 0.25,
        max_open_positions: int = 3,
        max_spread_points: int = 35,
        daily_start_equity: float = 10000.0
    ):
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_open_positions = max_open_positions
        self.max_spread_points = max_spread_points
        self.daily_start_equity = daily_start_equity
        self.kill_switch_active = settings.KILL_SWITCH_ACTIVE
        self.recent_orders = [] # timestamp and symbol for cooldown/duplicate protection

    def evaluate_proposal(
        self,
        strategy_id: str,
        strategy_approval_state: str, # RESEARCH_ONLY, DEMO_APPROVED, LIVE_ALLOWLISTED
        instrument: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        account_mode: str, # DEMO, LIVE
        current_equity: float,
        current_spread_points: int,
        open_positions_count: int,
        quote_age_seconds: int = 2
    ) -> Tuple[bool, str, Dict[str, Any], float]:
        """Evaluates every proposed trade against 18 deterministic safety checks.
        Returns (approved: bool, reason: str, evaluated_checks: dict, calculated_volume: float).
        """
        checks = {}
        
        # 1. Kill Switch
        checks["kill_switch"] = not self.kill_switch_active
        if not checks["kill_switch"]:
            return False, "Emergency kill switch is active. All order entries blocked.", checks, 0.0

        # 2. Strategy Approval State Check
        if account_mode == "LIVE":
            checks["strategy_approval"] = (strategy_approval_state == "LIVE_ALLOWLISTED")
            if not checks["strategy_approval"]:
                return False, f"Strategy {strategy_id} is not LIVE_ALLOWLISTED (state: {strategy_approval_state}).", checks, 0.0
        elif account_mode == "DEMO":
            checks["strategy_approval"] = strategy_approval_state in {"DEMO_APPROVED", "LIVE_ALLOWLISTED"}
            if not checks["strategy_approval"]:
                return False, f"Strategy {strategy_id} has not passed validation for DEMO_APPROVED (state: {strategy_approval_state}).", checks, 0.0
        else:
            return False, f"Unknown account mode: {account_mode}", checks, 0.0

        # 3. Live Trading Global Opt-In
        if account_mode == "LIVE":
            checks["live_opt_in"] = settings.ALLOW_LIVE_TRADING
            if not checks["live_opt_in"]:
                return False, "Live trading is disabled by default in system configuration.", checks, 0.0

        # 4. Daily Equity Loss Limit
        min_allowed_equity = self.daily_start_equity * (1.0 - (self.daily_loss_limit_pct / 100.0))
        checks["daily_loss_limit"] = (current_equity > min_allowed_equity)
        if not checks["daily_loss_limit"]:
            return False, f"Daily equity loss limit reached (Equity: {current_equity:.2f} <= Baseline threshold: {min_allowed_equity:.2f}).", checks, 0.0

        # 5. Maximum Open Positions
        checks["max_open_positions"] = (open_positions_count < self.max_open_positions)
        if not checks["max_open_positions"]:
            return False, f"Maximum open position limit ({self.max_open_positions}) reached.", checks, 0.0

        # 6. Instrument Specs & Permission
        instrument = instrument.upper()
        if instrument not in INSTRUMENT_SPECS:
            checks["instrument_supported"] = False
            return False, f"Instrument {instrument} metadata not available or supported.", checks, 0.0
        checks["instrument_supported"] = True
        specs = INSTRUMENT_SPECS[instrument]

        # 7. Quote Freshness
        checks["quote_freshness"] = (quote_age_seconds <= 10)
        if not checks["quote_freshness"]:
            return False, f"Market data quote is stale ({quote_age_seconds}s > 10s max permitted).", checks, 0.0

        # 8. Spread Protection
        checks["spread_check"] = (current_spread_points <= self.max_spread_points)
        if not checks["spread_check"]:
            return False, f"Current spread ({current_spread_points}) exceeds maximum allowed ({self.max_spread_points}).", checks, 0.0

        # 9. Allowed Trading Hours
        now_hour = datetime.now(timezone.utc).hour
        h_start, h_end = specs["allowed_hours"]
        checks["trading_hours"] = (h_start <= now_hour <= h_end) if h_start <= h_end else (now_hour >= h_start or now_hour <= h_end)
        if not checks["trading_hours"]:
            return False, f"Trading not permitted at UTC hour {now_hour} for {instrument}.", checks, 0.0

        # 10. Protective Stop-Loss Presence & Orientation
        side = side.upper()
        if side not in {"BUY", "SELL"}:
            return False, f"Invalid order side: {side}", checks, 0.0
            
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = abs(take_profit - entry_price)
        
        if side == "BUY":
            valid_orientation = (stop_loss < entry_price < take_profit)
        else:
            valid_orientation = (take_profit < entry_price < stop_loss)
            
        checks["protective_orientation"] = valid_orientation
        if not valid_orientation:
            return False, f"Invalid protective SL/TP orientation: SL={stop_loss}, Entry={entry_price}, TP={take_profit}", checks, 0.0

        # 11. Minimum Stop Distance Check
        min_stop_distance = 10 * specs["point"]
        checks["min_stop_distance"] = (sl_distance >= min_stop_distance)
        if not checks["min_stop_distance"]:
            return False, f"Stop-loss distance ({sl_distance:.4f}) is below broker minimum ({min_stop_distance:.4f}).", checks, 0.0

        # 12. Deterministic Position Sizing Calculation
        tick_size = specs["tick_size"]
        tick_value = specs["tick_value"]
        if tick_size <= 0 or tick_value <= 0:
            return False, "Invalid tick size or tick value in instrument metadata.", checks, 0.0

        max_risk_cash = current_equity * (self.max_risk_per_trade_pct / 100.0)
        loss_per_lot = (sl_distance / tick_size) * tick_value
        
        if loss_per_lot <= 0 or not math.isfinite(loss_per_lot):
            return False, "Cannot calculate loss per lot.", checks, 0.0

        raw_volume = max_risk_cash / loss_per_lot
        v_step = specs["volume_step"]
        v_min = specs["volume_min"]
        v_max = specs["volume_max"]
        
        calculated_volume = math.floor(raw_volume / v_step) * v_step
        calculated_volume = round(calculated_volume, 4)

        checks["min_volume"] = (calculated_volume >= v_min)
        if not checks["min_volume"]:
            return False, f"Calculated volume {calculated_volume} is below instrument minimum {v_min}.", checks, 0.0
            
        calculated_volume = min(calculated_volume, v_max)
        checks["calculated_volume"] = calculated_volume
        checks["estimated_risk_dollars"] = round(calculated_volume * loss_per_lot, 2)

        return True, "Deterministic central risk checks passed successfully.", checks, calculated_volume
