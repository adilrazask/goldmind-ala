"""Synthetic-only research tools. These deliberately do not fetch real market data."""
import math
import random
import uuid
from .models import ExperimentResult


def _synthetic_returns(seed: int, n: int = 600) -> list[float]:
    rng = random.Random(seed)
    values = []
    for i in range(n):
        regime = (i // 100) % 3
        drift = {0: 0.00045, 1: -0.00025, 2: 0.0}[regime]
        volatility = {0: 0.006, 1: 0.008, 2: 0.004}[regime]
        values.append(drift + rng.gauss(0, volatility))
    return values


def _moving_average_signal(returns: list[float], window: int = 8) -> list[float]:
    signal = [0.0] * len(returns)
    for i in range(window, len(returns)):
        avg = sum(returns[i-window:i]) / window
        signal[i] = 1.0 if avg > 0 else (-1.0 if avg < 0 else 0.0)
    return signal


def _equity_metrics(strategy_returns: list[float]) -> tuple[float, float, float]:
    equity, peak, max_dd = 1.0, 1.0, 0.0
    wins = active = 0
    for r in strategy_returns:
        equity *= max(0.000001, 1.0 + r)
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak)
        if r != 0:
            active += 1
            if r > 0:
                wins += 1
    return equity - 1.0, max_dd, (wins / active if active else 0.0)


def run_synthetic_experiment(objective: str, hypothesis: str, seed: int = 1729) -> ExperimentResult:
    raw = _synthetic_returns(seed)
    split = int(len(raw) * 0.7)
    signal = _moving_average_signal(raw)
    strategy_returns = []
    previous = 0.0
    for i, r in enumerate(raw):
        current = signal[i]
        turnover_cost = 0.00015 if current != previous else 0.0
        strategy_returns.append(current * r - turnover_cost)
        previous = current
    train_ret, _, _ = _equity_metrics(strategy_returns[:split])
    test_ret, test_dd, test_win = _equity_metrics(strategy_returns[split:])
    passed = test_ret > 0.0 and test_dd <= 0.20 and math.isfinite(test_ret)
    decision = "KEEP_FOR_FURTHER_RESEARCH" if passed else "REJECT_OR_REVISE"
    lesson = ("Toy test passed the initial illustrative gate; it still needs real-data, costs, walk-forward and out-of-sample validation."
              if passed else "Toy test did not pass the initial illustrative gate. Change one research assumption and retest; do not tune repeatedly to this same sample.")
    return ExperimentResult(str(uuid.uuid4()), objective, hypothesis, "toy_past_return_momentum", len(raw), round(train_ret, 6), round(test_ret, 6), round(test_dd, 6), round(test_win, 6), passed, decision, lesson)
