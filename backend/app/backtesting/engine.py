"""Robust, Vectorized and Event-Aware Backtesting Engine with realistic transaction costs, spreads, and slippage."""
from __future__ import annotations
import math
import uuid
from typing import List, Dict, Any, Tuple
from backend.app.strategy_factory.families import compute_positions

class BacktestEngine:
    def __init__(
        self,
        cost_bps: float = 3.0,
        spread_points: int = 25,
        slippage_points: int = 10,
        initial_equity: float = 10000.0,
        point_value: float = 0.01
    ):
        self.cost_bps = cost_bps
        self.spread_points = spread_points
        self.slippage_points = slippage_points
        self.initial_equity = initial_equity
        self.point_value = point_value

    def run_backtest(
        self,
        candles: List[Dict[str, Any]],
        spec: Dict[str, Any],
        experiment_id: str | None = None
    ) -> Dict[str, Any]:
        if len(candles) < 20:
            raise ValueError(f"Need at least 20 candles for backtesting, got {len(candles)}")
            
        exp_id = experiment_id or str(uuid.uuid4())
        positions = compute_positions(candles, spec)
        
        n = len(candles)
        closes = [float(c["close"]) for c in candles]
        timestamps = [c["timestamp"] for c in candles]
        
        # Transaction costs in price terms
        spread_penalty = self.spread_points * self.point_value
        slippage_penalty = self.slippage_points * self.point_value
        total_slippage_spread_drag = spread_penalty + slippage_penalty
        
        equity = self.initial_equity
        peak_equity = equity
        
        equity_curve = [{"timestamp": timestamps[0], "equity": round(equity, 2)}]
        drawdown_curve = [{"timestamp": timestamps[0], "drawdown": 0.0}]
        
        trades = []
        in_trade = False
        entry_idx = 0
        entry_price = 0.0
        
        bar_returns = [0.0] * n
        total_fees = 0.0
        total_slippage = 0.0
        
        for i in range(1, n):
            pos_prev = positions[i - 1]
            pos_curr = positions[i]
            
            # Position change
            turnover = abs(pos_curr - pos_prev)
            market_ret = (closes[i] / closes[i - 1]) - 1.0 if closes[i - 1] > 0 else 0.0
            
            # Basis points fee
            bps_fee = turnover * (self.cost_bps / 10000.0)
            price_drag_pct = (total_slippage_spread_drag / closes[i]) * turnover if closes[i] > 0 else 0.0
            
            bar_ret = (pos_prev * market_ret) - bps_fee - price_drag_pct
            bar_returns[i] = bar_ret
            
            fee_dollars = equity * bps_fee
            slippage_dollars = equity * price_drag_pct
            total_fees += fee_dollars
            total_slippage += slippage_dollars
            
            equity *= max(1e-6, 1.0 + bar_ret)
            peak_equity = max(peak_equity, equity)
            dd = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0.0
            
            equity_curve.append({"timestamp": timestamps[i], "equity": round(equity, 2)})
            drawdown_curve.append({"timestamp": timestamps[i], "drawdown": round(dd, 4)})
            
            # Trade entry / exit tracking
            if not in_trade and pos_curr > 0:
                in_trade = True
                entry_idx = i
                entry_price = closes[i] + (spread_penalty / 2.0) + (slippage_penalty / 2.0)
            elif in_trade and pos_curr == 0:
                in_trade = False
                exit_price = closes[i] - (spread_penalty / 2.0) - (slippage_penalty / 2.0)
                trade_ret = (exit_price / entry_price) - 1.0
                trade_pnl = (exit_price - entry_price) * (self.initial_equity / entry_price)
                trades.append({
                    "entry_time": timestamps[entry_idx],
                    "exit_time": timestamps[i],
                    "bars_held": i - entry_idx,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "return_pct": round(trade_ret, 6),
                    "pnl": round(trade_pnl, 2)
                })

        # Calculate robust quantitative statistics
        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        
        gross_profit = sum(t["pnl"] for t in wins)
        gross_loss = abs(sum(t["pnl"] for t in losses))
        
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)
        win_rate = len(wins) / len(trades) if trades else 0.0
        avg_win = (gross_profit / len(wins)) if wins else 0.0
        avg_loss = (gross_loss / len(losses)) if losses else 0.0
        expectancy = (win_rate * avg_win) - ((1.0 - win_rate) * avg_loss)
        
        total_return = (equity / self.initial_equity) - 1.0
        max_drawdown = max([pt["drawdown"] for pt in drawdown_curve]) if drawdown_curve else 0.0
        
        # Daily annualized Sharpe calculation (assuming ~96 M15 bars per day -> ~24000 bars per year)
        active_returns = [r for r in bar_returns[1:] if abs(r) > 1e-12]
        if active_returns and len(active_returns) > 5:
            mean_r = sum(active_returns) / len(active_returns)
            var_r = sum((r - mean_r)**2 for r in active_returns) / len(active_returns)
            std_r = math.sqrt(var_r)
            annual_factor = math.sqrt(24000)
            sharpe_ratio = (mean_r / std_r) * annual_factor if std_r > 0 else 0.0
            
            # Sortino ratio (downside deviation)
            downside_r = [r for r in active_returns if r < 0]
            if downside_r:
                downside_std = math.sqrt(sum(r**2 for r in downside_r) / len(downside_r))
                sortino_ratio = (mean_r / downside_std) * annual_factor if downside_std > 0 else 0.0
            else:
                sortino_ratio = sharpe_ratio
        else:
            sharpe_ratio = 0.0
            sortino_ratio = 0.0

        calmar_ratio = (total_return / max_drawdown) if max_drawdown > 0 else 0.0
        
        # Exposure %
        bars_in_market = sum(1 for p in positions if p > 0)
        exposure_pct = bars_in_market / float(n) if n > 0 else 0.0

        return {
            "experiment_id": exp_id,
            "observations": n,
            "total_return": round(total_return, 6),
            "max_drawdown": round(max_drawdown, 6),
            "win_rate": round(win_rate, 4),
            "trades_count": len(trades),
            "profit_factor": round(min(profit_factor, 99.0), 3),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "sortino_ratio": round(sortino_ratio, 3),
            "calmar_ratio": round(calmar_ratio, 3),
            "expectancy": round(expectancy, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "exposure_pct": round(exposure_pct, 4),
            "total_fees": round(total_fees, 2),
            "total_slippage": round(total_slippage, 2),
            "equity_curve": equity_curve,
            "drawdown_curve": drawdown_curve,
            "trades_log": trades[-50:] # keep recent trades for display
        }
