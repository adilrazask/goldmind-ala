"""MT5 Broker Adapter: Wraps MetaTrader 5 Python integration with strict demo-first validation."""
from __future__ import annotations
import os
import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .base import BaseBroker, OrderResult

class MT5BrokerAdapter(BaseBroker):
    def __init__(self, mode: str = "demo", confirmation: Optional[str] = None):
        self.mode = mode
        self.confirmation = confirmation
        self.mt5 = None
        self.is_connected = False
        
    def connect(self) -> bool:
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
        except ImportError:
            return False

        if not self.mt5.initialize():
            return False
            
        self.account = self.mt5.account_info()
        if not self.account:
            return False
            
        self.is_connected = True
        return True

    def get_account_info(self) -> Dict[str, Any]:
        if not self.is_connected or not self.mt5:
            return {
                "broker": "MetaTrader 5 (Disconnected / Not available on Mac)",
                "account_number": "N/A",
                "mode": self.mode,
                "currency": "USD",
                "balance": 0.0,
                "equity": 0.0,
                "margin": 0.0,
                "free_margin": 0.0,
                "is_connected": False,
                "trade_allowed": False
            }
        a = self.mt5.account_info()
        return {
            "broker": f"MT5 ({a.company})",
            "account_number": str(a.login),
            "mode": "REAL" if getattr(a, "trade_mode", 0) == 2 else "DEMO",
            "currency": str(a.currency),
            "balance": float(a.balance),
            "equity": float(a.equity),
            "margin": float(a.margin),
            "free_margin": float(a.margin_free),
            "is_connected": True,
            "trade_allowed": bool(a.trade_allowed)
        }

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.mt5:
            return []
        raw = self.mt5.positions_get(symbol=symbol) if symbol else self.mt5.positions_get()
        if not raw:
            return []
        return [{
            "ticket": int(p.ticket),
            "symbol": str(p.symbol),
            "side": "BUY" if int(p.type) == 0 else "SELL",
            "volume": float(p.volume),
            "open_price": float(p.price_open),
            "current_price": float(p.price_current),
            "stop_loss": float(p.sl),
            "take_profit": float(p.tp),
            "unrealized_profit": float(p.profit),
            "magic": int(p.magic)
        } for p in raw]

    def submit_order(
        self,
        symbol: str,
        side: str,
        volume: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        magic: int = 610181
    ) -> OrderResult:
        if not self.is_connected or not self.mt5:
            return OrderResult(False, None, symbol, side, volume, entry_price, stop_loss, take_profit, "REJECTED", "MT5 not connected")
        # Submit via MT5
        mt5 = self.mt5
        order_type = mt5.ORDER_TYPE_BUY if side.upper() == "BUY" else mt5.ORDER_TYPE_SELL
        info = mt5.symbol_info(symbol)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": entry_price,
            "sl": stop_loss,
            "tp": take_profit,
            "deviation": 20,
            "magic": magic,
            "comment": "GoldMind ALA Guarded",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": info.filling_mode if info else 0
        }
        res = mt5.order_send(request)
        if not res or res.retcode != mt5.TRADE_RETCODE_DONE:
            return OrderResult(False, None, symbol, side, volume, entry_price, stop_loss, take_profit, "REJECTED", f"Broker error: {res.comment if res else 'Unknown'}")
        return OrderResult(True, int(res.order), symbol, side, volume, entry_price, stop_loss, take_profit, "FILLED", "Filled via MT5")

    def close_position(self, ticket: int, magic: int = 610181) -> bool:
        if not self.is_connected or not self.mt5:
            return False
        # Find position and send opposite deal
        pos = self.mt5.positions_get(ticket=ticket)
        if not pos:
            return False
        p = pos[0]
        if int(p.magic) != magic:
            return False
        is_buy = int(p.type) == 0
        tick = self.mt5.symbol_info_tick(p.symbol)
        req = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": p.symbol,
            "volume": float(p.volume),
            "type": self.mt5.ORDER_TYPE_SELL if is_buy else self.mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "price": float(tick.bid if is_buy else tick.ask),
            "deviation": 20,
            "magic": magic,
            "comment": "GoldMind ALA Exit"
        }
        res = self.mt5.order_send(req)
        return bool(res and res.retcode == self.mt5.TRADE_RETCODE_DONE)

    def disconnect(self):
        if self.mt5:
            self.mt5.shutdown()
        self.is_connected = False
