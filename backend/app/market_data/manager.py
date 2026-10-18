"""Market Data Manager: Handles historical OHLCV data, provider adapters, data quality auditing, and timezone normalization."""
from __future__ import annotations
import csv
import math
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

INSTRUMENT_SPECS = {
    "XAUUSD": {
        "description": "Gold vs US Dollar (Spot)",
        "digits": 2,
        "point": 0.01,
        "tick_size": 0.01,
        "tick_value": 1.0,
        "contract_size": 100.0,
        "volume_min": 0.01,
        "volume_step": 0.01,
        "volume_max": 20.0,
        "typical_spread_points": 25,
        "allowed_hours": (0, 23)
    },
    "BTCUSD": {
        "description": "Bitcoin vs US Dollar",
        "digits": 2,
        "point": 0.01,
        "tick_size": 0.1,
        "tick_value": 0.1,
        "contract_size": 1.0,
        "volume_min": 0.01,
        "volume_step": 0.01,
        "volume_max": 10.0,
        "typical_spread_points": 35,
        "allowed_hours": (0, 24)
    },
    "BTC_USDT": {
        "description": "Delta Exchange Bitcoin Perpetual (USDT)",
        "digits": 2,
        "point": 0.1,
        "tick_size": 0.5,
        "tick_value": 0.5,
        "contract_size": 1.0,
        "volume_min": 1.0,
        "volume_step": 1.0,
        "volume_max": 100.0,
        "typical_spread_points": 20,
        "allowed_hours": (0, 24)
    },
    "BTC_INR": {
        "description": "Delta Exchange India Bitcoin Futures (INR)",
        "digits": 2,
        "point": 1.0,
        "tick_size": 1.0,
        "tick_value": 1.0,
        "contract_size": 1.0,
        "volume_min": 1.0,
        "volume_step": 1.0,
        "volume_max": 50.0,
        "typical_spread_points": 25,
        "allowed_hours": (0, 24)
    },
    "ETHUSD": {
        "description": "Ethereum vs US Dollar",
        "digits": 2,
        "point": 0.01,
        "tick_size": 0.05,
        "tick_value": 0.05,
        "contract_size": 1.0,
        "volume_min": 0.1,
        "volume_step": 0.1,
        "volume_max": 50.0,
        "typical_spread_points": 20,
        "allowed_hours": (0, 24)
    },
    "ETH_USDT": {
        "description": "Delta Exchange Ethereum Perpetual (USDT)",
        "digits": 2,
        "point": 0.01,
        "tick_size": 0.05,
        "tick_value": 0.05,
        "contract_size": 1.0,
        "volume_min": 1.0,
        "volume_step": 1.0,
        "volume_max": 100.0,
        "typical_spread_points": 15,
        "allowed_hours": (0, 24)
    }
}

class DataQualityAudit:
    @staticmethod
    def audit_candles(candles: List[Dict[str, Any]], expected_timeframe_minutes: int = 15) -> Dict[str, Any]:
        report = {
            "total_candles": len(candles),
            "missing_candles": 0,
            "duplicate_candles": 0,
            "invalid_ohlc_bars": 0,
            "zero_or_negative_prices": 0,
            "gaps_detected": [],
            "is_valid": True,
            "start_time": None,
            "end_time": None,
            "anomalies": []
        }
        
        if not candles:
            report["is_valid"] = False
            report["anomalies"].append("Empty candle dataset")
            return report
            
        timestamps = []
        for idx, c in enumerate(candles):
            try:
                stamp_str = c["timestamp"]
                dt = datetime.fromisoformat(stamp_str.replace("Z", "+00:00"))
                timestamps.append(dt)
            except Exception as e:
                report["invalid_ohlc_bars"] += 1
                report["anomalies"].append(f"Invalid timestamp format at bar {idx}: {c.get('timestamp')}")
                continue
                
            o, h, l, cl = c.get("open", 0), c.get("high", 0), c.get("low", 0), c.get("close", 0)
            if min(o, h, l, cl) <= 0 or not all(math.isfinite(x) for x in (o, h, l, cl)):
                report["zero_or_negative_prices"] += 1
            if h < max(o, cl, l) or l > min(o, cl, h):
                report["invalid_ohlc_bars"] += 1

        if timestamps:
            report["start_time"] = timestamps[0].isoformat()
            report["end_time"] = timestamps[-1].isoformat()
            
            # Check ordering, duplicates, and gaps
            expected_delta = timedelta(minutes=expected_timeframe_minutes)
            for i in range(1, len(timestamps)):
                prev_t = timestamps[i - 1]
                curr_t = timestamps[i]
                if curr_t <= prev_t:
                    report["duplicate_candles"] += 1
                diff = curr_t - prev_t
                if diff > expected_delta * 1.5:
                    # Gaps over weekends/sessions are normal, but let's record large abnormal gaps
                    report["missing_candles"] += int(diff / expected_delta) - 1
                    if len(report["gaps_detected"]) < 10:
                        report["gaps_detected"].append({
                            "from": prev_t.isoformat(),
                            "to": curr_t.isoformat(),
                            "gap_minutes": int(diff.total_seconds() / 60)
                        })

        if report["invalid_ohlc_bars"] > 0 or report["zero_or_negative_prices"] > 0 or report["duplicate_candles"] > 0:
            report["is_valid"] = False
            
        return report

class MarketDataManager:
    def __init__(self):
        self.sources = {}

    def get_instrument_specs(self, symbol: str) -> Dict[str, Any]:
        return INSTRUMENT_SPECS.get(symbol.upper(), {
            "description": f"Custom Instrument {symbol}",
            "digits": 2,
            "point": 0.01,
            "tick_size": 0.01,
            "tick_value": 1.0,
            "contract_size": 100.0,
            "volume_min": 0.01,
            "volume_step": 0.01,
            "volume_max": 10.0,
            "typical_spread_points": 30,
            "allowed_hours": (0, 24)
        })

    def generate_regime_dataset(self, symbol: str = "XAUUSD", timeframe: str = "M15", bars: int = 500, seed: int = 42) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Generates realistic market candles with distinct macro regimes (bull, bear, chop, high vol) for research."""
        rng = random.Random(seed)
        start_price = 2650.0 if symbol == "XAUUSD" else 88000.0
        curr_price = start_price
        start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        
        minutes_step = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}.get(timeframe, 15)
        candles = []
        
        for i in range(bars):
            # 4 distinct market regimes
            regime_idx = (i // (bars // 4)) % 4
            if regime_idx == 0:
                # Bullish trend
                drift = 0.0004
                vol = 0.003
            elif regime_idx == 1:
                # High volatility whipsaw / chop
                drift = -0.0001
                vol = 0.006
            elif regime_idx == 2:
                # Bearish correction
                drift = -0.00035
                vol = 0.0035
            else:
                # Low volatility range
                drift = 0.00005
                vol = 0.0015
                
            ret = drift + rng.gauss(0, vol)
            o = curr_price
            cl = o * (1.0 + ret)
            high_wiggle = abs(rng.gauss(0, vol * 0.8))
            low_wiggle = abs(rng.gauss(0, vol * 0.8))
            h = max(o, cl) * (1.0 + high_wiggle)
            l = min(o, cl) * (1.0 - low_wiggle)
            curr_price = cl
            
            bar_time = start_time + timedelta(minutes=minutes_step * i)
            candles.append({
                "timestamp": bar_time.isoformat(),
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(cl, 2),
                "volume": round(rng.uniform(50.0, 500.0), 2)
            })
            
        audit = DataQualityAudit.audit_candles(candles, expected_timeframe_minutes=minutes_step)
        return candles, audit

    def load_csv(self, file_path: str, timeframe_minutes: int = 15) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        path = Path(file_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
            
        candles = []
        with path.open("r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV header missing")
            col_map = {c.strip().lower(): c for c in reader.fieldnames}
            for row in reader:
                candles.append({
                    "timestamp": row[col_map["timestamp"]].strip(),
                    "open": float(row[col_map["open"]]),
                    "high": float(row[col_map["high"]]),
                    "low": float(row[col_map["low"]]),
                    "close": float(row[col_map["close"]]),
                    "volume": float(row[col_map["volume"]]) if "volume" in col_map and row[col_map["volume"]] else 0.0
                })
        audit = DataQualityAudit.audit_candles(candles, expected_timeframe_minutes=timeframe_minutes)
        return candles, audit
