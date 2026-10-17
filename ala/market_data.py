"""CSV loading utilities for user-provided historical OHLCV data."""
import csv
from datetime import datetime
from pathlib import Path
from typing import TypedDict

class Candle(TypedDict):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float

def load_ohlcv_csv(path: str) -> list[Candle]:
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    with file_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        normalized = {name.strip().lower(): name for name in reader.fieldnames if name}
        required = {"timestamp", "open", "high", "low", "close"}
        missing = sorted(required - set(normalized))
        if missing:
            raise ValueError("CSV is missing required columns: " + ", ".join(missing))
        rows: list[Candle] = []
        for line_no, row in enumerate(reader, start=2):
            try:
                stamp = str(row[normalized["timestamp"]]).strip()
                # Validate common ISO-like timestamps; retain original value for reporting.
                datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                candle = {
                    "timestamp": stamp,
                    "open": float(row[normalized["open"]]),
                    "high": float(row[normalized["high"]]),
                    "low": float(row[normalized["low"]]),
                    "close": float(row[normalized["close"]]),
                    "volume": float(row[normalized["volume"]]) if "volume" in normalized and row.get(normalized["volume"]) not in (None, "") else 0.0,
                }
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f"Invalid candle at CSV line {line_no}: {exc}") from exc
            vals = [candle[k] for k in ("open", "high", "low", "close", "volume")]
            if any(v != v or abs(v) == float("inf") for v in vals):
                raise ValueError(f"Non-finite numeric value at CSV line {line_no}")
            if min(candle["open"], candle["high"], candle["low"], candle["close"]) <= 0:
                raise ValueError(f"OHLC prices must be positive at CSV line {line_no}")
            if candle["high"] < max(candle["open"], candle["close"], candle["low"]):
                raise ValueError(f"Inconsistent high at CSV line {line_no}")
            if candle["low"] > min(candle["open"], candle["close"], candle["high"]):
                raise ValueError(f"Inconsistent low at CSV line {line_no}")
            rows.append(candle)
    if len(rows) < 50:
        raise ValueError(f"Need at least 50 candles; found {len(rows)}")
    stamps = [datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) for r in rows]
    if any(stamps[i] <= stamps[i-1] for i in range(1, len(stamps))):
        raise ValueError("Timestamps must be strictly increasing with no duplicates")
    return rows
