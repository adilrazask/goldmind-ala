"""Strategy Generator: creates bounded, declarative strategy candidates across all 10 families."""
from __future__ import annotations
import uuid
import itertools
from typing import List, Dict, Any, Optional
from .families import ALLOWED_FAMILIES

FAMILY_HYPOTHESES = {
    "moving_average_crossover": "A faster moving average crossing above a slower moving average captures sustained directional momentum.",
    "momentum": "Assets demonstrating positive relative price changes over a short lookback window tend to persist in the near term.",
    "breakout": "A decisive break above recent historical price highs signals institutional accumulation and continuation.",
    "rsi_mean_reversion": "Temporary oversold oscillators in liquid assets revert towards central mean prices when selling exhaust finishes.",
    "volatility_filtered": "Momentum signals perform with higher risk-adjusted return when market volatility is in a moderate regime.",
    "trend_following": "Trading in the direction of the dominant macro trend while buying minor pullbacks minimizes whipsaw.",
    "multi_timeframe_confirmation": "Requiring higher timeframe trend alignment before entering lower timeframe triggers filters countertrend noise.",
    "atr_volatility_adaptation": "Adapting breakout bands dynamically to market ATR accounts for regime shifts and expansion phases.",
    "session_based": "Concentrating entries during peak institutional liquidity sessions (London/NY overlap) reduces spread drag and slippage.",
    "composite_combination": "Combining trend filters with oversold mean-reversion entries provides high expectancy with controlled drawdown."
}

def generate_family_candidates(family: str, instrument: str = "XAUUSD", timeframe: str = "M15") -> List[Dict[str, Any]]:
    candidates = []
    
    if family == "moving_average_crossover":
        for fast, slow in [(5, 20), (8, 25), (10, 30), (15, 45), (20, 60)]:
            candidates.append({
                "family": family,
                "instrument": instrument,
                "timeframe": timeframe,
                "side": "long_only",
                "parameters": {"fast": fast, "slow": slow},
                "hypothesis": f"Fast SMA({fast}) crossing Slow SMA({slow}) captures {instrument} {timeframe} trend phases."
            })
            
    elif family == "momentum":
        for lookback in [3, 5, 8, 12, 16]:
            for thresh in [0.001, 0.002, 0.003]:
                candidates.append({
                    "family": family,
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "side": "long_only",
                    "parameters": {"lookback": lookback, "threshold": thresh},
                    "hypothesis": f"Positive momentum > {thresh*100}% over {lookback} bars identifies persistent continuation in {instrument}."
                })

    elif family == "breakout":
        for lookback in [10, 20, 30, 40]:
            for pct in [0.0005, 0.001, 0.002]:
                candidates.append({
                    "family": family,
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "side": "long_only",
                    "parameters": {"lookback": lookback, "breakout_pct": pct},
                    "hypothesis": f"Channel breakout over {lookback} bars with {pct*100}% margin filters false breaks in {instrument}."
                })

    elif family == "rsi_mean_reversion":
        for period in [7, 10, 14, 21]:
            for lower in [20, 25, 30]:
                for exit_lvl in [50, 55]:
                    candidates.append({
                        "family": family,
                        "instrument": instrument,
                        "timeframe": timeframe,
                        "side": "long_only",
                        "parameters": {"period": period, "lower": lower, "exit_level": exit_lvl},
                        "hypothesis": f"RSI({period}) dropping below {lower} with target exit at {exit_lvl} captures oversold bounces."
                    })

    elif family == "volatility_filtered":
        for lookback in [5, 8, 12]:
            for min_v, max_v in [(0.001, 0.02), (0.002, 0.03)]:
                candidates.append({
                    "family": family,
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "side": "long_only",
                    "parameters": {"lookback": lookback, "vol_window": 20, "min_vol_pct": min_v, "max_vol_pct": max_v},
                    "hypothesis": f"Momentum({lookback}) constrained to volatility between {min_v*100}% and {max_v*100}% avoids low-liquidity spikes."
                })

    elif family == "trend_following":
        for trend_ma in [50, 80, 100, 200]:
            for trigger_ma in [10, 15, 20]:
                candidates.append({
                    "family": family,
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "side": "long_only",
                    "parameters": {"trend_ma": trend_ma, "trigger_ma": trigger_ma},
                    "hypothesis": f"Trading when price > {trend_ma} SMA and bouncing over {trigger_ma} SMA rides macro direction."
                })

    elif family == "multi_timeframe_confirmation":
        for factor in [3, 4, 5]:
            for fast, slow in [(6, 18), (8, 24), (10, 30)]:
                candidates.append({
                    "family": family,
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "side": "long_only",
                    "parameters": {"higher_tf_factor": factor, "fast": fast, "slow": slow},
                    "hypothesis": f"Confirmation across {factor}x higher timeframe trend filters false LTF crossover signals."
                })

    elif family == "atr_volatility_adaptation":
        for p in [10, 14, 20]:
            for mult in [1.2, 1.5, 2.0]:
                candidates.append({
                    "family": family,
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "side": "long_only",
                    "parameters": {"period": p, "multiplier": mult, "ma_period": 20},
                    "hypothesis": f"Adaptive bands scaling by {mult} * ATR({p}) adapt to changing volatility regimes in {instrument}."
                })

    elif family == "session_based":
        for start_h, end_h in [(8, 16), (12, 19), (7, 15)]:
            for lb in [8, 12, 20]:
                candidates.append({
                    "family": family,
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "side": "long_only",
                    "parameters": {"start_hour": start_h, "end_hour": end_h, "lookback": lb},
                    "hypothesis": f"Limiting trend entries to {start_h}:00-{end_h}:00 UTC isolates peak market liquidity and tighter spreads."
                })

    elif family == "composite_combination":
        for ma in [30, 50]:
            for rsi_l in [30, 35]:
                candidates.append({
                    "family": family,
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "side": "long_only",
                    "parameters": {"trend_filter_ma": ma, "rsi_period": 14, "rsi_lower": rsi_l, "rsi_exit": 55},
                    "hypothesis": f"Buying oversold dips (RSI < {rsi_l}) exclusively in the direction of the {ma} SMA trend."
                })

    return candidates

def generate_all_candidates(instrument: str = "XAUUSD", timeframe: str = "M15") -> List[Dict[str, Any]]:
    all_cands = []
    for fam in ALLOWED_FAMILIES:
        all_cands.extend(generate_family_candidates(fam, instrument, timeframe))
    return all_cands
