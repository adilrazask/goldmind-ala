"""A deliberately small, long-only SMA crossover backtest for CSV candles."""
from dataclasses import dataclass, asdict
import math
import uuid
from .market_data import Candle

@dataclass
class BacktestReport:
    experiment_id: str
    strategy_name: str
    observations: int
    fast_window: int
    slow_window: int
    cost_bps_per_position_change: float
    train_return: float
    test_return: float
    test_max_drawdown: float
    test_win_rate: float
    test_trade_changes: int
    validation_passed: bool
    decision: str
    lesson: str
    data_start: str
    data_end: str
    def to_dict(self): return asdict(self)
    def to_json(self):
        import json
        return json.dumps(self.to_dict(), indent=2)

def _sma(values: list[float], end: int, window: int) -> float:
    return sum(values[end-window+1:end+1]) / window

def _metrics(returns: list[float]) -> tuple[float, float, float]:
    equity = peak = 1.0
    max_dd = 0.0
    active = wins = 0
    for r in returns:
        equity *= max(1e-12, 1.0 + r)
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak-equity)/peak)
        if abs(r) > 1e-15:
            active += 1
            wins += int(r > 0)
    return equity-1.0, max_dd, (wins/active if active else 0.0)

def run_sma_backtest(candles: list[Candle], fast: int = 10, slow: int = 30, cost_bps: float = 2.0) -> BacktestReport:
    if fast < 2 or slow <= fast:
        raise ValueError("Require 2 <= fast window < slow window")
    if cost_bps < 0 or not math.isfinite(cost_bps):
        raise ValueError("cost-bps must be finite and non-negative")
    if len(candles) < max(50, slow + 10):
        raise ValueError(f"Need at least {max(50, slow+10)} candles for these windows")
    closes = [c["close"] for c in candles]
    # A signal is calculated with candle t close, then held from t+1 to avoid same-bar look-ahead.
    positions = [0.0] * len(closes)
    for i in range(slow-1, len(closes)-1):
        positions[i+1] = 1.0 if _sma(closes, i, fast) > _sma(closes, i, slow) else 0.0
    bar_returns = [0.0] * len(closes)
    for i in range(1, len(closes)):
        market_ret = closes[i] / closes[i-1] - 1.0
        change = abs(positions[i] - positions[i-1])
        bar_returns[i] = positions[i-1] * market_ret - change * (cost_bps / 10000.0)
    split = int(len(closes)*0.7)
    train_ret, _, _ = _metrics(bar_returns[1:split])
    test = bar_returns[split:]
    test_ret, test_dd, test_win = _metrics(test)
    changes = sum(1 for i in range(split, len(positions)) if positions[i] != positions[i-1])
    # Gate is intentionally conservative but still only a preliminary filter, not proof of edge.
    passed = math.isfinite(test_ret) and test_ret > 0 and test_dd <= 0.20 and changes > 0
    decision = "KEEP_FOR_FURTHER_RESEARCH" if passed else "REJECT_OR_REVISE"
    lesson = ("Preliminary CSV test passed a simple gate; run additional untouched out-of-sample and walk-forward tests with broker-specific costs before drawing conclusions." if passed else "Candidate did not pass the preliminary gate on this test split. Do not tune repeatedly against this same test split; revise one assumption and reserve fresh data for validation.")
    return BacktestReport(str(uuid.uuid4()), "long_only_sma_crossover", len(candles), fast, slow, cost_bps, round(train_ret,6), round(test_ret,6), round(test_dd,6), round(test_win,6), changes, passed, decision, lesson, candles[0]["timestamp"], candles[-1]["timestamp"])
