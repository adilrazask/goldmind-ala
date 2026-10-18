"""FastAPI Router for Delta Exchange Integration."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from backend.app.delta.config import delta_settings
from backend.app.delta.rest_client import delta_client
from backend.app.delta.ws_client import delta_ws
from backend.app.delta.adapter import delta_broker
from backend.app.core.dependencies import order_manager

router = APIRouter(prefix="/delta", tags=["Delta Exchange"])

class ModeUpdateRequest(BaseModel):
    mode: str = Field(..., description="'PAPER' or 'LIVE'")
    live_confirmation_phrase: Optional[str] = None

@router.get("/status")
def get_delta_status():
    """Returns Delta Exchange connectivity health, latency, WebSocket status, and configuration."""
    conn_info = delta_client.check_connectivity()
    ws_info = delta_ws.get_status()
    cfg_info = delta_settings.validate_configuration()

    return {
        "status": "ONLINE" if conn_info["online"] else "OFFLINE",
        "rest": conn_info,
        "websocket": ws_info,
        "configuration": cfg_info,
        "active_trading_mode": delta_settings.trading_mode
    }

@router.get("/products")
def get_delta_products():
    """Retrieves discovered Delta Exchange products catalogue."""
    products = delta_broker.refresh_products()
    return {
        "count": len(products),
        "products": products
    }

@router.get("/tickers")
def get_delta_tickers(symbol: Optional[str] = None):
    """Retrieves live prices, bid/ask, and 24h volume from Delta Exchange."""
    tickers = delta_client.get_tickers(symbol)
    return {
        "count": len(tickers),
        "tickers": tickers
    }

@router.get("/candles")
def get_delta_candles(
    symbol: str = "BTCUSD",
    resolution: str = "15m",
    limit: int = 100
):
    """Retrieves historical OHLCV candlesticks with data quality audit."""
    candles, audit = delta_client.get_candles(symbol=symbol, resolution=resolution, limit=limit)
    return {
        "symbol": symbol,
        "resolution": resolution,
        "count": len(candles),
        "candles": candles,
        "audit": audit
    }

@router.get("/account")
def get_delta_account():
    """Retrieves authoritative account balances, margin, and equity."""
    info = delta_broker.get_account_info()
    return info

@router.get("/positions")
def get_delta_positions(symbol: Optional[str] = None):
    """Retrieves active positions from Delta Exchange."""
    positions = delta_broker.get_positions(symbol)
    return {
        "count": len(positions),
        "positions": positions
    }

@router.get("/orders")
def get_delta_orders(product_id: Optional[int] = None):
    """Retrieves open orders from Delta Exchange."""
    orders = delta_client.get_open_orders(product_id)
    return {
        "count": len(orders),
        "orders": orders
    }

@router.post("/mode")
def update_trading_mode(payload: ModeUpdateRequest):
    """Switches between Mode A (PAPER) and Mode B (LIVE) with strict risk gating."""
    mode = payload.mode.upper()
    if mode not in ("PAPER", "LIVE"):
        raise HTTPException(status_code=400, detail="Mode must be 'PAPER' or 'LIVE'.")

    if mode == "LIVE":
        if payload.live_confirmation_phrase != "I UNDERSTAND REAL MONEY RISK":
            raise HTTPException(
                status_code=403,
                detail="Live trading requires explicit confirmation phrase: 'I UNDERSTAND REAL MONEY RISK'."
            )
        if not delta_settings.api_key or not delta_settings.api_secret:
            raise HTTPException(
                status_code=400,
                detail="Cannot enable live trading: Delta Exchange API credentials are not configured."
            )
        delta_settings.trading_mode = "LIVE"
        delta_settings.is_live_enabled = True
    else:
        delta_settings.trading_mode = "PAPER"
        delta_settings.is_live_enabled = False

    return {
        "status": "SUCCESS",
        "trading_mode": delta_settings.trading_mode,
        "is_live_authorized": delta_settings.is_live_enabled
    }

@router.post("/reconcile")
def reconcile_delta_state():
    """Reconciles internal database positions with authoritative Delta Exchange state."""
    rec_result = order_manager.reconcile_state()
    return rec_result
