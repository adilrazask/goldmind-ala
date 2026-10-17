"""Deterministic implementations of all 10 supported strategy families.
Strictly eliminates look-ahead bias: a signal calculated at candle t is only applied at candle t+1.
"""
from __future__ import annotations
import math
from typing import List, Dict, Any
from datetime import datetime

ALLOWED_FAMILIES = {
    "moving_average_crossover",
    "momentum",
    "breakout",
    "rsi_mean_reversion",
    "volatility_filtered",
    "trend_following",
    "multi_timeframe_confirmation",
    "atr_volatility_adaptation",
    "session_based",
    "composite_combination"
}

def _sma(values: List[float], end_idx: int, window: int) -> float:
    if end_idx < window - 1 or window <= 0:
        return values[end_idx]
    return sum(values[end_idx - window + 1 : end_idx + 1]) / float(window)

def _ema(values: List[float], end_idx: int, window: int) -> float:
    k = 2.0 / (window + 1.0)
    ema = values[0]
    for i in range(1, end_idx + 1):
        ema = values[i] * k + ema * (1.0 - k)
    return ema

def _rsi(values: List[float], end_idx: int, period: int) -> float:
    if end_idx < period:
        return 50.0
    gains = []
    losses = []
    for i in range(end_idx - period + 1, end_idx + 1):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0 if avg_gain else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def _atr(highs: List[float], lows: List[float], closes: List[float], end_idx: int, period: int) -> float:
    if end_idx < 1:
        return highs[end_idx] - lows[end_idx]
    start = max(1, end_idx - period + 1)
    trs = []
    for i in range(start, end_idx + 1):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        trs.append(tr)
    return sum(trs) / len(trs) if trs else 1.0

def compute_positions(candles: List[Dict[str, Any]], spec: Dict[str, Any]) -> List[float]:
    family = spec.get("family")
    if family not in ALLOWED_FAMILIES:
        raise ValueError(f"Unsupported strategy family: {family}")
    
    n = len(candles)
    if n < 20:
        raise ValueError(f"Need at least 20 candles, got {n}")
        
    closes = [float(c["close"]) for c in candles]
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    opens = [float(c["open"]) for c in candles]
    timestamps = [c["timestamp"] for c in candles]
    
    params = spec.get("parameters", {})
    pos = [0.0] * n
    
    if family == "moving_average_crossover":
        fast = int(params.get("fast", 10))
        slow = int(params.get("slow", 30))
        if not (2 <= fast < slow <= 200):
            raise ValueError(f"Invalid MA parameters: fast={fast}, slow={slow}")
        for i in range(slow - 1, n - 1):
            f_ma = _sma(closes, i, fast)
            s_ma = _sma(closes, i, slow)
            pos[i + 1] = 1.0 if f_ma > s_ma else 0.0

    elif family == "momentum":
        lookback = int(params.get("lookback", 5))
        threshold = float(params.get("threshold", 0.002))
        if not (1 <= lookback <= 100 and 0.0 <= threshold <= 0.1):
            raise ValueError("Invalid momentum parameters")
        for i in range(lookback, n - 1):
            ret = closes[i] / closes[i - lookback] - 1.0
            pos[i + 1] = 1.0 if ret > threshold else 0.0

    elif family == "breakout":
        lookback = int(params.get("lookback", 20))
        pct = float(params.get("breakout_pct", 0.001))
        if not (2 <= lookback <= 100 and 0.0 <= pct <= 0.1):
            raise ValueError("Invalid breakout parameters")
        for i in range(lookback, n - 1):
            highest = max(highs[i - lookback : i])
            pos[i + 1] = 1.0 if closes[i] > highest * (1.0 + pct) else 0.0

    elif family == "rsi_mean_reversion":
        period = int(params.get("period", 14))
        lower = float(params.get("lower", 30))
        exit_level = float(params.get("exit_level", 50))
        if not (2 <= period <= 100 and 5 <= lower <= 45 and lower < exit_level <= 85):
            raise ValueError("Invalid RSI parameters")
        holding = False
        for i in range(period, n - 1):
            rsi = _rsi(closes, i, period)
            if not holding and rsi < lower:
                holding = True
            elif holding and rsi >= exit_level:
                holding = False
            pos[i + 1] = 1.0 if holding else 0.0

    elif family == "volatility_filtered":
        mom_lookback = int(params.get("lookback", 8))
        vol_window = int(params.get("vol_window", 20))
        min_vol = float(params.get("min_vol_pct", 0.001))
        max_vol = float(params.get("max_vol_pct", 0.03))
        start = max(mom_lookback, vol_window)
        for i in range(start, n - 1):
            # Rolling std dev of returns
            recent_ret = [closes[j]/closes[j-1] - 1.0 for j in range(i - vol_window + 1, i + 1)]
            mean_ret = sum(recent_ret) / len(recent_ret)
            variance = sum((r - mean_ret)**2 for r in recent_ret) / len(recent_ret)
            std_vol = math.sqrt(variance)
            mom = closes[i] / closes[i - mom_lookback] - 1.0
            if min_vol <= std_vol <= max_vol and mom > 0:
                pos[i + 1] = 1.0
            else:
                pos[i + 1] = 0.0

    elif family == "trend_following":
        trend_ma = int(params.get("trend_ma", 50))
        trigger_ma = int(params.get("trigger_ma", 15))
        if not (5 <= trigger_ma < trend_ma <= 250):
            raise ValueError("Invalid trend following parameters")
        for i in range(trend_ma, n - 1):
            above_trend = closes[i] > _sma(closes, i, trend_ma)
            pullback_bounce = closes[i] > _sma(closes, i, trigger_ma)
            pos[i + 1] = 1.0 if (above_trend and pullback_bounce) else 0.0

    elif family == "multi_timeframe_confirmation":
        # Simulate higher timeframe (e.g. 4x slower window)
        slow_factor = int(params.get("higher_tf_factor", 4))
        base_fast = int(params.get("fast", 8))
        base_slow = int(params.get("slow", 24))
        htf_period = base_slow * slow_factor
        for i in range(htf_period, n - 1):
            htf_trend = closes[i] > _sma(closes, i, htf_period)
            ltf_signal = _sma(closes, i, base_fast) > _sma(closes, i, base_slow)
            pos[i + 1] = 1.0 if (htf_trend and ltf_signal) else 0.0

    elif family == "atr_volatility_adaptation":
        period = int(params.get("period", 14))
        multiplier = float(params.get("multiplier", 1.5))
        ma_period = int(params.get("ma_period", 20))
        for i in range(max(period, ma_period), n - 1):
            atr_val = _atr(highs, lows, closes, i, period)
            band = _sma(closes, i, ma_period) + multiplier * atr_val
            pos[i + 1] = 1.0 if closes[i] > band else 0.0

    elif family == "session_based":
        # Filters trades by allowed UTC hours
        start_hour = int(params.get("start_hour", 8)) # e.g. London open 08:00 UTC
        end_hour = int(params.get("end_hour", 16))     # e.g. NY session 16:00 UTC
        base_lookback = int(params.get("lookback", 10))
        for i in range(base_lookback, n - 1):
            dt = datetime.fromisoformat(timestamps[i].replace("Z", "+00:00"))
            hour = dt.hour
            in_session = (start_hour <= hour <= end_hour) if start_hour <= end_hour else (hour >= start_hour or hour <= end_hour)
            trend = closes[i] > _sma(closes, i, base_lookback)
            pos[i + 1] = 1.0 if (in_session and trend) else 0.0

    elif family == "composite_combination":
        # Combinations of 2 validated components: e.g. Trend + RSI Mean Reversion
        ma_win = int(params.get("trend_filter_ma", 30))
        rsi_p = int(params.get("rsi_period", 14))
        rsi_l = float(params.get("rsi_lower", 35))
        rsi_exit = float(params.get("rsi_exit", 55))
        holding = False
        start = max(ma_win, rsi_p)
        for i in range(start, n - 1):
            uptrend = closes[i] > _sma(closes, i, ma_win)
            rsi_val = _rsi(closes, i, rsi_p)
            if not holding and uptrend and rsi_val < rsi_l:
                holding = True
            elif holding and (rsi_val >= rsi_exit or not uptrend):
                holding = False
            pos[i + 1] = 1.0 if holding else 0.0

    return pos
